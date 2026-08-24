"""Enumerate terminal histories under a policy."""

from __future__ import annotations

import pyspiel

from toy_poker.analysis.information_sets import display_action
from toy_poker.games.base import GamePlugin


def terminal_paths(game: pyspiel.Game, policy: pyspiel.Policy, plugin: GamePlugin) -> list[dict]:
    paths = []

    def visit(state, reach, chance_labels, action_labels):
        if state.is_terminal():
            paths.append(
                {
                    "chance": chance_labels,
                    "actions": action_labels,
                    "reach_probability": reach,
                    "returns": {
                        plugin.player_name(player): value
                        for player, value in enumerate(state.returns())
                    },
                }
            )
            return
        if state.is_chance_node():
            for action, probability in state.chance_outcomes():
                visit(
                    state.child(action),
                    reach * probability,
                    chance_labels + [plugin.chance_outcome_label(state, action)],
                    action_labels,
                )
            return
        player = state.current_player()
        probabilities = policy.action_probabilities(state)
        for action in state.legal_actions():
            visit(
                state.child(action),
                reach * probabilities.get(action, 0.0),
                chance_labels,
                action_labels + [display_action(state, player, action)],
            )

    visit(game.new_initial_state(), 1.0, [], [])
    return paths
