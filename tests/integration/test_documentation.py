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
        document_path = (
            PROJECT_ROOT / "docs" / "studies" / selection["document"]
        )
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
        "study_01_game_theory_basics.md",
        "study_02_poker_terms_and_math.md",
        "study_03_akq_01_polar_bet.md",
        "study_04_akq_02_polar_bet_sizing.md",
        "study_05_akq_03_position_and_check.md",
        "study_06_akq_04_ip_bet_sizing.md",
        "study_07_akq_05_bet_raise_strategy.md",
        "study_08_akqj_01_two_street_bluff.md",
        "study_09_akqj_02_geometric_bet.md",
        "study_10_akqj_03_multi_street_generalization.md",
        "study_11_akq_06_two_street_strategy.md",
        "study_12_01_game_01_oop_bet_strategy.md",
        "study_13_01_game_02_two_street_strategy.md",
    ]
    assert [path.name for path in sorted(studies_root.glob("study_*.md"))] == (
        ordered_documents
    )
    positions = [curriculum.index(f"({name})") for name in ordered_documents]
    assert positions == sorted(positions)

    game_studies = ordered_documents[2:]
    for name in game_studies:
        document = (studies_root / name).read_text(encoding="utf-8")
        assert "Status" not in document
        major_sections = [
            "## ルール",
            "## 最適戦略",
            "## ポーカーにおける概念理解",
            "## Solverによる再現結果",
        ]
        major_positions = [document.index(section) for section in major_sections]
        assert major_positions == sorted(major_positions)
        assert "### 均衡戦略" in document
        assert "### EV" in document
        assert "### 導出方法" in document
        assert document.count("\n---\n") >= 3

        rules = document.split("## ルール", maxsplit=1)[1].split("## ", maxsplit=1)[0]
        assert "| 項目 | 内容 |" in rules
        required_rows = [
            "| OOPハンド |",
            "| IPハンド |",
            "| Street |",
            "| 初期Pot |",
            "| 有効Stack |",
            "| 許可アクション |",
            "| 勝敗判定 |",
            "| 利得計算方法 |",
        ]
        positions = [rules.index(row) for row in required_rows]
        assert positions == sorted(positions)
        assert "標準minimum raise" not in rules

        solver_section = document.split(
            "## Solverによる再現結果", maxsplit=1
        )[1].split("\n---\n", maxsplit=1)[0]
        if "| 指標 | 結果 |" in solver_section:
            result_table = solver_section.split("| 指標 | 結果 |", maxsplit=1)[
                1
            ].strip().split("\n\n", maxsplit=1)[0]
            result_rows = [
                line
                for line in result_table.splitlines()
                if line.startswith("|") and not line.startswith("|---")
            ]
            assert [row.split("|", maxsplit=2)[1].strip() for row in result_rows] == [
                "IP EV",
                "OOP EV",
                "Exploitability",
            ]

    template = (studies_root / "zz_template.md").read_text(encoding="utf-8")
    assert "Status" not in template
    assert template.count("\n---\n") == 4

    for path in studies_root.glob("*.md"):
        document = path.read_text(encoding="utf-8")
        assert re.search(r"\butility\b|\bterminal\b", document, re.IGNORECASE) is None
