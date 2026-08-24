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
        elif config.backend == "python_game":
            solver_game = game
            translate_policy = lambda policy: clone_policy(game, policy)
        else:
            raise ValueError(f"Unsupported CFR+ backend: {config.backend}")
        solver = pyspiel.CFRPlusSolver(solver_game)
        convergence = []
        started = time.perf_counter()
        for iteration in range(1, config.iterations + 1):
            solver.evaluate_and_update_policy()
            if iteration % config.snapshot_every == 0 or iteration == config.iterations:
                snapshot_policy, _ = translate_policy(solver.average_policy())
                convergence.append(
                    {
                        "iteration": iteration,
                        "exploitability": pyspiel.exploitability(game, snapshot_policy),
                        "returns": expected_returns(game, snapshot_policy),
                    }
                )
        elapsed = time.perf_counter() - started
        policy, table = translate_policy(solver.average_policy())
        return SolveResult(
            policy=policy,
            policy_table=table,
            convergence=convergence,
            elapsed_seconds=elapsed,
        )
