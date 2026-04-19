"""Tests for the Game class: turn management, input parsing, termination (ckq.10)."""

import pytest

from chess.game import Game, GameStatus, _alg_to_pos, _pos_to_alg
from chess.pieces import Color, King, Pawn, Queen, Rook
from chess.board import Board

W = Color.WHITE
B = Color.BLACK


# ---------------------------------------------------------------------------
# Coordinate helpers
# ---------------------------------------------------------------------------

class TestCoordinateHelpers:
    def test_alg_to_pos_e2(self):
        assert _alg_to_pos("e2") == (6, 4)

    def test_alg_to_pos_a8(self):
        assert _alg_to_pos("a8") == (0, 0)

    def test_alg_to_pos_h1(self):
        assert _alg_to_pos("h1") == (7, 7)

    def test_pos_to_alg_roundtrip(self):
        for row in range(8):
            for col in range(8):
                assert _alg_to_pos(_pos_to_alg((row, col))) == (row, col)

    def test_alg_to_pos_invalid(self):
        with pytest.raises(ValueError):
            _alg_to_pos("z9")


# ---------------------------------------------------------------------------
# Input parsing
# ---------------------------------------------------------------------------

class TestParseMoves:
    def test_plain(self):
        assert Game.parse_move("e2e4") == ((6, 4), (4, 4))

    def test_dash_separator(self):
        assert Game.parse_move("e2-e4") == ((6, 4), (4, 4))

    def test_space_separator(self):
        assert Game.parse_move("e2 e4") == ((6, 4), (4, 4))

    def test_uppercase(self):
        assert Game.parse_move("E2E4") == ((6, 4), (4, 4))

    def test_invalid_length(self):
        with pytest.raises(ValueError):
            Game.parse_move("e2")

    def test_invalid_square(self):
        with pytest.raises(ValueError):
            Game.parse_move("z9z9")


# ---------------------------------------------------------------------------
# Turn management
# ---------------------------------------------------------------------------

class TestTurnManagement:
    def test_starts_white(self):
        game = Game()
        assert game.current_turn == W

    def test_turn_alternates(self):
        game = Game()
        game.make_move((6, 4), (4, 4))  # e4
        assert game.current_turn == B
        game.make_move((1, 4), (3, 4))  # e5
        assert game.current_turn == W

    def test_wrong_color_raises(self):
        game = Game()
        with pytest.raises(ValueError, match="white"):
            game.make_move((1, 4), (3, 4))  # black piece on white's turn

    def test_empty_square_raises(self):
        game = Game()
        with pytest.raises(ValueError):
            game.make_move((4, 4), (3, 4))

    def test_illegal_move_raises(self):
        game = Game()
        with pytest.raises(ValueError, match="legal"):
            game.make_move((6, 4), (3, 4))  # pawn can't jump 3 squares


# ---------------------------------------------------------------------------
# Move history
# ---------------------------------------------------------------------------

class TestMoveHistory:
    def test_history_records_moves(self):
        game = Game()
        game.make_move((6, 4), (4, 4))
        assert len(game.history) == 1
        assert game.history[0].notation == "e2e4"

    def test_history_records_capture(self):
        game = Game()
        # Scholars mate setup to get a capture
        game.make_move((6, 4), (4, 4))  # e4
        game.make_move((1, 4), (3, 4))  # e5
        game.make_move((7, 5), (4, 2))  # Bc4
        game.make_move((0, 1), (2, 2))  # Nc6
        game.make_move((4, 2), (1, 5))  # Bxf7
        rec = game.history[-1]
        assert rec.captured_symbol is not None

    def test_history_records_check(self):
        game = Game()
        # Fool's mate
        game.make_move((6, 5), (5, 5))  # f3
        game.make_move((1, 4), (3, 4))  # e5
        game.make_move((6, 6), (4, 6))  # g4
        game.make_move((0, 3), (4, 7))  # Qh4#
        last = game.history[-1]
        assert last.is_check
        assert last.is_checkmate


# ---------------------------------------------------------------------------
# Game termination
# ---------------------------------------------------------------------------

class TestGameTermination:
    def test_fool_mate_checkmate(self):
        game = Game()
        game.make_move((6, 5), (5, 5))
        game.make_move((1, 4), (3, 4))
        game.make_move((6, 6), (4, 6))
        game.make_move((0, 3), (4, 7))
        assert game.status == GameStatus.CHECKMATE
        assert game.is_over
        assert game.winner == B

    def test_stalemate_status(self):
        # Build stalemate position via Game
        board = Board()
        board.grid[0][0] = King(color=B, position=(0, 0))
        board.grid[1][2] = Queen(color=W, position=(1, 2))
        board.grid[2][1] = King(color=W, position=(2, 1))
        game = Game(board=board, current_turn=B)
        assert game.board.is_stalemate(B)
        # Trigger status update by attempting a move (all illegal for black)
        with pytest.raises(ValueError):
            game.make_move((0, 0), (0, 1))

    def test_move_after_game_over_raises(self):
        game = Game()
        game.make_move((6, 5), (5, 5))
        game.make_move((1, 4), (3, 4))
        game.make_move((6, 6), (4, 6))
        game.make_move((0, 3), (4, 7))
        assert game.is_over
        with pytest.raises(ValueError, match="over"):
            game.make_move((6, 4), (4, 4))

    def test_winner_none_when_ongoing(self):
        game = Game()
        assert game.winner is None

    def test_winner_none_on_stalemate(self):
        board = Board()
        board.grid[0][0] = King(color=B, position=(0, 0))
        board.grid[1][2] = Queen(color=W, position=(1, 2))
        board.grid[2][1] = King(color=W, position=(2, 1))
        game = Game(board=board, current_turn=B, status=GameStatus.STALEMATE)
        assert game.winner is None
