"""AKQJ plugin registration."""

from toy_poker.games.akqj_allin import game as _game  # noqa: F401
from toy_poker.games.akqj_allin.analytic import analytic_returns
from toy_poker.games.akqj_allin.metadata import METADATA
from toy_poker.games.base import GamePlugin
from toy_poker.games.registry import register_game


class AKQJPlugin(GamePlugin):
    def analytic_returns(self, game):
        return analytic_returns(game.effective_stack)


PLUGIN = AKQJPlugin()
PLUGIN.metadata = METADATA
register_game(PLUGIN)
