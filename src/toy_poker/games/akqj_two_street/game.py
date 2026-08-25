"""Two-street AKQJ game with geometric bets and all-in raises."""

from __future__ import annotations

import enum

import pyspiel

from toy_poker.games.fixed_oop_two_street import (
    Action,
    FixedOOPTwoStreetGame,
    FixedOOPTwoStreetState,
    PLAYER_IP,
    PLAYER_OOP,
    make_game_type,
)


class IPCard(enum.IntEnum):
    JACK = 0
    QUEEN = 1
    ACE = 2


_GAME_TYPE = make_game_type(
    "python_akqj_two_street", "AKQJ two-street geometric toy poker"
)


class AKQJTwoStreetGame(FixedOOPTwoStreetGame):
    def __init__(self, params=None):
        super().__init__(
            game_type=_GAME_TYPE,
            ip_cards=tuple(IPCard),
            ip_winning_cards=(IPCard.ACE,),
            oop_card_label="K",
            params=params,
        )


AKQJTwoStreetState = FixedOOPTwoStreetState

__all__ = [
    "Action",
    "AKQJTwoStreetGame",
    "AKQJTwoStreetState",
    "IPCard",
    "PLAYER_IP",
    "PLAYER_OOP",
]

pyspiel.register_game(_GAME_TYPE, AKQJTwoStreetGame)
