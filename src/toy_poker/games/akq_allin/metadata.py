"""Human-readable metadata for the AKQ all-in game."""

from toy_poker.games.base import GameMetadata

INFORMATION_LABELS = {
    "P1|A|ROOT": "OOP(A): first action",
    "P1|Q|ROOT": "OOP(Q): first action",
    "P0|K|ALL_IN": "IP(K): facing OOP all-in",
    "P0|K|CHECK": "IP(K): after OOP check",
    "P1|A|CHECK-ALL_IN": "OOP(A): facing IP all-in",
    "P1|Q|CHECK-ALL_IN": "OOP(Q): facing IP all-in",
}

METADATA = GameMetadata(
    game_id="akq_allin",
    open_spiel_name="python_akq_allin",
    title="AKQ all-in toy poker",
    player_names=("IP", "OOP"),
    utility_unit="net chips",
    information_labels=INFORMATION_LABELS,
    analytic_returns=(-0.25, 0.25),
    parameters={"initial_pot": 1.0, "stack_per_player": 1.0},
)
