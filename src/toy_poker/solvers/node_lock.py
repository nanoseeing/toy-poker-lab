"""Resolve human-readable node-lock specifications onto a public range tree."""

from __future__ import annotations

import math
import re

import numpy as np

from toy_poker.games.fixed_range_one_street import (
    PLAYER_IP,
    PLAYER_OOP,
    FixedRangeOneStreetGame,
)
from toy_poker.solvers.result import NodeLock


def _normalized_action(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def apply_node_locks(
    game: FixedRangeOneStreetGame,
    nodes: list,
    locks: tuple[NodeLock, ...],
) -> None:
    """Attach NaN-masked locked strategy matrices to matching public nodes."""
    if not locks:
        return
    rank_indexes = {rank: index for index, rank in enumerate(game.cards)}
    for lock in locks:
        player = PLAYER_OOP if lock.player == "OOP" else PLAYER_IP
        if lock.rank not in rank_indexes:
            raise ValueError(
                f"node lock rank {lock.rank} is outside the game range "
                f"{game.min_card}..{game.max_card}"
            )
        matches = [
            node
            for node in nodes
            if node.player == player
            and (("-".join(node.state.history_tokens) or "ROOT").upper() == lock.history)
        ]
        if len(matches) != 1:
            raise ValueError(
                f"node lock {lock.player} rank {lock.rank} history {lock.history!r} "
                f"matched {len(matches)} public nodes"
            )
        node = matches[0]
        if node.locked_strategy is None:
            node.locked_strategy = np.full(
                (game.num_ranks, len(node.actions)), np.nan, dtype=float
            )
        rank_index = rank_indexes[lock.rank]
        if np.isfinite(node.locked_strategy[rank_index]).any():
            raise ValueError(
                f"duplicate node lock for {lock.player} rank {lock.rank} at {lock.history}"
            )
        available: dict[str, int] = {}
        for action_index, action in enumerate(node.actions):
            available[str(action)] = action_index
            label = node.state._action_to_string(node.player, action)
            available[_normalized_action(label)] = action_index
            available[_normalized_action(node.state._history_token(action))] = action_index
        row = np.zeros(len(node.actions), dtype=float)
        used_indexes = set()
        for action_name, probability in lock.action_probabilities:
            key = action_name if action_name in available else _normalized_action(action_name)
            if key not in available:
                legal = [
                    node.state._action_to_string(node.player, action)
                    for action in node.actions
                ]
                raise ValueError(
                    f"unknown locked action {action_name!r} at {lock.history}; "
                    f"legal actions are {legal}"
                )
            action_index = available[key]
            if action_index in used_indexes:
                raise ValueError(f"duplicate locked action alias: {action_name!r}")
            used_indexes.add(action_index)
            row[action_index] = probability
        if any(not math.isfinite(value) or value < 0 for value in row):
            raise ValueError("node lock probabilities must be finite and nonnegative")
        if not math.isclose(float(row.sum()), 1.0, abs_tol=1e-12):
            raise ValueError("node lock action probabilities must sum to 1")
        node.locked_strategy[rank_index] = row


def locked_rows(node) -> np.ndarray | None:
    if node.locked_strategy is None:
        return None
    return np.isfinite(node.locked_strategy).all(axis=1)
