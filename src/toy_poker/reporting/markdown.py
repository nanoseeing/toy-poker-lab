"""Git-friendly Markdown report renderer."""

from __future__ import annotations

import html
from pathlib import Path

from toy_poker.games.base import GamePlugin


def _text(value: object) -> str:
    """Escape a value for use inside a GitHub-flavored Markdown table cell."""
    return html.escape(str(value), quote=False).replace("|", "\\|").replace("\n", "<br>")


def _number(value: object) -> str:
    return f"{value:.6g}" if isinstance(value, float) else str(value)


def _information_table(information_sets: list[dict]) -> str:
    rows = [
        "| Decision | Reach | Strategy | Policy EV | Action EV |",
        "|---|---:|---|---:|---|",
    ]
    for info in information_sets:
        label = _text(info["label"])
        if info["is_off_path"]:
            label += " · `off path`"
        context = ", ".join(
            f"{_text(key)}={_text(_number(value))}"
            for key, value in info.get("context", {}).items()
        )
        if context:
            label += f"<br><sub>{context}</sub>"
        strategy = "<br>".join(
            f"{_text(action['action'])}: **{action['probability']:.2%}**"
            for action in info["actions"]
        )
        action_evs = "<br>".join(
            f"{_text(action['action'])}: {action['ev']:+.6f}"
            for action in info["actions"]
        )
        rows.append(
            f"| {label} | {info['reach_probability']:.6%} | {strategy} | "
            f"{info['policy_ev']:+.6f} | {action_evs} |"
        )
    return "\n".join(rows)


def save_markdown(
    path: Path,
    analysis: dict,
    plugin: GamePlugin,
    tree_created: bool,
    major_tree_created: bool,
    viewer_created: bool = False,
    public_bundle: bool = False,
) -> None:
    """Write a report that renders directly in GitHub's repository view."""
    summary = analysis["summary"]
    solver = analysis["solver"]
    reporting = analysis.get("reporting", {})
    major_reach_threshold = float(reporting.get("major_reach_threshold", 1e-4))
    major_information_sets = [
        info
        for info in analysis["information_sets"]
        if info["reach_probability"] >= major_reach_threshold
    ]
    major_only = reporting.get("report_scope", "full") == "major_only"
    completed_iterations = solver.get("completed_iterations", solver["iterations"])
    requested_iterations = solver.get("requested_iterations", solver["iterations"])
    target_exploitability = solver.get("target_exploitability")
    target_text = (
        "—"
        if target_exploitability is None
        else f"`{float(target_exploitability):.1e}`"
    )
    returns = "\n".join(
        f"| {_text(player)} EV | {value:+.6f} |"
        for player, value in summary["returns"].items()
    )
    unconstrained_rows = (
        [
            f"| Unconstrained exploitability | "
            f"{float(summary['unconstrained_exploitability']):.8g} |"
        ]
        if summary.get("unconstrained_exploitability") is not None
        else []
    )

    sections = [
        f"# {_text(plugin.metadata.title)}",
        "",
        f"EV is {_text(plugin.metadata.utility_unit)} for the acting player, conditional "
        "on reaching the information set. "
        f"{_text(plugin.metadata.utility_convention)} This game has terminal utility sum "
        f"{analysis['game'].get('utility_sum', 1.0):g}.",
        "",
        "## Solver summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Iterations | {completed_iterations:,} / {requested_iterations:,} |",
        f"| {'Constrained Nash gap' if solver.get('exploitability_definition') == 'constrained_nash_gap' else 'Exploitability'} | {summary['exploitability']:.8g} |",
        *unconstrained_rows,
        returns,
        "",
        f"- Backend: `{_text(solver['backend'])}`",
        f"- Algorithm: `{_text(solver.get('algorithm', 'cfr_plus'))}`",
        "- Checkpoint evaluation: "
        f"`{_text(solver.get('checkpoint_evaluation_backend', solver['backend']))}`",
        f"- Stop reason: `{_text(solver.get('stop_reason', 'max_iterations'))}`",
        f"- Target exploitability: {target_text}",
        "- Best checkpoint: "
        f"`{solver.get('best_exploitability', summary['exploitability']):.8g}` at "
        f"iteration {solver.get('best_iteration', solver.get('iterations', 0)):,}",
        "",
    ]

    node_locks = solver.get("node_locks", [])
    if node_locks:
        lock_lines = []
        for lock in node_locks:
            actions = ", ".join(
                f"{_text(action)} {float(probability):.2%}"
                for action, probability in lock["actions"].items()
            )
            lock_lines.append(
                f"- `{_text(lock['player'])}` rank `{lock['rank']}` at "
                f"`{_text(lock['history'])}`: {actions}"
            )
        sections.extend(
            [
                "### Node locks",
                "",
                *lock_lines,
                "",
                "The convergence metric is the constrained Nash gap: locked actions "
                "cannot be changed by the best response.",
                "",
            ]
        )

    if viewer_created:
        sections.extend(
            [
                "> [Interactive strategy viewer](strategy_viewer.html) — 履歴を選び、"
                "各private numberの混合戦略とAction EVを確認できます。",
                "",
            ]
        )
    if analysis["game"].get("rank_distribution") is not None:
        sections.extend(
            [
                "## Private-number distributions",
                "",
                "![Private-number distributions](figures/rank_distribution.png)",
                "",
            ]
        )

    sections.extend(
        [
            "## Major strategy",
            "",
            "Information sets and tree nodes with reach probability below "
            f"{major_reach_threshold:.4%} are omitted here. Showing "
            f"{len(major_information_sets)} of {len(analysis['information_sets'])} "
            "information sets. All actions at a retained information set remain visible.",
            "",
        ]
    )
    if major_tree_created:
        sections.extend(
            [
                "### Major action tree",
                "",
                "![Major strategy tree](figures/major_strategy_tree.png)",
                "",
            ]
        )
    sections.extend(
        [
            "### Major action probabilities",
            "",
            "![Major action probabilities](figures/major_strategy_probabilities.png)",
            "",
            "### Major information sets",
            "",
            _information_table(major_information_sets),
            "",
        ]
    )
    if major_only:
        sections.extend(
            [
                "### Major action EV",
                "",
                "![Major action EV](figures/action_ev.png)",
                "",
            ]
        )
    else:
        sections.extend(["## Full analysis", ""])
        if tree_created:
            sections.extend(
                [
                    "### Full legal-action tree",
                    "",
                    "![Full strategy tree](figures/strategy_tree.png)",
                    "",
                ]
            )
        sections.extend(
            [
                "### Full action probabilities",
                "",
                "![Full action probabilities](figures/strategy_probabilities.png)",
                "",
                "### Full information sets",
                "",
                _information_table(analysis["information_sets"]),
                "",
                "### Full action EV",
                "",
                "![Action EV](figures/action_ev.png)",
                "",
            ]
        )

    sections.extend(
        [
            "## Convergence",
            "",
            "![Convergence](figures/convergence.png)",
            "",
            "## Reproducibility",
            "",
        ]
    )
    if public_bundle:
        sections.extend(
            [
                "- [Summary](summary.json)",
                "- [Resolved configuration](resolved_config.json)",
                "- [Source manifest](manifest.json)",
            ]
        )
    else:
        policy_filename = reporting.get("policy_filename", "policy.json")
        analysis_filename = reporting.get("analysis_filename", "analysis.json")
        information_sets_filename = reporting.get(
            "information_sets_filename", "information_sets.csv"
        )
        terminal_paths_filename = reporting.get(
            "terminal_paths_filename", "terminal_paths.csv"
        )
        sections.extend(
            [
                f"- [Analysis data]({analysis_filename})",
                f"- [Policy]({policy_filename})",
                f"- [Information sets]({information_sets_filename})",
                f"- [Terminal paths]({terminal_paths_filename})",
                "- [Convergence data](convergence.csv)",
            ]
        )
        if analysis["game"].get("rank_distribution") is not None:
            sections.append("- [Rank distribution](rank_distribution.csv)")
    sections.extend(
        [
            "- [Resolved configuration](resolved_config.json)",
            "- [Source manifest](manifest.json)",
            "- [Standalone HTML report](report.html)",
            "",
        ]
    )
    path.write_text("\n".join(sections), encoding="utf-8")
