# AKQゲーム① PolarなBetについて

## ルール

| 項目 | 内容 |
|---|---|
| OOPハンド | K（100%） |
| IPハンド | A / Q（各50%） |
| Street | 1 Street |
| 初期Pot | 1 |
| 有効Stack | 1 |
| 許可アクション | Check、All-in、Call、Fold |
| 勝敗判定 | A > K > Q |
| 利得計算方法 | 初期Potをデッドマネーとし、両者の終端利得の合計は1 |

---

## 最適戦略

### 均衡戦略

| 局面 | 戦略 |
|---|---|
| OOP(K)、root | Check 100% |
| IP(A)、Check後 | All-in 100% |
| IP(Q)、Check後 | All-in 50% / Check 50% |
| OOP(K)、All-inに直面 | Call 50% / Fold 50% |

### EV

| プレイヤー | EV |
|---|---:|
| IP | 0.75 |
| OOP | 0.25 |
| 合計 | 1.00 |

### 導出方法

#### 純粋戦略のヒューリスティック解釈

IPのAは常にKへ勝ちます。Checkなら初期pot 1を獲得しますが、All-inならOOPがCallする確率 $`c`$ だけ
追加の1を獲得できるため、$`c>0`$ではAll-inがCheckより厳密に高利得です。したがってAは100% All-inします。

OOPがKで先にAll-inすると、IPはAをCall、QをFoldできます。そのときOOPの利得は、

$$
\frac{1}{2}(-1)+\frac{1}{2}(1)=0
$$

です。後述の均衡でCheckしたKの期待利得は0.25なので、OOPは自分からAll-inせず100% Checkします。
QはCheckすると必ずKに負けるため利得0ですが、All-inにもriskとFold equityがあり、ここだけが混合候補になります。

#### QのBluff頻度の数学的導出

IP(Q)のbluff率を $`b`$、OOP(K)のCall率を $`c`$ とします。OOPがAll-inに直面したとき、IPの事前確率は
Aが$`1/2`$、Qが$`b/2`$です。共通の$`1/2`$を除けば、bet range内の重みは`A : Q = 1 : b`です。

KがCallすると、Qには`+2`、Aには`-1`の利得です。KをCallとFoldで無差別にするには、

$$
2b-1=0 \quad\Rightarrow\quad b=\frac{1}{2}
$$

です。これはbet range全体ではQが1/3、Aが2/3、すなわちvalue:bluffが2:1であることを
意味します。

#### KのCall頻度の数学的導出

QはCheckするとKに負けて利得0です。All-inしたときは、Foldされると`+1`、Callされると`-1`なので、

$$
(1-c)-c=0 \quad\Rightarrow\quad c=\frac{1}{2}
$$

です。pot-sized betに対するMDF (1/(1+1)=1/2) と一致します。

#### ゲーム価値

AのAll-inは、Fold時に1、Call時に2を得るため、$`c=1/2`$では期待利得1.5です。QはCheckとAll-inの
どちらでも利得0です。IPはA/Qを各1/2で持つので、

$$
EV_{IP}=\frac{1}{2}(1.5)+\frac{1}{2}(0)=0.75,
\qquad EV_{OOP}=1-0.75=0.25
$$

となります。これで使用する全アクションの無差別条件とゲーム価値が一致します。

---

## ポーカーにおける概念理解

このゲームでは、pot-sized All-inのValue:Bluff比、MDF、Pot odds、Positionが同じ無差別条件から
どのように現れるかを学びます。

IPはAというNut advantageと、Qという自然なBluff候補を同数持ちます。必要なBluffはA 1 comboに
対してQ 0.5 comboだけなので、Qの半分をCheckできます。OOPにはKしかなくRange advantageも
Nut advantageもないため、先にBetしてPolar rangeを表現できません。

要点は次の3点です。

1. Pot-sized river BetのValue:Bluff比は2:1。
2. OOPのCall頻度はMDFと同じ50%。
3. IPのPolar rangeはKだけのBluff-catching rangeに対して`0.75 Pot`のEVを得る。

---

## Solverによる再現結果

固定カード版`akq_allin`とは別に、strategy viewerを生成できるinteger-range solverへ
`1=Q, 2=K, 3=A`を割り当て、OOP weightを`0,1,0`、IP weightを`1,0,1`として再現しました。

| 指標 | 結果 |
|---|---:|
| IP EV | 0.75 |
| OOP EV | 0.25 |
| Exploitability | 0 |

- [Strategy Viewer](../../public/studies/akq_k_vs_aq_allin/strategy_viewer.html)
- [計算条件](../../public/studies/akq_k_vs_aq_allin/resolved_config.json)

### 再現方法

```bash
toy-poker run configs/experiments/study_akq_k_vs_aq_allin_dcfr.toml
```
