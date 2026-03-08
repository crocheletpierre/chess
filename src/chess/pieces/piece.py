from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, field_validator
from termcolor import colored

if TYPE_CHECKING:
    pass

_DIAGONALS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
_CARDINALS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
_KING_OFFSETS = [
    (-1, -1), (-1, 0), (-1, 1),
    ( 0, -1),           ( 0, 1),
    ( 1, -1), ( 1, 0), ( 1, 1),
]
_KNIGHT_OFFSETS = [
    (-2, -1), (-2, 1),
    (-1, -2), (-1, 2),
    ( 1, -2), ( 1, 2),
    ( 2, -1), ( 2, 1),
]

# Board coordinates: row 0 = rank 8 (black's back rank), row 7 = rank 1 (white's back rank)
Position = tuple[int, int]  # (row, col), both in range [0, 7]


class Color(str, Enum):
    WHITE = "white"
    BLACK = "black"

    @property
    def opponent(self) -> "Color":
        return Color.BLACK if self == Color.WHITE else Color.WHITE


class Piece(BaseModel, ABC):
    """Abstract base class for all chess pieces."""

    color: Color
    position: Position

    model_config = {"arbitrary_types_allowed": True}

    @field_validator("position")
    @classmethod
    def validate_position(cls, v: Position) -> Position:
        row, col = v
        if not (0 <= row <= 7 and 0 <= col <= 7):
            raise ValueError(f"Position {v} is out of bounds (must be 0-7 for each coordinate)")
        return v

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def symbol(self) -> str:
        """Single Unicode character representing this piece."""
        ...

    @abstractmethod
    def legal_moves(self, board: "list[list[Piece | None]]") -> list[Position]:
        """Return all pseudo-legal destination squares for this piece.

        Does NOT filter for checks — callers are responsible for that.

        Args:
            board: 8×8 list of lists where each cell is either a Piece or None.

        Returns:
            List of (row, col) positions this piece can move to.
        """
        ...

    # ------------------------------------------------------------------
    # Helpers shared across subclasses
    # ------------------------------------------------------------------

    def is_opponent(self, other: "Piece | None") -> bool:
        """Return True if *other* belongs to the opposing color."""
        return other is not None and other.color != self.color

    def is_friendly(self, other: "Piece | None") -> bool:
        """Return True if *other* belongs to the same color."""
        return other is not None and other.color == self.color

    def _slide(
        self,
        board: "list[list[Piece | None]]",
        directions: list[tuple[int, int]],
    ) -> list[Position]:
        """Collect squares reachable by sliding in the given directions.

        Stops at board edges, friendly pieces (exclusive), and opponent
        pieces (inclusive — capture allowed).
        """
        moves: list[Position] = []
        row, col = self.position
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r <= 7 and 0 <= c <= 7:
                target = board[r][c]
                if self.is_friendly(target):
                    break
                moves.append((r, c))
                if self.is_opponent(target):
                    break
                r += dr
                c += dc
        return moves

    def _jump(
        self,
        board: "list[list[Piece | None]]",
        offsets: list[tuple[int, int]],
    ) -> list[Position]:
        """Collect squares reachable by jumping to fixed offsets.

        Filters out out-of-bounds squares and squares occupied by friendly pieces.
        """
        moves: list[Position] = []
        row, col = self.position
        for dr, dc in offsets:
            r, c = row + dr, col + dc
            if 0 <= r <= 7 and 0 <= c <= 7:
                target = board[r][c]
                if not self.is_friendly(target):
                    moves.append((r, c))
        return moves

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def render(self) -> str:
        """Return a colored string representation of this piece."""
        term_color = "white" if self.color == Color.WHITE else "cyan"
        return colored(self.symbol, term_color, attrs=["bold"])

    def __str__(self) -> str:
        return self.render()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.color.value}, {self.position})"
