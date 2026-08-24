from pathlib import Path

import pytest

from toy_poker.solvers.policy import load_policy, save_policy_npz


def test_policy_npz_round_trip(tmp_path: Path):
    table = {
        "P0|1|ROOT": [(0, 0.25), (3, 0.75)],
        "P1|2|CHECK": [(1, 0.0), (2, 1.0)],
    }
    save_policy_npz(tmp_path, table)
    _, loaded = load_policy(tmp_path / "policy.npz")

    assert loaded.keys() == table.keys()
    for key, actions in table.items():
        assert dict(loaded[key]) == pytest.approx(dict(actions))
