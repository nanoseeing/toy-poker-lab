"""Solver configuration and result models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pyspiel


@dataclass(frozen=True)
class SolverConfig:
    solver_id: str = "cfr_plus"
    backend: str = "python_game"
    iterations: int = 100_000
    snapshot_every: int = 1_000


@dataclass
class SolveResult:
    policy: pyspiel.TabularPolicy
    policy_table: dict[str, list[tuple[int, float]]]
    convergence: list[dict[str, Any]]
    elapsed_seconds: float
