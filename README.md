# Toy Poker Experiments

OpenSpielを利用して有限のtoy poker gameを定義し、CFR+による求解、解析、
可視化を再現可能な設定から実行するプロジェクトです。

## Quick start

```bash
python -m pip install -e '.[dev]'
toy-poker list-games
toy-poker run configs/experiments/akq_allin_cfr_plus.toml
toy-poker benchmark configs/experiments/integer_range_betting_dcfr.toml --iterations 1000
```

各runは `artifacts/<game>/<run-id>/` に分けて保存されます。保存された
`policy.json`または`policy.npz`はC++ソルバーから独立しており、再求解せずレポートを
再生成できます。
numeric rangeゲームでは、履歴選択と1〜Nの混合戦略gridを備えた
`strategy_viewer.html`も生成されます。
コミット済みの代表結果は[public results](public/results/README.md)から閲覧できます。
理論、最適戦略、実戦への読み替えは[strategy studies](docs/studies/README.md)にまとめています。

```bash
toy-poker report artifacts/akq_allin/<run-id>
toy-poker publish-results --selection configs/public_results.toml \
  --artifact-root artifacts --output-root public/results
```

## Documentation

- [文書の構成と更新方針](docs/README.md)
- [toyゲーム一覧](docs/games/README.md)
- [AKQ all-inゲーム](docs/games/akq_allin.md)
- [AKQJ all-inゲーム](docs/games/akqj_allin.md)
- [AKQJ two-street geometricゲーム](docs/games/akqj_two_street.md)
- [Integer 1-N weighted-range custom-sizeゲーム](docs/games/integer_range_betting.md)
- [Integer 1-N two-streetゲーム](docs/games/integer_range_betting_two_street.md)
- [戦略Study一覧](docs/studies/README.md)
- [実験設定・CLI・artifact](docs/experiments.md)
- [Solver構成・高速化・benchmark](docs/solvers.md)
- [公開済みの解析結果](public/results/README.md)

実行可能なAKQ設定例は
[`configs/experiments/akq_allin_cfr_plus.toml`](configs/experiments/akq_allin_cfr_plus.toml)
です。
