# AKQJ game: K vs AQJ, two streets with variable size

> Status: `解析解あり`・`数値検証済み`

## ルール

| 項目 | 内容 |
|---|---|
| Street | 2 street。public runoutなし |
| OOP range | K 100% |
| IP range | J / Q / Aを各1/3 |
| 強さ | A > K > Q > J |
| 初期pot / stack | pot 1、両者stack 4 |
| Bet / Raise size | 25/50/75/100/125/150% pot、All-in |
| Raise制約 | 標準minimum raise。両者Raise可能 |
| Street遷移 | Check-checkまたはbet-callで同じrankのまま次streetへ進む |
| Node lock | なし |
| 利得 | 終端利得の合計は常に1 |

## Solverが選んだ戦略

OOPはrootを100% Checkしました。IPの1st-street戦略は次です。

| IP | Check | Bet 100% |
|---|---:|---:|
| J | 37.50% | 62.46% |
| Q | 37.50% | 62.46% |
| A | 約0% | 99.94% |

OOPはpot betへCall/Foldを各50%。bet-call後の2nd streetでは、IPのJ/Qが40%、Aが100%を
All-inします。25〜150%の候補を与えても、on-pathの1st streetではpot betだけが残りました。

## 純粋戦略になる部分

OOPのKはAにだけ負け、J/Qには勝つbluff catcherです。先打ちではvalue handを持たないためrootをCheckします。
IPのAは唯一のvalue handなので、主要なbet-call経路では両streetをbetします。J/QはKに勝てず、blocker差も
ないため同価値のbluff候補です。ここまでが戦略の形で、各bluff頻度とsizeは以下の無差別条件から決まります。

## Geometric pot betが最適になる証明

### 2nd streetのCall率

1st-street bet額を $B$、Call後に残りstack $C=4-B$ を2nd streetでbetするとします。
2nd streetのpotは $1+2B$ です。

riverでbluffとCheckを無差別にするOOPのCall率は、

\[
c_2=\frac{1+2B}{1+B+4}
\]

です。

### 1st streetで開始できるbluff量

OOPが1st betをCallした場合、Aに対する期待損失の大きさは$B+c_2C$です。J/Qに対しては、IPが
2nd streetでCheckしても均衡頻度でbluffしても、OOPの期待利得は$1+B$です。したがって、

$$
x(B)(1+B)=B+c_2C
$$

が1st Call/Foldの無差別条件になり、次の$x(B)$が得られます。

$$
x(B)=\frac{B+c_2C}{1+B}
=\frac{4+12B-B^2}{(1+B)(5+B)}
$$

bet rangeに対するOOPの期待利得が0で、J/Qの均衡利得も0なので、constant-sum 1からIPのAの利得は
$1+x(B)$になります。したがってIPは$x(B)$を最大化します。

### sizeの最大化

微分を分母まで書くと、

\[
x'(B)=\frac{-18(B-1)(B+2)}{(B^2+6B+5)^2}
\]

です。合法範囲 $0\le B\le4$ では $B=1$ が一意な最大値です。Call後のpotは3、残りstackも3
なので、2nd streetもpot-sized All-inになります。したがって両streetのpot比率が等しい
geometric betが、単なる事前指定ではなく戦略から内生的に選ばれます。

この閉形式は、主要なpolar経路でOOPがCall/Foldし、IPが2nd streetで残stackをbetする戦略クラスを
backward inductionしたものです。元の有限ゲームにはRaiseと他sizeもあります。保存runではpot betに対する
Raiseや他の1st-street sizeのAction EVが上回らず、この解析解が拡張ゲームでも均衡条件を満たすことを
数値的に確認しています。

## Bluff配分

$B=1$を代入すると、

\[
x(1)=1.25
\]

です。J/Qへ均等配分すると各62.5%。最終streetまで残す総bluff massは0.5なので各handの
40%、rootからは`62.5% × 40% = 25%`がbarrelします。

## Solver結果

| 指標 | 結果 |
|---|---:|
| Iterations | 4,000 / 10,000 |
| Exploitability | `3.6924e-6` |
| IP EV | 0.749997846 |
| OOP EV | 0.250002154 |

- [Strategy Viewer](../../public/studies/akqj_two_street_variable_size/strategy_viewer.html)
- [計算条件](../../public/studies/akqj_two_street_variable_size/resolved_config.json)

## 注意

Check-check後の2nd streetにはAがほぼ残らないため、Kは常に勝っています。その枝のCheckや小betは
同じEVになり、混合は非一意です。geometric optimalityはAがbet-call経路を通る主要枝で判断します。

## 再現方法

```bash
toy-poker run configs/experiments/study_akqj_two_street_variable_size_dcfr.toml
```
