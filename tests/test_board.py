"""Tests for Board state (ckq.7), special moves (ckq.8), and check/checkmate/stalemate (ckq.9)."""

import pytest

from chess.board import Board
from chess.pieces import Bishop, Color, King, Knight, Pawn, Queen, Rook
from chess.pieces.piece import Piece

W = Color.WHITE
B = Color.BLACK


def bare_board(*pieces: Piece) -> Board:
    """Return a Board containing only the given pieces."""
    board = Board()
    for p in pieces:
        r, c = p.position
        board.grid[r][c] = p
    return board


# ---------------------------------------------------------------------------
# Board state (ckq.7)
# ---------------------------------------------------------------------------

class TestBoardState:
    def test_new_game_piece_count(self):
        board = Board.new_game()
        pieces = [p for row in board.grid for p in row if p is not None]
        assert len(pieces) == 32

    def test_new_game_white_pawns_on_rank_2(self):
        board = Board.new_game()
        for col in range(8):
            assert isinstance(board.grid[6][col], Pawn)
            assert board.grid[6][col].color == W

    def test_new_game_black_pawns_on_rank_7(self):
        board = Board.new_game()
        for col in range(8):
            assert isinstance(board.grid[1][col], Pawn)
            assert board.grid[1][col].color == B

    def test_new_game_back_ranks(self):
        board = Board.new_game()
        expected = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for col, cls in enumerate(expected):
            assert isinstance(board.grid[0][col], cls)
            assert isinstance(board.grid[7][col], cls)

    def test_piece_at(self):
        board = Board.new_game()
        assert isinstance(board.piece_at((7, 4)), King)
        assert board.piece_at((4, 4)) is None

    def test_move_updates_grid_and_position(self):
        board = Board.new_game()
        board.move((6, 4), (4, 4))  # e2-e4
        assert board.grid[6][4] is None
        piece = board.grid[4][4]
        assert isinstance(piece, Pawn)
        assert piece.position == (4, 4)

    def test_move_returns_captured_piece(self):
        board = bare_board(
            King(color=W, position=(7, 4)),
            King(color=B, position=(0, 4)),
            Rook(color=W, position=(4, 4)),
            Pawn(color=B, position=(4, 7)),
        )
        board.grid[4][7] = Pawn(color=B, position=(4, 7))
        captured = board.move((4, 4), (4, 7))
        assert isinstance(captured, Pawn)
        assert captured.color == B

    def test_has_moved_flag_set(self):
        board = Board.new_game()
        pawn = board.grid[6][4]
        assert isinstance(pawn, Pawn)
        assert not pawn.has_moved
        board.move((6, 4), (4, 4))
        assert pawn.has_moved

    def test_en_passant_square_set_after_double_push(self):
        board = Board.new_game()
        board.move((6, 4), (4, 4))
        assert board.en_passant_square == (5, 4)

    def test_en_passant_square_cleared_after_other_move(self):
        board = Board.new_game()
        board.move((6, 4), (4, 4))
        board.move((1, 0), (2, 0))  # a6 — not a double push
        assert board.en_passant_square is None


# ---------------------------------------------------------------------------
# Special moves (ckq.8)
# ---------------------------------------------------------------------------

class TestSpecialMoves:
    # --- En passant ---

    def test_en_passant_capture_removes_pawn(self):
        board = Board.new_game()
        board.move((6, 4), (4, 4))  # e4
        board.move((1, 0), (3, 0))  # a5 (irrelevant)
        board.move((4, 4), (3, 4))  # e5
        board.move((1, 3), (3, 3))  # d5 (double push — sets en passant on d6)
        assert board.en_passant_square == (2, 3)
        board.move((3, 4), (2, 3))  # exd6 en passant
        assert board.grid[3][3] is None  # captured pawn removed
        assert isinstance(board.grid[2][3], Pawn)

    def test_en_passant_legal_move_present(self):
        board = Board.new_game()
        board.move((6, 4), (4, 4))  # e4
        board.move((1, 0), (3, 0))  # a5
        board.move((4, 4), (3, 4))  # e5
        board.move((1, 3), (3, 3))  # d5
        assert (2, 3) in board.legal_moves((3, 4))

    def test_en_passant_not_available_next_turn(self):
        board = Board.new_game()
        board.move((6, 4), (4, 4))  # e4
        board.move((1, 3), (3, 3))  # d5
        board.move((4, 4), (3, 4))  # e5
        # Black plays something other than double push
        board.move((1, 0), (2, 0))  # a6
        # White makes another move
        board.move((6, 0), (5, 0))  # a3
        # Now black double pushes
        board.move((1, 5), (3, 5))  # f5
        # The d5 en passant opportunity is long gone
        assert board.en_passant_square == (2, 5)
        assert (2, 3) not in board.legal_moves((3, 4))

    # --- Castling ---

    def test_kingside_castling_white(self):
        board = bare_board(
            King(color=W, position=(7, 4)),
            Rook(color=W, position=(7, 7)),
            King(color=B, position=(0, 4)),
        )
        assert (7, 6) in board.legal_moves((7, 4))
        board.move((7, 4), (7, 6))
        assert isinstance(board.grid[7][6], King)
        assert isinstance(board.grid[7][5], Rook)
        assert board.grid[7][7] is None
        assert board.grid[7][4] is None

    def test_queenside_castling_white(self):
        board = bare_board(
            King(color=W, position=(7, 4)),
            Rook(color=W, position=(7, 0)),
            King(color=B, position=(0, 4)),
        )
        assert (7, 2) in board.legal_moves((7, 4))
        board.move((7, 4), (7, 2))
        assert isinstance(board.grid[7][2], King)
        assert isinstance(board.grid[7][3], Rook)

    def test_castling_blocked_by_piece(self):
        board = bare_board(
            King(color=W, position=(7, 4)),
            Rook(color=W, position=(7, 7)),
            Knight(color=W, position=(7, 6)),
            King(color=B, position=(0, 4)),
        )
        assert (7, 6) not in board.legal_moves((7, 4))

    def test_castling_not_allowed_after_king_moved(self):
        board = bare_board(
            King(color=W, position=(7, 4), has_moved=True),
            Rook(color=W, position=(7, 7)),
            King(color=B, position=(0, 4)),
        )
        assert (7, 6) not in board.legal_moves((7, 4))

    def test_castling_not_allowed_after_rook_moved(self):
        board = bare_board(
            King(color=W, position=(7, 4)),
            Rook(color=W, position=(7, 7), has_moved=True),
            King(color=B, position=(0, 4)),
        )
        assert (7, 6) not in board.legal_moves((7, 4))

    def test_castling_not_allowed_while_in_check(self):
        board = bare_board(
            King(color=W, position=(7, 4)),
            Rook(color=W, position=(7, 7)),
            Rook(color=B, position=(0, 4)),  # attacks e1
            King(color=B, position=(0, 0)),
        )
        assert board.is_in_check(W)
        assert (7, 6) not in board.legal_moves((7, 4))

    def test_castling_not_allowed_through_attacked_square(self):
        board = bare_board(
            King(color=W, position=(7, 4)),
            Rook(color=W, position=(7, 7)),
            Rook(color=B, position=(0, 5)),  # attacks f1 (the transit square)
            King(color=B, position=(0, 0)),
        )
        assert (7, 6) not in board.legal_moves((7, 4))

    # --- Pawn promotion ---

    def test_promotion_auto_queen(self):
        board = bare_board(
            King(color=W, position=(7, 4)),
            King(color=B, position=(0, 4)),
            Pawn(color=W, position=(1, 0), has_moved=True),
        )
        board.grid[0][0] = None  # clear the square
        board.move((1, 0), (0, 0))
        promoted = board.grid[0][0]
        assert isinstance(promoted, Queen)
        assert promoted.color == W

    def test_promotion_capture_promotes(self):
        board = bare_board(
            King(color=W, position=(7, 4)),
            King(color=B, position=(0, 4)),
            Pawn(color=W, position=(1, 1), has_moved=True),
            Rook(color=B, position=(0, 0)),
        )
        board.move((1, 1), (0, 0))
        assert isinstance(board.grid[0][0], Queen)
        assert board.grid[0][0].color == W


# ---------------------------------------------------------------------------
# Check, checkmate, stalemate (ckq.9)
# ---------------------------------------------------------------------------

class TestCheckMateStalemate:
    def test_is_in_check_basic(self):
        board = bare_board(
            King(color=W, position=(7, 4)),
            Rook(color=B, position=(7, 0)),
            King(color=B, position=(0, 4)),
        )
        assert board.is_in_check(W)

    def test_not_in_check(self):
        board = Board.new_game()
        assert not board.is_in_check(W)
        assert not board.is_in_check(B)

    def test_legal_moves_filter_leaves_king_in_check(self):
        # Pinned rook cannot move (would expose king)
        board = bare_board(
            King(color=W, position=(7, 4)),
            Rook(color=W, position=(7, 2)),
            Rook(color=B, position=(7, 0)),
            King(color=B, position=(0, 4)),
        )
        # The white rook on c1 is pinned along the 1st rank
        legal = board.legal_moves((7, 2))
        # Can only move along rank 7 between the two rooks, not off it
        for pos in legal:
            assert pos[0] == 7

    def test_fools_mate_checkmate(self):
        board = Board.new_game()
        board.move((6, 5), (5, 5))  # f3
        board.move((1, 4), (3, 4))  # e5
        board.move((6, 6), (4, 6))  # g4
        board.move((0, 3), (4, 7))  # Qh4#
        assert board.is_in_check(W)
        assert board.is_checkmate(W)
        assert not board.is_stalemate(W)

    def test_stalemate(self):
        # Classic stalemate: black king trapped with no legal moves, not in check
        board = bare_board(
            King(color=B, position=(0, 0)),
            Queen(color=W, position=(1, 2)),
            King(color=W, position=(2, 1)),
        )
        assert not board.is_in_check(B)
        assert board.is_stalemate(B)
        assert not board.is_checkmate(B)

    def test_no_checkmate_when_can_block(self):
        # King in check but a piece can interpose
        board = bare_board(
            King(color=W, position=(7, 4)),
            Rook(color=B, position=(7, 0)),
            Rook(color=W, position=(6, 7)),  # can block on rank 7
            King(color=B, position=(0, 4)),
        )
        assert board.is_in_check(W)
        assert not board.is_checkmate(W)

    def test_no_checkmate_when_can_capture_attacker(self):
        board = bare_board(
            King(color=W, position=(7, 4)),
            Rook(color=B, position=(7, 7)),  # attacks king from h file? No — same rank
            Rook(color=W, position=(6, 7)),  # white rook can take it
            King(color=B, position=(0, 4)),
        )
        assert board.is_in_check(W)
        assert not board.is_checkmate(W)
