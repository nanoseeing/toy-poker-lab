"""Rules for the two-street independent integer-range game."""

import pyspiel
import pytest

from toy_poker.games import get_game
from toy_poker.games.fixed_range_one_street import Action, FIRST_CUSTOM_ACTION


def dealt_state(oop_card=2, ip_card=3, params=None):
    game = get_game("integer_range_betting_two_street").load_game(
        {"num_ranks": 3} | (params or {})
    )
    state = game.new_initial_state()
    state.apply_action((oop_card - 1) * game.num_ranks + (ip_card - 1))
    return state


def test_check_check_advances_then_ends_on_second_street():
    state = dealt_state()
    state.apply_action(Action.CHECK)
    state.apply_action(Action.CHECK)
    assert not state.is_terminal()
    assert state.street == 1
    assert state.current_player() == 1
    assert state.history_tokens == ["CHECK", "CHECK", "STREET_2"]
    state.apply_action(Action.CHECK)
    state.apply_action(Action.CHECK)
    assert state.is_terminal()
    assert state.returns() == [1.0, 0.0]


def test_pot_bet_call_carries_commitments_to_second_street():
    state = dealt_state(params={"bet_fractions": "1.0", "oop_stack": 4.0, "ip_stack": 4.0})
    pot_bet = FIRST_CUSTOM_ACTION
    state.apply_action(pot_bet)
    state.apply_action(Action.CALL)
    assert state.street == 1
    assert state.commitments == [1.0, 1.0]
    assert state.pot == pytest.approx(3.0)
    assert state.last_full_raise_increment == 0.0
    assert pot_bet not in state.legal_actions()
    state.apply_action(Action.ALL_IN)
    state.apply_action(Action.CALL)
    assert state.is_terminal()
    assert state.commitments == [4.0, 4.0]
    assert state.returns() == [5.0, -4.0]


def test_first_street_fold_and_all_in_call_end_immediately():
    state = dealt_state(params={"bet_fractions": "0.5"})
    state.apply_action(FIRST_CUSTOM_ACTION)
    state.apply_action(Action.FOLD)
    assert state.is_terminal()
    assert state.returns() == [0.0, 1.0]

    state = dealt_state()
    state.apply_action(Action.ALL_IN)
    state.apply_action(Action.CALL)
    assert state.is_terminal()


def test_random_play_preserves_constant_sum():
    game = get_game("integer_range_betting_two_street").load_game(
        {"num_ranks": 3, "bet_fractions": "0.5,1.0"}
    )
    pyspiel.random_sim_test(game, 100, False, False, False)
