"""Python adapter for the compiled flat range solver."""

from __future__ import annotations

import time

import numpy as np
import pyspiel

from toy_poker.games.fixed_range_one_street import FixedRangeOneStreetGame
from toy_poker.solvers.flat_range import FlatPublicTree, flatten_public_tree
from toy_poker.solvers.policy import standalone_policy
from toy_poker.solvers.result import SolveResult, SolverConfig
from toy_poker.solvers.vectorized_range import (
    VectorizedRangeCFRPlusSolver,
    VectorizedRangeEvaluator,
)


class CppRangeSolver:
    """C++20 CFR+/DCFR kernel over a compiled public tree and rank vectors."""

    backend = "cpp_range"

    def solve(self, game: pyspiel.Game, config: SolverConfig) -> SolveResult:
        if not isinstance(game, FixedRangeOneStreetGame):
            raise ValueError("cpp_range supports only FixedRangeOneStreetGame instances")
        try:
            from toy_poker._range_solver_cpp import (
                RangeSolverCore,
                RangeSolverCoreFloat32,
            )
        except ImportError as exc:
            raise RuntimeError(
                "cpp_range extension is not built; reinstall the project with "
                "`python -m pip install -e .`"
            ) from exc

        reference = VectorizedRangeCFRPlusSolver()
        root = reference._build_public_tree(game)
        decision_nodes = reference._decision_nodes(root)
        flat = flatten_public_tree(root)
        evaluator = VectorizedRangeEvaluator(game, root)
        core_type = RangeSolverCoreFloat32 if config.precision == "float32" else RangeSolverCore
        core = core_type(
            flat.players,
            flat.action_offsets,
            flat.children,
            flat.folders,
            flat.terminal_returns,
            flat.matched_commitments,
            np.asarray(game.oop_rank_probabilities, dtype=np.float64),
            np.asarray(game.ip_rank_probabilities, dtype=np.float64),
            config.algorithm,
            config.dcfr_alpha,
            config.dcfr_beta,
            config.dcfr_gamma,
        )
        convergence = []
        consecutive_hits = 0
        early_stopped = False
        stop_reason = "max_iterations"
        started = time.perf_counter()
        checkpoint = min(config.snapshot_every, config.iterations)
        while checkpoint <= config.iterations:
            core.run_until(checkpoint)
            average = self._strategies(flat, core.average_strategy())
            gap, returns = evaluator.evaluate(average)
            convergence.append(
                {
                    "iteration": checkpoint,
                    "exploitability": gap,
                    "returns": returns,
                }
            )
            if checkpoint >= config.min_iterations and gap <= config.target_exploitability:
                consecutive_hits += 1
            else:
                consecutive_hits = 0
            if config.early_stopping and consecutive_hits >= config.patience_checkpoints:
                early_stopped = True
                stop_reason = "target_exploitability"
                break
            checkpoint = min(checkpoint + config.snapshot_every, config.iterations)
            if checkpoint == core.iteration:
                break
        elapsed = time.perf_counter() - started
        average = self._strategies(flat, core.average_strategy())
        table = reference._policy_table(game, decision_nodes, average)
        best = min(convergence, key=lambda row: row["exploitability"])
        return SolveResult(
            policy=standalone_policy(table),
            policy_table=table,
            convergence=convergence,
            elapsed_seconds=elapsed,
            checkpoint_evaluation_backend=self.backend,
            completed_iterations=core.iteration,
            early_stopped=early_stopped,
            stop_reason=stop_reason,
            best_exploitability=float(best["exploitability"]),
            best_iteration=int(best["iteration"]),
        )

    @staticmethod
    def _strategies(
        flat: FlatPublicTree, slot_rank_strategy: np.ndarray
    ) -> dict[int, np.ndarray]:
        result = {}
        for node_index, node in enumerate(flat.nodes):
            if node.player is None:
                continue
            begin = int(flat.action_offsets[node_index])
            end = int(flat.action_offsets[node_index + 1])
            result[id(node)] = np.asarray(
                slot_rank_strategy[begin:end].T, dtype=np.float64
            )
        return result
