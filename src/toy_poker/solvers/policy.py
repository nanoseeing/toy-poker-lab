"""Portable serialization for OpenSpiel tabular policies."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pyspiel


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


def load_policy(path: Path) -> tuple[pyspiel.TabularPolicy, PolicyTable]:
    data = json.loads(path.read_text(encoding="utf-8"))
    table = {
        key: [(int(item["action_id"]), float(item["probability"])) for item in actions]
        for key, actions in data.items()
    }
    return standalone_policy(table), table
