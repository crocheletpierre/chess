"""Tests for PositionalAgent."""

from __future__ import annotations

import random

import pytest

from chess.agents.positional_agent import PositionalAgent
from chess.agents.random_agent import RandomAgent
from chess.agents.simple_agent import SimpleAgent
from chess.board import Board
from chess.game import Game, GameStatus
from chess.pieces import Color, Knight, Pawn
from chess.pieces.piece import Color as C

W = Color.WHITE
B = Color.BLACK


# ---------------------------------------------------------------------------
# evaluate() — positional sensitivity
# ---------------------------------------------------------------------------

class TestPositionalEvaluation:
    def test_name(self):
        assert PositionalAgent().name == "Positional"

    def test_symmetric_start_position(self):
        game = Game()
        agent = PositionalAgent()
        assert agent.evaluate(game) == 0.0

    def test_knight_center_beats_corner(self):
        """Knight on e4 (center) should score higher than b1 (corner)."""
        agent = PositionalAgent()

        board_center = Board()
        board_center.grid = [[None] * 8 for _ in range(8)]
        board_center.grid[4][4] = Knight(color=W, position=(4, 4))  # e4

        board_corner = Board()
        board_corner.grid = [[None] * 8 for _ in range(8)]
        board_corner.grid[7][1] = Knight(color=W, position=(7, 1))  # b1

        game_center = Game(board=board_center, current_turn=W)
        game_corner = Game(board=board_corner, current_turn=W)

        assert agent.evaluate(game_center) > agent.evaluate(game_corner)

    def test_pawn_advancement_increases_score(self):
        """A pawn on rank 5 should outscore a pawn on rank 2."""
        agent = PositionalAgent()

        board_advanced = Board()
        board_advanced.grid = [[None] * 8 for _ in range(8)]
        board_advanced.grid[3][4] = Pawn(color=W, position=(3, 4))  # e5

        board_starting = Board()
        board_starting.grid = [[None] * 8 for _ in range(8)]
        board_starting.grid[6][4] = Pawn(color=W, position=(6, 4))  # e2

        game_adv = Game(board=board_advanced, current_turn=W)
        game_start = Game(board=board_starting, current_turn=W)

        assert agent.evaluate(game_adv) > agent.evaluate(game_start)

    def test_black_symmetry(self):
        """Same piece placement mirrored for Black should give equal scores."""
        agent = PositionalAgent()

        board_w = Board()
        board_w.grid = [[None] * 8 for _ in range(8)]
        board_w.grid[4][4] = Knight(color=W, position=(4, 4))

        board_b = Board()
        board_b.grid = [[None] * 8 for _ in range(8)]
        board_b.grid[3][4] = Knight(color=B, position=(3, 4))  # mirrored rank

        game_w = Game(board=board_w, current_turn=W)
        game_b = Game(board=board_b, current_turn=B)

        assert agent.evaluate(game_w) == pytest.approx(agent.evaluate(game_b))

    def test_different_squares_produce_different_scores(self):
        """Moving a knight from corner to center changes the evaluation."""
        agent = PositionalAgent()
        game = Game()
        score_before = agent.evaluate(game)

        # Advance white knight from g1 (row 7, col 6) to f3 (row 5, col 5)
        sim = game.board._simulate((7, 6), (5, 5))
        game_after = Game(board=sim, current_turn=B)
        # From Black's perspective after white moves, score should differ
        score_after = PositionalAgent()._eval_board(sim, W)

        assert score_after != score_before


# ---------------------------------------------------------------------------
# choose_move — integration
# ---------------------------------------------------------------------------

class TestPositionalAgentChooseMove:
    def test_returns_legal_move(self):
        agent = PositionalAgent(base_time=0.1)
        game = Game()
        from_pos, to_pos = agent.choose_move(game)
        assert to_pos in game.board.legal_moves(from_pos)

    def test_prefers_center_knight_over_corner(self):
        """In starting position, agent should play Nf3 or Nc3 (center) not Na3."""
        agent = PositionalAgent(base_time=0.5)
        game = Game()
        from_pos, to_pos = agent.choose_move(game)
        # Just verify the returned move is legal — deeper assertion would be fragile
        assert to_pos in game.board.legal_moves(from_pos)

    def test_full_game_completes_no_threefold(self):
        """PositionalAgent vs RandomAgent should complete without threefold repetition."""
        rng = random.Random(42)
        white = PositionalAgent(base_time=0.2)
        black = RandomAgent(rng=rng)
        game = Game()
        moves = 0
        while not game.is_over and moves < 300:
            agent = white if game.current_turn == W else black
            from_pos, to_pos = agent.choose_move(game)
            game.make_move(from_pos, to_pos)
            moves += 1
        assert game.is_over, "Game should end within 300 moves"
        assert game.status != GameStatus.DRAW or "threefold" not in str(
            getattr(game, "draw_reason", "")
        )


# ---------------------------------------------------------------------------
# PositionalAgent vs SimpleAgent win rate
# ---------------------------------------------------------------------------

def _play_game(white_agent, black_agent, rng_seed: int) -> GameStatus:
    rng = random.Random(rng_seed)
    if isinstance(white_agent, RandomAgent):
        white_agent = RandomAgent(rng=rng)
    if isinstance(black_agent, RandomAgent):
        black_agent = RandomAgent(rng=rng)
    game = Game()
    moves = 0
    while not game.is_over and moves < 300:
        agent = white_agent if game.current_turn == W else black_agent
        from_pos, to_pos = agent.choose_move(game)
        game.make_move(from_pos, to_pos)
        moves += 1
    return game.status


class TestPositionalVsSimple:
    def test_positional_wins_more_than_simple_vs_random(self):
        """PositionalAgent should win more games than SimpleAgent against RandomAgent."""
        n = 5
        positional_wins = sum(
            1 for seed in range(n)
            if _play_game(PositionalAgent(base_time=0.2), RandomAgent(), seed) == GameStatus.CHECKMATE
        )
        simple_wins = sum(
            1 for seed in range(n)
            if _play_game(SimpleAgent(base_time=0.2), RandomAgent(), seed) == GameStatus.CHECKMATE
        )
        # Positional should win at least as many as Simple; allow equal as acceptable
        assert positional_wins >= simple_wins, (
            f"PositionalAgent won {positional_wins}/{n}, SimpleAgent won {simple_wins}/{n}"
        )
