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
        ("akq_allin", "P1|K|ROOT", "OOP(K)", [5.0 / 6.0, 1.0 / 6.0]),
        ("akqj_allin", "P0|J|CHECK", "IP(J)", [5.0 / 9.0, 4.0 / 9.0]),
        ("akqj_two_street", "P1|K|S1:ROOT", "OOP(K)", None),
        ("integer_range_betting", "P1|4|ROOT", "OOP(4)", None),
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
    assert (output / "figures" / "major_strategy_tree.png").exists()
    assert (output / "figures" / "major_strategy_probabilities.png").exists()
    assert result.analysis["game"]["player_names"] == ["IP", "OOP"]
    assert result.analysis["game"]["parameters"]["initial_pot"] == 1.0
    assert result.analysis["game"]["utility_sum"] == 1.0
    assert result.analysis["solver"]["checkpoint_evaluation_backend"] == "native_efg"
    assert result.analysis["solver"]["requested_iterations"] == 200
    assert result.analysis["solver"]["completed_iterations"] == 200
    assert result.analysis["solver"]["stop_reason"] == "max_iterations"
    assert result.analysis["game"]["analytic_returns"] == pytest.approx(expected_analytic)
    if game_id == "integer_range_betting":
        assert (output / "rank_distribution.csv").exists()
        assert (output / "figures" / "rank_distribution.png").exists()
        assert result.analysis["game"]["rank_distribution"]["OOP"] == pytest.approx(
            [0.1] * 10
        )
    policy_data = json.loads((output / "policy.json").read_text(encoding="utf-8"))
    assert policy_key in policy_data
    rerender_artifact(output)
    report = (output / "report.html").read_text(encoding="utf-8")
    assert label in report
    assert report.index("Major strategy") < report.index("Full analysis")


def test_compact_major_only_bundle_uses_npz_and_can_be_rerendered(tmp_path: Path):
    output = tmp_path / "compact"
    config = ExperimentConfig(
        name="compact",
        game_id="integer_range_betting",
        game_params={"num_ranks": 3},
        solver=SolverConfig(
            backend="cpp_range",
            algorithm="dcfr",
            iterations=2,
            snapshot_every=2,
            early_stopping=False,
        ),
        analysis=AnalysisConfig(report_scope="major_only", policy_format="npz"),
        artifact_root=tmp_path / "artifacts",
    )
    run_experiment(config, output_directory=output)

    assert (output / "policy.npz").exists()
    assert (output / "analysis.json.gz").exists()
    assert (output / "information_sets.csv.gz").exists()
    assert not (output / "policy.json").exists()
    assert not (output / "analysis.json").exists()
    assert not (output / "figures" / "strategy_probabilities.png").exists()
    assert (output / "figures" / "major_strategy_probabilities.png").exists()
    report = (output / "report.html").read_text(encoding="utf-8")
    assert "Full analysis" not in report
    rerender_artifact(output)
    assert (output / "report.html").exists()
