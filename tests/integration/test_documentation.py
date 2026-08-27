"""Keep the game registry, rule documents and runnable configs in sync."""

import json
import re
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
        if config["game"]["id"] in {
            "integer_range_betting",
            "integer_range_betting_two_street",
        }:
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


def test_every_pinned_study_has_documentation_and_public_result():
    selection_path = PROJECT_ROOT / "configs" / "public_studies.toml"
    with selection_path.open("rb") as handle:
        studies = tomllib.load(handle)["studies"]

    assert studies
    for study_id, selection in studies.items():
        document_path = PROJECT_ROOT / "docs" / "studies" / f"{study_id}.md"
        assert document_path.exists()
        document = document_path.read_text(encoding="utf-8")
        assert "## ルール" in document
        assert "Solver" in document

        result_directory = PROJECT_ROOT / "public" / "studies" / study_id
        assert (result_directory / "report.md").exists()
        assert (result_directory / "report.html").exists()
        assert (result_directory / "figures" / "root_strategy.png").exists()
        summary = json.loads(
            (result_directory / "summary.json").read_text(encoding="utf-8")
        )
        assert summary["study_id"] == study_id
        assert summary["game"]["id"] == selection["game_id"]
        assert summary["source"]["run_id"] == selection["run_id"]


def test_study_curriculum_and_rule_tables_are_structured():
    studies_root = PROJECT_ROOT / "docs" / "studies"
    curriculum = (studies_root / "README.md").read_text(encoding="utf-8")
    ordered_documents = [
        "game_theory_basics.md",
        "concepts.md",
        "akq_k_vs_aq_allin.md",
        "akq_k_vs_aq_variable_size.md",
        "akq_symmetric_allin.md",
        "akq_symmetric_ip_betting.md",
        "akq_symmetric_variable_size.md",
        "akqj_two_street_pot.md",
        "akqj_two_street_variable_size.md",
        "polar_multi_street_generalization.md",
        "akq_symmetric_two_street.md",
        "zero_one_n50_one_street.md",
        "zero_one_n50_two_street.md",
    ]
    positions = [curriculum.index(f"({name})") for name in ordered_documents]
    assert positions == sorted(positions)

    game_studies = ordered_documents[2:]
    for name in game_studies:
        document = (studies_root / name).read_text(encoding="utf-8")
        rules = document.split("## ルール", maxsplit=1)[1].split("## ", maxsplit=1)[0]
        assert "| 項目 | 内容 |" in rules
        assert "| 利得 |" in rules

    for path in studies_root.glob("*.md"):
        document = path.read_text(encoding="utf-8")
        assert re.search(r"\butility\b|\bterminal\b", document, re.IGNORECASE) is None
