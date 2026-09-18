"""
stealth_mouse: Human-like mouse trajectory generation for web automation and anti-bot evasion.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .recorder import MouseRecorder
    from .indexer import TrajectoryIndexer, TrajectoryMatch
    from .transformer import TrajectoryTransformer
    from .interpolator import TrajectoryInterpolator
    from .player import StealthMousePlayer

__all__ = [
    "move",
    "click",
    "MouseRecorder",
    "TrajectoryIndexer",
    "TrajectoryMatch",
    "TrajectoryTransformer",
    "TrajectoryInterpolator",
    "StealthMousePlayer",
]


def move(x: float, y: float) -> None:
    """Moves the mouse naturally to (x, y)."""
    from .player import StealthMousePlayer
    StealthMousePlayer(data_dir="data", top_k=10).move_to(float(x), float(y))


def click(x: float, y: float, button: str = "left") -> None:
    """Moves the mouse naturally to (x, y) and performs a click."""
    from .player import StealthMousePlayer
    StealthMousePlayer(data_dir="data", top_k=10).click(float(x), float(y), button=button)


def __getattr__(name: str) -> Any:
    if name == "MouseRecorder":
        from .recorder import MouseRecorder
        return MouseRecorder
    elif name in ("TrajectoryIndexer", "TrajectoryMatch"):
        from .indexer import TrajectoryIndexer, TrajectoryMatch
        return TrajectoryIndexer if name == "TrajectoryIndexer" else TrajectoryMatch
    elif name == "TrajectoryTransformer":
        from .transformer import TrajectoryTransformer
        return TrajectoryTransformer
    elif name == "TrajectoryInterpolator":
        from .interpolator import TrajectoryInterpolator
        return TrajectoryInterpolator
    elif name == "StealthMousePlayer":
        from .player import StealthMousePlayer
        return StealthMousePlayer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
