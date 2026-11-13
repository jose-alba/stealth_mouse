"""
stealth_mouse_common: Screen Vision and Capture
Provides robust desktop screenshot capture, cropping, and coordinate querying.
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageGrab

from .desktop import ensure_desktop_access, get_display_info


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
    except Exception as e:
        # Retry with default bbox
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

