# AKQJ two-street geometric game

## ルール概要

- River相当の情報を持ったまま2 betting streetをプレイし、street間でpublic cardは増えません。
- OOPは常にK、IPはA・Q・Jを各1/3で持ちます。強さは`A > K > Q > J`です。
- 初期potは1、両者の残りstackはデフォルト1で、各streetはOOPから始まります。
- betされていなければCheck、Geometric bet、All-inが可能です。Geometric betにはFold、Call、
  All-in raiseで応じます。
- 1st streetがCheck-checkまたはbet-callなら2nd streetへ進み、2nd streetの同様の終了やAll-in-callで
  showdownになります。Foldなら即終了します。

## toyゲームの目的

ハンドの強さやboardを変化させず、betting streetを増やすこと自体が戦略に与える影響を切り分けて学ぶための
ゲームです。同じ最終All-in額でも、bluffを1st streetと2nd streetのどちらに配分するか、valueをすぐ
betするかtrapするか、将来のAll-in脅威が現在のCallにどう影響するかを検証できます。

Geometric betは、残りstreetで同じpot比率を使ってstackをちょうど使い切る実戦的なサイズ設計を学ぶ題材です。
range更新、複数streetのequity realization、ディレイしたbluff/value、All-in raiseへの防御を観察できます。

## 公開解析結果

- [Stack 4・10万反復の高精度Report](../../public/results/akqj_two_street/report.md)
- [計算条件と要約](../../public/results/akqj_two_street/summary.json)

## プレイヤーと情報構造

| OpenSpiel index | 名前 | private card | 行動順 |
|---:|---|---|---|
| 0 | IP | A、Q、Jを各1/3 | 各streetでOOPの後 |
| 1 | OOP | 常にK | 各streetの最初 |

- IPだけがA/Q/Jのどれを配られたか知っています。
- OOPはIPのカードを知りません。
- street、pot、commit額、全アクション履歴は公開情報です。
- 同じカードを持ったまま2 streetをプレイします。

## ポット、スタック、Geometric bet

初期potは1で固定です。この1は両者の現在の拠出ではないデッドマネーとして扱います。
利得はゲーム開始後に得る初期potと追加commitの純増減で表します。

| パラメータ | 型 | デフォルト | 制約 | 意味 |
|---|---|---:|---|---|
| `oop_stack` | float | 1.0 | `> 0` | OOPの残りスタック |
| `ip_stack` | float | 1.0 | `> 0` | IPの残りスタック |

実効スタックは次のとおりです。

\[
S=\min(\text{oop\_stack},\text{ip\_stack})
\]

Geometric betのpot比率 \(e\) は次の式で計算します。

\[
e=\frac{-1+\sqrt{1+2S}}{2}
\]

初期pot 1に対する1st streetのbet額は \(b_1=e\)、call後のpotは \(1+2e\)、
2nd streetのbet額は \(b_2=e(1+2e)\) です。

\[
b_1+b_2=e+e(1+2e)=2e+2e^2=S
\]

したがって、両streetで同じpot比率をbetしてcallされると、2nd streetでちょうど
All-inになります。例えば \(S=1\) では \(e\simeq0.366025\)、bet額は順に
約0.366025と0.633975です。

## ゲーム進行と合法アクション

各streetはOOPから始まります。

| 現在の状態 | 合法アクション |
|---|---|
| betされていない | `Check`、`Geometric bet`、`All-in` |
| Geometric betに直面 | `Raise all-in`、`Call`、`Fold` |
| All-inまたはRaise all-inに直面 | `Call`、`Fold` |

- 1st streetのCheck-checkまたはGeometric bet-call後は2nd streetへ進みます。
- 2nd streetのCheck-checkまたはGeometric bet-call後はshowdownです。
- All-inがCallされた場合はstreetに関係なくshowdownです。
- Foldされた場合は直ちに終了します。
- Geometric bet額と残りスタックが一致する局面では、同値な選択肢を重複させず
  `All-in`だけを表示します。

## Showdownとペイオフ

- IPがAならIPの勝ちです。
- IPがQまたはJならOOPのKが勝ちです。
- showdownで両者が追加で \(c\) ずつcommitしていれば、勝者利得は
  \(1+c\)、敗者利得は \(-c\) です。
- Foldしたプレイヤーが追加で \(c_f\) をcommitしていれば、そのプレイヤーの利得は
  \(-c_f\)、勝者は \(1+c_f\) です。相手の未call分は返却されます。
- 利得の合計はすべての終端で初期pot額の1です。

これは従来の中心化した利得へ両プレイヤーとも一律に+0.5した規約です。そのため、
戦略確率、アクション間のEV差、Exploitabilityは変わらず、各Player EVとAction EVの
絶対値だけが+0.5されます。

## 解析方法

この2 street版には、現時点では閉形式の均衡戦略・ゲーム価値を設定していません。
OpenSpielのC++ `CFRPlusSolver`で数値的に解き、次の値で収束を判断します。

- Exploitability
- NashConv
- 各プレイヤーのEV
- 各information setのaction確率とAction EV
- 反復数に対するExploitabilityの推移

## 設定と実行

標準設定は
[`configs/experiments/akqj_two_street_cfr_plus.toml`](../../configs/experiments/akqj_two_street_cfr_plus.toml)
です。

```toml
[game]
id = "akqj_two_street"

[game.params]
oop_stack = 1.0
ip_stack = 1.0

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
toy-poker run configs/experiments/akqj_two_street_cfr_plus.toml
```

両者のスタックを4にする設定は
[`configs/experiments/akqj_two_street_stack_4_cfr_plus.toml`](../../configs/experiments/akqj_two_street_stack_4_cfr_plus.toml)
です。

```bash
toy-poker run configs/experiments/akqj_two_street_stack_4_cfr_plus.toml
```

出力先は `artifacts/akqj_two_street/<run-id>/` です。HTMLレポートとJSON/CSVには、
各information setのstreet、pot、IP/OOPのcommit額も保存されます。

## 標準設定の参考結果

両者のスタックを1、CFR+を最大10,000反復とした結果は次のとおりです。数値はCFR+による
均衡近似であり、丸め前の完全な値はartifactに保存されます。

| information set | 主な戦略 |
|---|---|
| OOP(K)、1st street最初 | Check 約100% |
| IP(A)、OOPのCheck後 | Geometric bet 約100% |
| IP(Q/J)、OOPのCheck後 | 各カードでCheck 約69.5995%、Geometric bet 約30.4005% |
| OOP(K)、IPの1st Geometric betに直面 | Call 約73.2043%、Fold 約26.7957% |
| 1st Geometric bet-call後のOOP(K) | 2nd streetでCheck 約100% |
| 同じ経路のIP(A) | All-in 約100% |
| 同じ経路のIP(Q/J) | 各カードでCheck 約55.9180%、All-in 約44.0820% |
| OOP(K)、上記2nd street All-inに直面 | Call 約73.2071%、Fold 約26.7929% |

1st streetがCheck-checkだった経路では、OOPは2nd streetで約12.1407% Geometric betし、
IPのQ/Jはそれにほぼ常にFoldしました。

| 指標 | 結果 |
|---|---:|
| IP EV | 0.5358985237 |
| OOP EV | 0.4641014763 |
| Exploitability | 0.0000315688 |
| NashConv | 0.0000631376 |
| 計算時間 | 約0.56秒 |

`native_efg` backendでは、Pythonゲーム木を最初にGambit EFGへ展開し、CFR+の反復を
OpenSpielのC++内で完結させます。現在は全標準設定で最大10,000反復の`native_efg`を
使用します。同じ環境での今回の実行時間は次のとおりです。

| stack | iteration | 計算時間 |
|---:|---:|---:|
| 1 | 10,000 | 約0.56秒 |
| 4 | 10,000 | 約0.50秒 |

計算時間は実行環境によって変わります。

## Stack 4の参考結果

両者のスタックを4にすると、Geometric betのpot比率はちょうど1になります。

\[
e=\frac{-1+\sqrt{1+2\times4}}{2}=1
\]

1st streetではpot 1へ1をbetし、call後のpot 3へ2nd streetで残り3をAll-inします。
両方がcallされると最終potは9、showdownの利得は勝者`+5`、敗者`-4`です。

10,000反復の主要戦略は次のとおりです。

| information set | 主な戦略 |
|---|---|
| OOP(K)、1st street最初 | Check 約100% |
| IP(A)、OOPのCheck後 | Geometric bet 約100% |
| IP(Q/J)、OOPのCheck後 | 各カードでCheck 約37.4917%、Geometric bet 約62.5083% |
| OOP(K)、IPの1st Geometric betに直面 | Call 約49.9955%、Fold 約50.0045% |
| 1st Geometric bet-call後のOOP(K) | 2nd streetでCheck 約100% |
| 同じ経路のIP(A) | All-in 100% |
| 同じ経路のIP(Q/J) | 各カードでCheck 約60.0057%、All-in 約39.9943% |
| OOP(K)、上記2nd street All-inに直面 | Call 約50.0008%、Fold 約49.9992% |

| 指標 | 結果 |
|---|---:|
| IP EV | 0.7499998240 |
| OOP EV | 0.2500001760 |
| Exploitability | 0.0000437285 |
| NashConv | 0.0000874571 |
| 計算時間 | 約0.50秒 |

stack 1・4とも目標`1e-5`へ届かなかったため、10,000反復上限で終了しました。

## 出力の読み方

- 同じプレイヤーとカードでも、streetとそれまでの履歴が異なれば別information setです。
- reportの冒頭には到達確率0.01%以上の主要tree、action probabilities、information set表を
  表示し、後段に低到達確率局面を含むfull版を表示します。
- 低い確率でしか到達しない局面では、戦略確率に加えてAction EVも確認します。
- 閉形式の比較対象がないため、EVだけでなくExploitabilityを主要な収束指標とします。
- QとJはshowdown上同じ強さなので、対称な局面での個別戦略は非一意になる場合があります。

## 実装とテスト

- [ゲーム実装](../../src/toy_poker/games/akqj_two_street/game.py)
- [2 street共通状態機械](../../src/toy_poker/games/fixed_oop_two_street.py)
- [表示用メタデータ](../../src/toy_poker/games/akqj_two_street/metadata.py)
- [ゲームルールテスト](../../tests/games/test_akqj_two_street.py)
- [解析・CFR+テスト](../../tests/analysis/test_akqj_two_street_analysis.py)
