# Toy Poker Experiments

Configuration-driven OpenSpiel experiments for finite toy poker games.

The bundled AKQ game has OOP holding K and acting first, while IP is dealt A
or Q with equal probability. The pot is fixed at 1. Configure each player's
stack independently in the experiment TOML; both default to 1. Unmatched
all-in excess is returned, so only the effective stack is at risk.

```bash
python -m pip install -e '.[dev]'
toy-poker list-games
toy-poker run configs/experiments/akq_allin_cfr_plus.toml
```

```toml
[game.params]
oop_stack = 1.0
ip_stack = 1.0
```

Each run is stored in an immutable directory under `artifacts/<game>/<run-id>/`.
The saved `policy.json` is independent of the C++ solver and can be used to
re-render a report without solving again:

```bash
toy-poker report artifacts/akq_allin/<run-id>
```
