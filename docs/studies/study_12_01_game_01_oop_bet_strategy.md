# 01-game① OOPのBet戦略

## ルール

| 項目 | 内容 |
|---|---|
| OOPハンド | Rank 1〜50（一様ランダム・独立配布） |
| IPハンド | Rank 1〜50（一様ランダム・独立配布） |
| Street | 1 Street |
| 初期Pot | 1 |
| 有効Stack | 4 |
| 許可アクション | Check、Fold、Call、10/20/33/50/75/100/150% PotのBet・Raise、All-in |
| 勝敗判定 | 数字が大きい方が勝ち。同じ数字はTie |
| 利得計算方法 | 初期Potをデッドマネーとし、両者の終端利得の合計は1 |
| 補足 | 連続一様な0–1 gameを50 Rankへ離散化した近似 |

---

## 最適戦略

### 均衡戦略

#### RootのOOP戦略

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

### EV

| プレイヤー | EV |
|---|---:|
| IP | 0.532201433 |
| OOP | 0.467798567 |
| 合計 | 1.00 |

### 導出方法

RootでRank $r$を持つとき、一様な相手rangeに対するShowdown equityは、

$$
EQ(r)=\frac{r-1}{50}+\frac12\frac1{50}=\frac{r-0.5}{50}
$$

です。ただし、Bet EVは相手のsize別Call / Raise rangeに依存するため、EQだけでは最適sizeは決まりません。

#### なぜ中上位は強さに応じてsizeを増やすのか

27〜40は、弱いrankからCallを受けるthin/merged value領域です。rankが上がるほど相手のcontinue rangeに
対するequityが増え、大きいsizeでもvalueを失いにくくなります。しかしRaiseに対するnut advantageは
まだ十分でないため、All-inへ直線的には移行しません。

#### なぜNut級はCheckするのか

44〜50をすべてbetすると、OOPのCheck rangeが中間以下へ偏ります。IPはCheckを見た後に大sizeを高頻度で
使えるため、OOPの中間rangeのequity realizationが低下します。nut級のCheckには次の価値があります。

- IPのbluffを誘発する。
- checking rangeからRaise/Callできるようにする。
- 中間rankをIPのpolar betから守る。
- 複数sizeのvalue rangeを相手に特定させない。

これはposition disadvantageをchecking rangeの強さで補う戦略です。

#### 低RankのBluff混合

rank 1〜7はCheck EVがほぼ0で、多数のbluff actionも無差別に近くなります。同じshowdown valueに近い
低rankをどのsizeへ割り当てるかには非一意性があります。個別rankより、range全体のbluff量と各sizeに
対する相手のMDF/raise responseを優先して読みます。

#### 混合頻度の数学的検証

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

---

## ポーカーにおける概念理解

この結果はBet sizing、Thin value、Nut advantage、Checking-range protectionを観察する教材です。
中上位RankはEQが増えるにつれてValue Betのsizeを段階的に増やす一方、Nut級はIPの攻撃から
Checking rangeを守るため、一部をCheckへ残します。

---

## Solverによる再現結果

| 指標 | 結果 |
|---|---:|
| IP EV | 0.532201433 |
| OOP EV | 0.467798567 |
| Exploitability | `1.6662e-8` |

- [Strategy Viewer](../../public/studies/zero_one_n50_one_street/strategy_viewer.html)
- [計算条件](../../public/studies/zero_one_n50_one_street/resolved_config.json)

### 再現方法

```bash
toy-poker run configs/experiments/integer_range_betting_n50_7_sizes_cpp_dcfr_target_1e8.toml
```

---

## その他備考

### 41、42、43が非単調な理由

高精度runでは、41は主にCheck、42は主に75% bet、43は100% Checkでした。これは単純なequity順の
thresholdではなく、複数sizeのvalue密度、IPのRaise、checking range防御を同時に満たす離散均衡です。
Action EVが近い隣接rankでは、`Check → Bet → Check`のような非単調性も均衡条件に反しません。
