import copy

from .pieces import Bishop, Color, King, Knight, Pawn, Queen, Rook
from .pieces.piece import Piece, Position

_FILE_LABELS = "  a b c d e f g h"
_BACK_RANK = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]


class Board:
    """8x8 chess board managing piece placement, move execution, and rule enforcement."""

    def __init__(self) -> None:
        self.grid: list[list[Piece | None]] = [[None] * 8 for _ in range(8)]
        # The square the capturing pawn lands on, i.e. behind the double-pushed pawn
        self.en_passant_square: Position | None = None

    @classmethod
    def new_game(cls) -> "Board":
        """Return a Board with the standard chess starting position."""
        board = cls()
        # Black setup
        for col, piece_cls in enumerate(_BACK_RANK):
            board.grid[0][col] = piece_cls(color=Color.BLACK, position=(0, col))
        for col in range(8):
            board.grid[1][col] = Pawn(color=Color.BLACK, position=(1, col))

        # White setup
        for col in range(8):
            board.grid[6][col] = Pawn(color=Color.WHITE, position=(6, col))
        for col, piece_cls in enumerate(_BACK_RANK):
            board.grid[7][col] = piece_cls(color=Color.WHITE, position=(7, col))
        return board

    def piece_at(self, position: Position) -> Piece | None:
        row, col = position
        return self.grid[row][col]

    def _find_king(self, color: Color) -> Position:
        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if isinstance(piece, King) and piece.color == color:
                    return (row, col)
        raise RuntimeError(f"No {color.value} king on the board. The game should be over")

    def is_in_check(self, color: Color) -> bool:
        """Return True if the *color* king is currently attacked by any opponent piece."""
        king_pos = self._find_king(color)
        opponent = color.opponent
        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if piece is not None and piece.color == opponent:
                    if king_pos in piece.legal_moves(self.grid):
                        return True
        return False

    # ------------------------------------------------------------------
    # Legal move generation
    # ------------------------------------------------------------------

    def legal_moves(self, from_pos: Position) -> list[Position]:
        """Return all fully legal moves for the piece at *from_pos*.

        Filters pseudo-legal moves by simulating each move and checking
        whether it leaves the moving side's king in check. Also injects
        special moves: castling and en passant.
        """
        piece = self.piece_at(from_pos)
        if piece is None:
            return []

        pseudo = piece.legal_moves(self.grid)

        # Inject castling squares for the king
        if isinstance(piece, King):
            pseudo += self._castling_moves(piece)

        # Inject en passant for pawns
        if isinstance(piece, Pawn) and self.en_passant_square is not None:
            ep = self.en_passant_square
            row, col = from_pos
            ep_row, ep_col = ep
            direction = -1 if piece.color == Color.WHITE else 1
            if ep_row == row + direction and abs(ep_col - col) == 1:
                pseudo.append(ep)

        # Filter: keep only moves that don't leave own king in check
        legal: list[Position] = []
        for to_pos in pseudo:
            sim = self._simulate(from_pos, to_pos)
            if not sim.is_in_check(piece.color):
                legal.append(to_pos)

        return legal

    def all_legal_moves(self, color: Color) -> list[tuple[Position, Position]]:
        """Return every (from, to) legal move pair for *color*."""
        moves: list[tuple[Position, Position]] = []
        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if piece is not None and piece.color == color:
                    for to_pos in self.legal_moves((row, col)):
                        moves.append(((row, col), to_pos))
        return moves

    # ------------------------------------------------------------------
    # Game-state checks
    # ------------------------------------------------------------------

    def is_checkmate(self, color: Color) -> bool:
        """Return True if *color* is in checkmate (in check with no legal moves)."""
        return self.is_in_check(color) and len(self.all_legal_moves(color)) == 0

    def is_stalemate(self, color: Color) -> bool:
        """Return True if *color* is in stalemate (not in check but no legal moves)."""
        return not self.is_in_check(color) and len(self.all_legal_moves(color)) == 0

    # ------------------------------------------------------------------
    # Move execution
    # ------------------------------------------------------------------

    def move(self, from_pos: Position, to_pos: Position) -> Piece | None:
        """Execute a move and return the captured piece (or None).

        Handles: normal moves, en passant capture, castling,
        pawn promotion (auto-promotes to Queen), and en passant square updates.
        """
        from_row, from_col = from_pos
        to_row, to_col = to_pos

        piece = self.grid[from_row][from_col]
        if piece is None:
            raise ValueError(f"No piece at {from_pos}")

        captured = self.grid[to_row][to_col]
        next_ep_square: Position | None = None

        # --- En passant capture ---
        if isinstance(piece, Pawn) and to_pos == self.en_passant_square:
            captured_row = from_row
            captured = self.grid[captured_row][to_col]
            self.grid[captured_row][to_col] = None

        # --- Double pawn push: set en passant square ---
        if isinstance(piece, Pawn) and abs(to_row - from_row) == 2:
            direction = -1 if piece.color == Color.WHITE else 1
            next_ep_square = (from_row + direction, from_col)

        # --- Castling: move the rook ---
        if isinstance(piece, King) and abs(to_col - from_col) == 2:
            if to_col == 6:  # kingside
                rook_from = (from_row, 7)
                rook_to = (from_row, 5)
            else:  # queenside
                rook_from = (from_row, 0)
                rook_to = (from_row, 3)
            rook = self.grid[rook_from[0]][rook_from[1]]
            self.grid[rook_to[0]][rook_to[1]] = rook
            self.grid[rook_from[0]][rook_from[1]] = None
            if isinstance(rook, Rook):
                rook.position = rook_to
                rook.has_moved = True

        self.grid[to_row][to_col] = piece
        self.grid[from_row][from_col] = None
        piece.position = to_pos

        if isinstance(piece, (Pawn, King, Rook)):
            piece.has_moved = True

        # --- Pawn promotion ---
        back_rank = 0 if piece.color == Color.WHITE else 7
        if isinstance(piece, Pawn) and to_row == back_rank:
            self.grid[to_row][to_col] = Queen(color=piece.color, position=to_pos)

        self.en_passant_square = next_ep_square
        return captured

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _simulate(self, from_pos: Position, to_pos: Position) -> "Board":
        """Return a deep-copied board after executing *from_pos* → *to_pos*."""
        sim = copy.deepcopy(self)
        sim.move(from_pos, to_pos)
        return sim

    def _castling_moves(self, king: King) -> list[Position]:
        """Return castling destination squares available to *king*."""
        if king.has_moved:
            return []

        color = king.color
        row = 7 if color == Color.WHITE else 0
        moves: list[Position] = []

        # King must not currently be in check
        if self.is_in_check(color):
            return []

        # Kingside: rook at col 7, squares 5 and 6 must be empty and not attacked
        rook_ks = self.grid[row][7]
        if (
            isinstance(rook_ks, Rook)
            and not rook_ks.has_moved
            and self.grid[row][5] is None
            and self.grid[row][6] is None
            and not self._square_attacked((row, 5), color.opponent)
            and not self._square_attacked((row, 6), color.opponent)
        ):
            moves.append((row, 6))

        # Queenside: rook at col 0, squares 1, 2, 3 must be empty; 2 and 3 not attacked
        rook_qs = self.grid[row][0]
        if (
            isinstance(rook_qs, Rook)
            and not rook_qs.has_moved
            and self.grid[row][1] is None
            and self.grid[row][2] is None
            and self.grid[row][3] is None
            and not self._square_attacked((row, 2), color.opponent)
            and not self._square_attacked((row, 3), color.opponent)
        ):
            moves.append((row, 2))

        return moves

    def _square_attacked(self, square: Position, by_color: Color) -> bool:
        """Return True if *square* is attacked by any piece of *by_color*."""
        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if piece is not None and piece.color == by_color:
                    if square in piece.legal_moves(self.grid):
                        return True
        return False

    def render(self) -> str:
        """Return a terminal-friendly string of the current board state."""
        lines = [_FILE_LABELS]
        for row in range(8):
            rank = 8 - row
            cells = [piece.render() if piece else "·" for piece in self.grid[row]]
            lines.append(f"{rank} {' '.join(cells)} {rank}")
        lines.append(_FILE_LABELS)
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.render()
