# Toy Poker Experiments

OpenSpielを利用して有限のtoy poker gameを定義し、CFR+による求解、解析、
可視化を再現可能な設定から実行するプロジェクトです。

## Quick start

```bash
python -m pip install -e '.[dev]'
toy-poker list-games
toy-poker run configs/experiments/akq_allin_cfr_plus.toml
```

各runは `artifacts/<game>/<run-id>/` に分けて保存されます。保存された
`policy.json` はC++ソルバーから独立しており、再求解せずレポートを再生成できます。

```bash
toy-poker report artifacts/akq_allin/<run-id>
```

## Documentation

- [文書の構成と更新方針](docs/README.md)
- [toyゲーム一覧](docs/games/README.md)
- [AKQ all-inゲーム](docs/games/akq_allin.md)
- [AKQJ all-inゲーム](docs/games/akqj_allin.md)
- [AKQJ two-street geometricゲーム](docs/games/akqj_two_street.md)
- [Integer 1-10 custom-sizeゲーム](docs/games/integer_range_betting.md)
- [実験設定・CLI・artifact](docs/experiments.md)

実行可能なAKQ設定例は
[`configs/experiments/akq_allin_cfr_plus.toml`](configs/experiments/akq_allin_cfr_plus.toml)
です。
