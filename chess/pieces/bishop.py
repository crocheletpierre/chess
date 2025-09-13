from chess.piece import Piece
from chess.board import Board
from chess.models import ChessTuple

class Bishop(Piece):
    name: str = "Bishop"

    def fetch_moves(self, board: Board) -> set[(ChessTuple[int, int], str)]:
        moves = set()
        
        return moves