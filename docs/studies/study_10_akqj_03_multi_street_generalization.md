# AKQJゲーム③ Multi-streetへの一般化

## ルール

| 項目 | 内容 |
|---|---|
| OOPハンド | 中間のBluff catcher |
| IPハンド | Nutsと複数のAirからなるPolar range |
| Street | $`n`$ Street |
| 初期Pot | 1 |
| 有効Stack | $`S`$ |
| 許可アクション | OOPはCheck、Call、Fold。IPはCheck、Bet |
| アクション制約 | OOPは各Streetで先に行動し、Bet不可。両者Raise不可。全Streetで同じPot比率 $`e`$ を使用 |
| 勝敗判定 | Nuts > Bluff catcher > Air |
| Street遷移 | Bet–CallまたはCheck–Check後、同じprivate handで次streetへ進む |
| 利得計算方法 | 初期Potをデッドマネーとし、ゲーム終了時の両者の利得合計は1 |

AKQのK vs AQが1 street、AKQJのK vs AQJが2 streetの最小例です。3 street以上では、
必要なBluff候補を表現するためにJ、Tのような弱いhandを追加できます。

---

## 最適戦略

### 均衡戦略

| 対象 | 均衡条件 |
|---|---|
| 各StreetのBet size | $`e_{n}=((1+2S)^{1/n}-1)/2`$ |
| 最終StreetのBluff:Value比 | $`e:(1+e)`$ |
| 最終StreetのOOP Call率 | $`1/(1+e)`$ |
| Early StreetのBluff | 最終StreetまでBarrelするBluffと途中でGive upするBluffを後ろ向き帰納法で配分 |

### EV

| プレイヤー | EV |
|---|---:|
| IP | $`S`$、$`n`$、Value / Bluff候補の初期分布に依存 |
| OOP | $`1-EV_{IP}`$ |
| 合計 | 1 |

### 導出方法

#### 後ろ向き帰納法で解く順序

| 順序 | 局面 | hand・rangeの役割 | 求めるもの |
|---:|---|---|---|
| 1 | 最終street | IPはValue / Bluff、OOPはBluff catcher | Bluff:Value比とOOPのCall率 |
| 2 | 一つ前のstreet | IPはbarrelを続けるBluffとgive-up Bluffを分ける | 次streetへ残すBluff量 |
| 3 | Rootまで反復 | 各streetで同じpot比を使う | stackを使い切るgeometric size |

最終streetからRootへ逆向きに解くことで、sizeとstreet別Bluff量を分けて導出します。

#### Geometric sizingの一般式

毎streetで、そのstreet開始時のpotに対して同じ比率 $`e`$ をBetすると、Bet–Call後のpotは
$`(1+2e)`$ 倍になります。$`n`$ 回のBet–Callでstack $`S`$を使い切る条件は、

$$
1+2S=(1+2e)^n
$$

したがって、geometric fractionは、

$$
e_{n}=\frac{(1+2S)^{1/n}-1}{2}
$$

です。$`S=4`$、$`n=2`$を代入すると、

$$
e_{2}=\frac{(1+2\cdot4)^{1/2}-1}{2}
=\frac{3-1}{2}=1
$$

となります。したがって、pot betを2回行うとちょうどAll-inになります。

#### 最終Streetで必ず成立する比率

最終streetのBet額を $`eP`$ とすると、OOPのPot oddsから、Bet rangeに必要な
Bluff:Value比は、

$$
\frac{\text{bluff}}{\text{value}}=\frac{e}{1+e}
$$

OOPがIPのBluffを無差別にするCall率、すなわちMDFは、

$$
\mathrm{MDF}=\frac{1}{1+e}
$$

です。Pot BetならBluff:Valueは1:2、MDFは50%です。

#### 前のStreetほどBluff候補が多くなる理由

early streetのBluffには、現在のFold equityに加えて、Call後に次streetで再びBluffする選択肢があります。
そのため、最終streetまでbarrelするBluffだけでなく、途中でgive upするBluffも最初のBet rangeへ入れられます。
K vs AQJの2 street pot-bet例では、J/Qはそれぞれ62.5%で1st streetをbetし、そのうち40%だけを
2nd streetでAll-inします。

一般の $`n`$ streetでも、後ろからPot oddsと無差別条件を解く後ろ向き帰納法を使います。ただし、
early-streetの正確なBluff量は $`S`$、$`n`$、range内のValue/Bluff候補数に依存し、最終streetの比率だけから
一意には決まりません。

---

## ポーカーにおける概念理解

- **Future street:** 追加streetはBluffを一度に使い切らず、段階的に選別する価値を生みます。
- **Geometric betting:** 複数streetで均等な圧力をかけながらriverでstackを使い切る基準です。
- **EQR:** Polar側はPositionと将来のactionを利用し、Nutsの価値とAirのFold equityを実現します。

要点は次の3点です。

1. $`n`$ streetのgeometric fractionは $`((1+2S)^{1/n}-1)/2`$ です。
2. 最終streetのBluff:Value比とMDFはPot oddsだけで決まります。
3. early-streetのBluff量は後ろ向き帰納法と利用可能なBluff候補数で決まります。

---

## Solverによる再現結果

この一般化Studyには独立したSolver runはありません。$`n=1`$はAKQゲーム①、$`n=2,S=4`$は
AKQJゲーム①・②の解析解とSolver結果で確認できます。

---

## その他備考

### Bluff候補が不足する場合

離散AKQ型ゲームでは、必要なEarly-street Bluff massがQだけでは足りないことがあります。J、Tなどの
Air handを追加すると、

- 最終StreetまでBarrelするBluff
- 途中でGive upするBluff
- Off-pathのChecking rangeを守るhand

を別々に割り当てられます。追加したhandが同じshowdown valueを持つ場合、どのAir handを使うかは
非一意になり得ます。
