"""
Main entrypoint for stealth_mouse.

Super-simplified API:
    move(x, y)                    -> natural human movement to target
    click(x, y, button="left")    -> movement + pre-click hesitation + click + settle
    scroll(delta_y)               -> natural scrolling with bursts, friction, and rebound
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
    Moves the mouse to (x, y), hesitates naturally, and performs a click.
    Args:
        x: Target X coordinate
        y: Target Y coordinate
        button: 'left' or 'right' (default: 'left')
    Usage:
        click(800, 450)
        click(800, 450, button="right")
    """
    _get_player().click(float(x), float(y), button=button)


def scroll(delta_y: float) -> None:
    """
    Scrolls vertically with human biological physics (flick bursts, friction decay, rebound).
    Args:
        delta_y: Pixels to scroll. Positive: scroll down. Negative: scroll up.
    Usage:
        scroll(600)   # Scroll down 600px
        scroll(-300)  # Scroll up 300px
    """
    _get_player().scroll(float(delta_y))


def drag(
    target_x: float,
    target_y: float,
    start_x: Optional[float] = None,
    start_y: Optional[float] = None,
    button: str = "left",
) -> None:
    """
    Performs realistic human drag-and-drop from current position (or start_x, start_y)
    to (target_x, target_y) with breakaway friction delay, physiological kinematics,
    and release alignment hesitation.
    Args:
        target_x: Target X coordinate
        target_y: Target Y coordinate
        start_x: Optional origin X coordinate (moves here first if provided)
        start_y: Optional origin Y coordinate
        button: 'left' or 'right' (default: 'left')
    Usage:
        drag(800, 450)
        drag(800, 450, start_x=200, start_y=450)
    """
    _get_player().drag(float(target_x), float(target_y), start_x=start_x, start_y=start_y, button=button)


def main() -> None:
    """CLI usage: python main.py [x] [y] | click | scroll | drag"""
    args = sys.argv[1:]
    if not args or "-h" in args or "--help" in args:
        print("Usage:")
        print("  python main.py <x> <y>                          # Move to coordinates")
        print("  python main.py click <x> <y> [button]           # Move and click ('left' or 'right')")
        print("  python main.py scroll <delta_y>                 # Scroll down (+) or up (-)")
        print("  python main.py drag <target_x> <target_y>       # Drag from current pos to target")
        print("  python main.py drag <x1> <y1> <x2> <y2>         # Drag from (x1, y1) to (x2, y2)")
        print("\nOr in your Python code:")
        print("  from main import move, click, scroll, drag")
        print("  move(800, 500)")
        print("  click(800, 500, button='left')")
        print("  scroll(600)")
        print("  drag(550, 300, start_x=200, start_y=300)")
        return

    cmd = args[0].lower()
    if cmd == "click":
        if len(args) < 3:
            print("Error: Provide X and Y coordinates. Example: python main.py click 500 300 [left|right]")
            return
        x, y = float(args[1]), float(args[2])
        btn = args[3].lower() if len(args) > 3 else "left"
        print(f"Moving and clicking ({btn}) at ({x}, {y})...")
        click(x, y, button=btn)
    elif cmd == "scroll":
        if len(args) < 2:
            print("Error: Provide delta_y value. Example: python main.py scroll 500")
            return
        dy = float(args[1])
        direction = "down" if dy > 0 else "up"
        print(f"Scrolling {direction} ({dy}px)...")
        scroll(dy)
    elif cmd == "drag":
        if len(args) == 3:
            # drag <target_x> <target_y>
            tx, ty = float(args[1]), float(args[2])
            print(f"Dragging naturally to ({tx}, {ty})...")
            drag(tx, ty)
        elif len(args) >= 5:
            # drag <start_x> <start_y> <target_x> <target_y>
            sx, sy, tx, ty = float(args[1]), float(args[2]), float(args[3]), float(args[4])
            print(f"Dragging naturally from ({sx}, {sy}) to ({tx}, {ty})...")
            drag(tx, ty, start_x=sx, start_y=sy)
        else:
            print("Error: Provide target or start + target coordinates. Example: python main.py drag 200 300 500 300")
            return
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
