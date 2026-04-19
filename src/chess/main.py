"""Entry point for a terminal chess game between two human players."""

from __future__ import annotations

import sys

from .game import Game


def main() -> None:
    game = Game()

    print("Chess — enter moves as coordinate notation (e.g. e2e4, e7-e5)")
    print("Type 'quit' or 'q' to exit.\n")
    print(game.render())

    while not game.is_over:
        prompt = f"\n{game.current_turn.value.capitalize()}> "
        try:
            raw = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGame aborted.")
            sys.exit(0)

        if raw.lower() in ("q", "quit", "exit"):
            print("Game aborted.")
            sys.exit(0)

        if raw.lower() in ("h", "help"):
            print("Enter moves as coordinate notation, e.g. 'e2e4' or 'e2-e4'.")
            print("Commands: quit, history")
            continue

        if raw.lower() in ("history", "hist"):
            if not game.history:
                print("No moves yet.")
            else:
                for i, rec in enumerate(game.history, 1):
                    suffix = "#" if rec.is_checkmate else "+" if rec.is_check else ""
                    cap = f" x{rec.captured_symbol}" if rec.captured_symbol else ""
                    print(f"  {i:3}. {rec.piece_symbol} {rec.notation}{cap}{suffix}")
            continue

        try:
            from_pos, to_pos = Game.parse_move(raw)
            record = game.make_move(from_pos, to_pos)
        except ValueError as exc:
            print(f"  Error: {exc}")
            continue

        suffix = "#" if record.is_checkmate else "+" if record.is_check else ""
        cap = f" captures {record.captured_symbol}" if record.captured_symbol else ""
        print(f"\n  {record.piece_symbol} {record.notation}{cap}{suffix}\n")
        print(game.render())

    if game.winner:
        print(f"\n{'=' * 30}")
        print(f"  {game.winner.value.capitalize()} wins!")
        print(f"{'=' * 30}")
    else:
        print(f"\n{'=' * 30}")
        print("  Draw!")
        print(f"{'=' * 30}")


if __name__ == "__main__":
    main()
