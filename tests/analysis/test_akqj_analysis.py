"""Analytic equilibrium and CFR+ checks for AKQJ."""

import pyspiel

from toy_poker.analysis import analyze_information_sets, expected_returns, terminal_paths
from toy_poker.games import get_game
from toy_poker.games.akqj_allin.analytic import analytic_returns, analytic_strategy
from toy_poker.solvers import CFRPlusSolverAdapter, SolverConfig


def symmetric_default_policy():
    return pyspiel.TabularPolicy(
        {
            "P1|K|ROOT": [(0, 1.0), (1, 0.0)],
            "P0|A|CHECK": [(0, 0.0), (1, 1.0)],
            "P0|Q|CHECK": [(0, 0.75), (1, 0.25)],
            "P0|J|CHECK": [(0, 0.75), (1, 0.25)],
            "P1|K|CHECK-ALL_IN": [(1, 0.5), (2, 0.5)],
            "P0|A|ALL_IN": [(1, 1.0), (2, 0.0)],
            "P0|Q|ALL_IN": [(1, 0.0), (2, 1.0)],
            "P0|J|ALL_IN": [(1, 0.0), (2, 1.0)],
        }
    )


def test_symmetric_analytic_equilibrium():
    plugin = get_game("akqj_allin")
    game = plugin.load_game()
    policy = symmetric_default_policy()
    infos = {row["key"]: row for row in analyze_information_sets(game, policy, plugin)}
    returns = expected_returns(game, policy)
    assert all(abs(value) < 1e-12 for value in returns)
    assert pyspiel.exploitability(game, policy) < 1e-12
    assert abs(infos["P1|K|CHECK-ALL_IN"]["reach_probability"] - 0.5) < 1e-12
    assert all(
        abs(action["ev"] + 0.5) < 1e-12
        for action in infos["P1|K|CHECK-ALL_IN"]["actions"]
    )
    paths = terminal_paths(game, policy, plugin)
    assert abs(sum(path["reach_probability"] for path in paths) - 1.0) < 1e-12


def test_analytic_solution_scales_and_has_nonunique_bluff_split():
    strategy = analytic_strategy(2.0)
    q_bluff = strategy["P0|Q|CHECK"]["All-in"]
    j_bluff = strategy["P0|J|CHECK"]["All-in"]
    assert abs(q_bluff + j_bluff - 2.0 / 3.0) < 1e-12
    assert strategy["P1|K|CHECK-ALL_IN"]["Call"] == 1.0 / 3.0
    ip_value, oop_value = analytic_returns(2.0)
    assert abs(ip_value - 1.0 / 18.0) < 1e-12
    assert abs(oop_value + 1.0 / 18.0) < 1e-12


def test_cpp_cfr_plus_converges_to_equilibrium_family():
    plugin = get_game("akqj_allin")
    game = plugin.load_game()
    result = CFRPlusSolverAdapter().solve(
        game, SolverConfig(iterations=30_000, snapshot_every=10_000)
    )
    infos = {row["key"]: row for row in analyze_information_sets(game, result.policy, plugin)}
    action_maps = {
        key: {action["action"]: action for action in row["actions"]}
        for key, row in infos.items()
    }
    returns = expected_returns(game, result.policy)
    q_bluff = action_maps["P0|Q|CHECK"]["All-in"]["probability"]
    j_bluff = action_maps["P0|J|CHECK"]["All-in"]["probability"]
    assert pyspiel.exploitability(game, result.policy) < 1e-4
    assert all(abs(value) < 1e-5 for value in returns)
    assert action_maps["P1|K|ROOT"]["Check"]["probability"] > 0.999
    assert action_maps["P0|A|CHECK"]["All-in"]["probability"] > 0.999
    assert abs(q_bluff + j_bluff - 0.5) < 0.01
    assert abs(action_maps["P1|K|CHECK-ALL_IN"]["Call"]["probability"] - 0.5) < 0.01
