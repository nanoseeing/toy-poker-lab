# AKQゲーム⑥ 2 StreetのBet・Raise戦略

## ルール

| 項目 | 内容 |
|---|---|
| OOPハンド | A / K / Q（各1/3・独立配布） |
| IPハンド | A / K / Q（各1/3・独立配布） |
| Street | 2 Street |
| 初期Pot | 1 |
| 有効Stack | 1 |
| 許可アクション | Check、Fold、Call、Stackの範囲内の任意サイズのBet・Raise、All-in |
| 勝敗判定 | A > K > Q。同じhandはTie |
| Street遷移 | Check–CheckまたはBet–Callで同じhandのまま次streetへ進む |
| 利得計算方法 | 初期Potをデッドマネーとし、ゲーム終了時の両者の利得合計は1 |

---

## 最適戦略

### 均衡戦略

ルール上は任意のBet・Raise sizeを選べます。計算では10/20/33/50/75% PotとAll-inへaction abstractionし、
以下にその有限actionゲームの均衡を示します。

#### RootのOOP戦略

| OOP hand | Check | Bet 33% |
|---|---:|---:|
| Q | 73.18% | 26.82% |
| K | 59.17% | 40.83% |
| A | 42.62% | 57.38% |

このaction abstractionではone-street版の主要sizeが50%、2 street版が33%になりました。QのBluff、KのBlock/Thin
Value、AのValueが同じsizeを使い、強さに従ってBet頻度を増やすMergedな構造です。

#### OOP Check後のIP戦略

| IP hand | Check | Bet 10% | Bet 20% |
|---|---:|---:|---:|
| Q | 37.49% | 32.73% | 29.78% |
| K | 51.60% | 29.86% | 18.54% |
| A | 27.66% | 40.77% | 31.57% |

IPも1st streetでは大きくPolarizeせず、小sizeで次streetへrangeを運びます。将来All-inできるため、
現在のbetだけで全圧力をかける必要がありません。

### EV

| プレイヤー | EV |
|---|---:|
| IP | 0.522561744 |
| OOP | 0.477438256 |
| 合計 | 1.00 |

### 導出方法

#### 戦略の形をhand・局面別に整理

| 局面 | hand | 主な役割・action |
|---|---|---|
| Root、OOP | Q | Checkと33% Pot Bluffを混合 |
| Root、OOP | K | Checkと33% PotのBlock / Thin valueを混合 |
| Root、OOP | A | 33% Pot ValueとChecking-range防御のCheckを混合 |
| OOP Check後、IP | Q | Checkと10/20% Pot Bluffを混合 |
| OOP Check後、IP | K | 主にCheck |
| OOP Check後、IP | A | 10/20% Pot ValueとCheckを混合 |

1 streetだけの無差別条件ではなく、各action後に残る2nd-street EVまで含めて比較します。

このゲームでは、両者がA/K/Qの3 handを持ち得て、2 streetの各Raise枝でも再び混合します。Solverは有限個の
Bet sizeについて、使用中actionのAction EVを等しくし、未使用actionのEVをそれ以下にする条件を数値的に解きます。

rootでhand $`h`$がCheckとBet 33%を混ぜるなら必要条件は、

$$
EV_h(\mathrm{Check})=EV_h(B_{0.33})
$$

です。ただし、この等式は相手の1st-street応答だけでなく、Call後の2nd-streetで得るEVも含みます。
したがって、riverのBluff:Value式だけから26.82%、40.83%、57.38%という個別頻度を直接導くことはできません。
これらは全ゲーム木の均衡条件を同時に満たした数値解です。

純粋戦略に近い枝はhand strengthで直観的に説明できますが、混合頻度は上のAction EV等式と全rangeの
最適反応の条件で検証します。低reach枝の細かな混合には閉形式の意味を与えません。

---

## ポーカーにおける概念理解

### 同じ離散action setでの1 Street比較

| Street | IP EV | OOP EV |
|---|---:|---:|
| 1 street | 0.530193 | 0.469807 |
| 2 street | 0.522562 | 0.477438 |

この比較では、1 Streetと2 Streetの両方で10/20/33/50/75% PotとAll-inを許可しています。同じ有限action setでは、
2 Street化によりIP EVが約0.00763低下しました。K vs AQJではfuture streetがPolarなIPを強化しましたが、
対称rangeでは、2nd streetもOOPから始まり、OOP自身がQ/K/Aを使ってlead、Block bet、Value Betを再構成できる
ためです。future streetの価値は常にIPだけへ帰属せず、両者のrange構造と行動順に依存します。

### 戦略的な読み方

- OOPのK Betは、IPの自由なPolar sizingを抑えるBlock betとThin valueを兼ねます。
- Aを42.6% Checkへ残すことで、2nd-street Checking rangeを防御します。
- Qは現在のFold equityだけでなく、Bet–Call後のfuture barrelを含めてBluffを開始できます。
- 多数の2nd-street actionはEVがほぼ等しく、個別混合よりrange全体のEVとreachを優先します。

---

## Solverによる再現結果

Solverのaction abstractionは10/20/33/50/75% PotとAll-inです。ここでのExploitabilityは、この有限ゲームに
対する値であり、連続サイズゲームに対する上界ではありません。

| 指標 | 結果 |
|---|---:|
| IP EV | 0.522561744 |
| OOP EV | 0.477438256 |
| Exploitability | `5.8007e-6` |

- [Strategy Viewer](../../public/studies/akq_symmetric_two_street/strategy_viewer.html)
- [計算条件](../../public/studies/akq_symmetric_two_street/resolved_config.json)

### 再現方法

```bash
toy-poker run configs/experiments/study_akq_symmetric_two_street_dcfr.toml
```
