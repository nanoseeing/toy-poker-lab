"""Closed-form checks for the static two-street clairvoyance game."""

import pytest

from toy_poker.games.akqj_two_street.analytic import (
    akqj_two_street_equilibrium,
    first_bluff_mass_two_street,
    geometric_fraction,
)


def test_stack_four_two_street_equilibrium():
    solution = akqj_two_street_equilibrium(4.0)

    assert solution["first_bet"] == pytest.approx(1.0)
    assert solution["second_bet"] == pytest.approx(3.0)
    assert solution["first_bet_fraction"] == pytest.approx(1.0)
    assert solution["second_bet_fraction"] == pytest.approx(1.0)
    assert solution["air_first_bet"] == pytest.approx(0.625)
    assert solution["air_barrel_conditional"] == pytest.approx(0.4)
    assert solution["air_final_barrel"] == pytest.approx(0.25)
    assert solution["oop_first_call"] == pytest.approx(0.5)
    assert solution["oop_second_call"] == pytest.approx(0.5)
    assert solution["ip_ev"] == pytest.approx(0.75)
    assert solution["ip_ev"] + solution["oop_ev"] == pytest.approx(1.0)


@pytest.mark.parametrize("stack", [0.5, 1.0, 4.0, 10.0])
def test_geometric_first_bet_is_global_maximum_of_supported_bluff_mass(stack):
    optimum = geometric_fraction(stack, 2)
    optimum_mass = first_bluff_mass_two_street(stack, optimum)

    # The derivative has the sign of S - 2B(B+1), so it changes from positive
    # to negative exactly once at the geometric size.
    assert 2.0 * optimum**2 + 2.0 * optimum - stack == pytest.approx(0.0)
    for step in range(1001):
        bet = stack * step / 1000.0
        assert first_bluff_mass_two_street(stack, bet) <= optimum_mass + 1e-12
