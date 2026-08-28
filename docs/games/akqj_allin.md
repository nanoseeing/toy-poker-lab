# AKQJ all-in game

## ルール概要

- Riverの1 streetを抽象化し、追加のpublic cardは配られません。
- OOPは常にK、IPはA・Q・Jを各1/3で持ちます。強さは`A > K > Q > J`です。
- 初期potは1、両者の残りstackはデフォルト4で、OOPから行動します。
- bet sizeはAll-inのみです。bet前はCheckまたはAll-in、All-inに直面したらCallまたはFoldを
  選びます。
- IPのAはKに勝ち、QとJはいずれもKに負けます。利得合計は初期potの1です。

## toyゲームの目的

AKQのvalue/bluff比とbluff-catchの無差別条件を保ったまま、showdown上は完全に同価なQとJの2種類の
bluff候補を用意します。均衡が要求するのはQ/Jの個別頻度ではなく、bluffの合計頻度であることを
数式とsolver結果の両方から確認できます。

これは、ナッシュ均衡の戦略表示が必ずしも一意でないこと、同じEVのハンド間でsolverが異なる混合を
返し得ることを学ぶ題材です。実戦では、個別comboの頻度よりもrange全体のvalue/bluff比と、
同じshowdown valueを持つbluff候補の方策が非一意になり得ることを学べます。

## 公開解析結果

- [Stack 4・10万反復の高精度Report](../../public/results/akqj_allin/report.md)
- [計算条件と要約](../../public/results/akqj_allin/summary.json)

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

初期ポットは常に1で変更できません。この1はデッドマネーとして扱い、利得は
ゲーム開始後に獲得する初期ポットと追加commitの純増減です。

| パラメータ | 型 | デフォルト | 制約 | 意味 |
|---|---|---:|---|---|
| `oop_stack` | float | 4.0 | `> 0` | OOPの残りスタック |
| `ip_stack` | float | 4.0 | `> 0` | IPの残りスタック |

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

| 終了方法 | 勝者利得 | 敗者利得 |
|---|---:|---:|
| Check-checkのshowdown | +1 | 0 |
| All-inにFold | +1 | 0 |
| All-inをCall | \(1+s\) | \(-s\) |

常に利得の合計が初期ポット額の1になる定和ゲームです。従来の中心化した利得へ
各プレイヤー一律に+0.5しただけなので、均衡戦略とExploitabilityは変わりません。

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
EV_{IP}=\frac{1+2s}{3(1+s)},\qquad
EV_{OOP}=\frac{2+s}{3(1+s)}
\]

デフォルトの \(s=4\) では、IP(Q)とIP(J)は対称解で各40% All-in、OOPは20% Call、
IP EVは0.6、OOP EVは0.4です。Qだけ80%でJを0%、またはその逆にする方策も同じ
均衡族に含まれます。

例えば `oop_stack=2`, `ip_stack=3` なら \(s=2\) なので、Q/Jの合計ブラフ率は2/3、
対称解では各1/3、OOPのCall率は1/3、IP EVは5/9、OOP EVは4/9です。

## 設定と実行

標準設定は
[`configs/experiments/akqj_allin_cfr_plus.toml`](../../configs/experiments/akqj_allin_cfr_plus.toml)
です。

```toml
[game]
id = "akqj_allin"

[game.params]
oop_stack = 4.0
ip_stack = 4.0

[solver]
id = "cfr_plus"
backend = "native_efg"
iterations = 10000
snapshot_every = 1000
early_stopping = true
target_exploitability = 1e-5
min_iterations = 1000
patience_checkpoints = 2
```

```bash
toy-poker run configs/experiments/akqj_allin_cfr_plus.toml
```

10,000反復上限の標準runでは、IP(Q/J)はそれぞれ約39.9951% All-in、OOPは約20.0061%
Callとなりました。IP EVは約0.6000000179、OOP EVは約0.3999999821、Exploitabilityは
約`0.0000569292`、計算時間は約0.09秒です。このrunは目標`1e-5`へ届かなかったため、
early stoppingではなく10,000反復上限で終了しました。

出力先は `artifacts/akqj_allin/<run-id>/` です。最新runは
`artifacts/akqj_allin/latest.json` から確認できます。

## 出力の読み方

- Q/Jの個別All-in率ではなく、まず両者の合計が解析条件を満たすか確認します。
- `reach_probability` が小さいoff-path局面は、アクション確率よりAction EVを優先します。
- `exploitability` は非一意な均衡族のどのメンバーへ収束したかに関係なく、方策全体を評価します。
- デフォルトではIPのゲーム価値が0.6、OOPが0.4なので、EVだけで収束を判断せずExploitabilityも確認します。

共通の各列とartifactの説明は[実験設定とartifact](../experiments.md)を参照してください。

## 実装とテスト

- [ゲーム実装](../../src/toy_poker/games/akqj_allin/game.py)
- [表示用メタデータ](../../src/toy_poker/games/akqj_allin/metadata.py)
- [一般スタックでの解析解](../../src/toy_poker/games/akqj_allin/analytic.py)
- [共通All-inゲーム基盤](../../src/toy_poker/games/fixed_oop_allin.py)
- [ゲームルールテスト](../../tests/games/test_akqj_allin.py)
- [解析・CFR+テスト](../../tests/analysis/test_akqj_analysis.py)
