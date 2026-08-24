# AKQ all-in game

## 概要

1ストリートのヘッズアップポーカーから、カードをA/K/Qの3ランク、ベットをAll-inだけに
限定した有限定和ゲームです。ランクの強さは `A > K > Q` です。

このゲームではOOPがレンジ中央のKを必ず持ち、IPがナッツのAまたはブラフ候補のQを
持ちます。OOPのCheck後にIPがvalue betとbluffをどの比率で混ぜるかを検証できます。

## プレイヤーと情報構造

| OpenSpiel index | 名前 | private card | 行動順 |
|---:|---|---|---|
| 0 | IP | AまたはQを各50% | OOPの後 |
| 1 | OOP | 常にK | 最初 |

- IPだけがA/Qのどちらを配られたか知っています。
- OOPはIPのカードを知りません。
- アクション履歴は両者に公開されます。
- chance nodeでIPへAまたはQを配った後、OOPから開始します。

## ポットとスタック

初期ポットは常に1で、設定からは変更できません。この1は両者の現在の拠出ではない
デッドマネーとして扱います。utilityはゲーム開始時点以降に得る初期ポットと、追加で
commitするチップの純増減です。

| パラメータ | 型 | デフォルト | 制約 | 意味 |
|---|---|---:|---|---|
| `oop_stack` | float | 1.0 | `> 0` | OOPの残りスタック |
| `ip_stack` | float | 1.0 | `> 0` | IPの残りスタック |

実効スタックを次で定義します。

\[
s=\min(\text{oop\_stack},\text{ip\_stack})
\]

スタックが異なる場合、相手がカバーできないAll-inの超過分は返却されます。そのため
戦略とペイオフに影響するAll-in額は実効スタック \(s\) です。

## ゲーム進行と合法アクション

1. IPへAまたはQを各50%で配る。
2. OOP(K)が `Check` または `All-in` を選ぶ。
3. OOPがAll-inした場合、IPは `Call` または `Fold` を選んで終了する。
4. OOPがCheckした場合、IPは `Check` または `All-in` を選ぶ。
5. IPがCheckした場合はshowdown。IPがAll-inした場合、OOPが `Call` または `Fold` を選ぶ。

OpenSpiel内部では、ベットされていない状態の `ALL_IN` はAll-in、All-inに直面した状態の
`ALL_IN` はCallを意味します。FoldはAll-inに直面したときだけ合法です。

## Showdownとペイオフ

- IPがAならIPの勝ち。
- IPがQならOOPのKが勝ち。

| 終了方法 | 勝者utility | 敗者utility |
|---|---:|---:|
| Check-checkのshowdown | +1 | 0 |
| All-inにFold | +1 | 0 |
| All-inをCall | \(1+s\) | \(-s\) |

常に2人のutility合計が初期ポット額の1になる定和ゲームです。以前の「初期ポットを
0.5ずつ拠出済み」とする表現からは、全プレイヤー・全終端のutilityへ一律に+0.5した
ものです。この平行移動はアクション間のEV差を変えないため、均衡戦略とExploitabilityは
変わりません。

## 解析解

\(s>0\) のとき、均衡戦略は次のとおりです。

| 情報集合 | 均衡戦略 |
|---|---|
| OOP(K)、初手 | Check 100% |
| IP(A)、OOPのCheck後 | All-in 100% |
| IP(Q)、OOPのCheck後 | All-in \(s/(1+s)\)、Check \(1/(1+s)\) |
| OOP(K)、IPのAll-inに直面 | Call \(1/(1+s)\)、Fold \(s/(1+s)\) |
| IP(A)、OOPのAll-inに直面 | Call 100% |
| IP(Q)、OOPのAll-inに直面 | Fold 100% |

最後の2局面は、均衡ではOOPが初手All-inしないためoff-pathです。

ゲーム価値は次のとおりです。

\[
EV_{IP}=\frac{1+2s}{2(1+s)},\qquad
EV_{OOP}=\frac{1}{2(1+s)}
\]

デフォルトの \(s=1\) では、IP(Q)のbluff率とOOPのCall率がともに50%、
`IP EV = 0.75`、`OOP EV = 0.25` です。

例えば `oop_stack=2`, `ip_stack=3` なら \(s=2\) なので、IP(Q)のbluff率は
2/3、OOPのCall率は1/3、IP EVは5/6、OOP EVは1/6になります。

## 設定と実行

標準設定は
[`configs/experiments/akq_allin_cfr_plus.toml`](../../configs/experiments/akq_allin_cfr_plus.toml)
です。

```toml
[game]
id = "akq_allin"

[game.params]
oop_stack = 1.0
ip_stack = 1.0
```

```bash
toy-poker run configs/experiments/akq_allin_cfr_plus.toml
```

出力先は `artifacts/akq_allin/<run-id>/` です。最新runは
`artifacts/akq_allin/latest.json` から確認できます。

## 出力の読み方

- `reach_probability`: 平均方策のもとで情報集合へ到達する確率
- `policy_ev`: 到達したという条件のもとで現在の混合方策を使ったEV
- `action_ev`: そのアクションを固定し、以降は平均方策を使ったEV
- `exploitability`: 方策全体のナッシュ均衡からのずれ
- `is_off_path`: 到達確率が設定した閾値未満の情報集合

off-pathのアクション確率はExploitabilityへほとんど寄与せず、CFR+での収束が遅い場合が
あります。その場合は確率だけでなく、`action_ev` と `reach_probability` も確認します。

## 実装とテスト

- [ゲーム実装](../../src/toy_poker/games/akq_allin/game.py)
- [表示用メタデータ](../../src/toy_poker/games/akq_allin/metadata.py)
- [一般スタックでの解析解](../../src/toy_poker/games/akq_allin/analytic.py)
- [ゲームルールテスト](../../tests/games/test_akq_allin.py)
- [解析解テスト](../../tests/analysis/test_akq_analysis.py)
- [CFR+収束テスト](../../tests/solvers/test_cfr_plus.py)
