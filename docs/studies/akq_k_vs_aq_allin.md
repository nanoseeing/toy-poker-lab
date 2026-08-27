# AKQ game: K vs AQ, All-in only

> Status: `解析解あり`・`数値検証済み`

## ルール

| 項目 | 内容 |
|---|---|
| Street | River相当の1 street。runoutなし |
| OOP range | K 100% |
| IP range | A / Qを各50% |
| 強さ | A > K > Q |
| Pot / stack | 初期pot 1、実効stack 1 |
| Action | Check、All-in、Call、Fold |
| 利得 | 初期potはデッドマネーで、終端利得の合計は常に1 |

## このゲームで検証する問い

- pot-sized All-inのvalue/bluff比を無差別条件から導けるか。
- polar rangeを持つIPが、Kだけのbluff-catching rangeへどれだけEVを得るか。
- MDF、pot odds、positionが同じ数式のどこに現れるか。

## 最適戦略

| 局面 | 戦略 |
|---|---|
| OOP(K)、root | Check 100% |
| IP(A)、Check後 | All-in 100% |
| IP(Q)、Check後 | All-in 50% / Check 50% |
| OOP(K)、All-inに直面 | Call 50% / Fold 50% |

ゲーム価値は`IP EV = 0.75`、`OOP EV = 0.25`です。

## 数学的導出

### 純粋戦略になる部分

IPのAは常にKへ勝ちます。Checkなら初期pot 1を獲得しますが、All-inならOOPがCallする確率 $c$ だけ
追加の1を獲得できるため、$c>0$ではAll-inがCheckより厳密に高利得です。したがってAは100% All-inします。

OOPがKで先にAll-inすると、IPはAをCall、QをFoldできます。そのときOOPの利得は、

$$
\frac12(-1)+\frac12(1)=0
$$

です。後述の均衡でCheckしたKの期待利得は0.25なので、OOPは自分からAll-inせず100% Checkします。
QはCheckすると必ずKに負けるため利得0ですが、All-inにもriskとFold equityがあり、ここだけが混合候補になります。

### Qのbluff頻度

IP(Q)のbluff率を $b$、OOP(K)のCall率を $c$ とします。OOPがAll-inに直面したとき、IPの事前確率は
Aが$1/2$、Qが$b/2$です。共通の$1/2$を除けば、bet range内の重みは`A : Q = 1 : b`です。

KがCallすると、Qには`+2`、Aには`-1`の利得です。KをCallとFoldで無差別にするには、

\[
2b-1=0 \quad\Rightarrow\quad b=\frac12
\]

です。これはbet range全体ではQが1/3、Aが2/3、すなわちvalue:bluffが2:1であることを
意味します。

### KのCall頻度

QはCheckするとKに負けて利得0です。All-inしたときは、Foldされると`+1`、Callされると`-1`なので、

\[
(1-c)-c=0 \quad\Rightarrow\quad c=\frac12
\]

です。pot-sized betに対するMDF (1/(1+1)=1/2) と一致します。

### ゲーム価値

AのAll-inは、Fold時に1、Call時に2を得るため、$c=1/2$では期待利得1.5です。QはCheckとAll-inの
どちらでも利得0です。IPはA/Qを各1/2で持つので、

$$
EV_{IP}=\frac12(1.5)+\frac12(0)=0.75,
\qquad EV_{OOP}=1-0.75=0.25
$$

となります。これで使用する全アクションの無差別条件とゲーム価値が一致します。

## Solverによる再現

固定カード版`akq_allin`とは別に、strategy viewerを生成できるinteger-range solverへ
`1=Q, 2=K, 3=A`を割り当て、OOP weightを`0,1,0`、IP weightを`1,0,1`として再現しました。

| 指標 | 結果 |
|---|---:|
| Iterations | 2,000 / 10,000 |
| Exploitability | 0 |
| IP EV | 0.75 |
| OOP EV | 0.25 |

- [Strategy Viewer](../../public/studies/akq_k_vs_aq_allin/strategy_viewer.html)
- [計算条件](../../public/studies/akq_k_vs_aq_allin/resolved_config.json)

## ポーカー的解釈

IPはAというnut advantageと、Qという自然なbluff候補を同数持ちます。必要なbluffはA 1 comboに
対してQ 0.5 comboだけなので、Qの半分をCheckできます。OOPにはKしかなくrange advantageも
nut advantageもないため、先にbetしてpolar rangeを表現できません。

このゲームにはcard removalがないので、Qの50%をどのcomboで選ぶかというblocker問題は扱いません。

## 要点

1. pot-sized river betのvalue:bluff比は2:1。
2. OOPのCall頻度はMDFと同じ50%。
3. IPのpolar rangeはKだけのbluff-catching rangeに対して`0.75 pot`のEVを得る。

## 再現方法

```bash
toy-poker run configs/experiments/study_akq_k_vs_aq_allin_dcfr.toml
```
