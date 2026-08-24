"""Vectorized CFR+ for the one-street independent integer-range game."""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np
import pyspiel

from toy_poker.games.fixed_range_one_street import (
    INITIAL_POT,
    PLAYER_IP,
    PLAYER_OOP,
    FixedRangeOneStreetGame,
)
from toy_poker.solvers.policy import PolicyTable, standalone_policy
from toy_poker.solvers.result import SolveResult, SolverConfig


@dataclass
class _PublicNode:
    state: pyspiel.State
    player: int | None
    actions: tuple[int, ...]
    children: tuple["_PublicNode", ...]
    regrets: np.ndarray | None
    strategy_sum: np.ndarray | None


class VectorizedRangeEvaluator:
    """Exact vectorized policy evaluation and best response on a public tree."""

    def __init__(self, game: FixedRangeOneStreetGame, root: _PublicNode):
        self.game = game
        self.root = root
        self.oop_probability = np.asarray(game.oop_rank_probabilities, dtype=float)
        self.ip_probability = np.asarray(game.ip_rank_probabilities, dtype=float)

    def terminal_counterfactual_values(
        self,
        state: pyspiel.State,
        player: int,
        opponent_reach: np.ndarray,
    ) -> np.ndarray:
        """Return one value per private rank, already weighted by opponent reach."""
        opponent_probability = (
            self.oop_probability if player == PLAYER_IP else self.ip_probability
        )
        weights = opponent_probability * opponent_reach
        total_weight = float(weights.sum())
        if state._folder is not None:
            return np.full(
                self.game.num_ranks,
                state.returns()[player] * total_weight,
                dtype=float,
            )
        matched = state.commitments[PLAYER_IP]
        lower = np.concatenate(([0.0], np.cumsum(weights)[:-1]))
        equal = weights
        higher = total_weight - lower - equal
        win = INITIAL_POT + matched
        lose = -matched
        return win * lower + (INITIAL_POT / 2.0) * equal + lose * higher

    def _policy_counterfactual_values(
        self,
        node: _PublicNode,
        strategies: dict[int, np.ndarray],
        player: int,
        opponent_reach: np.ndarray,
    ) -> np.ndarray:
        if node.player is None:
            return self.terminal_counterfactual_values(
                node.state, player, opponent_reach
            )
        strategy = strategies[id(node)]
        if node.player != player:
            return sum(
                (
                    self._policy_counterfactual_values(
                        child,
                        strategies,
                        player,
                        opponent_reach * strategy[:, action_index],
                    )
                    for action_index, child in enumerate(node.children)
                ),
                np.zeros(self.game.num_ranks, dtype=float),
            )
        children = np.stack(
            [
                self._policy_counterfactual_values(
                    child, strategies, player, opponent_reach
                )
                for child in node.children
            ],
            axis=1,
        )
        return np.sum(strategy * children, axis=1)

    def expected_returns(self, strategies: dict[int, np.ndarray]) -> list[float]:
        result = []
        for player in range(2):
            values = self._policy_counterfactual_values(
                self.root,
                strategies,
                player,
                np.ones(self.game.num_ranks, dtype=float),
            )
            own_probability = (
                self.ip_probability if player == PLAYER_IP else self.oop_probability
            )
            result.append(float(np.dot(own_probability, values)))
        return result

    def best_response_value(
        self, strategies: dict[int, np.ndarray], best_responder: int
    ) -> float:
        def visit(node: _PublicNode, opponent_reach: np.ndarray) -> np.ndarray:
            if node.player is None:
                return self.terminal_counterfactual_values(
                    node.state, best_responder, opponent_reach
                )
            if node.player != best_responder:
                strategy = strategies[id(node)]
                return sum(
                    (
                        visit(
                            child,
                            opponent_reach * strategy[:, action_index],
                        )
                        for action_index, child in enumerate(node.children)
                    ),
                    np.zeros(self.game.num_ranks, dtype=float),
                )
            children = np.stack(
                [visit(child, opponent_reach) for child in node.children], axis=1
            )
            return np.max(children, axis=1)

        values = visit(self.root, np.ones(self.game.num_ranks, dtype=float))
        own_probability = (
            self.ip_probability
            if best_responder == PLAYER_IP
            else self.oop_probability
        )
        return float(np.dot(own_probability, values))

    def evaluate(
        self, strategies: dict[int, np.ndarray]
    ) -> tuple[float, list[float]]:
        returns = self.expected_returns(strategies)
        improvements = [
            self.best_response_value(strategies, player) - returns[player]
            for player in range(2)
        ]
        return float(sum(improvements) / 2.0), returns


class VectorizedRangeCFRPlusSolver:
    """CFR+/DCFR specialized to rank-independent public betting trees."""

    backend = "vectorized_range"

    def solve(
        self, game: pyspiel.Game, config: SolverConfig
    ) -> SolveResult:
        if not isinstance(game, FixedRangeOneStreetGame):
            raise ValueError(
                "vectorized_range supports only FixedRangeOneStreetGame instances"
            )
        if config.algorithm not in {"cfr_plus", "dcfr"}:
            raise ValueError(f"Unsupported vectorized algorithm: {config.algorithm}")
        root = self._build_public_tree(game)
        decision_nodes = self._decision_nodes(root)
        evaluator = VectorizedRangeEvaluator(game, root)
        convergence = []
        consecutive_hits = 0
        completed_iterations = 0
        early_stopped = False
        stop_reason = "max_iterations"
        started = time.perf_counter()

        for iteration in range(1, config.iterations + 1):
            for updating_player in (PLAYER_IP, PLAYER_OOP):
                strategies = {
                    id(node): self._regret_matching(node.regrets)
                    for node in decision_nodes
                }
                deltas: dict[int, np.ndarray] = {}
                self._cfr_update(
                    root,
                    strategies,
                    np.ones(game.num_ranks, dtype=float),
                    np.ones(game.num_ranks, dtype=float),
                    updating_player,
                    game,
                    evaluator,
                    deltas,
                )
                for node in decision_nodes:
                    if node.player == updating_player:
                        if config.algorithm == "cfr_plus":
                            node.regrets[:] = np.maximum(
                                node.regrets + deltas[id(node)], 0.0
                            )
                        else:
                            self._discount_dcfr_regrets(node.regrets, iteration, config)
                            node.regrets += deltas[id(node)]
            strategies = {
                id(node): self._regret_matching(node.regrets) for node in decision_nodes
            }
            if config.algorithm == "dcfr":
                average_discount = ((iteration - 1.0) / iteration) ** config.dcfr_gamma
                for node in decision_nodes:
                    node.strategy_sum *= average_discount
            self._accumulate_average(
                root,
                strategies,
                np.ones(game.num_ranks, dtype=float),
                np.ones(game.num_ranks, dtype=float),
                float(iteration) if config.algorithm == "cfr_plus" else 1.0,
            )
            completed_iterations = iteration

            if iteration % config.snapshot_every == 0 or iteration == config.iterations:
                average = self._average_strategies(decision_nodes)
                gap, returns = evaluator.evaluate(average)
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
        average = self._average_strategies(decision_nodes)
        table = self._policy_table(game, decision_nodes, average)
        best_checkpoint = min(convergence, key=lambda row: row["exploitability"])
        return SolveResult(
            policy=standalone_policy(table),
            policy_table=table,
            convergence=convergence,
            elapsed_seconds=elapsed,
            checkpoint_evaluation_backend=self.backend,
            completed_iterations=completed_iterations,
            early_stopped=early_stopped,
            stop_reason=stop_reason,
            best_exploitability=float(best_checkpoint["exploitability"]),
            best_iteration=int(best_checkpoint["iteration"]),
        )

    def _build_public_tree(self, game: FixedRangeOneStreetGame) -> _PublicNode:
        state = game.new_initial_state()
        state.apply_action(0)

        def build(current: pyspiel.State) -> _PublicNode:
            if current.is_terminal():
                return _PublicNode(current.clone(), None, (), (), None, None)
            player = current.current_player()
            actions = tuple(int(action) for action in current.legal_actions())
            rank_actions = (game.num_ranks, len(actions))
            return _PublicNode(
                state=current.clone(),
                player=player,
                actions=actions,
                children=tuple(build(current.child(action)) for action in actions),
                regrets=np.zeros(rank_actions, dtype=float),
                strategy_sum=np.zeros(rank_actions, dtype=float),
            )

        return build(state)

    def _decision_nodes(self, root: _PublicNode) -> list[_PublicNode]:
        result = []

        def visit(node: _PublicNode) -> None:
            if node.player is None:
                return
            result.append(node)
            for child in node.children:
                visit(child)

        visit(root)
        return result

    @staticmethod
    def _regret_matching(regrets: np.ndarray) -> np.ndarray:
        positive = np.maximum(regrets, 0.0)
        totals = positive.sum(axis=1, keepdims=True)
        uniform = np.full_like(regrets, 1.0 / regrets.shape[1])
        return np.divide(positive, totals, out=uniform, where=totals > 0.0)

    @staticmethod
    def _discount_dcfr_regrets(
        regrets: np.ndarray, iteration: int, config: SolverConfig
    ) -> None:
        """Apply the standard DCFR(alpha, beta) cumulative-regret discount."""
        positive_factor = iteration**config.dcfr_alpha / (
            iteration**config.dcfr_alpha + 1.0
        )
        negative_factor = iteration**config.dcfr_beta / (
            iteration**config.dcfr_beta + 1.0
        )
        regrets *= np.where(regrets > 0.0, positive_factor, negative_factor)

    @staticmethod
    def _average_strategies(
        nodes: list[_PublicNode],
    ) -> dict[int, np.ndarray]:
        result = {}
        for node in nodes:
            totals = node.strategy_sum.sum(axis=1, keepdims=True)
            uniform = np.full_like(node.strategy_sum, 1.0 / len(node.actions))
            result[id(node)] = np.divide(
                node.strategy_sum, totals, out=uniform, where=totals > 0.0
            )
        return result

    def _cfr_update(
        self,
        node: _PublicNode,
        strategies: dict[int, np.ndarray],
        oop_reach: np.ndarray,
        ip_reach: np.ndarray,
        updating_player: int,
        game: FixedRangeOneStreetGame,
        evaluator: VectorizedRangeEvaluator,
        deltas: dict[int, np.ndarray],
    ) -> np.ndarray:
        if node.player is None:
            opponent_reach = (
                oop_reach if updating_player == PLAYER_IP else ip_reach
            )
            return evaluator.terminal_counterfactual_values(
                node.state, updating_player, opponent_reach
            )
        strategy = strategies[id(node)]
        child_values = []
        for action_index, child in enumerate(node.children):
            if node.player == PLAYER_OOP and node.player != updating_player:
                child_values.append(
                    self._cfr_update(
                        child,
                        strategies,
                        oop_reach * strategy[:, action_index],
                        ip_reach,
                        updating_player,
                        game,
                        evaluator,
                        deltas,
                    )
                )
            elif node.player == PLAYER_IP and node.player != updating_player:
                child_values.append(
                    self._cfr_update(
                        child,
                        strategies,
                        oop_reach,
                        ip_reach * strategy[:, action_index],
                        updating_player,
                        game,
                        evaluator,
                        deltas,
                    )
                )
            else:
                child_values.append(
                    self._cfr_update(
                        child,
                        strategies,
                        oop_reach,
                        ip_reach,
                        updating_player,
                        game,
                        evaluator,
                        deltas,
                    )
                )
        children = np.stack(child_values, axis=1)
        if node.player == updating_player:
            result = np.sum(strategy * children, axis=1)
            deltas[id(node)] = children - result[:, None]
            return result
        return np.sum(children, axis=1)

    def _accumulate_average(
        self,
        node: _PublicNode,
        strategies: dict[int, np.ndarray],
        oop_reach: np.ndarray,
        ip_reach: np.ndarray,
        weight: float,
    ) -> None:
        if node.player is None:
            return
        strategy = strategies[id(node)]
        own_reach = oop_reach if node.player == PLAYER_OOP else ip_reach
        node.strategy_sum += weight * own_reach[:, None] * strategy
        for action_index, child in enumerate(node.children):
            if node.player == PLAYER_OOP:
                self._accumulate_average(
                    child,
                    strategies,
                    oop_reach * strategy[:, action_index],
                    ip_reach,
                    weight,
                )
            else:
                self._accumulate_average(
                    child,
                    strategies,
                    oop_reach,
                    ip_reach * strategy[:, action_index],
                    weight,
                )

    def _policy_table(
        self,
        game: FixedRangeOneStreetGame,
        nodes: list[_PublicNode],
        strategies: dict[int, np.ndarray],
    ) -> PolicyTable:
        table: PolicyTable = {}
        for node in nodes:
            history = "-".join(node.state.history_tokens) or "ROOT"
            strategy = strategies[id(node)]
            for rank_index, rank in enumerate(game.cards):
                key = f"P{node.player}|{rank}|{history}"
                table[key] = [
                    (action, float(strategy[rank_index, action_index]))
                    for action_index, action in enumerate(node.actions)
                ]
        return table
