"""Correctness tests for the compiled range-vector solver."""

import pytest

from toy_poker.games import get_game
from toy_poker.solvers import CFRPlusSolverAdapter, NodeLock, SolverConfig


@pytest.mark.parametrize("algorithm", ["cfr_plus", "dcfr"])
def test_cpp_matches_numpy_range_solver(algorithm):
    game = get_game("integer_range_betting").load_game(
        {
            "num_ranks": 3,
            "oop_rank_weights": "1,2,7",
            "ip_rank_weights": "6,3,1",
        }
    )
    common = dict(
        algorithm=algorithm,
        iterations=100,
        snapshot_every=100,
        early_stopping=False,
    )
    numpy_result = CFRPlusSolverAdapter().solve(
        game, SolverConfig(backend="vectorized_range", **common)
    )
    cpp_result = CFRPlusSolverAdapter().solve(
        game, SolverConfig(backend="cpp_range", **common)
    )

    assert cpp_result.convergence[-1]["exploitability"] == pytest.approx(
        numpy_result.convergence[-1]["exploitability"], abs=1e-12
    )
    assert cpp_result.convergence[-1]["returns"] == pytest.approx(
        numpy_result.convergence[-1]["returns"], abs=1e-12
    )
    for key, actions in numpy_result.policy_table.items():
        assert dict(cpp_result.policy_table[key]) == pytest.approx(dict(actions), abs=1e-12)


def test_float32_storage_retains_low_exploitability():
    game = get_game("integer_range_betting").load_game({"num_ranks": 3})
    result = CFRPlusSolverAdapter().solve(
        game,
        SolverConfig(
            backend="cpp_range",
            algorithm="dcfr",
            precision="float32",
            iterations=500,
            snapshot_every=500,
            early_stopping=False,
        ),
    )

    assert result.convergence[-1]["exploitability"] < 5e-4
    assert sum(result.convergence[-1]["returns"]) == pytest.approx(1.0, abs=1e-12)


def test_cpp_matches_numpy_with_zero_weight_ranks():
    game = get_game("integer_range_betting").load_game(
        {
            "num_ranks": 3,
            "oop_rank_weights": "1,0,1",
            "ip_rank_weights": "uniform",
        }
    )
    common = dict(
        algorithm="dcfr",
        iterations=100,
        snapshot_every=100,
        early_stopping=False,
    )
    numpy_result = CFRPlusSolverAdapter().solve(
        game, SolverConfig(backend="vectorized_range", **common)
    )
    cpp_result = CFRPlusSolverAdapter().solve(
        game, SolverConfig(backend="cpp_range", **common)
    )

    assert cpp_result.convergence[-1]["exploitability"] == pytest.approx(
        numpy_result.convergence[-1]["exploitability"], abs=1e-12
    )
    assert cpp_result.convergence[-1]["returns"] == pytest.approx(
        numpy_result.convergence[-1]["returns"], abs=1e-12
    )


def test_cpp_matches_numpy_with_node_lock():
    game = get_game("integer_range_betting").load_game(
        {
            "num_ranks": 3,
            "oop_stack": 1.0,
            "ip_stack": 1.0,
            "bet_fractions": "0.1,0.2,0.3333333333333333,0.5,0.75",
        }
    )
    common = dict(
        algorithm="dcfr",
        iterations=100,
        snapshot_every=100,
        early_stopping=False,
        node_locks=(NodeLock("OOP", 2, "ROOT", (("check", 1.0),)),),
    )
    numpy_result = CFRPlusSolverAdapter().solve(
        game, SolverConfig(backend="vectorized_range", **common)
    )
    cpp_result = CFRPlusSolverAdapter().solve(
        game, SolverConfig(backend="cpp_range", **common)
    )

    assert cpp_result.convergence[-1]["exploitability"] == pytest.approx(
        numpy_result.convergence[-1]["exploitability"], abs=1e-12
    )
    assert cpp_result.convergence[-1]["returns"] == pytest.approx(
        numpy_result.convergence[-1]["returns"], abs=1e-12
    )
    for key, actions in numpy_result.policy_table.items():
        assert dict(cpp_result.policy_table[key]) == pytest.approx(dict(actions), abs=1e-12)
