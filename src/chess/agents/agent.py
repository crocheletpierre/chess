from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..game import Game
    from ..pieces.piece import Position


class Agent(ABC):
    """Abstract base class for all chess AI agents.

    Subclasses must implement `name` and `choose_move`.

    For search-based agents (minimax, alpha-beta, H-minimax, …) the evaluation
    interface provides a ready-made contract aligned with AIMA ch. 5:

        evaluate(game)          EVAL function — heuristic score of a non-terminal
                                position from game.current_turn's perspective
                                (negamax convention: positive = good for the mover).

        utility(game)           UTILITY function — exact score of a terminal
                                position (+inf win, -inf loss, 0 draw).
                                Concrete default is provided.

        cutoff_test(game, depth)  CUTOFF-TEST — whether to stop the search here.
                                  Default: stop when depth >= max_depth or the
                                  move time budget is exhausted.

    Time management
    ---------------
    Call `self._start_move_timer()` at the top of `choose_move`. Then use
    `self.time_remaining()` inside your search to check the budget, and
    `self.time_elapsed()` for logging.

    Configurable class-level defaults (override in __init__):
        max_depth   int    depth at which cutoff_test returns True  (default 3)
        time_limit  float  seconds per move; inf = no limit         (default inf)
    """

    max_depth: int = 3
    time_limit: float = float("inf")

    # ------------------------------------------------------------------
    # Required interface
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name displayed in the game loop."""
        ...

    @abstractmethod
    def choose_move(self, game: "Game") -> "tuple[Position, Position]":
        """Return the (from_pos, to_pos) the agent wants to play.

        The returned move must be legal — the game loop will raise if it is not.
        """
        ...

    # ------------------------------------------------------------------
    # Evaluation interface (AIMA ch. 5)
    # ------------------------------------------------------------------

    def evaluate(self, game: "Game") -> float:
        """Heuristic score of a non-terminal position (EVAL in AIMA).

        Convention: positive = good for game.current_turn (the side to move).
        This is the *negamax* convention — the search negates the value at
        each level, so you only need to think about 'higher is better for me'.

        Subclasses implementing search MUST override this method.
        """
        raise NotImplementedError(
            f"{type(self).__name__}.evaluate() is not implemented. "
            "Override it to enable search-based move selection."
        )

    def utility(self, game: "Game") -> float:
        """Exact score of a terminal position (UTILITY in AIMA).

        Returns:
            -inf  if game.current_turn is in checkmate (current player lost).
             0.0  for any draw (stalemate, repetition, 50-move, insufficient material).

        Follows the negamax convention so it can be returned directly in a
        negamax search without sign-flipping.
        """
        from ..game import GameStatus

        if game.status == GameStatus.CHECKMATE:
            return float("-inf")  # current player is the one who got checkmated
        return 0.0  # draw of any kind

    def cutoff_test(self, game: "Game", depth: int) -> bool:
        """Return True if the search should stop at this node (CUTOFF-TEST in AIMA).

        Default behaviour:
          - Always stop at terminal positions.
          - Stop when depth >= self.max_depth.
          - Stop when the move time budget is exhausted (if time_limit is set).

        Override for custom strategies (quiescence search, iterative deepening, …).
        """
        if game.is_over:
            return True
        if depth >= self.max_depth:
            return True
        if self.time_limit < float("inf") and self.time_remaining() <= 0:
            return True
        return False

    # ------------------------------------------------------------------
    # Time management helpers
    # ------------------------------------------------------------------

    def _start_move_timer(self) -> None:
        """Record the deadline for the current move.

        Call this once at the top of choose_move so that cutoff_test and
        time_remaining() work correctly throughout the search.
        """
        self._move_deadline: float = time.monotonic() + self.time_limit

    def time_elapsed(self) -> float:
        """Seconds elapsed since _start_move_timer() was called."""
        if not hasattr(self, "_move_deadline"):
            return 0.0
        return time.monotonic() - (self._move_deadline - self.time_limit)

    def time_remaining(self) -> float:
        """Seconds remaining before the move time budget expires."""
        if not hasattr(self, "_move_deadline"):
            return float("inf")
        return max(0.0, self._move_deadline - time.monotonic())

    # ------------------------------------------------------------------
    # Optional lifecycle hooks
    # ------------------------------------------------------------------

    def on_game_start(self, game: "Game") -> None:
        """Called once before the first move. Override to set up per-game state."""

    def on_move_made(
        self,
        game: "Game",
        from_pos: "Position",
        to_pos: "Position",
    ) -> None:
        """Called after every move (by either side). Override to track board state."""
