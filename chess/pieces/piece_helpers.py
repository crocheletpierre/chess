from chess.piece import Piece
from chess.models import ChessTuple, COLUMNS, ROWS
from chess.board import Board

def is_valid_move(move: str):
    if move[0] in COLUMNS and move[1] in ROWS:
        return True
    return False


def check_moves_in_direction(
        piece: Piece,
        direction: ChessTuple[int, int],
        board: Board
) -> set[(ChessTuple[int, int], str)]:
    moves = set()
    for i in range(1, 8):
        this_move = piece.position+direction*i
        if not is_valid_move(this_move):
            break
        if board[this_move] is None:
            moves.add((this_move), f"{piece.name.lower()}_move")
        if board[this_move].color == piece.color:
            break
        if board[this_move].color == board._TOGGLE[piece.color]:
            moves.add((this_move), f"{piece.name.lower()}_capture")
            break
    return moves