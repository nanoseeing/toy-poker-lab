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
backend = "native_efg"
algorithm = "cfr_plus"
iterations = 10000
snapshot_every = 1000
early_stopping = true
target_exploitability = 1e-5
min_iterations = 1000
patience_checkpoints = 2

[analysis]
mode = "exact_tree"
off_path_threshold = 1e-8
major_reach_threshold = 1e-4
report_scope = "full"
policy_format = "json_csv"
interactive_viewer = true
viewer_grid_columns = 10

[output]
artifact_root = "artifacts"
```

| セクション | 主な役割 |
|---|---|
| `experiment` | 人間が識別する実験名 |
| `game` | Registry上のゲームID |
| `game.params` | ゲーム固有パラメータ。詳細は各ゲーム文書を参照 |
| `solver` | solver種別、最大反復数、checkpoint間隔、early stopping条件 |
| `analysis` | 解析方法とoff-path判定閾値 |
| `output` | runの保存先 |

`solver.backend`は実行エンジン、`solver.algorithm`は後悔値更新則です。backendの
選択肢は次の4種類です。

| backend | 特性 |
|---|---|
| `python_game` | Pythonで実装したゲーム状態をC++ CFR+から直接たどる標準方式 |
| `native_efg` | 最初に全ゲーム木をGambit EFGへ展開し、反復をC++内で実行する高速方式 |
| `vectorized_range` | integer 1-Nゲーム専用。range軸をNumPyで一括処理する方式 |
| `cpp_range` | integer 1-Nゲーム専用。public treeを連続配列化し、C++20でrangeを一括処理する高速方式 |

`algorithm="cfr_plus"`はregret matching+、交互更新、線形平均を使います。
`algorithm="dcfr"`は正負の累積regretと平均方策を反復ごとにdiscountします。現在DCFRを
使用できるのは`vectorized_range`と`cpp_range`です。標準指数は
`dcfr_alpha=1.5`、`dcfr_beta=0.0`、`dcfr_gamma=2.0`です。
`cpp_range`では`precision="float64"`（既定）と`precision="float32"`を選べます。
float32はregret・strategyだけに使い、checkpointのEV・Exploitabilityはfloat64で厳密評価します。

`native_efg`は有限の2人逐次ゲームに使用できます。元ゲームと同じinformation set、
action、chance確率、terminal utilityを持つ木を生成し、求解後の方策を元ゲームのaction IDへ
戻します。ゲーム木全体を事前構築するため、大規模ゲームには適しません。

`native_efg`使用時はCFR+の反復だけでなく、各checkpointのExploitabilityとExpected
Returnsも変換後のC++ EFG上で評価します。最終summaryは最後のcheckpoint値を再利用します。
評価経路は`analysis.json`の`solver.checkpoint_evaluation_backend`へ保存されます。
`python_game`を明示した場合だけ、checkpointも元のPythonゲーム上で評価します。
`vectorized_range`ではExpected ReturnsとExploitabilityも専用のベクトル計算で厳密評価します。
`cpp_range`のcheckpointも同じ厳密評価器を使用します。

全標準設定では最大10,000反復、最小1,000反復、Exploitability目標`1e-5`のearly
stoppingを使用します。目標を2 checkpoint連続で満たした時点で停止し、満たさなければ
10,000反復まで実行します。`analysis.json`には`requested_iterations`、
`completed_iterations`、`stop_reason`、最良checkpointも保存されます。

通常の`exact_tree`は有限ゲーム木を完全列挙します。integer 1-Nゲームだけはpublic treeと
rank配列を使う等価な厳密解析を行い、private dealのN²列挙を避けます。

組み込みゲームでは初期ポット1を両プレイヤーの過去の拠出とはみなさず、デッドマネー
として扱います。したがって各terminalのutility合計と、ゲーム開始時点の両者EV合計は
常に1です。この規約は`analysis.json`の`game.utility_convention`と`game.utility_sum`にも
保存されます。

`major_reach_threshold`はHTMLレポート冒頭の主要戦略に残すinformation setとtree nodeの
最小到達確率です。デフォルトの`1e-4`は0.01%を意味します。閾値未満の局面も削除されず、
report後段のfull版と`information_sets.csv`にはすべて残ります。

大規模木では`report_scope="major_only"`を指定すると、巨大なfull図とfull HTML表だけを
省略します。全データは`analysis.json.gz`と`*.csv.gz`へ標準gzip形式で残します。
`policy_format="npz"`は方策を
pickle不使用の圧縮`policy.npz`へ保存し、再描画にも使用できます。

numeric rangeゲームでは`interactive_viewer=true`により、履歴をたどりながら戦略を確認する
自己完結型`strategy_viewer.html`を生成します。`viewer_grid_columns`はprivate numberを並べる
1行あたりのマス数で、デフォルトは10です。viewerはartifact内のデータだけで動作し、
Webサーバーや外部JavaScriptを必要としません。各局面ではrank別strategyに加えて、条件付き
rangeで集約したノード全体のaction頻度、履歴でBayes更新したOOP/IP両range、および相手range
に対するEquity Distributionとrange全体の即時showdown EQを表示します。Equity Distribution
の横軸はEQ順に並べた自分の条件付きrange percentile、縦軸は相手rangeに対するEQです。

## CLI

```bash
# 実験を実行
toy-poker run configs/experiments/akq_allin_cfr_plus.toml

# 保存済み方策から図とHTMLを再生成
toy-poker report artifacts/akq_allin/<run-id>

# 複数runの要約を比較
toy-poker compare artifacts/akq_allin/<run-id-1> artifacts/akq_allin/<run-id-2>

# artifactを生成せずsolverだけを反復測定
toy-poker benchmark configs/experiments/integer_range_betting_dcfr.toml --iterations 1000 --repeat 3
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
├── strategy_viewer.html
└── report.html
```

`report_scope="major_only"`かつ`policy_format="npz"`では、`policy.json/csv`の代わりに
`policy.npz`、大きなJSON/CSVの代わりに`analysis.json.gz`と`*.csv.gz`を保存します。

- `manifest.json`: バージョン、設定ハッシュ、実行時間などの再現情報
- `resolved_config.json`: 実際に使用した全設定
- `policy.*`: solverから独立して復元可能な平均方策
- `analysis.json`: utility規約、EV、Exploitability、情報集合、終端経路、収束履歴の統合データ
- `information_sets.csv`: 情報集合・合法アクション単位の確率とEV
- `terminal_paths.csv`: 終端履歴の到達確率とutility
- `convergence.csv`: 反復数ごとのEVとExploitability
- `figures/`, `report.html`: 生データから再生成できる表示用成果物

`figures/major_strategy_tree.png`と`major_strategy_probabilities.png`は到達確率で絞った
主要局面版です。`strategy_tree.png`と`strategy_probabilities.png`は全局面版です。

`latest.json` はゲームごとの最新runを指します。artifactはGit管理対象外です。
