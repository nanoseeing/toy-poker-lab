# AKQJゲーム② Geometric Bet

## ルール

| 項目 | 内容 |
|---|---|
| OOPハンド | K（100%） |
| IPハンド | A / Q / J（各1/3） |
| Street | 2 Street |
| 初期Pot | 1 |
| 有効Stack | 4 |
| 許可アクション | Check、Fold、Call、25/50/75/100/125/150% PotのBet・Raise、All-in |
| 勝敗判定 | A > K > Q > J |
| Street遷移 | Check–CheckまたはBet–Callで同じhandのまま次streetへ進む |
| 利得計算方法 | 初期Potをデッドマネーとし、ゲーム終了時の両者の利得合計は1 |

---

## 最適戦略

### 均衡戦略

OOPはrootを100% Checkしました。IPの1st-street戦略は次です。

| IP | Check | Bet 100% |
|---|---:|---:|
| J | 37.50% | 62.46% |
| Q | 37.50% | 62.46% |
| A | 約0% | 99.94% |

OOPはPot BetへCall/Foldを各50%。Bet–Call後の2nd streetでは、IPのJ/Qが40%、Aが100%を
All-inします。25〜150%の候補を与えても、on-pathの1st streetではpot betだけが残りました。

### EV

| プレイヤー | EV |
|---|---:|
| IP | 0.75 |
| OOP | 0.25 |
| 合計 | 1.00 |

### 導出方法

#### 戦略の形をhand・street別に整理

| street・局面 | プレイヤー・hand | 比較するaction | 結論 |
|---|---|---|---|
| 各street先頭 | OOP(K) | Check / Bet | Check 100% |
| 1st street、OOP Check後 | IP(A) | Check / 各sizeのBet | 選ばれたsizeでBet 100% |
| 1st street、OOP Check後 | IP(Q/J) | Check / 各sizeのBet | CheckとBluffを混合 |
| 1st Betに直面 | OOP(K) | Fold / Call / Raise | 主要経路ではFoldとCallを混合 |
| 2nd street、Bet–Call後 | IP(A) | Check / Bet | 残stackをBet |
| 2nd street、Bet–Call後 | IP(Q/J) | Check / Bet | CheckとBluffを混合 |

#### 各handの役割

OOPのKはAにだけ負け、J/Qには勝つBluff catcherです。先打ちではValue handを持たないためrootをCheckします。
IPのAは唯一のValue handなので、主要なBet–Call経路では両streetをBetします。J/QはKに勝てず、
同じshowdown valueを持つBluff候補です。ここまでが戦略の形で、各Bluff頻度とsizeは以下の無差別条件から決まります。

以下では、Geometric Pot Betが最適になることを後ろ向き帰納法で導出します。

#### 2nd StreetのCall率

1st-street bet額を $`B`$、Call後に残りstack $`C=4-B`$ を2nd streetでbetするとします。
2nd streetのpotは $`1+2B`$ です。

riverでBluffとCheckを無差別にするOOPのCall率は、

$$
c_2=\frac{1+2B}{1+B+4}
$$

です。

#### 1st Streetで開始できるBluff量

OOPが1st betをCallした場合、Aに対する期待損失の大きさは$`B+c_2C`$です。J/Qに対しては、IPが
2nd streetでCheckしても均衡頻度でBluffしても、OOPの期待利得は$`1+B`$です。したがって、

$$
x(B)(1+B)=B+c_2C
$$

が1st Call/Foldの無差別条件になり、次の$`x(B)`$が得られます。

$$
x(B)=\frac{B+c_2C}{1+B}
=\frac{4+12B-B^2}{(1+B)(5+B)}
$$

Bet rangeに対するOOPの期待利得が0で、J/Qの均衡利得も0であり、両者の利得合計が1なので、IPのAの利得は
$`1+x(B)`$になります。したがってIPは$`x(B)`$を最大化します。

#### Sizeの最大化

微分を分母まで書くと、

$$
x'(B)=\frac{-18(B-1)(B+2)}{(B^2+6B+5)^2}
$$

です。合法範囲 $`0\leq B\leq4`$ では $`B=1`$ が一意な最大値です。Call後のpotは3、残りstackも3
なので、2nd streetもpot-sized All-inになります。したがって両streetのpot比率が等しい
geometric betが、単なる事前指定ではなく戦略から内生的に選ばれます。

この閉形式は、主要なPolar経路でOOPがCall/Foldし、IPが2nd streetで残stackをBetする戦略クラスを
後ろ向き帰納法で解いたものです。元の有限ゲームにはRaiseと他sizeもあります。保存runではpot betに対する
Raiseや他の1st-street sizeのAction EVが上回らず、この解析解が拡張ゲームでも均衡条件を満たすことを
数値的に確認しています。

#### Bluff配分

$`B=1`$を代入すると、

$$
x(1)=1.25
$$

です。J/Qへ均等配分すると各62.5%。最終streetまで残す総Bluff massは0.5なので各handの
40%、rootからは`62.5% × 40% = 25%`がbarrelします。

---

## ポーカーにおける概念理解

Geometric Betは、複数Streetで同じPot比率を使い、Bet–Callが続いたときに最後のStreetでStackを
使い切るsizeです。このゲームでは候補sizeの一つとして与えられたPot Betが、OOPの無差別条件とIPの
Bluff供給量を同時に最大化するため、均衡から内生的に選ばれます。

---

## Solverによる再現結果

| 指標 | 結果 |
|---|---:|
| IP EV | 0.749997846 |
| OOP EV | 0.250002154 |
| Exploitability | `3.6924e-6` |

- [Strategy Viewer](../../public/studies/akqj_two_street_variable_size/strategy_viewer.html)
- [計算条件](../../public/studies/akqj_two_street_variable_size/resolved_config.json)

### 再現方法

```bash
toy-poker run configs/experiments/study_akqj_two_street_variable_size_dcfr.toml
```

---

## その他備考

Check-check後の2nd streetにはAがほぼ残らないため、Kは常に勝っています。その枝のCheckや小betは
同じEVになり、混合は非一意です。geometric optimalityはAがBet–Call経路を通る主要枝で判断します。
