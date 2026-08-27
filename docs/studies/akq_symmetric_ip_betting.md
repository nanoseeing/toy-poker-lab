# Symmetric AKQ: OOP forced check, IP chooses bet size

> Status: `解析解あり`・`数値検証済み`

## ルール

| 項目 | 内容 |
|---|---|
| Street | River相当の1 street。runoutなし |
| OOP range | Q / K / Aを各1/3。rootを全rank 100% Checkに固定 |
| IP range | Q / K / Aを各1/3 |
| 配布 / 強さ | 独立配布、A > K > Q、同rankはtie |
| 初期pot / stack | pot 1、両者stack 1 |
| IPのBet size | 5%刻みのpot bet（5〜95%）とAll-in |
| OOPの応答 | Call / Foldのみ。Raise不可 |
| 最適化対象 | rootのNode lockを守る条件付きゲーム |
| 利得 | 終端利得の合計は常に1 |

## 連続sizeの解析解

### 純粋戦略の形

Aは全ての非Aに勝つためvalue bet、Kは弱いQに勝って強いAに負けるshowdown handなのでCheck、Qは
showdown valueがtie分しかなくbluff候補、と仮定します。後で得られる解に対して各Action EVを比較すると、
AのBetとKのCheckは他のaction以上になるため、この純粋戦略の形が自己整合的です。

### Qのbluff頻度

IPはAを100% bet、KをCheck、Qを頻度 $b$ でbluffするとします。bet額を $B$ とすると、
OOPのKをCall/Foldで無差別にする条件は、

\[
b(1+B)-B=0
\quad\Rightarrow\quad
b(B)=\frac{B}{1+B}
\]

です。

### OOP(K)のCall頻度

IPのQはCheckするとOOPのQとのtieだけから $1/6$ を得ます。OOP(K)のCall率を $c$ とすると、
Qのbet EVは、

\[
EV_Q(B)=\frac{2-B-c(1+B)}{3}
\]

なので、Checkと無差別にする条件は、

\[
c(B)=\frac{1.5-B}{1+B}
\]

です。IP(A)のEVは、OOP(Q)がFold、Kが頻度 $c$ でCall、AがCallすることから、

\[
EV_A(B)=\frac{2.5+B\frac{1.5-B}{1+B}}{3}
\]

です。$B$に依存する部分を微分すると、

$$
\frac{d}{dB}\left(\frac{B(1.5-B)}{1+B}\right)
=\frac{1.5-2B-B^2}{(1+B)^2}
$$

です。分子を0とすると、

\[
B^*=\sqrt{\frac52}-1\simeq0.581139
\]

となります。二次導関数または導関数の符号変化から最大値であり、$b,c$も0〜1に入ります。したがって
連続sizeの最適値は約58.1% potです。このsizeは、AがKから得るthin valueとQが負うbluff riskを
同時に最適化した結果です。

この最適sizeでの混合頻度は、

$$
b^*=\frac{B^*}{1+B^*}\simeq0.367544,
\qquad
c^*=\frac{1.5-B^*}{1+B^*}=B^*\simeq0.581139
$$

です。つまり連続ゲームではQを約36.75% bluffし、OOPのKは約58.11% Callします。

## 5%刻みでの戦略

離散actionでは60%が主要sizeになりました。

| IP rank | 戦略 |
|---|---|
| Q | Check 62.63% / Bet 55% 2.33% / Bet 60% 35.03% |
| K | Checkほぼ100% |
| A | Bet 55% 6.58% / Bet 60% 93.41% |

60%だけを使う解析値は、

\[
b(0.6)=37.5\%,\qquad c(0.6)=56.25\%
\]

です。solverではOOP(K)が`Call 56.244% / Fold 43.756%`となり、解析値と一致しました。

## なぜAll-inではないのか

All-inはKから1 stackを取れる一方、KのCall頻度を25%まで下げます。約58% betならKを約60%近く
Callさせ、Aがより頻繁にthin valueを得られます。Qのbluff riskも小さくなるため、必要なbluff量と
KのCall量を最も効率よく釣り合わせる中間sizeが選ばれます。

## Solver結果

| 指標 | 結果 |
|---|---:|
| Iterations | 8,000 / 10,000 |
| Constrained Nash gap | `5.0386e-6` |
| IP EV | 0.537497132 |
| OOP EV | 0.462502868 |

- [Strategy Viewer](../../public/studies/akq_symmetric_ip_betting/strategy_viewer.html)
- [計算条件](../../public/studies/akq_symmetric_ip_betting/resolved_config.json)

Node lockを破る通常Exploitabilityは`0.15579`です。これはOOP全checkというルールを外した元ゲームの
指標であり、本教材の収束判定にはconstrained Nash gapを使います。

## 再現方法

```bash
toy-poker run configs/experiments/study_akq_symmetric_oop_check_ip_variable_size_dcfr.toml
```
