"""AKQJ all-in game: OOP holds K and IP receives A, Q or J equally."""

from __future__ import annotations

import enum

import pyspiel

from toy_poker.games.fixed_oop_allin import (
    Action,
    FixedOOPAllInGame,
    FixedOOPAllInState,
    PLAYER_IP,
    PLAYER_OOP,
    make_game_type,
)


class IPCard(enum.IntEnum):
    JACK = 0
    QUEEN = 1
    ACE = 2


_GAME_TYPE = make_game_type("python_akqj_allin", "AKQJ all-in toy poker")


class AKQJGame(FixedOOPAllInGame):
    def __init__(self, params=None):
        super().__init__(
            game_type=_GAME_TYPE,
            ip_cards=tuple(IPCard),
            ip_winning_cards=(IPCard.ACE,),
            oop_card_label="K",
            params=params,
        )


AKQJState = FixedOOPAllInState

pyspiel.register_game(_GAME_TYPE, AKQJGame)
