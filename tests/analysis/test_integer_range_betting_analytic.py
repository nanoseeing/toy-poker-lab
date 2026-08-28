"""Closed-form checks for the independent AKQ continuous-size candidate."""

import math

import pytest

from toy_poker.games.integer_range_betting.analytic import (
    akq_k_vs_aq_fixed_bet,
    symmetric_akq_allin_equilibrium,
    symmetric_akq_continuous_candidate,
    symmetric_akq_ip_continuous_bet,
    symmetric_akq_ip_off_path_calls,
)


def test_k_vs_aq_fixed_bet_conditions_and_monotonic_value():
    half = akq_k_vs_aq_fixed_bet(0.5)
    shove = akq_k_vs_aq_fixed_bet(1.0)

    assert half["ip_q_bet"] * 1.5 - 0.5 == pytest.approx(0.0)
    assert (1.0 - half["oop_k_call"]) - 0.5 * half["oop_k_call"] == pytest.approx(0.0)
    assert shove["ip_ev"] > half["ip_ev"]
    assert shove["ip_q_bet"] == pytest.approx(0.5)
    assert shove["oop_k_call"] == pytest.approx(0.5)
    assert shove["ip_ev"] == pytest.approx(0.75)


def test_symmetric_akq_allin_equilibrium_and_root_deviations():
    solution = symmetric_akq_allin_equilibrium()
    d = solution["ip_k_off_path_call"]

    assert solution["ip_q_bet_after_check"] == pytest.approx(0.5)
    assert solution["oop_k_call"] == pytest.approx(0.25)
    assert 3.0 / 8.0 <= d <= 0.5

    # OOP's root all-in EV for Q/K/A under the canonical off-path response.
    root_bet_evs = ((1.0 - 2.0 * d) / 3.0, (1.0 - 0.5 * d) / 3.0, (2.5 + d) / 3.0)
    root_check_evs = (1.0 / 12.0, 1.0 / 3.0, 1.0)
    assert all(bet <= check + 1e-12 for bet, check in zip(root_bet_evs, root_check_evs))
    assert solution["ip_ev"] + solution["oop_ev"] == pytest.approx(1.0)


def test_symmetric_akq_ip_continuous_bet_conditions():
    solution = symmetric_akq_ip_continuous_bet()
    bet = solution["bet"]
    bluff = solution["ip_q_bet"]
    call = solution["oop_k_call"]

    assert bet == pytest.approx(math.sqrt(5.0 / 2.0) - 1.0)
    assert 1.5 - 2.0 * bet - bet**2 == pytest.approx(0.0)
    assert bluff * (1.0 + bet) - bet == pytest.approx(0.0)
    assert call == pytest.approx((1.5 - bet) / (1.0 + bet))
    assert solution["ip_ev"] == pytest.approx(0.5375247044257356)
    assert solution["ip_ev"] + solution["oop_ev"] == pytest.approx(1.0)


@pytest.mark.parametrize("bet", [0.01, 0.1, 0.249, 0.25, 0.4, 0.5811388300841898, 0.8, 1.0])
def test_symmetric_akq_continuous_off_path_response_deters_deviations(bet):
    solution = symmetric_akq_ip_continuous_bet()
    q_call, k_call, a_call = symmetric_akq_ip_off_path_calls(bet)

    q_bet_ev = (2.0 - bet - 0.5 * q_call - (1.0 + bet) * k_call) / 3.0
    k_bet_ev = (2.0 - bet + bet * q_call - 0.5 * k_call) / 3.0
    a_bet_ev = (2.5 + bet * (q_call + k_call)) / 3.0
    a_equilibrium_ev = (2.5 + solution["bet"] ** 2) / 3.0

    assert q_bet_ev <= 1.0 / 6.0 + 1e-12
    assert k_bet_ev <= 0.5 + 1e-12
    assert a_bet_ev <= a_equilibrium_ev + 1e-12


def test_symmetric_akq_continuous_candidate_satisfies_indifference_conditions():
    solution = symmetric_akq_continuous_candidate()
    bet = solution["ip_after_check_bet"]
    q_bet = solution["ip_q_after_check_bet"]
    scale = solution["root_bet_scale"]

    assert bet == pytest.approx((9.0 + math.sqrt(177.0)) / 24.0)
    assert 12.0 * bet**2 - 9.0 * bet - 2.0 == pytest.approx(0.0)
    assert q_bet == pytest.approx(bet / (1.0 + bet))
    assert solution["oop_k_root_bet"] == pytest.approx(3.0 * scale)
    assert solution["oop_a_root_bet"] == pytest.approx(6.0 * scale)

    # The two IP indifference conditions force the root bet-mass ratio 1:3:6.
    q_mass = solution["oop_q_root_bet"]
    k_mass = solution["oop_k_root_bet"]
    a_mass = solution["oop_a_root_bet"]
    assert 1.5 * q_mass + 0.5 * k_mass - 0.5 * a_mass == pytest.approx(0.0)
    assert 1.5 * (q_mass + k_mass) - a_mass == pytest.approx(0.0)

    # OOP(A)'s root check/bet indifference determines the non-all-in size.
    assert (
        solution["ip_bluff_raise_after_oop_bet"]
        + 0.5 * solution["ip_k_call_after_oop_bet"]
    ) == pytest.approx(q_bet * bet)

    # OOP(Q/K)'s root indifference fixes IP's raise/call continuation.
    raise_frequency = solution["ip_bluff_raise_after_oop_bet"]
    k_call = solution["ip_k_call_after_oop_bet"]
    assert raise_frequency + k_call == pytest.approx((2.0 + q_bet) / 3.0)
    assert 3.0 * raise_frequency + k_call == pytest.approx(2.0 * q_bet)

    # The derivative of IP(A)'s value at the post-check bet size is zero.
    q = 1.0 - scale
    k = 1.0 - 3.0 * scale
    a = 1.0 - 6.0 * scale
    assert 0.5 * q + k == pytest.approx(a * bet * (2.0 + bet))
    assert solution["ip_ev"] + solution["oop_ev"] == pytest.approx(1.0)
