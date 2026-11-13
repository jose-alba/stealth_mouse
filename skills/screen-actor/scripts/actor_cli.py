#!/usr/bin/env python3
"""
Screen Actor CLI: The agent's physical motor execution system.
Performs human-like mouse movements, clicks, drags, scrolls, keystrokes,
and authentic stealth typing using stealth_mouse physiological kinematics.
Supports instant auto-capture (--capture) to halve agent execution turns.
"""

import sys
import time
import json
import random
import argparse
from pathlib import Path

# Add directories containing stealth_mouse_common to sys.path (local skills root first)
script_dir = Path(__file__).resolve().parent
skills_root = script_dir.parent.parent

if str(skills_root) in sys.path:
    sys.path.remove(str(skills_root))
sys.path.insert(0, str(skills_root))

for p in [Path.home() / ".gemini" / "config" / "skills", Path.home() / ".claude" / "skills"]:
    if p.exists() and str(p) not in sys.path:
        sys.path.append(str(p))

import stealth_mouse_common as smc


def execute_stealth_type(text: str) -> dict:
    """
    Types text with authentic human neuromuscular kinematics:
    - Biomechanical dwell times (time key is held down)
    - Digraph pacing (letter-to-letter intervals)
    - Inter-word cognitive pauses (longer dwell at spaces/punctuation)
    """
    from pynput.keyboard import Controller
    keyboard = Controller()
    smc.ensure_desktop_access()

    t0 = time.perf_counter()

    for i, ch in enumerate(text):
        # Human key dwell time (time key is physically held down)
        dwell_time = random.uniform(0.035, 0.085)
        keyboard.press(ch)
        time.sleep(dwell_time)
        keyboard.release(ch)

        # Dynamic inter-key interval
        if ch == " ":
            # Word cognitive transition pause
            inter_key_delay = random.uniform(0.120, 0.240)
        elif ch in (".", ",", "?", "!", "-", "_", ":", "/"):
            # Symbol reach pause
            inter_key_delay = random.uniform(0.090, 0.180)
        else:
            # Standard physiological keystroke interval
            inter_key_delay = random.uniform(0.040, 0.095)

        time.sleep(inter_key_delay)

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    return {
        "status": "success",
        "action": "stealth_type",
        "text": text,
        "length": len(text),
        "elapsed_ms": elapsed_ms,
    }


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
        time.sleep(0.06)
        keyboard.release(regular_key)

    # Release modifiers in reverse
    for mod in reversed(modifiers):
        time.sleep(0.03)
        keyboard.release(mod)

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    return {"status": "success", "action": "key", "combo": keys_str, "elapsed_ms": elapsed_ms}


def maybe_auto_capture(result: dict, auto_capture: bool, delay_s: float = 0.4) -> dict:
    """
    If --capture flag was provided, sleeps briefly to let the UI settle
    and appends full screenshot metadata to the response.
    """
    if auto_capture:
        time.sleep(delay_s)
        cap = smc.capture_screen()
        result["screenshot"] = {
            "path": cap["path"],
            "width": cap["width"],
            "height": cap["height"],
            "cursor_pos": cap["cursor_pos"],
            "timestamp": cap["timestamp"],
        }
    return result


def main():
    parser = argparse.ArgumentParser(description="Screen Actor CLI (Kinematic Mouse & Keyboard)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Move
    move_parser = subparsers.add_parser("move", help="Move mouse cursor to (x, y)")
    move_parser.add_argument("x", type=float, help="Target X coordinate")
    move_parser.add_argument("y", type=float, help="Target Y coordinate")
    move_parser.add_argument("--capture", action="store_true", help="Auto-capture screenshot after movement")

    # Click
    click_parser = subparsers.add_parser("click", help="Move and click at (x, y)")
    click_parser.add_argument("x", type=float, help="Target X coordinate")
    click_parser.add_argument("y", type=float, help="Target Y coordinate")
    click_parser.add_argument("--button", choices=["left", "right", "middle"], default="left", help="Mouse button")
    click_parser.add_argument("--capture", action="store_true", help="Auto-capture screenshot after click")

    # Scroll
    scroll_parser = subparsers.add_parser("scroll", help="Scroll vertically")
    scroll_parser.add_argument("delta_y", type=float, help="Pixels to scroll (+down, -up)")
    scroll_parser.add_argument("--capture", action="store_true", help="Auto-capture screenshot after scrolling")

    # Drag
    drag_parser = subparsers.add_parser("drag", help="Drag and drop")
    drag_parser.add_argument("target_x", type=float, help="Destination X")
    drag_parser.add_argument("target_y", type=float, help="Destination Y")
    drag_parser.add_argument("--start_x", type=float, default=None, help="Start X (default: current pos)")
    drag_parser.add_argument("--start_y", type=float, default=None, help="Start Y (default: current pos)")
    drag_parser.add_argument("--button", choices=["left", "right"], default="left", help="Mouse button to hold")
    drag_parser.add_argument("--capture", action="store_true", help="Auto-capture screenshot after drag")

    # Type (Human Stealth Typing)
    type_parser = subparsers.add_parser("type", help="Type string text with human stealth kinematics")
    type_parser.add_argument("text", type=str, help="Text to type")
    type_parser.add_argument("--capture", action="store_true", help="Auto-capture screenshot after typing")

    # Key
    key_parser = subparsers.add_parser("key", help="Press key or key combo (e.g. enter, ctrl+c)")
    key_parser.add_argument("combo", type=str, help="Key combination")
    key_parser.add_argument("--capture", action="store_true", help="Auto-capture screenshot after keypress")

    args = parser.parse_args()

    try:
        if args.command == "move":
            res = smc.move(args.x, args.y)
            res = maybe_auto_capture(res, args.capture)
            print(json.dumps(res, indent=2))
        elif args.command == "click":
            res = smc.click(args.x, args.y, button=args.button)
            res = maybe_auto_capture(res, args.capture)
            print(json.dumps(res, indent=2))
        elif args.command == "scroll":
            res = smc.scroll(args.delta_y)
            res = maybe_auto_capture(res, args.capture)
            print(json.dumps(res, indent=2))
        elif args.command == "drag":
            res = smc.drag(args.target_x, args.target_y, start_x=args.start_x, start_y=args.start_y, button=args.button)
            res = maybe_auto_capture(res, args.capture)
            print(json.dumps(res, indent=2))
        elif args.command == "type":
            res = execute_stealth_type(args.text)
            res = maybe_auto_capture(res, args.capture)
            print(json.dumps(res, indent=2))
        elif args.command == "key":
            res = execute_keystroke(args.combo)
            res = maybe_auto_capture(res, args.capture)
            print(json.dumps(res, indent=2))
    except Exception as e:
        err_res = {"status": "error", "message": str(e)}
        print(json.dumps(err_res, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
