"""Closed-form results for the small independent-rank poker studies.

The functions in this module are intentionally independent from a solver.  They
encode the mathematical result that a solver run is expected to reproduce.
"""

from __future__ import annotations

import math


def akq_k_vs_aq_fixed_bet(bet: float = 1.0) -> dict[str, float]:
    """Equilibrium after OOP checks in the K versus A/Q polar game.

    ``bet`` is measured in initial-pot units.  OOP has K, IP has A or Q with
    equal probability, and OOP may call or fold.  The stack-one continuous-size
    game maximizes IP's value at ``bet == 1``.
    """
    if not 0.0 < bet <= 1.0:
        raise ValueError("bet must be in (0, 1]")
    bluff = bet / (1.0 + bet)
    call = 1.0 / (1.0 + bet)
    ip_ev = (1.0 + 2.0 * bet) / (2.0 * (1.0 + bet))
    return {
        "bet": bet,
        "ip_q_bet": bluff,
        "oop_k_call": call,
        "ip_ev": ip_ev,
        "oop_ev": 1.0 - ip_ev,
    }


def symmetric_akq_allin_equilibrium() -> dict[str, float]:
    """One equilibrium of the independent A/K/Q, all-in-only game.

    The response to OOP's zero-reach root all-in is not unique.  Any IP(K) call
    frequency in [3/8, 1/2] supports the on-path equilibrium.  We return the
    lower endpoint as a canonical exact representative.
    """
    return {
        "oop_root_check": 1.0,
        "ip_q_bet_after_check": 0.5,
        "ip_k_bet_after_check": 0.0,
        "ip_a_bet_after_check": 1.0,
        "oop_q_call": 0.0,
        "oop_k_call": 0.25,
        "oop_a_call": 1.0,
        "ip_k_off_path_call": 3.0 / 8.0,
        "ip_k_off_path_call_min": 3.0 / 8.0,
        "ip_k_off_path_call_max": 0.5,
        "ip_ev": 19.0 / 36.0,
        "oop_ev": 17.0 / 36.0,
    }


def symmetric_akq_ip_continuous_bet() -> dict[str, float]:
    """Closed-form constrained equilibrium when OOP must check and cannot raise."""
    bet = math.sqrt(5.0 / 2.0) - 1.0
    bluff = bet / (1.0 + bet)
    ip_ev = 8.0 / 9.0 - 2.0 * math.sqrt(5.0 / 2.0) / 9.0
    return {
        "bet": bet,
        "ip_q_bet": bluff,
        "ip_k_bet": 0.0,
        "ip_a_bet": 1.0,
        "oop_q_call": 0.0,
        "oop_k_call": bet,
        "oop_a_call": 1.0,
        "ip_ev": ip_ev,
        "oop_ev": 1.0 - ip_ev,
    }


def symmetric_akq_ip_off_path_calls(bet: float) -> tuple[float, float, float]:
    """Return OOP(Q/K/A) calls that deter every off-path IP bet size.

    This completes the continuous-size equilibrium used by
    :func:`symmetric_akq_ip_continuous_bet`.  IP(Q) is held to its check value,
    while IP(A) cannot exceed the value obtained at the analytic optimum.
    """
    if not 0.0 < bet <= 1.0:
        raise ValueError("bet must be in (0, 1]")
    if bet < 0.25:
        return 1.0 - 4.0 * bet, 1.0, 1.0
    return 0.0, (1.5 - bet) / (1.0 + bet), 1.0


def symmetric_akq_continuous_candidate() -> dict[str, float]:
    """Return the closed-form candidate for pot 1, stack 1 and continuous sizing.

    The derivation assumes the equilibrium support observed in the full one-street
    game: OOP pools Q/K/A at one root size, IP raises that bet all-in, and after
    a check IP pools Q/A at one non-all-in size.  The returned values satisfy all
    on-path indifference and first-order sizing conditions for that support.
    """
    root_bet = 0.5
    ip_bet = (9.0 + math.sqrt(177.0)) / 24.0
    ip_q_bet = ip_bet / (1.0 + ip_bet)

    # IP(Q)'s total all-in raise frequency and IP(K)'s call frequency after
    # OOP's root half-pot bet.  Bluff raises may be redistributed between Q/K.
    ip_bluff_raise = (5.0 * ip_q_bet - 2.0) / 6.0
    ip_k_call = 1.0 - ip_q_bet / 2.0

    size_product = ip_bet * (2.0 + ip_bet)
    root_bet_scale = (size_product - 1.5) / (6.0 * size_product - 3.5)
    oop_q_check = 1.0 - root_bet_scale
    oop_k_check = 1.0 - 3.0 * root_bet_scale
    oop_a_check = 1.0 - 6.0 * root_bet_scale
    oop_k_call = (
        0.5 * oop_q_check + oop_k_check - oop_a_check * ip_bet
    ) / (oop_k_check * (1.0 + ip_bet))

    oop_q_ev = (1.0 - ip_q_bet) / 6.0
    oop_k_ev = 0.5 - ip_q_bet / 3.0
    oop_a_ev = (2.5 + ip_q_bet * ip_bet) / 3.0
    oop_ev = (oop_q_ev + oop_k_ev + oop_a_ev) / 3.0

    return {
        "oop_root_bet": root_bet,
        "ip_after_check_bet": ip_bet,
        "root_bet_scale": root_bet_scale,
        "oop_q_root_bet": root_bet_scale,
        "oop_k_root_bet": 3.0 * root_bet_scale,
        "oop_a_root_bet": 6.0 * root_bet_scale,
        "ip_q_after_check_bet": ip_q_bet,
        "ip_a_after_check_bet": 1.0,
        "oop_k_call_after_ip_bet": oop_k_call,
        "ip_bluff_raise_after_oop_bet": ip_bluff_raise,
        "ip_k_call_after_oop_bet": ip_k_call,
        "oop_ev": oop_ev,
        "ip_ev": 1.0 - oop_ev,
    }
