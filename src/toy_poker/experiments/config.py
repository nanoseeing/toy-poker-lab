"""TOML experiment configuration."""

from __future__ import annotations

import json
import tomllib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from toy_poker.solvers.result import SolverConfig


@dataclass(frozen=True)
class AnalysisConfig:
    mode: str = "exact_tree"
    off_path_threshold: float = 1e-8
    major_reach_threshold: float = 1e-4


@dataclass(frozen=True)
class ExperimentConfig:
    name: str
    game_id: str
    game_params: dict[str, Any] = field(default_factory=dict)
    solver: SolverConfig = field(default_factory=SolverConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    artifact_root: Path = Path("artifacts")

    @classmethod
    def from_toml(cls, path: Path) -> "ExperimentConfig":
        with path.open("rb") as handle:
            data = tomllib.load(handle)
        experiment = data.get("experiment", {})
        game = data.get("game", {})
        solver = data.get("solver", {})
        analysis = data.get("analysis", {})
        output = data.get("output", {})
        if "name" not in experiment or "id" not in game:
            raise ValueError("Config requires [experiment].name and [game].id")
        config = cls(
            name=str(experiment["name"]),
            game_id=str(game["id"]),
            game_params=dict(game.get("params", {})),
            solver=SolverConfig(
                solver_id=str(solver.get("id", "cfr_plus")),
                backend=str(solver.get("backend", "native_efg")),
                iterations=int(solver.get("iterations", 100_000)),
                snapshot_every=int(solver.get("snapshot_every", 1_000)),
            ),
            analysis=AnalysisConfig(
                mode=str(analysis.get("mode", "exact_tree")),
                off_path_threshold=float(analysis.get("off_path_threshold", 1e-8)),
                major_reach_threshold=float(
                    analysis.get("major_reach_threshold", 1e-4)
                ),
            ),
            artifact_root=Path(output.get("artifact_root", "artifacts")),
        )
        config.validate()
        return config

    def validate(self) -> None:
        if self.solver.iterations <= 0 or self.solver.snapshot_every <= 0:
            raise ValueError("iterations and snapshot_every must be positive")
        if self.solver.backend not in {"python_game", "native_efg"}:
            raise ValueError("solver.backend must be 'python_game' or 'native_efg'")
        if self.analysis.mode != "exact_tree":
            raise ValueError("Only analysis.mode='exact_tree' is implemented")
        if self.analysis.off_path_threshold < 0:
            raise ValueError("off_path_threshold cannot be negative")
        if not 0 <= self.analysis.major_reach_threshold <= 1:
            raise ValueError("major_reach_threshold must be between 0 and 1")

    def to_dict(self) -> dict:
        data = asdict(self)
        data["artifact_root"] = str(self.artifact_root)
        return data

    def canonical_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
