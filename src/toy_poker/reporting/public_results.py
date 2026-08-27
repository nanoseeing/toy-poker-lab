"""Publish lightweight, browsable copies of representative experiment results."""

from __future__ import annotations

import gzip
import html
import json
import shutil
import tempfile
import tomllib
from collections.abc import Mapping
from pathlib import Path

from toy_poker.games import get_game
from toy_poker.reporting.html import save_html
from toy_poker.reporting.markdown import save_markdown


def _load_analysis(run_directory: Path) -> dict:
    compressed = run_directory / "analysis.json.gz"
    if compressed.exists():
        with gzip.open(compressed, "rt", encoding="utf-8") as handle:
            return json.load(handle)
    return json.loads((run_directory / "analysis.json").read_text(encoding="utf-8"))


def _representative_run(
    artifact_root: Path,
    game_id: str,
    selected_run_id: str | None,
) -> tuple[str, Path]:
    if selected_run_id is None:
        pointer_path = artifact_root / game_id / "latest.json"
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
        run_id = str(pointer["run_id"])
    else:
        run_id = selected_run_id
    run_directory = artifact_root / game_id / run_id
    if not run_directory.is_dir():
        raise FileNotFoundError(f"Representative artifact does not exist: {run_directory}")
    return run_id, run_directory


def load_result_selection(path: Path) -> dict[str, str]:
    """Load the reproducible game-to-run mapping used for public results."""
    with path.open("rb") as handle:
        document = tomllib.load(handle)
    games = document.get("games")
    if not isinstance(games, dict) or not games:
        raise ValueError(f"Public result selection has no [games] entries: {path}")
    if not all(isinstance(key, str) and isinstance(value, str) for key, value in games.items()):
        raise ValueError(f"Public result selection must map game IDs to run IDs: {path}")
    return dict(games)


def _summary_document(
    analysis: dict,
    manifest: dict,
    run_id: str,
    viewer_created: bool,
) -> dict:
    return {
        "schema_version": 1,
        "game": {
            "id": analysis["game"]["id"],
            "title": analysis["game"]["title"],
            "parameters": analysis["game"].get("parameters", {}),
            "utility_sum": analysis["game"].get("utility_sum"),
        },
        "source": {
            "run_id": run_id,
            "config_sha256": manifest.get("config_sha256"),
            "git_commit": manifest.get("git_commit"),
        },
        "solver": analysis["solver"],
        "summary": analysis["summary"],
        "files": {
            "report": "report.md",
            "html_report": "report.html",
            "strategy_viewer": "strategy_viewer.html" if viewer_created else None,
        },
    }


def _write_index(output_root: Path, entries: list[dict]) -> None:
    rows = []
    markdown_rows = []
    for entry in entries:
        game_id = entry["game_id"]
        viewer_link = (
            f'<a href="{html.escape(game_id)}/strategy_viewer.html">Viewer</a>'
            if entry["viewer"]
            else "—"
        )
        rows.append(
            "<tr>"
            f"<td>{html.escape(entry['title'])}</td>"
            f"<td><a href=\"{html.escape(game_id)}/report.md\">Report</a></td>"
            f"<td>{viewer_link}</td>"
            f"<td>{entry['iterations']:,}</td>"
            f"<td>{entry['exploitability']:.8g}</td>"
            f"<td><code>{html.escape(entry['run_id'])}</code></td>"
            "</tr>"
        )
        viewer_markdown = (
            f"[Viewer]({game_id}/strategy_viewer.html)" if entry["viewer"] else "—"
        )
        markdown_rows.append(
            f"| `{game_id}` | [Report]({game_id}/report.md) | {viewer_markdown} | "
            f"{entry['iterations']:,} | `{entry['exploitability']:.8g}` |"
        )

    document = """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Toy poker public results</title><style>
body{font-family:system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#17212b}
table{border-collapse:collapse;width:100%}th,td{border-bottom:1px solid #d9dee7;padding:.7rem;text-align:left}
th{background:#f4f7fa}code{font-size:.85em}a{color:#315efb}
</style></head><body><h1>Toy poker public results</h1>
<p>各ゲームの代表的な計算結果です。生のpolicy・全analysis・CSVは容量を抑えるため含めていません。</p>
<table><thead><tr><th>Game</th><th>Report</th><th>Viewer</th><th>Iterations</th>
<th>Exploitability</th><th>Source run</th></tr></thead><tbody>"""
    document += "".join(rows)
    document += "</tbody></table></body></html>"
    (output_root / "index.html").write_text(document, encoding="utf-8")

    readme = """# 公開解析結果

各toyゲームの代表runから、Gitで閲覧しやすいreportと図を抽出したものです。
numeric range gameはinteractive strategy viewerも含みます。

| Game | Report | Viewer | Iterations | Exploitability |
|---|---|---|---:|---:|
""" + "\n".join(markdown_rows)
    readme += """

各ディレクトリの`summary.json`、`resolved_config.json`、`manifest.json`で計算条件と
source runを確認できます。全policy・analysis・CSVは`artifacts/`にのみ保存します。

再生成:

```bash
toy-poker publish-results --selection configs/public_results.toml \\
  --artifact-root artifacts --output-root public/results
```
"""
    (output_root / "README.md").write_text(readme, encoding="utf-8")


def publish_results(
    artifact_root: Path,
    output_root: Path,
    selections: Mapping[str, str] | None = None,
) -> list[Path]:
    """Publish pinned runs, or each game's latest run when no mapping is given."""
    if selections is None:
        selected = [
            (path.name, None)
            for path in sorted(artifact_root.iterdir())
            if path.is_dir() and (path / "latest.json").exists()
        ]
    else:
        selected = sorted(selections.items())
    if not selected:
        raise ValueError("No games were selected for publication")

    output_root.mkdir(parents=True, exist_ok=True)
    published = []
    entries = []
    for game_id, selected_run_id in selected:
        run_id, source = _representative_run(
            artifact_root, game_id, selected_run_id
        )
        analysis = _load_analysis(source)
        plugin = get_game(game_id)
        manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
        target = output_root / game_id
        staging = Path(tempfile.mkdtemp(prefix=f".{game_id}-", dir=output_root))
        try:
            figures = source / "figures"
            if figures.is_dir():
                shutil.copytree(figures, staging / "figures")
            viewer_created = (source / "strategy_viewer.html").exists()
            if viewer_created:
                shutil.copy2(
                    source / "strategy_viewer.html",
                    staging / "strategy_viewer.html",
                )
            for name in ("resolved_config.json", "manifest.json"):
                shutil.copy2(source / name, staging / name)
            save_html(
                staging / "report.html",
                analysis,
                plugin,
                tree_created=(figures / "strategy_tree.png").exists(),
                major_tree_created=(figures / "major_strategy_tree.png").exists(),
                viewer_created=viewer_created,
                include_data_links=False,
            )
            save_markdown(
                staging / "report.md",
                analysis,
                plugin,
                tree_created=(figures / "strategy_tree.png").exists(),
                major_tree_created=(figures / "major_strategy_tree.png").exists(),
                viewer_created=viewer_created,
                public_bundle=True,
            )
            summary = _summary_document(analysis, manifest, run_id, viewer_created)
            (staging / "summary.json").write_text(
                json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            if target.exists():
                shutil.rmtree(target)
            staging.replace(target)
        except BaseException:
            shutil.rmtree(staging, ignore_errors=True)
            raise

        solver = analysis["solver"]
        entries.append(
            {
                "game_id": game_id,
                "title": analysis["game"]["title"],
                "viewer": viewer_created,
                "iterations": int(
                    solver.get("completed_iterations", solver.get("iterations", 0))
                ),
                "exploitability": float(analysis["summary"]["exploitability"]),
                "run_id": run_id,
            }
        )
        published.append(target)

    _write_index(output_root, entries)
    return published
