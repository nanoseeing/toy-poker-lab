# AKQJゲーム① 2 StreetのBluff戦略

## ルール

| 項目 | 内容 |
|---|---|
| OOPハンド | K（100%） |
| IPハンド | A / Q / J（各1/3） |
| Street | 2 Street |
| 初期Pot | 1 |
| 有効Stack | 4 |
| 許可アクション | Check、Pot Bet、Call、Fold、All-in Raise |
| 勝敗判定 | A > K > Q > J |
| Street遷移 | Check–CheckまたはBet–Callで同じhandのまま次streetへ進む |
| 利得計算方法 | 初期Potをデッドマネーとし、ゲーム終了時の両者の利得合計は1 |

stack 4では2-street geometric fractionが1なので、1st streetで1、Call後のpot 3へ2nd streetで3を
betするとちょうどAll-inになります。

---

## 最適戦略

### 均衡戦略

| 局面 | 戦略 |
|---|---|
| OOP(K)、各street先頭 | Check 100% |
| IP(A)、1st street | Pot Bet 100% |
| IP(Q/J)、1st street | Pot Bet 62.5% / Check 37.5% |
| OOP(K)、1st pot betに直面 | Call 50% / Fold 50% |
| IP(A)、1st Bet–Call後 | All-in 100% |
| IP(Q/J)、1st Bet–Call後 | All-in 40% / Check 60% |
| OOP(K)、river All-inに直面 | Call 50% / Fold 50% |

Q/Jはそれぞれ、最初のrangeの`62.5% × 40% = 25%`を最終streetまでBluffします。

### EV

| プレイヤー | EV |
|---|---:|
| IP | 0.75 |
| OOP | 0.25 |
| 合計 | 1.00 |

### 導出方法

#### 戦略の形をhand・street別に整理

| street・局面 | プレイヤー・hand | 比較するaction | 結論 |
|---|---|---|---|
| 各street先頭 | OOP(K) | Check / Bet | Check 100% |
| 1st street、OOP Check後 | IP(A) | Check / Pot Bet | Pot Bet 100% |
| 1st street、OOP Check後 | IP(Q/J) | Check / Pot Bet | 両actionを混合 |
| 1st Pot Betに直面 | OOP(K) | Fold / Call | 両actionを混合 |
| 2nd street、Bet–Call後 | IP(A) | Check / All-in | All-in 100% |
| 2nd street、Bet–Call後 | IP(Q/J) | Check / All-in | 両actionを混合 |
| 2nd-street All-inに直面 | OOP(K) | Fold / Call | 両actionを混合 |

#### 各handの役割

- OOPのKはAに負け、Q/Jに勝つBluff catcherです。先にBetするとAだけにCallされやすく、Polarな
  Value/Bluff構成を作れないため、各streetでCheckします。
- IPのAは全てのKに勝つ唯一のValue handなので、両streetで100% Betします。
- Q/JはshowdownでKに勝てないため、Checkの利得が0になる枝では同価値のBluff候補です。

QとJは同じshowdown valueを持つため、個別の割当は非一意です。対称解として同じ頻度を割り当てます。

#### 最終streetのBluff比

AのValue massを1とすると、Q/Jの最終barrelは各0.25なので、総Bluff massは0.5です。

$$
\text{value:bluff}=1:0.5=2:1
$$

pot-sized river betの理論比と一致し、OOPは50% Callします。

最終streetへ到達したQ/JがAll-inする条件付き頻度を $`t`$ とします。1st streetでBetした各Air massは
0.625、最終streetに必要な総Bluff massは0.5なので、

$$
2\times0.625\times t=0.5
\quad\Rightarrow\quad
t=0.4
$$

です。これが「1st streetで入れたBluffのうち40%だけをbarrelする」の正確な由来です。

#### 1st streetのBluff頻度

OOPが1st streetをCallした後、riverでFoldすれば利得は`-1`、CallしてAに負ければ`-4`です。
Aに対する期待値は、riverでCall/Foldを半分ずつ選ぶので、

$$
\frac{1}{2}(-1)+\frac{1}{2}(-4)=-2.5
$$

です。一方、Q/Jに対してはriver Checkでも、river BluffへCall/Foldを半分ずつ選んでも期待値は`+2`です。
OOPの1st Callを無差別にする総Bluff massを $`x`$ とすると、

$$
-2.5+2x=0 \Rightarrow x=1.25
$$

Q/Jへ均等配分すると、

$$
\frac{1.25}{2}=0.625
$$

になります。early streetでは最終barrelに残らないgive-up Bluffも含むため、最終streetより多くの
Bluffを開始できます。

最後にOOPの1st-street Call率を $`c_1`$ とします。Q/Jが1st streetでCheckすると利得0です。
1st BetがFoldされればBluffの利得は`+1`、Callされれば、2nd streetでCheckしても均衡頻度でAll-inしても
利得は`-1`です。したがって1st-street Bluffの期待利得は、

$$
EV_{bluff}=(1-c_1)(1)+c_1(-1)=1-2c_1
$$

です。Checkの0と等置すると$`c_1=1/2`$となり、ソルバーでも50%へ収束します。

Bet range内でOOPの期待利得が0、各Bluffの期待利得も0であり、両者の利得合計が1なので、Aの利得は
Value mass 1とBluff mass 1.25の合計$`2.25`$になります。IPはAを1/3で持つため、range全体では
$`2.25/3=0.75`$です。

---

## ポーカーにおける概念理解

### 1 StreetとのEV比較

同じK vs AQJ、stack 4のAll-in-only 1-streetゲームでは`IP EV = 0.6`です。2 street pot bettingでは、

$$
EV_{IP}=0.75,\qquad EV_{OOP}=0.25
$$

となります。future streetがIPへ「今betして、Callされた後にbarrelまたはgive upを選ぶ」権利を与え、
Polar側のEQRを大きくします。

このゲームはFuture streetのOption valueとGeometric bettingを純粋に示します。Early streetでは、
最終StreetまでBarrelしないGive-up BluffもBet rangeへ入るため、最終Streetより多くのBluffを開始できます。

---

## Solverによる再現結果

| 指標 | 結果 |
|---|---:|
| IP EV | 0.749999998 |
| OOP EV | 0.250000002 |
| Exploitability | `3.5914e-6` |

- [公開Report](../../public/results/akqj_two_street/report.md)
- [計算条件](../../configs/experiments/akqj_two_street_stack_4_cfr_plus.toml)

### 再現方法

```bash
toy-poker run configs/experiments/akqj_two_street_stack_4_cfr_plus.toml
```
