# AKQゲーム② Polar rangeのBet size

## ルール

| 項目 | 内容 |
|---|---|
| OOPハンド | K（100%） |
| IPハンド | A / Q（各50%） |
| Street | 1 Street |
| 初期Pot | 1 |
| 有効Stack | 1 |
| 許可アクション | Check、Fold、Call、10/20/33/50/75% PotのBet・Raise、All-in |
| 勝敗判定 | A > K > Q |
| 利得計算方法 | 初期Potをデッドマネーとし、両者の終端利得の合計は1 |

---

## 最適戦略

### 均衡戦略

solverはAll-in-only版と同じon-path戦略へ収束しました。

| 局面 | 戦略 |
|---|---|
| OOP(K)、root | Check 100% |
| IP(A) | All-in 100% |
| IP(Q) | All-in 50% / Check 50% |
| OOP(K) | Call 50% / Fold 50% |

10〜75%の中間sizeは数値誤差を除いて使いません。

### EV

| プレイヤー | EV |
|---|---:|
| IP | 0.75 |
| OOP | 0.25 |
| 合計 | 1.00 |

### 導出方法

#### 固定したsize $`B`$ に対する数学的導出

初期pot 1へIPが $`B\leq1`$ をbetし、Aを100% value bet、Qを頻度 $`b`$ でbluffするとします。
KのCall EVを0にする条件は、

$$
b(1+B)-B=0
\quad\Rightarrow\quad
b=\frac{B}{1+B}
$$

です。QをCheckとbluffで無差別にするKのCall率は、

$$
(1-c)-cB=0
\quad\Rightarrow\quad
c=\frac{1}{1+B}
$$

です。AはFoldされれば1、Callされれば $`1+B`$ を得るので、

$$
EV_A=1+cB=1+\frac{B}{1+B}
$$

となります。Qの均衡EVは0なので、IPのrange EVは、

$$
EV_{IP}(B)=\frac{1}{2}\left(1+\frac{B}{1+B}\right)
=\frac{1+2B}{2(1+B)}
$$

です。微分すると、

$$
\frac{dEV_{IP}}{dB}=\frac{1}{2(1+B)^2}>0
$$

となります。したがってstack制約内の最大値 $`B=1`$、つまりAll-inが最適です。

#### 純粋戦略と未使用sizeのヒューリスティック解釈

- AはKに必ず勝つため、選ばれたsizeでは100% value betします。
- OOPの先打ちAll-inは、AにCall、QにFoldされて期待利得0です。Checkの均衡利得0.25を下回るため、Kは100% Checkします。
- $`EV_{IP}(B)`$が厳密に増加するため、10〜75%はAll-inより低利得で、均衡頻度0になります。
- $`B=1`$では$`b=c=1/2`$となり、All-in-only版の混合頻度をそのまま再現します。

上の式はOOPの応答をCall/Foldに限定したときの値です。実装上は合法なRaiseもありますが、相手へRaiseという
追加選択肢を与えてもIPが保証できる利得は増えません。$`B<1`$のCall/Fold限定値がすでに0.75未満である一方、
$`B=1`$ならRaise余地を消して0.75を保証できます。したがってRaiseを含む元ゲームでもAll-inが最適です。

---

## ポーカーにおける概念理解

Polar range側がsizeを自由に選べるとき、中間sizeでCallを増やすのか、最大sizeでBluff catcherへ
圧力をかけるのかを検証する題材です。

KしかないOOPにはRaiseでIPのThin valueを罰するrangeも、Aを上回るNutsもありません。IPはsizeを
小さくしてCallを増やすより、Aと必要量のQをPolarizeして最大sizeを使う方が高EVです。

---

## Solverによる再現結果

| 指標 | 結果 |
|---|---:|
| IP EV | 0.750000003 |
| OOP EV | 0.249999997 |
| Exploitability | `2.3830e-6` |

- [Strategy Viewer](../../public/studies/akq_k_vs_aq_variable_size/strategy_viewer.html)
- [計算条件](../../public/studies/akq_k_vs_aq_variable_size/resolved_config.json)

### 再現方法

```bash
toy-poker run configs/experiments/study_akq_k_vs_aq_variable_size_dcfr.toml
```
