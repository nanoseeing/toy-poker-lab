# `<study title>`

> Status: `解析解あり` / `数値検証済み` / `考察`

## ルール

| 項目 | 内容 |
|---|---|
| Street | |
| OOP range | |
| IP range | |
| Pot / stack | |
| Bet / raise | |
| Showdown | |
| 利得 | 終端利得の基準とconstant-sumを記載 |

## このゲームで検証する問い

- 数学的に何を導くか
- どのポーカー概念を切り分けるか

## 最適戦略

主要なon-path戦略を表にします。非一意な混合とoff-path戦略は分けて記載します。

## 数学的導出

純粋戦略は、他actionとの利得比較とrange全体での役割を説明します。混合戦略は、混合する全actionの
期待利得を等置し、相手を無差別にする式から頻度を正確に導きます。閉形式がない場合は無理に式を作らず、
数値解で満たしているAction EVの等式とbest-response条件を明記します。

pot odds、無差別条件、value/bluff比、ゲーム価値は、利得の基準を明示して導きます。

## Solverによる再現

| 指標 | 結果 |
|---|---:|
| Iterations | |
| Exploitability / constrained Nash gap | |
| IP EV | |
| OOP EV | |

- [Strategy Viewer](../../public/studies/<study_id>/strategy_viewer.html)
- [計算条件](../../public/studies/<study_id>/resolved_config.json)

![Root strategy](../../public/studies/<study_id>/figures/root_strategy.png)

## ポーカー的解釈

該当する概念だけを扱い、モデルに存在しないblockerやdynamic equityを実在するようには説明しません。

## 実戦への応用と限界

- NLHEへ移せる原理
- 抽象化で除かれている要素
- 結論が変わる条件

## 要点

1. `<要点1>`
2. `<要点2>`
3. `<要点3>`

## 再現方法

```bash
toy-poker run configs/experiments/<config>.toml
```
