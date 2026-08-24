"""Shared two-street betting game for a fixed-card OOP player."""

from __future__ import annotations

import enum
import math
from collections.abc import Iterable

import pyspiel


class Action(enum.IntEnum):
    CHECK = 0
    GEOMETRIC_BET = 1
    ALL_IN = 2
    CALL = 3
    FOLD = 4


PLAYER_IP = 0
PLAYER_OOP = 1
NUM_PLAYERS = 2
INITIAL_POT = 1.0
NUM_STREETS = 2
_CHIP_TOLERANCE = 1e-12


def geometric_fraction(effective_stack: float) -> float:
    """Return the constant pot fraction that gets all-in over two bet-call streets."""
    if effective_stack <= 0:
        raise ValueError("effective_stack must be positive")
    return (math.sqrt(1.0 + 2.0 * effective_stack) - 1.0) / 2.0


def make_game_type(short_name: str, long_name: str) -> pyspiel.GameType:
    return pyspiel.GameType(
        short_name=short_name,
        long_name=long_name,
        dynamics=pyspiel.GameType.Dynamics.SEQUENTIAL,
        chance_mode=pyspiel.GameType.ChanceMode.EXPLICIT_STOCHASTIC,
        information=pyspiel.GameType.Information.IMPERFECT_INFORMATION,
        utility=pyspiel.GameType.Utility.ZERO_SUM,
        reward_model=pyspiel.GameType.RewardModel.TERMINAL,
        max_num_players=NUM_PLAYERS,
        min_num_players=NUM_PLAYERS,
        provides_information_state_string=True,
        provides_information_state_tensor=False,
        provides_observation_string=True,
        provides_observation_tensor=False,
        parameter_specification={"oop_stack": 1.0, "ip_stack": 1.0},
    )


class FixedOOPTwoStreetGame(pyspiel.Game):
    """Base game with two betting rounds and no new card between them."""

    def __init__(
        self,
        game_type: pyspiel.GameType,
        ip_cards: Iterable[enum.IntEnum],
        ip_winning_cards: Iterable[enum.IntEnum],
        oop_card_label: str,
        params=None,
    ):
        params = params or {}
        self.oop_stack = float(params.get("oop_stack", 1.0))
        self.ip_stack = float(params.get("ip_stack", 1.0))
        if self.oop_stack <= 0 or self.ip_stack <= 0:
            raise ValueError("oop_stack and ip_stack must both be positive")
        self.effective_stack = min(self.oop_stack, self.ip_stack)
        self.geometric_fraction = geometric_fraction(self.effective_stack)
        self.ip_cards = tuple(ip_cards)
        if not self.ip_cards:
            raise ValueError("ip_cards cannot be empty")
        self.ip_winning_cards = frozenset(int(card) for card in ip_winning_cards)
        self.oop_card_label = oop_card_label
        max_payoff = INITIAL_POT / 2.0 + self.effective_stack
        game_info = pyspiel.GameInfo(
            num_distinct_actions=len(Action),
            max_chance_outcomes=len(self.ip_cards),
            num_players=NUM_PLAYERS,
            min_utility=-max_payoff,
            max_utility=max_payoff,
            utility_sum=0.0,
            max_game_length=6,
        )
        super().__init__(game_type, game_info, params)

    def new_initial_state(self):
        return FixedOOPTwoStreetState(self)

    def make_py_observer(self, iig_obs_type=None, params=None):
        if params:
            raise ValueError(f"Observation parameters are unsupported: {params}")
        return StringObserver(iig_obs_type or pyspiel.IIGObservationType(perfect_recall=True))

    def card_from_action(self, action: int) -> enum.IntEnum:
        for card in self.ip_cards:
            if int(card) == action:
                return card
        raise ValueError(f"Unknown IP card action: {action}")


class FixedOOPTwoStreetState(pyspiel.State):
    def __init__(self, game: FixedOOPTwoStreetGame):
        super().__init__(game)
        self.ip_card: enum.IntEnum | None = None
        self.street = 0
        self.street_histories: list[list[Action]] = [[]]
        self.commitments = [0.0, 0.0]
        self._terminal = False
        self._folder: int | None = None
        self._current_player = PLAYER_OOP

    @property
    def pot(self) -> float:
        return INITIAL_POT + sum(self.commitments)

    def current_player(self):
        if self._terminal:
            return pyspiel.PlayerId.TERMINAL
        if self.ip_card is None:
            return pyspiel.PlayerId.CHANCE
        return self._current_player

    def _legal_actions(self, player):
        if (
            player < 0
            or self._terminal
            or self.ip_card is None
            or player != self._current_player
        ):
            return []
        if self._amount_to_call(player) > _CHIP_TOLERANCE:
            if not self._facing_all_in(player):
                return [Action.ALL_IN, Action.CALL, Action.FOLD]
            return [Action.CALL, Action.FOLD]
        actions = [Action.CHECK]
        if self._geometric_bet_is_distinct(player):
            actions.append(Action.GEOMETRIC_BET)
        actions.append(Action.ALL_IN)
        return actions

    def chance_outcomes(self):
        if not self.is_chance_node():
            raise ValueError("chance_outcomes called outside the chance node")
        game = self.get_game()
        probability = 1.0 / len(game.ip_cards)
        return [(int(card), probability) for card in game.ip_cards]

    def _apply_action(self, action):
        if self.is_chance_node():
            self.ip_card = self.get_game().card_from_action(action)
            self._current_player = PLAYER_OOP
            return
        action = Action(action)
        if action not in self._legal_actions(self._current_player):
            raise ValueError(
                f"Illegal action {action.name} for history {self._public_history()}"
            )
        player = self._current_player
        facing_bet = self._amount_to_call(player) > _CHIP_TOLERANCE
        self.street_histories[-1].append(action)
        if action == Action.FOLD:
            self._folder = player
            self._terminal = True
            return
        if action == Action.CALL:
            opponent = 1 - player
            self.commitments[player] = self.commitments[opponent]
            if self._facing_all_in_after_call() or self.street == NUM_STREETS - 1:
                self._terminal = True
            else:
                self._advance_street()
            return
        if action == Action.ALL_IN:
            self.commitments[player] = self.get_game().effective_stack
            self._current_player = 1 - player
            return
        if action == Action.GEOMETRIC_BET:
            self.commitments[player] += self.geometric_bet_amount(player)
            self._current_player = 1 - player
            return
        if facing_bet:
            raise AssertionError("Check cannot face a bet")
        if player == PLAYER_IP:
            if self.street == NUM_STREETS - 1:
                self._terminal = True
            else:
                self._advance_street()
        else:
            self._current_player = PLAYER_IP

    def _advance_street(self) -> None:
        self.street += 1
        self.street_histories.append([])
        self._current_player = PLAYER_OOP

    def _amount_to_call(self, player: int) -> float:
        return max(0.0, self.commitments[1 - player] - self.commitments[player])

    def _facing_all_in(self, player: int) -> bool:
        return math.isclose(
            self.commitments[1 - player],
            self.get_game().effective_stack,
            rel_tol=1e-12,
            abs_tol=_CHIP_TOLERANCE,
        )

    def _facing_all_in_after_call(self) -> bool:
        return math.isclose(
            self.commitments[PLAYER_IP],
            self.get_game().effective_stack,
            rel_tol=1e-12,
            abs_tol=_CHIP_TOLERANCE,
        )

    def geometric_bet_amount(self, player: int | None = None) -> float:
        if player is None:
            player = self._current_player
        remaining = self.get_game().effective_stack - self.commitments[player]
        return min(self.get_game().geometric_fraction * self.pot, remaining)

    def _geometric_bet_is_distinct(self, player: int) -> bool:
        amount = self.geometric_bet_amount(player)
        remaining = self.get_game().effective_stack - self.commitments[player]
        return amount > _CHIP_TOLERANCE and not math.isclose(
            amount, remaining, rel_tol=1e-12, abs_tol=_CHIP_TOLERANCE
        )

    def _public_history(self) -> str:
        segments = []
        for index, actions in enumerate(self.street_histories, start=1):
            action_text = "-".join(action.name for action in actions) or "ROOT"
            segments.append(f"S{index}:{action_text}")
        return "/".join(segments)

    def _action_to_string(self, player, action):
        if player == pyspiel.PlayerId.CHANCE:
            card = self.get_game().card_from_action(action)
            return f"Deal{card.name[0]}"
        action = Action(action)
        if action == Action.ALL_IN and self._amount_to_call(player) > _CHIP_TOLERANCE:
            return "Raise all-in"
        return {
            Action.CHECK: "Check",
            Action.GEOMETRIC_BET: "Geometric bet",
            Action.ALL_IN: "AllIn",
            Action.CALL: "Call",
            Action.FOLD: "Fold",
        }[action]

    def is_terminal(self):
        return self._terminal

    def returns(self):
        if not self._terminal:
            return [0.0, 0.0]
        if self._folder is not None:
            winner = 1 - self._folder
            payoff = INITIAL_POT / 2.0 + self.commitments[self._folder]
        else:
            assert math.isclose(
                self.commitments[PLAYER_IP],
                self.commitments[PLAYER_OOP],
                rel_tol=1e-12,
                abs_tol=_CHIP_TOLERANCE,
            )
            payoff = INITIAL_POT / 2.0 + self.commitments[PLAYER_IP]
            assert self.ip_card is not None
            winner = (
                PLAYER_IP
                if int(self.ip_card) in self.get_game().ip_winning_cards
                else PLAYER_OOP
            )
        result = [-payoff, -payoff]
        result[winner] = payoff
        return result

    def information_state_string(self, player=None):
        if player is None:
            player = self.current_player()
        if player not in (PLAYER_IP, PLAYER_OOP):
            raise ValueError(f"No information state for player {player}")
        private_card = (
            self.get_game().oop_card_label
            if player == PLAYER_OOP
            else self.ip_card.name[0]
        )
        return f"P{player}|{private_card}|{self._public_history()}"

    def observation_string(self, player):
        return self.information_state_string(player)

    def __str__(self):
        card = "?" if self.ip_card is None else self.ip_card.name[0]
        return (
            f"IP:{card}|{self._public_history()}|pot={self.pot:.6g}|"
            f"committed={self.commitments}"
        )


class StringObserver:
    def __init__(self, iig_obs_type):
        self.iig_obs_type = iig_obs_type
        self.tensor = None
        self.dict = {}

    def set_from(self, state, player):
        del state, player

    def string_from(self, state, player):
        return state.information_state_string(player)
