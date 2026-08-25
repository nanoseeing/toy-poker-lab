# 公開解析結果

各toyゲームの代表runから、Gitで閲覧しやすいreportと図を抽出したものです。
`integer_range_betting`はinteractive strategy viewerも含みます。

| Game | Report | Viewer | Iterations | Exploitability |
|---|---|---|---:|---:|
| `akq_allin` | [Report](akq_allin/report.md) | — | 100,000 | `3.749967e-11` |
| `akqj_allin` | [Report](akqj_allin/report.md) | — | 100,000 | `6.8038675e-06` |
| `akqj_two_street` | [Report](akqj_two_street/report.md) | — | 100,000 | `3.5914e-06` |
| `integer_range_betting` | [Report](integer_range_betting/report.md) | [Viewer](integer_range_betting/strategy_viewer.html) | 300,000 | `1.6662251e-08` |

各ディレクトリの`summary.json`、`resolved_config.json`、`manifest.json`で計算条件と
source runを確認できます。全policy・analysis・CSVは`artifacts/`にのみ保存します。

再生成:

```bash
toy-poker publish-results --selection configs/public_results.toml \
  --artifact-root artifacts --output-root public/results
```
