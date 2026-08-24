"""Human-readable metadata for the AKQJ all-in game."""

from toy_poker.games.base import GameMetadata

INFORMATION_LABELS = {
    "P1|K|ROOT": "OOP(K): first action",
    "P0|A|CHECK": "IP(A): after OOP check",
    "P0|Q|CHECK": "IP(Q): after OOP check",
    "P0|J|CHECK": "IP(J): after OOP check",
    "P1|K|CHECK-ALL_IN": "OOP(K): facing IP all-in",
    "P0|A|ALL_IN": "IP(A): facing OOP all-in",
    "P0|Q|ALL_IN": "IP(Q): facing OOP all-in",
    "P0|J|ALL_IN": "IP(J): facing OOP all-in",
}

METADATA = GameMetadata(
    game_id="akqj_allin",
    open_spiel_name="python_akqj_allin",
    title="AKQJ all-in toy poker",
    player_names=("IP", "OOP"),
    utility_unit="chips (initial pot is dead money)",
    information_labels=INFORMATION_LABELS,
    parameters={"initial_pot": 1.0, "oop_stack": 1.0, "ip_stack": 1.0},
)
