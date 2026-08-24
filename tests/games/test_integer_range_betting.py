"""Game-contract tests for integer range custom-size poker."""

import math

import pyspiel
import pytest

from toy_poker.games import get_game
from toy_poker.games.fixed_range_one_street import parse_bet_fractions
from toy_poker.games.integer_range_betting import Action, FIRST_CUSTOM_ACTION


BET_33 = FIRST_CUSTOM_ACTION
BET_100 = FIRST_CUSTOM_ACTION + 1


def dealt_state(oop_card: int, ip_card: int, params=None):
    game = get_game("integer_range_betting").load_game(params or {})
    state = game.new_initial_state()
    action = (oop_card - 1) * 10 + (ip_card - 1)
    state.apply_action(action)
    return state


def apply_actions(state, actions):
    for action in actions:
        state.apply_action(int(action))
    return state


def test_defaults_and_independent_uniform_deals():
    game = get_game("integer_range_betting").load_game()
    assert game.oop_stack == 4.0
    assert game.ip_stack == 4.0
    assert game.effective_stack == 4.0
    assert game.bet_fractions == pytest.approx((1.0 / 3.0, 1.0))
    assert game.get_type().utility == pyspiel.GameType.Utility.CONSTANT_SUM
    outcomes = game.new_initial_state().chance_outcomes()
    assert len(outcomes) == 100
    assert all(math.isclose(probability, 0.01) for _, probability in outcomes)
    assert math.isclose(sum(probability for _, probability in outcomes), 1.0)


def test_opening_bets_and_raise_formula():
    state = dealt_state(oop_card=4, ip_card=8)
    assert state.legal_actions() == [Action.CHECK, Action.ALL_IN, BET_33, BET_100]
    state.apply_action(BET_100)
    assert state.commitments == [0.0, 1.0]
    assert math.isclose(state.pot, 2.0)

    # B + x(P + 2B) = 1 + (1/3)(1 + 2) = 2 total chips added.
    assert math.isclose(state.custom_target(0, BET_33), 2.0)
    assert BET_33 in state.legal_actions()
    # A 100% raise reaches stack 4 exactly and is represented only by All-in.
    assert math.isclose(state.custom_target(0, BET_100), 4.0)
    assert BET_100 not in state.legal_actions()
    assert Action.ALL_IN in state.legal_actions()


def test_standard_minimum_raise_and_short_all_in():
    params = {
        "oop_stack": 1.5,
        "ip_stack": 1.5,
        "bet_fractions": "0.25,1.0",
    }
    state = dealt_state(oop_card=4, ip_card=8, params=params)
    state.apply_action(FIRST_CUSTOM_ACTION + 1)  # Pot-sized opening bet of 1.
    # 25% would raise by only 0.75 after calling, below the previous increment 1.
    assert FIRST_CUSTOM_ACTION not in state.legal_actions()
    # Raising all-in to 1.5 is short of a full minimum raise but remains legal.
    assert Action.ALL_IN in state.legal_actions()
    apply_actions(state, [Action.ALL_IN, Action.CALL])
    assert state.returns() == [2.5, -1.5]


def test_showdown_fold_and_tie_utilities():
    state = apply_actions(
        dealt_state(oop_card=4, ip_card=8), [Action.CHECK, Action.CHECK]
    )
    assert state.returns() == [1.0, 0.0]

    state = apply_actions(
        dealt_state(oop_card=8, ip_card=4), [BET_33, Action.CALL]
    )
    assert state.returns() == pytest.approx([-1.0 / 3.0, 4.0 / 3.0])

    state = apply_actions(
        dealt_state(oop_card=6, ip_card=6), [BET_100, Action.CALL]
    )
    assert state.returns() == [0.5, 0.5]

    state = apply_actions(
        dealt_state(oop_card=4, ip_card=8),
        [BET_33, BET_33, Action.FOLD],
    )
    assert state.returns() == pytest.approx([4.0 / 3.0, -1.0 / 3.0])


def test_custom_fraction_validation_and_dynamic_actions():
    assert parse_bet_fractions("1,0.25,0.5") == (0.25, 0.5, 1.0)
    for invalid in ("", "0,1", "-0.5,1", "nan,1", "0.5,0.5", "word,1"):
        with pytest.raises(ValueError):
            parse_bet_fractions(invalid)

    game = get_game("integer_range_betting").load_game(
        {"bet_fractions": "0.25,0.5,1.0"}
    )
    assert game.num_distinct_actions() == 7


def test_every_terminal_has_utility_sum_one():
    game = get_game("integer_range_betting").load_game()

    def visit(state):
        if state.is_terminal():
            assert math.isclose(sum(state.returns()), 1.0, abs_tol=1e-12)
            return
        actions = (
            [action for action, _ in state.chance_outcomes()]
            if state.is_chance_node()
            else state.legal_actions()
        )
        for action in actions:
            visit(state.child(action))

    visit(game.new_initial_state())
    pyspiel.random_sim_test(game, 50, False, False, False)
