"""Tests for the self-contained numeric-range strategy viewer."""

import base64
from pathlib import Path

import numpy as np
import pytest

from toy_poker.games import get_game
from toy_poker.reporting.strategy_viewer import (
    action_color,
    action_order_key,
    build_strategy_viewer_payload,
    current_node_ev,
    save_strategy_viewer,
    showdown_equities,
)


def _info(rank: int) -> dict:
    all_in = {1: 0.2, 2: 0.5, 3: 0.8}[rank]
    check = {1: 0.6, 2: 0.3, 3: 0.0}[rank]
    return {
        "card": str(rank),
        "history": [],
        "player": "OOP",
        "reach_probability": 1.0 / 3.0,
        "context": {
            "pot": 1.0,
            "ip_committed": 0.0,
            "oop_committed": 0.0,
            "amount_to_call": 0.0,
        },
        "actions": [
            {"action_id": 0, "action": "Check", "probability": check, "ev": 0.1},
            {"action_id": 3, "action": "All-in", "probability": all_in, "ev": 0.2},
            {"action_id": 7, "action": "Bet 50%", "probability": 0.2, "ev": 0.3},
        ],
    }


def _analysis() -> dict:
    children = [
        {"action": "Check", "history": ["Check"], "probability": 0.3},
        {"action": "All-in", "history": ["All-in"], "probability": 0.5},
        {"action": "Bet 50%", "history": ["Bet 50%"], "probability": 0.2},
    ]
    return {
        "game": {
            "title": "Integer test",
            "player_names": ["IP", "OOP"],
            "parameters": {"ip_stack": 4.0, "oop_stack": 4.0},
            "rank_distribution": {
                "ranks": [1, 2, 3],
                "OOP": [1.0 / 3.0] * 3,
                "IP": [1.0 / 3.0] * 3,
            },
        },
        "reporting": {"major_reach_threshold": 1e-4},
        "information_sets": [_info(rank) for rank in range(1, 4)],
        "public_tree": [
            {
                "history": [],
                "reach_probability": 1.0,
                "terminal": False,
                "player_index": 1,
                "children": children,
            },
            {
                "history": ["Check"],
                "reach_probability": 0.3,
                "terminal": True,
                "player_index": None,
                "children": [],
                "returns": [0.4, 0.6],
            },
            {
                "history": ["All-in"],
                "reach_probability": 0.5,
                "terminal": True,
                "player_index": None,
                "children": [],
                "returns": [0.7, 0.3],
            },
            {
                "history": ["Bet 50%"],
                "reach_probability": 0.2,
                "terminal": True,
                "player_index": None,
                "children": [],
                "returns": [0.5, 0.5],
            },
        ],
    }


def test_action_palette_and_display_order():
    labels = ["Fold", "Check", "Bet 20%", "Call", "All-in", "Raise 100%"]
    assert sorted(labels, key=action_order_key) == [
        "All-in",
        "Raise 100%",
        "Bet 20%",
        "Call",
        "Check",
        "Fold",
    ]
    assert action_color("Check") == "#9acd32"
    assert action_color("All-in") == "#1565c0"
    assert action_color("Bet 20%").startswith("hsl(0")
    assert action_color("Raise 100%") == "#b71c1c"


def test_payload_flattens_rank_strategies_in_display_order():
    plugin = get_game("integer_range_betting")
    payload = build_strategy_viewer_payload(_analysis(), plugin, grid_columns=10)

    root = payload["nodes"][0]
    assert payload["schema_version"] == 6
    assert payload["ranks"] == [1, 2, 3]
    assert payload["grid_columns"] == 10
    assert [action["label"] for action in root["actions"]] == [
        "All-in",
        "Bet 50%",
        "Check",
    ]
    raw = base64.b64decode(payload["probabilities_f32"])
    probabilities = np.frombuffer(raw, dtype="<f4")
    assert probabilities[:3] == pytest.approx([0.2, 0.2, 0.6])
    assert probabilities.size == 9
    assert [
        action["aggregate_probability"] for action in root["actions"]
    ] == pytest.approx([0.5, 0.2, 0.3])
    assert [action["aggregate_ev"] for action in root["actions"]] == pytest.approx(
        [0.2, 0.3, 0.1]
    )
    assert root["context"]["ip_remaining_stack"] == pytest.approx(4.0)
    assert root["context"]["oop_remaining_stack"] == pytest.approx(4.0)
    assert root["profile_returns"] == pytest.approx([0.57, 0.43])
    assert root["range_evs"] == pytest.approx([0.57, 0.43])
    assert sum(root["range_evs"]) == pytest.approx(root["context"]["pot"])


def test_payload_propagates_both_conditional_ranges_by_bayes_rule():
    payload = build_strategy_viewer_payload(
        _analysis(), get_game("integer_range_betting"), grid_columns=10
    )
    ranges = np.frombuffer(
        base64.b64decode(payload["conditional_ranges_f32"]), dtype="<f4"
    )
    root = payload["nodes"][0]
    all_in_child = payload["nodes"][2]

    assert ranges[root["ranges_offset"] : root["ranges_offset"] + 6] == pytest.approx(
        [1.0 / 3.0] * 6
    )
    child_ranges = ranges[
        all_in_child["ranges_offset"] : all_in_child["ranges_offset"] + 6
    ].reshape(2, 3)
    assert child_ranges[0] == pytest.approx([1.0 / 3.0] * 3)
    assert child_ranges[1] == pytest.approx([2.0 / 15.0, 1.0 / 3.0, 8.0 / 15.0])
    assert "range_belief" not in all_in_child


def test_action_evs_are_rebased_to_the_current_node():
    analysis = _analysis()
    for info in analysis["information_sets"]:
        info["context"]["pot"] = 1.4
        info["context"]["oop_committed"] = 0.4

    payload = build_strategy_viewer_payload(
        analysis, get_game("integer_range_betting"), grid_columns=10
    )
    action_evs = np.frombuffer(
        base64.b64decode(payload["action_evs_f32"]), dtype="<f4"
    )
    root = payload["nodes"][0]

    assert current_node_ev(-0.4, 0.4) == pytest.approx(0.0)
    assert action_evs[:3] == pytest.approx([0.6, 0.7, 0.5])
    assert [action["aggregate_ev"] for action in root["actions"]] == pytest.approx(
        [0.6, 0.7, 0.5]
    )


def test_payload_propagates_root_relative_rank_retention():
    payload = build_strategy_viewer_payload(
        _analysis(), get_game("integer_range_betting"), grid_columns=10
    )
    ranges = np.frombuffer(
        base64.b64decode(payload["conditional_ranges_f32"]), dtype="<f4"
    )
    masses = np.frombuffer(
        base64.b64decode(payload["range_masses_f32"]), dtype="<f4"
    )
    root = payload["nodes"][0]
    all_in_child = payload["nodes"][2]

    assert masses[root["range_masses_offset"] : root["range_masses_offset"] + 2] == (
        pytest.approx([1.0, 1.0])
    )
    assert masses[
        all_in_child["range_masses_offset"] : all_in_child["range_masses_offset"]
        + 2
    ] == pytest.approx([1.0, 0.5])
    root_ranges = ranges[
        root["ranges_offset"] : root["ranges_offset"] + 6
    ].reshape(2, 3)
    child_ranges = ranges[
        all_in_child["ranges_offset"] : all_in_child["ranges_offset"] + 6
    ].reshape(2, 3)
    child_masses = masses[
        all_in_child["range_masses_offset"] : all_in_child["range_masses_offset"]
        + 2
    ]
    child_retentions = child_ranges * child_masses[:, None] / root_ranges
    assert child_retentions[0] == pytest.approx([1.0, 1.0, 1.0])
    assert child_retentions[1] == pytest.approx([0.2, 0.5, 0.8])


def test_showdown_equity_uses_opponent_conditional_range():
    opponent = np.array([0.2, 0.3, 0.5])
    assert showdown_equities(opponent) == pytest.approx([0.1, 0.35, 0.75])

    oop = np.array([0.1, 0.2, 0.7])
    ip = np.array([0.6, 0.3, 0.1])
    oop_equity = float(np.dot(oop, showdown_equities(ip)))
    ip_equity = float(np.dot(ip, showdown_equities(oop)))
    assert oop_equity + ip_equity == pytest.approx(1.0)


def test_viewer_is_a_self_contained_html_file(tmp_path: Path):
    path = tmp_path / "strategy_viewer.html"
    created = save_strategy_viewer(
        path, _analysis(), get_game("integer_range_betting"), grid_columns=10
    )

    document = path.read_text(encoding="utf-8")
    assert created is True
    assert "Interactive strategy viewer" in document
    assert 'id="viewer-data"' in document
    assert "DATA.schema_version!==6" in document
    assert "Invalid viewer array length" in document
    assert "strategy-grid" in document
    assert ">Node strategy<" not in document
    assert "Conditional ranges" in document
    assert "Equity distribution" in document
    assert "Equity distribution by range percentile" in document
    assert "renderEquityDistribution" in document
    assert "Manhattan strategy" in document
    assert "Show zero-weight ranks" in document
    assert "renderManhattan" in document
    assert "manhattanRows" in document
    assert "Hands sorted by equity (equal-width ranks)" in document
    assert "range weight ${pct(row.weight)}" in document
    assert "box.clientWidth||720" in document
    assert "bar幅は条件付きrange weightを表しません" not in document
    assert "range_masses_f32" in document
    assert "playerRetention" in document
    assert "Range retained:" in document
    assert "segs.style.height=pct" in document
    assert "weight.textContent=pct(retentions[ri])" in document
    assert "weight.textContent=`R " not in document
    assert "Range metrics" in document
    assert "ev/(pot*equity)" in document
    assert "EVはcurrent node基準" not in document
    assert "historyStepLabel" in document
    assert "[${parent.player}] ${action}" in document
    assert "steps.push(`[${node.player}] ?`)" in document
    assert "current-turn" in document
    assert 'id="title"' not in document
    assert 'href="report.html"' not in document
    assert "Showdown equity by rank" not in document
    assert 'class="panel history-nav"' in document
    assert 'id="history-info"' in document
    assert "renderHistoryInfo" in document
    assert "infoBadge(`Node ${node.id}`)" not in document
    assert "Reach ${pct(node.reach_probability)}" in document
    assert "Belief ${node.range_belief" not in document
    assert "Low reach / off path" not in document
    assert "Zero-probability ancestor: reference ranges shown" not in document
    assert 'id="low-reach-alert"' in document
    assert "renderLowReachAlert" in document
    assert "このnodeへの到達確率は${pct(node.reach_probability)}と低いため" in document
    assert document.index('id="low-reach-alert"') < document.index(
        'class="panel history-nav"'
    )
    assert "pot-state" in document
    assert "label.textContent='Pot'" in document
    assert "pot-main" in document
    assert "On table" in document
    assert "to act" not in document
    assert "facingBetData" in document
    assert "Bet size ${facing?" in document
    assert "metric('History'" not in document
    assert "Freq ${pct(a.aggregate_probability)} · EV" in document
    assert document.index('id="breadcrumbs"') < document.index('id="history-jump"')
    assert document.index('id="history-jump"') < document.index('id="history-info"')
    assert document.index('id="action-panel"') < document.index(
        '<div class="layout">'
    )
    assert document.index('id="strategy-grid"') < document.index(
        'id="node-panel"'
    )
    assert document.index('id="node-panel"') < document.index('id="details"')
    assert document.index('<div class="layout">') < document.index(
        'id="range-metrics-panel"'
    )
    assert document.index('id="range-metrics-panel"') < document.index(
        '<section id="manhattan-panel"'
    )
    assert "align-items:stretch;margin-bottom:12px" in document
    assert "grid-template-rows:auto minmax(0,1fr)" in document
    assert "equity.className='rank-equity'" in document
    assert "equity.textContent=`EQ ${pct(" in document
    assert "`${node.player} rank ${RANKS[selectedRank]}`" not in document
    assert "`Rank ${RANKS[selectedRank]}`" in document
    details_function = document[document.index("function renderDetails"):document.index("function navigate")]
    assert "Range retained" not in details_function
    assert "Conditional range weight" not in details_function
    assert document.index('<section id="manhattan-panel"') < document.index(
        '<div class="charts">'
    )
    assert "https://" not in document
