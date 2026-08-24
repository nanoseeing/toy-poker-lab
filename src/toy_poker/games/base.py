"""Metadata and extension points shared by game plugins."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pyspiel


@dataclass(frozen=True)
class GameMetadata:
    game_id: str
    open_spiel_name: str
    title: str
    player_names: tuple[str, ...]
    utility_unit: str
    utility_convention: str = "Initial pot is dead money; terminal utilities sum to it."
    information_labels: dict[str, str] = field(default_factory=dict)
    analytic_returns: tuple[float, ...] | None = None
    parameters: dict[str, Any] = field(default_factory=dict)


class GamePlugin:
    """Small presentation layer around an OpenSpiel game registration."""

    metadata: GameMetadata

    def load_game(self, params: dict[str, Any] | None = None) -> pyspiel.Game:
        return pyspiel.load_game(self.metadata.open_spiel_name, params or {})

    def player_name(self, player: int) -> str:
        return self.metadata.player_names[player]

    def information_label(self, key: str) -> str:
        return self.metadata.information_labels.get(key, key)

    def private_card(self, state: pyspiel.State, player: int) -> str:
        """Default convention used by bundled poker games: Pn|CARD|HISTORY."""
        parts = state.information_state_string(player).split("|")
        return parts[1] if len(parts) >= 3 else ""

    def information_context(self, state: pyspiel.State) -> dict[str, Any]:
        """Return optional public state data shown beside an information set."""
        del state
        return {}

    def chance_outcome_label(self, state: pyspiel.State, action: int) -> str:
        label = state.action_to_string(pyspiel.PlayerId.CHANCE, action)
        return label.removeprefix("Deal")

    def analytic_returns(self, game: pyspiel.Game) -> tuple[float, ...] | None:
        del game
        return self.metadata.analytic_returns
