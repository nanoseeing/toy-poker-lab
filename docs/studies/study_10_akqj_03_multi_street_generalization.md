# AKQJゲーム③ Multi-streetへの一般化

## ルール

| 項目 | 内容 |
|---|---|
| OOPハンド | 中間のBluff catcher |
| IPハンド | Nutsと複数のAirからなるPolar range |
| Street | $n$ Street |
| 初期Pot | 1 |
| 有効Stack | $S$ |
| 許可アクション | OOPはCheck、Call、Fold。IPはCheck、Bet |
| アクション制約 | OOPは各Streetで先に行動し、Bet不可。両者Raise不可。全Streetで同じPot比率 $e$ を使用 |
| 勝敗判定 | Nuts > Bluff catcher > Air |
| Street遷移 | bet-callまたはcheck-check後、同じprivate rankで次streetへ進む |
| 利得計算方法 | 初期Potをデッドマネーとし、両者の終端利得の合計は1 |

AKQのK vs AQが1 street、AKQJのK vs AQJが2 streetの最小例です。3 street以上では、
必要なbluff候補を表現するためにJ、Tのような弱いrankを追加できます。

---

## 最適戦略

### 均衡戦略

| 対象 | 均衡条件 |
|---|---|
| 各StreetのBet size | $e_n=((1+2S)^{1/n}-1)/2$ |
| 最終StreetのBluff:Value比 | $e:(1+e)$ |
| 最終StreetのOOP Call率 | $1/(1+e)$ |
| Early StreetのBluff | 最終StreetまでBarrelするBluffと途中でGive upするBluffをBackward inductionで配分 |

### EV

| プレイヤー | EV |
|---|---:|
| IP | $S$、$n$、Value / Bluff候補の初期分布に依存 |
| OOP | $1-EV_{IP}$ |
| 合計 | 1 |

### 導出方法

#### Geometric sizingの一般式

毎streetで、そのstreet開始時のpotに対して同じ比率 $e$ をbetすると、bet-call後のpotは
$(1+2e)$ 倍になります。$n$ 回のbet-callでstack $S$を使い切る条件は、

$$
1+2S=(1+2e)^n
$$

したがって、geometric bet fractionは、

$$
e_n=\frac{(1+2S)^{1/n}-1}{2}
$$

です。$S=4,n=2$なら $e_2=1$、つまりpot betを2回行うとちょうどAll-inになります。

#### 最終Streetで必ず成立する比率

最終streetのbet額を $eP$ とすると、OOPのpot oddsから、bet rangeに必要な
bluff:value比は、

$$
\frac{\text{bluff}}{\text{value}}=\frac{e}{1+e}
$$

OOPがbluffを無差別にするCall率、すなわちMDFは、

$$
\operatorname{MDF}=\frac{1}{1+e}
$$

です。pot betならbluff:valueは1:2、MDFは50%です。

#### 前のStreetほどBluff候補が多くなる理由

early streetのbluffには、現在のFold equityに加えて、Call後に次streetで再びbluffする選択肢があります。
そのため、最終streetまでbarrelするbluffだけでなく、途中でgive upするbluffも最初のbet rangeへ入れられます。
K vs AQJの2 street pot-bet例では、J/Qはそれぞれ62.5%で1st streetをbetし、そのうち40%だけを
2nd streetでAll-inします。

一般の $n$ streetでも、後ろからpot oddsと無差別条件を解くbackward inductionを使います。ただし、
early-streetの正確なbluff量は $S$、$n$、range内のvalue/bluff候補数に依存し、最終streetの比率だけから
一意には決まりません。

---

## ポーカーにおける概念理解

- **Future street:** 追加streetはbluffを一度に使い切らず、段階的に選別する価値を生みます。
- **Geometric betting:** 複数streetで均等な圧力をかけながらriverでstackを使い切る基準です。
- **Equity realization:** polar側はpositionと将来のactionを利用し、nutsの価値とairのFold equityを実現します。

要点は次の3点です。

1. $n$ streetのgeometric fractionは $((1+2S)^{1/n}-1)/2$ です。
2. 最終streetのbluff:value比とMDFはpot oddsだけで決まります。
3. early-streetのbluff量はbackward inductionと利用可能なbluff候補数で決まります。

---

## Solverによる再現結果

この一般化Studyには独立したSolver runはありません。$n=1$はAKQゲーム①、$n=2,S=4$は
AKQJゲーム①・②の解析解とSolver結果で確認できます。

---

## その他備考

### Bluff候補が不足する場合

離散AKQ型ゲームでは、必要なEarly-street Bluff massがQだけでは足りないことがあります。J、Tなどの
Air rankを追加すると、

- 最終StreetまでBarrelするBluff
- 途中でGive upするBluff
- Off-pathのChecking rangeを守るrank

を別々に割り当てられます。追加したrankが同じShowdown valueを持つ場合、どのAir rankを使うかは
非一意になり得ます。
