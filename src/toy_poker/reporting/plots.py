"""Generic plots built from normalized analysis data."""

from __future__ import annotations

import math
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pyspiel
from matplotlib.colors import Normalize, TwoSlopeNorm

from toy_poker.analysis.information_sets import display_action
from toy_poker.games.base import GamePlugin

ACTION_COLORS = {
    "Check": "#4C78A8",
    "All-in": "#F58518",
    "Geometric bet": "#B279A2",
    "Raise all-in": "#E45756",
    "Call": "#54A24B",
    "Fold": "#9D9DA1",
}


def action_color(action: str) -> str:
    return ACTION_COLORS.get(action, "#B279A2")


def save_rank_distribution_plot(path: Path, distribution: dict) -> None:
    ranks = distribution["ranks"]
    fig, ax = plt.subplots(figsize=(max(8, min(18, len(ranks) * 0.45)), 4.5))
    ax.plot(ranks, distribution["OOP"], marker="o", linewidth=2, label="OOP")
    ax.plot(ranks, distribution["IP"], marker="o", linewidth=2, label="IP")
    ax.set_xlabel("Private number")
    ax.set_ylabel("Deal probability")
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:.1%}")
    if len(ranks) <= 30:
        ax.set_xticks(ranks)
    ax.set_title("Private-number distributions")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def save_strategy_plot(
    path: Path, infos: list[dict], title: str, scope: str = "average strategy"
) -> None:
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
    ax.set_title(f"{title}: {scope}")
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _numeric_range_groups(infos: list[dict]) -> list[tuple[tuple, list[dict]]]:
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    for info in infos:
        try:
            int(info["card"])
        except (TypeError, ValueError):
            continue
        key = (info["player"], tuple(info["history"]))
        grouped[key].append(info)
    return sorted(
        grouped.items(),
        key=lambda item: (len(item[0][1]), item[0][1], item[0][0]),
    )


def _range_axes(group_count: int):
    columns = 2
    rows = max(1, math.ceil(group_count / columns))
    fig, axes = plt.subplots(
        rows,
        columns,
        figsize=(18, max(4.5, rows * 3.1)),
        squeeze=False,
    )
    return fig, axes.ravel()


def _set_private_number_ticks(ax, cards: list[str]) -> None:
    if len(cards) <= 30:
        positions = list(range(len(cards)))
    else:
        step = math.ceil(len(cards) / 20)
        positions = list(range(0, len(cards), step))
        if positions[-1] != len(cards) - 1:
            positions.append(len(cards) - 1)
    ax.set_xticks(positions, [cards[position] for position in positions])


def save_range_strategy_plot(
    path: Path, infos: list[dict], title: str, scope: str = "average strategy"
) -> None:
    """Plot numeric private-card strategies as one heatmap per public history."""
    groups = _numeric_range_groups(infos)
    fig, axes = _range_axes(len(groups))
    image_artist = None
    for ax, ((player, history), rows) in zip(axes, groups):
        rows = sorted(rows, key=lambda row: int(row["card"]))
        cards = [row["card"] for row in rows]
        action_names = []
        for row in rows:
            for action in row["actions"]:
                if action["action"] not in action_names:
                    action_names.append(action["action"])
        matrix = []
        for action_name in action_names:
            matrix.append(
                [
                    next(
                        (
                            action["probability"]
                            for action in row["actions"]
                            if action["action"] == action_name
                        ),
                        0.0,
                    )
                    for row in rows
                ]
            )
        image_artist = ax.imshow(matrix, vmin=0.0, vmax=1.0, cmap="Blues", aspect="auto")
        for y, values in enumerate(matrix):
            for x, value in enumerate(values):
                if value >= 0.005:
                    ax.text(
                        x,
                        y,
                        f"{value:.0%}",
                        ha="center",
                        va="center",
                        fontsize=7,
                        color="white" if value >= 0.55 else "#222222",
                    )
        public_history = " → ".join(history) or "ROOT"
        ax.set_title(f"{player}: {public_history}", fontsize=10)
        _set_private_number_ticks(ax, cards)
        ax.set_yticks(range(len(action_names)), action_names)
        ax.set_xlabel("Private number")
    for ax in axes[len(groups) :]:
        ax.set_visible(False)
    if image_artist is not None:
        colorbar_axis = fig.add_axes([0.92, 0.08, 0.012, 0.82])
        fig.colorbar(image_artist, cax=colorbar_axis, label="Probability")
    fig.suptitle(f"{title}: {scope} by private number", fontsize=15)
    fig.subplots_adjust(top=0.97, bottom=0.02, left=0.1, right=0.89, hspace=0.55)
    fig.savefig(path, dpi=120)
    plt.close(fig)


def save_range_ev_plot(
    path: Path, infos: list[dict], utility_unit: str
) -> None:
    """Plot action EVs by numeric private card and public history."""
    groups = _numeric_range_groups(infos)
    all_evs = [action["ev"] for info in infos for action in info["actions"]]
    minimum, maximum = min(all_evs), max(all_evs)
    norm = (
        TwoSlopeNorm(vmin=minimum, vcenter=0.0, vmax=maximum)
        if minimum < 0.0 < maximum
        else Normalize(vmin=minimum, vmax=maximum)
    )
    fig, axes = _range_axes(len(groups))
    image_artist = None
    for ax, ((player, history), rows) in zip(axes, groups):
        rows = sorted(rows, key=lambda row: int(row["card"]))
        cards = [row["card"] for row in rows]
        action_names = []
        for row in rows:
            for action in row["actions"]:
                if action["action"] not in action_names:
                    action_names.append(action["action"])
        matrix = []
        for action_name in action_names:
            matrix.append(
                [
                    next(
                        (
                            action["ev"]
                            for action in row["actions"]
                            if action["action"] == action_name
                        ),
                        math.nan,
                    )
                    for row in rows
                ]
            )
        image_artist = ax.imshow(matrix, norm=norm, cmap="coolwarm", aspect="auto")
        public_history = " → ".join(history) or "ROOT"
        ax.set_title(f"{player}: {public_history}", fontsize=10)
        _set_private_number_ticks(ax, cards)
        ax.set_yticks(range(len(action_names)), action_names)
        ax.set_xlabel("Private number")
    for ax in axes[len(groups) :]:
        ax.set_visible(False)
    if image_artist is not None:
        colorbar_axis = fig.add_axes([0.92, 0.08, 0.012, 0.82])
        fig.colorbar(image_artist, cax=colorbar_axis, label=utility_unit)
    fig.suptitle("Action EV by private number and public history", fontsize=15)
    fig.subplots_adjust(top=0.97, bottom=0.02, left=0.1, right=0.89, hspace=0.55)
    fig.savefig(path, dpi=120)
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


def save_convergence_plot(
    path: Path,
    convergence: list[dict],
    plugin: GamePlugin,
    analytic_returns: list[float] | None,
    target_exploitability: float | None = None,
    stopped_iteration: int | None = None,
) -> None:
    iterations = [row["iteration"] for row in convergence]
    gaps = [row["exploitability"] for row in convergence]
    analytic = analytic_returns
    rows = 2 if analytic is not None else 1
    fig, axes = plt.subplots(rows, 1, figsize=(10, 7.5 if rows == 2 else 4.5), sharex=True, squeeze=False)
    ax_gap = axes[0][0]
    constrained = all("unconstrained_exploitability" in row for row in convergence)
    ax_gap.semilogy(
        iterations,
        gaps,
        color="#E45756",
        linewidth=2,
        label="Constrained Nash gap" if constrained else None,
    )
    if constrained:
        ax_gap.semilogy(
            iterations,
            [row["unconstrained_exploitability"] for row in convergence],
            color="#4C78A8",
            linestyle=":",
            linewidth=1.5,
            label="Unconstrained exploitability",
        )
    if target_exploitability is not None:
        ax_gap.axhline(
            target_exploitability,
            color="#54A24B",
            linestyle="--",
            linewidth=1.5,
            label=f"Target ({target_exploitability:.0e})",
        )
    if stopped_iteration is not None:
        ax_gap.axvline(
            stopped_iteration,
            color="#777777",
            linestyle=":",
            linewidth=1.2,
            label=f"Stopped ({stopped_iteration:,})",
        )
    if constrained or target_exploitability is not None or stopped_iteration is not None:
        ax_gap.legend()
    ax_gap.set_ylabel("Nash gap" if constrained else "Exploitability")
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


def _tree(
    state: pyspiel.State,
    policy: pyspiel.Policy,
    plugin: GamePlugin,
    initial_reach: float = 1.0,
    min_reach: float = 0.0,
):
    nodes: list[dict] = []
    edges: list[tuple[int, int, str, float]] = []

    def build(current: pyspiel.State, depth: int, reach: float) -> int:
        node_id = len(nodes)
        if current.is_terminal():
            payoff = " / ".join(
                f"{plugin.player_name(player)} {value:+.1f}"
                for player, value in enumerate(current.returns())
            )
            nodes.append(
                {
                    "label": payoff,
                    "depth": depth,
                    "reach": reach,
                    "terminal": True,
                    "children": [],
                }
            )
            return node_id
        player = current.current_player()
        nodes.append(
            {
                "label": plugin.player_name(player),
                "depth": depth,
                "reach": reach,
                "terminal": False,
                "children": [],
            }
        )
        probabilities = policy.action_probabilities(current)
        for action in current.legal_actions():
            probability = probabilities.get(action, 0.0)
            child_reach = reach * probability
            if min_reach > 0.0 and child_reach < min_reach:
                continue
            child_id = build(current.child(action), depth + 1, child_reach)
            label = display_action(current, player, action)
            edges.append((node_id, child_id, label, probability))
            nodes[node_id]["children"].append(child_id)
        return node_id

    root_id = build(state, 0, initial_reach)
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


def _merged_public_tree(
    game: pyspiel.Game,
    policy: pyspiel.Policy,
    plugin: GamePlugin,
    min_reach: float = 0.0,
):
    """Merge private chance outcomes into one reach-weighted public action tree."""
    records: dict[tuple[str, ...], dict] = {}

    def record(prefix: tuple[str, ...], terminal: bool, player: int | None) -> dict:
        return records.setdefault(
            prefix,
            {
                "reach": 0.0,
                "terminal": terminal,
                "player": player,
                "returns": [0.0] * game.num_players(),
                "children": {},
            },
        )

    def aggregate(state: pyspiel.State, reach: float, prefix: tuple[str, ...]) -> None:
        if state.is_chance_node():
            for action, probability in state.chance_outcomes():
                aggregate(state.child(action), reach * probability, prefix)
            return
        if state.is_terminal():
            node = record(prefix, True, None)
            node["reach"] += reach
            for player, value in enumerate(state.returns()):
                node["returns"][player] += reach * value
            return
        player = state.current_player()
        node = record(prefix, False, player)
        node["reach"] += reach
        probabilities = policy.action_probabilities(state)
        for action in state.legal_actions():
            action_name = display_action(state, player, action)
            child_prefix = prefix + (action_name,)
            node["children"][action_name] = child_prefix
            aggregate(
                state.child(action),
                reach * probabilities.get(action, 0.0),
                child_prefix,
            )

    aggregate(game.new_initial_state(), 1.0, ())
    nodes: list[dict] = []
    edges: list[tuple[int, int, str, float]] = []

    def build(prefix: tuple[str, ...], depth: int) -> int:
        source = records[prefix]
        node_id = len(nodes)
        if source["terminal"]:
            if source["reach"] > 0.0:
                payoff = " / ".join(
                    f"{plugin.player_name(player)} {weighted / source['reach']:+.2f}"
                    for player, weighted in enumerate(source["returns"])
                )
                label = f"Avg.\n{payoff}"
            else:
                label = "off path"
        else:
            label = plugin.player_name(source["player"])
        nodes.append(
            {
                "label": label,
                "depth": depth,
                "reach": source["reach"],
                "terminal": source["terminal"],
                "children": [],
            }
        )
        for action_name, child_prefix in source["children"].items():
            child = records[child_prefix]
            if min_reach > 0.0 and child["reach"] < min_reach:
                continue
            child_id = build(child_prefix, depth + 1)
            probability = (
                child["reach"] / source["reach"]
                if source["reach"] > 0.0
                else 0.0
            )
            edges.append((node_id, child_id, action_name, probability))
            nodes[node_id]["children"].append(child_id)
        return node_id

    root_id = build((), 0)
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


def _stored_public_tree(
    rows: list[dict], plugin: GamePlugin, min_reach: float = 0.0
):
    """Prepare a pre-aggregated public tree without revisiting private deals."""
    records = {tuple(row["history"]): row for row in rows}
    nodes: list[dict] = []
    edges: list[tuple[int, int, str, float]] = []

    def build(history: tuple[str, ...], depth: int) -> int:
        source = records[history]
        node_id = len(nodes)
        if source["terminal"]:
            payoff = " / ".join(
                f"{plugin.player_name(player)} {value:+.2f}"
                for player, value in enumerate(source.get("returns", []))
            )
            label = f"Avg.\n{payoff}"
        else:
            label = plugin.player_name(source["player_index"])
        nodes.append(
            {
                "label": label,
                "depth": depth,
                "reach": source["reach_probability"],
                "terminal": source["terminal"],
                "children": [],
            }
        )
        for child in source["children"]:
            child_history = tuple(child["history"])
            child_source = records[child_history]
            if min_reach > 0.0 and child_source["reach_probability"] < min_reach:
                continue
            child_id = build(child_history, depth + 1)
            edges.append(
                (node_id, child_id, child["action"], child["probability"])
            )
            nodes[node_id]["children"].append(child_id)
        return node_id

    root_id = build((), 0)
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


def save_tree_plot(
    path: Path,
    game: pyspiel.Game,
    policy: pyspiel.Policy,
    plugin: GamePlugin,
    min_reach: float = 0.0,
    public_tree: list[dict] | None = None,
) -> bool:
    if public_tree is not None:
        nodes, edges = _stored_public_tree(public_tree, plugin, min_reach)
        scenarios = [(game.new_initial_state(), "All private deals", 1.0)]
        trees = [("All private deals", 1.0, nodes, edges)]
    else:
        initial = game.new_initial_state()
        if initial.is_chance_node():
            scenarios = [
                (initial.child(action), plugin.chance_outcome_label(initial, action), probability)
                for action, probability in initial.chance_outcomes()
            ]
        else:
            scenarios = [(initial, "Game tree", 1.0)]
        if min_reach > 0.0:
            scenarios = [
                scenario for scenario in scenarios if scenario[2] >= min_reach
            ]
        if not scenarios:
            return False
        if len(scenarios) > 4:
            nodes, edges = _merged_public_tree(game, policy, plugin, min_reach=min_reach)
            scenarios = [(initial, "All private deals", 1.0)]
            trees = [("All private deals", 1.0, nodes, edges)]
        else:
            trees = [
                (
                    scenario,
                    chance_probability,
                    *_tree(
                        state,
                        policy,
                        plugin,
                        initial_reach=chance_probability,
                        min_reach=min_reach,
                    ),
                )
                for state, scenario, chance_probability in scenarios
            ]
    max_leaves = max(
        sum(not node["children"] for node in nodes)
        for _, _, nodes, _ in trees
    )
    height = max(7.0, min(24.0, max_leaves * 0.45))
    fig, axes = plt.subplots(
        1,
        len(scenarios),
        figsize=(9 * len(scenarios), height),
        squeeze=False,
        sharey=True,
    )
    for ax, (scenario, chance_probability, nodes, edges) in zip(axes[0], trees):
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
            label = node["label"]
            if min_reach > 0.0:
                label += f"\nReach {node['reach']:.3%}"
            ax.text(
                node["depth"], node["y"], label, ha="center", va="center", fontsize=8,
                bbox={"boxstyle": "round,pad=0.35", "facecolor": color, "edgecolor": "#666666"}, zorder=3,
            )
        ax.set_title(f"Chance: {scenario} ({chance_probability:.1%})")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.invert_yaxis()
        ax.set_frame_on(False)
    scope = (
        f"major action tree (reach >= {min_reach:.4%})"
        if min_reach > 0.0
        else "full legal-action tree"
    )
    fig.suptitle(f"{plugin.metadata.title}: {scope}", fontsize=15)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return True
