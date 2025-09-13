from chess.piece import Piece
from chess.board import Board
from chess.models import ChessTuple
from chess.pieces.piece_helpers import is_valid_move

class King(Piece):
    name: str = "King"

    def fetch_moves(self, board: Board) -> set[(ChessTuple[int, int], str)]:
        moves = set()

        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                this_move = self.position+ChessTuple((i,j))
                if is_valid_move(this_move):
                    if board[this_move] is None:
                        moves.add((this_move), "king_move")
                    elif board[this_move].color == board._TOGGLE[self.color]:
                        moves.add((this_move), "king_capture")
        return moves