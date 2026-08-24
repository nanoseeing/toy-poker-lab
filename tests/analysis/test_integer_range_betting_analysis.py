"""Native EFG and analysis checks for integer range custom-size poker."""

import pyspiel

from toy_poker.analysis import analyze_information_sets, expected_returns
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
        "amount_to_call": 0.0,
        "minimum_raise_increment": 0.0,
    }
    returns = expected_returns(game, result.policy)
    assert abs(sum(returns) - 1.0) < 1e-12
    assert pyspiel.exploitability(game, result.policy) >= 0.0
