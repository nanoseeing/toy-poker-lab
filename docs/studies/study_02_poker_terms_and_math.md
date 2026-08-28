# 基礎② ポーカー用語と計算

この文書は、各toyゲームの数式と戦略を理解するために必要なポーカー用語を説明します。
行動戦略、Nash均衡、無差別条件、reachは先に
[ゲーム理論の基本用語](study_01_game_theory_basics.md)を参照してください。

---

## ゲーム状態と記号

同じ「pot-size Bet」でも、現在potと残りstackによって戦略的な意味は変わります。この文書では、特記しない限り
次の記号を使います。

| 記号・用語 | 意味 |
| --- | --- |
| $`P`$ | アクション前の現在pot |
| $`B`$ | 現在potに対して新たにBetする額 |
| $`C`$ | 相手のBetまたはRaiseにCallするための追加額 |
| $`S`$ | 両者の残りstackの小さい方であるeffective stack |
| 投入済み額 | 現在のnodeまでに各プレイヤーがpotへ入れた額 |
| $`SPR`$ | Stack-to-Pot Ratio。effective stackを現在potで割った値 $`S/P`$ |
| $`e`$ | Bet額のpot比 $`B/P`$ |

Raiseでは、Raise後の合計投入額と、直前の投入額との差が追加投資額です。minimum raise、stack上限、All-inにより
実際に選べるRaise sizeが制限されるため、単純なBetの式を使うときは $`B`$ と $`C`$ の意味を確認します。

### handとrank

handは、プレイヤーに配られたprivate cardまたはその組合せです。AKQゲームならA、K、Qがhandに当たります。
rankはhandの強さを比較するための値です。数値型toyゲームではhand $`h`$ に数値rank $`r(h)`$ を割り当て、
$`r(h_1)>r(h_2)`$ なら $`h_1`$ の勝ちとします。したがって、プレイヤーが持つのはhandであり、rankは
そのhandの属性です。

数値型ゲームのStrategy Viewerでは、1〜$`N`$ のhandをrank順に並べるため、画面上の識別子として`rank`を
使用しています。

---

## rangeとconditional range

### range

rangeは、あるプレイヤーが持ち得るhandと、その確率またはcomboの重みの分布です。hand $`h`$ の重みを
$`w(h)`$ とすると、正規化されたrangeでは、

$$
w(h)\geq0,
\qquad
\sum_h w(h)=1
$$

です。実際のHold'emではカード除去により両者のcomboは独立ではありません。このプロジェクトの01-gameでは、
設定されたOOP/IPのhand分布から独立に配布します。

### conditional rangeとBayes更新

action履歴 $`H`$ を観察すると、その履歴を選びやすいhandの相対的なweightが上がります。rootのprior rangeを
$`w_0(h)`$、hand $`h`$ が履歴 $`H`$ まで進む確率を $`L(H\mid h)`$ とすると、current nodeのconditional rangeは、

$$
w(h\mid H)=
\frac{w_0(h)L(H\mid h)}
{\sum_{h'}w_0(h')L(H\mid h')}
$$

です。これはBayes更新です。本教材のnode別戦略、EQ、EVは、このconditional rangeを基準に計算します。
Strategy Viewerでは、同じ分布をrange heightとconditional rangeの表示に使います。

### Blockerとカード除去

Blockerは、自分のカードによって相手が特定のcomboを持てる確率が下がる効果です。重要なのは
カード自体の絶対的な強さではなく、そのカードを知った後に相手のconditional rangeがどう変わるかです。

- Bluff候補：相手のCall・Raise用Valueをブロックし、Fold候補をできるだけアンブロックするカードが有利
- Bluff catcher：相手のValueをブロックし、Bluffをできるだけアンブロックするカードが有利

---

## EV、EQ、EQR

### EV（Expected Value、期待値）

EVは、起こり得る結果の利得を、その結果が起こる確率で重み付けした平均です。結果 $`i`$ の確率を $`p_i`$、
利得を $`x_i`$ とすると、

$$
EV=\sum_i p_i x_i
$$

です。例えば、50%で2を得て50%で1を失う賭けのEVは、
$`0.5\times2+0.5\times(-1)=0.5`$です。

#### Root基準とcurrent-node基準

本教材では、中間nodeのEVを**current-node基準**で表します。現在までに投入した自分のチップは、現在の判断では
埋没費用です。root基準の利得EVを $`EV_{root}`$、現在までの自分の投入済み額を $`c_i`$ とすると、

$$
EV_{current}=EV_{root}+c_i
$$

です。現在potが $`P`$ なら、両者のcurrent-node EVの合計は $`P`$ になります。range全体のEVは、current nodeの
conditional range weightを使って、

$$
EV_{range}=\sum_h w(h\mid H)EV_h
$$

と計算します。異なるノードのEVを比較するときは、同じ基準と同じpotを使っているかを確認します。

### EQ（Equity）

EQは、これ以上Betせずshowdownした場合に受け取るpotの期待割合です。以後、Equityは全てEQと表記します。

$$
EQ=\Pr(Win)+\frac{1}{2}\Pr(Tie)
$$

相手hand $`v`$ の条件付き確率を $`q(v)`$、自分のhandを $`h`$ とすると、

$$
EQ(h)=\sum_v q(v)
\left[
\mathbf{1}(h>v)+\frac{1}{2}\mathbf{1}(h=v)
\right]
$$

です。自分のrange全体のEQは、

$$
EQ_{range}=\sum_h w(h\mid H)EQ(h)
$$

です。EQはshowdownの取り分だけを測り、将来のBet、Fold equity、Positionによる選択権は含みません。

EQ分布は、range内の各handが相手のrangeに対して持つEQの分布です。ViewerではhandをEQの小さい順に
並べ、横軸を「そのEQ以下のhandを持つ累積頻度」、縦軸をEQとして表示します。

### EQR（Equity Realization）

EQRは、showdown EQが示すpot shareに対して、実際の戦略EVをどれだけ実現したかを表します。current-nodeの
potを $`P`$ とすると、本教材では、

$$
EQR=\frac{EV}{P\times EQ}
$$

です。

- $`EQR=1`$（100%）：EQどおりのpot shareを実現した
- $`EQR>1`$（100%超）：Fold equityや有利なBet選択によってEQ以上のEVを得た
- $`EQR<1`$（100%未満）：Foldを強いられるなどしてEQの一部しか実現できなかった

$`EQ=0`$ では定義できず、Viewerでは`—`と表示します。EQが非常に小さいhandでは分母が小さいため、EQRが
極端に大きくなることがあります。EQRは**EQに対するEVの比率**であり、EQRが高いhandほど絶対EVも高いとは
限りません。

例えばpot 1、EQ 40%、EV 0.30なら、$`EQR=0.30/(1\times0.40)=0.75`$、すなわち75%です。

---

## 一つのBetを解く数学

### Pot odds

相手が現在pot $`P`$ に $`B`$ をBetし、自分が同額 $`C=B`$ をCallする場面を考えます。Call後の最終potは
$`P+2B`$、Callに必要な追加投資は $`B`$ です。Call側の損益分岐EQは、

$$
EQ_{call}=\frac{B}{P+2B}
$$

です。これはCall EVを、

$$
EV(Call)=EQ(P+B)-(1-EQ)B
=EQ(P+2B)-B
$$

と書き、$`EV(Call)=0`$ と置けば得られます。pot-size Bet、すなわち $`B=P`$ なら損益分岐EQは1/3です。

future streetが残る場合、raw EQを全て実現できるとは限らないため、Pot oddsだけでCallを決めることはできません。

### Fold equityとAlpha

Fold equityは、自分のBetやRaiseによって相手がFoldすることで得られるEVです。
showdown EQが0で、CallされたらBet額 $`B`$ を失うPure bluffを考えます。相手のFold率を $`F`$ とすると、

$$
EV(Bluff)=FP-(1-F)B
$$

です。Bluffの損益分岐Fold率であるAlpha $`\alpha`$ は、

$$
\alpha=\frac{B}{P+B}
$$

です。Alphaは、EQが0のBluffが即時利益を得るために必要なFold率を表します。

Bluffしない場合にもCheckによるshowdown EVやfuture-street EVがあるなら、本当の無差別条件は
$`EV(Bluff)=EV(Check)`$ です。その場合、Alphaだけでは最適なBluff頻度を決められません。

### MDF（Minimum Defense Frequency）

MDFは、相手の0 EQ BluffがBetだけで自動利益を得ないように、range全体でContinueする頻度です。
Continue率を $`d`$ とすると、

$$
EV(Bluff)=(1-d)P-dB
$$

なので、Bluffを0EVにする防御頻度は、

$$
MDF=d=\frac{P}{P+B}=1-\alpha
$$

です。Betをpot比 $`e=B/P`$ で表せば、$`MDF=1/(1+e)`$です。pot-size Betなら50%になります。

MDFを使うときは次の条件に注意します。

- EQが0のBluffとgive-upを無差別にするrisk/reward上の基準である
- 各handを同じ頻度で防御する規則ではない
- CallとRaiseを合わせてContinueと数える
- BluffにEQや正のCheck EVがあるfuture streetでは、実際の均衡Continue率と一致するとは限らない
- 相手が均衡よりBluff不足なら、実戦の最適反応はMDFより多くFoldし得る

### Value、Bluff、Bluff catcher

| 役割 | 意味 |
| --- | --- |
| Value Bet | 弱いhandから十分にCallまたはRaiseされることで、Checkより高いEVを得るBet |
| Thin value | 相手のContinue rangeに対する優位が小さく、Value Betの中でも境界に近いhand |
| Pure bluff | Callされた場合のshowdown EQがなく、主にFold equityからEVを得るBet |
| Semi-bluff | 現在も一部EQを持つか、将来強いhandへ改善でき、Foldとshowdownの両方からEVを得るBet |
| Bluff catcher | 相手のValueには負けるがBluffには勝ち、主にCallとFoldを比較する中間hand |

ValueやBluffはカード固有の分類ではなく、相手のrange、size、street、選んだ経路に対する役割です。同じhandが
小さいsizeではValue Bet、大きいsizeではCheckになることもあります。

### Bluff:Value比

最終streetで完全にPolarなrangeがpot $`P`$ に $`B`$ をBetする場合を考えます。Bet range中のBluff割合を
$`q`$ とすると、相手のBluff catcherがCallした場合のEVは、

$$
EV(Call)=q(P+B)-(1-q)B
$$

です。CallとFoldを無差別にする $`EV(Call)=0`$ から、

$$
q=\frac{B}{P+2B}
$$

を得ます。混同しやすい三つの表記は次のとおりです。

| 表す量 | 式 | Pot-size Bet |
| --- | --- | --- |
| Bet range中のBluff割合 | $`B/(P+2B)`$ | $`1/3`$ |
| Bluff:Value | $`B:(P+B)`$ | $`1:2`$ |
| Value:Bluff | $`(P+B):B`$ | $`2:1`$ |

このBluff割合はBet側のrange構成、MDFはCall側の継続頻度であり、別の量です。

### Bet size

Bet sizeは、Valueが得るCall額とBluffが負担するriskを同時に変えます。$`e=B/P`$ と置くと、最終streetの
主要なリスク・リワード基準は次の表になります。

| Bet size | Call側の損益分岐EQ $`e/(1+2e)`$ | MDF $`1/(1+e)`$ | Bluff:Value $`e:(1+e)`$ |
| ---: | ---: | ---: | ---: |
| 50% pot | 25.00% | 66.67% | 1:3 |
| 75% pot | 30.00% | 57.14% | 3:7 |
| 100% pot | 33.33% | 50.00% | 1:2 |
| 150% pot | 37.50% | 40.00% | 3:5 |

大きいsizeほどCall側の損益分岐EQを上げ、MDFを下げ、均衡Bet rangeへ許容されるBluff比率を増やします。
ただし、どのsizeが最大EVになるかは、両者のrange、Raise、残りstack、future streetにも依存します。

---

## handの役割とrange構造

### Linear、Merged、Polar、Condensed

これらは明確に二分される分類というより、range形状を説明する連続的な概念です。

| range構造 | 典型的な構成 |
| --- | --- |
| Linear | 最強handから一定の強さまでを連続的に含み、弱いBluffをほとんど含まない |
| Merged | Nut級だけでなく中上位handもValueやequity denialのため同じBet rangeに含める |
| Polar | 強いValueと弱いBluffをBetし、中間のBluff catcherをCheckへ残す |
| Condensed | Nut級と完全なairが少なく、中間強度へ集中している |

Polar rangeは大きいsizeを使いやすく、相手の中間rangeへ強い圧力をかけます。Merged rangeはより広いhandから
Valueを取りやすい小さいsizeと結びつくことが多いですが、実際の最適sizeは相手のContinue戦略で決まります。

### CappedとUncapped

Capped rangeは、過去のactionによって最上位handをほとんど持てないrangeです。Uncapped rangeは、現在の
lineでもNut級handを十分に持ち得ます。相手がCappedで自分がUncappedなら、大きいPolar Betを使いやすくなります。

### Range advantageとNut advantage

Range advantageは、両rangeのEQ distribution全体を比較した優位です。平均EQは重要な要約値ですが、同じ
平均EQでも分布の形は異なります。Nut advantageは、最上位のEQ領域にあるhandの強さと密度に関する優位です。

- Range advantage：広いrangeでValueを得る小中sizeと結びつきやすい
- Nut advantage：最大級sizeを支えるValueを多く持ち、polarizationしやすい

これは一般的な傾向であり、Raise、stack、future streetを含む完全なEV比較が最終判断になります。

### Checking range

Checkはgive-upだけではありません。強いhandを残すことで、相手のBetに対するCall・Raiseを守り、中間handの
EQRを改善します。Nut級の一部Checkは、相手が全rangeへ自動的にBetすることを防ぐrange protectionやtrapとして
働きます。

### Block bet、Raise、Range protection

Block betは、中間handが小さいsizeを使ってThin valueを取り、Check backされるEQを回収し、相手の大きいBetに
直面する頻度を変える戦略です。ただし相手はRaiseできるため、Betしただけでshowdown価格を保証できるわけでは
ありません。

Raiseは、ValueとBluffの比率だけでなく、相手のThin valueやBlock betのEVも変えます。Bet rangeがRaiseに対して
過剰にFoldしないよう、強いhandやRaiseへContinueできるhandを同じBet rangeへ配分します。

### Equity denial

Equity denialは、相手をFoldさせることで、そのhandが将来potを獲得する可能性を放棄させる価値です。自分より
弱いhandをFoldさせても、そのhandに将来逆転される確率を消せるためEVを得ることがあります。Fold equityが
「相手がFoldする確率と、そのとき得る即時EV」に注目するのに対し、equity denialは「Foldしたrangeが放棄した
showdown EQ」に注目します。同じFoldによって同時に生じる、関連した二つの見方です。

---

## Position、stack、future street

### Position

IPはOOPのCheckを観察してからBetまたはCheckを選べます。この追加情報とstreetで最後に行動する権利により、
ValueとBluffを効率よく配分し、一般にOOPより高いEQRを得やすくなります。OOPは強いhandをChecking rangeへ残し、
IPがCheck後に過剰なBetを行えないよう防御します。

OOPはOut of Position、IPはIn Positionの略です。以後はOOP/IPで統一します。

### Effective stackとSPR

Effective stackは、そのhandで両者が追加投入できる最大共通額です。SPRは、

$$
SPR=\frac{S}{P}
$$

です。SPRが小さいほど現在のBetでAll-inへ近づき、raw EQとPot oddsが直接EVへ反映されやすくなります。
SPRが大きいほどfuture streetのBet、Position、nut potential、Implied oddsが重要になります。

### Geometric Bet

Geometric Betは、残り全streetで同じpot比率をBetし、Bet–Callが続いたとき最終streetまでにeffective stackを
ちょうど使い切るsizeです。現在potを $`P_0`$、effective stackを $`S`$、残りstreet数を $`n`$、各streetのBetを
その時点のpotの $`e`$ 倍とします。

1回Bet–Callされるたびpotは $`1+2e`$ 倍になるため、$`n`$ street後のpotは、

$$
P_n=P_0(1+2e)^n
$$

です。effective stackを全て投入すると最終potは $`P_0+2S`$ なので、

$$
P_0(1+2e)^n=P_0+2S
$$

を解いて、

$$
e=\frac{\left(1+\frac{2S}{P_0}\right)^{1/n}-1}{2}
=\frac{(1+2SPR_0)^{1/n}-1}{2}
$$

を得ます。$`P_0=1`$、$`S=4`$、$`n=2`$ なら $`e=(\sqrt{9}-1)/2=1`$、つまり両streetで
pot-size Betです。

Geometric sizeはstackを均等なpot比で配分する基準です。常に最適とは限りませんが、完全なPolar rangeが
複数streetでValueとBluffを配分しながらAll-inを目指す問題では重要な候補になります。

### Future streetとOption value

Future streetは、現在のaction後にも意思決定が残っていることです。現在のBetは即時のFold equityに加え、
次streetでValue BetやBluffを選び直せるoption valueを作ります。逆にCheckは、potを小さく保つだけでなく、
次streetで相手のアクションを観察してから戦略を分岐させる権利を残します。

### Dynamic equity

Dynamic equityは、将来のpublic cardによってhand strengthやEQが変化する性質です。runout $`r`$ の確率を
$`p_r`$、その後のEQを $`EQ_r`$ とすると、そのままshowdownまで進めた場合の現在EQは、

$$
EQ=\sum_r p_r EQ_r
$$

ですが、同じ現在EQでもrunout別の分布と将来actionが異なればEVとEQRも異なります。

このプロジェクトのhandが固定された2-street gameには新しいpublic cardがないため、future-street option valueはありますが、
カードによるdynamic equityはありません。この二つは区別します。

### Implied oddsとReverse implied odds

Implied oddsは、将来強いhandへ改善したときに追加で得られるチップを含めたCallの価値です。Reverse implied oddsは、
改善しても相手のさらに強いhandへ追加チップを失う危険です。どちらもraw Pot oddsには含まれず、future streetの
戦略を通してEVとEQRへ現れます。

---

## ソルバーとStrategy Viewerの数値を読む順序

1. 現在pot、effective stack、投入済み額、手番を確認する。
2. Historyとnode reachを確認する。
3. 両者のconditional rangeと`Range retained`を確認する。
4. Range EV、EQ、EQRを比較する。
5. `Node strategy`でrange全体のアクション頻度を見る。
6. hand別戦略、`Action EV`、マンハッタングラフで混合の境界を見る。
7. Exploitabilityとlow reach警告を確認する。

- Exploitabilityは元ゲームでの最適反応に対する戦略全体の弱さです。
- Node lock使用時のconstrained Nash gapは、lockを破らない戦略集合内の収束指標です。
- low reachのoff-path戦略は、on-path戦略より混合頻度が不安定な場合があります。
- Action EVが等しいhandやactionの混合頻度は非一意になり得ます。
- 個別handの色だけでなく、conditional range、node頻度、EVを一緒に確認します。

---

## 参考資料

- [GTO Wizard: What is Equity in Poker?](https://blog.gtowizard.com/what-is-equity-in-poker/)
- [GTO Wizard: Equity Realization](https://blog.gtowizard.com/equity-realization/)
- [GTO Wizard: MDF & Alpha](https://blog.gtowizard.com/mdf-alpha/)
- [GTO Wizard: Range Morphology](https://blog.gtowizard.com/range-morphology/)
- [GTO Wizard: The Power of the Hypergeometric Bet](https://blog.gtowizard.com/the-power-of-the-hypergeometric-bet/)
