"""Portable serialization for OpenSpiel tabular policies."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pyspiel
import numpy as np


PolicyTable = dict[str, list[tuple[int, float]]]


def extract_policy_table(game: pyspiel.Game, policy: pyspiel.Policy) -> PolicyTable:
    table: PolicyTable = {}

    def visit(state: pyspiel.State) -> None:
        if state.is_terminal():
            return
        if state.is_chance_node():
            for action, _ in state.chance_outcomes():
                visit(state.child(action))
            return
        player = state.current_player()
        key = state.information_state_string(player)
        if key not in table:
            probabilities = policy.action_probabilities(state)
            table[key] = [
                (int(action), float(probabilities.get(action, 0.0)))
                for action in state.legal_actions()
            ]
        for action in state.legal_actions():
            visit(state.child(action))

    visit(game.new_initial_state())
    return table


def standalone_policy(table: PolicyTable) -> pyspiel.TabularPolicy:
    return pyspiel.TabularPolicy(table)


def clone_policy(game: pyspiel.Game, policy: pyspiel.Policy) -> tuple[pyspiel.TabularPolicy, PolicyTable]:
    table = extract_policy_table(game, policy)
    return standalone_policy(table), table


def save_policy(directory: Path, table: PolicyTable) -> None:
    json_data = {
        key: [{"action_id": action, "probability": probability} for action, probability in actions]
        for key, actions in sorted(table.items())
    }
    (directory / "policy.json").write_text(
        json.dumps(json_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    with (directory / "policy.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["information_state", "action_id", "probability"])
        writer.writeheader()
        for key, actions in sorted(table.items()):
            for action, probability in actions:
                writer.writerow(
                    {"information_state": key, "action_id": action, "probability": probability}
                )


def save_policy_npz(directory: Path, table: PolicyTable) -> None:
    """Store a policy compactly without pickle or per-action JSON objects."""
    keys = sorted(table)
    offsets = np.zeros(len(keys) + 1, dtype=np.int64)
    for index, key in enumerate(keys):
        offsets[index + 1] = offsets[index] + len(table[key])
    actions = np.asarray(
        [action for key in keys for action, _ in table[key]], dtype=np.int32
    )
    probabilities = np.asarray(
        [probability for key in keys for _, probability in table[key]],
        dtype=np.float64,
    )
    np.savez_compressed(
        directory / "policy.npz",
        keys=np.asarray(keys, dtype=np.str_),
        offsets=offsets,
        actions=actions,
        probabilities=probabilities,
    )


def load_policy(path: Path) -> tuple[pyspiel.TabularPolicy, PolicyTable]:
    if path.suffix == ".npz":
        with np.load(path, allow_pickle=False) as data:
            keys = data["keys"]
            offsets = data["offsets"]
            actions = data["actions"]
            probabilities = data["probabilities"]
            table = {
                str(key): [
                    (int(actions[item]), float(probabilities[item]))
                    for item in range(int(offsets[index]), int(offsets[index + 1]))
                ]
                for index, key in enumerate(keys)
            }
        return standalone_policy(table), table
    data = json.loads(path.read_text(encoding="utf-8"))
    table = {
        key: [(int(item["action_id"]), float(item["probability"])) for item in actions]
        for key, actions in data.items()
    }
    return standalone_policy(table), table
