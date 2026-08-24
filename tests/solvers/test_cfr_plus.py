"""C++ CFR+ adapter convergence test."""

import pyspiel

from toy_poker.analysis import analyze_information_sets, expected_returns
from toy_poker.games import get_game
from toy_poker.solvers import CFRPlusSolverAdapter, SolverConfig


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
    assert abs(returns[0] + 0.25) < 1e-5
    assert abs(returns[1] - 0.25) < 1e-5
    root_a = {action["action"]: action for action in strategies["P1|A|ROOT"]["actions"]}
    root_q = {action["action"]: action for action in strategies["P1|Q|ROOT"]["actions"]}
    assert root_a["All-in"]["probability"] > 0.999
    assert abs(root_q["All-in"]["probability"] - 0.5) < 0.005
    assert len(result.convergence) == 3
