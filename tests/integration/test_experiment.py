"""Configuration-to-artifact integration test."""

import json
from pathlib import Path

from toy_poker.experiments.config import AnalysisConfig, ExperimentConfig
from toy_poker.experiments.runner import rerender_artifact, run_experiment
from toy_poker.solvers import SolverConfig


def test_experiment_writes_replayable_bundle(tmp_path: Path):
    output = tmp_path / "run"
    config = ExperimentConfig(
        name="integration",
        game_id="akq_allin",
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
    policy_data = json.loads((output / "policy.json").read_text(encoding="utf-8"))
    assert "P1|A|ROOT" in policy_data
    rerender_artifact(output)
    assert "OOP(A)" in (output / "report.html").read_text(encoding="utf-8")
