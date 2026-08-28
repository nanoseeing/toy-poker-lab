"""Publish multiple pinned experiment runs as study-specific Git bundles."""

from __future__ import annotations

import html
import json
import shutil
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path

from toy_poker.reporting.plots import save_strategy_plot
from toy_poker.reporting.public_results import _load_analysis, _summary_document


@dataclass(frozen=True)
class StudySelection:
    study_id: str
    game_id: str
    run_id: str
    document: str


def load_study_selection(path: Path) -> list[StudySelection]:
    with path.open("rb") as handle:
        document = tomllib.load(handle)
    studies = document.get("studies")
    if not isinstance(studies, dict) or not studies:
        raise ValueError(f"Public study selection has no [studies.*] entries: {path}")
    result = []
    for study_id, entry in studies.items():
        if not isinstance(entry, dict):
            raise ValueError(f"studies.{study_id} must be a table")
        game_id = entry.get("game_id")
        run_id = entry.get("run_id")
        study_document = entry.get("document")
        if (
            not isinstance(game_id, str)
            or not isinstance(run_id, str)
            or not isinstance(study_document, str)
        ):
            raise ValueError(
                f"studies.{study_id} requires string game_id, run_id and document"
            )
        if Path(study_document).name != study_document or not study_document.endswith(
            ".md"
        ):
            raise ValueError(
                f"studies.{study_id}.document must be a Markdown filename"
            )
        result.append(StudySelection(study_id, game_id, run_id, study_document))
    result.sort(key=lambda selection: selection.document)
    return result


def _write_index(output_root: Path, entries: list[dict]) -> None:
    markdown_rows = []
    html_rows = []
    for entry in entries:
        study_id = entry["study_id"]
        viewer_md = (
            f"[Viewer]({study_id}/strategy_viewer.html)" if entry["viewer"] else "—"
        )
        viewer_html = (
            f'<a href="{html.escape(study_id)}/strategy_viewer.html">Viewer</a>'
            if entry["viewer"]
            else "—"
        )
        markdown_rows.append(
            f"| `{study_id}` | [Report]({study_id}/report.md) | {viewer_md} | "
            f"`{entry['exploitability']:.8g}` |"
        )
        html_rows.append(
            "<tr>"
            f"<td><code>{html.escape(study_id)}</code></td>"
            f'<td><a href="{html.escape(study_id)}/report.md">Report</a></td>'
            f"<td>{viewer_html}</td>"
            f"<td>{entry['exploitability']:.8g}</td>"
            f"<td><code>{html.escape(entry['run_id'])}</code></td>"
            "</tr>"
        )
    readme = """# Public strategy studies

教材で参照する固定済みsolver runです。理論と解説は[`docs/studies`](../../docs/studies/README.md)を参照してください。

| Study | Report | Viewer | Exploitability |
|---|---|---|---:|
""" + "\n".join(markdown_rows)
    readme += """

再生成:

```bash
toy-poker publish-studies --selection configs/public_studies.toml
```
"""
    (output_root / "README.md").write_text(readme, encoding="utf-8")
    document = """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Toy poker strategy studies</title><style>
body{font-family:system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#17212b}
table{border-collapse:collapse;width:100%}th,td{border-bottom:1px solid #d9dee7;padding:.7rem;text-align:left}
th{background:#f4f7fa}a{color:#315efb}</style></head><body><h1>Toy poker strategy studies</h1>
<table><thead><tr><th>Study</th><th>Report</th><th>Viewer</th><th>Exploitability</th><th>Run</th></tr></thead><tbody>"""
    document += "".join(html_rows) + "</tbody></table></body></html>"
    (output_root / "index.html").write_text(document, encoding="utf-8")


def _write_study_report(
    directory: Path,
    analysis: dict,
    selection: StudySelection,
    viewer_created: bool,
) -> None:
    summary = analysis["summary"]
    solver = analysis["solver"]
    viewer_markdown = (
        "- [Interactive strategy viewer](strategy_viewer.html)\n"
        if viewer_created
        else ""
    )
    markdown = f"""# {analysis['game']['title']}

Pinned result for study `{selection.study_id}` from run `{selection.run_id}`.

| Metric | Value |
|---|---:|
| Iterations | {solver.get('completed_iterations', solver.get('iterations', 0)):,} |
| Exploitability | {float(summary['exploitability']):.8g} |
| IP EV | {float(summary['returns']['IP']):+.8f} |
| OOP EV | {float(summary['returns']['OOP']):+.8f} |

![Root strategy](figures/root_strategy.png)

{viewer_markdown}- [Resolved configuration](resolved_config.json)
- [Source manifest](manifest.json)

The theory and poker interpretation are documented in
[`docs/studies/{selection.document}`](../../../docs/studies/{selection.document}).
"""
    (directory / "report.md").write_text(markdown, encoding="utf-8")
    viewer_html = (
        '<p><a href="strategy_viewer.html">Interactive strategy viewer</a></p>'
        if viewer_created
        else ""
    )
    document = f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(selection.study_id)}</title>
<style>body{{font-family:system-ui,sans-serif;max-width:1000px;margin:2rem auto;padding:0 1rem}}
img{{max-width:100%;height:auto}}table{{border-collapse:collapse}}td,th{{padding:.5rem;border-bottom:1px solid #ddd}}</style>
</head><body><h1>{html.escape(analysis['game']['title'])}</h1>
<p>Study <code>{html.escape(selection.study_id)}</code>; run <code>{html.escape(selection.run_id)}</code>.</p>
<table><tr><th>Iterations</th><td>{solver.get('completed_iterations', solver.get('iterations', 0)):,}</td></tr>
<tr><th>Exploitability</th><td>{float(summary['exploitability']):.8g}</td></tr>
<tr><th>IP EV</th><td>{float(summary['returns']['IP']):+.8f}</td></tr>
<tr><th>OOP EV</th><td>{float(summary['returns']['OOP']):+.8f}</td></tr></table>
{viewer_html}<img src="figures/root_strategy.png" alt="Root strategy"></body></html>"""
    (directory / "report.html").write_text(document, encoding="utf-8")


def publish_studies(
    artifact_root: Path,
    output_root: Path,
    selections: list[StudySelection],
) -> list[Path]:
    if not selections:
        raise ValueError("No studies were selected for publication")
    output_root.mkdir(parents=True, exist_ok=True)
    published = []
    entries = []
    for selection in selections:
        source = artifact_root / selection.game_id / selection.run_id
        if not source.is_dir():
            raise FileNotFoundError(f"Study artifact does not exist: {source}")
        analysis = _load_analysis(source)
        manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
        target = output_root / selection.study_id
        staging = Path(
            tempfile.mkdtemp(prefix=f".{selection.study_id}-", dir=output_root)
        )
        try:
            target_figures = staging / "figures"
            target_figures.mkdir()
            root_infos = [
                info for info in analysis["information_sets"] if not info.get("history")
            ]
            save_strategy_plot(
                target_figures / "root_strategy.png",
                root_infos,
                analysis["game"]["title"],
                "root strategy",
            )
            viewer_created = (source / "strategy_viewer.html").exists()
            if viewer_created:
                shutil.copy2(source / "strategy_viewer.html", staging / "strategy_viewer.html")
            for name in ("resolved_config.json", "manifest.json"):
                shutil.copy2(source / name, staging / name)
            _write_study_report(staging, analysis, selection, viewer_created)
            summary = _summary_document(
                analysis, manifest, selection.run_id, viewer_created
            )
            summary["study_id"] = selection.study_id
            (staging / "summary.json").write_text(
                json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            if target.exists():
                shutil.rmtree(target)
            staging.replace(target)
        except BaseException:
            shutil.rmtree(staging, ignore_errors=True)
            raise
        entries.append(
            {
                "study_id": selection.study_id,
                "viewer": viewer_created,
                "exploitability": float(analysis["summary"]["exploitability"]),
                "run_id": selection.run_id,
            }
        )
        published.append(target)
    _write_index(output_root, entries)
    return published
