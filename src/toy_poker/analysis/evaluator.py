"""Policy evaluation utilities."""

from __future__ import annotations

import pyspiel


def expected_returns(game: pyspiel.Game, policy: pyspiel.Policy) -> list[float]:
    def value(state: pyspiel.State) -> list[float]:
        if state.is_terminal():
            return list(state.returns())
        transitions = (
            state.chance_outcomes()
            if state.is_chance_node()
            else policy.action_probabilities(state).items()
        )
        total = [0.0] * game.num_players()
        for action, probability in transitions:
            child_value = value(state.child(action))
            for player in range(game.num_players()):
                total[player] += probability * child_value[player]
        return total

    return value(game.new_initial_state())


def state_value_function(game: pyspiel.Game, policy: pyspiel.Policy):
    cache: dict[tuple[tuple[int, int], ...], tuple[float, ...]] = {}

    def value(state: pyspiel.State) -> tuple[float, ...]:
        key = tuple((item.player, item.action) for item in state.full_history())
        if key in cache:
            return cache[key]
        if state.is_terminal():
            result = tuple(state.returns())
        else:
            transitions = (
                state.chance_outcomes()
                if state.is_chance_node()
                else policy.action_probabilities(state).items()
            )
            aggregate = [0.0] * game.num_players()
            for action, probability in transitions:
                child_value = value(state.child(action))
                for player in range(game.num_players()):
                    aggregate[player] += probability * child_value[player]
            result = tuple(aggregate)
        cache[key] = result
        return result

    value(game.new_initial_state())
    return value
