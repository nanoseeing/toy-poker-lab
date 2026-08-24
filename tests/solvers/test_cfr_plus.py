"""C++ CFR+ adapter convergence test."""

import pyspiel

from toy_poker.analysis import analyze_information_sets, expected_returns
from toy_poker.games import get_game
from toy_poker.solvers import CFRPlusSolverAdapter, SolverConfig


def test_solver_defaults_to_native_efg_and_100k_iterations():
    config = SolverConfig()
    assert config.backend == "native_efg"
    assert config.iterations == 100_000


def test_cfr_plus_converges_and_returns_standalone_policy():
    plugin = get_game("akq_allin")
    game = plugin.load_game()
    result = CFRPlusSolverAdapter().solve(
        game, SolverConfig(iterations=30_000, snapshot_every=10_000)
    )
    strategies = {
        row["key"]: row for row in analyze_information_sets(game, result.policy, plugin)
    }
    returns = expected_returns(game, result.policy)
    assert pyspiel.exploitability(game, result.policy) < 5e-5
    assert abs(returns[0] - 0.75) < 1e-5
    assert abs(returns[1] - 0.25) < 1e-5
    root = {action["action"]: action for action in strategies["P1|K|ROOT"]["actions"]}
    ace = {action["action"]: action for action in strategies["P0|A|CHECK"]["actions"]}
    queen = {action["action"]: action for action in strategies["P0|Q|CHECK"]["actions"]}
    assert root["Check"]["probability"] > 0.999
    assert ace["All-in"]["probability"] > 0.999
    assert abs(queen["All-in"]["probability"] - 0.5) < 0.005
    assert len(result.convergence) == 3


def test_native_efg_backend_matches_python_game_backend():
    game = get_game("akqj_two_street").load_game()
    config = {"iterations": 100, "snapshot_every": 100}
    python_result = CFRPlusSolverAdapter().solve(
        game, SolverConfig(backend="python_game", **config)
    )
    native_result = CFRPlusSolverAdapter().solve(
        game, SolverConfig(backend="native_efg", **config)
    )

    assert python_result.policy_table.keys() == native_result.policy_table.keys()
    for key in python_result.policy_table:
        python_actions = python_result.policy_table[key]
        native_actions = native_result.policy_table[key]
        assert [action for action, _ in python_actions] == [
            action for action, _ in native_actions
        ]
        assert all(
            abs(python_probability - native_probability) < 1e-12
            for (_, python_probability), (_, native_probability) in zip(
                python_actions, native_actions
            )
        )
    assert abs(
        pyspiel.exploitability(game, python_result.policy)
        - pyspiel.exploitability(game, native_result.policy)
    ) < 1e-12
