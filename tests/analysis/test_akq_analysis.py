"""Exact-analysis and policy-persistence tests."""

from pathlib import Path

import pyspiel

from toy_poker.analysis import analyze_information_sets, expected_returns, terminal_paths
from toy_poker.games import get_game
from toy_poker.solvers.policy import extract_policy_table, load_policy, save_policy


def analytic_policy():
    return pyspiel.TabularPolicy(
        {
            "P1|A|ROOT": [(0, 0.0), (1, 1.0)],
            "P1|Q|ROOT": [(0, 0.5), (1, 0.5)],
            "P0|K|ALL_IN": [(1, 0.5), (2, 0.5)],
            "P0|K|CHECK": [(0, 1.0), (1, 0.0)],
            "P1|A|CHECK-ALL_IN": [(1, 1.0), (2, 0.0)],
            "P1|Q|CHECK-ALL_IN": [(1, 0.0), (2, 1.0)],
        }
    )


def test_exact_information_set_evs():
    plugin = get_game("akq_allin")
    game = plugin.load_game()
    policy = analytic_policy()
    infos = {row["key"]: row for row in analyze_information_sets(game, policy, plugin)}
    assert expected_returns(game, policy) == [-0.25, 0.25]
    assert infos["P0|K|ALL_IN"]["reach_probability"] == 0.75
    assert all(abs(action["ev"] + 0.5) < 1e-12 for action in infos["P0|K|ALL_IN"]["actions"])
    assert infos["P1|A|CHECK-ALL_IN"]["is_off_path"]
    paths = terminal_paths(game, policy, plugin)
    assert abs(sum(path["reach_probability"] for path in paths) - 1.0) < 1e-12


def test_policy_json_round_trip(tmp_path: Path):
    game = get_game("akq_allin").load_game()
    original = analytic_policy()
    table = extract_policy_table(game, original)
    save_policy(tmp_path, table)
    restored, restored_table = load_policy(tmp_path / "policy.json")
    assert restored_table == table
    assert expected_returns(game, restored) == expected_returns(game, original)
