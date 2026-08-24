"""AKQ all-in toy poker implemented as an OpenSpiel Python game.

Player 1 is OOP and always holds K. Player 0 is IP and receives A or Q with
equal probability. OOP acts first. With no outstanding bet, legal actions are
check and all-in. Facing an all-in, legal actions are fold and all-in, where
the latter means call. The pot is fixed at one chip. Stacks are independently
configurable and unmatched excess is returned, so the wager at risk is the
effective stack: min(oop_stack, ip_stack).
"""

from __future__ import annotations

import enum

import pyspiel


class Action(enum.IntEnum):
    CHECK = 0
    ALL_IN = 1
    FOLD = 2


class IPCard(enum.IntEnum):
    QUEEN = 0
    ACE = 1


PLAYER_IP = 0
PLAYER_OOP = 1
_NUM_PLAYERS = 2

_GAME_TYPE = pyspiel.GameType(
    short_name="python_akq_allin",
    long_name="AKQ all-in toy poker",
    dynamics=pyspiel.GameType.Dynamics.SEQUENTIAL,
    chance_mode=pyspiel.GameType.ChanceMode.EXPLICIT_STOCHASTIC,
    information=pyspiel.GameType.Information.IMPERFECT_INFORMATION,
    utility=pyspiel.GameType.Utility.ZERO_SUM,
    reward_model=pyspiel.GameType.RewardModel.TERMINAL,
    max_num_players=_NUM_PLAYERS,
    min_num_players=_NUM_PLAYERS,
    provides_information_state_string=True,
    provides_information_state_tensor=False,
    provides_observation_string=True,
    provides_observation_tensor=False,
    parameter_specification={"oop_stack": 1.0, "ip_stack": 1.0},
)


class AKQGame(pyspiel.Game):
    def __init__(self, params=None):
        params = params or {}
        self.oop_stack = float(params.get("oop_stack", 1.0))
        self.ip_stack = float(params.get("ip_stack", 1.0))
        if self.oop_stack <= 0 or self.ip_stack <= 0:
            raise ValueError("oop_stack and ip_stack must both be positive")
        self.effective_stack = min(self.oop_stack, self.ip_stack)
        all_in_payoff = 0.5 + self.effective_stack
        game_info = pyspiel.GameInfo(
            num_distinct_actions=len(Action),
            max_chance_outcomes=len(IPCard),
            num_players=_NUM_PLAYERS,
            min_utility=-all_in_payoff,
            max_utility=all_in_payoff,
            utility_sum=0.0,
            max_game_length=3,
        )
        super().__init__(_GAME_TYPE, game_info, params)

    def new_initial_state(self):
        return AKQState(self)

    def make_py_observer(self, iig_obs_type=None, params=None):
        if params:
            raise ValueError(f"Observation parameters are unsupported: {params}")
        return AKQObserver(iig_obs_type or pyspiel.IIGObservationType(perfect_recall=True))


class AKQState(pyspiel.State):
    def __init__(self, game):
        super().__init__(game)
        self.ip_card: IPCard | None = None
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
        return [(int(IPCard.QUEEN), 0.5), (int(IPCard.ACE), 0.5)]

    def _apply_action(self, action):
        if self.is_chance_node():
            self.ip_card = IPCard(action)
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
            return "DealQ" if action == int(IPCard.QUEEN) else "DealA"
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
            result = [-0.5, -0.5]
            result[winner] = 0.5
            return result
        payoff = (
            0.5 + self.get_game().effective_stack
            if self.history.count(Action.ALL_IN) == 2
            else 0.5
        )
        assert self.ip_card is not None
        winner = PLAYER_IP if self.ip_card == IPCard.ACE else PLAYER_OOP
        result = [-payoff, -payoff]
        result[winner] = payoff
        return result

    def information_state_string(self, player=None):
        if player is None:
            player = self.current_player()
        if player not in (PLAYER_IP, PLAYER_OOP):
            raise ValueError(f"No information state for player {player}")
        private_card = "K" if player == PLAYER_OOP else self.ip_card.name[0]
        public_history = "-".join(action.name for action in self.history) or "ROOT"
        return f"P{player}|{private_card}|{public_history}"

    def observation_string(self, player):
        return self.information_state_string(player)

    def __str__(self):
        card = "?" if self.ip_card is None else self.ip_card.name[0]
        actions = "-".join(action.name for action in self.history) or "ROOT"
        return f"IP:{card}|{actions}"


class AKQObserver:
    def __init__(self, iig_obs_type):
        self.iig_obs_type = iig_obs_type
        self.tensor = None
        self.dict = {}

    def set_from(self, state, player):
        del state, player

    def string_from(self, state, player):
        return state.information_state_string(player)


pyspiel.register_game(_GAME_TYPE, AKQGame)
