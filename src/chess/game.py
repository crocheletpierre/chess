from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import NamedTuple

from .board import Board
from .pieces import Bishop, Color, King, Knight, Pawn, Queen, Rook
from .pieces.piece import Position

_FILES = "abcdefgh"


class GameStatus(str, Enum):
    ONGOING = "ongoing"
    CHECKMATE = "checkmate"
    STALEMATE = "stalemate"
    DRAW = "draw"


class DrawReason(str, Enum):
    STALEMATE = "stalemate"
    REPETITION = "threefold repetition"
    FIFTY_MOVES = "fifty-move rule"
    INSUFFICIENT_MATERIAL = "insufficient material"


class MoveRecord(NamedTuple):
    from_pos: Position
    to_pos: Position
    piece_symbol: str
    captured_symbol: str | None
    is_check: bool
    is_checkmate: bool
    notation: str  # coordinate notation, e.g. "e2e4"


@dataclass
class Game:
    """Orchestrates a chess game: turn management, move history, draw detection, and FEN."""

    board: Board = field(default_factory=Board.new_game)
    current_turn: Color = Color.WHITE
    history: list[MoveRecord] = field(default_factory=list)
    status: GameStatus = GameStatus.ONGOING
    draw_reason: DrawReason | None = None
    halfmove_clock: int = 0
    fullmove_number: int = 1
    # Counts how many times each position (placement+turn+castling+ep) has occurred
    position_counts: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Record the starting position
        self._record_position()

    # ------------------------------------------------------------------
    # State queries
    # ------------------------------------------------------------------

    @property
    def is_over(self) -> bool:
        return self.status != GameStatus.ONGOING

    @property
    def winner(self) -> Color | None:
        if self.status == GameStatus.CHECKMATE:
            return self.current_turn.opponent
        return None

    # ------------------------------------------------------------------
    # Draw detection
    # ------------------------------------------------------------------

    def is_draw_by_repetition(self) -> bool:
        """Return True if the current position has occurred three or more times."""
        return self.position_counts.get(self._position_key(), 0) >= 3

    def is_draw_by_fifty_moves(self) -> bool:
        """Return True if 50 consecutive moves have been played without a pawn move or capture."""
        return self.halfmove_clock >= 100  # halfmove_clock counts half-moves

    def is_draw_by_insufficient_material(self) -> bool:
        """Return True if neither side has enough material to deliver checkmate."""
        white_pieces = [
            p for row in self.board.grid for p in row
            if p is not None and p.color == Color.WHITE
        ]
        black_pieces = [
            p for row in self.board.grid for p in row
            if p is not None and p.color == Color.BLACK
        ]

        def piece_types(pieces: list) -> list[str]:
            return sorted([type(p).__name__ for p in pieces if not isinstance(p, King)])

        wt = piece_types(white_pieces)
        bt = piece_types(black_pieces)

        # K vs K
        if not wt and not bt:
            return True
        # K+minor vs K, or K vs K+minor
        minor = {"Bishop", "Knight"}
        if (not wt and len(bt) == 1 and bt[0] in minor) or \
           (not bt and len(wt) == 1 and wt[0] in minor):
            return True
        # K+B vs K+B — only drawn if both bishops on the same color square
        if wt == ["Bishop"] and bt == ["Bishop"]:
            wb = next(p for p in white_pieces if isinstance(p, Bishop))
            bb = next(p for p in black_pieces if isinstance(p, Bishop))
            w_sq_color = (wb.position[0] + wb.position[1]) % 2
            b_sq_color = (bb.position[0] + bb.position[1]) % 2
            return w_sq_color == b_sq_color

        return False

    # ------------------------------------------------------------------
    # Move execution
    # ------------------------------------------------------------------

    def make_move(self, from_pos: Position, to_pos: Position) -> MoveRecord:
        """Validate and execute a move for the current player.

        Raises ValueError if the move is illegal or the game is already over.
        """
        if self.is_over:
            raise ValueError("The game is already over.")

        piece = self.board.piece_at(from_pos)
        if piece is None:
            raise ValueError(f"No piece at {_pos_to_alg(from_pos)}.")
        if piece.color != self.current_turn:
            raise ValueError(
                f"It is {self.current_turn.value}'s turn, "
                f"but the piece at {_pos_to_alg(from_pos)} is {piece.color.value}."
            )

        legal = self.board.legal_moves(from_pos)
        if to_pos not in legal:
            raise ValueError(
                f"{_pos_to_alg(from_pos)}{_pos_to_alg(to_pos)} is not a legal move."
            )

        piece_symbol = piece.symbol
        is_pawn_move = isinstance(piece, Pawn)

        captured = self.board.move(from_pos, to_pos)
        captured_symbol = captured.symbol if captured is not None else None

        # Update clocks
        if is_pawn_move or captured is not None:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1
        if self.current_turn == Color.BLACK:
            self.fullmove_number += 1

        self.current_turn = self.current_turn.opponent
        self._record_position()

        # Evaluate game state
        in_check = self.board.is_in_check(self.current_turn)
        is_checkmate = False

        if self.board.is_checkmate(self.current_turn):
            self.status = GameStatus.CHECKMATE
            is_checkmate = True
        elif self.board.is_stalemate(self.current_turn):
            self.status = GameStatus.DRAW
            self.draw_reason = DrawReason.STALEMATE
        elif self.is_draw_by_repetition():
            self.status = GameStatus.DRAW
            self.draw_reason = DrawReason.REPETITION
        elif self.is_draw_by_fifty_moves():
            self.status = GameStatus.DRAW
            self.draw_reason = DrawReason.FIFTY_MOVES
        elif self.is_draw_by_insufficient_material():
            self.status = GameStatus.DRAW
            self.draw_reason = DrawReason.INSUFFICIENT_MATERIAL

        record = MoveRecord(
            from_pos=from_pos,
            to_pos=to_pos,
            piece_symbol=piece_symbol,
            captured_symbol=captured_symbol,
            is_check=in_check,
            is_checkmate=is_checkmate,
            notation=f"{_pos_to_alg(from_pos)}{_pos_to_alg(to_pos)}",
        )
        self.history.append(record)
        return record

    # ------------------------------------------------------------------
    # FEN
    # ------------------------------------------------------------------

    def to_fen(self) -> str:
        """Return the full FEN string for the current game state."""
        color = "w" if self.current_turn == Color.WHITE else "b"
        ep = _pos_to_alg(self.board.en_passant_square) if self.board.en_passant_square else "-"
        return (
            f"{self.board.fen_position()} {color} "
            f"{self.board.fen_castling()} {ep} "
            f"{self.halfmove_clock} {self.fullmove_number}"
        )

    @classmethod
    def from_fen(cls, fen: str) -> "Game":
        """Construct a Game from a FEN string."""
        parts = fen.strip().split()
        if len(parts) != 6:
            raise ValueError(f"Invalid FEN: expected 6 fields, got {len(parts)}.")

        placement, color, castling, ep_str, halfmove, fullmove = parts

        board = Board.from_fen_position(placement, castling)
        current_turn = Color.WHITE if color == "w" else Color.BLACK

        ep_square: Position | None = None
        if ep_str != "-":
            ep_square = _alg_to_pos(ep_str)
        board.en_passant_square = ep_square

        game = cls(
            board=board,
            current_turn=current_turn,
            halfmove_clock=int(halfmove),
            fullmove_number=int(fullmove),
        )
        return game

    # ------------------------------------------------------------------
    # Input parsing
    # ------------------------------------------------------------------

    @staticmethod
    def parse_move(text: str) -> tuple[Position, Position]:
        """Parse coordinate notation into (from_pos, to_pos).

        Accepts: "e2e4", "e2-e4", "e2 e4".
        """
        text = text.strip().lower().replace("-", "").replace(" ", "")
        if len(text) != 4:
            raise ValueError(
                f"Invalid move '{text}'. Use coordinate notation like 'e2e4'."
            )
        return _alg_to_pos(text[:2]), _alg_to_pos(text[2:])

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def render(self) -> str:
        lines = [self.board.render(), ""]
        if self.status == GameStatus.CHECKMATE:
            lines.append(f"Checkmate! {self.winner.value.capitalize()} wins.")  # type: ignore[union-attr]
        elif self.status == GameStatus.DRAW:
            lines.append(f"Draw by {self.draw_reason.value}.")  # type: ignore[union-attr]
        else:
            in_check = " (in check!)" if self.board.is_in_check(self.current_turn) else ""
            lines.append(f"{self.current_turn.value.capitalize()} to move{in_check}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _position_key(self) -> str:
        """Encode the current position as a string for repetition detection."""
        ep = _pos_to_alg(self.board.en_passant_square) if self.board.en_passant_square else "-"
        color = "w" if self.current_turn == Color.WHITE else "b"
        return f"{self.board.fen_position()} {color} {self.board.fen_castling()} {ep}"

    def _record_position(self) -> None:
        key = self._position_key()
        self.position_counts[key] = self.position_counts.get(key, 0) + 1


# ------------------------------------------------------------------
# Coordinate helpers
# ------------------------------------------------------------------

def _alg_to_pos(square: str) -> Position:
    """Convert algebraic square ('e2') to board position (row, col)."""
    if len(square) != 2 or square[0] not in _FILES or square[1] not in "12345678":
        raise ValueError(f"Invalid square '{square}'.")
    col = _FILES.index(square[0])
    row = 8 - int(square[1])
    return (row, col)


def _pos_to_alg(pos: Position) -> str:
    """Convert board position (row, col) to algebraic square ('e2')."""
    row, col = pos
    return f"{_FILES[col]}{8 - row}"
