from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import NamedTuple

from .board import Board
from .pieces import Color, King, Pawn, Queen, Rook
from .pieces.piece import Position

_FILES = "abcdefgh"


class GameStatus(str, Enum):
    ONGOING = "ongoing"
    CHECKMATE = "checkmate"
    STALEMATE = "stalemate"
    DRAW = "draw"


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
    """Orchestrates a chess game: turn management, move history, and termination."""

    board: Board = field(default_factory=Board.new_game)
    current_turn: Color = Color.WHITE
    history: list[MoveRecord] = field(default_factory=list)
    status: GameStatus = GameStatus.ONGOING

    # ------------------------------------------------------------------
    # State queries
    # ------------------------------------------------------------------

    @property
    def is_over(self) -> bool:
        return self.status != GameStatus.ONGOING

    @property
    def winner(self) -> Color | None:
        """Return the winning color, or None if the game is drawn/ongoing."""
        if self.status == GameStatus.CHECKMATE:
            return self.current_turn.opponent
        return None

    # ------------------------------------------------------------------
    # Move execution
    # ------------------------------------------------------------------

    def make_move(self, from_pos: Position, to_pos: Position) -> MoveRecord:
        """Validate and execute a move for the current player.

        Raises ValueError if the move is illegal or the game is already over.
        Returns the MoveRecord describing the move.
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
        captured = self.board.move(from_pos, to_pos)
        captured_symbol = captured.symbol if captured is not None else None

        # Advance turn
        self.current_turn = self.current_turn.opponent

        # Evaluate game state
        in_check = self.board.is_in_check(self.current_turn)
        if self.board.is_checkmate(self.current_turn):
            self.status = GameStatus.CHECKMATE
            is_checkmate = True
        elif self.board.is_stalemate(self.current_turn):
            self.status = GameStatus.STALEMATE
            is_checkmate = False
        else:
            is_checkmate = False

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
    # Input parsing
    # ------------------------------------------------------------------

    @staticmethod
    def parse_move(text: str) -> tuple[Position, Position]:
        """Parse a move string into (from_pos, to_pos).

        Accepts coordinate notation: "e2e4", "e2-e4", or "e2 e4".
        """
        text = text.strip().lower().replace("-", "").replace(" ", "")
        if len(text) != 4:
            raise ValueError(
                f"Invalid move '{text}'. Use coordinate notation like 'e2e4'."
            )
        from_pos = _alg_to_pos(text[:2])
        to_pos = _alg_to_pos(text[2:])
        return from_pos, to_pos

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def render(self) -> str:
        """Return the board plus status line."""
        lines = [self.board.render(), ""]
        if self.status == GameStatus.CHECKMATE:
            winner = self.winner
            lines.append(f"Checkmate! {winner.value.capitalize()} wins.")  # type: ignore[union-attr]
        elif self.status == GameStatus.STALEMATE:
            lines.append("Stalemate! The game is a draw.")
        else:
            in_check = " (in check!)" if self.board.is_in_check(self.current_turn) else ""
            lines.append(f"{self.current_turn.value.capitalize()} to move{in_check}")
        return "\n".join(lines)


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
