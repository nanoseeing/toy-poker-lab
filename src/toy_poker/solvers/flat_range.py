"""Compile a public betting tree into compact structure-of-arrays storage."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from toy_poker.solvers.vectorized_range import _PublicNode


@dataclass(frozen=True)
class FlatPublicTree:
    nodes: tuple[_PublicNode, ...]
    players: np.ndarray
    action_offsets: np.ndarray
    children: np.ndarray
    folders: np.ndarray
    terminal_returns: np.ndarray
    matched_commitments: np.ndarray

    @property
    def num_action_slots(self) -> int:
        return int(self.children.size)


def flatten_public_tree(root: _PublicNode) -> FlatPublicTree:
    """Assign preorder node IDs and store all edges in CSR-like arrays."""
    nodes: list[_PublicNode] = []
    child_objects: list[tuple[_PublicNode, ...]] = []

    def collect(node: _PublicNode) -> None:
        nodes.append(node)
        child_objects.append(node.children)
        for child in node.children:
            collect(child)

    collect(root)
    node_ids = {id(node): index for index, node in enumerate(nodes)}
    players = np.asarray(
        [-1 if node.player is None else node.player for node in nodes], dtype=np.int32
    )
    offsets = np.zeros(len(nodes) + 1, dtype=np.int32)
    for index, children in enumerate(child_objects):
        offsets[index + 1] = offsets[index] + len(children)
    children = np.asarray(
        [node_ids[id(child)] for group in child_objects for child in group],
        dtype=np.int32,
    )
    folders = np.full(len(nodes), -1, dtype=np.int32)
    terminal_returns = np.zeros((len(nodes), 2), dtype=np.float64)
    matched = np.zeros(len(nodes), dtype=np.float64)
    for index, node in enumerate(nodes):
        if node.player is not None:
            continue
        state = node.state
        folders[index] = -1 if state._folder is None else int(state._folder)
        matched[index] = float(state.commitments[0])
        if state._folder is not None:
            terminal_returns[index] = state.returns()
    return FlatPublicTree(
        nodes=tuple(nodes),
        players=players,
        action_offsets=offsets,
        children=children,
        folders=folders,
        terminal_returns=terminal_returns,
        matched_commitments=matched,
    )
