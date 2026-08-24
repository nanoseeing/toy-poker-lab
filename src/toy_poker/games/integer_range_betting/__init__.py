"""Integer 1-10 custom-size betting game plugin."""

from toy_poker.games.integer_range_betting.game import (
    Action,
    FIRST_CUSTOM_ACTION,
    IntegerRangeBettingGame,
    IntegerRangeBettingState,
    PLAYER_IP,
    PLAYER_OOP,
)
from toy_poker.games.integer_range_betting.plugin import PLUGIN

__all__ = [
    "Action",
    "FIRST_CUSTOM_ACTION",
    "IntegerRangeBettingGame",
    "IntegerRangeBettingState",
    "PLAYER_IP",
    "PLAYER_OOP",
    "PLUGIN",
]
