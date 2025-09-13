from chess.game import Game
import logging

logger = logging.Logger(__name__)

if __name__=="__main__":
    logger.info("Let's play a game of chess")
    game = Game()
    game.play()