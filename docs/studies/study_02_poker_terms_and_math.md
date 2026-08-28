# 基礎② ポーカー用語と計算

この用語集は、各toyゲームの数式、Strategy Viewer、実戦的な読み替えで用語を同じ意味に揃えるための
基準です。純粋戦略、混合戦略、Nash均衡、無差別条件は先に
[ゲーム理論の基本用語](study_01_game_theory_basics.md)を参照してください。

## EV（Expected Value、期待値）

EVは、起こり得る結果の利得を、その結果が起こる確率で重み付けした平均です。結果 $i$ の確率を
$p_i$、利得を $x_i$ とすると、

$$
EV=\sum_i p_i x_i
$$

です。例えば、50%で2を得て50%で1を失う賭けのEVは
$0.5\times2+0.5\times(-1)=0.5$です。

このプロジェクトのViewerは**current-node基準**を使います。現在までに投入したチップは埋没費用なので、
root基準の利得EVに自分の既投入額を足し戻します。現在potが $P$ なら、両者のcurrent-node EVの合計は
$P$です。range全体のEVは、そのnodeにおける条件付きrange weight $w_h$ を使って、

$$
EV_{range}=\sum_h w_h EV_h,\qquad \sum_h w_h=1
$$

と計算します。

## EQ（Equity）

EQは、これ以上bettingせずshowdownした場合に受け取るpotの期待割合です。

$$
EQ=P(Win)+\frac12P(Tie)
$$

相手のhand $v$ に条件付き確率 $q_v$ があり、自分のhandを $h$ とすると、

$$
EQ(h)=\sum_v q_v\left[
\mathbf{1}(h>v)+\frac12\mathbf{1}(h=v)
\right]
$$

です。自range全体のEQは $EQ_{range}=\sum_h w_h EQ(h)$ です。EQはshowdownの取り分だけを測り、
将来のBet、Fold equity、Positionによる選択権は含みません。

## EQR（Equity Realization、Equity実現率）

EQRは、showdown EQが示すpot shareに対して、実際の戦略EVをどれだけ実現したかを表します。現在potを
$P$ とすると、Viewerの計算は

$$
EQR=\frac{EV}{P\times EQ}
$$

です。表示時は100倍して百分率にします。

- $EQR=100\%$: EQどおりのpot shareを実現した
- $EQR>100\%$: Fold equityや有利なBet選択によってEQ以上のEVを得た
- $EQR<100\%$: Foldを強いられるなどしてEQの一部しか実現できなかった

$EQ=0$ のときは分母が0なのでEQRを定義せず、Viewerでは`—`と表示します。例えばpot 1、EQ 40%、
EV 0.30なら、$EQR=0.30/(1\times0.40)=75\%$です。

## Pot odds

相手が現在pot $P$ に $B$ をBetし、自分が $B$ をCallする場面を考えます。Call後の最終potは
$P+2B$、Callに必要な追加投資は $B$ です。必要EQは

$$
EQ_{break-even}=\frac{B}{P+2B}
$$

です。これはCall EVを

$$
EV(Call)=EQ\,(P+B)-(1-EQ)B
           =EQ\,(P+2B)-B
$$

と書き、$EV(Call)=0$ と置けば得られます。pot-size Bet、すなわち $B=P$ なら必要EQは
$P/(3P)=1/3$です。

## MDF（Minimum Defense Frequency、最低防御頻度）

MDFは、相手の0 equity BluffがBetだけで自動利益を得ないために、range全体で最低限Continueする頻度です。
現在pot $P$ にBet $B$ を受け、Continue率を $d$ とすると、BluffのEVは

$$
EV(Bluff)=(1-d)P-dB
$$

です。これを0にすることで、

$$
MDF=d=\frac{P}{P+B}
$$

を得ます。Betをpot比 $e=B/P$ で表せば、$MDF=1/(1+e)$です。pot-size Betなら50%になります。
MDFは各handを同じ頻度で防御する規則ではなく、CallとRaiseを合わせたrange全体の基準です。

## Bluff:value比

最終streetで完全にpolarなrangeがpot $P$ に $B$ をBetする場合を考えます。相手のbluff catcherがCallした
とき、Bet range中のBluff比率を $q$ とすると、

$$
EV(Call)=q(P+B)-(1-q)B
$$

です。CallとFoldを無差別にする $EV(Call)=0$ から、

$$
q=\frac{B}{P+2B}
$$

を得ます。したがって、Bet range全体に占めるBluffの割合は $B/(P+2B)$、比率表記では

$$
Bluff:Value=B:(P+B)
$$

です。pot-size Betなら $Bluff:Value=1:2$、すなわちBluffはBet rangeの1/3です。このBluff比率と、
bluff catcher側のMDFは別の量です。

## Bet sizing

Bet sizeはValueが得るCall額と、Bluffが負担するriskを同時に変えます。$e=B/P$ と置くと、最終streetの
主要な基準は次の表になります。

| Bet size | 必要EQ $e/(1+2e)$ | MDF $1/(1+e)$ | Bluff:Value $e:(1+e)$ |
|---:|---:|---:|---:|
| 50% pot | 25.00% | 66.67% | 1:3 |
| 75% pot | 30.00% | 57.14% | 3:7 |
| 100% pot | 33.33% | 50.00% | 1:2 |
| 150% pot | 37.50% | 40.00% | 3:5 |

大きいsizeほど相手の必要EQを上げ、MDFを下げ、Bet rangeへ許容されるBluff比率を増やします。

## Geometric Bet

Geometric Betは、残り全streetで同じpot比率をBetし、Bet–Callが続いたとき最終streetまでに実効stackを
ちょうど使い切るsizeです。現在potを $P_0$、実効stackを $S$、残りstreet数を $n$、各streetのBetを
その時点のpotの $e$ 倍とします。

1回Bet–Callされるたびpotは $1+2e$ 倍になるため、$n$ street後のpotは

$$
P_n=P_0(1+2e)^n
$$

です。実効stackを全て投入すると最終potは $P_0+2S$ なので、

$$
P_0(1+2e)^n=P_0+2S
$$

を解いて、

$$
e=\frac{\left(1+\frac{2S}{P_0}\right)^{1/n}-1}{2}
$$

を得ます。$P_0=1$、$S=4$、$n=2$ なら $e=(\sqrt9-1)/2=1$、つまり両streetでpot-size Betです。

## Range構造

### Polarization

強いValueとshowdown valueのないBluffを中心にBetし、中間のbluff catcherをCheckへ残す構造です。
polar rangeは大きいsizeを使いやすく、相手の中間rangeへ大きな圧力をかけます。

### Merged rangeとThin value

Merged rangeはnut級だけでなく、中上位のhandも弱いhandからCallを受けるためにBetする構造です。
Thin valueは、相手のContinue rangeに僅かな優位を持つValue Betを指します。

### Checking range

Checkはgive-upだけではありません。強いhandを残すことで相手のBetに対するCall・Raiseを守り、
中間handのEQRを改善します。nut級の一部Checkはrange protectionやtrapとして働きます。

### Range advantageとNut advantage

Range advantageはrange全体の平均EQに関する優位、Nut advantageは最上位handの密度に関する優位です。
平均EQが近くてもNut advantageが大きい側はpolarな大sizeを使いやすくなります。

## Bet、Raise、Block bet

RaiseはValueとBluffの比率だけでなく、相手のThin valueやBlock betのEVも変えます。Block betは中間handが
自分で小さく価格を決めるBetです。Raiseに直面してもrange全体が過剰にFoldしないよう、強いhandや
RaiseへのContinueを同じBet rangeへ配分します。

## Position

IPはOOPのCheckを観察してからBetまたはCheckを選べます。この追加情報と最後に行動できる権利により、
ValueとBluffを効率よく配分し、一般にOOPより高いEQRを得やすくなります。OOPは強いhandをChecking rangeへ
残すことで、IPのBetに対して防御します。

## Future streetとDynamic equity

Future streetは、現在のaction後に意思決定が残っていることです。現在のBetは即時のFold equityに加え、
次streetで再びBetできるoption valueを作ります。

Dynamic equityは、将来のpublic cardによってhand strengthやEQが変化する性質です。あるrunout $r$ の確率を
$p_r$、そのrunout後のEQを $EQ_r$ とすると、現在のEQは $\sum_r p_r EQ_r$ ですが、各 $EQ_r$ の分布と、
runoutごとに異なる将来actionがEVを左右します。

## Blocker

Blockerは、自分のcardによって相手が特定のcomboを持てる確率が下がる効果です。相手のValue comboを減らす
cardはBluff候補に、相手のBluff comboを減らすcardはbluff catcherのFold候補になりやすい、という形で
range構築に影響します。

## Solver数値の読み方

- Exploitabilityは元ゲームでのbest responseに対する弱さです。
- Node lock使用時のconstrained Nash gapは、lockを破らない戦略集合内の収束指標です。
- 到達確率が低いoff-path戦略は、on-path戦略より収束が遅い場合があります。
- Action EVが等しいhandやactionの混合頻度は非一意になり得ます。
- 個別rankの色だけでなく、条件付きrange、node頻度、EVを一緒に確認します。
