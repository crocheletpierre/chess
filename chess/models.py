
ROWS = range(1, 9)
COLUMNS = "abcdefgh"

class ChessTuple(tuple):
    def __add__(self, other):
        if len(self)!=len(other):
            raise RuntimeError(f"Cannot add two tuples of different sizes: {self} and {other}")
        return tuple(map(lambda x,y: x+y, self, other))
    
    def __mul__(self, other):
        if isinstance(other, float) or isinstance(other, int):
            return tuple(map(lambda x: x*other, self))