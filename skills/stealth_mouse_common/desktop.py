"""
stealth_mouse_common: Desktop and Input Desktop Manager
Ensures process thread is attached to the interactive user desktop session in Windows,
preventing ERROR_ACCESS_DENIED (5) in background or agent subshells.
"""

import sys
import ctypes
from typing import Dict, Any, Tuple


def ensure_desktop_access() -> bool:
    """
    Attaches the current thread to the active user desktop station on Windows.
    Returns True if successfully attached or if running on non-Windows.
    """
    if sys.platform != "win32":
        return True

    try:
        user32 = ctypes.windll.user32
        # DESKTOP_ALL_ACCESS = 0x01FF
        hdesk = user32.OpenInputDesktop(0, False, 0x01FF)
        if hdesk:
            res = user32.SetThreadDesktop(hdesk)
            return bool(res)
    except Exception:
        pass
    return False


def get_display_info() -> Dict[str, Any]:
    """
    Retrieves screen dimensions, DPI awareness, and cursor coordinates.
    """
    ensure_desktop_access()

    info: Dict[str, Any] = {
        "platform": sys.platform,
        "width": 1920,
        "height": 1080,
        "cursor_x": 0,
        "cursor_y": 0,
        "dpi_aware": False,
    }

    if sys.platform == "win32":
        user32 = ctypes.windll.user32
        
        # Set DPI awareness to get true physical pixels
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2) # Per monitor DPI aware
            info["dpi_aware"] = True
        except Exception:
            try:
                user32.SetProcessDPIAware()
                info["dpi_aware"] = True
            except Exception:
                pass

        # Primary screen metrics
        info["width"] = int(user32.GetSystemMetrics(0))   # SM_CXSCREEN
        info["height"] = int(user32.GetSystemMetrics(1))  # SM_CYSCREEN

        # Virtual screen metrics (multi-monitor span)
        info["virtual_x"] = int(user32.GetSystemMetrics(76))      # SM_XVIRTUALSCREEN
        info["virtual_y"] = int(user32.GetSystemMetrics(77))      # SM_YVIRTUALSCREEN
        info["virtual_width"] = int(user32.GetSystemMetrics(78))  # SM_CXVIRTUALSCREEN
        info["virtual_height"] = int(user32.GetSystemMetrics(79)) # SM_CYVIRTUALSCREEN

        # Cursor position
        from ctypes import wintypes
        class POINT(ctypes.Structure):
            _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]
        pt = POINT()
        if user32.GetCursorPos(ctypes.byref(pt)):
            info["cursor_x"] = int(pt.x)
            info["cursor_y"] = int(pt.y)

    return info

