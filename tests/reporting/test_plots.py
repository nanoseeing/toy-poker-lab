"""Focused checks for report plot filtering."""

import pyspiel
import pytest

from toy_poker.games import get_game
from toy_poker.reporting.plots import _merged_public_tree, _tree


def test_tree_reach_threshold_prunes_low_probability_branches():
    plugin = get_game("akqj_two_street")
    game = plugin.load_game()
    policy = pyspiel.UniformRandomPolicy(game)
    initial = game.new_initial_state()
    chance_action, chance_probability = initial.chance_outcomes()[0]
    state = initial.child(chance_action)

    full_nodes, _ = _tree(
        state, policy, plugin, initial_reach=chance_probability
    )
    major_nodes, _ = _tree(
        state,
        policy,
        plugin,
        initial_reach=chance_probability,
        min_reach=0.2,
    )

    assert len(major_nodes) < len(full_nodes)
    assert all(node["reach"] >= 0.2 for node in major_nodes)


def test_many_chance_outcomes_can_be_merged_into_a_public_tree():
    plugin = get_game("integer_range_betting")
    game = plugin.load_game()
    policy = pyspiel.UniformRandomPolicy(game)
    nodes, edges = _merged_public_tree(game, policy, plugin, min_reach=1e-4)

    assert nodes[0]["label"] == "OOP"
    assert nodes[0]["reach"] == pytest.approx(1.0)
    assert edges
    assert any(action == "Bet 33%" for _, _, action, _ in edges)
