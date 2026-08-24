"""Generic plots built from normalized analysis data."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pyspiel

from toy_poker.analysis.information_sets import display_action
from toy_poker.games.base import GamePlugin

ACTION_COLORS = {
    "Check": "#4C78A8",
    "All-in": "#F58518",
    "Call": "#54A24B",
    "Fold": "#9D9DA1",
}


def action_color(action: str) -> str:
    return ACTION_COLORS.get(action, "#B279A2")


def save_strategy_plot(path: Path, infos: list[dict], title: str) -> None:
    labels = [info["label"] for info in infos]
    height = max(4.5, 1.0 + len(infos) * 0.9)
    fig, ax = plt.subplots(figsize=(12, height))
    for row, info in enumerate(infos):
        left = 0.0
        for action in info["actions"]:
            probability = action["probability"]
            ax.barh(
                row,
                probability,
                left=left,
                color=action_color(action["action"]),
                edgecolor="white",
                height=0.65,
            )
            if probability >= 0.04:
                text_color = "#222222" if action["action"] == "Fold" else "white"
                ax.text(
                    left + probability / 2,
                    row,
                    f"{action['action']}\n{probability:.1%}",
                    ha="center",
                    va="center",
                    fontsize=9,
                    color=text_color,
                    fontweight="bold",
                )
            left += probability
    ax.set_yticks(range(len(labels)), labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    ax.set_xlabel("Action probability")
    ax.set_title(f"{title}: average strategy")
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_ev_plot(path: Path, infos: list[dict], utility_unit: str) -> None:
    labels = [info["label"] for info in infos]
    all_evs = [action["ev"] for info in infos for action in info["actions"]]
    padding = max(0.2, (max(all_evs) - min(all_evs)) * 0.1)
    fig, ax = plt.subplots(figsize=(12, max(5.0, 1.0 + len(infos))))
    for row, info in enumerate(infos):
        count = len(info["actions"])
        offsets = [0.0] if count == 1 else [(-0.18 + 0.36 * i / (count - 1)) for i in range(count)]
        for offset, action in zip(offsets, info["actions"]):
            ev = action["ev"]
            y = row + offset
            ax.scatter(ev, y, s=90, color=action_color(action["action"]), edgecolor="white", zorder=3)
            ax.text(ev + padding * 0.12, y, f"{action['action']} {ev:+.3f}", va="center", fontsize=9)
        ax.scatter(info["policy_ev"], row, marker="|", s=250, color="#222222", linewidth=2, zorder=4)
    ax.axvline(0, color="#555555", linewidth=1)
    ax.set_yticks(range(len(labels)), labels)
    ax.invert_yaxis()
    ax.set_xlim(min(all_evs) - padding, max(all_evs) + padding * 1.8)
    ax.set_xlabel(f"EV for the acting player ({utility_unit})")
    ax.set_title("Action EV conditional on reaching each information set")
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_convergence_plot(path: Path, convergence: list[dict], plugin: GamePlugin) -> None:
    iterations = [row["iteration"] for row in convergence]
    gaps = [row["exploitability"] for row in convergence]
    analytic = plugin.metadata.analytic_returns
    rows = 2 if analytic is not None else 1
    fig, axes = plt.subplots(rows, 1, figsize=(10, 7.5 if rows == 2 else 4.5), sharex=True, squeeze=False)
    ax_gap = axes[0][0]
    ax_gap.semilogy(iterations, gaps, color="#E45756", linewidth=2)
    ax_gap.set_ylabel("Exploitability")
    ax_gap.set_title("Solver convergence")
    ax_gap.grid(alpha=0.25)
    if analytic is not None:
        max_error = [
            max(abs(value - target) for value, target in zip(row["returns"], analytic))
            for row in convergence
        ]
        ax_error = axes[1][0]
        ax_error.semilogy(iterations, max_error, color="#4C78A8", linewidth=2)
        ax_error.set_ylabel("Max absolute EV error")
        ax_error.set_title("Error from analytic game value")
        ax_error.grid(alpha=0.25)
    axes[-1][0].set_xlabel("Solver iterations")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _tree(state: pyspiel.State, policy: pyspiel.Policy, plugin: GamePlugin):
    nodes: list[dict] = []
    edges: list[tuple[int, int, str, float]] = []

    def build(current: pyspiel.State, depth: int) -> int:
        node_id = len(nodes)
        if current.is_terminal():
            payoff = " / ".join(
                f"{plugin.player_name(player)} {value:+.1f}"
                for player, value in enumerate(current.returns())
            )
            nodes.append({"label": f"Terminal\n{payoff}", "depth": depth, "terminal": True, "children": []})
            return node_id
        player = current.current_player()
        nodes.append(
            {"label": plugin.player_name(player), "depth": depth, "terminal": False, "children": []}
        )
        probabilities = policy.action_probabilities(current)
        for action in current.legal_actions():
            child_id = build(current.child(action), depth + 1)
            label = display_action(current, player, action)
            edges.append((node_id, child_id, label, probabilities.get(action, 0.0)))
            nodes[node_id]["children"].append(child_id)
        return node_id

    root_id = build(state, 0)
    leaf = 0

    def layout(node_id: int) -> float:
        nonlocal leaf
        children = nodes[node_id]["children"]
        if children:
            y = sum(layout(child) for child in children) / len(children)
        else:
            y = leaf
            leaf += 1
        nodes[node_id]["y"] = y
        return y

    layout(root_id)
    return nodes, edges


def save_tree_plot(path: Path, game: pyspiel.Game, policy: pyspiel.Policy, plugin: GamePlugin) -> bool:
    initial = game.new_initial_state()
    if initial.is_chance_node():
        scenarios = [
            (initial.child(action), plugin.chance_outcome_label(initial, action), probability)
            for action, probability in initial.chance_outcomes()
        ]
    else:
        scenarios = [(initial, "Game tree", 1.0)]
    if len(scenarios) > 4:
        return False
    fig, axes = plt.subplots(1, len(scenarios), figsize=(9 * len(scenarios), 9), squeeze=False, sharey=True)
    for ax, (state, scenario, chance_probability) in zip(axes[0], scenarios):
        nodes, edges = _tree(state, policy, plugin)
        for parent, child, action, probability in edges:
            x0, y0 = nodes[parent]["depth"], nodes[parent]["y"]
            x1, y1 = nodes[child]["depth"], nodes[child]["y"]
            ax.plot([x0, x1], [y0, y1], color=action_color(action), linewidth=1.8)
            ax.text(
                (x0 + x1) / 2,
                (y0 + y1) / 2,
                f"{action}\n{probability:.1%}",
                fontsize=8,
                ha="center",
                va="center",
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 1},
            )
        for node in nodes:
            color = "#F1F1F1" if node["terminal"] else "#DCEAF7"
            ax.text(
                node["depth"], node["y"], node["label"], ha="center", va="center", fontsize=8,
                bbox={"boxstyle": "round,pad=0.35", "facecolor": color, "edgecolor": "#666666"}, zorder=3,
            )
        ax.set_title(f"Chance: {scenario} ({chance_probability:.1%})")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.invert_yaxis()
        ax.set_frame_on(False)
    fig.suptitle(f"{plugin.metadata.title}: legal-action tree", fontsize=15)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return True
