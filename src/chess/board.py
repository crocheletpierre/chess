from __future__ import annotations

from .pieces import Bishop, Color, King, Knight, Pawn, Queen, Rook
from .pieces.piece import Piece, Position

_FILE_LABELS = "  a b c d e f g h"
_BACK_RANK = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]


class Board:
    """8x8 chess board managing piece placement and move execution."""

    def __init__(self) -> None:
        self.grid: list[list[Piece | None]] = [[None] * 8 for _ in range(8)]

    @classmethod
    def new_game(cls) -> "Board":
        """Return a Board with the standard chess starting position."""
        board = cls()
        # Black back rank and pawns
        for col, piece_cls in enumerate(_BACK_RANK):
            board.grid[0][col] = piece_cls(color=Color.BLACK, position=(0, col))
        for col in range(8):
            board.grid[1][col] = Pawn(color=Color.BLACK, position=(1, col))
        # White pawns and back rank
        for col in range(8):
            board.grid[6][col] = Pawn(color=Color.WHITE, position=(6, col))
        for col, piece_cls in enumerate(_BACK_RANK):
            board.grid[7][col] = piece_cls(color=Color.WHITE, position=(7, col))
        return board

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def piece_at(self, position: Position) -> Piece | None:
        row, col = position
        return self.grid[row][col]

    # ------------------------------------------------------------------
    # Move execution
    # ------------------------------------------------------------------

    def move(self, from_pos: Position, to_pos: Position) -> Piece | None:
        """Move a piece and return the captured piece (or None).

        Updates the grid and the piece's internal position. Marks pawns,
        kings, and rooks as having moved (used for castling / en passant).
        """
        from_row, from_col = from_pos
        to_row, to_col = to_pos

        piece = self.grid[from_row][from_col]
        if piece is None:
            raise ValueError(f"No piece at {from_pos}")

        captured = self.grid[to_row][to_col]

        self.grid[to_row][to_col] = piece
        self.grid[from_row][from_col] = None
        piece.position = to_pos

        if isinstance(piece, (Pawn, King, Rook)):
            piece.has_moved = True

        return captured

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def render(self) -> str:
        """Return a terminal-friendly string of the current board state."""
        lines = [_FILE_LABELS]
        for row in range(8):
            rank = 8 - row
            cells = [piece.render() if piece else "·" for piece in self.grid[row]]
            lines.append(f"{rank} {' '.join(cells)} {rank}")
        lines.append(_FILE_LABELS)
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.render()
