# Toy poker strategy studies

このREADMEを学習の起点とします。ゲーム実装の仕様は[`docs/games`](../games/README.md)、ここでは
最適戦略の数学、solverによる再現、実戦への読み替えを扱います。

## 推奨する学習順序

| 順番 | 文書 | 状態 | 主な学習内容 |
|---:|---|---|---|
| 1 | [ゲーム理論の基本用語](game_theory_basics.md) | 基礎 | 利得、終端、純粋/混合戦略、Nash均衡、無差別条件 |
| 2 | [ポーカー戦略の基本概念](concepts.md) | 基礎 | polarization、bluff:value比、MDF、position |
| 3 | [K vs AQ, All-in](akq_k_vs_aq_allin.md) | 解析解・数値検証済み | 最小のvalue/bluff比とMDF |
| 4 | [K vs AQ, variable size](akq_k_vs_aq_variable_size.md) | 解析解・数値検証済み | polar側が最大sizeを選ぶ条件 |
| 5 | [Symmetric AKQ, All-in](akq_symmetric_allin.md) | 解析解・数値検証済み | OOP checking range、IP polarization、tie |
| 6 | [Symmetric AKQ, OOP forced check](akq_symmetric_ip_betting.md) | 解析解・数値検証済み | 約58%の最適size、thin value |
| 7 | [Symmetric AKQ, variable size](akq_symmetric_variable_size.md) | 数値検証済み | block bet、Raise、checking-range防御 |
| 8 | [K vs AQJ, two-street pot betting](akqj_two_street_pot.md) | 解析解・数値検証済み | future street、street別bluff配分 |
| 9 | [K vs AQJ, two-street variable size](akqj_two_street_variable_size.md) | 解析解・数値検証済み | geometric sizingの内生的選択 |
| 10 | [Polar multi-street generalization](polar_multi_street_generalization.md) | 解析済み | $n$-street geometric betting |
| 11 | [Symmetric AKQ, two street](akq_symmetric_two_street.md) | 数値検証済み | positionとfuture streetの相互作用 |
| 12 | [0–1 approximation N=50, one street](zero_one_n50_one_street.md) | 数値検証済み | root sizing、nut check、range protection |
| 13 | [0–1 approximation N=50, two street](zero_one_n50_two_street.md) | 数値検証済み | delayed aggression、street別polarization |

最初の2文書を読んだ後、3から順に進む構成です。後のStudyは、それ以前に導入した無差別条件や
ポーカー用語を前提にします。

## Statusの意味

- `解析解あり`: 成立条件を含む閉形式または厳密な無差別条件を記載しています。
- `数値検証済み`: 保存した設定とsolver結果があり、収束指標を確認しています。
- `考察`: solver未検証の仮説を含み、検証済みの結論とは区別します。

各Studyの数値は初期pot 1をデッドマネーとするプラスサム利得です。両者EVの合計は1です。
