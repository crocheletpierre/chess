"""SimpleAgent: material-count evaluation with BFS-style iterative deepening.

Search strategy
---------------
BFS explores a graph level by level — all nodes at depth d before any at
depth d+1. Applied to a game tree this becomes *iterative deepening*: run a
full depth-1 negamax, then depth-2, then depth-3, … stopping when the time
budget expires. Each completed depth refines the best-move estimate; the last
*fully completed* depth is returned.

Time budget
-----------
The budget decays exponentially with the number of half-moves already played:

    budget(n) = base_time × exp(−decay × n)

This allocates more thinking time in the opening (many possibilities, high
strategic value) and progressively less time in the endgame (simpler
positions, fewer legal moves).
"""

from __future__ import annotations

import math

from .agent import Agent
from ..board import Board
from ..game import Game
from ..pieces import Bishop, Color, King, Knight, Pawn, Queen, Rook
from ..pieces.piece import Position

# Standard piece values (King excluded — always present, not counted)
_PIECE_VALUES: dict[type, float] = {
    Pawn:   1.0,
    Knight: 3.0,
    Bishop: 3.25,
    Rook:   5.0,
    Queen:  9.0,
}


class SimpleAgent(Agent):
    """Chess agent using material-count evaluation and BFS-style iterative deepening.

    Parameters
    ----------
    base_time : float
        Time budget (seconds) at move 0. Decreases exponentially.
    decay : float
        Exponential decay rate applied to the half-move count.
        budget(n) = base_time × exp(−decay × n)
    """

    def __init__(self, base_time: float = 2.0, decay: float = 0.02) -> None:
        self.base_time = base_time
        self.decay = decay

    @property
    def name(self) -> str:
        return "Simple"

    # ------------------------------------------------------------------
    # Evaluation (AIMA EVAL function)
    # ------------------------------------------------------------------

    def evaluate(self, game: Game) -> float:
        """Material score from game.current_turn's perspective (negamax convention)."""
        return self._eval_board(game.board, game.current_turn)

    def _eval_board(self, board: Board, color: Color) -> float:
        """Sum piece values: positive = good for *color*."""
        score = 0.0
        for row in board.grid:
            for piece in row:
                if piece is None or type(piece) not in _PIECE_VALUES:
                    continue
                v = _PIECE_VALUES[type(piece)]
                score += v if piece.color == color else -v
        return score

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def choose_move(self, game: Game) -> tuple[Position, Position]:
        """BFS-style iterative deepening negamax with exponential time budget."""
        # Compute and start the move timer
        n = len(game.history)
        self.time_limit = self.base_time * math.exp(-self.decay * n)
        self._start_move_timer()

        moves = game.board.all_legal_moves(game.current_turn)
        if not moves:
            raise RuntimeError("choose_move called but no legal moves available.")

        best_move = moves[0]  # fallback: first legal move

        # BFS level-by-level: search depth 1, then 2, …
        for depth in range(1, 50):
            if self.time_remaining() <= 0:
                break

            candidate, completed = self._search_depth(
                game.board, game.current_turn, moves, depth
            )

            # Only promote a result from a fully completed depth pass
            if completed and candidate is not None:
                best_move = candidate

        return best_move

    def _search_depth(
        self,
        board: Board,
        color: Color,
        moves: list[tuple[Position, Position]],
        depth: int,
    ) -> tuple[tuple[Position, Position] | None, bool]:
        """Evaluate all root moves at *depth* via negamax.

        Returns (best_move, completed) where *completed* is False if the
        time budget expired before all root moves were evaluated.
        """
        best_score = float("-inf")
        best_move: tuple[Position, Position] | None = None

        for from_pos, to_pos in moves:
            if self.time_remaining() <= 0:
                return best_move, False  # aborted mid-level

            sim = board._simulate(from_pos, to_pos)
            score = -self._negamax(sim, color.opponent, depth - 1)

            if score > best_score:
                best_score = score
                best_move = (from_pos, to_pos)

        return best_move, True

    def _negamax(self, board: Board, color: Color, depth: int) -> float:
        """Negamax: returns the score of *board* from *color*'s perspective.

        Positive = good for *color*. The caller negates the result to get
        the score from the opponent's perspective.
        """
        if board.is_checkmate(color):
            return float("-inf")
        if board.is_stalemate(color):
            return 0.0
        if depth == 0 or self.time_remaining() <= 0:
            return self._eval_board(board, color)

        best = float("-inf")
        for from_pos, to_pos in board.all_legal_moves(color):
            if self.time_remaining() <= 0:
                break
            sim = board._simulate(from_pos, to_pos)
            score = -self._negamax(sim, color.opponent, depth - 1)
            if score > best:
                best = score

        return best
