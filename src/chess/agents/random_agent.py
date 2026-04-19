from __future__ import annotations

import random as _random
from typing import TYPE_CHECKING

from .agent import Agent

if TYPE_CHECKING:
    from ..game import Game
    from ..pieces.piece import Position


class RandomAgent(Agent):
    """Picks a legal move uniformly at random each turn."""

    def __init__(self, rng: _random.Random | None = None) -> None:
        self._rng = rng or _random.Random()

    @property
    def name(self) -> str:
        return "Random"

    def choose_move(self, game: "Game") -> "tuple[Position, Position]":
        moves = game.board.all_legal_moves(game.current_turn)
        if not moves:
            raise RuntimeError("choose_move called but no legal moves available.")
        return self._rng.choice(moves)
