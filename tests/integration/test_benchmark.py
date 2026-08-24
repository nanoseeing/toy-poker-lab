"""Tests for the artifact-free benchmark command implementation."""

from pathlib import Path

from toy_poker.experiments.benchmark import benchmark_experiment


def test_benchmark_returns_timing_without_artifacts(tmp_path: Path):
    config = tmp_path / "benchmark.toml"
    config.write_text(
        """
[experiment]
name = "benchmark"
[game]
id = "integer_range_betting"
[game.params]
num_ranks = 3
[solver]
backend = "vectorized_range"
iterations = 2
snapshot_every = 2
early_stopping = false
""",
        encoding="utf-8",
    )
    result = benchmark_experiment(config, iterations=3, repeat=2)

    assert result["solver"]["iterations"] == 3
    assert result["solver"]["repeat"] == 2
    assert len(result["samples"]) == 2
    assert result["summary"]["median_seconds_per_iteration"] > 0.0
    assert not (tmp_path / "artifacts").exists()
