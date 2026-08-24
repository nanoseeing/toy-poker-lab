"""Integer range betting game plugin registration."""

from toy_poker.games.base import GamePlugin
from toy_poker.games.integer_range_betting import game as _game  # noqa: F401
from toy_poker.games.integer_range_betting.metadata import METADATA
from toy_poker.games.registry import register_game


class IntegerRangeBettingPlugin(GamePlugin):
    numeric_range_strategy = True

    def information_label(self, key: str) -> str:
        player_key, card, history = key.split("|", maxsplit=2)
        player = self.player_name(int(player_key.removeprefix("P")))
        readable = (
            history.replace("RAISE_ALL_IN", "raise all-in")
            .replace("ALL_IN", "all-in")
            .replace("RAISE_", "raise ")
            .replace("BET_", "bet ")
            .replace("CHECK", "check")
            .replace("CALL", "call")
            .replace("FOLD", "fold")
            .replace("ROOT", "start")
            .replace("-", " → ")
        )
        return f"{player}({card}): {readable}"

    def information_context(self, state):
        player = state.current_player()
        return {
            "pot": state.pot,
            "ip_committed": state.commitments[0],
            "oop_committed": state.commitments[1],
            "amount_to_call": state._amount_to_call(player),
            "minimum_raise_increment": state.last_full_raise_increment,
        }

    def chance_outcome_label(self, state, action: int) -> str:
        oop_card, ip_card = state.get_game().deal_from_action(action)
        return f"OOP {oop_card} / IP {ip_card}"


PLUGIN = IntegerRangeBettingPlugin()
PLUGIN.metadata = METADATA
register_game(PLUGIN)
