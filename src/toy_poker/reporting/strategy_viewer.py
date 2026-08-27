"""Self-contained interactive strategy viewer for numeric private ranges."""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path

import numpy as np

from toy_poker.games.base import GamePlugin

_SIZE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)%")


def action_size(action: str) -> float | None:
    """Extract a displayed pot percentage from a bet or raise label."""
    match = _SIZE_PATTERN.search(action)
    return float(match.group(1)) if match else None


def action_order_key(action: str) -> tuple[int, float, str]:
    """Place aggression left-to-right, followed by passive actions."""
    normalized = action.lower()
    if "all-in" in normalized:
        return (0, 0.0, action)
    size = action_size(action)
    if size is not None and ("bet" in normalized or "raise" in normalized):
        return (1, -size, action)
    if normalized == "call":
        return (2, 0.0, action)
    if normalized == "check":
        return (3, 0.0, action)
    if normalized == "fold":
        return (4, 0.0, action)
    return (5, 0.0, action)


def action_color(action: str) -> str:
    """Return the default GTO-style color for an action label."""
    normalized = action.lower()
    if "all-in" in normalized:
        return "#1565c0"
    size = action_size(action)
    if size is not None and ("bet" in normalized or "raise" in normalized):
        if size >= 100.0:
            return "#7f0000" if size > 100.0 else "#b71c1c"
        ratio = max(0.0, min(1.0, size / 100.0))
        lightness = 88.0 - 48.0 * ratio
        return f"hsl(0 76% {lightness:.1f}%)"
    if normalized == "check":
        return "#9acd32"
    if normalized == "call":
        return "#2e8b57"
    if normalized == "fold":
        return "#9e9e9e"
    return "#8e7cc3"


def _float32_base64(values: list[float]) -> str:
    data = np.asarray(values, dtype="<f4").tobytes()
    return base64.b64encode(data).decode("ascii")


def current_node_ev(root_utility_ev: float, committed: float) -> float:
    """Root基準の利得EVを、既投入チップを埋没費用とする現在node基準へ直す。"""
    return float(root_utility_ev) + float(committed)


def showdown_equities(opponent_range: np.ndarray | list[float]) -> np.ndarray:
    """Return rank-by-rank showdown equity against a numeric opponent range."""
    weights = np.asarray(opponent_range, dtype=np.float64)
    if weights.ndim != 1 or weights.size == 0:
        raise ValueError("opponent_range must be a non-empty one-dimensional array")
    if np.any(weights < 0.0) or not np.all(np.isfinite(weights)):
        raise ValueError("opponent_range must contain finite non-negative values")
    total = float(weights.sum())
    if total <= 0.0:
        raise ValueError("opponent_range must have positive mass")
    normalized = weights / total
    lower = np.concatenate(([0.0], np.cumsum(normalized)[:-1]))
    return lower + 0.5 * normalized


def build_strategy_viewer_payload(
    analysis: dict,
    plugin: GamePlugin,
    grid_columns: int = 10,
) -> dict | None:
    """Build compact public-node metadata and flat Float32 strategy arrays."""
    if not getattr(plugin, "numeric_range_strategy", False):
        return None
    public_tree = analysis.get("public_tree")
    distribution = analysis.get("game", {}).get("rank_distribution")
    if not public_tree or not distribution:
        return None
    ranks = list(distribution["ranks"])
    rank_keys = [str(rank) for rank in ranks]
    game_parameters = analysis["game"].get("parameters", {})
    history_to_infos: dict[tuple[str, ...], dict[str, dict]] = {}
    for info in analysis["information_sets"]:
        history_to_infos.setdefault(tuple(info["history"]), {})[
            str(info["card"])
        ] = info

    history_to_id = {
        tuple(row["history"]): node_id
        for node_id, row in enumerate(public_tree)
    }
    parent_ids: dict[int, int] = {}
    for parent_id, row in enumerate(public_tree):
        for child in row["children"]:
            parent_ids[history_to_id[tuple(child["history"])]] = parent_id

    probabilities: list[float] = []
    action_evs: list[float] = []
    nodes = []
    for node_id, public in enumerate(public_tree):
        history = tuple(public["history"])
        node = {
            "id": node_id,
            "parent_id": parent_ids.get(node_id),
            "history": list(history),
            "reach_probability": float(public["reach_probability"]),
            "terminal": bool(public["terminal"]),
        }
        if public["terminal"]:
            node["returns"] = list(public.get("returns", []))
            node["actions"] = []
            nodes.append(node)
            continue

        infos = history_to_infos.get(history, {})
        missing = [rank for rank in rank_keys if rank not in infos]
        if missing:
            raise ValueError(
                f"Interactive viewer is missing ranks at history {history}: {missing[:5]}"
            )
        representative = infos[rank_keys[0]]
        context = dict(representative.get("context", {}))
        for position in ("ip", "oop"):
            remaining_key = f"{position}_remaining_stack"
            stack = game_parameters.get(f"{position}_stack")
            committed = context.get(f"{position}_committed")
            if remaining_key not in context and stack is not None and committed is not None:
                context[remaining_key] = max(0.0, float(stack) - float(committed))
        public_children = {
            child["action"]: child for child in public["children"]
        }
        source_actions = sorted(
            representative["actions"], key=lambda action: action_order_key(action["action"])
        )
        acting_committed = float(
            context.get(f"{representative['player'].lower()}_committed", 0.0)
        )
        actions = []
        for source in source_actions:
            label = source["action"]
            child = public_children[label]
            actions.append(
                {
                    "action_id": int(source["action_id"]),
                    "label": label,
                    "color": action_color(label),
                    "aggregate_probability": float(child["probability"]),
                    "child_id": history_to_id[tuple(child["history"])],
                }
            )
        strategy_offset = len(probabilities)
        ev_offset = len(action_evs)
        for rank in rank_keys:
            info = infos[rank]
            by_action_id = {
                int(action["action_id"]): action for action in info["actions"]
            }
            for action in actions:
                source = by_action_id[action["action_id"]]
                probabilities.append(float(source["probability"]))
                action_evs.append(current_node_ev(source["ev"], acting_committed))
        node.update(
            {
                "player_index": int(public["player_index"]),
                "player": representative["player"],
                "context": context,
                "actions": actions,
                "strategy_offset": strategy_offset,
                "ev_offset": ev_offset,
                "action_count": len(actions),
            }
        )
        nodes.append(node)

    player_names = list(analysis["game"]["player_names"])
    priors = []
    for player_name in player_names:
        prior = np.asarray(distribution[player_name], dtype=np.float64)
        priors.append(prior / prior.sum())
    node_ranges: list[list[np.ndarray] | None] = [None] * len(nodes)
    node_range_masses: list[np.ndarray | None] = [None] * len(nodes)
    root_id = history_to_id[()]
    node_ranges[root_id] = [prior.copy() for prior in priors]
    node_range_masses[root_id] = np.ones(len(priors), dtype=np.float64)
    conditional_ranges: list[float] = []
    range_masses: list[float] = []

    for node in nodes:
        ranges = node_ranges[node["id"]]
        masses = node_range_masses[node["id"]]
        if ranges is None:
            raise ValueError(f"Interactive viewer range propagation missed node {node['id']}")
        if masses is None:
            raise ValueError(
                f"Interactive viewer range-mass propagation missed node {node['id']}"
            )
        node["ranges_offset"] = len(conditional_ranges)
        node["range_masses_offset"] = len(range_masses)
        for player_range in ranges:
            conditional_ranges.extend(float(value) for value in player_range)
        range_masses.extend(float(value) for value in masses)
        if node["terminal"]:
            continue
        acting_player = node["player_index"]
        action_count = node["action_count"]
        for action_index, action in enumerate(node["actions"]):
            likelihood = np.asarray(
                [
                    probabilities[
                        node["strategy_offset"] + rank_index * action_count + action_index
                    ]
                    for rank_index in range(len(ranks))
                ],
                dtype=np.float64,
            )
            weighted = ranges[acting_player] * likelihood
            action_mass = float(weighted.sum())
            action["aggregate_probability"] = action_mass
            rank_action_evs = np.asarray(
                [
                    action_evs[
                        node["ev_offset"]
                        + rank_index * action_count
                        + action_index
                    ]
                    for rank_index in range(len(ranks))
                ],
                dtype=np.float64,
            )
            action["aggregate_ev"] = (
                float(np.dot(weighted, rank_action_evs) / action_mass)
                if action_mass > 1e-15
                else None
            )
            child_ranges = [player_range.copy() for player_range in ranges]
            if action_mass > 1e-15:
                child_ranges[acting_player] = weighted / action_mass
            child_masses = masses.copy()
            child_masses[acting_player] *= action_mass
            child_id = action["child_id"]
            node_ranges[child_id] = child_ranges
            node_range_masses[child_id] = child_masses

    profile_returns: list[np.ndarray | None] = [None] * len(nodes)

    def expected_profile_returns(node_id: int) -> np.ndarray:
        cached = profile_returns[node_id]
        if cached is not None:
            return cached
        node = nodes[node_id]
        if node["terminal"]:
            result = np.asarray(node["returns"], dtype=np.float64)
        else:
            result = np.zeros(len(player_names), dtype=np.float64)
            for action in node["actions"]:
                result += float(action["aggregate_probability"]) * (
                    expected_profile_returns(action["child_id"])
                )
        profile_returns[node_id] = result
        return result

    for node in nodes:
        returns = expected_profile_returns(node["id"])
        node["profile_returns"] = [float(value) for value in returns]
        if node["terminal"]:
            continue
        context = node["context"]
        node["range_evs"] = [
            float(returns[player_index])
            + float(context.get(f"{player_name.lower()}_committed", 0.0))
            for player_index, player_name in enumerate(player_names)
        ]

    return {
        "schema_version": 6,
        "ranks": ranks,
        "grid_columns": grid_columns,
        "root_id": root_id,
        "major_reach_threshold": float(
            analysis.get("reporting", {}).get("major_reach_threshold", 1e-4)
        ),
        "player_names": player_names,
        "nodes": nodes,
        "probabilities_f32": _float32_base64(probabilities),
        "action_evs_f32": _float32_base64(action_evs),
        "conditional_ranges_f32": _float32_base64(conditional_ranges),
        "range_masses_f32": _float32_base64(range_masses),
        "array_counts": {
            "probabilities": len(probabilities),
            "action_evs": len(action_evs),
            "conditional_ranges": len(conditional_ranges),
            "range_masses": len(range_masses),
        },
    }


def save_strategy_viewer(
    path: Path,
    analysis: dict,
    plugin: GamePlugin,
    grid_columns: int = 10,
) -> bool:
    """Write a dependency-free interactive viewer and return whether it exists."""
    payload = build_strategy_viewer_payload(analysis, plugin, grid_columns)
    if payload is None:
        return False
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    serialized = serialized.replace("</", "<\\/")
    path.write_text(_viewer_document(serialized), encoding="utf-8")
    return True


def _viewer_document(serialized_payload: str) -> str:
    return f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Interactive strategy viewer</title>
<style>
:root {{--bg:#f5f7fa;--panel:#fff;--ink:#17212b;--muted:#667085;--line:#d9dee7;--accent:#315efb;}}
* {{box-sizing:border-box}} body {{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,system-ui,sans-serif}}
button,select {{font:inherit}} .app {{max-width:1500px;margin:auto;padding:18px}}
.panel {{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px;margin-bottom:12px;box-shadow:0 1px 2px #1018280d}}
.history-nav {{display:grid;gap:10px}}
.crumbs {{display:flex;flex-wrap:wrap;gap:6px;align-items:center}}
.crumb {{border:0;background:#eef2ff;color:#273b8f;border-radius:7px;padding:7px 9px;cursor:pointer}}
.current-turn {{background:#e7f8ef;color:#17633a;font-weight:750}}
.separator {{color:#98a2b3}} .jump {{width:100%;padding:8px;border:1px solid var(--line);border-radius:8px}}
.history-info {{display:flex;gap:7px;flex-wrap:wrap}}
.badge {{font-size:12px;border-radius:999px;padding:4px 8px;background:#eef2f6}}
.low-reach-alert {{border:1px solid #e6b800;border-left:5px solid #d69e00;border-radius:10px;background:#fff7d6;color:#694b00;padding:11px 13px;margin-bottom:12px;font-size:14px;font-weight:650}}
.low-reach-alert[hidden] {{display:none}}
.pot-state {{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px;align-items:stretch}}
.seat-card,.pot-center {{border:1px solid var(--line);border-radius:9px;padding:7px;background:#f8fafc}}
.seat-card h3 {{margin:0 0 4px;font-size:15px}} .seat-card.active {{border-color:#315efb;box-shadow:inset 0 0 0 1px #315efb}}
.seat-values {{display:grid;grid-template-columns:1fr;gap:3px}}
.seat-value {{display:flex;align-items:baseline;justify-content:space-between;gap:5px;background:#fff;border-radius:6px;padding:3px 5px;color:var(--muted);font-size:10px;white-space:nowrap}}
.seat-value b {{color:var(--ink);font-size:13px;margin:0}}
.pot-center {{grid-column:1/-1;display:grid;place-items:center;text-align:center;background:#fffaf0;border-color:#ead8a8}}
.pot-main {{display:flex;align-items:baseline;justify-content:center;gap:7px}}
.pot-center small {{color:var(--muted)}} .pot-amount {{font-size:24px;font-weight:800;line-height:1.1;margin:0}}
.bet-state {{display:flex;justify-content:center;gap:7px;flex-wrap:wrap}}
.bet-state span {{background:#fff;border:1px solid #ead8a8;border-radius:999px;padding:2px 5px;font-size:10px}}
.range-metrics-head {{margin-bottom:10px}} .range-metrics-head h3 {{margin:0}}
.range-metrics-grid {{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}}
.range-player-card {{border:1px solid var(--line);border-radius:9px;padding:10px;background:#fbfcfe}}
.range-player-card h4 {{margin:0 0 8px;font-size:15px}}
.range-player-values {{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}}
.range-player-value {{background:#f1f4f8;border-radius:7px;padding:7px;font-size:11px;color:var(--muted)}}
.range-player-value b {{display:block;color:var(--ink);font-size:17px;margin-top:2px}}
.actions {{display:flex;flex-wrap:wrap;gap:8px}}
.action-button {{border:1px solid var(--line);border-left:8px solid var(--action-color);background:white;border-radius:8px;padding:8px 11px;cursor:pointer;text-align:left}}
.action-button:hover {{background:#f4f6ff;border-color:#b5c2ff}} .action-button span {{display:block;color:var(--muted);font-size:12px}}
.node-strategy {{display:flex;width:100%;height:38px;border-radius:7px;overflow:hidden;background:#eef1f5;margin:8px 0 12px}}
.node-strategy-segment {{min-width:0;display:flex;align-items:center;justify-content:center;color:#fff;text-shadow:0 1px 2px #0009;font-size:12px;font-weight:750;white-space:nowrap;overflow:hidden}}
.charts {{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.chart-panel h3 {{margin:0 0 3px}} .chart-note {{margin:0 0 8px;color:var(--muted);font-size:12px}}
.chart {{min-height:250px}} .chart svg {{display:block;width:100%;height:auto;overflow:visible}}
.chart-legend {{display:flex;gap:14px;flex-wrap:wrap;margin:5px 0 8px;font-size:13px}}
.chart-legend span {{display:flex;align-items:center;gap:5px}}
.line-key {{width:18px;height:3px;border-radius:2px}}
.manhattan-head {{display:flex;align-items:start;justify-content:space-between;gap:12px;flex-wrap:wrap}}
.manhattan-head h3 {{margin:0 0 3px}} .manhattan-toggle {{display:flex;align-items:center;gap:6px;color:var(--muted);font-size:12px;white-space:nowrap}}
.manhattan-chart {{min-height:310px;overflow-x:auto;overflow-y:hidden;border:1px solid #eef1f5;border-radius:8px;background:#fff}}
.manhattan-chart svg {{display:block;height:auto;max-width:none}}
.eq-summary {{display:grid;grid-template-columns:repeat(2,1fr);gap:7px;margin:5px 0 8px}}
.eq-card {{background:#f7f8fa;border-radius:7px;padding:7px 9px;font-size:12px}} .eq-card b {{display:block;font-size:17px;margin-top:2px}}
.layout {{display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:12px;align-items:stretch;margin-bottom:12px}}
.layout > .panel,.side-column > .panel {{margin-bottom:0}}
.layout > .panel {{height:100%}}
.side-column {{display:grid;grid-template-rows:auto minmax(0,1fr);gap:12px;height:100%}}
#node-panel,#details {{padding:10px}}
.legend {{display:flex;gap:8px 14px;flex-wrap:wrap;margin:8px 0 12px}} .legend-item {{display:flex;align-items:center;gap:5px;font-size:13px}}
.swatch {{width:14px;height:14px;border-radius:3px;border:1px solid #0002}}
.strategy-grid {{display:grid;grid-template-columns:repeat(var(--grid-columns),minmax(58px,1fr));gap:5px}}
.rank-cell {{position:relative;height:70px;border:1px solid #bfc6d1;border-radius:5px;overflow:hidden;background:#fff;cursor:pointer;padding:0}}
.rank-cell:hover,.rank-cell.selected {{outline:3px solid #315efb;outline-offset:1px}}
.segments {{position:absolute;left:0;bottom:0;display:flex;width:100%}} .segment {{height:100%;min-width:0}}
.rank-label {{position:absolute;left:5px;top:4px;padding:1px 4px;background:#ffffffd9;border-radius:4px;font-weight:800;font-size:13px}}
.range-weight {{position:absolute;right:4px;bottom:3px;background:#111827c7;color:white;border-radius:3px;padding:1px 3px;font-size:10px}}
.details h3 {{margin:0 0 5px;font-size:16px}} .rank-equity {{margin:0 0 6px;color:var(--muted);font-size:12px}}
table {{border-collapse:collapse;width:100%}} th,td {{padding:7px 5px;border-bottom:1px solid var(--line);text-align:right;font-size:13px}} th:first-child,td:first-child {{text-align:left}}
#details th,#details td {{padding:4px 3px;font-size:12px;line-height:1.2}}
.terminal {{font-size:18px;line-height:1.8}}
.empty {{color:var(--muted);padding:30px;text-align:center}}
@media(max-width:900px) {{.layout,.charts,.range-metrics-grid {{grid-template-columns:1fr}} .strategy-grid {{overflow-x:auto}}}}
</style></head><body><div class="app">
<div id="low-reach-alert" class="low-reach-alert" role="alert" hidden></div>
<section class="panel history-nav"><div id="breadcrumbs" class="crumbs"></div><select id="history-jump" class="jump" aria-label="履歴へ移動"></select><div id="history-info" class="history-info"></div></section>
<div id="action-panel" class="panel"></div>
<div class="layout"><main class="panel"><div id="legend" class="legend"></div><div id="strategy-grid" class="strategy-grid"></div></main><aside class="side-column"><div id="node-panel" class="panel"></div><div id="details" class="panel details"></div></aside></div>
<div id="range-metrics-panel" class="panel"></div>
<section id="manhattan-panel" class="panel chart-panel">
  <div class="manhattan-head"><div><h3>Manhattan strategy</h3><p class="chart-note">EQが低い順に並べた等幅rankごとのaction頻度（各barの合計は100%）</p></div><label class="manhattan-toggle"><input id="manhattan-show-zero" type="checkbox">Show zero-weight ranks</label></div>
  <div id="manhattan-legend" class="chart-legend"></div><div id="manhattan-chart" class="manhattan-chart"></div>
</section>
<div class="charts">
  <section class="panel chart-panel"><h3>Conditional ranges</h3><p class="chart-note">選択した履歴へ到達したときの両プレイヤーの条件付きrank分布</p><div id="range-legend" class="chart-legend"></div><div id="range-chart" class="chart"></div></section>
  <section class="panel chart-panel"><h3>Equity distribution</h3><p class="chart-note">横軸はEQが低い順に並べた自分のrange percentile、縦軸は相手rangeに対するshowdown EQ</p><div id="eq-summary" class="eq-summary"></div><div id="equity-legend" class="chart-legend"></div><div id="equity-chart" class="chart"></div></section>
</div>
</div>
<script id="viewer-data" type="application/json">{serialized_payload}</script>
<script>
const DATA=JSON.parse(document.getElementById('viewer-data').textContent);
if(DATA.schema_version!==6)throw new Error(`Unsupported viewer schema: ${{DATA.schema_version}}`);
const NODES=DATA.nodes; const RANKS=DATA.ranks;
function floats(encoded,expected){{const raw=atob(encoded),bytes=new Uint8Array(raw.length);for(let i=0;i<raw.length;i++)bytes[i]=raw.charCodeAt(i);const values=new Float32Array(bytes.buffer);if(values.length!==expected)throw new Error(`Invalid viewer array length: expected ${{expected}}, got ${{values.length}}`);return values}}
const PROBS=floats(DATA.probabilities_f32,DATA.array_counts.probabilities), EVS=floats(DATA.action_evs_f32,DATA.array_counts.action_evs), RANGES=floats(DATA.conditional_ranges_f32,DATA.array_counts.conditional_ranges), RANGE_MASSES=floats(DATA.range_masses_f32,DATA.array_counts.range_masses);
const PLAYER_COLORS=['#0f766e','#7c3aed'];
const ZERO_RANGE_EPSILON=1e-10;
let current=DATA.root_id,selectedRank=0,showZeroWeightRanks=false;
const el=id=>document.getElementById(id), pct=x=>`${{(100*x).toFixed(x<0.001?3:1)}}%`, num=x=>Number(x).toFixed(4);
function historyStepLabel(node){{if(node.parent_id===null)return 'ROOT';const parent=NODES[node.parent_id],action=node.history[node.history.length-1];return `[${{parent.player}}] ${{action}}`}}
function historyLabel(node){{const steps=[];let currentNode=node;while(currentNode.parent_id!==null){{steps.push(historyStepLabel(currentNode));currentNode=NODES[currentNode.parent_id]}}steps.reverse();if(!node.terminal)steps.push(`[${{node.player}}] ?`);return steps.length?steps.join(' → '):'ROOT'}}
function buildJump(){{const select=el('history-jump');NODES.filter(n=>!n.terminal).sort((a,b)=>a.history.length-b.history.length||historyLabel(a).localeCompare(historyLabel(b))).forEach(n=>{{const o=document.createElement('option');o.value=n.id;o.textContent=historyLabel(n);select.append(o)}});select.addEventListener('change',()=>navigate(Number(select.value)))}}
function ancestors(node){{const result=[];let n=node;while(n){{result.push(n);n=n.parent_id===null?null:NODES[n.parent_id]}}return result.reverse()}}
function renderCrumbs(node){{const box=el('breadcrumbs');box.replaceChildren();ancestors(node).forEach((n,i)=>{{if(i){{const s=document.createElement('span');s.className='separator';s.textContent='›';box.append(s)}}const b=document.createElement('button');b.className='crumb';b.textContent=historyStepLabel(n);b.onclick=()=>navigate(n.id);box.append(b)}});if(!node.terminal){{const separator=document.createElement('span');separator.className='separator';separator.textContent='›';const turn=document.createElement('span');turn.className='crumb current-turn';turn.textContent=`[${{node.player}}] ?`;box.append(separator,turn)}}el('history-jump').value=String(node.terminal?(node.parent_id??DATA.root_id):node.id)}}
function infoBadge(textValue){{const item=document.createElement('span');item.className='badge';item.textContent=textValue;return item}}
function renderLowReachAlert(node){{const alert=el('low-reach-alert'),lowReach=node.reach_probability<DATA.major_reach_threshold;alert.hidden=!lowReach;alert.textContent=lowReach?`このnodeへの到達確率は${{pct(node.reach_probability)}}と低いため、戦略が十分に収束していない可能性があります。`:''}}
function renderHistoryInfo(node){{const box=el('history-info');box.replaceChildren();box.append(infoBadge(`Reach ${{pct(node.reach_probability)}}`),infoBadge(`Depth ${{node.history.length}}`))}}
function playerRange(node,playerIndex){{const start=node.ranges_offset+playerIndex*RANKS.length;return Array.from(RANGES.subarray(start,start+RANKS.length))}}
function playerRetention(node,playerIndex){{const range=playerRange(node,playerIndex),prior=playerRange(NODES[DATA.root_id],playerIndex),mass=RANGE_MASSES[node.range_masses_offset+playerIndex];return range.map((weight,index)=>prior[index]>0?weight*mass/prior[index]:0)}}
function equitiesAgainst(opponent){{let lower=0;return opponent.map(w=>{{const equity=lower+0.5*w;lower+=w;return equity}})}}
function equityData(node){{const ranges=DATA.player_names.map((_,i)=>playerRange(node,i));const byRank=ranges.map((_,i)=>equitiesAgainst(ranges[1-i]));const overall=ranges.map((own,i)=>own.reduce((sum,w,r)=>sum+w*byRank[i][r],0));return {{ranges,byRank,overall}}}}
function seatValue(label,value){{const item=document.createElement('div');item.className='seat-value';item.textContent=label;const strong=document.createElement('b');strong.textContent=value;item.append(strong);return item}}
function renderSeat(name,context,active){{const key=name.toLowerCase(),seat=document.createElement('section');seat.className=`seat-card${{active?' active':''}}`;const heading=document.createElement('h3');heading.textContent=name;const values=document.createElement('div');values.className='seat-values';const stack=context[`${{key}}_remaining_stack`],committed=context[`${{key}}_committed`];values.append(seatValue('Stack',stack==null?'—':num(stack)),seatValue('On table',committed==null?'—':num(committed)));seat.append(heading,values);return seat}}
function facingBetData(node){{if(node.parent_id===null||node.terminal)return null;const parent=NODES[node.parent_id],action=node.history[node.history.length-1];if(parent.terminal||!/(bet|raise|all-in)/i.test(action))return null;const key=parent.player.toLowerCase(),before=Number(parent.context?.[`${{key}}_committed`]??0),after=Number(node.context?.[`${{key}}_committed`]??before),callBefore=Number(parent.context?.amount_to_call??0),basis=Number(parent.context?.pot??0)+callBefore,aggressiveAmount=Math.max(0,(after-before)-callBefore);return {{label:action,fraction:basis>0?aggressiveAmount/basis:0}}}}
function renderNode(node){{const panel=el('node-panel');panel.replaceChildren();if(node.terminal){{const summary=document.createElement('p');summary.textContent=(node.returns||[]).map((value,index)=>`${{DATA.player_names[index]}} EV ${{Number(value).toFixed(4)}}`).join(' / ');panel.append(summary);return}}const context=node.context||{{}},state=document.createElement('div');state.className='pot-state';const center=document.createElement('section');center.className='pot-center';const potMain=document.createElement('div');potMain.className='pot-main';const label=document.createElement('small');label.textContent='Pot';const amount=document.createElement('div');amount.className='pot-amount';amount.textContent=num(context.pot??0);potMain.append(label,amount);const betState=document.createElement('div');betState.className='bet-state';const facing=facingBetData(node);betState.append(infoBadge(`Facing ${{facing?.label??'—'}}`),infoBadge(`Bet size ${{facing?pct(facing.fraction)+' pot':'—'}}`),infoBadge(`To call ${{num(context.amount_to_call??0)}}`));center.append(potMain,betState);state.append(center,renderSeat('OOP',context,node.player==='OOP'),renderSeat('IP',context,node.player==='IP'));panel.append(state)}}
function renderRangeMetrics(node){{const panel=el('range-metrics-panel');panel.replaceChildren();panel.hidden=node.terminal;if(node.terminal)return;const eq=equityData(node),pot=Number(node.context?.pot??0),head=document.createElement('div');head.className='range-metrics-head';const title=document.createElement('h3');title.textContent='Range metrics';head.append(title);panel.append(head);const grid=document.createElement('div');grid.className='range-metrics-grid';const order=DATA.player_names.map((name,index)=>({{name:name,index:index}})).sort((a,b)=>(a.name==='OOP'?0:1)-(b.name==='OOP'?0:1));order.forEach(player=>{{const card=document.createElement('section');card.className='range-player-card';const heading=document.createElement('h4');heading.textContent=player.name;card.append(heading);const values=document.createElement('div');values.className='range-player-values';const equity=eq.overall[player.index],ev=Number(node.range_evs[player.index]),eqr=pot>0&&equity>1e-12?ev/(pot*equity):null;[['EV',ev.toFixed(5)],['EQ',pct(equity)],['EQR',eqr===null?'—':pct(eqr)]].forEach(([label,value])=>{{const item=document.createElement('div');item.className='range-player-value';item.textContent=label;const strong=document.createElement('b');strong.textContent=value;item.append(strong);values.append(item)}});card.append(values);grid.append(card)}});panel.append(grid)}}
function renderActions(node){{const panel=el('action-panel');panel.replaceChildren();if(node.terminal){{const d=document.createElement('div');d.className='terminal';d.textContent='この履歴は終端です。Breadcrumbまたは履歴選択から別の局面へ移動してください。';panel.append(d);return}}const aggregate=document.createElement('div');aggregate.className='node-strategy';aggregate.setAttribute('aria-label','Node-level aggregate action frequencies');node.actions.forEach(a=>{{if(a.aggregate_probability<=1e-10)return;const seg=document.createElement('div');seg.className='node-strategy-segment';seg.style.background=a.color;seg.style.flexGrow=String(a.aggregate_probability);seg.title=`${{a.label}}: ${{pct(a.aggregate_probability)}}`;if(a.aggregate_probability>=0.08)seg.textContent=`${{a.label}} ${{pct(a.aggregate_probability)}}`;aggregate.append(seg)}});panel.append(aggregate);const row=document.createElement('div');row.className='actions';node.actions.forEach(a=>{{const b=document.createElement('button');b.className='action-button';b.style.setProperty('--action-color',a.color);b.textContent=a.label;const p=document.createElement('span');const ev=a.aggregate_ev===null?'—':Number(a.aggregate_ev).toFixed(5);p.textContent=`Freq ${{pct(a.aggregate_probability)}} · EV ${{ev}}`;b.append(p);b.onclick=()=>navigate(a.child_id);row.append(b)}});panel.append(row)}}
function fillActionLegend(box,node){{box.replaceChildren();if(node.terminal)return;node.actions.forEach(a=>{{const item=document.createElement('span'),s=document.createElement('i');item.className='legend-item';s.className='swatch';s.style.background=a.color;item.append(s,document.createTextNode(a.label));box.append(item)}})}}
function renderLegend(node){{fillActionLegend(el('legend'),node);fillActionLegend(el('manhattan-legend'),node)}}
function strategy(node,rankIndex,actionIndex){{return PROBS[node.strategy_offset+rankIndex*node.action_count+actionIndex]}}
function actionEv(node,rankIndex,actionIndex){{return EVS[node.ev_offset+rankIndex*node.action_count+actionIndex]}}
function svgElement(tag,attributes={{}}){{const node=document.createElementNS('http://www.w3.org/2000/svg',tag);Object.entries(attributes).forEach(([key,value])=>node.setAttribute(key,String(value)));return node}}
function manhattanRows(node){{const eq=equityData(node),player=node.player_index;return RANKS.map((rank,ri)=>({{rank:rank,rankIndex:ri,equity:eq.byRank[player][ri],weight:eq.ranges[player][ri]}})).filter(row=>showZeroWeightRanks||row.weight>ZERO_RANGE_EPSILON).sort((a,b)=>a.equity-b.equity||a.rank-b.rank)}}
function selectRank(node,rankIndex){{selectedRank=rankIndex;renderGrid(node);renderDetails(node);renderManhattan(node)}}
function renderManhattan(node){{const box=el('manhattan-chart');box.replaceChildren();if(node.terminal){{const d=document.createElement('div');d.className='empty';d.textContent='終端ノードには戦略がありません';box.append(d);return}}const rows=manhattanRows(node);if(!rows.length){{const d=document.createElement('div');d.className='empty';d.textContent='No in-range ranks';box.append(d);return}}const H=310,M={{l:50,r:16,t:12,b:54}},minimumBarWidth=13,W=Math.max(box.clientWidth||720,M.l+M.r+rows.length*minimumBarWidth),plotW=W-M.l-M.r,plotH=H-M.t-M.b,barWidth=plotW/rows.length,svg=svgElement('svg',{{viewBox:`0 0 ${{W}} ${{H}}`,width:W,height:H,role:'img','aria-label':`${{node.player}} Manhattan strategy: equal-width ranks sorted by equity`}}),defs=svgElement('defs'),pattern=svgElement('pattern',{{id:'zero-range-hatch',width:6,height:6,patternUnits:'userSpaceOnUse',patternTransform:'rotate(45)'}});pattern.append(svgElement('line',{{x1:0,y1:0,x2:0,y2:6,stroke:'#111827','stroke-width':2,opacity:.28}}));defs.append(pattern);svg.append(defs);[0,.25,.5,.75,1].forEach(f=>{{const y=M.t+plotH*(1-f);svg.append(svgElement('line',{{x1:M.l,x2:W-M.r,y1:y,y2:y,stroke:'#e2e6ed','stroke-width':1}}));const label=svgElement('text',{{x:M.l-8,y:y+4,'text-anchor':'end','font-size':11,fill:'#667085'}});label.textContent=pct(f);svg.append(label)}});const tickIndexes=[0,.25,.5,.75,1].map(f=>Math.round(f*(rows.length-1))).filter((value,index,array)=>array.indexOf(value)===index);tickIndexes.forEach(index=>{{const row=rows[index],x=M.l+barWidth*(index+.5);svg.append(svgElement('line',{{x1:x,x2:x,y1:M.t+plotH,y2:M.t+plotH+5,stroke:'#98a2b3','stroke-width':1}}));const label=svgElement('text',{{x:x,y:H-24,'text-anchor':'middle','font-size':11,fill:'#667085'}});label.textContent=`EQ ${{pct(row.equity)}}`;svg.append(label)}});rows.forEach((row,index)=>{{const x=M.l+barWidth*index,group=svgElement('g',{{role:'button',tabindex:0,'aria-label':`Rank ${{row.rank}}, equity ${{pct(row.equity)}}`}});let cumulative=0,tooltip=`${{node.player}} rank ${{row.rank}} | EQ ${{pct(row.equity)}} | range weight ${{pct(row.weight)}}`;node.actions.forEach((action,ai)=>{{const probability=Math.max(0,Math.min(1,strategy(node,row.rankIndex,ai))),remaining=Math.max(0,1-cumulative),heightProbability=Math.min(probability,remaining),height=plotH*heightProbability,y=M.t+plotH*(1-cumulative-heightProbability);tooltip+=`\n${{action.label}}: ${{pct(probability)}} | EV ${{actionEv(node,row.rankIndex,ai).toFixed(5)}}`;if(height>1e-6)group.append(svgElement('rect',{{x:x+.5,y:y,width:Math.max(.5,barWidth-1),height:height,fill:action.color}}));cumulative+=heightProbability}});if(row.weight<=ZERO_RANGE_EPSILON)group.append(svgElement('rect',{{x:x+.5,y:M.t,width:Math.max(.5,barWidth-1),height:plotH,fill:'url(#zero-range-hatch)'}}));if(row.rankIndex===selectedRank)group.append(svgElement('rect',{{x:x+.5,y:M.t+.5,width:Math.max(.5,barWidth-1),height:plotH-1,fill:'none',stroke:'#315efb','stroke-width':3}}));const title=svgElement('title');title.textContent=tooltip;group.append(title);group.style.cursor='pointer';group.addEventListener('click',()=>selectRank(node,row.rankIndex));group.addEventListener('keydown',event=>{{if(event.key==='Enter'||event.key===' '){{event.preventDefault();selectRank(node,row.rankIndex)}}}});svg.append(group)}});const xTitle=svgElement('text',{{x:M.l+plotW/2,y:H-6,'text-anchor':'middle','font-size':12,fill:'#475467'}});xTitle.textContent='Hands sorted by equity (equal-width ranks)';svg.append(xTitle);box.append(svg)}}
function renderChart(containerId,series,yMax,percentAxis){{const box=el(containerId);box.replaceChildren();const W=720,H=260,M={{l:50,r:16,t:12,b:34}},plotW=W-M.l-M.r,plotH=H-M.t-M.b;const svg=svgElement('svg',{{viewBox:`0 0 ${{W}} ${{H}}`,role:'img'}});[0,.25,.5,.75,1].forEach(f=>{{const y=M.t+plotH*(1-f);svg.append(svgElement('line',{{x1:M.l,x2:W-M.r,y1:y,y2:y,stroke:'#e2e6ed','stroke-width':1}}));const label=svgElement('text',{{x:M.l-8,y:y+4,'text-anchor':'end','font-size':11,fill:'#667085'}});label.textContent=percentAxis?pct(yMax*f):(yMax*f).toFixed(yMax<.1?3:2);svg.append(label)}});const labelStep=Math.max(1,Math.ceil(RANKS.length/10));RANKS.forEach((rank,i)=>{{if(i%labelStep!==0&&i!==RANKS.length-1)return;const x=M.l+(RANKS.length===1?plotW/2:plotW*i/(RANKS.length-1));const label=svgElement('text',{{x:x,y:H-10,'text-anchor':'middle','font-size':11,fill:'#667085'}});label.textContent=rank;svg.append(label)}});series.forEach(s=>{{const points=s.values.map((value,i)=>{{const x=M.l+(RANKS.length===1?plotW/2:plotW*i/(RANKS.length-1)),y=M.t+plotH*(1-Math.min(value,yMax)/yMax);return `${{x}},${{y}}`}}).join(' ');svg.append(svgElement('polyline',{{points:points,fill:'none',stroke:s.color,'stroke-width':2.5,'stroke-linejoin':'round','stroke-linecap':'round'}}));s.values.forEach((value,i)=>{{const x=M.l+(RANKS.length===1?plotW/2:plotW*i/(RANKS.length-1)),y=M.t+plotH*(1-Math.min(value,yMax)/yMax),dot=svgElement('circle',{{cx:x,cy:y,r:RANKS.length<=60?3:1.8,fill:s.color}}),title=svgElement('title');title.textContent=`${{s.name}} rank ${{RANKS[i]}}: ${{pct(value)}}`;dot.append(title);svg.append(dot)}})}});box.append(svg)}}
function renderEquityDistribution(series){{const box=el('equity-chart');box.replaceChildren();const W=720,H=260,M={{l:50,r:16,t:12,b:34}},plotW=W-M.l-M.r,plotH=H-M.t-M.b,svg=svgElement('svg',{{viewBox:`0 0 ${{W}} ${{H}}`,role:'img','aria-label':'Equity distribution by range percentile'}});[0,.25,.5,.75,1].forEach(f=>{{const y=M.t+plotH*(1-f);svg.append(svgElement('line',{{x1:M.l,x2:W-M.r,y1:y,y2:y,stroke:'#e2e6ed','stroke-width':1}}));const yLabel=svgElement('text',{{x:M.l-8,y:y+4,'text-anchor':'end','font-size':11,fill:'#667085'}});yLabel.textContent=pct(f);svg.append(yLabel);const x=M.l+plotW*f,xLabel=svgElement('text',{{x:x,y:H-10,'text-anchor':'middle','font-size':11,fill:'#667085'}});xLabel.textContent=pct(f);svg.append(xLabel)}});series.forEach(s=>{{const order=s.equities.map((equity,index)=>({{equity:equity,index:index,rank:RANKS[index],weight:s.weights[index]}})).sort((a,b)=>a.equity-b.equity||a.rank-b.rank);let cumulative=0,path='';const points=[];order.forEach((hand,index)=>{{const start=cumulative,end=index===order.length-1?1:Math.min(1,cumulative+hand.weight),y=M.t+plotH*(1-hand.equity),xStart=M.l+plotW*start,xEnd=M.l+plotW*end;if(index===0)path=`M ${{xStart}} ${{y}}`;else path+=` L ${{xStart}} ${{y}}`;path+=` L ${{xEnd}} ${{y}}`;points.push({{...hand,start:start,end:end,x:(xStart+xEnd)/2,y:y}});cumulative=end}});svg.append(svgElement('path',{{d:path,fill:'none',stroke:s.color,'stroke-width':2.5,'stroke-linejoin':'round','stroke-linecap':'round'}}));points.forEach(point=>{{if(point.weight<=1e-10)return;const dot=svgElement('circle',{{cx:point.x,cy:point.y,r:RANKS.length<=60?3:1.8,fill:s.color}}),title=svgElement('title');title.textContent=`${{s.name}} rank ${{point.rank}} | percentile ${{pct(point.start)}}–${{pct(point.end)}} | EQ ${{pct(point.equity)}} | weight ${{pct(point.weight)}}`;dot.append(title);svg.append(dot)}})}});box.append(svg)}}
function renderChartLegend(id){{const box=el(id);box.replaceChildren();DATA.player_names.forEach((name,i)=>{{const item=document.createElement('span'),key=document.createElement('i');key.className='line-key';key.style.background=PLAYER_COLORS[i%PLAYER_COLORS.length];item.append(key,document.createTextNode(name));box.append(item)}})}}
function renderCharts(node){{const eq=equityData(node),rangeMax=Math.max(...eq.ranges.flat(),1e-6)*1.08,series=DATA.player_names.map((name,i)=>({{name:name,values:eq.ranges[i],color:PLAYER_COLORS[i%PLAYER_COLORS.length]}}));renderChartLegend('range-legend');renderChart('range-chart',series,rangeMax,true);renderChartLegend('equity-legend');renderEquityDistribution(DATA.player_names.map((name,i)=>({{name:name,equities:eq.byRank[i],weights:eq.ranges[i],color:PLAYER_COLORS[i%PLAYER_COLORS.length]}})));const summary=el('eq-summary');summary.replaceChildren();DATA.player_names.forEach((name,i)=>{{const card=document.createElement('div');card.className='eq-card';card.textContent=`${{name}} range EQ`;const value=document.createElement('b');value.textContent=pct(eq.overall[i]);card.append(value);summary.append(card)}})}}
function renderGrid(node){{const grid=el('strategy-grid');grid.replaceChildren();grid.style.setProperty('--grid-columns',DATA.grid_columns);if(node.terminal){{const d=document.createElement('div');d.className='empty';d.textContent='終端ノード';grid.append(d);return}}const weights=playerRange(node,node.player_index),retentions=playerRetention(node,node.player_index);RANKS.forEach((rank,ri)=>{{const cell=document.createElement('button');cell.className='rank-cell'+(ri===selectedRank?' selected':'');cell.setAttribute('aria-label',`Rank ${{rank}} strategy, ${{pct(retentions[ri])}} retained from root`);const segs=document.createElement('div');segs.className='segments';segs.style.height=pct(Math.max(0,Math.min(1,retentions[ri])));let tooltip=`${{node.player}}(${{rank}})\nRange retained: ${{pct(retentions[ri])}}\nConditional range weight: ${{pct(weights[ri])}}\n`;node.actions.forEach((a,ai)=>{{const p=strategy(node,ri,ai);tooltip+=`${{a.label}}: ${{pct(p)}}  EV ${{actionEv(node,ri,ai).toFixed(5)}}\n`;if(p>1e-7){{const seg=document.createElement('span');seg.className='segment';seg.style.background=a.color;seg.style.flexGrow=String(p);seg.title=`${{a.label}} ${{pct(p)}}`;segs.append(seg)}}}});cell.title=tooltip.trim();const label=document.createElement('span');label.className='rank-label';label.textContent=rank;const weight=document.createElement('span');weight.className='range-weight';weight.textContent=pct(retentions[ri]);weight.title=`Root retention ${{pct(retentions[ri])}}`;cell.append(segs,label,weight);cell.onclick=()=>selectRank(node,ri);grid.append(cell)}})}}
function renderDetails(node){{const box=el('details');box.replaceChildren();const h=document.createElement('h3');h.textContent=node.terminal?'終端の詳細':`Rank ${{RANKS[selectedRank]}}`;box.append(h);if(node.terminal){{const p=document.createElement('p');p.textContent=(node.returns||[]).map((v,i)=>`${{DATA.player_names[i]}} ${{Number(v).toFixed(4)}}`).join(' / ');box.append(p);return}}const eq=equityData(node),equity=document.createElement('p');equity.className='rank-equity';equity.textContent=`EQ ${{pct(eq.byRank[node.player_index][selectedRank])}}`;box.append(equity);const table=document.createElement('table');table.innerHTML='<thead><tr><th>Action</th><th>Freq.</th><th>EV</th></tr></thead>';const body=document.createElement('tbody');node.actions.forEach((a,ai)=>{{const tr=document.createElement('tr'),name=document.createElement('td'),prob=document.createElement('td'),ev=document.createElement('td');const sw=document.createElement('span');sw.className='swatch';sw.style.display='inline-block';sw.style.background=a.color;name.append(sw,document.createTextNode(' '+a.label));prob.textContent=pct(strategy(node,selectedRank,ai));ev.textContent=actionEv(node,selectedRank,ai).toFixed(5);tr.append(name,prob,ev);body.append(tr)}});table.append(body);box.append(table)}}
function navigate(id){{current=id;const node=NODES[id];renderLowReachAlert(node);renderCrumbs(node);renderHistoryInfo(node);renderNode(node);renderRangeMetrics(node);renderActions(node);renderLegend(node);renderGrid(node);renderDetails(node);renderManhattan(node);renderCharts(node);window.scrollTo({{top:0,behavior:'smooth'}})}}
el('manhattan-show-zero').addEventListener('change',event=>{{showZeroWeightRanks=event.target.checked;renderManhattan(NODES[current])}});
window.addEventListener('resize',()=>renderManhattan(NODES[current]));
buildJump();navigate(DATA.root_id);
</script></body></html>"""
