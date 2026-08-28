# `<ゲーム系列と連番> <Study title>`

## ルール

| 項目 | 内容 |
|---|---|
| OOPハンド | hand、確率、配布方式 |
| IPハンド | hand、確率、配布方式 |
| Street | Street数 |
| 初期Pot | 初期Pot額 |
| 有効Stack | 実効Stack |
| 許可アクション | Check、任意またはルールで固定されたBet / Raise size、Call、Fold、All-in |
| アクション制約 | Node lock、強制Check、Raise不可など。該当しない場合は行を削除 |
| 勝敗判定 | handの強弱、Tieの扱い |
| Street遷移 | 複数Streetの場合のみ。該当しない場合は行を削除 |
| 利得計算方法 | Fold・showdown時の利得と、ゲーム終了時の両者の利得合計 |
| 補足 | その他、ルール理解に必要な事項。不要なら行を削除 |

---

## 最適戦略

### 均衡戦略

主要なon-path戦略を表にします。

| 局面 | プレイヤー | hand | アクション | 頻度 |
|---|---|---|---|---:|
| | | | | |

### EV

| プレイヤー | EV |
|---|---:|
| IP | |
| OOP | |
| 合計 | |

### 導出方法

#### 解析方針

このStudyで固定する条件、数学的に導出する対象、Solverで求める対象を、読者が必要な順序で簡潔に示します。
数値解から選んだBet sizeを使う場合は、「Solverで得たsizeを固定し、頻度を解析する」のように出発点を明記します。

#### 戦略の形を場合別に整理

| 局面 | プレイヤー・hand | 比較するaction | 結論・役割 |
|---|---|---|---|
| 例：Root | OOP(hand) | Check / Bet | 純粋actionまたは混合候補を明記 |

プレイヤー、hand、street、直前のactionを明示し、どの場合を説明しているか先に整理します。

#### 混合頻度の数学的導出

混合する全アクションの期待利得を等置し、相手を無差別にする条件から頻度を導きます。閉形式がない場合は
無理に式を作らず、数値解が満たすAction EVの等式と最適反応の条件を明記します。

比率だけが決まって絶対頻度が残る場合は、その自由度を明記します。絶対頻度を決めるために相手の応答戦略や
後続streetの戦略が必要なら、それらを先に導出してから絶対頻度へ戻ります。

#### Bet sizeと逸脱の検証

自由なBet sizeが使われる場合はsizeを変数として大域的な最適性を確認します。未使用size、Raise、off-pathの
応答まで証明できない場合は、証明できた範囲とSolverのaction abstractionを区別します。

#### 純粋actionとrange全体の解釈

純粋戦略とrange全体の構造を、hand strengthやポーカー戦略上の役割から説明します。

---

## ポーカーにおける概念理解

MDF、Bluff:Value比、Position、Bet sizingなど、このゲームで学べる概念だけを扱います。

---

## Solverによる再現結果

連続actionを有限候補へ離散化した場合は、ここにaction abstractionを記載します。

| 指標 | 結果 |
|---|---:|
| IP EV | |
| OOP EV | |
| Exploitability | |

- [Strategy Viewer](../../public/studies/<study_id>/strategy_viewer.html)
- [計算条件](../../public/studies/<study_id>/resolved_config.json)

![Root strategy](../../public/studies/<study_id>/figures/root_strategy.png)

### 再現方法

```bash
toy-poker run configs/experiments/<config>.toml
```

---

## その他備考

非一意な混合、off-path戦略、Node lock、action abstractionなど、補足がある場合だけ記載します。
不要な場合はこの節を削除します。
