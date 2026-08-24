"""C++ CFR+ adapter convergence test."""

import pyspiel

from toy_poker.analysis import analyze_information_sets, expected_returns
from toy_poker.games import get_game
from toy_poker.solvers import CFRPlusSolverAdapter, SolverConfig


def test_solver_defaults_to_native_efg_and_early_stopping():
    config = SolverConfig()
    assert config.backend == "native_efg"
    assert config.iterations == 10_000
    assert config.snapshot_every == 1_000
    assert config.early_stopping is True
    assert config.target_exploitability == 1e-5
    assert config.min_iterations == 1_000
    assert config.patience_checkpoints == 2


def test_cfr_plus_converges_and_returns_standalone_policy():
    plugin = get_game("akq_allin")
    game = plugin.load_game()
    result = CFRPlusSolverAdapter().solve(
        game,
        SolverConfig(
            iterations=30_000,
            snapshot_every=10_000,
            early_stopping=False,
        ),
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


def test_early_stopping_respects_minimum_and_consecutive_checkpoints():
    game = get_game("akq_allin").load_game()
    result = CFRPlusSolverAdapter().solve(
        game,
        SolverConfig(
            iterations=10_000,
            snapshot_every=1_000,
            target_exploitability=1.0,
            min_iterations=1_500,
            patience_checkpoints=2,
        ),
    )

    assert result.early_stopped is True
    assert result.stop_reason == "target_exploitability"
    assert result.completed_iterations == 3_000
    assert [row["iteration"] for row in result.convergence] == [
        1_000,
        2_000,
        3_000,
    ]


def test_solver_runs_to_maximum_when_target_is_not_reached():
    game = get_game("akq_allin").load_game()
    result = CFRPlusSolverAdapter().solve(
        game,
        SolverConfig(
            iterations=2_500,
            snapshot_every=1_000,
            target_exploitability=1e-30,
        ),
    )

    assert result.early_stopped is False
    assert result.stop_reason == "max_iterations"
    assert result.completed_iterations == 2_500
    assert [row["iteration"] for row in result.convergence] == [1_000, 2_000, 2_500]


def test_native_efg_backend_matches_python_game_backend():
    game = get_game("akqj_two_street").load_game()
    config = {"iterations": 100, "snapshot_every": 100}
    python_result = CFRPlusSolverAdapter().solve(
        game, SolverConfig(backend="python_game", **config)
    )
    native_result = CFRPlusSolverAdapter().solve(
        game, SolverConfig(backend="native_efg", **config)
    )

    assert python_result.checkpoint_evaluation_backend == "python_game"
    assert native_result.checkpoint_evaluation_backend == "native_efg"

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
    assert abs(
        python_result.convergence[-1]["exploitability"]
        - native_result.convergence[-1]["exploitability"]
    ) < 1e-12
    assert all(
        abs(python_value - native_value) < 1e-12
        for python_value, native_value in zip(
            python_result.convergence[-1]["returns"],
            native_result.convergence[-1]["returns"],
        )
    )
