# AKQJ game: K vs AQJ, two-street pot betting

> Status: `解析解あり`・`数値検証済み`

## ルール

| 項目 | 内容 |
|---|---|
| OOP | K 100% |
| IP | A、Q、Jを各1/3 |
| Street | 2 street、runoutなし |
| Pot / stack | 初期pot 1、stack 4 |
| 1st street | OOPから行動。Check、pot bet、Call/Fold、All-in raise |
| 2nd street | OOPから行動。残stackに対するAll-inはpot bet |
| Street遷移 | Check-checkまたはbet-callで同じrankのまま次streetへ進む |
| 利得 | 終端利得の合計は常に1 |

stack 4では2-street geometric fractionが1なので、1st streetで1、Call後のpot 3へ2nd streetで3を
betするとちょうどAll-inになります。

## 最適戦略

| 局面 | 戦略 |
|---|---|
| OOP(K)、各street先頭 | Check 100% |
| IP(A)、1st street | Pot bet 100% |
| IP(Q/J)、1st street | Pot bet 62.5% / Check 37.5% |
| OOP(K)、1st pot betに直面 | Call 50% / Fold 50% |
| IP(A)、1st bet-call後 | All-in 100% |
| IP(Q/J)、1st bet-call後 | All-in 40% / Check 60% |
| OOP(K)、river All-inに直面 | Call 50% / Fold 50% |

Q/Jはそれぞれ、最初のrangeの`62.5% × 40% = 25%`を最終streetまでbluffします。

## 純粋戦略になる部分

- OOPのKはAに負け、Q/Jに勝つbluff catcherです。先にbetするとAだけにCallされやすく、polarな
  value/bluff構成を作れないため、各streetでCheckします。
- IPのAは全てのKに勝つ唯一のvalue handなので、両streetで100% betします。
- Q/JはshowdownでKに勝てないため、Checkの利得が0になる枝では同価値のbluff候補です。

QとJにblocker差はなく、個別の割当は非一意です。対称解として同じ頻度を割り当てます。

## 最終streetのbluff比

Aのvalue massを1とすると、Q/Jの最終barrelは各0.25なので、総bluff massは0.5です。

\[
\text{value:bluff}=1:0.5=2:1
\]

pot-sized river betの理論比と一致し、OOPは50% Callします。

最終streetへ到達したQ/JがAll-inする条件付き頻度を $t$ とします。1st streetでbetした各air massは
0.625、最終streetに必要な総bluff massは0.5なので、

$$
2\times0.625\times t=0.5
\quad\Rightarrow\quad
t=0.4
$$

です。これが「1st streetで入れたbluffのうち40%だけをbarrelする」の正確な由来です。

## なぜ1st streetでは各62.5%なのか

OOPが1st streetをCallした後、riverでFoldすれば利得は`-1`、CallしてAに負ければ`-4`です。
Aに対する期待値は、riverでCall/Foldを半分ずつ選ぶので、

\[
\frac12(-1)+\frac12(-4)=-2.5
\]

です。一方、Q/Jに対してはriver Checkでも、river bluffへCall/Foldを半分ずつ選んでも期待値は`+2`です。
OOPの1st Callを無差別にする総bluff massを $x$ とすると、

\[
-2.5+2x=0 \Rightarrow x=1.25
\]

Q/Jへ均等配分すると、

\[
\frac{1.25}{2}=0.625=62.5\%
\]

になります。early streetでは最終barrelに残らないgive-up bluffも含むため、最終streetより多くの
bluffを開始できます。

最後にOOPの1st-street Call率を $c_1$ とします。Q/Jが1st streetでCheckすると利得0です。
1st betがFoldされればbluffの利得は`+1`、Callされれば、2nd streetでCheckしても均衡頻度でAll-inしても
利得は`-1`です。したがって1st-street bluffの期待利得は、

$$
EV_{bluff}=(1-c_1)(1)+c_1(-1)=1-2c_1
$$

です。Checkの0と等置すると$c_1=1/2$となり、solverでも50%へ収束します。

bet range内でOOPの期待利得が0、各bluffの期待利得も0なので、constant-sum 1より、Aの利得は
value mass 1とbluff mass 1.25の合計$2.25$になります。IPはAを1/3で持つため、range全体では
$2.25/3=0.75$です。

## 1 streetとのEV比較

同じK vs AQJ、stack 4のAll-in-only 1-streetゲームでは`IP EV = 0.6`です。2 street pot bettingでは、

\[
EV_{IP}=0.75,\qquad EV_{OOP}=0.25
\]

となります。future streetがIPへ「今betして、Callされた後にbarrelまたはgive upを選ぶ」権利を与え、
polar側のequity realizationを大きくします。

## Solverによる再現

| 指標 | 結果 |
|---|---:|
| Iterations | 100,000 |
| Exploitability | `3.5914e-6` |
| IP EV | 0.749999998 |
| OOP EV | 0.250000002 |

- [公開Report](../../public/results/akqj_two_street/report.md)
- [計算条件](../../configs/experiments/akqj_two_street_stack_4_cfr_plus.toml)

## 実戦への応用と限界

このゲームはfuture streetのoption valueとgeometric bettingを純粋に示します。ただしpublic cardが
増えないためdynamic equityはなく、QとJにもblocker差がありません。実際のturn/riverではrunout、
blocker、value handの強さ変化がbarrel選択を変えます。
