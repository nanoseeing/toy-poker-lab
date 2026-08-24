"""Load compact metrics across completed runs."""

from __future__ import annotations

import json
from pathlib import Path


def compare_runs(directories: list[Path]) -> list[dict]:
    rows = []
    for directory in directories:
        analysis = json.loads((directory / "analysis.json").read_text(encoding="utf-8"))
        rows.append(
            {
                "run": directory.name,
                "game": analysis["game"]["id"],
                "solver": analysis["solver"]["id"],
                "iterations": analysis["solver"]["iterations"],
                "exploitability": analysis["summary"]["exploitability"],
                "returns": analysis["summary"]["returns"],
            }
        )
    return rows
