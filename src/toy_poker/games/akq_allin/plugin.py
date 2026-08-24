"""AKQ plugin registration."""

from toy_poker.games.akq_allin import game as _game  # noqa: F401
from toy_poker.games.akq_allin.analytic import analytic_returns
from toy_poker.games.akq_allin.metadata import METADATA
from toy_poker.games.base import GamePlugin
from toy_poker.games.registry import register_game

class AKQPlugin(GamePlugin):
    def analytic_returns(self, game):
        return analytic_returns(game.effective_stack)


PLUGIN = AKQPlugin()
PLUGIN.metadata = METADATA
register_game(PLUGIN)
