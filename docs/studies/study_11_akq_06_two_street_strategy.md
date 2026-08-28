# AKQゲーム⑥ 2 StreetのBet・Raise戦略

## ルール

| 項目 | 内容 |
|---|---|
| OOPハンド | A / K / Q（各1/3・独立配布） |
| IPハンド | A / K / Q（各1/3・独立配布） |
| Street | 2 Street |
| 初期Pot | 1 |
| 有効Stack | 1 |
| 許可アクション | Check、Fold、Call、10/20/33/50/75% PotのBet・Raise、All-in |
| 勝敗判定 | A > K > Q。同じハンドはTie |
| Street遷移 | Check-checkまたはbet-callで同じrankのまま次streetへ進む |
| 利得計算方法 | 初期Potをデッドマネーとし、両者の終端利得の合計は1 |

---

## 最適戦略

### 均衡戦略

#### RootのOOP戦略

| OOP rank | Check | Bet 33% |
|---|---:|---:|
| Q | 73.18% | 26.82% |
| K | 59.17% | 40.83% |
| A | 42.62% | 57.38% |

one-street版の主要sizeは50%でしたが、2 streetでは33%へ小さくなりました。Qのbluff、Kのblock/thin
value、Aのvalueが同じsizeを使い、強さに従ってbet頻度を増やすmergedな構造です。

#### OOP Check後のIP戦略

| IP rank | Check | Bet 10% | Bet 20% |
|---|---:|---:|---:|
| Q | 37.49% | 32.73% | 29.78% |
| K | 51.60% | 29.86% | 18.54% |
| A | 27.66% | 40.77% | 31.57% |

IPも1st streetでは大きくpolarizeせず、小sizeで次streetへrangeを運びます。将来All-inできるため、
現在のbetだけで全圧力をかける必要がありません。

### EV

| プレイヤー | EV |
|---|---:|
| IP | 0.522561744 |
| OOP | 0.477438256 |
| 合計 | 1.00 |

### 導出方法

このゲームは両者が3 rankを持ち、2 streetの各Raise枝でも再び混合するため、単一sizeのriverゲームのような
閉形式は使えません。solverは全情報集合について、使用中actionのAction EVを等しくし、未使用actionのEVを
それ以下にする連立条件を数値的に解いています。

rootでrank $`r`$がCheckとBet 33%を混ぜるなら必要条件は、

$$
EV_r(\mathrm{Check})=EV_r(B_{0.33})
$$

です。ただし、この等式は相手の1st-street応答だけでなく、Call後の2nd-street方策を含む継続利得を使います。
したがって、riverのbluff:value式だけから26.82%、40.83%、57.38%という個別頻度を直接導くことはできません。
これらは全ゲーム木の均衡条件を同時に満たした数値解です。

純粋戦略に近い枝はhand strengthで直観的に説明できますが、混合頻度は上のAction EV等式と全rangeの
best-response条件で検証します。低reach枝の細かな混合には閉形式の意味を与えません。

---

## ポーカーにおける概念理解

### 1 StreetとのEV比較

| Game | IP EV | OOP EV |
|---|---:|---:|
| 1 street | 0.530193 | 0.469807 |
| 2 street | 0.522562 | 0.477438 |

K vs AQJではfuture streetがpolarなIPを大きく強化しましたが、対称rangeではIP EVが約0.00763低下しました。
理由は、2nd streetもOOPから始まり、OOP自身がQ/K/Aを使ってlead、block bet、value betを再構成できる
ためです。future streetの価値は常にIPだけへ帰属せず、両者のrange構造と行動順に依存します。

### 戦略的な読み方

- OOPのK betは、IPの自由なpolar sizingを抑えるblock betとthin valueを兼ねます。
- Aを42.6% Checkへ残すことで、2nd-street checking rangeを防御します。
- Qは現在のFold equityだけでなく、bet-call後のfuture barrelを含めてbluffを開始できます。
- 多数の2nd-street actionはEVがほぼ等しく、個別混合よりrange全体のEVとreachを優先します。

---

## Solverによる再現結果

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
