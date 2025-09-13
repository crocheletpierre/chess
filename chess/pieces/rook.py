from chess.piece import Piece
from chess.board import Board
from chess.models import ChessTuple
from chess.pieces.piece_helpers import check_moves_in_direction


class Rook(Piece):
    name: str = "Rook"

    def fetch_moves(self, board: Board) -> set[(ChessTuple[int, int], str)]:
        moves = set()
        
        moves.update(check_moves_in_direction(self, ChessTuple[-1, 0], board))
        moves.update(check_moves_in_direction(self, ChessTuple[1, 0], board))
        moves.update(check_moves_in_direction(self, ChessTuple[0, -1], board))
        moves.update(check_moves_in_direction(self, ChessTuple[0, 1], board))
        return moves