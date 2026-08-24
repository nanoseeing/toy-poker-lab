"""Analytic reference solution for regression tests and reports."""

def analytic_strategy(effective_stack: float) -> dict[str, dict[str, float]]:
    if effective_stack <= 0:
        raise ValueError("effective_stack must be positive")
    bluff = effective_stack / (1.0 + effective_stack)
    call = 1.0 / (1.0 + effective_stack)
    return {
        "P1|K|ROOT": {"Check": 1.0, "All-in": 0.0},
        "P0|A|CHECK": {"Check": 0.0, "All-in": 1.0},
        "P0|Q|CHECK": {"Check": 1.0 - bluff, "All-in": bluff},
        "P1|K|CHECK-ALL_IN": {"Call": call, "Fold": 1.0 - call},
        "P0|A|ALL_IN": {"Call": 1.0, "Fold": 0.0},
        "P0|Q|ALL_IN": {"Call": 0.0, "Fold": 1.0},
    }


def analytic_returns(effective_stack: float) -> tuple[float, float]:
    centered_ip_value = effective_stack / (2.0 * (1.0 + effective_stack))
    return (0.5 + centered_ip_value, 0.5 - centered_ip_value)
