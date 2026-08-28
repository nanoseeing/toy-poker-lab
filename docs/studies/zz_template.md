# `<ゲーム系列と連番> <Study title>`

## ルール

| 項目 | 内容 |
|---|---|
| OOPハンド | ハンド、確率、配布方式 |
| IPハンド | ハンド、確率、配布方式 |
| Street | Street数 |
| 初期Pot | 初期Pot額 |
| 有効Stack | 実効Stack |
| 許可アクション | Check、Bet / Raise size、Call、Fold、All-in |
| アクション制約 | Node lock、強制Check、Raise不可など。該当しない場合は行を削除 |
| 勝敗判定 | ハンドの強弱、Tieの扱い |
| Street遷移 | 複数Streetの場合のみ。該当しない場合は行を削除 |
| 利得計算方法 | Fold・Showdown時の利得とconstant-sumの基準 |
| 補足 | その他、ルール理解に必要な事項。不要なら行を削除 |

---

## 最適戦略

### 均衡戦略

主要なon-path戦略を表にします。

| 局面 | プレイヤー | ハンド | アクション | 頻度 |
|---|---|---|---|---:|
| | | | | |

### EV

| プレイヤー | EV |
|---|---:|
| IP | |
| OOP | |
| 合計 | |

### 導出方法

#### 数学的導出

混合する全アクションの期待利得を等置し、相手を無差別にする条件から頻度を導きます。閉形式がない場合は
無理に式を作らず、数値解が満たすAction EVの等式とbest-response条件を明記します。

#### ヒューリスティック解釈

純粋戦略とrange全体の構造を、hand strengthやポーカー戦略上の役割から説明します。

---

## ポーカーにおける概念理解

MDF、Bluff:value比、Position、Bet sizingなど、このゲームで学べる概念だけを扱います。

---

## Solverによる再現結果

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

非一意な混合、Off-path戦略、Node lock、Action abstractionなど、補足がある場合だけ記載します。
不要な場合はこの節を削除します。
