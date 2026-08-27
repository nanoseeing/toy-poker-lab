"""Two-street extension of the independent integer-range betting game."""

from __future__ import annotations

from toy_poker.games.fixed_range_one_street import (
    _CHIP_TOLERANCE,
    Action,
    FixedRangeOneStreetGame,
    FixedRangeOneStreetState,
    PLAYER_IP,
    PLAYER_OOP,
)


class FixedRangeTwoStreetGame(FixedRangeOneStreetGame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, num_streets=2)

    def new_initial_state(self):
        return FixedRangeTwoStreetState(self)


class FixedRangeTwoStreetState(FixedRangeOneStreetState):
    def __init__(self, game: FixedRangeTwoStreetGame):
        super().__init__(game)
        self.street = 0

    def _advance_street(self) -> None:
        self.street += 1
        if self.street >= self.get_game().num_streets:
            raise AssertionError("cannot advance beyond the final street")
        self.history_tokens.append(f"STREET_{self.street + 1}")
        self.last_full_raise_increment = 0.0
        self._current_player = PLAYER_OOP

    def _apply_action(self, action):
        if self.is_chance_node():
            return super()._apply_action(action)
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
            if self._opponent_is_all_in(player) or self.street == self.get_game().num_streets - 1:
                self._terminal = True
            else:
                self._advance_street()
            return
        if action == Action.CHECK:
            if player == PLAYER_IP:
                if self.street == self.get_game().num_streets - 1:
                    self._terminal = True
                else:
                    self._advance_street()
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
