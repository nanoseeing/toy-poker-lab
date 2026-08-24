"""Compile a Python OpenSpiel tree to the native C++ Gambit EFG game."""

from __future__ import annotations

from dataclasses import dataclass

import pyspiel

from toy_poker.solvers.policy import PolicyTable, standalone_policy


def _quoted(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


class _EFGWriter:
    def __init__(self, game: pyspiel.Game):
        if game.num_players() != 2:
            raise ValueError("The native EFG CFR+ backend requires exactly two players")
        if game.get_type().dynamics != pyspiel.GameType.Dynamics.SEQUENTIAL:
            raise ValueError("The native EFG backend requires a sequential game")
        if game.get_type().utility != pyspiel.GameType.Utility.ZERO_SUM:
            raise ValueError("The native EFG CFR+ backend requires a zero-sum game")
        self.game = game
        self.lines: list[str] = []
        self.information_set_ids: list[dict[str, int]] = [{}, {}]
        self.chance_id = 0
        self.outcome_id = 0

    def write(self) -> str:
        self._visit(self.game.new_initial_state())
        header = 'EFG 2 R "Compiled OpenSpiel game" { "Player 1" "Player 2" }'
        return header + "\n" + "\n".join(self.lines) + "\n"

    def _visit(self, state: pyspiel.State) -> None:
        if state.is_terminal():
            self.outcome_id += 1
            utilities = " ".join(f"{value:.17g}" for value in state.returns())
            self.lines.append(
                f't "" {self.outcome_id} "Outcome {self.outcome_id}" '
                f"{{ {utilities} }}"
            )
            return
        if state.is_chance_node():
            self.chance_id += 1
            outcomes = state.chance_outcomes()
            actions = " ".join(
                f"{_quoted(state.action_to_string(pyspiel.PlayerId.CHANCE, action))} "
                f"{probability:.17g}"
                for action, probability in outcomes
            )
            self.lines.append(
                f'c "" {self.chance_id} "chance {self.chance_id}" '
                f"{{ {actions} }} 0"
            )
            for action, _ in outcomes:
                self._visit(state.child(action))
            return
        player = state.current_player()
        key = state.information_state_string(player)
        information_sets = self.information_set_ids[player]
        information_set_id = information_sets.setdefault(key, len(information_sets) + 1)
        actions = " ".join(
            _quoted(state.action_to_string(player, action))
            for action in state.legal_actions()
        )
        self.lines.append(
            f'p "" {player + 1} {information_set_id} {_quoted(key)} '
            f"{{ {actions} }} 0"
        )
        for action in state.legal_actions():
            self._visit(state.child(action))


@dataclass(frozen=True)
class _InformationSetMapping:
    native_state: pyspiel.State
    action_pairs: tuple[tuple[int, int], ...]


@dataclass
class NativeEFGGame:
    """Native game plus a mapping back to the source game's policy keys/actions."""

    game: pyspiel.Game
    policy_mapping: dict[str, _InformationSetMapping]

    def translate_policy(
        self, native_policy: pyspiel.Policy
    ) -> tuple[pyspiel.TabularPolicy, PolicyTable]:
        table: PolicyTable = {}
        for source_key, mapping in self.policy_mapping.items():
            native_probabilities = native_policy.action_probabilities(mapping.native_state)
            table[source_key] = [
                (source_action, float(native_probabilities.get(native_action, 0.0)))
                for source_action, native_action in mapping.action_pairs
            ]
        return standalone_policy(table), table


def compile_to_native_efg(game: pyspiel.Game) -> NativeEFGGame:
    """Materialize a Python game tree as an EFG game implemented in native C++."""
    native_game = pyspiel.load_efg_game(_EFGWriter(game).write())
    mapping: dict[str, _InformationSetMapping] = {}

    def pair_states(source: pyspiel.State, native: pyspiel.State) -> None:
        if source.is_terminal():
            if not native.is_terminal():
                raise ValueError("EFG compilation changed a terminal node")
            if any(
                abs(source_value - native_value) > 1e-12
                for source_value, native_value in zip(
                    source.returns(), native.returns()
                )
            ):
                raise ValueError("EFG compilation changed terminal utilities")
            return
        if source.is_chance_node():
            if not native.is_chance_node():
                raise ValueError("EFG compilation changed a chance node")
            source_outcomes = source.chance_outcomes()
            native_outcomes = native.chance_outcomes()
            if len(source_outcomes) != len(native_outcomes):
                raise ValueError("EFG compilation changed chance outcomes")
            for (source_action, source_probability), (native_action, native_probability) in zip(
                source_outcomes, native_outcomes
            ):
                if abs(source_probability - native_probability) > 1e-12:
                    raise ValueError("EFG compilation changed a chance probability")
                pair_states(source.child(source_action), native.child(native_action))
            return
        if source.current_player() != native.current_player():
            raise ValueError("EFG compilation changed the acting player")
        player = source.current_player()
        source_actions = source.legal_actions()
        native_actions = native.legal_actions()
        if len(source_actions) != len(native_actions):
            raise ValueError("EFG compilation changed legal actions")
        source_key = source.information_state_string(player)
        native_key = native.information_state_string(player)
        action_pairs = tuple(zip(source_actions, native_actions))
        existing = mapping.get(source_key)
        if existing is None:
            mapping[source_key] = _InformationSetMapping(native.clone(), action_pairs)
        elif (
            existing.native_state.information_state_string(player) != native_key
            or existing.action_pairs != action_pairs
        ):
            raise ValueError(f"Inconsistent EFG mapping for information set {source_key}")
        for source_action, native_action in action_pairs:
            pair_states(source.child(source_action), native.child(native_action))

    pair_states(game.new_initial_state(), native_game.new_initial_state())
    return NativeEFGGame(game=native_game, policy_mapping=mapping)
