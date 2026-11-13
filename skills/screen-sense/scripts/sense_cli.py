#!/usr/bin/env python3
"""
Screen Sense CLI: The agent's visual sensing tool.
Provides screenshot capture, display resolution, DPI metrics,
cursor tracking, and dynamic quadrant target reticle preview.
"""

import sys
import json
import argparse
from pathlib import Path

# Priority search order: local workspace root first, then global skills
script_dir = Path(__file__).resolve().parent
skills_root = script_dir.parent.parent

# Ensure local skills folder has absolute top priority
if str(skills_root) in sys.path:
    sys.path.remove(str(skills_root))
sys.path.insert(0, str(skills_root))

# Fallbacks for global installation
for p in [Path.home() / ".gemini" / "config" / "skills", Path.home() / ".claude" / "skills"]:
    if p.exists() and str(p) not in sys.path:
        sys.path.append(str(p))

import stealth_mouse_common as smc


def main():
    parser = argparse.ArgumentParser(description="Screen Sense CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: info
    subparsers.add_parser("info", help="Get display dimensions, DPI info, and cursor position")

    # Subcommand: pos
    subparsers.add_parser("pos", help="Get current cursor coordinates")

    # Subcommand: capture
    cap_parser = subparsers.add_parser("capture", help="Capture a screenshot")
    cap_parser.add_argument("--out", type=str, default=None, help="Output image file path (.png)")
    cap_parser.add_argument(
        "--region",
        type=int,
        nargs=4,
        metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"),
        default=None,
        help="Crop region coordinates",
    )

    # Subcommand: aim (dynamic ~1/4 screen preview with large high-contrast crosshair)
    aim_parser = subparsers.add_parser("aim", help="Generate generous context preview (~1/4 screen) with crosshair")
    aim_parser.add_argument("x", type=int, help="Target X coordinate")
    aim_parser.add_argument("y", type=int, help="Target Y coordinate")
    aim_parser.add_argument("--scale", type=float, default=0.5, help="Scale factor of screen width/height (default: 0.5 = 1/4 area)")
    aim_parser.add_argument("--out", type=str, default=None, help="Output image path (.png)")

    args = parser.parse_args()

    try:
        if args.command == "info":
            info = smc.get_display_info()
            print(json.dumps(info, indent=2))

        elif args.command == "pos":
            info = smc.get_display_info()
            pos_data = {
                "cursor_x": info.get("cursor_x", 0),
                "cursor_y": info.get("cursor_y", 0),
                "screen_width": info.get("width", 1920),
                "screen_height": info.get("height", 1080),
            }
            print(json.dumps(pos_data, indent=2))

        elif args.command == "capture":
            region_tuple = tuple(args.region) if args.region else None
            result = smc.capture_screen(output_path=args.out, region=region_tuple)
            print(json.dumps(result, indent=2))

        elif args.command == "aim":
            result = smc.aim_crosshair_preview(
                target_x=args.x,
                target_y=args.y,
                scale=args.scale,
                output_path=args.out
            )
            print(json.dumps(result, indent=2))

    except Exception as e:
        err_res = {"status": "error", "message": str(e)}
        print(json.dumps(err_res, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
