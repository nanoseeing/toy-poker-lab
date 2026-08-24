"""AKQ plugin registration."""

from toy_poker.games.akq_allin import game as _game  # noqa: F401
from toy_poker.games.akq_allin.metadata import METADATA
from toy_poker.games.base import GamePlugin
from toy_poker.games.registry import register_game

PLUGIN = GamePlugin()
PLUGIN.metadata = METADATA
register_game(PLUGIN)
