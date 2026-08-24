"""End-to-end experiment orchestration."""

from __future__ import annotations

import json
import gzip
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from toy_poker.analysis import analyze_information_sets, terminal_paths
from toy_poker.analysis.vectorized_range import analyze_vectorized_range
from toy_poker.experiments.artifacts import manifest, new_run_directory, write_latest_pointer
from toy_poker.experiments.config import ExperimentConfig
from toy_poker.games import get_game
from toy_poker.games.fixed_range_one_street import FixedRangeOneStreetGame
from toy_poker.solvers import CFRPlusSolverAdapter
from toy_poker.solvers.policy import save_policy, save_policy_npz


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
    final_checkpoint = solver_result.convergence[-1]
    returns = list(final_checkpoint["returns"])
    gap = float(final_checkpoint["exploitability"])
    public_tree = None
    if isinstance(game, FixedRangeOneStreetGame):
        infos, paths, public_tree = analyze_vectorized_range(
            game,
            policy,
            plugin,
            off_path_threshold=config.analysis.off_path_threshold,
        )
    else:
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
            "utility_convention": plugin.metadata.utility_convention,
            "utility_sum": game.utility_sum(),
            "parameters": plugin.resolved_parameters(game, config.game_params),
            "rank_distribution": plugin.rank_distribution(game),
            "analytic_returns": list(reference_returns) if reference_returns is not None else None,
        },
        "solver": {
            "id": config.solver.solver_id,
            "name": (
                f"Vectorized NumPy {config.solver.algorithm.upper()}"
                if config.solver.backend == "vectorized_range"
                else (
                    f"C++ range-vector {config.solver.algorithm.upper()}"
                    if config.solver.backend == "cpp_range"
                    else "OpenSpiel C++ CFRPlusSolver"
                )
            ),
            "backend": config.solver.backend,
            "algorithm": config.solver.algorithm,
            "precision": config.solver.precision,
            "checkpoint_evaluation_backend": solver_result.checkpoint_evaluation_backend,
            "iterations": solver_result.completed_iterations,
            "requested_iterations": config.solver.iterations,
            "completed_iterations": solver_result.completed_iterations,
            "snapshot_every": config.solver.snapshot_every,
            "early_stopping": config.solver.early_stopping,
            "early_stopped": solver_result.early_stopped,
            "stop_reason": solver_result.stop_reason,
            "target_exploitability": config.solver.target_exploitability,
            "min_iterations": config.solver.min_iterations,
            "patience_checkpoints": config.solver.patience_checkpoints,
            "dcfr": (
                {
                    "alpha": config.solver.dcfr_alpha,
                    "beta": config.solver.dcfr_beta,
                    "gamma": config.solver.dcfr_gamma,
                }
                if config.solver.algorithm == "dcfr"
                else None
            ),
            "best_exploitability": solver_result.best_exploitability,
            "best_iteration": solver_result.best_iteration,
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
            "report_scope": config.analysis.report_scope,
            "policy_format": config.analysis.policy_format,
            "policy_filename": (
                "policy.npz"
                if config.analysis.policy_format == "npz"
                else "policy.json"
            ),
        },
        "information_sets": infos,
        "terminal_paths": paths,
        "public_tree": public_tree,
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
    if config.analysis.policy_format == "npz":
        save_policy_npz(directory, solver_result.policy_table)
    else:
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

    policy_path = (
        directory / "policy.json"
        if (directory / "policy.json").exists()
        else directory / "policy.npz"
    )
    policy, _ = load_policy(policy_path)
    analysis_path = directory / "analysis.json"
    if analysis_path.exists():
        analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    else:
        with gzip.open(directory / "analysis.json.gz", "rt", encoding="utf-8") as handle:
            analysis = json.load(handle)
    from toy_poker.reporting import write_report_bundle

    write_report_bundle(directory, analysis, game, policy, plugin)
