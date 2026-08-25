# Integer 1-N weighted-range custom-size game

## ルール概要

- Riverの1 streetを抽象化し、追加のpublic cardは配られません。
- OOPとIPはそれぞれ1〜Nの整数rankを独立に持ちます。大きい数字が勝ち、同じ数字はtieです。
  各プレイヤーのrank確率は別々に設定できます。
- 初期potは1、両者のstackはデフォルト4で、OOPから1 streetのbettingを始めます。
- Check、Fold、Call、All-inに加え、設定したpot比率のBet/Raiseを両者が使えます。デフォルトは
  33% potと100% potで、no-limit hold'em標準のminimum raise制約を適用します。
- Check-checkまたはCallでshowdown、Foldで即終了します。utility合計は初期potの1です。

## toyゲームの目的

AKQ系の少数ランクとAll-inだけの世界を拡張し、riverの連続的なrange対rangeと複数サイズ戦略に近い現象を
観察するためのゲームです。rankごとのEVとbet頻度から、value threshold、bluff-catch threshold、
polarな大きいbet、薄いvalueを含む小さいbet、check rangeの保護がどのように分離するかを学べます。

Bet/Raiseサイズとminimum raiseが作るアクション木の中で、複数サイズの使い分け、raiseに対する防御、
rangeのBayes更新、非一様rangeが戦略に与える影響を検証できます。実戦的にはGTO viewerのrange grid、
node頻度、EQ、EV、EQRの読み方を練習する題材です。ただしrankは独立配布なので、実カードのblockerと
card-removal effectはこのゲームからは学べません。

## 公開解析結果

- [N=50・7サイズ高精度設定のReport](../../public/results/integer_range_betting/report.md)
- [Interactive strategy viewer](../../public/results/integer_range_betting/strategy_viewer.html)
- [計算条件と要約](../../public/results/integer_range_betting/summary.json)

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
| `oop_rank_weights` | string | `"uniform"` | N個の有限な非負数、合計は正 | OOPの相対重み |
| `ip_rank_weights` | string | `"uniform"` | N個の有限な非負数、合計は正 | IPの相対重み |

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
weightを`0`にすると、そのrankを当該プレイヤーのrangeから除外できます。全rankを`0`にはできません。

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

`strategy_viewer.html`では、ROOTから合法actionを順に選んで任意のpublic historyへ移動し、
その局面の手番プレイヤーの1〜N戦略を方眼状に表示します。各マスはAll-in、サイズの大きい
bet/raiseから小さいbet/raise、Call、Check、Foldの順に左から塗り分けます。Checkは黄緑、
bet/raiseは薄い赤から濃い赤、All-inは青です。マスを選ぶと正確なaction頻度、Action EV、
rootからのrange残存率、条件付きrange weight、showdown EQを確認できます。

方眼の横方向はrankごとのaction頻度、縦方向はそのrankがrootから当該nodeまで残っている
割合です。残存率が40%ならマスの上60%を白、下40%をaction色で横分割します。これは
[GTO WizardのRange height表示](https://help.gtowizard.com/study-mode/)に対応する考え方です。

Historyとbreadcrumbは、単なるaction列ではなく、actionを選択したプレイヤーを付けて
`[OOP] Bet 10% → [IP] Raise 33% → [OOP] ?`のように表示します。末尾の`?`は現在の
手番プレイヤーを表し、terminal historyには付けません。

viewer最上段はbreadcrumb、history選択リスト、node情報を縦に配置します。node情報には
reach probabilityとhistory depthを表示します。rangeの更新方法は表示しません。
reach probabilityが`major_reach_threshold`未満の場合は、局所戦略が十分に収束していない
可能性を示す警告バナーをページ最上段に表示します。閾値はreportの主要局面
抽出とviewer警告で共通の`1e-4`（0.01%）です。

pot stateは戦略方眼の右側、選択rankの詳細パネルの上に配置します。手番名の見出しは置かず、
potを上段、OOP/IPを下段にまとめ、両者の残stackとtable上のcommit、現在pot、to call、直前の
bet/raise名とpot比率を表示します。通常サイズはaction前のpotとcall額を基準にし、All-inも
親nodeから増えたcommit額から実際のpot比率を逆算します。右カラムの上下端は戦略方眼の
パネルに揃え、stackやcommitはラベルと値を横並びにして縦方向を圧縮します。選択rankの
詳細パネルにはEQとaction別の頻度・EVだけを表示します。

`Range metrics`は戦略方眼と`Manhattan strategy`の間に配置し、現在のhistoryにおけるOOP/IP
それぞれのrange全体のEV、EQ、EQRを表示します。
EVは現在nodeより前に支払ったcommitをsunk costとして戻したcurrent-node基準です。保存されて
いるroot基準utilityを (U_p(h))、現在までのcommitを (C_p(h)) とすると、表示EVは次です。

\[
EV_p(h)=U_p(h)+C_p(h)
\]

viewer内の`Node strategy`、rank詳細、tooltipのAction EVもすべて同じcurrent-node基準へ
変換します。したがってbetに直面した局面のFold EVは0です。元の`analysis.json`とCSVは
実験全体で統一しているroot基準utilityを保持し、表示時だけrebaseします。

この基準では両プレイヤーの表示EV合計が現在potと一致し、現在foldした場合の追加EVは0です。
EQは現在の両条件付きrangeをそのままshowdownさせたときのrange equityです。EQRは
[GTO Wizard公式の定義](https://blog.gtowizard.com/what-is-equity-in-poker/#eqr-defined)に従います。

\[
EQR_p(h)=\frac{EV_p(h)}{Pot(h)\times EQ_p(h)}
\]

たとえばEVがpotの75%、EQが50%ならEQRは150%です。EQが実質0の場合はゼロ除算を避けて
EQRを未定義として表示します。

戦略方眼上のnode集計strategyは、rankごとのstrategyを、その履歴における手番プレイヤーの
条件付きrangeで重み付けしたaction頻度です。履歴 (h)、手番プレイヤーのrank (r)、action
(a)に対して次の値を表示します。

\[
F(a\mid h)=\sum_r P(r\mid h)\,\sigma(a\mid r,h)
\]

actionを選んで次の局面へ進むと、実際にそのactionを取る頻度を使って、手番プレイヤーの
rangeをBayes更新します。

\[
P(r\mid h,a)=
\frac{P(r\mid h)\,\sigma(a\mid r,h)}
{\sum_{r'}P(r'\mid h)\,\sigma(a\mid r',h)}
\]

プレイヤー (p) のrank (r) がrootから履歴 (h) まで残っている割合を
(W_p(r,h)) とします。rootでは全rankが100%残っています。

\[
W_p(r,\emptyset)=1
\]

プレイヤー (p) 自身がaction (a) を選んだときだけ、そのaction頻度を乗算します。
相手がactionした場合、自分の残存率は変わりません。

\[
W_p(r,h+a)=
\begin{cases}
W_p(r,h)\,\sigma_p(a\mid r,h) & \text{if player}(h)=p \\
W_p(r,h) & \text{otherwise}
\end{cases}
\]

条件付きrangeはrootの事前分布 (P_{0,p}) と残存率を使って正規化した別の値です。

\[
P_p(r\mid h)=
\frac{P_{0,p}(r)W_p(r,h)}
{\sum_{r'}P_{0,p}(r')W_p(r',h)}
\]

このため、重み付きroot rangeでもrootにある全rankの表示高は100%です。元々の出現確率は
`Conditional range weight`、rootから同rankが残った割合は`Range retained`として区別します。

`Manhattan strategy`は、手番プレイヤーのrange内にある各rankを相手の条件付きrangeに
対するshowdown EQが低い順に並べ、rankごとのaction頻度を高さ100%の積み上げbarとして
表示します。[GTO WizardのBreakdown Tab](https://help.gtowizard.com/breakdown-tab/)で使われる
Manhattan plotと同じく、横座標は連続値としてのEQではなく、EQでsortしたhandの位置です。
横軸の目盛りには、その位置にあるrankの実際のEQを表示します。

各rankの横幅は等しく、条件付きrange weightには比例しません。そのため、range weightが
一様でない局面では、グラフ上の色面積比と上段の`Node strategy`のaction頻度は一致しない
場合があります。正確な集計頻度には`Node strategy`を使用します。

デフォルトでは条件付きweightが実質0のrankを除外します。`Show zero-weight ranks`を有効に
すると全rankを表示し、range外のrankは斜線で区別します。barを選択すると方眼strategyと
rank詳細も同じrankへ移動します。

`Conditional ranges`はこの更新後のOOP/IP両rangeをrank軸で表示します。`Equity
distribution`は[GTO WizardのEquity Graph](https://blog.gtowizard.com/what-is-equity-in-poker/#equity-graphs)
と同様に、各プレイヤーのrankを相手rangeに対するEQが低い順に並べ、横軸を自分の条件付き
range percentile、縦軸をshowdown EQとして表示します。rank \(r\) のEQは、相手が弱い確率と
同rankの半分です。

\[
EQ(r)=P(R_{opp}<r)+\frac12P(R_{opp}=r)
\]

EQ順のrankを \(r_1,\ldots,r_N\) とすると、rank \(r_i\) は横軸の次の区間を占めます。

\[
\left[
\sum_{j<i}P(r_j\mid h),
\sum_{j\le i}P(r_j\mid h)
\right]
\]

したがって、action後にBayes更新された重みの大きいrankほど、Equity Distribution上でも
広い横幅を占めます。

`range EQ`はこれを自分の条件付きrangeで平均した値です。これはfold equity、pot odds、
将来のactionを含む戦略EVではなく、現在の両rangeをそのままshowdownさせたときのequityです。
到達確率0のactionではBayes分母も0になるため、viewerは親局面のrangeを引き継いだ参考表示に
切り替え、警告を表示します。

```toml
[analysis]
interactive_viewer = true
viewer_grid_columns = 10
```

到達確率が`major_reach_threshold`未満の局面も移動先として残しますが、off-pathに近い戦略を
均衡上重要な混合と誤解しないようviewer内に警告を表示します。

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

N=50・7サイズをfloat64で再確認する高精度設定は
[`integer_range_betting_n50_7_sizes_cpp_dcfr_high_precision.toml`](../../configs/experiments/integer_range_betting_n50_7_sizes_cpp_dcfr_high_precision.toml)
です。最大1,000,000反復、Exploitability目標`1e-6`で実行したところ、38,000反復の
`9.05e-7`と39,000反復の`8.42e-7`で目標を連続して満たし、early stoppingしました。
最終EVはIP `0.5322014584`、OOP `0.4677985416`、solver時間は約91.1秒でした。

さらに厳しい
[`integer_range_betting_n50_7_sizes_cpp_dcfr_target_1e8.toml`](../../configs/experiments/integer_range_betting_n50_7_sizes_cpp_dcfr_target_1e8.toml)
では、目標`1e-8`、最大300,000反復で実行しました。100,000反復で`7.58e-8`、
200,000反復で`2.12e-8`、最良は295,000反復の`1.319e-8`でした。目標には届かず、
300,000反復の最終Exploitability `1.666e-8`で上限停止しました。最終EVはIP
`0.5322014334`、OOP `0.4677985666`、solver時間は約668.4秒です。Exploitabilityは
checkpointごとに単調減少するとは限らないため、最終値が最良値を上回る場合があります。

### OOPがlow/high rankだけを持つ実験

[`integer_range_betting_n50_7_sizes_oop_extremes_dcfr_target_1e8.toml`](../../configs/experiments/integer_range_betting_n50_7_sizes_oop_extremes_dcfr_target_1e8.toml)
は、OOPが`1–10, 41–50`を各5%、IPが`1–50`を各2%持つ非対称rangeです。stack 4、
7サイズ、float64 DCFR、最大300,000反復、Exploitability目標`1e-8`で実行しました。
288,000反復でearly stoppingし、最終Exploitabilityは`9.417e-9`、最良値は263,000反復の
`5.000e-9`、solver時間は約636.7秒でした。最終EVはIP `0.4074386373`、OOP
`0.5925613627`です。

rootでサイズ10%、20%、33%、50%、All-inは実質的に使われず、全OOP rangeで集計した
戦略は次のとおりです。

| action | frequency | betting range内のrank 1–10 |
|---|---:|---:|
| Check | 29.1888% | 87.3807% |
| Bet 75% | 16.3495% | 30.0000% |
| Bet 100% | 20.0001% | 33.3333% |
| Bet 150% | 34.4617% | 37.5000% |

potを1、bet額を`b`とすると、pure bluffの最適比率は`b / (1 + 2b)`です。したがって
75%、100%、150% pot betのbluff比率はそれぞれ30%、1/3、37.5%となり、数値解と一致します。
IPの集計応答も、各サイズで必要なfold率`b / (1 + b)`と一致します。

| facing | Fold | Call | Raise合計 |
|---|---:|---:|---:|
| Bet 75% | 42.8571% | 44.6749% | 12.4680% |
| Bet 100% | 50.0000% | 39.7436% | 10.2564% |
| Bet 150% | 60.0000% | 31.6923% | 8.3077% |

OOPのrank 1–6はcheckと3サイズへ分散するbluff、7–10はcheck、41–42は主に75%、
43–44は100%、45–47は150%のvalueとして使われます。48–50は各betting rangeを
必要なvalue/bluff比に保つため、checkと3サイズへ分散します。OOPがbetした条件下では
IPのrank 11–40は「全low bluffに勝ち、全high valueに負ける」という同じequityを持つため、
同一の混合応答になり得ます。この同価性はrank順に単調な戦略にならない理由であり、バグではありません。

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
