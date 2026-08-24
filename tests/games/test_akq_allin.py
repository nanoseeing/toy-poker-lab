"""Game-contract tests for the AKQ plugin."""

from toy_poker.games import get_game
from toy_poker.games.akq_allin import Action, OOPCard


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

    state = apply_actions(dealt_state(OOPCard.QUEEN), [Action.CHECK, Action.CHECK])
    assert state.returns() == [0.5, -0.5]

    state = apply_actions(dealt_state(OOPCard.ACE), [Action.ALL_IN, Action.ALL_IN])
    assert state.returns() == [-1.5, 1.5]

    state = apply_actions(dealt_state(OOPCard.QUEEN), [Action.ALL_IN, Action.FOLD])
    assert state.returns() == [-0.5, 0.5]


def test_chance_and_zero_sum_contract():
    game = get_game("akq_allin").load_game()
    state = game.new_initial_state()
    assert abs(sum(probability for _, probability in state.chance_outcomes()) - 1.0) < 1e-12

    def visit(current):
        if current.is_terminal():
            assert abs(sum(current.returns())) < 1e-12
            return
        actions = current.chance_outcomes() if current.is_chance_node() else [(a, 1.0) for a in current.legal_actions()]
        for action, _ in actions:
            visit(current.child(action))

    visit(state)
