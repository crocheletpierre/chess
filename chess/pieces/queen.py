from chess.piece import Piece
from chess.board import Board
from chess.models import ChessTuple


class Queen(Piece):
    name: str = "Queen"

    def fetch_moves(self, board: Board) -> set[(ChessTuple[int, int], str)]:
        moves = set()
        return moves