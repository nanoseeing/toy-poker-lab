# Integer 1-N weighted-range custom-size game

## 概要

OOPとIPへ1〜Nの整数をそれぞれ独立な重み付き確率で配り、1 streetでpot比率のbetと
raiseを繰り返せる有限定和ゲームです。数字が大きい方がshowdownで勝ち、同じ数字はtieです。

初期potはデッドマネーの1、両者のstackはデフォルト4です。標準サイズとして33%と
100% potのbet/raise、およびAll-inを使用します。通常のno-limitと同じminimum raise
制約を適用します。

## プレイヤーと情報構造

| OpenSpiel index | 名前 | private number | 行動順 |
|---:|---|---|---|
| 0 | IP | 1〜N、IP固有の重み付き分布 | OOPの後 |
| 1 | OOP | 1〜N、OOP固有の重み付き分布 | 最初 |

OOPの正規化済み確率を`p_oop(i)`、IPを`p_ip(j)`とすると、deal確率は
`p_oop(i) * p_ip(j)`です。各プレイヤーは自分の数字、公開action履歴、pot、commit額を
知りますが、相手の数字は知りません。

## パラメータ

| 名前 | 型 | デフォルト | 制約 | 意味 |
|---|---|---:|---|---|
| `oop_stack` | float | 4.0 | `> 0` | OOPの残りstack |
| `ip_stack` | float | 4.0 | `> 0` | IPの残りstack |
| `bet_fractions` | string | `"0.3333333333333333,1.0"` | 正数、有限、重複なし | 使用できるpot比率 |
| `num_ranks` | int | 10 | `>= 2` | private numberの最大値N |
| `oop_rank_weights` | string | `"uniform"` | N個の有限な正数 | OOPの相対重み |
| `ip_rank_weights` | string | `"uniform"` | N個の有限な正数 | IPの相対重み |

`bet_fractions`はOpenSpielのparameterとして渡せるよう、カンマ区切り文字列で指定します。
読み込み時に数値へ変換し、昇順に正規化します。標準の1/3は表示上`33%`とします。

range重みもカンマ区切りで指定し、それぞれ合計1へ正規化します。合計を1に揃えて入力する
必要はありません。例えば次はOOPとIPで異なる3-rank rangeです。

```toml
num_ranks = 3
oop_rank_weights = "1,2,7"
ip_rank_weights = "6,3,1"
```

この場合、OOPの確率は`[0.1, 0.2, 0.7]`、IPは`[0.6, 0.3, 0.1]`になります。

実効stackは次のとおりです。

\[
S=\min(\text{oop\_stack},\text{ip\_stack})
\]

heads-upでは相手がcoverできない超過分を返却できるため、commit額を実効stackまでに
制限します。

## ゲーム進行と合法アクション

1. OOPとIPへ数字をdealする。
2. OOPから1 streetのbettingを開始する。
3. Check-check、Call、Foldのいずれかで終了する。
4. CallまたはCheck-checkならshowdownする。

| 状況 | 合法アクション |
|---|---|
| betされていない | `Check`、各`Bet x%`、`All-in` |
| 通常bet/raiseに直面 | `Fold`、`Call`、合法な各`Raise x%`、`Raise all-in` |
| All-inに直面 | `Fold`、`Call` |

計算したカスタムサイズが残りstack以上なら同値actionを重複させず、`All-in`だけを
表示します。

## Bet・Raiseサイズ

未bet時のfraction \(x\) によるbet額は、action前のpotを \(P\) として次のとおりです。

\[
\text{bet}=xP
\]

raise時は、現在のcall必要額を \(C\)、相手のbetを含む現在potを \(P_{current}\) とします。

\[
P_{after\ call}=P_{current}+C
\]

\[
\text{chips added}=C+xP_{after\ call}
\]

相手のbet前のpotを \(P\)、相手のbet額を \(B\) と置けば、\(C=B\)、
\(P_{current}=P+B\)なので、同じ式は次の形になります。

\[
B+x(P+2B)
\]

## Minimum raise

カスタムraiseによるwager levelの増額は、直前のfull bet/raiseによる増額以上でなければ
なりません。これを満たさないカスタムraiseは非合法です。

stack上限によるAll-inだけはminimum未満のshort raiseを許可します。heads-upで相手は
その後`Call`または`Fold`するため、reopen判定は必要ありません。

例として初期pot 1へpot-sizeの1をbetされた場合、1/3 pot raiseは次の額になります。

\[
1+\frac{1}{3}(1+2)=2
\]

raise incrementは1で直前のbet increment 1と等しいため、minimum raiseを満たします。

## Showdownとutility

両者が追加で \(c\) ずつcommitしている場合は次のとおりです。

| 結果 | IP utility | OOP utility |
|---|---:|---:|
| IPの数字が大きい | \(1+c\) | \(-c\) |
| OOPの数字が大きい | \(-c\) | \(1+c\) |
| tie | 0.5 | 0.5 |

Fold側が \(c_f\) commitしている場合、Fold側は \(-c_f\)、勝者は \(1+c_f\) です。
すべてのterminalでutility合計は初期pot額の1になります。

## 設定と実行

標準設定は
[`configs/experiments/integer_range_betting_dcfr.toml`](../../configs/experiments/integer_range_betting_dcfr.toml)
です。

```toml
[game]
id = "integer_range_betting"

[game.params]
oop_stack = 4.0
ip_stack = 4.0
bet_fractions = "0.3333333333333333,1.0"
num_ranks = 10
oop_rank_weights = "uniform"
ip_rank_weights = "uniform"

[solver]
id = "cfr_plus"
backend = "cpp_range"
algorithm = "dcfr"
dcfr_alpha = 1.5
dcfr_beta = 0.0
dcfr_gamma = 2.0
iterations = 10000
snapshot_every = 1000
early_stopping = true
target_exploitability = 1e-5
min_iterations = 1000
patience_checkpoints = 2
```

```bash
toy-poker run configs/experiments/integer_range_betting_dcfr.toml
```

## 標準設定の参考結果

stack 4、N=10の一様range、標準サイズ、`cpp_range` DCFRをearly stopping付きで
実行した結果は次のとおりです。

| 指標 | 結果 |
|---|---:|
| 完了iteration | 5,000 / 10,000 |
| IP EV | 0.5320656292 |
| OOP EV | 0.4679343708 |
| Exploitability | 0.00000537082 |
| NashConv | 0.0000107416 |
| solver計算時間 | 約0.14秒 |

4,000・5,000反復の2 checkpointで目標`1e-5`を連続して下回り、5,000反復で停止しました。
主要なrange構造は次のようになりました。

- OOPは2〜6をほぼ常にCheckし、7〜8をほぼ常に33% Betしました。
- OOPの1は33%・100% Betを混ぜたbluff、9〜10はCheckとvalue betを混ぜました。
- OOPのCheck後、IPは3〜6をほぼ常にCheckしました。
- IPの8〜10は主にvalue bet、1は主に100% Betのbluff、2はCheckとbluffを混ぜました。

数値は反復solverによる均衡近似です。個々の低到達確率局面や非一意な混合は、HTMLの
reach probability、Action EV、Exploitabilityと併せて解釈してください。

## 解析と出力

閉形式の均衡解は設定していません。CFR+のExploitability、NashConv、Player EV、
information setごとのAction EVで収束を確認します。

数字1〜Nを比較しやすくするため、strategyとAction EVは、private numberを列、actionを
行、公開履歴をパネルとするヒートマップで出力します。HTML後段のfull information set表と
CSVには低到達確率局面を含む全データを残します。private dealは、action treeとterminal
paths上では到達確率で重み付けした1本のpublic treeへ集約します。正規化後の両rangeは
`rank_distribution.csv`とレポートの分布図にも保存します。

`vectorized_range` backendはpublic betting treeを1本だけ保持し、rank別のregret、strategy、
reachをNumPy配列で更新します。showdown EV、Expected Returns、best response、
Exploitabilityはrank順序の累積和で厳密に計算するため、N²個のdealを列挙しません。
`native_efg`も正しさを比較する基準backendとして引き続き利用できます。

標準の`cpp_range` backendは同じpublic treeをCSR風の連続配列へ変換し、CFR+/DCFRの
tree traversalをC++20で実行します。Python/NumPy版は参照実装、OpenSpielの
`native_efg`は独立した小規模検証用oracleとして残します。

大規模設定では`precision="float32"`によりCFR状態メモリを半減できます。N=50・7サイズ・
10,000反復のDCFRでは約24.9秒、Exploitability `5.60e-6`でした。N=100・10サイズの
100反復ではfloat64の約7.18秒に対してfloat32は約6.40秒でした。混合精度はメモリ削減が
主目的であり、小さな木では速度差がほとんどないため、再現性を優先する標準N=10設定は
float64のままです。

同じ環境での参考値では、N=10・2サイズ・1,000反復のC++ DCFRは約0.022秒でした。
N=50・7サイズ・1,000反復はfloat64で約2.70秒、float32で約2.67秒です。N=100・10サイズは
public treeが54,201ノードへ増えるため、100反復でもfloat64約7.18秒、float32約6.40秒です。
計算量はNだけでなく、サイズ組合せから生じる合法raise履歴数に強く依存します。

小さいfractionを多数追加するとraise回数とゲーム木が急増します。標準の1/3・1.0、
stack 4では約12,900ノードです。

## 実装とテスト

- [ゲーム定義](../../src/toy_poker/games/integer_range_betting/game.py)
- [共通1 street状態機械](../../src/toy_poker/games/fixed_range_one_street.py)
- [表示用plugin](../../src/toy_poker/games/integer_range_betting/plugin.py)
- [ゲームルールテスト](../../tests/games/test_integer_range_betting.py)
- [ベクトル化CFR+](../../src/toy_poker/solvers/vectorized_range.py)
- [C++ range solver adapter](../../src/toy_poker/solvers/cpp_range.py)
- [C++ CFR+/DCFR kernel](../../src/toy_poker/solvers/cpp/range_solver.cpp)
- [ベクトル化レポート解析](../../src/toy_poker/analysis/vectorized_range.py)
- [解析テスト](../../tests/analysis/test_integer_range_betting_analysis.py)
- [native EFGとの整合テスト](../../tests/solvers/test_vectorized_range.py)
