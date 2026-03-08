from __future__ import annotations

from .piece import Color, Piece, Position, _KNIGHT_OFFSETS


class Knight(Piece):
    """Chess knight — jumps in an L-shape, ignoring pieces in between."""

    @property
    def symbol(self) -> str:
        return "♘" if self.color == Color.WHITE else "♞"

    def legal_moves(self, board: list[list[Piece | None]]) -> list[Position]:
        return self._jump(board, _KNIGHT_OFFSETS)
