"""Configuration-to-artifact integration test."""

import json
from pathlib import Path

import pytest

from toy_poker.experiments.config import AnalysisConfig, ExperimentConfig
from toy_poker.experiments.runner import rerender_artifact, run_experiment
from toy_poker.solvers import SolverConfig


@pytest.mark.parametrize(
    ("game_id", "policy_key", "label", "expected_analytic"),
    [
        ("akq_allin", "P1|K|ROOT", "OOP(K)", [1.0 / 3.0, -1.0 / 3.0]),
        ("akqj_allin", "P0|J|CHECK", "IP(J)", [1.0 / 18.0, -1.0 / 18.0]),
        ("akqj_two_street", "P1|K|S1:ROOT", "OOP(K)", None),
    ],
)
def test_experiment_writes_replayable_bundle(
    tmp_path: Path, game_id, policy_key, label, expected_analytic
):
    output = tmp_path / game_id
    config = ExperimentConfig(
        name="integration",
        game_id=game_id,
        game_params={"oop_stack": 2.0, "ip_stack": 3.0},
        solver=SolverConfig(iterations=200, snapshot_every=100),
        analysis=AnalysisConfig(),
        artifact_root=tmp_path / "artifacts",
    )
    result = run_experiment(config, output_directory=output)
    expected = {
        "manifest.json", "resolved_config.json", "policy.json", "policy.csv",
        "analysis.json", "information_sets.csv", "terminal_paths.csv",
        "convergence.csv", "report.html",
    }
    assert expected.issubset({path.name for path in output.iterdir()})
    assert (output / "figures" / "strategy_tree.png").exists()
    assert result.analysis["game"]["player_names"] == ["IP", "OOP"]
    assert result.analysis["game"]["parameters"]["initial_pot"] == 1.0
    assert result.analysis["game"]["analytic_returns"] == expected_analytic
    policy_data = json.loads((output / "policy.json").read_text(encoding="utf-8"))
    assert policy_key in policy_data
    rerender_artifact(output)
    assert label in (output / "report.html").read_text(encoding="utf-8")
