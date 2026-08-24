"""One-street range game with configurable pot-fraction bets and raises."""

from __future__ import annotations

import enum
import math

import pyspiel


class Action(enum.IntEnum):
    CHECK = 0
    FOLD = 1
    CALL = 2
    ALL_IN = 3


PLAYER_IP = 0
PLAYER_OOP = 1
NUM_PLAYERS = 2
INITIAL_POT = 1.0
FIRST_CUSTOM_ACTION = len(Action)
_CHIP_TOLERANCE = 1e-10


def parse_bet_fractions(value: str) -> tuple[float, ...]:
    """Parse a comma-separated list of positive, unique pot fractions."""
    if not isinstance(value, str):
        raise ValueError("bet_fractions must be a comma-separated string")
    try:
        fractions = tuple(sorted(float(part.strip()) for part in value.split(",")))
    except ValueError as exc:
        raise ValueError("bet_fractions contains a non-numeric value") from exc
    if not fractions or any(not math.isfinite(value) or value <= 0 for value in fractions):
        raise ValueError("bet_fractions must contain finite positive values")
    if any(
        math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12)
        for left, right in zip(fractions, fractions[1:])
    ):
        raise ValueError("bet_fractions cannot contain duplicates")
    return fractions


def fraction_label(fraction: float) -> str:
    if math.isclose(fraction, 1.0 / 3.0, rel_tol=1e-12, abs_tol=1e-12):
        return "33%"
    percentage = fraction * 100.0
    return f"{percentage:.6g}%"


def make_game_type(
    short_name: str,
    long_name: str,
    default_stack: float,
    default_bet_fractions: str,
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
            "bet_fractions": default_bet_fractions,
        },
    )


class FixedRangeOneStreetGame(pyspiel.Game):
    """Base game where both players receive an independent integer private value."""

    def __init__(
        self,
        game_type: pyspiel.GameType,
        min_card: int,
        max_card: int,
        default_stack: float,
        default_bet_fractions: str,
        params=None,
    ):
        params = params or {}
        self.oop_stack = float(params.get("oop_stack", default_stack))
        self.ip_stack = float(params.get("ip_stack", default_stack))
        if self.oop_stack <= 0 or self.ip_stack <= 0:
            raise ValueError("oop_stack and ip_stack must both be positive")
        self.effective_stack = min(self.oop_stack, self.ip_stack)
        self.min_card = int(min_card)
        self.max_card = int(max_card)
        if self.min_card > self.max_card:
            raise ValueError("min_card cannot exceed max_card")
        self.cards = tuple(range(self.min_card, self.max_card + 1))
        self.bet_fractions = parse_bet_fractions(
            str(params.get("bet_fractions", default_bet_fractions))
        )
        minimum_open = self.bet_fractions[0] * INITIAL_POT
        max_wager_actions = math.ceil(self.effective_stack / minimum_open) + 1
        game_info = pyspiel.GameInfo(
            num_distinct_actions=FIRST_CUSTOM_ACTION + len(self.bet_fractions),
            max_chance_outcomes=len(self.cards) ** 2,
            num_players=NUM_PLAYERS,
            min_utility=-self.effective_stack,
            max_utility=INITIAL_POT + self.effective_stack,
            utility_sum=INITIAL_POT,
            max_game_length=max_wager_actions + 4,
        )
        super().__init__(game_type, game_info, params)

    def new_initial_state(self):
        return FixedRangeOneStreetState(self)

    def make_py_observer(self, iig_obs_type=None, params=None):
        if params:
            raise ValueError(f"Observation parameters are unsupported: {params}")
        return StringObserver(iig_obs_type or pyspiel.IIGObservationType(perfect_recall=True))

    def custom_action(self, index: int) -> int:
        return FIRST_CUSTOM_ACTION + index

    def fraction_for_action(self, action: int) -> float:
        index = int(action) - FIRST_CUSTOM_ACTION
        if not 0 <= index < len(self.bet_fractions):
            raise ValueError(f"Unknown custom action: {action}")
        return self.bet_fractions[index]

    def deal_from_action(self, action: int) -> tuple[int, int]:
        action = int(action)
        card_count = len(self.cards)
        if not 0 <= action < card_count**2:
            raise ValueError(f"Unknown deal action: {action}")
        oop_index, ip_index = divmod(action, card_count)
        return self.cards[oop_index], self.cards[ip_index]


class FixedRangeOneStreetState(pyspiel.State):
    def __init__(self, game: FixedRangeOneStreetGame):
        super().__init__(game)
        self.private_cards: list[int | None] = [None, None]
        self.commitments = [0.0, 0.0]
        self.history: list[int] = []
        self.history_tokens: list[str] = []
        self.last_full_raise_increment = 0.0
        self._terminal = False
        self._folder: int | None = None
        self._current_player = PLAYER_OOP

    @property
    def pot(self) -> float:
        return INITIAL_POT + sum(self.commitments)

    def current_player(self):
        if self._terminal:
            return pyspiel.PlayerId.TERMINAL
        if self.private_cards[PLAYER_IP] is None:
            return pyspiel.PlayerId.CHANCE
        return self._current_player

    def chance_outcomes(self):
        if not self.is_chance_node():
            raise ValueError("chance_outcomes called outside the chance node")
        game = self.get_game()
        probability = 1.0 / (len(game.cards) ** 2)
        return [(action, probability) for action in range(len(game.cards) ** 2)]

    def _amount_to_call(self, player: int) -> float:
        return max(0.0, self.commitments[1 - player] - self.commitments[player])

    def _remaining(self, player: int) -> float:
        return self.get_game().effective_stack - self.commitments[player]

    def _opponent_is_all_in(self, player: int) -> bool:
        return math.isclose(
            self.commitments[1 - player],
            self.get_game().effective_stack,
            rel_tol=1e-12,
            abs_tol=_CHIP_TOLERANCE,
        )

    def custom_target(self, player: int, action: int) -> float:
        fraction = self.get_game().fraction_for_action(action)
        to_call = self._amount_to_call(player)
        if to_call <= _CHIP_TOLERANCE:
            chips_added = fraction * self.pot
        else:
            pot_after_call = self.pot + to_call
            chips_added = to_call + fraction * pot_after_call
        return min(
            self.commitments[player] + chips_added,
            self.get_game().effective_stack,
        )

    def _custom_action_is_distinct_and_legal(self, player: int, action: int) -> bool:
        target = self.custom_target(player, action)
        if target >= self.get_game().effective_stack - _CHIP_TOLERANCE:
            return False
        to_call = self._amount_to_call(player)
        if to_call <= _CHIP_TOLERANCE:
            return target > self.commitments[player] + _CHIP_TOLERANCE
        raise_increment = target - self.commitments[1 - player]
        return (
            raise_increment > _CHIP_TOLERANCE
            and raise_increment + _CHIP_TOLERANCE >= self.last_full_raise_increment
        )

    def _legal_actions(self, player):
        if (
            player < 0
            or self._terminal
            or self.private_cards[PLAYER_IP] is None
            or player != self._current_player
        ):
            return []
        to_call = self._amount_to_call(player)
        if to_call > _CHIP_TOLERANCE:
            actions = [Action.FOLD, Action.CALL]
            if self._opponent_is_all_in(player):
                return actions
            actions.extend(
                self.get_game().custom_action(index)
                for index in range(len(self.get_game().bet_fractions))
                if self._custom_action_is_distinct_and_legal(
                    player, self.get_game().custom_action(index)
                )
            )
            if self._remaining(player) > to_call + _CHIP_TOLERANCE:
                actions.append(Action.ALL_IN)
            return sorted(actions)
        actions = [Action.CHECK]
        actions.extend(
            self.get_game().custom_action(index)
            for index in range(len(self.get_game().bet_fractions))
            if self._custom_action_is_distinct_and_legal(
                player, self.get_game().custom_action(index)
            )
        )
        actions.append(Action.ALL_IN)
        return sorted(actions)

    def _history_token(self, action: int) -> str:
        facing_bet = self._amount_to_call(self._current_player) > _CHIP_TOLERANCE
        if action >= FIRST_CUSTOM_ACTION:
            prefix = "RAISE" if facing_bet else "BET"
            return f"{prefix}_{fraction_label(self.get_game().fraction_for_action(action))}"
        base_action = Action(action)
        if base_action == Action.ALL_IN and facing_bet:
            return "RAISE_ALL_IN"
        return base_action.name

    def _apply_action(self, action):
        if self.is_chance_node():
            oop_card, ip_card = self.get_game().deal_from_action(action)
            self.private_cards[PLAYER_OOP] = oop_card
            self.private_cards[PLAYER_IP] = ip_card
            self._current_player = PLAYER_OOP
            return
        action = int(action)
        if action not in self._legal_actions(self._current_player):
            raise ValueError(
                f"Illegal action {action} for history {'-'.join(self.history_tokens)}"
            )
        player = self._current_player
        opponent = 1 - player
        facing_bet = self._amount_to_call(player) > _CHIP_TOLERANCE
        self.history.append(action)
        self.history_tokens.append(self._history_token(action))
        if action == Action.FOLD:
            self._folder = player
            self._terminal = True
            return
        if action == Action.CALL:
            self.commitments[player] = self.commitments[opponent]
            self._terminal = True
            return
        if action == Action.CHECK:
            if player == PLAYER_IP:
                self._terminal = True
            else:
                self._current_player = PLAYER_IP
            return
        if action == Action.ALL_IN:
            previous_wager = self.commitments[opponent]
            self.commitments[player] = self.get_game().effective_stack
            increment = self.commitments[player] - previous_wager
            if increment + _CHIP_TOLERANCE >= self.last_full_raise_increment:
                self.last_full_raise_increment = increment
            self._current_player = opponent
            return
        target = self.custom_target(player, action)
        previous_wager = self.commitments[opponent]
        self.commitments[player] = target
        increment = target - previous_wager
        if facing_bet:
            assert increment + _CHIP_TOLERANCE >= self.last_full_raise_increment
        self.last_full_raise_increment = increment
        self._current_player = opponent

    def _action_to_string(self, player, action):
        if player == pyspiel.PlayerId.CHANCE:
            oop_card, ip_card = self.get_game().deal_from_action(action)
            return f"DealOOP{oop_card}IP{ip_card}"
        action = int(action)
        if action >= FIRST_CUSTOM_ACTION:
            prefix = "Raise" if self._amount_to_call(player) > _CHIP_TOLERANCE else "Bet"
            return f"{prefix} {fraction_label(self.get_game().fraction_for_action(action))}"
        base_action = Action(action)
        if base_action == Action.ALL_IN and self._amount_to_call(player) > _CHIP_TOLERANCE:
            return "Raise all-in"
        return {
            Action.CHECK: "Check",
            Action.FOLD: "Fold",
            Action.CALL: "Call",
            Action.ALL_IN: "AllIn",
        }[base_action]

    def is_terminal(self):
        return self._terminal

    def returns(self):
        if not self._terminal:
            return [0.0, 0.0]
        if self._folder is not None:
            winner = 1 - self._folder
            matched = self.commitments[self._folder]
            result = [-matched, -matched]
            result[winner] = INITIAL_POT + matched
            return result
        assert math.isclose(
            self.commitments[PLAYER_IP],
            self.commitments[PLAYER_OOP],
            rel_tol=1e-12,
            abs_tol=_CHIP_TOLERANCE,
        )
        ip_card = self.private_cards[PLAYER_IP]
        oop_card = self.private_cards[PLAYER_OOP]
        assert ip_card is not None and oop_card is not None
        if ip_card == oop_card:
            return [INITIAL_POT / 2.0, INITIAL_POT / 2.0]
        matched = self.commitments[PLAYER_IP]
        winner = PLAYER_IP if ip_card > oop_card else PLAYER_OOP
        result = [-matched, -matched]
        result[winner] = INITIAL_POT + matched
        return result

    def information_state_string(self, player=None):
        if player is None:
            player = self.current_player()
        if player not in (PLAYER_IP, PLAYER_OOP):
            raise ValueError(f"No information state for player {player}")
        card = self.private_cards[player]
        history = "-".join(self.history_tokens) or "ROOT"
        return f"P{player}|{card}|{history}"

    def observation_string(self, player):
        return self.information_state_string(player)

    def __str__(self):
        cards = f"IP:{self.private_cards[PLAYER_IP]}|OOP:{self.private_cards[PLAYER_OOP]}"
        history = "-".join(self.history_tokens) or "ROOT"
        return f"{cards}|{history}|pot={self.pot:.6g}|committed={self.commitments}"


class StringObserver:
    def __init__(self, iig_obs_type):
        self.iig_obs_type = iig_obs_type
        self.tensor = None
        self.dict = {}

    def set_from(self, state, player):
        del state, player

    def string_from(self, state, player):
        return state.information_state_string(player)
