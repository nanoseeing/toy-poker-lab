"""Tests for publishing lightweight browsable result bundles."""

from __future__ import annotations

import json
from pathlib import Path

from toy_poker.reporting.public_results import load_result_selection, publish_results


def _analysis() -> dict:
    return {
        "game": {
            "id": "akq_allin",
            "title": "AKQ all-in toy poker",
            "player_names": ["IP", "OOP"],
            "parameters": {"oop_stack": 1.0, "ip_stack": 1.0},
            "utility_sum": 1.0,
            "rank_distribution": None,
        },
        "solver": {
            "backend": "native_efg",
            "algorithm": "cfr_plus",
            "checkpoint_evaluation_backend": "native_efg",
            "iterations": 10,
            "requested_iterations": 10,
            "completed_iterations": 10,
            "target_exploitability": 1e-5,
            "stop_reason": "max_iterations",
            "best_exploitability": 1e-4,
            "best_iteration": 10,
        },
        "summary": {
            "returns": {"IP": 0.75, "OOP": 0.25},
            "exploitability": 1e-4,
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
                "label": "OOP(K)",
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


def test_publish_results_writes_browsable_lightweight_bundle(tmp_path: Path):
    artifact_root = tmp_path / "artifacts"
    run_id = "20260101T000000000000Z_deadbeef"
    run = artifact_root / "akq_allin" / run_id
    figures = run / "figures"
    figures.mkdir(parents=True)
    for name in (
        "action_ev.png",
        "convergence.png",
        "major_strategy_probabilities.png",
        "major_strategy_tree.png",
    ):
        (figures / name).write_bytes(b"representative figure")
    (run / "analysis.json").write_text(
        json.dumps(_analysis()), encoding="utf-8"
    )
    (run / "manifest.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "config_sha256": "deadbeef",
                "git_commit": "abc123",
            }
        ),
        encoding="utf-8",
    )
    (run / "resolved_config.json").write_text("{}", encoding="utf-8")
    (run / "strategy_viewer.html").write_text("viewer", encoding="utf-8")
    (artifact_root / "akq_allin" / "latest.json").write_text(
        json.dumps({"run_id": run_id, "path": str(run)}), encoding="utf-8"
    )

    output_root = tmp_path / "public" / "results"
    stale = output_root / "akq_allin" / "stale.txt"
    stale.parent.mkdir(parents=True)
    stale.write_text("old", encoding="utf-8")
    published = publish_results(artifact_root, output_root, {"akq_allin": run_id})

    target = output_root / "akq_allin"
    assert published == [target]
    assert not stale.exists()
    assert (target / "report.html").exists()
    assert (target / "strategy_viewer.html").read_text(encoding="utf-8") == "viewer"
    assert (target / "figures" / "convergence.png").exists()
    assert (target / "summary.json").exists()
    assert (target / "resolved_config.json").exists()
    assert (target / "manifest.json").exists()
    report = (target / "report.html").read_text(encoding="utf-8")
    assert 'href="strategy_viewer.html"' in report
    assert "Data:" not in report
    index = (output_root / "index.html").read_text(encoding="utf-8")
    assert 'akq_allin/report.html' in index
    assert 'akq_allin/strategy_viewer.html' in index
    readme = (output_root / "README.md").read_text(encoding="utf-8")
    assert "toy-poker publish-results" in readme


def test_load_result_selection(tmp_path: Path):
    selection = tmp_path / "public_results.toml"
    selection.write_text(
        '[games]\nakq_allin = "20260101T000000000000Z_deadbeef"\n',
        encoding="utf-8",
    )

    assert load_result_selection(selection) == {
        "akq_allin": "20260101T000000000000Z_deadbeef"
    }
