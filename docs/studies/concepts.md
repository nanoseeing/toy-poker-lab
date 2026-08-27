# ポーカー戦略の基本概念

この用語集は、各toyゲームの数式と実戦的な読み替えを同じ意味で使うための基準です。
純粋戦略、混合戦略、Nash均衡、無差別条件は先に[ゲーム理論の基本用語](game_theory_basics.md)を
参照してください。

## Range構造

### Polarization

強いvalueとshowdown valueのないbluffを中心にbetし、中間のbluff catcherをcheckへ残す構造です。
polar rangeは大きいsizeを使いやすく、相手の中間rangeへ最大の圧力をかけます。

### Merged rangeとthin value

nut級だけでなく、中上位のハンドも弱いハンドからcallを受けるためにbetする構造です。
thin valueは相手のcontinue rangeに対するequityが僅かに50%を超えるvalue betで、raiseに対して
難しい判断を持ちやすくなります。

### Checking range

Checkはgive-upだけではありません。強いハンドを残すことで相手のbetに対するcall/raiseを守り、
中間ハンドのequity realizationを改善します。nut級の一部checkはrange protectionやtrapとして
働きます。

### Range advantageとnut advantage

range advantageはrange全体の平均equity、nut advantageは最上位ハンドの密度に関する優位です。
平均equityが近くてもnut advantageが大きい側はpolarな大sizeを使いやすくなります。

## Betと防御

### Bluff:value比

riverでpotを $P$、betを $B$ とすると、bluff catcherを無差別にするbluffの割合は、bet range
全体に対して次です。

\[
\text{bluff share}=\frac{B}{P+2B}
\]

同じ条件をbluff:value比で書くと $B:(P+B)$ です。将来street、raise、tie、複数のvalue階層が
ある場合はこの単純式をそのまま適用できません。

### Pot oddsとMDF

bet $B$ をcallして最終pot $P+2B$ を争うときの必要equityは $B/(P+2B)$ です。
bluffを自動利益にしない最低防御頻度は、raiseを無視したriverモデルでは次です。

\[
MDF=\frac{P}{P+B}
\]

MDFは各ハンドを一律に防御する指示ではなく、range全体のcall/raise頻度の基準です。

### Bet sizingとgeometric betting

sizeはvalueが得るcall量とbluffのriskを同時に変えます。残り $n$ street、初期pot 1、実効stack
$S$ を毎street同じpot比率で使い切るgeometric fractionは次です。

\[
e_n=\frac{(1+2S)^{1/n}-1}{2}
\]

これは全streetでbet-callが続く経路のサイズ設計であり、常に全rangeが同じ頻度でbetするという
意味ではありません。

### Raiseとblock bet

Raiseはvalue/bluff比だけでなく、相手のthin valueとblock betの実現価値を変えます。block betは
中間ハンドが自分で小さく価格を決めるbetですが、raise rangeに対して脆くなるため、強いハンドや
raiseへのcontinueを組み合わせる必要があります。

## Positionと複数street

### Positionとequity realization

IPはOOPのCheckを観察してからbet/checkを選べるため、valueとbluffを効率よく配分できます。
equity realizationは、現在のshowdown equityのうち実際のEVとして回収できる割合です。強制Fold、
将来のbet、positionによって100%を上回ったり下回ったりします。

### Future street

将来streetがあると、現在のbetは即時のFold equityだけでなく、次streetでさらに圧力をかける権利を
作ります。early-streetのbluff開始頻度と、最終streetまで継続するbluff頻度は区別します。

### Dynamic equity

public cardによってhand strengthやequityが変化することです。本プロジェクトの現行AKQ/AKQJと
integer 1-Nゲームにはrunoutがないため、future-street option valueはありますがdynamic equityは
ありません。dynamic equityを検証するにはpublic chance cardを追加した別ゲームが必要です。

### Blocker

相手が特定のhandを持てるcombo数を自分のcardが減らす効果です。現行rangeゲームはprivate rankを
独立配布するためcard removalがなく、blockerはモデル化されていません。同じ強さのrank間で頻度が
異なっても、それをblocker効果とは呼びません。

## Solver結果を読む注意

- Exploitabilityは元ゲームでのbest responseに対する弱さです。
- Node lock使用時のconstrained Nash gapは、lockを破らない範囲だけの収束指標です。
- 到達確率が低いoff-path戦略は、on-path戦略より収束が遅い場合があります。
- Action EVが同じhandやactionの混合頻度は非一意になり得ます。
- 個別rankの色だけでなく、条件付きrange、node頻度、EVを一緒に確認します。
