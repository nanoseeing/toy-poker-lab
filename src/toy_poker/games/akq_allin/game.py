"""AKQ all-in game: OOP holds K and IP receives A or Q equally."""

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
    QUEEN = 0
    ACE = 1


_GAME_TYPE = make_game_type("python_akq_allin", "AKQ all-in toy poker")


class AKQGame(FixedOOPAllInGame):
    def __init__(self, params=None):
        super().__init__(
            game_type=_GAME_TYPE,
            ip_cards=tuple(IPCard),
            ip_winning_cards=(IPCard.ACE,),
            oop_card_label="K",
            params=params,
        )


AKQState = FixedOOPAllInState

__all__ = ["Action", "AKQGame", "AKQState", "IPCard", "PLAYER_IP", "PLAYER_OOP"]

pyspiel.register_game(_GAME_TYPE, AKQGame)
