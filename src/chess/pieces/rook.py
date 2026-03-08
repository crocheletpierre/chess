from __future__ import annotations

from .piece import Color, Piece, Position

_CARDINALS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


class Rook(Piece):
    """Chess rook — slides along ranks and files. Tracks whether it has moved for castling."""

    has_moved: bool = False

    @property
    def symbol(self) -> str:
        return "♖" if self.color == Color.WHITE else "♜"

    def legal_moves(self, board: list[list[Piece | None]]) -> list[Position]:
        return self._slide(board, _CARDINALS)
