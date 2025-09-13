from pydantic import BaseModel
from chess.board import Board
import logging
from typing import Literal
from chess.piece import Piece
from chess.helpers import __init_board

logger = logging.Logger(__name__)

class Game(BaseModel):
    _score: dict[str, int]
    board: Board
    turn: Literal["White", "Black"]

    def __init__(self):
        base_score = {
            "White": 0,
            "Black": 0
        }
        board = Board()
        Board.model_rebuild()

        super().__init__(
            score=base_score,
            board=board,
            turn="White"
        )

    @property
    def score(self):
        return self._score
    
    @score.getter
    def score(self, value):
        return self._score[value]

    def play(self):
        while True:
            logger.info(f"{self.turn} to play")
            if self.board.game_over():
                winner = self.board.winner
                logger.info(f"{winner} has won the game!")
                break

        #self._update_score()

if __name__=="__main__":
    board = Board()
    board.set_board(__init_board())
    board.show_board()