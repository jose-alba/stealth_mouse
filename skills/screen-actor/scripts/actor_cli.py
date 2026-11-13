#!/usr/bin/env python3
"""
Screen Actor CLI: The agent's physical motor execution system.
Performs human-like mouse movements, clicks, drags, scrolls, and keystrokes
using stealth_mouse physiological kinematics.
"""

import sys
import time
import json
import argparse
from pathlib import Path

# Add possible paths to stealth_mouse_common
script_dir = Path(__file__).resolve().parent
search_paths = [
    script_dir,
    script_dir / "stealth_mouse_common",
    script_dir.parent.parent,
    script_dir.parent.parent / "stealth_mouse_common",
    Path.home() / ".gemini" / "config" / "skills",
    Path.home() / ".gemini" / "config" / "skills" / "stealth_mouse_common",
    Path.home() / ".claude" / "skills",
    Path.home() / ".claude" / "skills" / "stealth_mouse_common",
]
for p in search_paths:
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    import stealth_mouse_common as smc
except ImportError:
    sys.path.insert(0, str(script_dir.parent.parent))
    import stealth_mouse_common as smc


def execute_keystroke(keys_str: str) -> dict:
    """
    Types characters or executes special key combinations with realistic human delays.
    """
    from pynput.keyboard import Controller, Key
    keyboard = Controller()
    smc.ensure_desktop_access()

    t0 = time.perf_counter()
    key_mapping = {
        "enter": Key.enter,
        "return": Key.enter,
        "esc": Key.esc,
        "escape": Key.esc,
        "tab": Key.tab,
        "space": Key.space,
        "backspace": Key.backspace,
        "delete": Key.delete,
        "up": Key.up,
        "down": Key.down,
        "left": Key.left,
        "right": Key.right,
    }

    combo = [k.strip().lower() for k in keys_str.split("+")]
    modifiers = []
    regular_key = None

    for k in combo:
        if k in ("ctrl", "control"):
            modifiers.append(Key.ctrl)
        elif k in ("alt",):
            modifiers.append(Key.alt)
        elif k in ("shift",):
            modifiers.append(Key.shift)
        elif k in key_mapping:
            regular_key = key_mapping[k]
        else:
            regular_key = k

    # Press modifiers
    for mod in modifiers:
        keyboard.press(mod)
        time.sleep(0.04)

    # Press regular key
    if regular_key is not None:
        keyboard.press(regular_key)
        time.sleep(0.05)
        keyboard.release(regular_key)

    # Release modifiers in reverse
    for mod in reversed(modifiers):
        time.sleep(0.03)
        keyboard.release(mod)

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    return {"status": "success", "action": "key", "combo": keys_str, "elapsed_ms": elapsed_ms}


def execute_type(text: str) -> dict:
    """
    Types a string with natural inter-key intervals (40-90ms).
    """
    from pynput.keyboard import Controller
    import random

    keyboard = Controller()
    smc.ensure_desktop_access()
    t0 = time.perf_counter()

    for ch in text:
        keyboard.type(ch)
        time.sleep(random.uniform(0.035, 0.085))

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    return {"status": "success", "action": "type", "length": len(text), "elapsed_ms": elapsed_ms}


def main():
    parser = argparse.ArgumentParser(description="Screen Actor CLI (Kinematic Mouse & Keyboard)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Move
    move_parser = subparsers.add_parser("move", help="Move mouse cursor to (x, y)")
    move_parser.add_argument("x", type=float, help="Target X coordinate")
    move_parser.add_argument("y", type=float, help="Target Y coordinate")

    # Click
    click_parser = subparsers.add_parser("click", help="Move and click at (x, y)")
    click_parser.add_argument("x", type=float, help="Target X coordinate")
    click_parser.add_argument("y", type=float, help="Target Y coordinate")
    click_parser.add_argument("--button", choices=["left", "right", "middle"], default="left", help="Mouse button")

    # Scroll
    scroll_parser = subparsers.add_parser("scroll", help="Scroll vertically")
    scroll_parser.add_argument("delta_y", type=float, help="Pixels to scroll (+down, -up)")

    # Drag
    drag_parser = subparsers.add_parser("drag", help="Drag and drop")
    drag_parser.add_argument("target_x", type=float, help="Destination X")
    drag_parser.add_argument("target_y", type=float, help="Destination Y")
    drag_parser.add_argument("--start_x", type=float, default=None, help="Start X (default: current pos)")
    drag_parser.add_argument("--start_y", type=float, default=None, help="Start Y (default: current pos)")
    drag_parser.add_argument("--button", choices=["left", "right"], default="left", help="Mouse button to hold")

    # Type
    type_parser = subparsers.add_parser("type", help="Type string text")
    type_parser.add_argument("text", type=str, help="Text to type")

    # Key
    key_parser = subparsers.add_parser("key", help="Press key or key combo (e.g. enter, ctrl+c)")
    key_parser.add_argument("combo", type=str, help="Key combination")

    args = parser.parse_args()

    try:
        if args.command == "move":
            res = smc.move(args.x, args.y)
            print(json.dumps(res, indent=2))
        elif args.command == "click":
            res = smc.click(args.x, args.y, button=args.button)
            print(json.dumps(res, indent=2))
        elif args.command == "scroll":
            res = smc.scroll(args.delta_y)
            print(json.dumps(res, indent=2))
        elif args.command == "drag":
            res = smc.drag(args.target_x, args.target_y, start_x=args.start_x, start_y=args.start_y, button=args.button)
            print(json.dumps(res, indent=2))
        elif args.command == "type":
            res = execute_type(args.text)
            print(json.dumps(res, indent=2))
        elif args.command == "key":
            res = execute_keystroke(args.combo)
            print(json.dumps(res, indent=2))
    except Exception as e:
        err_res = {"status": "error", "message": str(e)}
        print(json.dumps(err_res, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()

