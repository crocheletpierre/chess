from chess.piece import Piece
from chess.board import Board
from chess.models import ChessTuple, COLUMNS
from chess.pieces.piece_helpers import is_valid_move

def has_enemy_piece(color: str, board: Board, position: str) -> bool:
    if is_valid_move(position) and board[position] is not None:
        if board[position].color!=color:
            return True
    return False


def find_neighboring_columns(column: str) -> list[str]:
    res = []
    index = COLUMNS.index(column)
    if index!=0:
        res.append(COLUMNS[index-1])
    if index!=7:
        res.append(COLUMNS[index+1])
    return res

class Pawn(Piece):
    name: str = "Pawn"

    def fetch_moves(self, board: Board) -> set[(ChessTuple[int, int], str)]:
        moves = set()
        # moves
        if board[self.position+self.forward] is None:
            moves.add((self.position+self.forward), "pawn_move")
            if self._moves == 0 and board[self.position+self.forward+self.forward] is None:
                moves.add((self.position+self.forward+self.forward), "pawn_jump")

        # normal captures
        for i in [-1, 1]:
            if has_enemy_piece(
                self.color,
                board,
                self.position+self.forward+ChessTuple((0, i))
            ):
                moves.add((self.position+self.forward+ChessTuple((0, i))), "pawn_capture")

        # en passant
        last_played_move, last_played_move_type = board.last_played[
            board._TOGGLE[self.color]
        ]
        if last_played_move_type=="pawn_jump":
            if last_played_move[0] in find_neighboring_columns(self.position[0]):
                moves.add((), "pawn_en_passant")

        return moves