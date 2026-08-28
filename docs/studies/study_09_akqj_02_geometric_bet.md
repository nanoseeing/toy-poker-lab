# AKQJゲーム② Geometric Bet

## ルール

| 項目 | 内容 |
|---|---|
| OOPハンド | K（100%） |
| IPハンド | A / Q / J（各1/3） |
| Street | 2 Street |
| 初期Pot | 1 |
| 有効Stack | 4 |
| 許可アクション | Check、Fold、Call、Stackの範囲内の任意サイズのBet・Raise、All-in |
| 勝敗判定 | A > K > Q > J |
| Street遷移 | Check–CheckまたはBet–Callで同じhandのまま次streetへ進む |
| 利得計算方法 | 初期Potをデッドマネーとし、ゲーム終了時の両者の利得合計は1 |

---

## 最適戦略

### 均衡戦略

連続サイズゲームの対称なAir配分を使う均衡は次のとおりです。

| IP | Check | Bet 100% |
|---|---:|---:|
| J | 37.5% | 62.5% |
| Q | 37.5% | 62.5% |
| A | 0% | 100% |

OOPはPot BetへCall/Foldを各50%。Bet–Call後の2nd streetでは、IPのJ/Qが40%、Aが100%を
All-inします。

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

このように、IPが「Aなら必ず勝ち、Q/Jなら必ず負ける」と自分のhandの役割を完全に識別できる静的ゲームを、
clairvoyance gameと呼びます。Streetが進んでもhandの強さは変わりません。

static clairvoyance gameには、OOPがCheckしてBluff catcherとして応答し、IPがNutsをValue、AirをBluffとして
Betする既知の均衡があります。ここではこの均衡構造を使い、1st-streetのBet sizeを変数としてGeometric Pot Betを
導出します。game tree全体の均衡構成は長くなるため省略し、一般化と出典をStudy 10にまとめます。

#### 2nd StreetのCall率

有効Stackを $`S`$、1st-street Bet額を $`B`$、Call後に残る $`S-B`$ を2nd streetでBetするとします。
2nd streetのpotは $`1+2B`$ です。

riverでBluffとCheckを無差別にするOOPのCall率は、

$$
c_2=\frac{1+2B}{1+B+S}
$$

です。

#### 1st Streetで開始できるBluff量

OOPが1st betをCallした場合、Aに対する期待損失の大きさは $`B+c_2(S-B)`$です。J/Qに対しては、IPが
2nd streetでCheckしても均衡頻度でBluffしても、OOPの期待利得は$`1+B`$です。したがって、

$$
x_S(B)(1+B)=B+c_2(S-B)
$$

が1st Call/Foldの無差別条件になり、次の $`x_S(B)`$ が得られます。

$$
x_S(B)=\frac{S+3SB-B^2}{(1+B)(1+B+S)}
$$

Bet rangeに対するOOPの期待利得が0で、J/Qの均衡利得も0であり、両者の利得合計が1なので、IPのAの利得は
$`1+x_S(B)`$になります。したがってIPは$`x_S(B)`$を最大化します。

#### Sizeの最大化

微分の符号を決める分子は、正の定数因子を除いて、

$$
S-2B(B+1)
$$

です。これは $`B`$について厳密に減少するため、唯一の大域的最大値は、

$$
B_{\mathrm{opt}}=\frac{\sqrt{1+2S}-1}{2}
$$

です。$`S=4`$では $`B_{\mathrm{opt}}=1`$になります。また、最適条件
$`S=2B_{\mathrm{opt}}^2+2B_{\mathrm{opt}}`$から、

$$
S-B_{\mathrm{opt}}=B_{\mathrm{opt}}(1+2B_{\mathrm{opt}})
$$

なので、Call後の残りStackは、次StreetのPot $`1+2B_{\mathrm{opt}}`$に対して再び
$`B_{\mathrm{opt}}`$倍です。したがって
両StreetのPot比率が等しいgeometric betが、事前指定ではなく戦略から内生的に選ばれます。

2nd streetで残りStackをBetすることは、1 StreetのPolarゲームで最大sizeが最適になるStudy 02の結果から
従います。上の微分は、既知の均衡構造の中で1st-street sizeを任意に動かしたとき、開始できるBluff量を
大域的に最大化するsizeがGeometric Betであることを証明しています。

KのLeadやRaiseに対しても、static clairvoyance gameの均衡では逸脱を有利にしない応答戦略を構成できます。
以下ではsizeとBluff頻度の計算に焦点を絞ります。

#### Bluff配分

$`B=1`$を代入すると、

$$
x_4(1)=1.25
$$

です。J/Qへ均等配分すると各62.5%。最終streetまで残す総Bluff massは0.5なので各handの
40%、rootからは`62.5% × 40% = 25%`がbarrelします。

---

## ポーカーにおける概念理解

Geometric Betは、複数Streetで同じPot比率を使い、Bet–Callが続いたときに最後のStreetでStackを
使い切るsizeです。このゲームでは連続的に選べるsizeの中からPot Betが、OOPの無差別条件とIPの
Bluff供給量を同時に最大化するため、均衡から内生的に選ばれます。

---

## Solverによる再現結果

Solverは連続actionを直接扱えないため、解析解の100% Potに25/50/75/125/150%を比較候補として加えています。

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

一般の $`S`$に対するsize最大化とStack 4の戦略は
[`analytic.py`](../../src/toy_poker/games/akqj_two_street/analytic.py)で計算し、テストしています。

---

## その他備考

Check-check後の2nd streetにはAがほぼ残らないため、Kは常に勝っています。その枝のCheckや小betは
同じEVになり、混合は非一意です。geometric optimalityはAがBet–Call経路を通る主要枝で判断します。

一般のstatic clairvoyance gameの解析上の根拠は、Study 10の「解析解の出典」に記載しています。
