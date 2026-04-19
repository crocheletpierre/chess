"""Tests for per-piece pseudo-legal move generation (ckq.1 – ckq.6)."""

import pytest

from chess.pieces import Bishop, Color, King, Knight, Pawn, Queen, Rook
from chess.pieces.piece import Piece

W = Color.WHITE
B = Color.BLACK


def empty_grid() -> list[list[Piece | None]]:
    return [[None] * 8 for _ in range(8)]


def place(grid: list[list[Piece | None]], *pieces: Piece) -> list[list[Piece | None]]:
    for p in pieces:
        r, c = p.position
        grid[r][c] = p
    return grid


# ---------------------------------------------------------------------------
# Pawn (ckq.1)
# ---------------------------------------------------------------------------

class TestPawn:
    def test_white_single_step(self):
        grid = empty_grid()
        pawn = Pawn(color=W, position=(4, 4))
        place(grid, pawn)
        assert (3, 4) in pawn.legal_moves(grid)

    def test_white_double_step_from_start(self):
        grid = empty_grid()
        pawn = Pawn(color=W, position=(6, 4))
        place(grid, pawn)
        moves = pawn.legal_moves(grid)
        assert (4, 4) in moves
        assert (5, 4) in moves

    def test_white_no_double_step_after_moved(self):
        grid = empty_grid()
        pawn = Pawn(color=W, position=(6, 4), has_moved=True)
        place(grid, pawn)
        moves = pawn.legal_moves(grid)
        assert (4, 4) not in moves

    def test_white_blocked_by_piece(self):
        grid = empty_grid()
        pawn = Pawn(color=W, position=(4, 4))
        blocker = Pawn(color=W, position=(3, 4))
        place(grid, pawn, blocker)
        assert (3, 4) not in pawn.legal_moves(grid)

    def test_double_step_blocked_by_piece_on_intermediate(self):
        grid = empty_grid()
        pawn = Pawn(color=W, position=(6, 4))
        blocker = Pawn(color=B, position=(5, 4))
        place(grid, pawn, blocker)
        moves = pawn.legal_moves(grid)
        assert (5, 4) not in moves
        assert (4, 4) not in moves

    def test_white_diagonal_capture(self):
        grid = empty_grid()
        pawn = Pawn(color=W, position=(4, 4))
        target = Pawn(color=B, position=(3, 5))
        place(grid, pawn, target)
        assert (3, 5) in pawn.legal_moves(grid)

    def test_no_capture_friendly(self):
        grid = empty_grid()
        pawn = Pawn(color=W, position=(4, 4))
        friendly = Pawn(color=W, position=(3, 5))
        place(grid, pawn, friendly)
        assert (3, 5) not in pawn.legal_moves(grid)

    def test_black_moves_down(self):
        grid = empty_grid()
        pawn = Pawn(color=B, position=(1, 4))
        place(grid, pawn)
        moves = pawn.legal_moves(grid)
        assert (2, 4) in moves
        assert (3, 4) in moves

    def test_en_passant_included(self):
        grid = empty_grid()
        pawn = Pawn(color=W, position=(3, 4), en_passant_target=(2, 5))
        place(grid, pawn)
        assert (2, 5) in pawn.legal_moves(grid)


# ---------------------------------------------------------------------------
# Knight (ckq.2)
# ---------------------------------------------------------------------------

class TestKnight:
    def test_center_has_eight_moves(self):
        grid = empty_grid()
        knight = Knight(color=W, position=(4, 4))
        place(grid, knight)
        assert len(knight.legal_moves(grid)) == 8

    def test_corner_has_two_moves(self):
        grid = empty_grid()
        knight = Knight(color=W, position=(0, 0))
        place(grid, knight)
        assert len(knight.legal_moves(grid)) == 2

    def test_jumps_over_pieces(self):
        grid = empty_grid()
        knight = Knight(color=W, position=(4, 4))
        # Fill all adjacent squares
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr != 0 or dc != 0:
                    place(grid, Pawn(color=W, position=(4 + dr, 4 + dc)))
        place(grid, knight)
        assert len(knight.legal_moves(grid)) == 8

    def test_cannot_capture_friendly(self):
        grid = empty_grid()
        knight = Knight(color=W, position=(4, 4))
        friendly = Pawn(color=W, position=(3, 6))
        place(grid, knight, friendly)
        assert (3, 6) not in knight.legal_moves(grid)

    def test_can_capture_opponent(self):
        grid = empty_grid()
        knight = Knight(color=W, position=(4, 4))
        enemy = Pawn(color=B, position=(3, 6))
        place(grid, knight, enemy)
        assert (3, 6) in knight.legal_moves(grid)


# ---------------------------------------------------------------------------
# Bishop (ckq.3)
# ---------------------------------------------------------------------------

class TestBishop:
    def test_center_open_board(self):
        grid = empty_grid()
        bishop = Bishop(color=W, position=(4, 4))
        place(grid, bishop)
        moves = bishop.legal_moves(grid)
        # 4 diagonals, 4+3+3+4 = 13 squares
        assert len(moves) == 13

    def test_blocked_by_friendly(self):
        grid = empty_grid()
        bishop = Bishop(color=W, position=(4, 4))
        blocker = Pawn(color=W, position=(3, 5))
        place(grid, bishop, blocker)
        assert (3, 5) not in bishop.legal_moves(grid)
        assert (2, 6) not in bishop.legal_moves(grid)

    def test_can_capture_then_stops(self):
        grid = empty_grid()
        bishop = Bishop(color=W, position=(4, 4))
        enemy = Pawn(color=B, position=(3, 5))
        place(grid, bishop, enemy)
        moves = bishop.legal_moves(grid)
        assert (3, 5) in moves
        assert (2, 6) not in moves

    def test_corner(self):
        grid = empty_grid()
        bishop = Bishop(color=W, position=(0, 0))
        place(grid, bishop)
        assert len(bishop.legal_moves(grid)) == 7


# ---------------------------------------------------------------------------
# Rook (ckq.4)
# ---------------------------------------------------------------------------

class TestRook:
    def test_center_open_board(self):
        grid = empty_grid()
        rook = Rook(color=W, position=(4, 4))
        place(grid, rook)
        assert len(rook.legal_moves(grid)) == 14

    def test_blocked_by_friendly(self):
        grid = empty_grid()
        rook = Rook(color=W, position=(4, 4))
        blocker = Pawn(color=W, position=(4, 6))
        place(grid, rook, blocker)
        moves = rook.legal_moves(grid)
        assert (4, 6) not in moves
        assert (4, 7) not in moves

    def test_captures_enemy_stops(self):
        grid = empty_grid()
        rook = Rook(color=W, position=(4, 4))
        enemy = Pawn(color=B, position=(4, 6))
        place(grid, rook, enemy)
        moves = rook.legal_moves(grid)
        assert (4, 6) in moves
        assert (4, 7) not in moves

    def test_corner(self):
        grid = empty_grid()
        rook = Rook(color=W, position=(0, 0))
        place(grid, rook)
        assert len(rook.legal_moves(grid)) == 14


# ---------------------------------------------------------------------------
# Queen (ckq.5)
# ---------------------------------------------------------------------------

class TestQueen:
    def test_center_open_board(self):
        grid = empty_grid()
        queen = Queen(color=W, position=(4, 4))
        place(grid, queen)
        assert len(queen.legal_moves(grid)) == 27  # 14 rook + 13 bishop

    def test_blocked_by_friendly(self):
        grid = empty_grid()
        queen = Queen(color=W, position=(4, 4))
        blocker = Pawn(color=W, position=(4, 6))
        place(grid, queen, blocker)
        assert (4, 6) not in queen.legal_moves(grid)

    def test_captures_diagonal(self):
        grid = empty_grid()
        queen = Queen(color=W, position=(4, 4))
        enemy = Pawn(color=B, position=(2, 6))
        place(grid, queen, enemy)
        moves = queen.legal_moves(grid)
        assert (2, 6) in moves
        assert (1, 7) not in moves


# ---------------------------------------------------------------------------
# King (ckq.6)
# ---------------------------------------------------------------------------

class TestKing:
    def test_center_has_eight_moves(self):
        grid = empty_grid()
        king = King(color=W, position=(4, 4))
        place(grid, king)
        assert len(king.legal_moves(grid)) == 8

    def test_corner_has_three_moves(self):
        grid = empty_grid()
        king = King(color=W, position=(0, 0))
        place(grid, king)
        assert len(king.legal_moves(grid)) == 3

    def test_cannot_move_to_friendly(self):
        grid = empty_grid()
        king = King(color=W, position=(4, 4))
        friendly = Pawn(color=W, position=(3, 4))
        place(grid, king, friendly)
        assert (3, 4) not in king.legal_moves(grid)

    def test_can_capture_enemy(self):
        grid = empty_grid()
        king = King(color=W, position=(4, 4))
        enemy = Pawn(color=B, position=(3, 4))
        place(grid, king, enemy)
        assert (3, 4) in king.legal_moves(grid)
