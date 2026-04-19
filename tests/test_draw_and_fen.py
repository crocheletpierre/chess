"""Tests for draw conditions and FEN import/export."""

import pytest

from chess.board import Board
from chess.game import DrawReason, Game, GameStatus, _alg_to_pos, _pos_to_alg
from chess.pieces import Bishop, Color, King, Knight, Pawn, Queen, Rook

W = Color.WHITE
B = Color.BLACK

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


# ---------------------------------------------------------------------------
# FEN export
# ---------------------------------------------------------------------------

class TestFenExport:
    def test_starting_position(self):
        game = Game()
        assert game.to_fen() == STARTING_FEN

    def test_after_e4(self):
        game = Game()
        game.make_move((6, 4), (4, 4))
        fen = game.to_fen()
        parts = fen.split()
        assert parts[0] == "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR"
        assert parts[1] == "b"
        assert parts[4] == "0"   # halfmove clock reset (pawn move)
        assert parts[5] == "1"   # fullmove not yet incremented (black hasn't moved)

    def test_en_passant_square_in_fen(self):
        game = Game()
        game.make_move((6, 4), (4, 4))  # e4
        fen = game.to_fen()
        assert fen.split()[3] == "e3"   # en passant target square

    def test_en_passant_cleared_next_move(self):
        game = Game()
        game.make_move((6, 4), (4, 4))  # e4
        game.make_move((1, 0), (2, 0))  # a6 — not a double push
        assert game.to_fen().split()[3] == "-"

    def test_fullmove_increments_after_black(self):
        game = Game()
        game.make_move((6, 4), (4, 4))  # white
        game.make_move((1, 4), (3, 4))  # black
        assert game.to_fen().split()[5] == "2"

    def test_halfmove_clock_increments_on_non_pawn_non_capture(self):
        game = Game()
        game.make_move((6, 4), (4, 4))  # e4 — resets
        game.make_move((1, 4), (3, 4))  # e5 — resets
        game.make_move((7, 6), (5, 5))  # Nf3 — increments
        assert game.halfmove_clock == 1

    def test_halfmove_clock_resets_on_capture(self):
        game = Game()
        game.make_move((6, 4), (4, 4))  # e4
        game.make_move((1, 3), (3, 3))  # d5
        game.make_move((4, 4), (3, 3))  # exd5
        assert game.halfmove_clock == 0

    def test_castling_rights_lost_after_king_moves(self):
        game = Game()
        # Clear squares between king and rooks manually
        game.board.grid[7][5] = None
        game.board.grid[7][6] = None
        game.make_move((7, 4), (7, 5))  # King moves — loses all castling rights
        fen_castling = game.to_fen().split()[2]
        assert "K" not in fen_castling
        assert "Q" not in fen_castling

    def test_fen_position_only_field(self):
        board = Board.new_game()
        assert board.fen_position() == "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"


# ---------------------------------------------------------------------------
# FEN import
# ---------------------------------------------------------------------------

class TestFenImport:
    def test_starting_position_roundtrip(self):
        game = Game.from_fen(STARTING_FEN)
        assert game.current_turn == W
        assert game.halfmove_clock == 0
        assert game.fullmove_number == 1
        assert game.board.en_passant_square is None

    def test_piece_placement_parsed(self):
        game = Game.from_fen(STARTING_FEN)
        assert isinstance(game.board.grid[0][0], Rook)
        assert isinstance(game.board.grid[7][4], King)
        assert isinstance(game.board.grid[6][0], Pawn)
        assert game.board.grid[6][0].color == W

    def test_active_color_black(self):
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        game = Game.from_fen(fen)
        assert game.current_turn == B

    def test_en_passant_square_parsed(self):
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        game = Game.from_fen(fen)
        assert game.board.en_passant_square == (5, 4)  # e3

    def test_castling_rights_parsed_no_kingside(self):
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w Qkq - 0 1"
        game = Game.from_fen(fen)
        rook = game.board.grid[7][7]
        assert isinstance(rook, Rook)
        assert rook.has_moved  # kingside rook marked as moved

    def test_castling_rights_parsed_no_castling(self):
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1"
        game = Game.from_fen(fen)
        king = game.board.grid[7][4]
        assert isinstance(king, King)
        assert king.has_moved

    def test_halfmove_and_fullmove_parsed(self):
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 42 15"
        game = Game.from_fen(fen)
        assert game.halfmove_clock == 42
        assert game.fullmove_number == 15

    def test_invalid_fen_raises(self):
        with pytest.raises(ValueError, match="FEN"):
            Game.from_fen("not a fen")

    def test_to_fen_from_fen_roundtrip(self):
        game = Game()
        game.make_move((6, 4), (4, 4))
        game.make_move((1, 4), (3, 4))
        game.make_move((7, 6), (5, 5))
        fen = game.to_fen()
        restored = Game.from_fen(fen)
        assert restored.to_fen() == fen


# ---------------------------------------------------------------------------
# Draw: stalemate (via Game)
# ---------------------------------------------------------------------------

class TestDrawStalemate:
    def test_stalemate_sets_draw_status(self):
        board = Board()
        board.grid[0][0] = King(color=B, position=(0, 0))
        board.grid[1][2] = Queen(color=W, position=(1, 2))
        board.grid[2][1] = King(color=W, position=(2, 1))
        # White queen just moved to c7, it's black's turn
        game = Game(board=board, current_turn=B)
        # Trigger via make_move — all of black's moves are illegal so it'll raise
        # but we can verify stalemate is detected on the board directly
        assert game.board.is_stalemate(B)

    def test_stalemate_draw_reason(self):
        board = Board()
        board.grid[0][0] = King(color=B, position=(0, 0))
        board.grid[1][2] = Queen(color=W, position=(1, 2))
        board.grid[2][2] = King(color=W, position=(2, 2))
        game = Game(board=board, current_turn=W)
        # White moves queen to b6 — creates stalemate for black
        game.make_move((1, 2), (2, 1))  # Qb6 — black king now stalemated
        assert game.status == GameStatus.DRAW
        assert game.draw_reason == DrawReason.STALEMATE


# ---------------------------------------------------------------------------
# Draw: threefold repetition
# ---------------------------------------------------------------------------

class TestDrawRepetition:
    def test_repetition_detected_after_three_occurrences(self):
        game = Game()
        # Shuttle the knights back and forth to repeat the position
        for _ in range(2):
            game.make_move((7, 1), (5, 2))  # Nc3
            game.make_move((0, 1), (2, 2))  # Nc6
            game.make_move((5, 2), (7, 1))  # Nb1
            game.make_move((2, 2), (0, 1))  # Nb8
        # After 2 full cycles we've seen the starting position 3 times
        assert game.status == GameStatus.DRAW
        assert game.draw_reason == DrawReason.REPETITION

    def test_no_repetition_on_two_occurrences(self):
        game = Game()
        game.make_move((7, 1), (5, 2))
        game.make_move((0, 1), (2, 2))
        game.make_move((5, 2), (7, 1))
        game.make_move((2, 2), (0, 1))
        # Back to start — that's the 2nd occurrence, not yet 3rd
        assert game.status == GameStatus.ONGOING

    def test_position_count_increments(self):
        game = Game()
        start_key = game._position_key()
        assert game.position_counts[start_key] == 1
        game.make_move((7, 1), (5, 2))
        game.make_move((0, 1), (2, 2))
        game.make_move((5, 2), (7, 1))
        game.make_move((2, 2), (0, 1))
        assert game.position_counts[start_key] == 2


# ---------------------------------------------------------------------------
# Draw: fifty-move rule
# ---------------------------------------------------------------------------

class TestDrawFiftyMoves:
    def test_fifty_move_rule_triggers(self):
        # Position with two kings and two rooks — can shuttle without pawn moves or captures
        board = Board()
        board.grid[7][4] = King(color=W, position=(7, 4), has_moved=True)
        board.grid[0][4] = King(color=B, position=(0, 4), has_moved=True)
        board.grid[7][0] = Rook(color=W, position=(7, 0), has_moved=True)
        board.grid[0][7] = Rook(color=B, position=(0, 7), has_moved=True)
        game = Game(board=board, current_turn=W, halfmove_clock=98)
        game.make_move((7, 0), (6, 0))  # halfmove → 99
        game.make_move((0, 7), (1, 7))  # halfmove → 100 — triggers fifty-move rule
        assert game.status == GameStatus.DRAW
        assert game.draw_reason == DrawReason.FIFTY_MOVES

    def test_fifty_move_resets_on_pawn_move(self):
        game = Game(halfmove_clock=90)
        game.make_move((6, 4), (4, 4))  # pawn move
        assert game.halfmove_clock == 0

    def test_fifty_move_resets_on_capture(self):
        game = Game()
        game.make_move((6, 4), (4, 4))
        game.make_move((1, 3), (3, 3))
        game.board.en_passant_square = None
        game.halfmove_clock = 90
        game.make_move((4, 4), (3, 3))  # capture
        assert game.halfmove_clock == 0


# ---------------------------------------------------------------------------
# Draw: insufficient material
# ---------------------------------------------------------------------------

class TestDrawInsufficientMaterial:
    def _bare(self, *pieces) -> Board:
        board = Board()
        for p in pieces:
            r, c = p.position
            board.grid[r][c] = p
        return board

    def test_k_vs_k(self):
        board = self._bare(
            King(color=W, position=(7, 4)),
            King(color=B, position=(0, 4)),
        )
        game = Game(board=board, current_turn=W)
        assert game.is_draw_by_insufficient_material()

    def test_k_plus_bishop_vs_k(self):
        board = self._bare(
            King(color=W, position=(7, 4)),
            Bishop(color=W, position=(7, 2)),
            King(color=B, position=(0, 4)),
        )
        game = Game(board=board, current_turn=W)
        assert game.is_draw_by_insufficient_material()

    def test_k_plus_knight_vs_k(self):
        board = self._bare(
            King(color=W, position=(7, 4)),
            Knight(color=W, position=(7, 2)),
            King(color=B, position=(0, 4)),
        )
        game = Game(board=board, current_turn=W)
        assert game.is_draw_by_insufficient_material()

    def test_k_plus_b_vs_k_plus_b_same_color(self):
        # Both bishops on light squares (even row+col sum)
        board = self._bare(
            King(color=W, position=(7, 4)),
            Bishop(color=W, position=(6, 5)),  # row+col=11, odd → dark
            King(color=B, position=(0, 4)),
            Bishop(color=B, position=(1, 6)),  # row+col=7, odd → dark
        )
        game = Game(board=board, current_turn=W)
        assert game.is_draw_by_insufficient_material()

    def test_k_plus_b_vs_k_plus_b_different_color(self):
        board = self._bare(
            King(color=W, position=(7, 4)),
            Bishop(color=W, position=(7, 2)),  # row+col=9, odd → dark
            King(color=B, position=(0, 4)),
            Bishop(color=B, position=(0, 2)),  # row+col=2, even → light
        )
        game = Game(board=board, current_turn=W)
        assert not game.is_draw_by_insufficient_material()

    def test_k_plus_rook_vs_k_is_not_draw(self):
        board = self._bare(
            King(color=W, position=(7, 4)),
            Rook(color=W, position=(7, 0), has_moved=True),
            King(color=B, position=(0, 4)),
        )
        game = Game(board=board, current_turn=W)
        assert not game.is_draw_by_insufficient_material()

    def test_insufficient_material_triggers_in_make_move(self):
        # White king captures the last black non-king piece → K vs K
        board = self._bare(
            King(color=W, position=(4, 4)),
            King(color=B, position=(0, 4)),
            Knight(color=B, position=(4, 5)),  # adjacent to white king, not guarded
        )
        game = Game(board=board, current_turn=W)
        game.make_move((4, 4), (4, 5))  # King captures Knight → K vs K
        assert game.status == GameStatus.DRAW
        assert game.draw_reason == DrawReason.INSUFFICIENT_MATERIAL
