# Toy Poker Experiments

Configuration-driven OpenSpiel experiments for finite toy poker games.

```bash
python -m pip install -e '.[dev]'
toy-poker list-games
toy-poker run configs/experiments/akq_allin_cfr_plus.toml
```

Each run is stored in an immutable directory under `artifacts/<game>/<run-id>/`.
The saved `policy.json` is independent of the C++ solver and can be used to
re-render a report without solving again:

```bash
toy-poker report artifacts/akq_allin/<run-id>
```
