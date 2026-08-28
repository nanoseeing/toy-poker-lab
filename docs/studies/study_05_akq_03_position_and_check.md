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
| 勝敗判定 | A > K > Q。同じハンドはTie |
| 利得計算方法 | 初期Potをデッドマネーとし、両者の終端利得の合計は1 |

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

#### IPの純粋戦略のヒューリスティック解釈

OOPが全rangeをCheckした後を考えます。後で導くOOPの応答`Q Fold / K Call 25% / A Call`を使うと、

- IPのKはCheckで $`(1+0.5+0)/3=0.5`$を得ます。All-inは
  $`(1+0.75\times1+0.25\times0.5-1)/3=7/24`$なので、Checkが厳密に優れます。
- IPのAはCheckで$`(1+1+0.5)/3=5/6`$、All-inで
  $`(1+1.25+0.5)/3=11/12`$を得るため、All-inが厳密に優れます。

したがって、Kは純粋Check、Aは純粋All-inです。Qだけがbluff候補になります。

#### IP(Q)のBluff頻度の数学的導出

IPがAを100%、Qを頻度 $`b`$ でAll-inするとします。OOPのKがCallしたとき、Qには`+2`、
Aには`-1`なので、

$$
2b-1=0 \Rightarrow b=\frac{1}{2}
$$

です。bet range内のQは1/3となり、Kの必要equity1/3と一致します。

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

OOPが先にbetすると、IPは後手から自分のQ/K/Aに応じてFold、Callを選び、OOPの中間rangeを効率よく
選別できます。CheckならAをrangeに残したままIPのbluffを受け、Kをbluff catcherとして使えます。
この純粋なroot Checkは、各rankの先打ちAll-inがCheckの利得を上回らないことをsolverのAction EVでも
確認しています。rootのoff-path応答を含む完全な不等式は長くなるため、ここでは混合頻度の閉形式と分け、
checking-range protectionとして解釈します。

#### ゲーム価値

IPのrank別利得は、Qが$`1/6`$、Kが$`1/2`$、Aが$`11/12`$です。したがって、

$$
EV_{IP}=\frac{1}{3}\left(\frac{1}{6}+\frac{1}{2}+\frac{11}{12}\right)
=\frac{19}{36},
\qquad EV_{OOP}=1-EV_{IP}=\frac{17}{36}
$$

となります。

---

## ポーカーにおける概念理解

OOPは全rangeをCheckし、Aを含むChecking rangeを守ります。IPはPositionを使って、AとQの一部を
Polarizeします。KはIPではShowdown valueを持つためCheck、OOPではAll-in rangeに対するBluff
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
