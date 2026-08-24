# 実験設定とartifact

## インストール

```bash
python -m pip install -e '.[dev]'
toy-poker list-games
```

## TOML設定

実験は `configs/experiments/*.toml` で定義します。

```toml
[experiment]
name = "akq_allin_cfr_plus"

[game]
id = "akq_allin"

[game.params]
oop_stack = 1.0
ip_stack = 1.0

[solver]
id = "cfr_plus"
iterations = 100000
snapshot_every = 1000

[analysis]
mode = "exact_tree"
off_path_threshold = 1e-8

[output]
artifact_root = "artifacts"
```

| セクション | 主な役割 |
|---|---|
| `experiment` | 人間が識別する実験名 |
| `game` | Registry上のゲームID |
| `game.params` | ゲーム固有パラメータ。詳細は各ゲーム文書を参照 |
| `solver` | solver種別、反復数、収束履歴の保存間隔 |
| `analysis` | 解析方法とoff-path判定閾値 |
| `output` | runの保存先 |

現在の `exact_tree` は有限ゲーム木を完全列挙します。ゲーム木が大きくなった場合の
sampling解析はまだ実装されていません。

## CLI

```bash
# 実験を実行
toy-poker run configs/experiments/akq_allin_cfr_plus.toml

# 保存済み方策から図とHTMLを再生成
toy-poker report artifacts/akq_allin/<run-id>

# 複数runの要約を比較
toy-poker compare artifacts/akq_allin/<run-id-1> artifacts/akq_allin/<run-id-2>
```

## Artifact

```text
artifacts/<game_id>/<run-id>/
├── manifest.json
├── resolved_config.json
├── policy.json
├── policy.csv
├── analysis.json
├── information_sets.csv
├── terminal_paths.csv
├── convergence.csv
├── figures/
└── report.html
```

- `manifest.json`: バージョン、設定ハッシュ、実行時間などの再現情報
- `resolved_config.json`: 実際に使用した全設定
- `policy.*`: solverから独立して復元可能な平均方策
- `analysis.json`: EV、Exploitability、情報集合、終端経路、収束履歴の統合データ
- `information_sets.csv`: 情報集合・合法アクション単位の確率とEV
- `terminal_paths.csv`: 終端履歴の到達確率とutility
- `convergence.csv`: 反復数ごとのEVとExploitability
- `figures/`, `report.html`: 生データから再生成できる表示用成果物

`latest.json` はゲームごとの最新runを指します。artifactはGit管理対象外です。
