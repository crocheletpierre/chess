from chess.piece import Piece
from chess.pieces.bishop import Bishop
from chess.pieces.king import King
from chess.pieces.knight import Knight
from chess.pieces.pawn import Pawn
from chess.pieces.queen import Queen
from chess.pieces.rook import Rook

def __init_board() -> dict[str, list[Piece | None]]:
        board: dict[str, list[Piece | None]] = {
            "a": [None for _ in range(8)],
            "b": [None for _ in range(8)],
            "c": [None for _ in range(8)],
            "d": [None for _ in range(8)],
            "e": [None for _ in range(8)],
            "f": [None for _ in range(8)],
            "g": [None for _ in range(8)],
            "h": [None for _ in range(8)]
        }
        board["a"][0] = Rook("White", position="a1")
        board["b"][0] = Knight("White", position="b1")
        board["c"][0] = Bishop("White", position="c1")
        board["d"][0] = Queen("White", position="d1")
        board["e"][0] = King("White", position="e1")
        board["f"][0] = Bishop("White", position="f1")
        board["g"][0] = Knight("White", position="g1")
        board["h"][0] = Rook("White", position="h1")

        board["a"][7] = Rook("Black", position="a8")
        board["b"][7] = Knight("Black", position="b8")
        board["c"][7] = Bishop("Black", position="c8")
        board["d"][7] = Queen("Black", position="d8")
        board["e"][7] = King("Black", position="e8")
        board["f"][7] = Bishop("Black", position="f8")
        board["g"][7] = Knight("Black", position="g8")
        board["h"][7] = Rook("Black", position="h8")

        for letter in "abcdefgh":
            board[letter][1] = Pawn("White", position=f"{letter}2")
            board[letter][6] = Pawn("Black", position=f"{letter}7")
        return board