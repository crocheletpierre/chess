from __future__ import annotations

from .piece import Color, Piece, Position


class Pawn(Piece):
    """Chess pawn — moves forward, captures diagonally, supports en-passant square."""

    # Track whether this pawn has moved (for double-step logic)
    has_moved: bool = False
    # En-passant target square set by the board after an opponent's double push
    en_passant_target: Position | None = None

    @property
    def symbol(self) -> str:
        return "♙" if self.color == Color.WHITE else "♟"

    def legal_moves(self, board: list[list[Piece | None]]) -> list[Position]:
        moves: list[Position] = []
        row, col = self.position

        # White moves up the board (decreasing row index), black moves down
        direction = -1 if self.color == Color.WHITE else 1

        # Single step forward
        r = row + direction
        if 0 <= r <= 7 and board[r][col] is None:
            moves.append((r, col))

            # Double step from starting rank
            start_row = 6 if self.color == Color.WHITE else 1
            if not self.has_moved and row == start_row:
                r2 = row + 2 * direction
                if board[r2][col] is None:
                    moves.append((r2, col))

        # Diagonal captures
        for dc in (-1, 1):
            c = col + dc
            if 0 <= r <= 7 and 0 <= c <= 7:
                target = board[r][c]
                if self.is_opponent(target):
                    moves.append((r, c))
                # En-passant
                elif self.en_passant_target == (r, c):
                    moves.append((r, c))

        return moves
