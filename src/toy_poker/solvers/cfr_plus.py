"""Adapter for OpenSpiel's compiled C++ CFR+ solver."""

from __future__ import annotations

import time

import pyspiel

from toy_poker.analysis.evaluator import expected_returns
from toy_poker.solvers.native_efg import compile_to_native_efg
from toy_poker.solvers.policy import clone_policy
from toy_poker.solvers.result import SolveResult, SolverConfig


class CFRPlusSolverAdapter:
    solver_id = "cfr_plus"

    def solve(self, game: pyspiel.Game, config: SolverConfig) -> SolveResult:
        if config.iterations <= 0 or config.snapshot_every <= 0:
            raise ValueError("iterations and snapshot_every must be positive")
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
            translate_policy = lambda policy: clone_policy(game, policy)

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
        started = time.perf_counter()
        for iteration in range(1, config.iterations + 1):
            solver.evaluate_and_update_policy()
            if iteration % config.snapshot_every == 0 or iteration == config.iterations:
                gap, returns = evaluate_snapshot(solver.average_policy())
                convergence.append(
                    {
                        "iteration": iteration,
                        "exploitability": gap,
                        "returns": returns,
                    }
                )
        elapsed = time.perf_counter() - started
        policy, table = translate_policy(solver.average_policy())
        return SolveResult(
            policy=policy,
            policy_table=table,
            convergence=convergence,
            elapsed_seconds=elapsed,
            checkpoint_evaluation_backend=config.backend,
        )
