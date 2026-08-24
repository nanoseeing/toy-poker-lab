"""Analytic equilibrium family and symmetric reference for AKQJ."""


def analytic_strategy(effective_stack: float) -> dict[str, dict[str, float]]:
    """Return the symmetric member of the Q/J bluff-allocation family."""
    if effective_stack <= 0:
        raise ValueError("effective_stack must be positive")
    total_bluff = effective_stack / (1.0 + effective_stack)
    bluff_per_card = total_bluff / 2.0
    call = 1.0 / (1.0 + effective_stack)
    return {
        "P1|K|ROOT": {"Check": 1.0, "All-in": 0.0},
        "P0|A|CHECK": {"Check": 0.0, "All-in": 1.0},
        "P0|Q|CHECK": {"Check": 1.0 - bluff_per_card, "All-in": bluff_per_card},
        "P0|J|CHECK": {"Check": 1.0 - bluff_per_card, "All-in": bluff_per_card},
        "P1|K|CHECK-ALL_IN": {"Call": call, "Fold": 1.0 - call},
        "P0|A|ALL_IN": {"Call": 1.0, "Fold": 0.0},
        "P0|Q|ALL_IN": {"Call": 0.0, "Fold": 1.0},
        "P0|J|ALL_IN": {"Call": 0.0, "Fold": 1.0},
    }


def analytic_returns(effective_stack: float) -> tuple[float, float]:
    centered_ip_value = (effective_stack - 1.0) / (6.0 * (1.0 + effective_stack))
    return (0.5 + centered_ip_value, 0.5 - centered_ip_value)
