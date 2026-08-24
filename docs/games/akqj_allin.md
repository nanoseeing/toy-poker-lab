# AKQJ all-in game

## 概要

AKQ all-inゲームにJを加え、IPがA/Q/Jのいずれかを持つ有限ゼロサムゲームです。
ランクの強さは `A > K > Q > J` です。

OOPは常にKを持ち、IPのAには負け、QとJには勝ちます。QとJはshowdown valueが同じ
ため、2種類のブラフ候補の間で頻度をどう配分するかが非一意になる点を検証できます。

## プレイヤーと情報構造

| OpenSpiel index | 名前 | private card | 行動順 |
|---:|---|---|---|
| 0 | IP | A、Q、Jを各1/3 | OOPの後 |
| 1 | OOP | 常にK | 最初 |

- IPだけがA/Q/Jのどれを配られたか知っています。
- OOPはIPのカードを知りません。
- アクション履歴は両者に公開されます。
- chance nodeでIPへカードを配った後、OOPから開始します。

## ポットとスタック

初期ポットは常に1で変更できません。utilityは初期ポットを両者が0.5ずつ拠出したと
考えた純利益です。

| パラメータ | 型 | デフォルト | 制約 | 意味 |
|---|---|---:|---|---|
| `oop_stack` | float | 1.0 | `> 0` | OOPの残りスタック |
| `ip_stack` | float | 1.0 | `> 0` | IPの残りスタック |

実効スタックは次のとおりです。

\[
s=\min(\text{oop\_stack},\text{ip\_stack})
\]

相手がカバーできないAll-inの超過分は返却され、戦略とペイオフには実効スタックだけが
影響します。

## ゲーム進行と合法アクション

1. IPへA、Q、Jを各1/3で配る。
2. OOP(K)が `Check` または `All-in` を選ぶ。
3. OOPがAll-inした場合、IPは `Call` または `Fold` を選んで終了する。
4. OOPがCheckした場合、IPは `Check` または `All-in` を選ぶ。
5. IPがCheckした場合はshowdown。IPがAll-inした場合、OOPが `Call` または `Fold` を選ぶ。

OpenSpiel内部では、ベットされていない状態の `ALL_IN` はAll-in、All-inに直面した状態の
`ALL_IN` はCallです。FoldはAll-inに直面したときだけ合法です。

## Showdownとペイオフ

- IPがAならIPの勝ち。
- IPがQまたはJならOOPのKが勝ち。

| 終了方法 | 勝者utility | 敗者utility |
|---|---:|---:|
| Check-checkのshowdown | +0.5 | -0.5 |
| All-inにFold | +0.5 | -0.5 |
| All-inをCall | \(+(0.5+s)\) | \(-(0.5+s)\) |

常にutilityの合計が0になるゼロサムゲームです。

## 解析解

IP(Q)とIP(J)のAll-in率をそれぞれ \(b_Q,b_J\)、OOPのCall率を \(c\) とすると、
\(s>0\) における均衡条件は次のとおりです。

\[
b_Q+b_J=\frac{s}{1+s},\qquad c=\frac{1}{1+s}
\]

| 情報集合 | 均衡戦略 |
|---|---|
| OOP(K)、初手 | Check 100% |
| IP(A)、OOPのCheck後 | All-in 100% |
| IP(Q/J)、OOPのCheck後 | 合計All-in率が \(s/(1+s)\) になるよう配分 |
| OOP(K)、IPのAll-inに直面 | Call \(1/(1+s)\)、Fold \(s/(1+s)\) |
| IP(A)、OOPのAll-inに直面 | Call 100% |
| IP(Q/J)、OOPのAll-inに直面 | Fold 100% |

QとJはOOPのKに対して同じ強さなので、個別のブラフ配分は非一意です。解析基準と
して使う対称解では、次のように均等配分します。

\[
b_Q=b_J=\frac{s}{2(1+s)}
\]

ゲーム価値は次のとおりです。

\[
EV_{IP}=\frac{s-1}{6(1+s)},\qquad
EV_{OOP}=\frac{1-s}{6(1+s)}
\]

デフォルトの \(s=1\) では、IP(Q)とIP(J)は対称解で各25% All-in、OOPは50% Call、
両者のEVは0です。Qだけ50%でJを0%、またはその逆にする方策も同じ均衡族に含まれます。

例えば `oop_stack=2`, `ip_stack=3` なら \(s=2\) なので、Q/Jの合計ブラフ率は2/3、
対称解では各1/3、OOPのCall率は1/3、IP EVは1/18です。

## 設定と実行

標準設定は
[`configs/experiments/akqj_allin_cfr_plus.toml`](../../configs/experiments/akqj_allin_cfr_plus.toml)
です。

```toml
[game]
id = "akqj_allin"

[game.params]
oop_stack = 1.0
ip_stack = 1.0
```

```bash
toy-poker run configs/experiments/akqj_allin_cfr_plus.toml
```

出力先は `artifacts/akqj_allin/<run-id>/` です。最新runは
`artifacts/akqj_allin/latest.json` から確認できます。

## 出力の読み方

- Q/Jの個別All-in率ではなく、まず両者の合計が解析条件を満たすか確認します。
- `reach_probability` が小さいoff-path局面は、アクション確率よりAction EVを優先します。
- `exploitability` は非一意な均衡族のどのメンバーへ収束したかに関係なく、方策全体を評価します。
- デフォルトではゲーム価値が0なので、EVの符号だけで収束を判断せずExploitabilityも確認します。

共通の各列とartifactの説明は[実験設定とartifact](../experiments.md)を参照してください。

## 実装とテスト

- [ゲーム実装](../../src/toy_poker/games/akqj_allin/game.py)
- [表示用メタデータ](../../src/toy_poker/games/akqj_allin/metadata.py)
- [一般スタックでの解析解](../../src/toy_poker/games/akqj_allin/analytic.py)
- [共通All-inゲーム基盤](../../src/toy_poker/games/fixed_oop_allin.py)
- [ゲームルールテスト](../../tests/games/test_akqj_allin.py)
- [解析・CFR+テスト](../../tests/analysis/test_akqj_analysis.py)
