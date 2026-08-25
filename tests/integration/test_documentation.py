"""Keep the game registry, rule documents and runnable configs in sync."""

import json
import tomllib
from pathlib import Path

from toy_poker.experiments.config import ExperimentConfig
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
        ExperimentConfig.from_toml(path)
        with path.open("rb") as handle:
            config = tomllib.load(handle)
        configured_games.add(config["game"]["id"])
        if config["game"]["id"] == "integer_range_betting":
            assert config["solver"]["backend"] in {"vectorized_range", "cpp_range"}
        else:
            assert config["solver"]["backend"] == "native_efg"
        assert config["solver"]["algorithm"] in {"cfr_plus", "dcfr"}

    registered_games = {plugin.metadata.game_id for plugin in list_games()}
    assert registered_games <= documented_games
    assert registered_games <= configured_games

    game_docs = [
        PROJECT_ROOT / "docs" / "games" / f"{game_id}.md"
        for game_id in registered_games
    ]
    game_docs.append(PROJECT_ROOT / "docs" / "games" / "_template.md")
    for path in game_docs:
        document = path.read_text(encoding="utf-8")
        assert "## 概要" not in document
        assert "## ルール概要" in document
        assert "## toyゲームの目的" in document
        assert document.index("## ルール概要") < document.index("## toyゲームの目的")

    for game_id in registered_games:
        standard_path = (
            PROJECT_ROOT / "configs" / "experiments" / f"{game_id}_cfr_plus.toml"
        )
        assert standard_path.exists()
        with standard_path.open("rb") as handle:
            standard = tomllib.load(handle)
        solver = standard["solver"]
        assert solver["iterations"] == 10_000
        assert solver["snapshot_every"] == 1_000
        assert solver["early_stopping"] is True
        assert solver["target_exploitability"] == 1e-5
        assert solver["min_iterations"] == 1_000
        assert solver["patience_checkpoints"] == 2


def test_every_registered_game_has_a_pinned_public_result():
    selection_path = PROJECT_ROOT / "configs" / "public_results.toml"
    with selection_path.open("rb") as handle:
        selections = tomllib.load(handle)["games"]

    registered_games = {plugin.metadata.game_id for plugin in list_games()}
    assert set(selections) == registered_games
    for game_id in registered_games:
        result_directory = PROJECT_ROOT / "public" / "results" / game_id
        assert (result_directory / "report.md").exists()
        assert (result_directory / "report.html").exists()
        summary_path = result_directory / "summary.json"
        assert summary_path.exists()
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        assert summary["source"]["run_id"] == selections[game_id]

    assert (
        PROJECT_ROOT
        / "public"
        / "results"
        / "integer_range_betting"
        / "strategy_viewer.html"
    ).exists()
