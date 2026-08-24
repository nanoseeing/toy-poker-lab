"""Information-set reach, strategy and conditional action-EV analysis."""

from __future__ import annotations

from collections import defaultdict

import pyspiel

from toy_poker.analysis.evaluator import state_value_function
from toy_poker.games.base import GamePlugin


def display_action(state: pyspiel.State, player: int, action: int) -> str:
    label = state.action_to_string(player, action)
    return "All-in" if label == "AllIn" else label


def analyze_information_sets(
    game: pyspiel.Game,
    policy: pyspiel.Policy,
    plugin: GamePlugin,
    off_path_threshold: float = 1e-8,
) -> list[dict]:
    value = state_value_function(game, policy)
    occurrences: dict[str, list[tuple[pyspiel.State, float, list[str]]]] = defaultdict(list)

    def visit(state: pyspiel.State, reach: float, public_actions: list[str]) -> None:
        if state.is_terminal():
            return
        if state.is_chance_node():
            for action, probability in state.chance_outcomes():
                visit(state.child(action), reach * probability, public_actions)
            return
        player = state.current_player()
        key = state.information_state_string(player)
        occurrences[key].append((state, reach, public_actions))
        probabilities = policy.action_probabilities(state)
        for action in state.legal_actions():
            visit(
                state.child(action),
                reach * probabilities.get(action, 0.0),
                public_actions + [display_action(state, player, action)],
            )

    visit(game.new_initial_state(), 1.0, [])
    rows = []
    for key, states in occurrences.items():
        total_reach = sum(reach for _, reach, _ in states)
        if total_reach > 0.0:
            weights = [reach / total_reach for _, reach, _ in states]
            belief = "on_policy_reach"
        else:
            weights = [1.0 / len(states)] * len(states)
            belief = "uniform_fallback_at_zero_reach"
        representative, _, history = states[0]
        player = representative.current_player()
        probabilities = policy.action_probabilities(representative)
        actions = []
        for action in representative.legal_actions():
            action_ev = sum(
                weight * value(state.child(action))[player]
                for (state, _, _), weight in zip(states, weights)
            )
            actions.append(
                {
                    "action_id": int(action),
                    "action": display_action(representative, player, action),
                    "probability": float(probabilities.get(action, 0.0)),
                    "ev": action_ev,
                }
            )
        policy_ev = sum(action["probability"] * action["ev"] for action in actions)
        best_ev = max(action["ev"] for action in actions)
        for action in actions:
            action["ev_vs_policy"] = action["ev"] - policy_ev
            action["ev_vs_best"] = action["ev"] - best_ev
        rows.append(
            {
                "key": key,
                "label": plugin.information_label(key),
                "player_index": player,
                "player": plugin.player_name(player),
                "card": plugin.private_card(representative, player),
                "history": history,
                "reach_probability": total_reach,
                "is_off_path": total_reach < off_path_threshold,
                "ev_belief": belief,
                "policy_ev": policy_ev,
                "best_action_ev": best_ev,
                "actions": actions,
            }
        )
    label_order = {key: index for index, key in enumerate(plugin.metadata.information_labels)}
    return sorted(rows, key=lambda row: label_order.get(row["key"], 999))
