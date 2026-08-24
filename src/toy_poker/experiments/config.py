"""TOML experiment configuration."""

from __future__ import annotations

import json
import math
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
    report_scope: str = "full"
    policy_format: str = "json_csv"


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
                algorithm=str(solver.get("algorithm", "cfr_plus")),
                iterations=int(solver.get("iterations", 10_000)),
                snapshot_every=int(solver.get("snapshot_every", 1_000)),
                early_stopping=bool(solver.get("early_stopping", True)),
                target_exploitability=float(
                    solver.get("target_exploitability", 1e-5)
                ),
                min_iterations=int(solver.get("min_iterations", 1_000)),
                patience_checkpoints=int(solver.get("patience_checkpoints", 2)),
                dcfr_alpha=float(solver.get("dcfr_alpha", 1.5)),
                dcfr_beta=float(solver.get("dcfr_beta", 0.0)),
                dcfr_gamma=float(solver.get("dcfr_gamma", 2.0)),
                precision=str(solver.get("precision", "float64")),
            ),
            analysis=AnalysisConfig(
                mode=str(analysis.get("mode", "exact_tree")),
                off_path_threshold=float(analysis.get("off_path_threshold", 1e-8)),
                major_reach_threshold=float(
                    analysis.get("major_reach_threshold", 1e-4)
                ),
                report_scope=str(analysis.get("report_scope", "full")),
                policy_format=str(analysis.get("policy_format", "json_csv")),
            ),
            artifact_root=Path(output.get("artifact_root", "artifacts")),
        )
        config.validate()
        return config

    def validate(self) -> None:
        if self.solver.iterations <= 0 or self.solver.snapshot_every <= 0:
            raise ValueError("iterations and snapshot_every must be positive")
        if self.solver.min_iterations < 0:
            raise ValueError("min_iterations cannot be negative")
        if (
            not math.isfinite(self.solver.target_exploitability)
            or self.solver.target_exploitability <= 0
        ):
            raise ValueError("target_exploitability must be positive and finite")
        if self.solver.patience_checkpoints <= 0:
            raise ValueError("patience_checkpoints must be positive")
        if self.solver.algorithm not in {"cfr_plus", "dcfr"}:
            raise ValueError("solver.algorithm must be 'cfr_plus' or 'dcfr'")
        if not all(
            math.isfinite(value)
            for value in (
                self.solver.dcfr_alpha,
                self.solver.dcfr_beta,
                self.solver.dcfr_gamma,
            )
        ):
            raise ValueError("DCFR exponents must be finite")
        if self.solver.precision not in {"float64", "float32"}:
            raise ValueError("solver.precision must be 'float64' or 'float32'")
        if self.solver.precision == "float32" and self.solver.backend != "cpp_range":
            raise ValueError("float32 storage is currently supported only by cpp_range")
        if self.solver.backend not in {
            "python_game",
            "native_efg",
            "vectorized_range",
            "cpp_range",
        }:
            raise ValueError(
                "solver.backend must be 'python_game', 'native_efg', "
                "'vectorized_range', or 'cpp_range'"
            )
        if self.solver.algorithm == "dcfr" and self.solver.backend not in {
            "vectorized_range",
            "cpp_range",
        }:
            raise ValueError(
                "DCFR is currently supported only by vectorized_range and cpp_range"
            )
        if self.analysis.mode != "exact_tree":
            raise ValueError("Only analysis.mode='exact_tree' is implemented")
        if self.analysis.off_path_threshold < 0:
            raise ValueError("off_path_threshold cannot be negative")
        if not 0 <= self.analysis.major_reach_threshold <= 1:
            raise ValueError("major_reach_threshold must be between 0 and 1")
        if self.analysis.report_scope not in {"full", "major_only"}:
            raise ValueError("analysis.report_scope must be 'full' or 'major_only'")
        if self.analysis.policy_format not in {"json_csv", "npz"}:
            raise ValueError("analysis.policy_format must be 'json_csv' or 'npz'")

    def to_dict(self) -> dict:
        data = asdict(self)
        data["artifact_root"] = str(self.artifact_root)
        return data

    def canonical_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
