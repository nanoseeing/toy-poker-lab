# 01-game① OOPのBet戦略

## ルール

| 項目 | 内容 |
|---|---|
| OOPハンド | rank 1〜50のhand（一様ランダム・独立配布） |
| IPハンド | rank 1〜50のhand（一様ランダム・独立配布） |
| Street | 1 Street |
| 初期Pot | 1 |
| 有効Stack | 4 |
| 許可アクション | Check、Fold、Call、10/20/33/50/75/100/150% PotのBet・Raise、All-in |
| 勝敗判定 | handのrankが高い方が勝ち。同じrankはTie |
| 利得計算方法 | 初期Potをデッドマネーとし、ゲーム終了時の両者の利得合計は1 |
| 補足 | 連続一様な0–1 gameを50段階のrankへ離散化した近似 |

---

## 最適戦略

### 均衡戦略

#### RootのOOP戦略

| rank帯 | 主な役割 | 主要戦略 |
|---|---|---|
| 1–7 | Bluff候補 | Checkと10〜75% Betを混合 |
| 8–26 | showdown/Check | ほぼ100% Check |
| 27–30 | Small value / Block bet | Bet 10% |
| 31–34 | Thin value | Bet 20% |
| 35–37 | Value | Bet 33% |
| 38–40 | Stronger value | Bet 50% |
| 41–43 | transition / range defense | Checkと75% betが非単調に混在 |
| 44–50 | Nut advantage | Checkと複数sizeを混合 |

中上位ではEQが上がるにつれて10% → 20% → 33% → 50%とsizeが段階的に増えます。一方、
nut級は単純に最大sizeへ移行せず、かなりの頻度をCheckへ残します。

### EV

| プレイヤー | EV |
|---|---:|
| IP | 0.532201433 |
| OOP | 0.467798567 |
| 合計 | 1.00 |

### 導出方法

#### rank帯ごとの候補actionを整理

| rank帯 | handの役割 | 主に比較するaction |
|---|---|---|
| 1〜7 | showdown valueがほぼないBluff候補 | Check / 各sizeのBluff |
| 8〜26 | 中間のshowdown hand | 主にCheck / 薄いBet |
| 27〜40 | Thin / Merged value | Check / rankに応じた小〜中size |
| 41〜43 | size間の移行帯 | Check / 75% Pot |
| 44〜50 | Nut級ValueとChecking-range防御 | Check / 複数sizeのValue Bet |

まずrankからshowdown EQを求め、次に各sizeへ対するIPのCall / Raise rangeを含めてAction EVを比較します。

Rootでrank $`r`$のhandを持つとき、一様な相手のrangeに対するshowdown EQは、

$$
EQ(r)=\frac{r-1}{50}+\frac{1}{2}\frac{1}{50}=\frac{r-0.5}{50}
$$

です。ただし、Bet EVは相手のsize別Call / Raise rangeに依存するため、EQだけでは最適sizeは決まりません。

#### なぜ中上位は強さに応じてsizeを増やすのか

rank 27〜40のhandは、より低いrankのhandからCallを受けるThin/Merged value領域です。rankが高くなるほど
相手のContinue rangeに対するEQが増え、大きいsizeでもValueを失いにくくなります。しかしRaiseに対するNut advantageは
まだ十分でないため、All-inへ直線的には移行しません。

#### なぜNut級はCheckするのか

44〜50をすべてbetすると、OOPのCheck rangeが中間以下へ偏ります。IPはCheckを見た後に大sizeを高頻度で
使えるため、OOPの中間rangeのEQRが低下します。Nut級のCheckには次の価値があります。

- IPのBluffを誘発する。
- Checking rangeからRaise/Callできるようにする。
- 中程度のrankを持つhandをIPのPolar Betから守る。
- 複数sizeのValue rangeを相手に特定させない。

これはPosition disadvantageをChecking rangeの強さで補う戦略です。

#### rankの低いhandのBluff混合

rank 1〜7のhandはCheck EVがほぼ0で、多数のBluff actionも無差別に近くなります。同じshowdown valueに近い
rankの低いhandをどのsizeへ割り当てるかには非一意性があります。個別handより、range全体のBluff量と各sizeに
対する相手のMDF/Raise responseを優先して読みます。

#### 混合頻度の数学的検証

この多size・Raiseゲームに既知の短い閉形式解はありません。Checkを$`C`$、Pot比$`s`$のBetを$`B_s`$と書きます。
rank $`r`$のhandがCheckと複数sizeを混ぜるなら、正の頻度を持つ全actionについて、

$$
EV_r(C)=EV_r(B_{0.10})
=\cdots=EV_r(B_x)
$$

が必要です。さらに、各sizeに対するIPのFold/Call/Raiseもそれぞれ最適反応でなければなりません。
Studyの頻度はこの大きな連立条件をDCFRで数値的に解いたものであり、個別handの丸め値を解析定数とは扱いません。

一方、純粋戦略に近い領域は直観的です。中程度のrankを持つhandは強いrangeにCall/RaiseされるBetよりshowdownを選び、
rankの高いhandは弱いCallからValueを得ます。最もrankの低いhandはshowdown EVがほぼないため、Fold equityを得られる
Bluffへ回す機会費用が小さくなります。

---

## ポーカーにおける概念理解

この結果はBet sizing、Thin value、Nut advantage、Checking-range protectionを観察する教材です。
rankが中上位のhandはEQが増えるにつれてValue Betのsizeを段階的に増やす一方、Nut級はIPの攻撃から
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

高精度runでは、41は主にCheck、42は主に75% Bet、43は100% Checkでした。これは単純なEQ順の
thresholdではなく、複数sizeのValue密度、IPのRaise、Checking range防御を同時に満たす離散均衡です。
Action EVが近い、rankが隣接するhandでは、`Check → Bet → Check`のような非単調性も均衡条件に反しません。
