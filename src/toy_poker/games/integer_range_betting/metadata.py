"""Human-readable metadata for the integer range betting game."""

from toy_poker.games.base import GameMetadata


METADATA = GameMetadata(
    game_id="integer_range_betting",
    open_spiel_name="python_integer_range_betting",
    title="Integer 1-N custom-size toy poker",
    player_names=("IP", "OOP"),
    utility_unit="chips (initial pot is dead money)",
    parameters={
        "initial_pot": 1.0,
        "oop_stack": 4.0,
        "ip_stack": 4.0,
        "min_card": 1,
        "max_card": 10,
        "num_ranks": 10,
        "oop_rank_weights": "uniform",
        "ip_rank_weights": "uniform",
        "bet_fractions": "0.3333333333333333,1.0",
        "minimum_raise": "standard no-limit minimum raise",
        "streets": 1,
    },
)
