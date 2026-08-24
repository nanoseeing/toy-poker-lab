"""Artifact-free solver benchmarks."""

from __future__ import annotations

import statistics
import time
from dataclasses import replace
from pathlib import Path

from toy_poker.experiments.config import ExperimentConfig
from toy_poker.experiments.runner import _solver
from toy_poker.games import get_game


def benchmark_experiment(
    config_path: Path,
    *,
    iterations: int | None = None,
    repeat: int = 1,
) -> dict:
    """Run only the solver and return machine-readable timing statistics."""
    if repeat <= 0:
        raise ValueError("repeat must be positive")
    config = ExperimentConfig.from_toml(config_path)
    solver_config = replace(
        config.solver,
        iterations=iterations or config.solver.iterations,
        early_stopping=False,
    )
    if solver_config.iterations <= 0:
        raise ValueError("iterations must be positive")
    plugin = get_game(config.game_id)
    samples = []
    for _ in range(repeat):
        game = plugin.load_game(config.game_params)
        started = time.perf_counter()
        result = _solver(solver_config.solver_id).solve(game, solver_config)
        wall_seconds = time.perf_counter() - started
        samples.append(
            {
                "elapsed_seconds": result.elapsed_seconds,
                "wall_seconds": wall_seconds,
                "seconds_per_iteration": (
                    result.elapsed_seconds / result.completed_iterations
                ),
                "exploitability": result.convergence[-1]["exploitability"],
                "returns": result.convergence[-1]["returns"],
                "policy_information_sets": len(result.policy_table),
            }
        )
    elapsed = [sample["elapsed_seconds"] for sample in samples]
    wall = [sample["wall_seconds"] for sample in samples]
    per_iteration = [sample["seconds_per_iteration"] for sample in samples]
    return {
        "game_id": config.game_id,
        "game_params": config.game_params,
        "solver": {
            "id": solver_config.solver_id,
            "backend": solver_config.backend,
            "algorithm": solver_config.algorithm,
            "precision": solver_config.precision,
            "iterations": solver_config.iterations,
            "repeat": repeat,
        },
        "summary": {
            "median_elapsed_seconds": statistics.median(elapsed),
            "min_elapsed_seconds": min(elapsed),
            "median_wall_seconds": statistics.median(wall),
            "median_seconds_per_iteration": statistics.median(per_iteration),
            "median_iterations_per_second": 1.0 / statistics.median(per_iteration),
        },
        "samples": samples,
    }
