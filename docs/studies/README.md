# Toy poker学習Study

このREADMEを学習の起点とします。ゲーム実装の仕様は[`docs/games`](../games/README.md)、ここでは
最適戦略の数学、ソルバーによる再現、実戦への読み替えを扱います。

## 推奨する学習順序

| 順番 | 文書 | 主な学習内容 |
|---:|---|---|
| 1 | [基礎① ゲーム理論の基本用語](study_01_game_theory_basics.md) | 展開形ゲーム、行動戦略、Nash均衡、reach、Exploitability、CFR |
| 2 | [基礎② ポーカー用語と計算](study_02_poker_terms_and_math.md) | conditional range、EV・EQ・EQR、Pot odds、MDF、range構造、SPR |
| 3 | [AKQゲーム① PolarなBetについて](study_03_akq_01_polar_bet.md) | 最小のValue:Bluff比とMDF |
| 4 | [AKQゲーム② Polar rangeのBet size](study_04_akq_02_polar_bet_sizing.md) | Polar側が最大sizeを選ぶ条件 |
| 5 | [AKQゲーム③ PositionとChecking range](study_05_akq_03_position_and_check.md) | OOP Checking range、IP Polarization、tie |
| 6 | [AKQゲーム④ IPの最適Bet size](study_06_akq_04_ip_bet_sizing.md) | 58.1139%の閉形式解、Thin value |
| 7 | [AKQゲーム⑤ OOPのBlock Bet](study_07_akq_05_bet_raise_strategy.md) | KのBlock Bet、Raiseへのrange防御 |
| 8 | [AKQJゲーム① 2 StreetのBluff戦略](study_08_akqj_01_two_street_bluff.md) | future street、street別Bluff配分 |
| 9 | [AKQJゲーム② Geometric Bet](study_09_akqj_02_geometric_bet.md) | geometric sizingの内生的選択 |
| 10 | [AKQJゲーム③ Multi-streetへの一般化](study_10_akqj_03_multi_street_generalization.md) | $`n`$-street geometric betting |
| 11 | [AKQゲーム⑥ 2 StreetのBet・Raise戦略](study_11_akq_06_two_street_strategy.md) | 離散数値解、Positionとfuture street |
| 12 | [01-game① OOPのBet戦略](study_12_01_game_01_oop_bet_strategy.md) | 離散数値解、root sizing、range protection |
| 13 | [01-game② 2 StreetのBet戦略](study_13_01_game_02_two_street_strategy.md) | 離散数値解、delayed aggression |

最初の2文書を読んだ後、3から順に進む構成です。後のStudyは、それ以前に導入した無差別条件や
ポーカー用語を前提にします。

各Studyでは初期pot 1をデッドマネーとして扱うため、OOPとIPのEV合計は1です。

執筆者向けの表記規則とテンプレートは[Study執筆ガイド](style_guide.md)に分離しています。
