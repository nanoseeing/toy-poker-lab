"""Explicit registry for available toy games."""

from __future__ import annotations

from toy_poker.games.base import GamePlugin

_REGISTRY: dict[str, GamePlugin] = {}
_BUILTINS_LOADED = False


def register_game(plugin: GamePlugin) -> None:
    game_id = plugin.metadata.game_id
    if game_id in _REGISTRY:
        raise ValueError(f"Game plugin already registered: {game_id}")
    _REGISTRY[game_id] = plugin


def _load_builtins() -> None:
    global _BUILTINS_LOADED
    if not _BUILTINS_LOADED:
        from toy_poker.games.akq_allin import plugin as _akq_plugin  # noqa: F401
        from toy_poker.games.akqj_allin import plugin as _akqj_plugin  # noqa: F401
        from toy_poker.games.akqj_two_street import plugin as _akqj_two_street_plugin  # noqa: F401

        _BUILTINS_LOADED = True


def get_game(game_id: str) -> GamePlugin:
    _load_builtins()
    try:
        return _REGISTRY[game_id]
    except KeyError as exc:
        available = ", ".join(sorted(_REGISTRY))
        raise KeyError(f"Unknown game {game_id!r}. Available: {available}") from exc


def list_games() -> list[GamePlugin]:
    _load_builtins()
    return [_REGISTRY[key] for key in sorted(_REGISTRY)]
