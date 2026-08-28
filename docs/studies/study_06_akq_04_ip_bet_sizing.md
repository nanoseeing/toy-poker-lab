# AKQゲーム④ IPの最適Bet size

## ルール

| 項目 | 内容 |
|---|---|
| OOPハンド | A / K / Q（各1/3・独立配布） |
| IPハンド | A / K / Q（各1/3・独立配布） |
| Street | 1 Street |
| 初期Pot | 1 |
| 有効Stack | 1 |
| 許可アクション | Check、Fold、Call、5%刻みのPot Bet（5〜95%）、All-in |
| アクション制約 | OOPのRoot戦略を全hand 100% Checkに固定。OOPはCall / FoldのみでRaise不可 |
| 勝敗判定 | A > K > Q。同じhandはTie |
| 利得計算方法 | 初期Potをデッドマネーとし、ゲーム終了時の両者の利得合計は1 |

---

## 最適戦略

### 均衡戦略

連続sizeでの均衡戦略は次のとおりです。

| 局面 | hand | 戦略 |
|---|---|---|
| IP、OOP Check後 | A | $`B^{*}=\sqrt{5/2}-1\simeq0.5811`$、すなわち58.11% Potを100% Bet |
| IP、OOP Check後 | K | Check 100% |
| IP、OOP Check後 | Q | Bet 36.75% / Check 63.25% |
| OOP、Betに直面 | K | Call 58.11% / Fold 41.89% |

5%刻みの離散actionでは60% Potが主要sizeになります。

| IP hand | 戦略 |
|---|---|
| Q | Check 62.63% / Bet 55% 2.33% / Bet 60% 35.03% |
| K | Checkほぼ100% |
| A | Bet 55% 6.58% / Bet 60% 93.41% |

### EV

| プレイヤー | EV |
|---|---:|
| IP | 0.537497132 |
| OOP | 0.462502868 |
| 合計 | 1.00 |

### 導出方法

#### 戦略の形を場合別に整理

| 局面 | プレイヤー・hand | 比較するaction | 結論 |
|---|---|---|---|
| Root | OOP(Q/K/A) | Check / Bet | Node lockによりCheck 100% |
| OOP Check後 | IP(A) | Check / 各sizeのBet | 最適sizeでValue Bet 100% |
| OOP Check後 | IP(K) | Check / 各sizeのBet | Check 100% |
| OOP Check後 | IP(Q) | Check / 各sizeのBet | CheckとBluffを混合 |
| IPのBetに直面 | OOP(Q) | Fold / Call | Fold 100% |
| IPのBetに直面 | OOP(K) | Fold / Call | 両actionを混合 |
| IPのBetに直面 | OOP(A) | Fold / Call | Call 100% |

#### IP(A/K/Q)の戦略の形

Aは全ての非Aに勝つためValue Bet、Kは弱いQに勝って強いAに負けるshowdown handなのでCheck、Qは
showdown valueがtie分しかなくBluff候補、と仮定します。後で得られる解に対して各Action EVを比較すると、
AのBetとKのCheckは他のaction以上になるため、この純粋戦略の形が自己整合的です。

#### QのBluff頻度の数学的導出

IPはAを100% Bet、KをCheck、Qを頻度 $`b`$ でBluffするとします。Bet額を $`B`$ とすると、
OOPのKをCall/Foldで無差別にする条件は、

$$
b(1+B)-B=0
\quad\Rightarrow\quad
b(B)=\frac{B}{1+B}
$$

です。

#### OOP(K)のCall頻度と最適sizeの数学的導出

IPのQはCheckするとOOPのQとのtieだけから $`1/6`$ を得ます。OOP(K)のCall率を $`c`$ とすると、
Qのbet EVは、

$$
EV_Q(B)=\frac{2-B-c(1+B)}{3}
$$

なので、Checkと無差別にする条件は、

$$
c(B)=\frac{1.5-B}{1+B}
$$

です。IP(A)のEVは、OOP(Q)がFold、Kが頻度 $`c`$ でCall、AがCallすることから、

$$
EV_A(B)=\frac{2.5+B\frac{1.5-B}{1+B}}{3}
$$

です。$`B`$に依存する部分を微分すると、

$$
\frac{d}{dB}\left(\frac{B(1.5-B)}{1+B}\right)
=\frac{1.5-2B-B^2}{(1+B)^2}
$$

です。分子を0とすると、

$$
B^{*}=\sqrt{\frac{5}{2}}-1\simeq0.581139
$$

となります。二次導関数または導関数の符号変化から最大値であり、$`b,c`$も0〜1に入ります。したがって
連続sizeの最適値は約58.1% potです。このsizeは、AがKから得るThin valueとQが負うBluff riskを
同時に最適化した結果です。

この最適sizeでの混合頻度は、

$$
b^{*}=\frac{B^{*}}{1+B^{*}}\simeq0.367544,
\qquad
c^{*}=\frac{1.5-B^{*}}{1+B^{*}}=B^{*}\simeq0.581139
$$

です。つまり連続ゲームではQを約36.75% Bluffし、OOPのKは約58.11% Callします。

#### 5%刻みの離散解との比較

60%だけを使う解析値は、

$$
b(0.6)=0.375,\qquad c(0.6)=0.5625
$$

です。ソルバーではOOP(K)が`Call 56.244% / Fold 43.756%`となり、解析値と一致しました。

#### なぜAll-inではないのか

All-inはKから1 stackを取れる一方、KのCall頻度を25%まで下げます。約58% betならKを約60%近く
Callさせ、Aがより頻繁にThin valueを得られます。QのBluff riskも小さくなるため、必要なBluff量と
KのCall量を最も効率よく釣り合わせる中間sizeが選ばれます。

---

## ポーカーにおける概念理解

このゲームは、最大sizeより中間sizeの方が高EVになり得ることを、Thin valueとBluff riskの両面から示します。
Aは大きくBetすればCall時に多く得られますが、KのCall頻度が下がります。約58% Potは、AがKからValueを
得る頻度とQのBluff costを最も効率よく釣り合わせるsizeです。

---

## Solverによる再現結果

| 指標 | 結果 |
|---|---:|
| IP EV | 0.537497132 |
| OOP EV | 0.462502868 |
| Exploitability | `5.0386e-6`（Constrained Nash gap） |

- [Strategy Viewer](../../public/studies/akq_symmetric_ip_betting/strategy_viewer.html)
- [計算条件](../../public/studies/akq_symmetric_ip_betting/resolved_config.json)

### 再現方法

```bash
toy-poker run configs/experiments/study_akq_symmetric_oop_check_ip_variable_size_dcfr.toml
```

---

## その他備考

Node lockを破る通常Exploitabilityは`0.15579`です。これはOOP全checkというルールを外した元ゲームの
指標であり、本教材の収束判定にはconstrained Nash gapを使います。
