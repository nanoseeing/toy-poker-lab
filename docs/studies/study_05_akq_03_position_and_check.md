# AKQゲーム③ PositionとChecking range

## ルール

| 項目 | 内容 |
|---|---|
| OOPハンド | A / K / Q（各1/3・独立配布） |
| IPハンド | A / K / Q（各1/3・独立配布） |
| Street | 1 Street |
| 初期Pot | 1 |
| 有効Stack | 1 |
| 許可アクション | Check、All-in、Call、Fold |
| アクション制約 | Bet sizeはAll-inだけに固定 |
| 勝敗判定 | A > K > Q。同じhandはTie |
| 利得計算方法 | 初期Potをデッドマネーとし、ゲーム終了時の両者の利得合計は1 |

---

## 最適戦略

### 均衡戦略

| 局面 | Q | K | A |
|---|---|---|---|
| OOP root | Check 100% | Check 100% | Check 100% |
| IP after Check | All-in 50% | Check 100% | All-in 100% |
| OOP facing All-in | Fold 100% | Call 25% | Call 100% |

### EV

| プレイヤー | EV |
|---|---:|
| IP | $`19/36 \simeq 0.527778`$ |
| OOP | $`17/36 \simeq 0.472222`$ |
| 合計 | 1.00 |

### 導出方法

#### 戦略の形を場合別に整理

| 局面 | プレイヤー・hand | 比較するaction | 結論 |
|---|---|---|---|
| Root | OOP(Q/K/A) | Check / All-in | 全hand Check 100% |
| OOP Check後 | IP(A) | Check / All-in | All-in 100% |
| OOP Check後 | IP(K) | Check / All-in | Check 100% |
| OOP Check後 | IP(Q) | Check / All-in | 両actionを混合 |
| IP All-inに直面 | OOP(Q) | Fold / Call | Fold 100% |
| IP All-inに直面 | OOP(K) | Fold / Call | 両actionを混合 |
| IP All-inに直面 | OOP(A) | Fold / Call | Call 100% |

#### IP(A/K/Q)のAction EV比較

OOPが全rangeをCheckした後を考えます。後で導くOOPの応答`Q Fold / K Call 25% / A Call`を使うと、

- IPのKはCheckで $`(1+0.5+0)/3=0.5`$を得ます。All-inは
  $`(1+0.75\times1+0.25\times0.5-1)/3=7/24`$なので、Checkが厳密に優れます。
- IPのAはCheckで$`(1+1+0.5)/3=5/6`$、All-inで
  $`(1+1.25+0.5)/3=11/12`$を得るため、All-inが厳密に優れます。

したがって、IP(A)は純粋All-in、IP(K)は純粋Checkです。IP(Q)だけがBluff候補になります。

#### IP(Q)のBluff頻度の数学的導出

IPがAを100%、Qを頻度 $`b`$ でAll-inするとします。OOPのKがCallしたとき、Qには`+2`、
Aには`-1`なので、

$$
2b-1=0 \Rightarrow b=\frac{1}{2}
$$

です。Bet range内のQは1/3となり、Kの必要EQ 1/3と一致します。

#### OOP(K)のCall頻度の数学的導出

IPのQはCheckすると、OOPのQとtieする1/3の場合だけpotの半分を得るため、

$$
EV_Q(\mathrm{check})=\frac{1}{3}\cdot\frac{1}{2}=\frac{1}{6}
$$

です。OOPのKのCall率を $`c`$ とすると、QのAll-in EVは、OOPのQがFold、KがCall/Fold、AがCall
することから、

$$
EV_Q(\mathrm{allin})=\frac{1-2c}{3}
$$

です。これを1/6に合わせると $`c=1/4`$ になります。

OOPのQはIPのbet rangeに一度も勝たないため100% Fold、Aは一度も負けないため100% Callです。

#### OOPが全rangeをCheckする理由

OOPがCheckしたときのhand別EVは、上で導いたIP戦略を使うと、

$$
EV_Q(C)=\frac{1}{12},\qquad
EV_K(C)=\frac{1}{3},\qquad
EV_A(C)=1
$$

です。次に、均衡では到達しないOOPのroot All-inに対し、IPを`QはFold、AはCall、Kは頻度dでCall`と
定めます。このときOOPのQ/K/AがAll-inへ逸脱したEVはそれぞれ、

$$
EV_Q(AI)=\frac{1-2d}{3},\qquad
EV_K(AI)=\frac{1-d/2}{3},\qquad
EV_A(AI)=\frac{5/2+d}{3}
$$

です。3種類のhandについて同時に

$$
EV_h(AI)\leq EV_h(C)
$$

とする条件は、

$$
\frac{3}{8}\leq d\leq\frac{1}{2}
$$

です。この範囲の任意の $`d`$ をoff-path戦略として選べるため、OOPの全hand Checkは
Nash均衡の逸脱不等式を満たします。off-pathのIP(K) Call率は非一意ですが、on-path戦略とゲーム価値は
変わりません。

#### ゲーム価値

IPのhand別利得は、Qが$`1/6`$、Kが$`1/2`$、Aが$`11/12`$です。したがって、

$$
EV_{IP}=\frac{1}{3}\left(\frac{1}{6}+\frac{1}{2}+\frac{11}{12}\right)
=\frac{19}{36},
\qquad EV_{OOP}=1-EV_{IP}=\frac{17}{36}
$$

となります。

---

## ポーカーにおける概念理解

OOPは全rangeをCheckし、Aを含むChecking rangeを守ります。IPはPositionを使って、AとQの一部を
Polarizeします。KはIPではshowdown valueを持つためCheck、OOPではAll-in rangeに対するBluff
catcherになります。同じKでもPositionと直前のrange更新によって役割が変わります。

---

## Solverによる再現結果

| 指標 | 結果 |
|---|---:|
| IP EV | 0.527777780 |
| OOP EV | 0.472222220 |
| Exploitability | `4.0376e-6` |

- [Strategy Viewer](../../public/studies/akq_symmetric_allin/strategy_viewer.html)
- [計算条件](../../public/studies/akq_symmetric_allin/resolved_config.json)

### 再現方法

```bash
toy-poker run configs/experiments/study_akq_symmetric_allin_dcfr.toml
```
