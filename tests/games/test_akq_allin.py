"""Game-contract tests for the AKQ plugin."""

import pyspiel

from toy_poker.games import get_game
from toy_poker.games.akq_allin import Action, IPCard


def dealt_state(card):
    state = get_game("akq_allin").load_game().new_initial_state()
    state.apply_action(int(card))
    return state


def apply_actions(state, actions):
    for action in actions:
        state.apply_action(int(action))
    return state


def test_roles_and_terminal_payoffs():
    plugin = get_game("akq_allin")
    assert plugin.metadata.player_names == ("IP", "OOP")

    # OOP(K) beats IP(Q) at showdown.
    state = apply_actions(dealt_state(IPCard.QUEEN), [Action.CHECK, Action.CHECK])
    assert state.returns() == [0.0, 1.0]

    # IP(A) calls OOP's all-in and wins.
    state = apply_actions(dealt_state(IPCard.ACE), [Action.ALL_IN, Action.ALL_IN])
    assert state.returns() == [2.0, -1.0]

    state = apply_actions(dealt_state(IPCard.QUEEN), [Action.ALL_IN, Action.FOLD])
    assert state.returns() == [0.0, 1.0]


def test_independent_stacks_use_effective_stack():
    game = get_game("akq_allin").load_game({"oop_stack": 2.0, "ip_stack": 3.0})
    assert game.effective_stack == 2.0
    assert game.max_utility() == 3.0
    state = game.new_initial_state()
    state.apply_action(int(IPCard.ACE))
    state.apply_action(int(Action.ALL_IN))
    state.apply_action(int(Action.ALL_IN))
    assert state.returns() == [3.0, -2.0]


def test_chance_and_constant_sum_contract():
    game = get_game("akq_allin").load_game()
    assert game.get_type().utility == pyspiel.GameType.Utility.CONSTANT_SUM
    assert game.utility_sum() == 1.0
    state = game.new_initial_state()
    assert abs(sum(probability for _, probability in state.chance_outcomes()) - 1.0) < 1e-12

    def visit(current):
        if current.is_terminal():
            assert abs(sum(current.returns()) - 1.0) < 1e-12
            return
        actions = current.chance_outcomes() if current.is_chance_node() else [(a, 1.0) for a in current.legal_actions()]
        for action, _ in actions:
            visit(current.child(action))

    visit(state)
