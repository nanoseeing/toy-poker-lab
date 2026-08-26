"""Correctness tests for the specialized vectorized range solver."""

import pyspiel
import pytest

from toy_poker.analysis import expected_returns
from toy_poker.games import get_game
from toy_poker.solvers import CFRPlusSolverAdapter, NodeLock, SolverConfig


def test_vectorized_weighted_evaluation_matches_open_spiel():
    game = get_game("integer_range_betting").load_game(
        {
            "num_ranks": 3,
            "oop_rank_weights": "1,2,7",
            "ip_rank_weights": "6,3,1",
        }
    )
    result = CFRPlusSolverAdapter().solve(
        game,
        SolverConfig(
            backend="vectorized_range",
            iterations=200,
            snapshot_every=200,
            early_stopping=False,
        ),
    )

    checkpoint = result.convergence[-1]
    assert checkpoint["exploitability"] == pytest.approx(
        pyspiel.exploitability(game, result.policy), abs=1e-12
    )
    assert checkpoint["returns"] == pytest.approx(
        expected_returns(game, result.policy), abs=1e-12
    )
    assert result.checkpoint_evaluation_backend == "vectorized_range"
    assert len(result.policy_table) == 132


def test_vectorized_and_native_backends_reach_similar_quality():
    game = get_game("integer_range_betting").load_game({"num_ranks": 3})
    common = {
        "iterations": 500,
        "snapshot_every": 500,
        "early_stopping": False,
    }
    vectorized = CFRPlusSolverAdapter().solve(
        game, SolverConfig(backend="vectorized_range", **common)
    )
    native = CFRPlusSolverAdapter().solve(
        game, SolverConfig(backend="native_efg", **common)
    )

    assert vectorized.convergence[-1]["exploitability"] < 5e-4
    assert native.convergence[-1]["exploitability"] < 5e-4
    assert vectorized.convergence[-1]["returns"] == pytest.approx(
        native.convergence[-1]["returns"], abs=5e-4
    )


def test_vectorized_backend_rejects_other_game_families():
    game = get_game("akq_allin").load_game()
    with pytest.raises(ValueError, match="FixedRangeOneStreetGame"):
        CFRPlusSolverAdapter().solve(
            game,
            SolverConfig(
                backend="vectorized_range",
                iterations=1,
                snapshot_every=1,
            ),
        )


def test_dcfr_reaches_a_low_exploitability_and_preserves_constant_sum():
    game = get_game("integer_range_betting").load_game({"num_ranks": 3})
    result = CFRPlusSolverAdapter().solve(
        game,
        SolverConfig(
            backend="vectorized_range",
            algorithm="dcfr",
            iterations=500,
            snapshot_every=500,
            early_stopping=False,
        ),
    )

    checkpoint = result.convergence[-1]
    assert checkpoint["exploitability"] < 5e-4
    assert sum(checkpoint["returns"]) == pytest.approx(1.0, abs=1e-12)


def test_node_lock_fixes_strategy_and_uses_constrained_best_response():
    game = get_game("integer_range_betting").load_game(
        {
            "num_ranks": 3,
            "oop_stack": 1.0,
            "ip_stack": 1.0,
            "bet_fractions": "0.1,0.2,0.3333333333333333,0.5,0.75",
        }
    )
    result = CFRPlusSolverAdapter().solve(
        game,
        SolverConfig(
            backend="vectorized_range",
            algorithm="dcfr",
            iterations=2_000,
            snapshot_every=1_000,
            early_stopping=False,
            node_locks=(
                NodeLock("OOP", 2, "ROOT", (("check", 1.0),)),
            ),
        ),
    )

    assert dict(result.policy_table["P1|2|ROOT"])[0] == 1.0
    assert sum(dict(result.policy_table["P1|2|ROOT"]).values()) == 1.0
    assert result.convergence[-1]["exploitability"] < 1e-4
    assert pyspiel.exploitability(game, result.policy) > result.convergence[-1][
        "exploitability"
    ]
