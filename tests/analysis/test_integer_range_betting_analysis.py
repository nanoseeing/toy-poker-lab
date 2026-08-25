"""Native EFG and analysis checks for integer range custom-size poker."""

import pyspiel
import pytest

from toy_poker.analysis import analyze_information_sets, expected_returns
from toy_poker.analysis.vectorized_range import analyze_vectorized_range
from toy_poker.games import get_game
from toy_poker.solvers import CFRPlusSolverAdapter, SolverConfig


def test_native_efg_solver_preserves_dynamic_actions_and_analysis_context():
    plugin = get_game("integer_range_betting")
    game = plugin.load_game()
    result = CFRPlusSolverAdapter().solve(
        game,
        SolverConfig(backend="native_efg", iterations=100, snapshot_every=100),
    )
    infos = analyze_information_sets(game, result.policy, plugin)
    root = next(row for row in infos if row["key"] == "P1|10|ROOT")
    assert [action["action"] for action in root["actions"]] == [
        "Check",
        "All-in",
        "Bet 33%",
        "Bet 100%",
    ]
    assert root["context"] == {
        "pot": 1.0,
        "ip_committed": 0.0,
        "oop_committed": 0.0,
        "ip_remaining_stack": 4.0,
        "oop_remaining_stack": 4.0,
        "amount_to_call": 0.0,
        "minimum_raise_increment": 0.0,
    }
    returns = expected_returns(game, result.policy)
    assert abs(sum(returns) - 1.0) < 1e-12
    assert pyspiel.exploitability(game, result.policy) >= 0.0


def test_vectorized_analysis_matches_exact_on_reached_information_sets():
    plugin = get_game("integer_range_betting")
    game = plugin.load_game(
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
            iterations=100,
            snapshot_every=100,
            early_stopping=False,
        ),
    )
    exact = {
        row["key"]: row for row in analyze_information_sets(game, result.policy, plugin)
    }
    vectorized, paths, public_tree = analyze_vectorized_range(
        game, result.policy, plugin
    )
    vectorized_by_key = {row["key"]: row for row in vectorized}

    assert exact.keys() == vectorized_by_key.keys()
    for key, expected in exact.items():
        actual = vectorized_by_key[key]
        assert actual["reach_probability"] == pytest.approx(
            expected["reach_probability"], abs=1e-12
        )
        if expected["reach_probability"] > 1e-10:
            assert actual["policy_ev"] == pytest.approx(
                expected["policy_ev"], abs=1e-12
            )
            assert [action["ev"] for action in actual["actions"]] == pytest.approx(
                [action["ev"] for action in expected["actions"]], abs=1e-12
            )
    assert sum(path["reach_probability"] for path in paths) == pytest.approx(1.0)
    assert public_tree[0]["reach_probability"] == pytest.approx(1.0)
