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
backend = "python_game"
iterations = 100000
snapshot_every = 1000

[analysis]
mode = "exact_tree"
off_path_threshold = 1e-8
major_reach_threshold = 1e-4

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

`solver.backend`は次の2種類です。

| backend | 特性 |
|---|---|
| `python_game` | Pythonで実装したゲーム状態をC++ CFR+から直接たどる標準方式 |
| `native_efg` | 最初に全ゲーム木をGambit EFGへ展開し、反復をC++内で実行する高速方式 |

`native_efg`は有限の2人逐次ゲームに使用できます。元ゲームと同じinformation set、
action、chance確率、terminal utilityを持つ木を生成し、求解後の方策を元ゲームのaction IDへ
戻します。ゲーム木全体を事前構築するため、大規模ゲームには適しません。

現在の `exact_tree` は有限ゲーム木を完全列挙します。ゲーム木が大きくなった場合の
sampling解析はまだ実装されていません。

`major_reach_threshold`はHTMLレポート冒頭の主要戦略に残すinformation setとtree nodeの
最小到達確率です。デフォルトの`1e-4`は0.01%を意味します。閾値未満の局面も削除されず、
report後段のfull版と`information_sets.csv`にはすべて残ります。

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

`figures/major_strategy_tree.png`と`major_strategy_probabilities.png`は到達確率で絞った
主要局面版です。`strategy_tree.png`と`strategy_probabilities.png`は全局面版です。

`latest.json` はゲームごとの最新runを指します。artifactはGit管理対象外です。
