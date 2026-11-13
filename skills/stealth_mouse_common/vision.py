"""
stealth_mouse_common: Screen Vision and Capture
Provides robust desktop screenshot capture, dynamic quadrant cropping,
and high-visibility target reticle/crosshair previews for LLM verification.
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageGrab, ImageDraw, ImageFont

from .desktop import ensure_desktop_access, get_display_info


def get_default_font(size: int = 18):
    """Retrieves standard Windows/system font or fallback."""
    if sys.platform == "win32":
        windir = os.environ.get("WINDIR", "C:/Windows")
        for font_name in ("segoeuib.ttf", "arialbd.ttf", "segoeui.ttf", "arial.ttf"):
            font_path = Path(windir) / "Fonts" / font_name
            if font_path.exists():
                try:
                    return ImageFont.truetype(str(font_path), size)
                except Exception:
                    pass
    return ImageFont.load_default()


def capture_screen(
    output_path: Optional[str] = None,
    region: Optional[Tuple[int, int, int, int]] = None,
    all_screens: bool = True
) -> Dict[str, Any]:
    """
    Captures a screenshot of the display or a specific region (left, top, right, bottom).
    Returns metadata including file path, dimensions, and timestamp.
    """
    ensure_desktop_access()

    if output_path is None:
        temp_dir = Path(os.environ.get("TEMP", os.environ.get("TMPDIR", "/tmp"))) / "agent_screen_sense"
        temp_dir.mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time() * 1000)
        output_file = temp_dir / f"screen_{timestamp}.png"
    else:
        output_file = Path(output_path).resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)

    # Capture image
    try:
        im = ImageGrab.grab(bbox=region, all_screens=all_screens)
    except Exception:
        im = ImageGrab.grab()
        if region:
            im = im.crop(region)

    im.save(str(output_file), "PNG")
    display_info = get_display_info()

    return {
        "status": "success",
        "path": str(output_file),
        "width": im.width,
        "height": im.height,
        "region": region,
        "cursor_pos": [display_info.get("cursor_x", 0), display_info.get("cursor_y", 0)],
        "timestamp": time.time(),
    }


def aim_crosshair_preview(
    target_x: int,
    target_y: int,
    scale: float = 0.5,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Captures the screen and generates a generous context preview (~1/4 of total screen area,
    default scale=0.5 -> half width and half height) centered around (target_x, target_y).
    Draws a prominent, high-contrast targeting reticle and coordinate badge so the LLM
    can immediately verify accuracy before firing physical clicks.
    """
    ensure_desktop_access()

    # Capture whole screen
    full_img = ImageGrab.grab()
    W, H = full_img.size

    # Clamp target to screen
    tx = max(0, min(W - 1, int(target_x)))
    ty = max(0, min(H - 1, int(target_y)))

    # Calculate dynamic crop dimensions (default 0.5 = 1/4 area of screen)
    crop_w = max(300, min(W, int(W * scale)))
    crop_h = max(200, min(H, int(H * scale)))

    left = max(0, min(W - crop_w, tx - crop_w // 2))
    top = max(0, min(H - crop_h, ty - crop_h // 2))
    right = left + crop_w
    bottom = top + crop_h

    # Crop section
    crop_img = full_img.crop((left, top, right, bottom)).convert("RGBA")
    draw = ImageDraw.Draw(crop_img)

    local_x = tx - left
    local_y = ty - top

    # Reticle styling: Double-layer stroke for 100% contrast on any dark/light background
    # Outer black halo + inner vibrant red/coral
    line_len = 70
    center_radius = 18
    gap = 6

    def draw_thick_line(p1, p2):
        # Black outline (width 5)
        draw.line([p1, p2], fill=(0, 0, 0, 255), width=5)
        # Vibrant red core (width 3)
        draw.line([p1, p2], fill=(255, 40, 40, 255), width=3)

    # 4 Cardinal Crosshair Rays (with central gap to not occlude target element)
    draw_thick_line((local_x, local_y - center_radius - line_len), (local_x, local_y - gap)) # North
    draw_thick_line((local_x, local_y + gap), (local_x, local_y + center_radius + line_len)) # South
    draw_thick_line((local_x - center_radius - line_len, local_y), (local_x - gap, local_y)) # West
    draw_thick_line((local_x + gap, local_y), (local_x + center_radius + line_len, local_y)) # East

    # Outer Targeting Ring (halo + red)
    draw.ellipse(
        (local_x - center_radius, local_y - center_radius, local_x + center_radius, local_y + center_radius),
        outline=(0, 0, 0, 255),
        width=4
    )
    draw.ellipse(
        (local_x - center_radius, local_y - center_radius, local_x + center_radius, local_y + center_radius),
        outline=(255, 40, 40, 255),
        width=2
    )

    # Central micro-dot (exact pixel)
    draw.ellipse(
        (local_x - 2, local_y - 2, local_x + 2, local_y + 2),
        fill=(255, 255, 255, 255),
        outline=(0, 0, 0, 255),
        width=1
    )

    # Coordinate Badge
    badge_text = f"[+] TARGET ({tx}, {ty})"
    font = get_default_font(size=18)
    bbox = font.getbbox(badge_text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    # Badge position: top-right of crosshair if space permits, else top-left
    bx = local_x + center_radius + 14
    if bx + tw + 20 > crop_w:
        bx = local_x - center_radius - tw - 24
    by = max(10, local_y - th // 2 - 14)

    # Badge background pill
    draw.rounded_rectangle(
        (bx - 8, by - 6, bx + tw + 12, by + th + 8),
        radius=6,
        fill=(15, 15, 20, 230),
        outline=(255, 40, 40, 255),
        width=2
    )
    draw.text((bx + 2, by - 2), badge_text, fill=(255, 255, 255, 255), font=font)

    # Save preview image
    if output_path is None:
        temp_dir = Path(os.environ.get("TEMP", os.environ.get("TMPDIR", "/tmp"))) / "agent_screen_sense"
        temp_dir.mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time() * 1000)
        output_file = temp_dir / f"aim_preview_{tx}_{ty}_{timestamp}.png"
    else:
        output_file = Path(output_path).resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)

    crop_img.convert("RGB").save(str(output_file), "PNG")

    return {
        "status": "success",
        "action": "aim_preview",
        "target": [tx, ty],
        "crop_bounds": [left, top, right, bottom],
        "crop_size": [crop_w, crop_h],
        "local_target": [local_x, local_y],
        "preview_image": str(output_file),
    }
