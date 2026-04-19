"""Entry point for a terminal chess game.

Usage:
    python -m chess.main                             # human vs human
    python -m chess.main --white PATH_TO_AGENT.py   # agent plays white
    python -m chess.main --black PATH_TO_AGENT.py   # agent plays black
    python -m chess.main --white A.py --black B.py  # agent vs agent

The agent file must define exactly one concrete Agent subclass.
"""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import sys
import time
from pathlib import Path

from .agents.agent import Agent
from .game import Game
from .pieces import Color


def _load_agent(path_str: str) -> Agent:
    """Import a Python file and return an instance of the first Agent subclass found.

    If the file lives under a directory on sys.path, it is imported as part of
    its package (preserving relative imports). Otherwise it is loaded as a
    standalone module — external agents must use absolute imports in that case.
    """
    path = Path(path_str).resolve()
    if not path.exists():
        print(f"Error: agent file not found: {path}", file=sys.stderr)
        sys.exit(1)

    # Sort by base-path length descending so the most specific sys.path entry wins.
    # This avoids treating e.g. '' (project root) as more specific than 'src/'.
    sorted_paths = sorted(
        (Path(e).resolve() for e in sys.path if e != ""),
        key=lambda p: len(p.parts),
        reverse=True,
    )
    module = None
    for base in sorted_paths:
        try:
            rel = path.relative_to(base)
        except ValueError:
            continue
        module_name = ".".join(rel.with_suffix("").parts)
        try:
            module = importlib.import_module(module_name)
            break  # only break on success; try next entry otherwise
        except ImportError:
            pass

    if module is None:
        # Standalone load — external agent, no relative imports
        spec = importlib.util.spec_from_file_location("_agent_module", path)
        if spec is None or spec.loader is None:
            print(f"Error: could not load module from {path}", file=sys.stderr)
            sys.exit(1)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]

    candidates = [
        cls for _, cls in inspect.getmembers(module, inspect.isclass)
        if issubclass(cls, Agent) and cls is not Agent and not inspect.isabstract(cls)
    ]

    if not candidates:
        print(f"Error: no concrete Agent subclass found in {path}", file=sys.stderr)
        sys.exit(1)
    if len(candidates) > 1:
        names = ", ".join(c.__name__ for c in candidates)
        print(f"Error: multiple Agent subclasses found in {path}: {names}", file=sys.stderr)
        sys.exit(1)

    return candidates[0]()


def _agent_for(color: Color, white_agent: Agent | None, black_agent: Agent | None) -> Agent | None:
    return white_agent if color == Color.WHITE else black_agent


def _print_move(record, agent_name: str | None = None) -> None:
    suffix = "#" if record.is_checkmate else "+" if record.is_check else ""
    cap = f" captures {record.captured_symbol}" if record.captured_symbol else ""
    who = f"[{agent_name}] " if agent_name else ""
    print(f"\n  {who}{record.piece_symbol} {record.notation}{cap}{suffix}\n")


def _print_result(game: Game) -> None:
    print(f"\n{'=' * 30}")
    if game.winner:
        print(f"  {game.winner.value.capitalize()} wins!")
    elif game.draw_reason:
        print(f"  Draw — {game.draw_reason.value}.")
    else:
        print("  Draw!")
    print(f"{'=' * 30}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Play chess in the terminal.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m chess.main\n"
            "  python -m chess.main --white src/chess/agents/random_agent.py\n"
            "  python -m chess.main --white agents/my_agent.py --black agents/my_agent.py"
        ),
    )
    parser.add_argument("--white", metavar="AGENT_FILE", help="Python file containing an Agent subclass to play white")
    parser.add_argument("--black", metavar="AGENT_FILE", help="Python file containing an Agent subclass to play black")
    args = parser.parse_args()

    white_agent = _load_agent(args.white) if args.white else None
    black_agent = _load_agent(args.black) if args.black else None

    is_hvh = white_agent is None and black_agent is None

    print("=== Chess ===")
    if white_agent:
        print(f"  White: {white_agent.name}")
    else:
        print("  White: Human")
    if black_agent:
        print(f"  Black: {black_agent.name}")
    else:
        print("  Black: Human")
    if is_hvh:
        print("\nEnter moves as coordinate notation (e.g. e2e4, e7-e5).")
        print("Commands: quit, history, help")
    print()

    game = Game()
    for agent in (white_agent, black_agent):
        if agent is not None:
            agent.on_game_start(game)

    print(game.render())

    while not game.is_over:
        agent = _agent_for(game.current_turn, white_agent, black_agent)

        if agent is not None:
            print(f"\n  {game.current_turn.value.capitalize()} [{agent.name}] is thinking...")
            time.sleep(0.4)
            from_pos, to_pos = agent.choose_move(game)
            record = game.make_move(from_pos, to_pos)
            _print_move(record, agent.name)
            for a in (white_agent, black_agent):
                if a is not None:
                    a.on_move_made(game, from_pos, to_pos)
            print(game.render())
            continue

        # Human turn
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
            print("  Moves: coordinate notation, e.g. 'e2e4' or 'e2-e4'.")
            print("  Commands: quit, history")
            continue

        if raw.lower() in ("history", "hist"):
            if not game.history:
                print("  No moves yet.")
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

        _print_move(record)
        for a in (white_agent, black_agent):
            if a is not None:
                a.on_move_made(game, from_pos, to_pos)
        print(game.render())

    _print_result(game)


if __name__ == "__main__":
    main()
