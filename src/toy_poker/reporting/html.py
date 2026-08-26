"""Small dependency-free HTML report renderer."""

from __future__ import annotations

import html
from pathlib import Path

from toy_poker.games.base import GamePlugin


def _information_table(infos: list[dict]) -> str:
    rows = []
    for info in infos:
        context = ", ".join(
            f"{html.escape(str(key))}={html.escape(f'{value:.6g}' if isinstance(value, float) else str(value))}"
            for key, value in info.get("context", {}).items()
        )
        context_html = f'<br><span class="context">{context}</span>' if context else ""
        strategy = "<br>".join(
            f"{html.escape(action['action'])}: <strong>{action['probability']:.2%}</strong>"
            for action in info["actions"]
        )
        action_evs = "<br>".join(
            f"{html.escape(action['action'])}: {action['ev']:+.6f}" for action in info["actions"]
        )
        off_path = " <span class=\"tag\">off path</span>" if info["is_off_path"] else ""
        rows.append(
            f"<tr><td>{html.escape(info['label'])}{off_path}{context_html}</td>"
            f"<td>{info['reach_probability']:.6%}</td><td>{strategy}</td>"
            f"<td>{info['policy_ev']:+.6f}</td><td>{action_evs}</td></tr>"
        )
    return (
        "<table><thead><tr><th>Decision</th><th>Reach</th><th>Strategy</th>"
        "<th>Policy EV</th><th>Action EV</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def save_html(
    path: Path,
    analysis: dict,
    plugin: GamePlugin,
    tree_created: bool,
    major_tree_created: bool,
    viewer_created: bool = False,
    include_data_links: bool = True,
) -> None:
    summary = analysis["summary"]
    solver = analysis["solver"]
    cards = "".join(
        f'<div class="card">{html.escape(player)} EV<div class="value">{value:+.6f}</div></div>'
        for player, value in summary["returns"].items()
    )
    unconstrained_card = (
        '<div class="card">Unconstrained exploitability<div class="value">'
        f"{float(summary['unconstrained_exploitability']):.8f}</div></div>"
        if summary.get("unconstrained_exploitability") is not None
        else ""
    )
    major_reach_threshold = float(
        analysis.get("reporting", {}).get("major_reach_threshold", 1e-4)
    )
    major_infos = [
        info
        for info in analysis["information_sets"]
        if info["reach_probability"] >= major_reach_threshold
    ]
    reporting = analysis.get("reporting", {})
    major_only = reporting.get("report_scope", "full") == "major_only"
    policy_filename = reporting.get("policy_filename", "policy.json")
    analysis_filename = reporting.get("analysis_filename", "analysis.json")
    information_sets_filename = reporting.get(
        "information_sets_filename", "information_sets.csv"
    )
    terminal_paths_filename = reporting.get(
        "terminal_paths_filename", "terminal_paths.csv"
    )
    major_tree = (
        '<h3>Major action tree</h3><img src="figures/major_strategy_tree.png" '
        'alt="Major strategy tree">'
        if major_tree_created
        else ""
    )
    full_tree = (
        '<h3>Full legal-action tree</h3><img src="figures/strategy_tree.png" '
        'alt="Full strategy tree">'
        if tree_created
        else ""
    )
    full_analysis = "" if major_only else f"""
<hr><h2>Full analysis</h2>
{full_tree}
<h3>Full action probabilities</h3><img src="figures/strategy_probabilities.png" alt="Full action probabilities">
<h3>Full information sets</h3>{_information_table(analysis['information_sets'])}
<h3>Full action EV</h3><img src="figures/action_ev.png" alt="Action EV">"""
    rank_distribution = (
        '<h2>Private-number distributions</h2>'
        '<img src="figures/rank_distribution.png" alt="Private-number distributions">'
        if analysis["game"].get("rank_distribution") is not None
        else ""
    )
    viewer = (
        '<section class="viewer-cta"><div><strong>Interactive strategy viewer</strong>'
        '<br><span>履歴を選び、各private numberの混合戦略とAction EVを確認できます。</span></div>'
        '<a href="strategy_viewer.html">Open viewer →</a></section>'
        if viewer_created
        else ""
    )
    node_locks = analysis["solver"].get("node_locks", [])
    node_lock_html = ""
    if node_locks:
        items = []
        for lock in node_locks:
            actions = ", ".join(
                f"{html.escape(action)} {float(probability):.2%}"
                for action, probability in lock["actions"].items()
            )
            items.append(
                f"<li><code>{html.escape(lock['player'])}</code> rank "
                f"<code>{lock['rank']}</code> at <code>{html.escape(lock['history'])}</code>: "
                f"{actions}</li>"
            )
        node_lock_html = (
            "<h3>Node locks</h3><ul>" + "".join(items) + "</ul>"
            "<p>The convergence metric is the constrained Nash gap: locked actions "
            "cannot be changed by the best response.</p>"
        )
    data_links = (
        f'<p>Data: <a href="{html.escape(analysis_filename)}">analysis JSON</a>, '
        f'<a href="{html.escape(policy_filename)}">policy</a>, '
        f'<a href="{html.escape(information_sets_filename)}">information sets CSV</a>, '
        f'<a href="{html.escape(terminal_paths_filename)}">terminal paths CSV</a>, '
        '<a href="convergence.csv">convergence CSV</a>'
        + (
            ', <a href="rank_distribution.csv">rank distribution CSV</a>'
            if rank_distribution
            else ""
        )
        + ".</p>"
        if include_data_links
        else ""
    )
    document = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>{html.escape(plugin.metadata.title)} report</title><style>
body {{ font-family: system-ui,sans-serif; margin:2rem auto; max-width:1200px; color:#222; }}
.cards {{ display:flex; gap:1rem; flex-wrap:wrap; }} .card {{ background:#f4f7fa; border-radius:8px; padding:1rem 1.4rem; min-width:180px; }}
.value {{ font-size:1.6rem; font-weight:700; }} table {{ border-collapse:collapse; width:100%; margin:1rem 0 2rem; }}
th,td {{ border-bottom:1px solid #ddd; padding:.65rem; text-align:left; vertical-align:top; }} th {{ background:#f4f7fa; }}
img {{ width:100%; height:auto; margin-bottom:2rem; }} .tag {{ font-size:.75rem; background:#eee; border-radius:4px; padding:.15rem .3rem; }}
.context {{ color:#666; font-size:.8rem; }} .section-note {{ color:#555; }}
hr {{ border:0; border-top:2px solid #ddd; margin:3rem 0; }}
.viewer-cta {{ display:flex;align-items:center;justify-content:space-between;gap:1rem;background:#eef2ff;border:1px solid #c7d2fe;border-radius:10px;padding:1rem 1.2rem;margin:1.5rem 0; }}
.viewer-cta a {{ background:#315efb;color:white;text-decoration:none;border-radius:7px;padding:.7rem 1rem;font-weight:700; }}
</style></head><body><h1>{html.escape(plugin.metadata.title)}</h1>
<p>EV is {html.escape(plugin.metadata.utility_unit)} for the acting player, conditional on reaching the information set.
{html.escape(plugin.metadata.utility_convention)} This game has terminal utility sum
{analysis['game'].get('utility_sum', 1.0):g}.</p>
<p>Solver backend: <code>{html.escape(analysis['solver']['backend'])}</code>;
algorithm: <code>{html.escape(analysis['solver'].get('algorithm', 'cfr_plus'))}</code>;
checkpoint evaluation: <code>{html.escape(analysis['solver'].get('checkpoint_evaluation_backend', analysis['solver']['backend']))}</code>.</p>
<div class="cards"><div class="card">Iterations<div class="value">{solver.get('completed_iterations', solver['iterations']):,} / {solver.get('requested_iterations', solver['iterations']):,}</div></div>
<div class="card">{'Constrained Nash gap' if solver.get('exploitability_definition') == 'constrained_nash_gap' else 'Exploitability'}<div class="value">{summary['exploitability']:.8f}</div></div>{unconstrained_card}{cards}</div>
<p>Stop reason: <code>{html.escape(solver.get('stop_reason', 'max_iterations'))}</code>;
target exploitability: <code>{solver.get('target_exploitability', float('nan')):.1e}</code>;
best checkpoint: <code>{solver.get('best_exploitability', summary['exploitability']):.8g}</code>
at iteration {solver.get('best_iteration', solver.get('iterations', 0)):,}.</p>
{node_lock_html}
{viewer}
{rank_distribution}
<h2>Major strategy</h2>
<p class="section-note">Information sets and tree nodes with reach probability below
{major_reach_threshold:.4%} are omitted here. Showing {len(major_infos)} of
{len(analysis['information_sets'])} information sets. All actions at a retained information set remain visible.</p>
{major_tree}
<h3>Major action probabilities</h3>
<img src="figures/major_strategy_probabilities.png" alt="Major action probabilities">
<h3>Major information sets</h3>{_information_table(major_infos)}
{'<h3>Major action EV</h3><img src="figures/action_ev.png" alt="Major action EV">' if major_only else ''}
{full_analysis}
<h3>Convergence</h3><img src="figures/convergence.png" alt="Convergence">
{data_links}</body></html>"""
    path.write_text(document, encoding="utf-8")
