"""
stealth_mouse_common: Path Resolver
Safely locates trajectory datasets (.npz) across local, global, or distributed skill directories.
"""

import os
from pathlib import Path
from typing import Optional


def find_data_dir() -> Path:
    """
    Searches for the directory containing trajectories_index.npz and trajectories_points.npz.
    Checks:
      1. stealth_mouse_common/data (bundled inside skill)
      2. Root repo data/ (if executing inside stealth_mouse development folder)
      3. User profile ~/.gemini/config/skills/stealth_mouse_common/data
      4. Current working directory ./data
    """
    # 1. Bundled inside stealth_mouse_common package
    current_file_dir = Path(__file__).resolve().parent
    candidates = [
        current_file_dir / "data",
        current_file_dir.parent / "data",
        current_file_dir.parent.parent / "data",
        Path.cwd() / "data",
        Path.home() / ".gemini" / "config" / "skills" / "stealth_mouse_common" / "data",
    ]

    for candidate in candidates:
        if (candidate / "trajectories_index.npz").exists() and (candidate / "trajectories_points.npz").exists():
            return candidate.resolve()

    # Fallback to local data dir inside stealth_mouse_common
    fallback = current_file_dir / "data"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback.resolve()

