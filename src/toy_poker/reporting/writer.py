"""Write normalized analysis data and visual reports."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pyspiel

from toy_poker.games.base import GamePlugin
from toy_poker.reporting.html import save_html
from toy_poker.reporting.plots import (
    save_convergence_plot,
    save_ev_plot,
    save_strategy_plot,
    save_tree_plot,
)


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_report_bundle(
    directory: Path,
    analysis: dict,
    game: pyspiel.Game,
    policy: pyspiel.Policy,
    plugin: GamePlugin,
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    figures = directory / "figures"
    figures.mkdir(exist_ok=True)
    serialized = json.dumps(analysis, indent=2, ensure_ascii=False)
    (directory / "analysis.json").write_text(serialized, encoding="utf-8")
    # Compatibility with the first AKQ report schema filename.
    (directory / "results.json").write_text(serialized, encoding="utf-8")

    info_rows = []
    for info in analysis["information_sets"]:
        for action in info["actions"]:
            info_rows.append(
                {
                    "information_state": info["key"], "label": info["label"],
                    "player": info["player"], "card": info["card"],
                    "history": " -> ".join(info["history"]) or "ROOT",
                    "reach_probability": info["reach_probability"], "is_off_path": info["is_off_path"],
                    "ev_belief": info["ev_belief"], "policy_ev": info["policy_ev"],
                    "action": action["action"], "action_probability": action["probability"],
                    "action_ev": action["ev"], "ev_vs_policy": action["ev_vs_policy"],
                    "ev_vs_best": action["ev_vs_best"],
                }
            )
    _write_csv(directory / "information_sets.csv", info_rows, list(info_rows[0]))

    terminal_rows = []
    for path in analysis["terminal_paths"]:
        row = {
            "chance": " -> ".join(path["chance"]),
            "actions": " -> ".join(path["actions"]),
            "reach_probability": path["reach_probability"],
        }
        row.update({f"return_{name.lower()}": value for name, value in path["returns"].items()})
        terminal_rows.append(row)
    _write_csv(directory / "terminal_paths.csv", terminal_rows, list(terminal_rows[0]))

    convergence_rows = []
    for snapshot in analysis["convergence"]:
        row = {"iteration": snapshot["iteration"], "exploitability": snapshot["exploitability"]}
        row.update(
            {
                f"return_{plugin.player_name(player).lower()}": value
                for player, value in enumerate(snapshot["returns"])
            }
        )
        convergence_rows.append(row)
    _write_csv(directory / "convergence.csv", convergence_rows, list(convergence_rows[0]))

    save_strategy_plot(figures / "strategy_probabilities.png", analysis["information_sets"], plugin.metadata.title)
    save_ev_plot(figures / "action_ev.png", analysis["information_sets"], plugin.metadata.utility_unit)
    save_convergence_plot(
        figures / "convergence.png",
        analysis["convergence"],
        plugin,
        analysis["game"].get("analytic_returns"),
    )
    tree_created = save_tree_plot(figures / "strategy_tree.png", game, policy, plugin)
    save_html(directory / "report.html", analysis, plugin, tree_created)
