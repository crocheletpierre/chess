from __future__ import annotations

from ..board import Board
from ..pieces.piece import Color
from .piece_square_tables import lookup
from .simple_agent import SimpleAgent, _PIECE_VALUES


class PositionalAgent(SimpleAgent):
    """Material evaluation plus Michniewski piece-square bonuses.

    Overrides evaluate() only; inherits all iterative-deepening search logic
    from SimpleAgent unchanged.
    """

    @property
    def name(self) -> str:
        return "Positional"

    def _eval_board(self, board: Board, color: Color) -> float:
        score = 0.0
        for row_idx, row in enumerate(board.grid):
            for col_idx, piece in enumerate(row):
                if piece is None:
                    continue
                piece_type = type(piece)
                material = _PIECE_VALUES.get(piece_type, 0.0)
                positional = lookup(piece_type, row_idx, col_idx, piece.color == Color.WHITE) / 100.0
                value = material + positional
                score += value if piece.color == color else -value
        return score
