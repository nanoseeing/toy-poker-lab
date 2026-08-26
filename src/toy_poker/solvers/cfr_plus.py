"""Adapter for OpenSpiel's compiled C++ CFR+ solver."""

from __future__ import annotations

import math
import time

import pyspiel

from toy_poker.analysis.evaluator import expected_returns
from toy_poker.solvers.native_efg import compile_to_native_efg
from toy_poker.solvers.policy import clone_policy
from toy_poker.solvers.result import SolveResult, SolverConfig
from toy_poker.solvers.vectorized_range import VectorizedRangeCFRPlusSolver


class CFRPlusSolverAdapter:
    solver_id = "cfr_plus"

    def solve(self, game: pyspiel.Game, config: SolverConfig) -> SolveResult:
        if config.iterations <= 0 or config.snapshot_every <= 0:
            raise ValueError("iterations and snapshot_every must be positive")
        if config.min_iterations < 0:
            raise ValueError("min_iterations cannot be negative")
        if (
            not math.isfinite(config.target_exploitability)
            or config.target_exploitability <= 0
        ):
            raise ValueError("target_exploitability must be positive and finite")
        if config.patience_checkpoints <= 0:
            raise ValueError("patience_checkpoints must be positive")
        if config.algorithm not in {"cfr_plus", "dcfr"}:
            raise ValueError(f"Unsupported algorithm: {config.algorithm}")
        if not all(
            math.isfinite(value)
            for value in (config.dcfr_alpha, config.dcfr_beta, config.dcfr_gamma)
        ):
            raise ValueError("DCFR exponents must be finite")
        if config.precision not in {"float64", "float32"}:
            raise ValueError(f"Unsupported precision: {config.precision}")
        if config.node_locks and config.backend not in {
            "vectorized_range",
            "cpp_range",
        }:
            raise ValueError(
                "node locks are currently supported only by vectorized_range and cpp_range"
            )
        for lock in config.node_locks:
            if lock.player not in {"OOP", "IP"}:
                raise ValueError("node lock player must be 'OOP' or 'IP'")
            probabilities = [value for _, value in lock.action_probabilities]
            if (
                not probabilities
                or any(not math.isfinite(value) or value < 0 for value in probabilities)
                or not math.isclose(sum(probabilities), 1.0, abs_tol=1e-12)
            ):
                raise ValueError(
                    "node lock action probabilities must be finite, nonnegative, and sum to 1"
                )
        if config.backend == "vectorized_range":
            return VectorizedRangeCFRPlusSolver().solve(game, config)
        if config.backend == "cpp_range":
            from toy_poker.solvers.cpp_range import CppRangeSolver

            return CppRangeSolver().solve(game, config)
        if config.algorithm != "cfr_plus":
            raise ValueError(
                f"Algorithm {config.algorithm!r} is not supported by {config.backend!r}"
            )
        if config.backend == "native_efg":
            compiled = compile_to_native_efg(game)
            solver_game = compiled.game
            translate_policy = compiled.translate_policy

            def evaluate_snapshot(policy):
                return (
                    pyspiel.exploitability(solver_game, policy),
                    list(
                        pyspiel.expected_returns(
                            solver_game.new_initial_state(), policy, -1, True
                        )
                    ),
                )

        elif config.backend == "python_game":
            solver_game = game

            def translate_policy(policy):
                return clone_policy(game, policy)

            def evaluate_snapshot(policy):
                source_policy, _ = translate_policy(policy)
                return (
                    pyspiel.exploitability(game, source_policy),
                    expected_returns(game, source_policy),
                )

        else:
            raise ValueError(f"Unsupported CFR+ backend: {config.backend}")
        solver = pyspiel.CFRPlusSolver(solver_game)
        convergence = []
        consecutive_hits = 0
        completed_iterations = 0
        early_stopped = False
        stop_reason = "max_iterations"
        started = time.perf_counter()
        for iteration in range(1, config.iterations + 1):
            solver.evaluate_and_update_policy()
            completed_iterations = iteration
            if iteration % config.snapshot_every == 0 or iteration == config.iterations:
                gap, returns = evaluate_snapshot(solver.average_policy())
                convergence.append(
                    {
                        "iteration": iteration,
                        "exploitability": gap,
                        "returns": returns,
                    }
                )
                if (
                    iteration >= config.min_iterations
                    and gap <= config.target_exploitability
                ):
                    consecutive_hits += 1
                else:
                    consecutive_hits = 0
                if config.early_stopping and consecutive_hits >= config.patience_checkpoints:
                    early_stopped = True
                    stop_reason = "target_exploitability"
                    break
        elapsed = time.perf_counter() - started
        policy, table = translate_policy(solver.average_policy())
        best_checkpoint = min(convergence, key=lambda row: row["exploitability"])
        return SolveResult(
            policy=policy,
            policy_table=table,
            convergence=convergence,
            elapsed_seconds=elapsed,
            checkpoint_evaluation_backend=config.backend,
            completed_iterations=completed_iterations,
            early_stopped=early_stopped,
            stop_reason=stop_reason,
            best_exploitability=float(best_checkpoint["exploitability"]),
            best_iteration=int(best_checkpoint["iteration"]),
        )
