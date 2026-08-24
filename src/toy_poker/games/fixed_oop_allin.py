"""Shared extensive form for fixed-OOP-card, one-bet all-in toy games."""

from __future__ import annotations

import enum
from collections.abc import Iterable

import pyspiel


class Action(enum.IntEnum):
    CHECK = 0
    ALL_IN = 1
    FOLD = 2


PLAYER_IP = 0
PLAYER_OOP = 1
NUM_PLAYERS = 2


def make_game_type(
    short_name: str, long_name: str, default_stack: float = 1.0
) -> pyspiel.GameType:
    return pyspiel.GameType(
        short_name=short_name,
        long_name=long_name,
        dynamics=pyspiel.GameType.Dynamics.SEQUENTIAL,
        chance_mode=pyspiel.GameType.ChanceMode.EXPLICIT_STOCHASTIC,
        information=pyspiel.GameType.Information.IMPERFECT_INFORMATION,
        utility=pyspiel.GameType.Utility.CONSTANT_SUM,
        reward_model=pyspiel.GameType.RewardModel.TERMINAL,
        max_num_players=NUM_PLAYERS,
        min_num_players=NUM_PLAYERS,
        provides_information_state_string=True,
        provides_information_state_tensor=False,
        provides_observation_string=True,
        provides_observation_tensor=False,
        parameter_specification={
            "oop_stack": default_stack,
            "ip_stack": default_stack,
        },
    )


class FixedOOPAllInGame(pyspiel.Game):
    """Base game where OOP holds one fixed card and IP receives a private card."""

    def __init__(
        self,
        game_type: pyspiel.GameType,
        ip_cards: Iterable[enum.IntEnum],
        ip_winning_cards: Iterable[enum.IntEnum],
        oop_card_label: str,
        default_stack: float = 1.0,
        params=None,
    ):
        params = params or {}
        self.oop_stack = float(params.get("oop_stack", default_stack))
        self.ip_stack = float(params.get("ip_stack", default_stack))
        if self.oop_stack <= 0 or self.ip_stack <= 0:
            raise ValueError("oop_stack and ip_stack must both be positive")
        self.effective_stack = min(self.oop_stack, self.ip_stack)
        self.ip_cards = tuple(ip_cards)
        if not self.ip_cards:
            raise ValueError("ip_cards cannot be empty")
        self.ip_winning_cards = frozenset(int(card) for card in ip_winning_cards)
        self.oop_card_label = oop_card_label
        game_info = pyspiel.GameInfo(
            num_distinct_actions=len(Action),
            max_chance_outcomes=len(self.ip_cards),
            num_players=NUM_PLAYERS,
            min_utility=-self.effective_stack,
            max_utility=1.0 + self.effective_stack,
            utility_sum=1.0,
            max_game_length=3,
        )
        super().__init__(game_type, game_info, params)

    def new_initial_state(self):
        return FixedOOPAllInState(self)

    def make_py_observer(self, iig_obs_type=None, params=None):
        if params:
            raise ValueError(f"Observation parameters are unsupported: {params}")
        return StringObserver(iig_obs_type or pyspiel.IIGObservationType(perfect_recall=True))

    def card_from_action(self, action: int) -> enum.IntEnum:
        for card in self.ip_cards:
            if int(card) == action:
                return card
        raise ValueError(f"Unknown IP card action: {action}")


class FixedOOPAllInState(pyspiel.State):
    def __init__(self, game: FixedOOPAllInGame):
        super().__init__(game)
        self.ip_card: enum.IntEnum | None = None
        self.history: list[Action] = []
        self._terminal = False
        self._current_player = PLAYER_OOP

    def current_player(self):
        if self._terminal:
            return pyspiel.PlayerId.TERMINAL
        if self.ip_card is None:
            return pyspiel.PlayerId.CHANCE
        return self._current_player

    def _legal_actions(self, player):
        if player < 0 or self._terminal or self.ip_card is None:
            return []
        if self._facing_all_in():
            return [Action.ALL_IN, Action.FOLD]
        return [Action.CHECK, Action.ALL_IN]

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
            raise ValueError(f"Illegal action {action.name} for history {self.history}")
        facing_all_in = self._facing_all_in()
        self.history.append(action)
        if facing_all_in:
            self._terminal = True
            return
        if action == Action.ALL_IN:
            self._current_player = 1 - self._current_player
            return
        if self._current_player == PLAYER_IP:
            self._terminal = True
        else:
            self._current_player = PLAYER_IP

    def _facing_all_in(self):
        return bool(self.history and self.history[-1] == Action.ALL_IN)

    def _action_to_string(self, player, action):
        if player == pyspiel.PlayerId.CHANCE:
            card = self.get_game().card_from_action(action)
            return f"Deal{card.name[0]}"
        action = Action(action)
        if action == Action.ALL_IN and self._facing_all_in():
            return "Call"
        return {Action.CHECK: "Check", Action.ALL_IN: "AllIn", Action.FOLD: "Fold"}[action]

    def is_terminal(self):
        return self._terminal

    def returns(self):
        if not self._terminal:
            return [0.0, 0.0]
        if self.history[-1] == Action.FOLD:
            folder = self._current_player
            winner = 1 - folder
            result = [0.0, 0.0]
            result[winner] = 1.0
            return result
        game = self.get_game()
        matched = game.effective_stack if self.history.count(Action.ALL_IN) == 2 else 0.0
        assert self.ip_card is not None
        winner = PLAYER_IP if int(self.ip_card) in game.ip_winning_cards else PLAYER_OOP
        result = [-matched, -matched]
        result[winner] = 1.0 + matched
        return result

    def information_state_string(self, player=None):
        if player is None:
            player = self.current_player()
        if player not in (PLAYER_IP, PLAYER_OOP):
            raise ValueError(f"No information state for player {player}")
        private_card = self.get_game().oop_card_label if player == PLAYER_OOP else self.ip_card.name[0]
        public_history = "-".join(action.name for action in self.history) or "ROOT"
        return f"P{player}|{private_card}|{public_history}"

    def observation_string(self, player):
        return self.information_state_string(player)

    def __str__(self):
        card = "?" if self.ip_card is None else self.ip_card.name[0]
        actions = "-".join(action.name for action in self.history) or "ROOT"
        return f"IP:{card}|{actions}"


class StringObserver:
    def __init__(self, iig_obs_type):
        self.iig_obs_type = iig_obs_type
        self.tensor = None
        self.dict = {}

    def set_from(self, state, player):
        del state, player

    def string_from(self, state, player):
        return state.information_state_string(player)
