# Polar toy game: multi-street generalization

> Status: `解析解あり`（sizeと最終street）・street別bluff量は`考察`

## ルール

| 項目 | 内容 |
|---|---|
| Street | $n$ street。public runoutなし |
| OOP range | 中間のbluff catcher |
| IP range | nutsと複数のair rankからなるpolar range |
| 初期pot / stack | pot 1、有効stack $S$ |
| 各streetの順序 | OOP Check → IP Bet/Check → OOP Call/Fold |
| Street遷移 | bet-callまたはcheck-check後、同じprivate rankで次streetへ進む |
| Size仮定 | 全streetで開始時potに対する同じ比率 $e$ を使用 |
| 利得 | 初期potをデッドマネーとし、終端利得の合計は1 |

AKQのK vs AQが1 street、AKQJのK vs AQJが2 streetの最小例です。3 street以上では、
必要なbluff候補を表現するためにJ、Tのような弱いrankを追加できます。

## Geometric sizingの一般式

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

## 最終streetで必ず成立する比率

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

## 前のstreetほどbluff候補が多くなる理由

early streetのbluffには、現在のFold equityに加えて、Call後に次streetで再びbluffする選択肢があります。
そのため、最終streetまでbarrelするbluffだけでなく、途中でgive upするbluffも最初のbet rangeへ入れられます。
K vs AQJの2 street pot-bet例では、J/Qはそれぞれ62.5%で1st streetをbetし、そのうち40%だけを
2nd streetでAll-inします。

一般の $n$ streetでも、後ろからpot oddsと無差別条件を解くbackward inductionを使います。ただし、
early-streetの正確なbluff量は $S$、$n$、range内のvalue/bluff候補数に依存し、最終streetの比率だけから
一意には決まりません。

## Bluff候補が不足する場合

離散AKQ型ゲームでは、必要なearly-street bluff massがQだけでは足りないことがあります。これは式の破綻ではなく、
rangeモデルの供給制約です。J、Tなどのair rankを追加すると、

- 最終streetまでbarrelするbluff
- 途中でgive upするbluff
- off-pathのchecking rangeを守るrank

を別々に割り当てられます。追加したrankは同じshowdown valueでもよく、card-removalを導入しない限り、
どのair rankを使うかは非一意になり得ます。

## ポーカー的解釈

- **Future street:** 追加streetはbluffを一度に使い切らず、段階的に選別する価値を生みます。
- **Geometric betting:** 複数streetで均等な圧力をかけながらriverでstackを使い切る基準です。
- **Equity realization:** polar側はpositionと将来のactionを利用し、nutsの価値とairのFold equityを実現します。
- **Dynamic equity:** このtoy gameにはrunoutがないため存在しません。実戦ではturn/river cardがrange advantageや
  blockerを変え、同じ式からずれることがあります。

## 要点

1. $n$ streetのgeometric fractionは $((1+2S)^{1/n}-1)/2$ です。
2. 最終streetのbluff:value比とMDFはpot oddsだけで決まります。
3. early-streetのbluff量はbackward inductionと利用可能なbluff候補数で決まります。
