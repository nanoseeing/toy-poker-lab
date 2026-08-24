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
            config = tomllib.load(handle)
        configured_games.add(config["game"]["id"])
        if config["game"]["id"] == "integer_range_betting":
            assert config["solver"]["backend"] in {"vectorized_range", "cpp_range"}
        else:
            assert config["solver"]["backend"] == "native_efg"
        assert config["solver"]["algorithm"] in {"cfr_plus", "dcfr"}
        assert config["solver"]["iterations"] == 10_000
        assert config["solver"]["snapshot_every"] == 1_000
        assert config["solver"]["early_stopping"] is True
        assert config["solver"]["target_exploitability"] == 1e-5
        assert config["solver"]["min_iterations"] == 1_000
        assert config["solver"]["patience_checkpoints"] == 2

    registered_games = {plugin.metadata.game_id for plugin in list_games()}
    assert registered_games <= documented_games
    assert registered_games <= configured_games
