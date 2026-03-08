from __future__ import annotations

from .piece import Color, Piece, Position, _KING_OFFSETS


class King(Piece):
    """Chess king — moves one square in any direction. Tracks whether it has moved for castling."""

    has_moved: bool = False

    @property
    def symbol(self) -> str:
        return "♔" if self.color == Color.WHITE else "♚"

    def legal_moves(self, board: list[list[Piece | None]]) -> list[Position]:
        """Returns one-step moves. Castling is handled at the Board level."""
        return self._jump(board, _KING_OFFSETS)
