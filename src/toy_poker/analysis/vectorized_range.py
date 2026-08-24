"""Vectorized reporting analysis for independent integer private ranges."""

from __future__ import annotations

import numpy as np
import pyspiel

from toy_poker.analysis.information_sets import display_action
from toy_poker.games.base import GamePlugin
from toy_poker.games.fixed_range_one_street import PLAYER_IP, PLAYER_OOP
from toy_poker.solvers.vectorized_range import (
    VectorizedRangeCFRPlusSolver,
    VectorizedRangeEvaluator,
    _PublicNode,
)


def _policy_strategies(
    game, policy: pyspiel.Policy, nodes: list[_PublicNode]
) -> dict[int, np.ndarray]:
    strategies = {}
    for node in nodes:
        history = "-".join(node.state.history_tokens) or "ROOT"
        rows = []
        for rank in game.cards:
            probabilities = policy.action_probabilities(
                f"P{node.player}|{rank}|{history}"
            )
            rows.append(
                [float(probabilities.get(action, 0.0)) for action in node.actions]
            )
        strategies[id(node)] = np.asarray(rows, dtype=float)
    return strategies


def analyze_vectorized_range(
    game,
    policy: pyspiel.Policy,
    plugin: GamePlugin,
    off_path_threshold: float = 1e-8,
) -> tuple[list[dict], list[dict], list[dict]]:
    """Return information sets, aggregated terminals, and a public tree."""
    solver = VectorizedRangeCFRPlusSolver()
    root = solver._build_public_tree(game)
    nodes = solver._decision_nodes(root)
    strategies = _policy_strategies(game, policy, nodes)
    evaluator = VectorizedRangeEvaluator(game, root)
    oop_probability = np.asarray(game.oop_rank_probabilities, dtype=float)
    ip_probability = np.asarray(game.ip_rank_probabilities, dtype=float)
    information_sets = []
    terminal_paths = []
    public_tree = []

    def visit(
        node: _PublicNode,
        oop_reach: np.ndarray,
        ip_reach: np.ndarray,
        action_history: list[str],
    ) -> None:
        oop_mass = float(np.dot(oop_probability, oop_reach))
        ip_mass = float(np.dot(ip_probability, ip_reach))
        public_reach = oop_mass * ip_mass
        public_row = {
            "history": list(action_history),
            "reach_probability": public_reach,
            "terminal": node.player is None,
            "player_index": node.player,
            "children": [],
        }
        public_tree.append(public_row)

        if node.player is None:
            weighted_returns = []
            for player in range(2):
                opponent_reach = oop_reach if player == PLAYER_IP else ip_reach
                own_reach = ip_reach if player == PLAYER_IP else oop_reach
                own_probability = (
                    ip_probability if player == PLAYER_IP else oop_probability
                )
                values = evaluator.terminal_counterfactual_values(
                    node.state, player, opponent_reach
                )
                weighted_returns.append(float(np.dot(own_probability * own_reach, values)))
            conditional_returns = [
                value / public_reach if public_reach > 0.0 else 0.0
                for value in weighted_returns
            ]
            public_row["returns"] = conditional_returns
            terminal_paths.append(
                {
                    "chance": ["Aggregated independent rank ranges"],
                    "actions": list(action_history),
                    "reach_probability": public_reach,
                    "returns": {
                        plugin.player_name(player): conditional_returns[player]
                        for player in range(2)
                    },
                }
            )
            return

        player = node.player
        strategy = strategies[id(node)]
        own_probability = ip_probability if player == PLAYER_IP else oop_probability
        own_reach = ip_reach if player == PLAYER_IP else oop_reach
        opponent_mass = oop_mass if player == PLAYER_IP else ip_mass
        opponent_reach = oop_reach if player == PLAYER_IP else ip_reach
        ev_opponent_reach = opponent_reach
        ev_denominator = opponent_mass
        belief = "on_policy_reach"
        if opponent_mass <= 0.0:
            ev_opponent_reach = np.ones(game.num_ranks, dtype=float)
            ev_denominator = 1.0
            belief = "prior_fallback_at_zero_reach"
        action_values = np.stack(
            [
                evaluator._policy_counterfactual_values(
                    child,
                    strategies,
                    player,
                    ev_opponent_reach,
                )
                / ev_denominator
                for child in node.children
            ],
            axis=1,
        )
        context = plugin.information_context(node.state)
        for rank_index, rank in enumerate(game.cards):
            reach = float(own_probability[rank_index] * own_reach[rank_index] * opponent_mass)
            actions = []
            for action_index, action in enumerate(node.actions):
                probability = float(strategy[rank_index, action_index])
                action_ev = float(action_values[rank_index, action_index])
                actions.append(
                    {
                        "action_id": int(action),
                        "action": display_action(node.state, player, action),
                        "probability": probability,
                        "ev": action_ev,
                    }
                )
            policy_ev = sum(action["probability"] * action["ev"] for action in actions)
            best_ev = max(action["ev"] for action in actions)
            for action in actions:
                action["ev_vs_policy"] = action["ev"] - policy_ev
                action["ev_vs_best"] = action["ev"] - best_ev
            key = f"P{player}|{rank}|{'-'.join(node.state.history_tokens) or 'ROOT'}"
            information_sets.append(
                {
                    "key": key,
                    "label": plugin.information_label(key),
                    "player_index": player,
                    "player": plugin.player_name(player),
                    "card": str(rank),
                    "history": list(action_history),
                    "context": context,
                    "reach_probability": reach,
                    "is_off_path": reach < off_path_threshold,
                    "ev_belief": belief,
                    "policy_ev": policy_ev,
                    "best_action_ev": best_ev,
                    "actions": actions,
                }
            )

        for action_index, child in enumerate(node.children):
            action_name = display_action(node.state, player, node.actions[action_index])
            if player == PLAYER_OOP:
                child_oop_reach = oop_reach * strategy[:, action_index]
                child_ip_reach = ip_reach
            else:
                child_oop_reach = oop_reach
                child_ip_reach = ip_reach * strategy[:, action_index]
            child_oop_mass = float(np.dot(oop_probability, child_oop_reach))
            child_ip_mass = float(np.dot(ip_probability, child_ip_reach))
            child_reach = child_oop_mass * child_ip_mass
            public_row["children"].append(
                {
                    "action": action_name,
                    "history": action_history + [action_name],
                    "probability": child_reach / public_reach if public_reach > 0.0 else 0.0,
                }
            )
            visit(
                child,
                child_oop_reach,
                child_ip_reach,
                action_history + [action_name],
            )

    visit(
        root,
        np.ones(game.num_ranks, dtype=float),
        np.ones(game.num_ranks, dtype=float),
        [],
    )
    return information_sets, terminal_paths, public_tree
