"""Tests for the Agent framework and RandomAgent."""

from __future__ import annotations

import random

import pytest

from chess.agents import Agent, RandomAgent
from chess.agents.agent import Agent as AgentBase
from chess.board import Board
from chess.game import Game, GameStatus
from chess.pieces import Color, King, Queen
from chess.pieces.piece import Position

W = Color.WHITE
B = Color.BLACK


# ---------------------------------------------------------------------------
# Agent abstract interface
# ---------------------------------------------------------------------------

class TestAgentInterface:
    def test_cannot_instantiate_abstract_agent(self):
        with pytest.raises(TypeError):
            AgentBase()  # type: ignore[abstract]

    def test_concrete_must_implement_choose_move(self):
        class NoChooseMove(Agent):
            @property
            def name(self) -> str:
                return "Broken"
            # missing choose_move

        with pytest.raises(TypeError):
            NoChooseMove()  # type: ignore[abstract]

    def test_concrete_must_implement_name(self):
        class NoName(Agent):
            def choose_move(self, game: Game) -> tuple[Position, Position]:
                return game.board.all_legal_moves(game.current_turn)[0]
            # missing name

        with pytest.raises(TypeError):
            NoName()  # type: ignore[abstract]

    def test_lifecycle_hooks_are_no_ops_by_default(self):
        class MinimalAgent(Agent):
            @property
            def name(self) -> str:
                return "Minimal"
            def choose_move(self, game: Game) -> tuple[Position, Position]:
                return game.board.all_legal_moves(game.current_turn)[0]

        agent = MinimalAgent()
        game = Game()
        # Should not raise
        agent.on_game_start(game)
        agent.on_move_made(game, (6, 4), (4, 4))

    def test_lifecycle_hooks_called_with_correct_args(self):
        received: list = []

        class TrackingAgent(Agent):
            @property
            def name(self) -> str:
                return "Tracker"
            def choose_move(self, game: Game) -> tuple[Position, Position]:
                return game.board.all_legal_moves(game.current_turn)[0]
            def on_game_start(self, game: Game) -> None:
                received.append(("start", type(game).__name__))
            def on_move_made(self, game: Game, from_pos: Position, to_pos: Position) -> None:
                received.append(("move", from_pos, to_pos))

        agent = TrackingAgent()
        game = Game()
        agent.on_game_start(game)
        agent.on_move_made(game, (6, 4), (4, 4))

        assert received[0] == ("start", "Game")
        assert received[1] == ("move", (6, 4), (4, 4))


# ---------------------------------------------------------------------------
# RandomAgent
# ---------------------------------------------------------------------------

class TestRandomAgent:
    def test_name(self):
        assert RandomAgent().name == "Random"

    def test_returns_legal_move(self):
        game = Game()
        agent = RandomAgent()
        from_pos, to_pos = agent.choose_move(game)
        assert to_pos in game.board.legal_moves(from_pos)

    def test_returns_legal_move_for_black(self):
        game = Game()
        game.make_move((6, 4), (4, 4))  # advance to black's turn
        agent = RandomAgent()
        from_pos, to_pos = agent.choose_move(game)
        assert game.board.piece_at(from_pos).color == B  # type: ignore[union-attr]
        assert to_pos in game.board.legal_moves(from_pos)

    def test_deterministic_with_seed(self):
        game = Game()
        move_a = RandomAgent(rng=random.Random(0)).choose_move(game)
        move_b = RandomAgent(rng=random.Random(0)).choose_move(game)
        assert move_a == move_b

    def test_different_seeds_may_differ(self):
        # With 20 legal moves at the start, two different seeds very likely differ
        results = {
            RandomAgent(rng=random.Random(s)).choose_move(Game())
            for s in range(10)
        }
        assert len(results) > 1

    def test_raises_when_no_legal_moves(self):
        # Build a position where the current player has no moves (stalemate)
        board = Board()
        board.grid[0][0] = King(color=B, position=(0, 0))
        board.grid[1][2] = Queen(color=W, position=(1, 2))
        board.grid[2][1] = King(color=W, position=(2, 1))
        game = Game(board=board, current_turn=B)
        agent = RandomAgent()
        with pytest.raises(RuntimeError, match="no legal moves"):
            agent.choose_move(game)

    def test_full_game_completes(self):
        rng = random.Random(1)
        white = RandomAgent(rng=rng)
        black = RandomAgent(rng=rng)
        game = Game()
        white.on_game_start(game)
        black.on_game_start(game)
        moves = 0
        while not game.is_over and moves < 600:
            agent = white if game.current_turn == W else black
            from_pos, to_pos = agent.choose_move(game)
            game.make_move(from_pos, to_pos)
            white.on_move_made(game, from_pos, to_pos)
            black.on_move_made(game, from_pos, to_pos)
            moves += 1
        assert game.is_over, "Game should end within 600 moves"

    def test_all_moves_returned_are_legal_over_many_turns(self):
        rng = random.Random(7)
        agent = RandomAgent(rng=rng)
        game = Game()
        for _ in range(30):
            if game.is_over:
                break
            from_pos, to_pos = agent.choose_move(game)
            legal = game.board.legal_moves(from_pos)
            assert to_pos in legal
            game.make_move(from_pos, to_pos)
