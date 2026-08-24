"""Immutable run directory and reproducibility metadata helpers."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from toy_poker import __version__
from toy_poker.experiments.config import ExperimentConfig


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def config_hash(config: ExperimentConfig) -> str:
    return hashlib.sha256(config.canonical_json().encode("utf-8")).hexdigest()


def new_run_directory(config: ExperimentConfig) -> tuple[Path, str]:
    digest = config_hash(config)[:8]
    run_id = f"{utc_now().strftime('%Y%m%dT%H%M%S%fZ')}_{digest}"
    directory = config.artifact_root / config.game_id / run_id
    directory.mkdir(parents=True, exist_ok=False)
    return directory, run_id


def git_commit() -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else None


def manifest(config: ExperimentConfig, run_id: str, elapsed_seconds: float) -> dict:
    return {
        "schema_version": 1,
        "run_id": run_id,
        "experiment_name": config.name,
        "created_at": utc_now().isoformat(),
        "config_sha256": config_hash(config),
        "toy_poker_version": __version__,
        "open_spiel_version": importlib.metadata.version("open_spiel"),
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "git_commit": git_commit(),
        "elapsed_seconds": elapsed_seconds,
    }


def write_latest_pointer(config: ExperimentConfig, run_directory: Path, run_id: str) -> None:
    game_root = config.artifact_root / config.game_id
    game_root.mkdir(parents=True, exist_ok=True)
    pointer = {"run_id": run_id, "path": str(run_directory.resolve())}
    (game_root / "latest.json").write_text(
        json.dumps(pointer, indent=2, ensure_ascii=False), encoding="utf-8"
    )
