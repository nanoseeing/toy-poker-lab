"""CFR+ and normalized-analysis checks for AKQJ two-street poker."""

import pyspiel

from toy_poker.analysis import analyze_information_sets, expected_returns, terminal_paths
from toy_poker.games import get_game
from toy_poker.solvers import CFRPlusSolverAdapter, SolverConfig


def test_cpp_cfr_plus_solves_and_analysis_keeps_public_context():
    plugin = get_game("akqj_two_street")
    game = plugin.load_game()
    result = CFRPlusSolverAdapter().solve(
        game, SolverConfig(iterations=1_000, snapshot_every=500)
    )
    infos = {row["key"]: row for row in analyze_information_sets(game, result.policy, plugin)}
    returns = expected_returns(game, result.policy)
    paths = terminal_paths(game, result.policy, plugin)

    assert pyspiel.exploitability(game, result.policy) < 5e-4
    assert abs(sum(returns)) < 1e-12
    assert len(infos) == 48
    assert abs(sum(path["reach_probability"] for path in paths) - 1.0) < 1e-12
    assert infos["P1|K|S1:ROOT"]["context"] == {
        "street": 1,
        "pot": 1.0,
        "ip_committed": 0.0,
        "oop_committed": 0.0,
    }
    second_street = infos["P1|K|S1:CHECK-CHECK/S2:ROOT"]
    assert second_street["context"]["street"] == 2
