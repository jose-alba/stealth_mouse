"""
stealth_mouse_common: Core Kinematic Action Engine
Wraps StealthMousePlayer with desktop session guarantees, path resolution, and JSON responses.
"""

import sys
import time
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

from .desktop import ensure_desktop_access, get_display_info
from .paths import find_data_dir
from .core.player import StealthMousePlayer

_shared_player: Optional[StealthMousePlayer] = None


def get_player() -> StealthMousePlayer:
    """
    Returns or lazily instantiates the global StealthMousePlayer instance
    using the auto-resolved trajectory database path.
    """
    global _shared_player
    ensure_desktop_access()

    if _shared_player is None:
        data_path = find_data_dir()
        _shared_player = StealthMousePlayer(data_dir=str(data_path), top_k=10)
    return _shared_player


def move(x: float, y: float) -> Dict[str, Any]:
    """
    Moves cursor from current position to (x, y) with human biological kinematics.
    """
    ensure_desktop_access()
    t0 = time.perf_counter()
    p = get_player()
    start_pos = p.get_current_position()
    p.move_to(float(x), float(y))
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    final_pos = p.get_current_position()

    return {
        "status": "success",
        "action": "move",
        "from": [float(start_pos[0]), float(start_pos[1])],
        "target": [float(x), float(y)],
        "final_pos": [float(final_pos[0]), float(final_pos[1])],
        "elapsed_ms": elapsed_ms,
    }


def click(x: float, y: float, button: str = "left") -> Dict[str, Any]:
    """
    Moves cursor to (x, y), performs natural pre-click hesitation, and clicks.
    """
    ensure_desktop_access()
    t0 = time.perf_counter()
    p = get_player()
    start_pos = p.get_current_position()
    p.click(float(x), float(y), button=button)
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    final_pos = p.get_current_position()

    return {
        "status": "success",
        "action": "click",
        "button": button,
        "from": [float(start_pos[0]), float(start_pos[1])],
        "target": [float(x), float(y)],
        "final_pos": [float(final_pos[0]), float(final_pos[1])],
        "elapsed_ms": elapsed_ms,
    }


def scroll(delta_y: float) -> Dict[str, Any]:
    """
    Scrolls vertically with human multi-flick bursts and friction decay.
    """
    ensure_desktop_access()
    t0 = time.perf_counter()
    p = get_player()
    p.scroll(float(delta_y))
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

    return {
        "status": "success",
        "action": "scroll",
        "delta_y": float(delta_y),
        "elapsed_ms": elapsed_ms,
    }


def drag(
    target_x: float,
    target_y: float,
    start_x: Optional[float] = None,
    start_y: Optional[float] = None,
    button: str = "left",
) -> Dict[str, Any]:
    """
    Realistic human drag-and-drop from start position to target.
    """
    ensure_desktop_access()
    t0 = time.perf_counter()
    p = get_player()
    current_pos = p.get_current_position()
    s_x = float(start_x if start_x is not None else current_pos[0])
    s_y = float(start_y if start_y is not None else current_pos[1])

    p.drag(
        target_x=float(target_x),
        target_y=float(target_y),
        start_x=s_x,
        start_y=s_y,
        button=button,
    )
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    final_pos = p.get_current_position()

    return {
        "status": "success",
        "action": "drag",
        "button": button,
        "from": [s_x, s_y],
        "target": [float(target_x), float(target_y)],
        "final_pos": [float(final_pos[0]), float(final_pos[1])],
        "elapsed_ms": elapsed_ms,
    }

