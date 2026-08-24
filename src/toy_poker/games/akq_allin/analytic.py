"""Analytic reference solution for regression tests and reports."""

ANALYTIC_STRATEGY = {
    "P1|A|ROOT": {"Check": 0.0, "All-in": 1.0},
    "P1|Q|ROOT": {"Check": 0.5, "All-in": 0.5},
    "P0|K|ALL_IN": {"Call": 0.5, "Fold": 0.5},
    # One member of the equilibrium family: IP's all-in rate may be [0, 0.5].
    "P0|K|CHECK": {"Check": 1.0, "All-in": 0.0},
    "P1|A|CHECK-ALL_IN": {"Call": 1.0, "Fold": 0.0},
    "P1|Q|CHECK-ALL_IN": {"Call": 0.0, "Fold": 1.0},
}

ANALYTIC_RETURNS = (-0.25, 0.25)
