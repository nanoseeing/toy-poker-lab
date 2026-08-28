"""Closed-form results for the static K versus A/Q/J two-street game."""

from __future__ import annotations

import math


def geometric_fraction(effective_stack: float, streets: int) -> float:
    """Return the equal pot fraction that exhausts ``effective_stack``."""
    if effective_stack <= 0.0:
        raise ValueError("effective_stack must be positive")
    if streets <= 0:
        raise ValueError("streets must be positive")
    return ((1.0 + 2.0 * effective_stack) ** (1.0 / streets) - 1.0) / 2.0


def first_bluff_mass_two_street(effective_stack: float, first_bet: float) -> float:
    """Return air mass per unit value that can start a two-street polar line.

    The second-street action is a shove of the remaining stack.  ``first_bet``
    and ``effective_stack`` are measured in initial-pot units.
    """
    if effective_stack <= 0.0:
        raise ValueError("effective_stack must be positive")
    if not 0.0 <= first_bet <= effective_stack:
        raise ValueError("first_bet must be between zero and the stack")
    numerator = effective_stack + 3.0 * effective_stack * first_bet - first_bet**2
    denominator = (1.0 + first_bet) * (1.0 + first_bet + effective_stack)
    return numerator / denominator


def akqj_two_street_equilibrium(effective_stack: float = 4.0) -> dict[str, float]:
    """Return the symmetric-air equilibrium of the static clairvoyance game."""
    first_bet = geometric_fraction(effective_stack, 2)
    second_pot = 1.0 + 2.0 * first_bet
    second_bet = effective_stack - first_bet
    first_bluff_mass = first_bluff_mass_two_street(effective_stack, first_bet)
    final_bluff_mass = second_bet / (second_pot + second_bet)
    barrel = final_bluff_mass / first_bluff_mass
    call = 1.0 / (1.0 + first_bet)
    ip_ev = (1.0 + first_bluff_mass) / 3.0
    return {
        "first_bet": first_bet,
        "second_bet": second_bet,
        "first_bet_fraction": first_bet,
        "second_bet_fraction": second_bet / second_pot,
        "air_first_bet": first_bluff_mass / 2.0,
        "air_barrel_conditional": barrel,
        "air_final_barrel": final_bluff_mass / 2.0,
        "oop_first_call": call,
        "oop_second_call": second_pot / (second_pot + second_bet),
        "ip_ev": ip_ev,
        "oop_ev": 1.0 - ip_ev,
    }
