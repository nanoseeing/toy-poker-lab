# Symmetric AKQ game: both players choose bet and raise sizes

> Status: `数値検証済み`

## ルール

| 項目 | 内容 |
|---|---|
| Street | River相当の1 street。runoutなし |
| OOP range | Q / K / Aを各1/3 |
| IP range | Q / K / Aを各1/3 |
| 配布 / 強さ | 独立配布、A > K > Q、同rankはtie |
| 初期pot / stack | pot 1、両者stack 1 |
| Bet / Raise size | 10/20/33/50/75% pot、All-in |
| Raise制約 | 標準minimum raise。両者Raise可能 |
| Node lock | なし |
| 利得 | 終端利得の合計は常に1 |

## Rootの最適戦略

| OOP rank | Check | Bet 50% |
|---|---:|---:|
| Q | 91.31% | 8.69% |
| K | 73.92% | 26.07% |
| A | 47.85% | 52.15% |

その他のroot sizeは数値誤差を除いてほぼ0%です。単純な`Q bluff / A value / K check`ではなく、
Kの一部を50% betし、Aの約半分をCheckへ残すmerged/polar混合のrangeになります。

## 数学的に確定できる条件

このゲームでは、各open sizeに対してIPがFold/Call/Raiseを選び、さらにRaise後のOOP応答まであるため、
K vs AQのような2本の無差別式だけでは閉じません。完全な閉形式解は主張せず、有限ゲームの連立した
最適反応条件をsolverで解いています。

ただし、正の頻度で混ぜるroot actionには必ず、

$$
EV_r(\mathrm{Check})=EV_r(\mathrm{Bet\ 50\%})
$$

というrank $r$ごとの無差別条件が必要です。保存runではQ/K/AのいずれもCheckとBet 50%のAction EVが
ほぼ一致し、それ以外のroot sizeはそれ以下でした。この等式だけでは各rankの混合頻度は決まりません。
IPのFold/Call/Raise頻度、OOPのRaise応答、全rangeの到達確率を同時に満たすことで初めて数値が決まります。

### 純粋戦略ではなく混合になる直観

- Qだけをbluff、Aだけをvalueにすると、IPはOOPのBetとCheckからrank構成を強く推定できます。
- Kを一部betするとIPのQ/Kからthin valueを得つつ、IPの自由なbetを先回りできます。
- KはAのRaiseに弱いため全betにはできません。
- Aを一部Checkへ残すと、IPはOOPのCheckを見ても無制限にbluff/raiseできません。

したがって、各rank単体の強さ順thresholdではなく、Bet rangeとCheck rangeを同時に守る混合になります。

## IPの主要戦略

OOPのCheck後は次です。

| IP rank | 主要戦略 |
|---|---|
| Q | Check 52.18% / All-in 34.72% / Bet 75% 13.10% |
| K | Check 100% |
| A | All-in 69.43% / Bet 75% 30.57% |

OOPの50% betに対しては次です。

| IP rank | 主要戦略 |
|---|---|
| Q | Fold 94.81% / Raise all-in 5.19% |
| K | Fold 22.58% / Call 76.10% / Raise all-in 1.32% |
| A | Raise all-in 100% |

## なぜOOPはKをbetするのか

OOPが全rangeをCheckすると、IPはpositionを使ってQ/Aをpolarizeし、Kへ大きなbetを突きつけられます。
Kの50% betには次の役割があります。

- IPに自由なbet sizeを選ばせず、自分でshowdownまでの価格を決めるblock-bet効果。
- IPのKからCallを受けるthin/merged value。
- Qのbluffと同じsizeを使い、bet rangeをAだけに限定しない。
- IPのRaise rangeを誘発し、AのCheckからの防御価値を作る。

KはAのRaiseに弱いため100% betできません。反対にAをすべてbetするとchecking rangeがQ/Kへ偏り、IPが
Check後に攻撃しやすくなるので、Aの一部をCheckへ残します。AのCheckはslow-playというより、OOPの
checking range全体を守るrange protectionです。

## 41–43型の非単調性との関係

離散rankゲームでは、隣接rankが必ず同じ主要actionになるとは限りません。複数の相手response range、
Raise、同rankのtie、checking-range防御が同時に釣り合うためです。Action EVが近い場合、個別rankの
混合は非一意またはsolver経路に敏感です。純粋なhand strengthだけでなくrange全体の制約を読みます。

## Solver結果

| 指標 | 結果 |
|---|---:|
| Iterations | 8,000 / 10,000 |
| Exploitability | `7.4617e-6` |
| IP EV | 0.530193219 |
| OOP EV | 0.469806781 |

- [Strategy Viewer](../../public/studies/akq_symmetric_variable_size/strategy_viewer.html)
- [計算条件](../../public/studies/akq_symmetric_variable_size/resolved_config.json)

## 限界

このモデルはindependent rankなのでblockerはありません。ここでの「block bet」は小sizeで価格を決める
戦略を指し、card-removalのblockerとは別概念です。また1 streetなのでdynamic equityもありません。

## 再現方法

```bash
toy-poker run configs/experiments/integer_range_betting_n3_stack_1_5_sizes_dcfr.toml
```
