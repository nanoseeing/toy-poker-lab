"""Tests for publishing multiple runs of one game as named studies."""

from __future__ import annotations

import json
from pathlib import Path

from toy_poker.reporting.public_studies import (
    StudySelection,
    load_study_selection,
    publish_studies,
)


def _analysis() -> dict:
    return {
        "game": {
            "id": "integer_range_betting",
            "title": "Integer range betting",
            "player_names": ["IP", "OOP"],
            "parameters": {"num_ranks": 3},
            "utility_sum": 1.0,
            "rank_distribution": None,
        },
        "solver": {
            "backend": "cpp_range",
            "algorithm": "dcfr",
            "iterations": 10,
            "requested_iterations": 10,
            "completed_iterations": 10,
            "target_exploitability": 1e-5,
            "stop_reason": "max_iterations",
            "best_exploitability": 1e-5,
            "best_iteration": 10,
        },
        "summary": {
            "returns": {"IP": 0.75, "OOP": 0.25},
            "exploitability": 1e-5,
        },
        "reporting": {
            "major_reach_threshold": 1e-4,
            "report_scope": "major_only",
            "policy_filename": "policy.json",
            "analysis_filename": "analysis.json",
            "information_sets_filename": "information_sets.csv",
            "terminal_paths_filename": "terminal_paths.csv",
        },
        "information_sets": [
            {
                "label": "OOP(2): start",
                "history": [],
                "reach_probability": 1.0,
                "is_off_path": False,
                "context": {},
                "policy_ev": 0.25,
                "actions": [
                    {"action": "Check", "probability": 1.0, "ev": 0.25}
                ],
            }
        ],
    }


def test_publish_studies_uses_study_id_as_target(tmp_path: Path):
    artifact_root = tmp_path / "artifacts"
    run_id = "run1"
    source = artifact_root / "integer_range_betting" / run_id
    (source / "figures").mkdir(parents=True)
    (source / "analysis.json").write_text(json.dumps(_analysis()), encoding="utf-8")
    (source / "manifest.json").write_text(
        json.dumps({"run_id": run_id}), encoding="utf-8"
    )
    (source / "resolved_config.json").write_text("{}", encoding="utf-8")
    (source / "strategy_viewer.html").write_text("viewer", encoding="utf-8")

    output = tmp_path / "public" / "studies"
    published = publish_studies(
        artifact_root,
        output,
        [StudySelection("akq-example", "integer_range_betting", run_id)],
    )

    target = output / "akq-example"
    assert published == [target]
    assert (target / "figures" / "root_strategy.png").exists()
    assert (target / "report.md").exists()
    assert (target / "strategy_viewer.html").read_text(encoding="utf-8") == "viewer"
    assert json.loads((target / "summary.json").read_text())["study_id"] == "akq-example"
    assert "akq-example/report.md" in (output / "README.md").read_text()


def test_load_study_selection(tmp_path: Path):
    path = tmp_path / "studies.toml"
    path.write_text(
        '[studies.example]\ngame_id="integer_range_betting"\nrun_id="run1"\n',
        encoding="utf-8",
    )

    assert load_study_selection(path) == [
        StudySelection("example", "integer_range_betting", "run1")
    ]
