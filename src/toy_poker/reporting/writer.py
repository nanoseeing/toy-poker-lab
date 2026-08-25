"""Write normalized analysis data and visual reports."""

from __future__ import annotations

import csv
import gzip
import json
from pathlib import Path

import pyspiel

from toy_poker.games.base import GamePlugin
from toy_poker.reporting.html import save_html
from toy_poker.reporting.markdown import save_markdown
from toy_poker.reporting.plots import (
    save_convergence_plot,
    save_ev_plot,
    save_range_ev_plot,
    save_range_strategy_plot,
    save_rank_distribution_plot,
    save_strategy_plot,
    save_tree_plot,
)
from toy_poker.reporting.strategy_viewer import save_strategy_viewer


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    opener = gzip.open if path.suffix == ".gz" else Path.open
    with opener(path, "wt" if path.suffix == ".gz" else "w", newline="", encoding="utf-8") as handle:
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
    reporting = analysis.setdefault("reporting", {})
    major_reach_threshold = float(
        reporting.setdefault("major_reach_threshold", 1e-4)
    )
    major_infos = [
        info
        for info in analysis["information_sets"]
        if info["reach_probability"] >= major_reach_threshold
    ]
    major_only = reporting.setdefault("report_scope", "full") == "major_only"
    reporting["analysis_filename"] = (
        "analysis.json.gz" if major_only else "analysis.json"
    )
    reporting["information_sets_filename"] = (
        "information_sets.csv.gz" if major_only else "information_sets.csv"
    )
    reporting["terminal_paths_filename"] = (
        "terminal_paths.csv.gz" if major_only else "terminal_paths.csv"
    )
    viewer_created = False
    if bool(reporting.setdefault("interactive_viewer", True)):
        viewer_created = save_strategy_viewer(
            directory / "strategy_viewer.html",
            analysis,
            plugin,
            grid_columns=int(reporting.setdefault("viewer_grid_columns", 10)),
        )
    reporting["strategy_viewer_filename"] = (
        "strategy_viewer.html" if viewer_created else None
    )
    serialized = json.dumps(analysis, indent=2, ensure_ascii=False)
    if major_only:
        with gzip.open(directory / "analysis.json.gz", "wt", encoding="utf-8") as handle:
            handle.write(serialized)
    else:
        (directory / "analysis.json").write_text(serialized, encoding="utf-8")
    # Compatibility with the first AKQ report schema filename.
    if not major_only:
        (directory / "results.json").write_text(serialized, encoding="utf-8")

    info_rows = []
    for info in analysis["information_sets"]:
        for action in info["actions"]:
            info_rows.append(
                {
                    "information_state": info["key"], "label": info["label"],
                    "player": info["player"], "card": info["card"],
                    "history": " -> ".join(info["history"]) or "ROOT",
                    "context": json.dumps(info.get("context", {}), ensure_ascii=False),
                    "reach_probability": info["reach_probability"], "is_off_path": info["is_off_path"],
                    "ev_belief": info["ev_belief"], "policy_ev": info["policy_ev"],
                    "action": action["action"], "action_probability": action["probability"],
                    "action_ev": action["ev"], "ev_vs_policy": action["ev_vs_policy"],
                    "ev_vs_best": action["ev_vs_best"],
                }
            )
    _write_csv(
        directory / reporting["information_sets_filename"],
        info_rows,
        list(info_rows[0]),
    )

    terminal_rows = []
    for path in analysis["terminal_paths"]:
        row = {
            "chance": " -> ".join(path["chance"]),
            "actions": " -> ".join(path["actions"]),
            "reach_probability": path["reach_probability"],
        }
        row.update({f"return_{name.lower()}": value for name, value in path["returns"].items()})
        terminal_rows.append(row)
    _write_csv(
        directory / reporting["terminal_paths_filename"],
        terminal_rows,
        list(terminal_rows[0]),
    )

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

    rank_distribution = analysis["game"].get("rank_distribution")
    if rank_distribution is not None:
        distribution_rows = [
            {
                "rank": rank,
                "oop_probability": oop_probability,
                "ip_probability": ip_probability,
            }
            for rank, oop_probability, ip_probability in zip(
                rank_distribution["ranks"],
                rank_distribution["OOP"],
                rank_distribution["IP"],
            )
        ]
        _write_csv(
            directory / "rank_distribution.csv",
            distribution_rows,
            list(distribution_rows[0]),
        )
        save_rank_distribution_plot(
            figures / "rank_distribution.png", rank_distribution
        )

    if getattr(plugin, "numeric_range_strategy", False):
        if not major_only:
            save_range_strategy_plot(
                figures / "strategy_probabilities.png",
                analysis["information_sets"],
                plugin.metadata.title,
            )
        save_range_strategy_plot(
            figures / "major_strategy_probabilities.png",
            major_infos,
            plugin.metadata.title,
            scope=f"major strategy (reach >= {major_reach_threshold:.4%})",
        )
        save_range_ev_plot(
            figures / "action_ev.png",
            major_infos if major_only else analysis["information_sets"],
            plugin.metadata.utility_unit,
        )
    else:
        if not major_only:
            save_strategy_plot(
                figures / "strategy_probabilities.png",
                analysis["information_sets"],
                plugin.metadata.title,
            )
        save_strategy_plot(
            figures / "major_strategy_probabilities.png",
            major_infos,
            plugin.metadata.title,
            scope=f"major strategy (reach >= {major_reach_threshold:.4%})",
        )
        save_ev_plot(
            figures / "action_ev.png",
            major_infos if major_only else analysis["information_sets"],
            plugin.metadata.utility_unit,
        )
    save_convergence_plot(
        figures / "convergence.png",
        analysis["convergence"],
        plugin,
        analysis["game"].get("analytic_returns"),
        analysis["solver"].get("target_exploitability"),
        (
            analysis["solver"].get("completed_iterations")
            if analysis["solver"].get("early_stopped")
            else None
        ),
    )
    tree_created = False
    if not major_only:
        tree_created = save_tree_plot(
            figures / "strategy_tree.png",
            game,
            policy,
            plugin,
            public_tree=analysis.get("public_tree"),
        )
    major_tree_created = save_tree_plot(
        figures / "major_strategy_tree.png",
        game,
        policy,
        plugin,
        min_reach=major_reach_threshold,
        public_tree=analysis.get("public_tree"),
    )
    save_html(
        directory / "report.html",
        analysis,
        plugin,
        tree_created,
        major_tree_created,
        viewer_created,
    )
    save_markdown(
        directory / "report.md",
        analysis,
        plugin,
        tree_created,
        major_tree_created,
        viewer_created,
    )
