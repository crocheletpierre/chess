from __future__ import annotations

from .piece import Color, Piece, Position, _DIAGONALS, _CARDINALS


class Queen(Piece):
    """Chess queen — slides in all eight directions."""

    @property
    def symbol(self) -> str:
        return "♕" if self.color == Color.WHITE else "♛"

    def legal_moves(self, board: list[list[Piece | None]]) -> list[Position]:
        return self._slide(board, _DIAGONALS+_CARDINALS)
