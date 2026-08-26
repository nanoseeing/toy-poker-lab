"""Solver configuration and result models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pyspiel


@dataclass(frozen=True)
class NodeLock:
    """A fixed behavioral strategy at one private-rank information set."""

    player: str
    rank: int
    history: str
    action_probabilities: tuple[tuple[str, float], ...]


@dataclass(frozen=True)
class SolverConfig:
    solver_id: str = "cfr_plus"
    backend: str = "native_efg"
    algorithm: str = "cfr_plus"
    iterations: int = 10_000
    snapshot_every: int = 1_000
    early_stopping: bool = True
    target_exploitability: float = 1e-5
    min_iterations: int = 1_000
    patience_checkpoints: int = 2
    dcfr_alpha: float = 1.5
    dcfr_beta: float = 0.0
    dcfr_gamma: float = 2.0
    precision: str = "float64"
    node_locks: tuple[NodeLock, ...] = ()


@dataclass
class SolveResult:
    policy: pyspiel.TabularPolicy
    policy_table: dict[str, list[tuple[int, float]]]
    convergence: list[dict[str, Any]]
    elapsed_seconds: float
    checkpoint_evaluation_backend: str
    completed_iterations: int
    early_stopped: bool
    stop_reason: str
    best_exploitability: float
    best_iteration: int
