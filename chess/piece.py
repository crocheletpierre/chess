import abc
from chess.models import ChessTuple
from typing import Any


class Piece(abc.ABC):
    position: ChessTuple[int, int]
    name: str = ""
    _moves: int = 0
    _color: str
    _forward: ChessTuple[int, int]

    def __init__(self, color, position):
        self.color = color
        self.position = position
        if color=="White":
            self._forward = ChessTuple((-1, 0))
        else:
            self._forward = ChessTuple((1, 0))

    #@abc.abstractmethod
    def fetch_moves(self, board: Any) -> set[(ChessTuple[int, int], str)]:
        """
        Returns all possible moves that this piece can make
        """
        return set()

    @property
    def forward(self) -> ChessTuple[int, int]:
        """
        Defines what is forward for that piece
        """
        return self._forward
    
    @property
    def color(self):
        """
        Returns the color of the piece
        """
        return self._color
    
    @color.setter
    def color(self, value):
        if value not in ["White", "Black"]:
            return ValueError("In Chess, pieces can only be White or Black")
        self._color = value
    
    def __str__(self):
        return self.name[0]