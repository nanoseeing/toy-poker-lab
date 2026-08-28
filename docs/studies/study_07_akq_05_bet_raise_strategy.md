# AKQゲーム⑤ OOPのBlock Bet

## ルール

| 項目 | 内容 |
|---|---|
| OOPハンド | A / K / Q（各1/3・独立配布） |
| IPハンド | A / K / Q（各1/3・独立配布） |
| Street | 1 Street |
| 初期Pot | 1 |
| 有効Stack | 1 |
| 許可アクション | Check、Fold、Call、Stackの範囲内の任意サイズのBet・Raise、All-in |
| 勝敗判定 | A > K > Q。同じhandはTie |
| 利得計算方法 | 初期Potをデッドマネーとし、ゲーム終了時の両者の利得合計は1 |

Solverで複数のBet sizeを比較すると、OOPのrootでは50% Potが主要sizeとして現れます。本Studyではこの結果を
出発点として50% Potを固定し、OOPがQのBluffとAのValueだけでなく、中間handのKもBetする理由と、その頻度を
解析します。

任意の連続sizeから50% Potそのものを導くには、全てのBet・Raise sizeと、その後の応答を同時に調べる必要があります。
その証明は本Studyでは扱わず、50% Potを固定した後の戦略に焦点を絞ります。

---

## 最適戦略

### 均衡戦略

以下は、OOPのroot Betを50% Potに固定して無差別条件を解いた戦略です。

#### 学習対象：OOPのRoot戦略

| OOP hand | Check | Bet 50% | Bet range内の比率 |
|---|---:|---:|---:|
| Q | 90.4758% | 9.5242% | 1 |
| K | 71.4273% | 28.5727% | 3 |
| A | 42.8546% | 57.1454% | 6 |

したがって、50% Bet rangeのmass比は、

$$
Q:K:A=1:3:6
$$

です。QはBluff、AはValue、KはBlock Betを担当します。Aの42.8546%をCheckへ残すことで、OOPの
Checking rangeもAを含む強いrangeになります。

#### OOPの50% Betに対するIP戦略

| IP hand・action | 頻度 |
|---|---:|
| Q/KからのAll-in Bluff Raise | 両handへの割当頻度の合計6.8073% |
| KのCall | 75.9156% |
| AのAll-in Raise | 100% |

QとKのどちらをBluff Raiseへ回すかには非一意性があります。代表例として、Bluff RaiseをQだけへ割り当てる
なら、IP(Q)が6.8073% All-in Raiseし、IP(K)は75.9156% Callして残りをFoldします。

50% Potを前提とすると、standard minimum raiseの合計commitmentは1で、有効Stackと一致します。そのため、
この局面でIPが行えるfull raiseはAll-inだけです。

#### OOP Check後の戦略

| 局面 | hand | 戦略 |
|---|---|---|
| OOP Check後、IP | Q | Check 51.8312% / Bet 92.9339% 48.1688% |
| OOP Check後、IP | K | Check 100% |
| OOP Check後、IP | A | Bet 92.9339% 100% |
| IPの92.9339% Betに直面、OOP | Q | Fold 100% |
| IPの92.9339% Betに直面、OOP | K | Call 55.7580% / Fold 44.2420% |
| IPの92.9339% Betに直面、OOP | A | All-in Raise 100% |

OOPがCheckすると、IPはQ/AをPolarizeして約92.93% Potを使えます。OOPがKで50%を先にBetすることには、
この大きなsizeを選ばせない意味があります。

### EV

| プレイヤー | 50% Pot固定時の解析EV |
|---|---:|
| IP | 0.530542271 |
| OOP | 0.469457729 |
| 合計 | 1.00 |

### 導出方法

#### 導出の順序

| 順序 | 求めるもの | 使用する条件 |
|---:|---|---|
| 出発点 | OOPのroot Bet sizeを50% Potに固定 | Solverで得た主要sizeを解析対象とする |
| 1 | OOPの50% Bet range比率 | IP(K)のCall/Fold、IP(Q/K)のBluff Raise/Fold無差別 |
| 2 | 絶対頻度を決めるために必要なIP戦略 | OOP Check後のIP Bet、OOPの応答、rootでのOOP各handの無差別 |
| 3 | OOPの絶対Bet頻度 | IP(A)のBet size最適化条件 |
| 4 | EV | OOP各handのCheck EV |

最初の無差別条件だけで決まるのは $`Q:K:A=1:3:6`$ という**比率**です。比率を保ったまま全頻度を
上下させる共通倍率 $`t`$ はまだ決まりません。$`t`$を特定するには、OOPのChecking rangeに対するIPの戦略まで
解く必要があります。以下では、その依存関係が分かる順序で導出します。

#### 1. なぜBet rangeがQ:K:A = 1:3:6になるのか

OOPが50% PotをBetするQ、K、Aのmassを、それぞれ $`x_Q,x_K,x_A`$ とします。

##### IP(K)をCallとFoldで無差別にする

IP(K)が50% BetをCallしたときの利得は、OOPのhandごとに次のとおりです。

| OOP hand | IP(K)のCall利得 |
|---|---:|
| Q | +1.5 |
| K | +0.5（Tie） |
| A | -0.5 |

Foldの利得0と等しくするには、

$$
1.5x_Q+0.5x_K-0.5x_A=0
$$

したがって、

$$
x_A=3x_Q+x_K
$$

が必要です。

##### IP(Q/K)をAll-in Bluff RaiseとFoldで無差別にする

IPのQまたはKがAll-in Raiseすると、OOPのQ/KはFoldし、AだけがCallします。Q/Kへ勝つ場合は1.5を得て、
AへCallされる場合は1を失うため、

$$
1.5(x_Q+x_K)-x_A=0
$$

すなわち、

$$
x_A=1.5(x_Q+x_K)
$$

が必要です。

2式を連立すると、

$$
x_K=3x_Q,\qquad x_A=6x_Q
$$

を得ます。したがって、

$$
Q:K:A=1:3:6
$$

です。ここでKをBet rangeから除くと、2つの無差別条件を同時に満たす非自明な解がなくなります。KのBlock Betは、
QのBluffとAのValueを同じ50% rangeへまとめ、IPにCallとBluff Raiseの両方を混ぜさせるために必要です。
これが本Studyの中心です。50%を固定して二つの無差別条件を同時に解くと、正の $`x_K`$ が現れます。
したがってKは、QとAの間を埋めるBlock Betとして必要です。

#### 2. 絶対頻度を決めるために必要なIP戦略

ここまででBet rangeの**構成比**は決まりましたが、OOPが各handを実際に何% Betするかは決まっていません。
絶対頻度を求めるには、BetしなかったhandでできるOOPのChecking rangeと、それに対するIPの最適戦略を同時に
解く必要があります。そのため、ここからIP戦略を導出します。

OOP Check後にIPが使うBet額を $`B`$、IP(Q)のBet頻度を $`u`$ とします。IP(A)は100% Betします。

OOP(K)がCallすると、Qには $`1+B`$ 勝ち、Aには $`B`$ 負けます。CallとFoldを無差別にする条件は、

$$
(1+B)u-B=0
$$

したがって、

$$
u=\frac{B}{1+B}
$$

です。

次に、OOPの50% Betに対するIP(Q/K)のBluff Raise割当頻度の合計を $`r`$、IP(K)のCall率を $`d`$ とします。
OOP(Q)とOOP(K)をCheckと50% Betで無差別にすると、

$$
r+d=\frac{2+u}{3},\qquad 3r+d=2u
$$

なので、

$$
r=\frac{5u-2}{6},\qquad d=1-\frac{u}{2}
$$

です。さらにOOP(A)もCheckと50% Betで無差別にする条件は、

$$
r+\frac{d}{2}=uB
$$

です。$`u,r,d`$を代入すると、

$$
12B^2-9B-2=0
$$

となり、正の解は、

$$
B_{\mathrm{opt}}=\frac{9+\sqrt{177}}{24}
\simeq0.929338946
$$

です。よって、

$$
u\simeq0.481688,\qquad
r\simeq0.068073,\qquad
d\simeq0.759156
$$

を得ます。

#### 3. OOPの絶対Bet頻度

Bet range比率を使い、OOPのQ/K/Aの50% Bet頻度を、

$$
b_Q=t,\qquad b_K=3t,\qquad b_A=6t
$$

と置きます。OOP Check後に残る各handのmassは、

$$
q=1-t,\qquad k=1-3t,\qquad a=1-6t
$$

です。IPの92.9339% Betに対するOOP(K)のCall率は、IP(Q)をCheckとBetで無差別にする条件から、

$$
c_B=\frac{0.5q+k-aB}{k(1+B)}
$$

となります。IP(A)がBet size $`B`$から得る追加利得は $`Bc_B`$に比例します。固定したCheck rangeに対して
この値を最大化する一階条件は、

$$
0.5q+k=aB(2+B)
$$

です。左辺と右辺の差は $`B`$について厳密に減少するため、固定support内ではこの停留点が一意な最大値です。
$`B=B_{\mathrm{opt}}`$を代入すると、

$$
t=
\frac{B_{\mathrm{opt}}(2+B_{\mathrm{opt}})-1.5}
{6B_{\mathrm{opt}}(2+B_{\mathrm{opt}})-3.5}
\simeq0.095242321
$$

です。したがって、OOPのroot Bet頻度は、

$$
b_Q\simeq0.095242,\qquad
b_K\simeq0.285727,\qquad
b_A\simeq0.571454
$$

になります。

この $`t`$ が、比率を保ったままBet頻度を上下させる自由度を消す値です。異なる $`t`$を選ぶとOOPのChecking rangeが
変わり、IP(A)が選ぶsize $`B`$の一階条件を満たさなくなります。したがって、IP戦略の導出は補足ではなく、OOPの
絶対頻度を特定するために必要な部分です。

#### 4. EV

OOPのQ/K/AがCheckしたときのEVは、

$$
EV_Q=\frac{1-u}{6},\qquad
EV_K=\frac{1}{2}-\frac{u}{3},\qquad
EV_A=\frac{2.5+uB_{\mathrm{opt}}}{3}
$$

です。各handはCheckと50% Betで無差別なので、

$$
EV_{OOP}=\frac{EV_Q+EV_K+EV_A}{3}
\simeq0.469457729
$$

となり、

$$
EV_{IP}=1-EV_{OOP}\simeq0.530542271
$$

です。

---

## ポーカーにおける概念理解

### Block Betとは何か

Block Betは、OOPが比較的小さいsizeを先に使い、IPがより大きなsizeを自由に選ぶことを防ぐBetです。この戦略では、

- OOPがCheckすると、IPはQ/Aで約92.93% Potを使える
- OOPがKで50% PotをBetすると、IPが通常のfull raiseをするにはAll-inが必要
- KをQ/Aと同じsizeへ混ぜるため、IPは50% Betを見ただけではOOPのhandを特定できない

という効果があります。

### なぜ中間handのKをBetするのか

Kだけを見れば、Qに勝ち、KとTieし、Aに負ける中間handです。しかしrange戦略として見ると、Kには次の役割があります。

1. QのBluffとAのValueの間を埋め、IP(K)のCall/Foldを無差別にする。
2. IPのBluff Raiseに対してAだけがCallするrange構造を作る。
3. Check後にIPが使える約92.93% Potより先に、50% Potで価格を設定する。

このため、均衡は単純な`Q Bluff / K Check / A Value`ではなく、Q/K/Aを同じsizeへpoolします。

### Checking rangeの防御

Aを100% Betすると、OOPのCheck rangeから最上位handが消えます。Aを42.85% Checkへ残すことで、IPはOOP Check後も
無制限に攻撃できません。Block BetとChecking-range defenseは別々ではなく、root range全体を分割する同じ均衡条件から
同時に生じます。

### RaiseがBet rangeを決める

IPにCall/Foldだけを許すゲームでは、KをBlock Betへ入れる必要性は同じ形では現れません。このStudyではIPが
All-in Bluff Raiseできるため、OOPのBet rangeはCallへの防御だけでなくRaiseへの防御も必要です。その2種類の
無差別条件が`1:3:6`を決めます。

---

## Solverによる再現結果

Solverには、前提とした50%および解析から導いた92.9339%を含め、10/20/33/75/90/95%も比較候補として
追加しています。表のExploitabilityは、これらの候補からなる有限actionゲームに対する値です。

| 指標 | 結果 |
|---|---:|
| IP EV | 0.530533939 |
| OOP EV | 0.469466061 |
| Exploitability | `7.4671e-6` |

Rootでは50% Pot、OOP Check後では92.9339% Potが主要sizeになりました。92.9339%付近のAction EV曲線は浅いため、
有限iterationの平均戦略は90/92.9339/95%へ一部の頻度を分散しています。

- [Strategy Viewer](../../public/studies/akq_symmetric_variable_size/strategy_viewer.html)
- [計算条件](../../public/studies/akq_symmetric_variable_size/resolved_config.json)

### 再現方法

```bash
toy-poker run configs/experiments/study_akq_symmetric_variable_size_dcfr.toml
```

解析値は[`analytic.py`](../../src/toy_poker/games/integer_range_betting/analytic.py)で計算し、on-pathの
無差別条件とsizeの一階条件をテストしています。
