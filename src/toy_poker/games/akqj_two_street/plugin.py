"""AKQJ two-street plugin registration."""

from toy_poker.games.akqj_two_street import game as _game  # noqa: F401
from toy_poker.games.akqj_two_street.metadata import METADATA
from toy_poker.games.base import GamePlugin
from toy_poker.games.registry import register_game


class AKQJTwoStreetPlugin(GamePlugin):
    def information_label(self, key: str) -> str:
        player_key, card, history = key.split("|", maxsplit=2)
        player = self.player_name(int(player_key.removeprefix("P")))
        readable = (
            history.replace("S1:", "street 1: ")
            .replace("/S2:", " / street 2: ")
            .replace("GEOMETRIC_BET", "geometric bet")
            .replace("ALL_IN", "all-in")
            .replace("CHECK", "check")
            .replace("CALL", "call")
            .replace("FOLD", "fold")
            .replace("ROOT", "start")
        )
        return f"{player}({card}): {readable}"

    def information_context(self, state):
        return {
            "street": state.street + 1,
            "pot": state.pot,
            "ip_committed": state.commitments[0],
            "oop_committed": state.commitments[1],
        }


PLUGIN = AKQJTwoStreetPlugin()
PLUGIN.metadata = METADATA
register_game(PLUGIN)
