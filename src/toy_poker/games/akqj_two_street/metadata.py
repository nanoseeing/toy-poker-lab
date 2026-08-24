"""Human-readable metadata for the AKQJ two-street game."""

from toy_poker.games.base import GameMetadata


METADATA = GameMetadata(
    game_id="akqj_two_street",
    open_spiel_name="python_akqj_two_street",
    title="AKQJ two-street geometric toy poker",
    player_names=("IP", "OOP"),
    utility_unit="chips (initial pot is dead money)",
    parameters={
        "initial_pot": 1.0,
        "oop_stack": 1.0,
        "ip_stack": 1.0,
        "streets": 2,
    },
)
