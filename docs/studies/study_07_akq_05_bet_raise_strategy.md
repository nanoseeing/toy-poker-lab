# AKQゲーム⑤ Bet・Raise戦略

## ルール

| 項目 | 内容 |
|---|---|
| OOPハンド | A / K / Q（各1/3・独立配布） |
| IPハンド | A / K / Q（各1/3・独立配布） |
| Street | 1 Street |
| 初期Pot | 1 |
| 有効Stack | 1 |
| 許可アクション | Check、Fold、Call、10/20/33/50/75% PotのBet・Raise、All-in |
| 勝敗判定 | A > K > Q。同じハンドはTie |
| 利得計算方法 | 初期Potをデッドマネーとし、両者の終端利得の合計は1 |

---

## 最適戦略

### 均衡戦略

#### RootのOOP戦略

| OOP rank | Check | Bet 50% |
|---|---:|---:|
| Q | 91.31% | 8.69% |
| K | 73.92% | 26.07% |
| A | 47.85% | 52.15% |

その他のroot sizeは数値誤差を除いてほぼ0%です。単純な`Q bluff / A value / K check`ではなく、
Kの一部を50% betし、Aの約半分をCheckへ残すmerged/polar混合のrangeになります。

#### OOP Check後のIP戦略

| IP rank | 主要戦略 |
|---|---|
| Q | Check 52.18% / All-in 34.72% / Bet 75% 13.10% |
| K | Check 100% |
| A | All-in 69.43% / Bet 75% 30.57% |

#### OOPの50% Betに対するIP戦略

| IP rank | 主要戦略 |
|---|---|
| Q | Fold 94.81% / Raise All-in 5.19% |
| K | Fold 22.58% / Call 76.10% / Raise All-in 1.32% |
| A | Raise All-in 100% |

### EV

| プレイヤー | EV |
|---|---:|
| IP | 0.530193219 |
| OOP | 0.469806781 |
| 合計 | 1.00 |

### 導出方法

#### 50% Bet rangeが1:3:6になる数学的導出

OOPが50% PotをBetするQ、K、Aのmassをそれぞれ$x_Q,x_K,x_A$とします。各handの事前確率は同じなので、
これはそのままRootのBet頻度比です。IPがKでCallした場合の利得は、OOPがQなら`+1.5`、KならTieで
`+0.5`、Aなら`-0.5`です。Foldの利得0と無差別になる条件は、

$$
1.5x_Q+0.5x_K-0.5x_A=0
\quad\Longrightarrow\quad
x_A=3x_Q+x_K
$$

です。

次にIPがQでAll-in Raiseすると、均衡応答ではOOPのQとKはFoldし、AだけがCallします。ここでOOPは
IPのQを観測しているのではなく、All-in range全体に対して応答しています。IPのQはOOPにFoldされたとき
`+1.5`、Callされたとき`-1`なので、RaiseとFoldで無差別になる条件は、

$$
1.5(x_Q+x_K)-x_A=0
\quad\Longrightarrow\quad
x_A=1.5(x_Q+x_K)
$$

です。2式を連立すると、

$$
x_K=3x_Q,\qquad x_A=6x_Q
$$

となり、50% Bet rangeの比率は厳密に、

$$
Q:K:A=1:3:6
$$

になります。つまりBet rangeの10%がQ、30%がK、60%がAです。この比率は、IPのQとKを同時に
無差別にするために必要であり、単なるSolverの丸め結果ではありません。

#### なぜOOP(K)はAll-in Raiseへ100% Foldするのか

OOPの50% Bet後、IPのAll-in Raiseに対してAだけをCallすればBet rangeの60%を防御できます。IPは1を
riskして、OOPのBetを含む1.5を取りにいくため、bluffに許せるFold率は、

$$
F=\frac{1}{1+1.5}=40\%
$$

です。OOPがQとKをFoldする割合はちょうど$(1+3)/10=40\%$なので、AだけのCallでMDFを満たします。
実際、IP(Q)のAll-in利得は、

$$
0.4\cdot1.5+0.6\cdot(-1)=0
$$

となり、Foldと無差別です。KまでCallするとIP(Q)のbluffは負の利得になりますが、OOP(K)自身も
All-in rangeに対して十分なequityを持っていないため、そのような防御は必要ありません。

保存runのIPのAll-in頻度はQが5.19%、Kが1.32%、Aが100%です。事前確率が等しいため、Raiseを見た
OOP(K)から見たIP rangeは、正規化前で、

$$
Q:K:A=0.0519:0.0132:1
$$

です。したがってOOP(K)のequityは約5.49%にすぎません。追加Call額0.5、Call後Pot 3から必要equityは、

$$
\frac{0.5}{3}=16.67\%
$$

です。保存runでもFoldのAction EVは$-0.5$、Callは約$-0.83524$であり、Kは無差別ではなく厳密に
Fold優位です。したがって100% Foldは未収束による偶然ではなく、Aだけでrange全体を十分に防御した
結果です。

#### 絶対頻度が$2/23$倍になる数学的導出

比率を保ったRootの50% Bet頻度を、

$$
b_Q=t,\qquad b_K=3t,\qquad b_A=6t,
\qquad 0\leq t\leq\frac{1}{6}
$$

と置きます。OOPがCheckした後に残るQ、K、Aのmassは、

$$
q=1-t,\qquad k=1-3t,\qquad a=1-6t
$$

です。IPのQがCheck、75% Bet、All-inを混合するため、OOP(K)のAll-inへのCall率を$c_1$、
75% BetへのCall率を$c_{0.75}$とすると、Qの無差別条件から、

$$
c_1=\frac{0.5q+k-a}{2k},
\qquad
c_{0.75}=\frac{0.5q+k-0.75a}{1.75k}
$$

を得ます。

IPのAも75% BetとAll-inを混合します。OOP(K)がCallしたとき、All-inではFold時より追加で1、
75% Betでは追加で0.75を得るため、Aの無差別条件は、

$$
c_1=0.75c_{0.75}
$$

です。上の2式を代入すると、

$$
q+2k-5a=0
$$

となります。$q=1-t,k=1-3t,a=1-6t$を代入すれば、

$$
-2+23t=0
\quad\Longrightarrow\quad
t=\frac{2}{23}
$$

です。したがってRootの厳密な50% Bet頻度は、

$$
b_Q=\frac{2}{23}\simeq8.70\%,\qquad
b_K=\frac{6}{23}\simeq26.09\%,\qquad
b_A=\frac{12}{23}\simeq52.17\%
$$

となり、保存runの`8.69% / 26.07% / 52.15%`と一致します。

#### なぜ75% BetとAll-inを混合するのか

$t=2/23$のとき、OOPのCheck後rangeは、共通因子$1/23$を除いて、

$$
q:k:a=21:17:11
$$

です。IPがQでPot比$B$をBetしたとき、OOPのQはFold、Kは確率$c_B$でCall、AはAll-inへRaiseし、
IP(Q)はそのRaiseへFoldするとします。IP(Q)をCheckとBetで無差別にするOOP(K)のCall率は、

$$
c_B=\frac{0.5q+k-aB}{k(1+B)}
=\frac{27.5-11B}{17(1+B)}
$$

です。したがって、

$$
c_{0.75}=\frac{11}{17},\qquad
c_1=\frac{33}{68}
$$

となります。IP(A)がOOP(K)のCallから得る追加利得は$Bc_B$に比例するため、

$$
0.75c_{0.75}=c_1=\frac{33}{68}
$$

です。75% BetはCallされる頻度が高く、All-inはCall時に得る額が大きいため、Aは両sizeで無差別に
なります。

各sizeのpolar rangeもそれぞれ整合しています。OOP(K)をCallとFoldで無差別にするbluff:value比は、

$$
\mathrm{bluff}:\mathrm{value}=B:(1+B)
$$

なので、75% Betでは$3:7$、All-inでは$1:2$です。保存runのIPのQ:A頻度も、75% Betでは
`13.10:30.57`、All-inでは`34.72:69.43`となり、ほぼこの比率です。

連続sizeとしてAの追加利得を最大化すると、共通の正の因子を除いて、

$$
g(B)=\frac{B(27.5-11B)}{1+B}
$$

であり、

$$
g'(B)=\frac{27.5-22B-11B^2}{(1+B)^2}=0
\quad\Longrightarrow\quad
B^{*}=\sqrt{\frac{7}{2}}-1\simeq87.08\%
$$

を得ます。許可sizeには87.08%がないため、その両側の75%と100%が候補になり、この均衡rangeでは
$g(0.75)=g(1)=8.25$と完全に一致します。ただし両size間の**混合頻度そのもの**は87.08%を線形補間して
決めるのではなく、size別のbluff:value比、RootのCheck/Bet頻度、OOPの応答を同時に無差別にすることで
決まります。87%前後のsizeを追加すればgame tree全体のrange構成も変わるため、改めて解く必要があります。

#### 数学的に確定できる条件

このゲームでは、各open sizeに対してIPがFold/Call/Raiseを選び、さらにRaise後のOOP応答まであるため、
K vs AQのような2本の無差別式だけでは閉じません。完全な閉形式解は主張せず、有限ゲームの連立した
最適反応条件をsolverで解いています。

ただし、正の頻度で混ぜるroot actionには必ず、

$$
EV_r(\mathrm{Check})=EV_r(\mathrm{Bet\ 50\%})
$$

というrank $r$ごとの無差別条件が必要です。保存runではQ/K/AのいずれもCheckとBet 50%のAction EVが
ほぼ一致し、それ以外のroot sizeはそれ以下でした。この等式だけでは各rankの混合頻度は決まりません。
IPのFold/Call/Raise頻度、OOPのRaise応答、全rangeの到達確率を同時に満たすことで初めて数値が決まります。

#### 純粋戦略ではなく混合になるヒューリスティック解釈

- Qだけをbluff、Aだけをvalueにすると、IPはOOPのBetとCheckからrank構成を強く推定できます。
- Kを一部betするとIPのQ/Kからthin valueを得つつ、IPの自由なbetを先回りできます。
- KはAのRaiseに弱いため全betにはできません。
- Aを一部Checkへ残すと、IPはOOPのCheckを見ても無制限にbluff/raiseできません。

したがって、各rank単体の強さ順thresholdではなく、Bet rangeとCheck rangeを同時に守る混合になります。

#### 1:3:6を保って頻度を上下させた場合のEV

IPの均衡戦略を固定したまま$t$だけを動かす場合、各OOP handはRootでCheckと50% Betが無差別なので、

$$
\frac{dEV_{OOP}}{dt}
=\frac{1}{3}\sum_{r\in\{Q,K,A\}}m_r
\left[EV_r(\mathrm{Bet\ 50\%})-EV_r(\mathrm{Check})\right]=0,
\qquad (m_Q,m_K,m_A)=(1,3,6)
$$

となります。したがって、**相手戦略を固定するならOOPのEVは変わりません**。これは混合戦略の
無差別性そのものです。

一方、IPが変更後のrangeへ最適化し直す場合、50% Bet後のrange比は1:3:6のままですが、Check後のrangeは
`(1-t):(1-3t):(1-6t)`へ変わります。上の無差別条件の下では、IP(A)のAll-inと75% BetのEV差は、

$$
EV_A(\mathrm{All\text{-}in})-EV_A(\mathrm{Bet\ 75\%})
=\frac{-2+23t}{28(3-10t)}
$$

です。$t<2/23$ではAが75% Betを、$t>2/23$ではAll-inを選びやすくなり、$t=2/23$だけが両方を
無差別にします。

Root頻度をNode lockし、それ以外を再最適化した感度分析は次のとおりです。数値誤差は最大約`2.1e-6`です。

| $t$ | Q / K / Aの50% Bet頻度 | OOP EV | IP EV |
|---:|---|---:|---:|
| 0 | 0% / 0% / 0% | 0.462962963 | 0.537037037 |
| 0.04 | 4% / 12% / 24% | 0.466825397 | 0.533174603 |
| $2/23$ | 8.70% / 26.09% / 52.17% | **0.469806763** | **0.530193237** |
| 0.12 | 12% / 36% / 72% | 0.468888889 | 0.531111111 |
| $1/6$ | 16.67% / 50% / 100% | 0.452576489 | 0.547423511 |

したがって、相手が再最適化する条件では$t=2/23$がOOP EVを最大化し、比率を保っていても絶対頻度を
上下させるとOOP EVは低下します。Node lockせずSolverを再実行した場合は、この頻度へ戻る方向に最適化されます。

---

## ポーカーにおける概念理解

### なぜOOPはKをBetするのか

OOPが全rangeをCheckすると、IPはpositionを使ってQ/Aをpolarizeし、Kへ大きなbetを突きつけられます。
Kの50% betには次の役割があります。

- IPに自由なbet sizeを選ばせず、自分でshowdownまでの価格を決めるblock-bet効果。
- IPのKからCallを受けるthin/merged value。
- Qのbluffと同じsizeを使い、bet rangeをAだけに限定しない。
- IPのRaise rangeを誘発し、AのCheckからの防御価値を作る。

KはAのRaiseに弱いため100% betできません。反対にAをすべてbetするとchecking rangeがQ/Kへ偏り、IPが
Check後に攻撃しやすくなるので、Aの一部をCheckへ残します。AのCheckはslow-playというより、OOPの
checking range全体を守るrange protectionです。

---

## Solverによる再現結果

| 指標 | 結果 |
|---|---:|
| IP EV | 0.530193219 |
| OOP EV | 0.469806781 |
| Exploitability | `7.4617e-6` |

- [Strategy Viewer](../../public/studies/akq_symmetric_variable_size/strategy_viewer.html)
- [計算条件](../../public/studies/akq_symmetric_variable_size/resolved_config.json)

### 再現方法

```bash
toy-poker run configs/experiments/integer_range_betting_n3_stack_1_5_sizes_dcfr.toml
```

---

## その他備考

### 41–43型の非単調性との関係

離散rankゲームでは、隣接rankが必ず同じ主要actionになるとは限りません。複数の相手response range、
Raise、同rankのtie、checking-range防御が同時に釣り合うためです。Action EVが近い場合、個別rankの
混合は非一意またはsolver経路に敏感です。純粋なhand strengthだけでなくrange全体の制約を読みます。
