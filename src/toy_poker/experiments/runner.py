"""End-to-end experiment orchestration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pyspiel

from toy_poker.analysis import analyze_information_sets, expected_returns, terminal_paths
from toy_poker.experiments.artifacts import manifest, new_run_directory, write_latest_pointer
from toy_poker.experiments.config import ExperimentConfig
from toy_poker.games import get_game
from toy_poker.solvers import CFRPlusSolverAdapter
from toy_poker.solvers.policy import save_policy


@dataclass
class RunResult:
    directory: Path
    analysis: dict


def _solver(solver_id: str):
    if solver_id == "cfr_plus":
        return CFRPlusSolverAdapter()
    raise ValueError(f"Unsupported solver: {solver_id}")


def run_experiment(
    config: ExperimentConfig,
    output_directory: Path | None = None,
    update_latest: bool = True,
) -> RunResult:
    config.validate()
    plugin = get_game(config.game_id)
    game = plugin.load_game(config.game_params)
    solver_result = _solver(config.solver.solver_id).solve(game, config.solver)
    policy = solver_result.policy
    returns = expected_returns(game, policy)
    gap = pyspiel.exploitability(game, policy)
    infos = analyze_information_sets(
        game, policy, plugin, off_path_threshold=config.analysis.off_path_threshold
    )
    paths = terminal_paths(game, policy, plugin)
    reference_returns = plugin.analytic_returns(game)
    analysis = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "game": {
            "id": plugin.metadata.game_id,
            "open_spiel_name": plugin.metadata.open_spiel_name,
            "title": plugin.metadata.title,
            "player_names": list(plugin.metadata.player_names),
            "utility_unit": plugin.metadata.utility_unit,
            "parameters": plugin.metadata.parameters | config.game_params,
            "analytic_returns": list(reference_returns) if reference_returns is not None else None,
        },
        "solver": {
            "id": config.solver.solver_id,
            "name": "OpenSpiel C++ CFRPlusSolver",
            "backend": config.solver.backend,
            "iterations": config.solver.iterations,
            "snapshot_every": config.solver.snapshot_every,
            "elapsed_seconds": solver_result.elapsed_seconds,
        },
        "summary": {
            "returns": {
                plugin.player_name(player): value for player, value in enumerate(returns)
            },
            "exploitability": gap,
            "nash_conv": gap * game.num_players(),
        },
        "reporting": {
            "major_reach_threshold": config.analysis.major_reach_threshold,
        },
        "information_sets": infos,
        "terminal_paths": paths,
        "convergence": solver_result.convergence,
    }
    if output_directory is None:
        directory, run_id = new_run_directory(config)
    else:
        directory = output_directory
        directory.mkdir(parents=True, exist_ok=True)
        run_id = directory.name
    (directory / "resolved_config.json").write_text(
        json.dumps(config.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
    )
    save_policy(directory, solver_result.policy_table)
    from toy_poker.reporting import write_report_bundle

    write_report_bundle(directory, analysis, game, policy, plugin)
    (directory / "manifest.json").write_text(
        json.dumps(
            manifest(config, run_id, solver_result.elapsed_seconds),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    if output_directory is None and update_latest:
        write_latest_pointer(config, directory, run_id)
    return RunResult(directory=directory, analysis=analysis)


def rerender_artifact(directory: Path) -> None:
    config_data = json.loads((directory / "resolved_config.json").read_text(encoding="utf-8"))
    config = ExperimentConfig(
        name=config_data["name"],
        game_id=config_data["game_id"],
        game_params=config_data["game_params"],
        artifact_root=Path(config_data["artifact_root"]),
    )
    plugin = get_game(config.game_id)
    game = plugin.load_game(config.game_params)
    from toy_poker.solvers.policy import load_policy

    policy, _ = load_policy(directory / "policy.json")
    analysis = json.loads((directory / "analysis.json").read_text(encoding="utf-8"))
    from toy_poker.reporting import write_report_bundle

    write_report_bundle(directory, analysis, game, policy, plugin)
