# 0–1 game approximation: N=50, one street

> Status: `数値検証済み`

## ルール

| 項目 | 内容 |
|---|---|
| Street | River相当の1 street。runoutなし |
| OOP range | rank 1〜50を一様に保有 |
| IP range | rank 1〜50を一様に保有 |
| 配布 / 強さ | 独立配布。数字が大きいほど強く、同rankはtie |
| 初期pot / stack | pot 1、両者stack 4 |
| Bet / Raise size | 10/20/33/50/75/100/150% pot、All-in |
| Raise制約 | 標準minimum raise。両者Raise可能 |
| 連続ゲームとの関係 | 連続一様な0–1 gameを50 rankへ離散化した近似 |
| 利得 | 終端利得の合計は常に1 |

rootでrank $r$を持つとき、一様な相手rangeに対するshowdown equityは、

$$
EQ(r)=\frac{r-1}{50}+\frac12\frac1{50}=\frac{r-0.5}{50}
$$

です。ただし、Bet EVは相手のsize別Call/Raise rangeに依存するため、EQだけでは最適sizeは決まりません。

## Root OOP戦略の全体像

| Rank帯 | 主な役割 | 主要戦略 |
|---|---|---|
| 1–7 | bluff候補 | Checkと10〜75% betを混合 |
| 8–26 | showdown/check | ほぼ100% Check |
| 27–30 | small value / block bet | Bet 10% |
| 31–34 | thin value | Bet 20% |
| 35–37 | value | Bet 33% |
| 38–40 | stronger value | Bet 50% |
| 41–43 | transition / range defense | Checkと75% betが非単調に混在 |
| 44–50 | nut advantage | Checkと複数sizeを混合 |

中上位ではequityが上がるにつれて10% → 20% → 33% → 50%とsizeが段階的に増えます。一方、
nut級は単純に最大sizeへ移行せず、かなりの頻度をCheckへ残します。

## なぜ中上位は強さに応じてsizeを増やすのか

27〜40は、弱いrankからCallを受けるthin/merged value領域です。rankが上がるほど相手のcontinue rangeに
対するequityが増え、大きいsizeでもvalueを失いにくくなります。しかしRaiseに対するnut advantageは
まだ十分でないため、All-inへ直線的には移行しません。

## なぜnut級はCheckするのか

44〜50をすべてbetすると、OOPのCheck rangeが中間以下へ偏ります。IPはCheckを見た後に大sizeを高頻度で
使えるため、OOPの中間rangeのequity realizationが低下します。nut級のCheckには次の価値があります。

- IPのbluffを誘発する。
- checking rangeからRaise/Callできるようにする。
- 中間rankをIPのpolar betから守る。
- 複数sizeのvalue rangeを相手に特定させない。

これはposition disadvantageをchecking rangeの強さで補う戦略です。

## 低rankのbluff混合

rank 1〜7はCheck EVがほぼ0で、多数のbluff actionも無差別に近くなります。card-removalがないため、
どの低rankをどのsizeへ割り当てるかには非一意性があります。個別rankより、range全体のbluff量と各sizeに
対する相手のMDF/raise responseを優先して読みます。

## 混合頻度をどう検証するか

この多size・Raiseゲームに既知の短い閉形式解はありません。rank $r$がCheckと複数sizeを混ぜるなら、
正の頻度を持つ全actionについて、

$$
EV_r(\mathrm{Check})=EV_r(\mathrm{Bet}_{10\%})
=\cdots=EV_r(\mathrm{Bet}_{x\%})
$$

が必要です。さらに、各sizeに対するIPのFold/Call/Raiseもそれぞれbest responseでなければなりません。
Studyの頻度はこの大きな連立条件をDCFRで数値的に解いたものであり、個別rankの丸め値を解析定数とは扱いません。

一方、純粋戦略に近い領域は直観的です。中位rankは強いrangeにCall/RaiseされるBetよりShowdownを選び、
十分強いrankは弱いCallからvalueを得ます。最弱rankはShowdown EVがほぼないため、Fold equityを得られる
bluffへ回す機会費用が小さくなります。

## 41、42、43が非単調な理由

高精度runでは、41は主にCheck、42は主に75% bet、43は100% Checkでした。これは単純なequity順の
thresholdではなく、複数sizeのvalue密度、IPのRaise、checking range防御を同時に満たす離散均衡です。
Action EVが近い隣接rankでは、`Check → Bet → Check`のような非単調性も均衡条件に反しません。

## Solver結果

| 指標 | 結果 |
|---|---:|
| Iterations | 300,000 |
| Target | `1e-8` |
| Final Exploitability | `1.6662e-8` |
| Best Exploitability | `1.3193e-8` at 295,000 |
| IP EV | 0.532201433 |
| OOP EV | 0.467798567 |
| Solver計算時間 | 約668秒 |

- [Strategy Viewer](../../public/studies/zero_one_n50_one_street/strategy_viewer.html)
- [計算条件](../../public/studies/zero_one_n50_one_street/resolved_config.json)

## 実戦への応用と限界

この結果はbet sizing、thin value、nut advantage、checking-range protectionを観察する教材です。
実カードのblocker、board texture、dynamic equityはありません。またrank数を50にしても連続ゲームの
厳密解ではなく離散近似です。
