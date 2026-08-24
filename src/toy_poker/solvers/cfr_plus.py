"""Adapter for OpenSpiel's compiled C++ CFR+ solver."""

from __future__ import annotations

import time

import pyspiel

from toy_poker.analysis.evaluator import expected_returns
from toy_poker.solvers.policy import clone_policy
from toy_poker.solvers.result import SolveResult, SolverConfig


class CFRPlusSolverAdapter:
    solver_id = "cfr_plus"

    def solve(self, game: pyspiel.Game, config: SolverConfig) -> SolveResult:
        if config.iterations <= 0 or config.snapshot_every <= 0:
            raise ValueError("iterations and snapshot_every must be positive")
        solver = pyspiel.CFRPlusSolver(game)
        convergence = []
        started = time.perf_counter()
        for iteration in range(1, config.iterations + 1):
            solver.evaluate_and_update_policy()
            if iteration % config.snapshot_every == 0 or iteration == config.iterations:
                snapshot_policy, _ = clone_policy(game, solver.average_policy())
                convergence.append(
                    {
                        "iteration": iteration,
                        "exploitability": pyspiel.exploitability(game, snapshot_policy),
                        "returns": expected_returns(game, snapshot_policy),
                    }
                )
        elapsed = time.perf_counter() - started
        policy, table = clone_policy(game, solver.average_policy())
        return SolveResult(
            policy=policy,
            policy_table=table,
            convergence=convergence,
            elapsed_seconds=elapsed,
        )
