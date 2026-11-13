"""
stealth_mouse_common: Shared Core for Antigravity & AI Agent Skills
Provides desktop session guarantees, trajectory path resolution, kinematics, and screen sensing.
"""

from .desktop import ensure_desktop_access, get_display_info
from .paths import find_data_dir
from .vision import capture_screen
from .engine import get_player, move, click, scroll, drag

__all__ = [
    "ensure_desktop_access",
    "get_display_info",
    "find_data_dir",
    "capture_screen",
    "get_player",
    "move",
    "click",
    "scroll",
    "drag",
]

