"""One-street game where both players receive an integer from 1 through 10."""

from __future__ import annotations

import pyspiel

from toy_poker.games.fixed_range_one_street import (
    Action,
    FIRST_CUSTOM_ACTION,
    FixedRangeOneStreetGame,
    FixedRangeOneStreetState,
    PLAYER_IP,
    PLAYER_OOP,
    make_game_type,
)

MIN_CARD = 1
MAX_CARD = 10
DEFAULT_STACK = 4.0
DEFAULT_BET_FRACTIONS = "0.3333333333333333,1.0"

_GAME_TYPE = make_game_type(
    "python_integer_range_betting",
    "Integer 1-10 custom-size toy poker",
    default_stack=DEFAULT_STACK,
    default_bet_fractions=DEFAULT_BET_FRACTIONS,
)


class IntegerRangeBettingGame(FixedRangeOneStreetGame):
    def __init__(self, params=None):
        super().__init__(
            game_type=_GAME_TYPE,
            min_card=MIN_CARD,
            max_card=MAX_CARD,
            default_stack=DEFAULT_STACK,
            default_bet_fractions=DEFAULT_BET_FRACTIONS,
            params=params,
        )


IntegerRangeBettingState = FixedRangeOneStreetState

pyspiel.register_game(_GAME_TYPE, IntegerRangeBettingGame)
