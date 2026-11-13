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
    from .scroller import HumanScroller

__all__ = [
    "move",
    "click",
    "scroll",
    "drag",
    "MouseRecorder",
    "TrajectoryIndexer",
    "TrajectoryMatch",
    "TrajectoryTransformer",
    "TrajectoryInterpolator",
    "StealthMousePlayer",
    "HumanScroller",
]


def move(x: float, y: float) -> None:
    """Moves the mouse naturally to (x, y)."""
    from .player import StealthMousePlayer
    StealthMousePlayer(data_dir="data", top_k=10).move_to(float(x), float(y))


def click(x: float, y: float, button: str = "left") -> None:
    """Moves the mouse naturally to (x, y) and performs a click (button='left' or 'right')."""
    from .player import StealthMousePlayer
    StealthMousePlayer(data_dir="data", top_k=10).click(float(x), float(y), button=button)


def scroll(delta_y: float) -> None:
    """Scrolls vertically with human biological physics (flicks, friction decay, rebound)."""
    from .player import StealthMousePlayer
    StealthMousePlayer(data_dir="data", top_k=10).scroll(float(delta_y))


def drag(target_x: float, target_y: float, start_x: float = None, start_y: float = None, button: str = "left") -> None:
    """Performs realistic human drag-and-drop to (target_x, target_y)."""
    from .player import StealthMousePlayer
    StealthMousePlayer(data_dir="data", top_k=10).drag(float(target_x), float(target_y), start_x=start_x, start_y=start_y, button=button)


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
    elif name == "HumanScroller":
        from .scroller import HumanScroller
        return HumanScroller
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
