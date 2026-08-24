"""Game-contract tests for AKQJ two-street geometric poker."""

import math

import pyspiel

from toy_poker.games import get_game
from toy_poker.games.akqj_two_street import Action, IPCard
from toy_poker.games.fixed_oop_two_street import geometric_fraction


def dealt_state(card, params=None):
    state = get_game("akqj_two_street").load_game(params or {}).new_initial_state()
    state.apply_action(int(card))
    return state


def apply_actions(state, actions):
    for action in actions:
        state.apply_action(int(action))
    return state


def test_geometric_fraction_uses_the_stack_over_two_streets():
    for effective_stack in (0.25, 1.0, 2.0, 10.0):
        fraction = geometric_fraction(effective_stack)
        first_bet = fraction
        second_bet = fraction * (1.0 + 2.0 * first_bet)
        assert math.isclose(first_bet + second_bet, effective_stack, abs_tol=1e-12)


def test_cards_roles_and_check_down_payoffs():
    plugin = get_game("akqj_two_street")
    game = plugin.load_game()
    assert plugin.metadata.player_names == ("IP", "OOP")
    outcomes = game.new_initial_state().chance_outcomes()
    assert len(outcomes) == 3
    assert all(math.isclose(probability, 1.0 / 3.0) for _, probability in outcomes)

    state = apply_actions(
        dealt_state(IPCard.ACE),
        [Action.CHECK, Action.CHECK, Action.CHECK, Action.CHECK],
    )
    assert state.returns() == [0.5, -0.5]
    state = apply_actions(
        dealt_state(IPCard.QUEEN),
        [Action.CHECK, Action.CHECK, Action.CHECK, Action.CHECK],
    )
    assert state.returns() == [-0.5, 0.5]


def test_geo_call_advances_street_and_second_geo_is_all_in():
    game = get_game("akqj_two_street").load_game()
    state = apply_actions(
        dealt_state(IPCard.ACE), [Action.GEOMETRIC_BET, Action.CALL]
    )
    first_bet = game.geometric_fraction
    assert state.street == 1
    assert all(math.isclose(value, first_bet) for value in state.commitments)
    assert math.isclose(state.pot, 1.0 + 2.0 * first_bet)
    assert state.legal_actions() == [Action.CHECK, Action.ALL_IN]

    apply_actions(state, [Action.ALL_IN, Action.CALL])
    assert state.returns() == [1.5, -1.5]


def test_geo_can_be_raised_all_in_and_fold_loses_only_committed_chips():
    game = get_game("akqj_two_street").load_game()
    state = apply_actions(
        dealt_state(IPCard.JACK),
        [Action.CHECK, Action.GEOMETRIC_BET, Action.ALL_IN],
    )
    assert state.action_to_string(state.current_player(), int(Action.CALL)) == "Call"
    apply_actions(state, [Action.FOLD])
    loss = 0.5 + game.geometric_fraction
    assert math.isclose(state.returns()[0], -loss)
    assert math.isclose(state.returns()[1], loss)


def test_independent_stacks_use_effective_stack_and_valid_game_tree():
    params = {"oop_stack": 2.0, "ip_stack": 3.0}
    game = get_game("akqj_two_street").load_game(params)
    assert game.effective_stack == 2.0
    assert math.isclose(game.geometric_fraction, (math.sqrt(5.0) - 1.0) / 2.0)
    assert game.max_utility() == 2.5
    state = apply_actions(
        dealt_state(IPCard.JACK, params), [Action.ALL_IN, Action.CALL]
    )
    assert state.returns() == [-2.5, 2.5]
    pyspiel.random_sim_test(game, 50, False, False, False)
