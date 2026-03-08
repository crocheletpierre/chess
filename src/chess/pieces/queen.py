from __future__ import annotations

from .piece import Color, Piece, Position

_ALL_DIRECTIONS = [
    (-1, 0), (1, 0), (0, -1), (0, 1),   # cardinals
    (-1, -1), (-1, 1), (1, -1), (1, 1),  # diagonals
]


class Queen(Piece):
    """Chess queen — slides in all eight directions."""

    @property
    def symbol(self) -> str:
        return "♕" if self.color == Color.WHITE else "♛"

    def legal_moves(self, board: list[list[Piece | None]]) -> list[Position]:
        return self._slide(board, _ALL_DIRECTIONS)
