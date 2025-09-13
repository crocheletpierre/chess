from pydantic import BaseModel, ConfigDict
from typing import Optional, Literal
from termcolor import colored
from chess.piece import Piece

class Board(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    _TOGGLE: dict[str, str] = {"Black": "White", "White": "Black"}
    state: dict[str, list[Piece | None]]
    winner: Optional[str]
    last_played: dict[str, tuple[str, str]]
    history: list[dict[str, list[Piece | None]]]

    def __init__(self):
        state = {}
        super().__init__(
            state=state,
            winner=None,
            last_played = {"Black": ("", "")},
            history = [state]
        )


    def __get_item__(self, key):
        """
        Get the piece of the board at `key` where `key` respects the chess notation
        ex: at the start of the game `a1` is a white rook, `e8` is the black king
        """
        if not isinstance(key, str) or len(key)!=2:
            raise ValueError(f"cannot get value of state at {key}")
        return self.state[key[0]][int(key[1])-1]
    

    def __set_item__(self, key, new_value):
        """
        Sets the piece of the board at `key` where `key` respects the chess notation
        """
        if not isinstance(key, str) or len(key)!=2:
            raise ValueError(f"cannot get value of state at {key}")
        self.state[key[0]][int(key[1])-1] = new_value
        self.last_played = self._TOGGLE[self.last_played]


    def set_board(self, state: dict[str, list[Piece | None]]):
        self.state=state

    def show_board(self, view: Literal["White", "Black"] = "White"):
        if view not in ["White", "Black"]:
            raise ValueError(f"View can only be Black or White, not {view}")
        order = range(8, 0, -1) if view == "White" else range(1, 9)
        inverted_state: dict[int, list[Piece | None]] = {x: [] for x in range(1, 9)}
        for _,v in self.state.items():
            for i, piece in enumerate(v):
                inverted_state[i+1].append(piece)
        for row in order:
            print(colored(f"{row}| ", "yellow"), end="")
            for piece in inverted_state[row]:
                if piece:
                    print(colored(f" {piece}", piece.color.lower()), end="")
                else:
                    print(colored(" _", "dark_grey"), end="")
            print()
        print(colored("    ---------------", "yellow"))
        print(colored("    A B C D E F G H", "yellow"))
        print()


    def game_over(self):
        return self.last_played