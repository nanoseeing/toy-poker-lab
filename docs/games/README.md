# Toy games

実装済みゲームの一覧です。`game_id` はTOMLの `[game].id` とCLIで使用します。

| game_id | 概要 | 標準設定 | 文書 |
|---|---|---|---|
| `akq_allin` | OOP(K)対IP(A/Q)、CheckまたはAll-in | [`akq_allin_cfr_plus.toml`](../../configs/experiments/akq_allin_cfr_plus.toml) | [ルールと解析解](akq_allin.md) |
| `akqj_allin` | OOP(K)対IP(A/Q/J)、2種類のブラフ候補 | [`akqj_allin_cfr_plus.toml`](../../configs/experiments/akqj_allin_cfr_plus.toml) | [ルールと解析解](akqj_allin.md) |
| `akqj_two_street` | AKQJを2 street化し、Geometric betとAll-in raiseを追加 | [`akqj_two_street_cfr_plus.toml`](../../configs/experiments/akqj_two_street_cfr_plus.toml) | [ルールと解析方法](akqj_two_street.md) |
| `integer_range_betting` | 両者が1〜10を持ち、可変pot比率bet/raiseとminimum raiseを使用 | [`integer_range_betting_cfr_plus.toml`](../../configs/experiments/integer_range_betting_cfr_plus.toml) | [ルールと解析方法](integer_range_betting.md) |

新しいゲームの文書は [`_template.md`](_template.md) を複製して作成してください。
