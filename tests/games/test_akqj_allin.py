"""Game-contract tests for the AKQJ plugin."""

from toy_poker.games import get_game
from toy_poker.games.akqj_allin import Action, IPCard


def dealt_state(card, params=None):
    state = get_game("akqj_allin").load_game(params or {}).new_initial_state()
    state.apply_action(int(card))
    return state


def apply_actions(state, actions):
    for action in actions:
        state.apply_action(int(action))
    return state


def test_cards_roles_and_terminal_payoffs():
    plugin = get_game("akqj_allin")
    assert plugin.metadata.player_names == ("IP", "OOP")
    outcomes = plugin.load_game().new_initial_state().chance_outcomes()
    assert len(outcomes) == 3
    assert all(abs(probability - 1.0 / 3.0) < 1e-12 for _, probability in outcomes)

    for losing_card in (IPCard.QUEEN, IPCard.JACK):
        state = apply_actions(dealt_state(losing_card), [Action.CHECK, Action.CHECK])
        assert state.returns() == [-0.5, 0.5]

    state = apply_actions(dealt_state(IPCard.ACE), [Action.CHECK, Action.ALL_IN, Action.ALL_IN])
    assert state.returns() == [1.5, -1.5]


def test_independent_stacks_use_effective_stack():
    params = {"oop_stack": 2.0, "ip_stack": 3.0}
    game = get_game("akqj_allin").load_game(params)
    assert game.effective_stack == 2.0
    assert game.max_utility() == 2.5
    state = apply_actions(dealt_state(IPCard.JACK, params), [Action.CHECK, Action.ALL_IN, Action.ALL_IN])
    assert state.returns() == [-2.5, 2.5]
