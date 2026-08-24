"""Keep the game registry, rule documents and runnable configs in sync."""

import tomllib
from pathlib import Path

from toy_poker.games import list_games


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_every_registered_game_has_documentation_and_standard_config():
    documented_games = {
        path.stem
        for path in (PROJECT_ROOT / "docs" / "games").glob("*.md")
        if not path.name.startswith("_") and path.name != "README.md"
    }
    configured_games = set()
    for path in (PROJECT_ROOT / "configs" / "experiments").glob("*.toml"):
        with path.open("rb") as handle:
            configured_games.add(tomllib.load(handle)["game"]["id"])

    registered_games = {plugin.metadata.game_id for plugin in list_games()}
    assert registered_games <= documented_games
    assert registered_games <= configured_games
