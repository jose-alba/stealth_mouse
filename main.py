"""
Main entrypoint for stealth_mouse.

Super-simplified API: 4 to 6 letters + destination coordinates:
    move(x, y)   -> 4 letters: natural human movement to target
    click(x, y)  -> 5 letters: natural movement + human click
"""

import sys
from typing import Optional
from src.player import StealthMousePlayer

# Global reusable player instance
_player: Optional[StealthMousePlayer] = None


def _get_player() -> StealthMousePlayer:
    global _player
    if _player is None:
        _player = StealthMousePlayer(data_dir="data", top_k=10)
    return _player


def move(x: float, y: float) -> None:
    """
    Moves the mouse from its current position to (x, y) with human kinematics.
    Usage: move(x, y)
    """
    _get_player().move_to(float(x), float(y))


def click(x: float, y: float, button: str = "left") -> None:
    """
    Moves the mouse to (x, y) and performs a click with human dwell time.
    Usage: click(x, y)
    """
    _get_player().click(float(x), float(y), button=button)


def main() -> None:
    """CLI usage: python main.py [x] [y]  or  python main.py click [x] [y]"""
    args = sys.argv[1:]
    if not args or "-h" in args or "--help" in args:
        print("Usage:")
        print("  python main.py <x> <y>          # Move to coordinates")
        print("  python main.py click <x> <y>    # Move and click")
        print("\nOr in your own Python script:")
        print("  from main import move, click")
        print("  move(800, 500)")
        print("  click(800, 500)")
        return

    if args[0] == "click":
        if len(args) < 3:
            print("Error: Provide X and Y coordinates. Example: python main.py click 500 300")
            return
        x, y = float(args[1]), float(args[2])
        print(f"Moving and clicking at ({x}, {y})...")
        click(x, y)
    else:
        if len(args) < 2:
            print("Error: Provide X and Y coordinates. Example: python main.py 500 300")
            return
        x, y = float(args[0]), float(args[1])
        print(f"Moving naturally to ({x}, {y})...")
        move(x, y)

    print("Completed.")


if __name__ == "__main__":
    main()
