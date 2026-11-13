"""
Player module for stealth_mouse.

Dispatches human-like mouse trajectories to the physical operating system (via pynput)
or into browser automation frameworks (Playwright / CDP pages).
"""

import time
import random
import asyncio
from typing import Optional, Tuple, Any, List, Union
import numpy as np
from pynput.mouse import Controller as MouseController, Button

from .indexer import TrajectoryIndexer, TrajectoryMatch
from .transformer import TrajectoryTransformer
from .interpolator import TrajectoryInterpolator
from .scroller import HumanScroller


class StealthMousePlayer:
    """
    Simulates human mouse movements towards target coordinates using database trajectories,
    conformal transformations, cubic splines, and hardware-rate event dispatch.
    """

    def __init__(
        self,
        page: Optional[Any] = None,
        data_dir: str = "data",
        top_k: int = 10,
    ):
        """
        Args:
            page: Optional Playwright / CDP page object. If None, moves OS native mouse.
            data_dir: Directory containing trajectories_index.npz and trajectories_points.npz.
            top_k: Number of top candidate trajectories to consider before random selection.
        """
        self.page = page
        self.top_k = top_k

        self.indexer = TrajectoryIndexer(data_dir)
        self.transformer = TrajectoryTransformer()
        self.interpolator = TrajectoryInterpolator()

        self._mouse_controller = MouseController()
        self._scroller = HumanScroller()
        self._current_pos: Tuple[float, float] = (0.0, 0.0)

    def get_current_position(self) -> Tuple[float, float]:
        """Reads current mouse coordinates from the operating system or browser state."""
        if self.page is None:
            try:
                pos = self._mouse_controller.position
                if pos is not None:
                    self._current_pos = (float(pos[0]), float(pos[1]))
                    return self._current_pos
            except Exception:
                pass
            return self._current_pos
        return self._current_pos

    def generate_path(
        self,
        target_x: float,
        target_y: float,
        start_x: Optional[float] = None,
        start_y: Optional[float] = None,
    ) -> np.ndarray:
        """
        Generates the human trajectory array of shape (M, 3) representing [x, y, t].

        Steps:
          1. Reads start coordinates.
          2. Calculates dx, dy.
          3. Queries the KDTree and selects 1 random trajectory among the top 10.
          4. Transforms source trajectory to target start and end.
          5. Generates cubic spline with 60-120 Hz variable sampling.
        """
        if start_x is None or start_y is None:
            curr_x, curr_y = self.get_current_position()
            start_x = curr_x if start_x is None else start_x
            start_y = curr_y if start_y is None else start_y

        dx = target_x - start_x
        dy = target_y - start_y
        dist = float(np.hypot(dx, dy))

        if dist < 2.0:
            return np.array([[target_x, target_y, 0.0]], dtype=np.float32)

        if not self.indexer.is_loaded:
            raise RuntimeError("Trajectory dataset not found in data/. Run 'python -m src.recorder' first.")

        # 1. Retrieve top candidates and pick 1 randomly to avoid deterministic replay
        candidates = self.indexer.query_nearest(dx, dy, k=self.top_k)
        chosen_match: TrajectoryMatch = random.choice(candidates)

        # 2. Geometric rotation, scaling and Fitts's Law temporal remapping
        transformed = self.transformer.transform(
            chosen_match.points,
            (start_x, start_y),
            (target_x, target_y),
        )

        # 3. Continuous cubic spline with 60-120 Hz variable sampling + temporal jitter
        smooth_path = self.interpolator.interpolate(transformed)
        return smooth_path

    def move_to(
        self,
        target_x: float,
        target_y: float,
        start_x: Optional[float] = None,
        start_y: Optional[float] = None,
    ) -> None:
        """Synchronously moves the mouse naturally to (target_x, target_y)."""
        path = self.generate_path(target_x, target_y, start_x, start_y)
        if len(path) == 0:
            return

        t_prev = float(path[0, 2])
        for i in range(len(path)):
            x = float(path[i, 0])
            y = float(path[i, 1])
            t_curr = float(path[i, 2])

            dt = t_curr - t_prev
            if dt > 0:
                time.sleep(dt)

            if self.page is None:
                self._mouse_controller.position = (int(round(x)), int(round(y)))
            else:
                self._current_pos = (x, y)

            t_prev = t_curr

        self._current_pos = (target_x, target_y)

    def click(
        self,
        target_x: float,
        target_y: float,
        button: str = "left",
        dwell_time_ms: Optional[float] = None,
    ) -> None:
        """
        Moves naturally to (target_x, target_y), pauses with pre-click visual confirmation hesitation,
        and performs a realistic human click (button='left' or 'right', default 'left').
        """
        self.move_to(target_x, target_y)

        # 1. Biological pre-click hesitation (visual target acquisition delay: 60 - 160 ms)
        time.sleep(random.uniform(0.060, 0.160))

        # 2. Realistic human dwell time (time between press and release: 45 - 115 ms)
        if dwell_time_ms is None:
            dwell_s = random.uniform(0.045, 0.115)
        else:
            dwell_s = dwell_time_ms / 1000.0

        btn = Button.left if button == "left" else (Button.right if button == "right" else Button.middle)

        if self.page is None:
            self._mouse_controller.press(btn)
            time.sleep(dwell_s)
            self._mouse_controller.release(btn)
        else:
            if hasattr(self.page, "mouse"):
                self.page.mouse.down(button=button)
                time.sleep(dwell_s)
                self.page.mouse.up(button=button)

        # 3. Micro-settle pause after click (30 - 70 ms)
        time.sleep(random.uniform(0.030, 0.070))

    def scroll(self, delta_y: float) -> None:
        """
        Dispatches realistic human scroll events with inertia, multi-flick bursts, and rebound.
        Usage:
            player.scroll(600)   # Scroll down 600px
            player.scroll(-300)  # Scroll up 300px
        """
        self._scroller.scroll(delta_y, mouse_controller=self._mouse_controller, page=self.page)

    async def async_move_to(
        self,
        target_x: float,
        target_y: float,
        start_x: Optional[float] = None,
        start_y: Optional[float] = None,
    ) -> None:
        """Asynchronously moves mouse to (target_x, target_y) for Playwright / async event loops."""
        path = self.generate_path(target_x, target_y, start_x, start_y)
        if len(path) == 0:
            return

        t_prev = float(path[0, 2])
        for i in range(len(path)):
            x = float(path[i, 0])
            y = float(path[i, 1])
            t_curr = float(path[i, 2])

            dt = t_curr - t_prev
            if dt > 0:
                await asyncio.sleep(dt)

            if self.page is not None and hasattr(self.page, "mouse"):
                await self.page.mouse.move(x, y)
            else:
                self._mouse_controller.position = (int(round(x)), int(round(y)))

            self._current_pos = (x, y)
            t_prev = t_curr

        self._current_pos = (target_x, target_y)

    async def async_click(
        self,
        target_x: float,
        target_y: float,
        button: str = "left",
        dwell_time_ms: Optional[float] = None,
    ) -> None:
        """
        Asynchronously moves to target, pauses with pre-click hesitation,
        and triggers Playwright click with realistic dwell time and settle.
        """
        await self.async_move_to(target_x, target_y)

        # 1. Biological pre-click hesitation (visual target acquisition delay: 60 - 160 ms)
        await asyncio.sleep(random.uniform(0.060, 0.160))

        # 2. Realistic human dwell time (45 - 115 ms)
        if dwell_time_ms is None:
            dwell_s = random.uniform(0.045, 0.115)
        else:
            dwell_s = dwell_time_ms / 1000.0

        if self.page is not None and hasattr(self.page, "mouse"):
            await self.page.mouse.down(button=button)
            await asyncio.sleep(dwell_s)
            await self.page.mouse.up(button=button)
        else:
            btn = Button.left if button == "left" else (Button.right if button == "right" else Button.middle)
            self._mouse_controller.press(btn)
            await asyncio.sleep(dwell_s)
            self._mouse_controller.release(btn)

        # 3. Micro-settle pause after click (30 - 70 ms)
        await asyncio.sleep(random.uniform(0.030, 0.070))

    async def async_scroll(self, delta_y: float) -> None:
        """
        Asynchronously dispatches realistic human scroll events for Playwright / asyncio.
        Usage:
            await player.async_scroll(600)   # Scroll down 600px
            await player.async_scroll(-300)  # Scroll up 300px
        """
        await self._scroller.async_scroll(delta_y, page=self.page, mouse_controller=self._mouse_controller)

    def drag(
        self,
        target_x: float,
        target_y: float,
        start_x: Optional[float] = None,
        start_y: Optional[float] = None,
        button: str = "left",
    ) -> None:
        """
        Performs realistic human drag-and-drop from (start_x, start_y) or current position
        to (target_x, target_y), with static friction breakaway delay, physiological kinematics,
        and target alignment hesitation before releasing.
        
        Args:
            target_x: Destination X coordinate.
            target_y: Destination Y coordinate.
            start_x: Optional origin X coordinate (moves here first if specified).
            start_y: Optional origin Y coordinate.
            button: Mouse button to drag with ('left' or 'right', default: 'left').
        """
        if start_x is not None and start_y is not None:
            curr_x, curr_y = self.get_current_position()
            if abs(curr_x - start_x) > 1.0 or abs(curr_y - start_y) > 1.0:
                self.move_to(start_x, start_y)

        # 1. Pre-press visual targeting delay (60 - 140 ms)
        time.sleep(random.uniform(0.060, 0.140))

        btn = Button.left if button == "left" else (Button.right if button == "right" else Button.middle)

        # 2. Press down
        if self.page is None:
            self._mouse_controller.press(btn)
        else:
            if hasattr(self.page, "mouse"):
                self.page.mouse.down(button=button)

        try:
            # 3. Static friction / muscle tension hesitation before motion starts (60 - 130 ms)
            time.sleep(random.uniform(0.060, 0.130))

            # 4. Generate and dispatch human trajectory while holding button
            path = self.generate_path(target_x, target_y)
            if len(path) > 0:
                t_prev = float(path[0, 2])
                for i in range(len(path)):
                    x = float(path[i, 0])
                    y = float(path[i, 1])
                    t_curr = float(path[i, 2])

                    dt = t_curr - t_prev
                    if dt > 0:
                        time.sleep(dt)

                    if self.page is None:
                        self._mouse_controller.position = (int(round(x)), int(round(y)))
                    else:
                        if hasattr(self.page, "mouse"):
                            self.page.mouse.move(x, y)
                    self._current_pos = (x, y)
                    t_prev = t_curr

            self._current_pos = (target_x, target_y)

            # 5. Visual confirmation hesitation before releasing at destination (80 - 180 ms)
            time.sleep(random.uniform(0.080, 0.180))
        finally:
            # 6. Always safely release button to prevent cursor stickiness
            if self.page is None:
                self._mouse_controller.release(btn)
            else:
                if hasattr(self.page, "mouse"):
                    self.page.mouse.up(button=button)

        # 7. Post-release settle pause (30 - 70 ms)
        time.sleep(random.uniform(0.030, 0.070))

    async def async_drag(
        self,
        target_x: float,
        target_y: float,
        start_x: Optional[float] = None,
        start_y: Optional[float] = None,
        button: str = "left",
    ) -> None:
        """
        Asynchronously performs realistic human drag-and-drop for Playwright.
        """
        if start_x is not None and start_y is not None:
            curr_x, curr_y = self.get_current_position()
            if abs(curr_x - start_x) > 1.0 or abs(curr_y - start_y) > 1.0:
                await self.async_move_to(start_x, start_y)

        # 1. Pre-press hesitation (60 - 140 ms)
        await asyncio.sleep(random.uniform(0.060, 0.140))

        btn = Button.left if button == "left" else (Button.right if button == "right" else Button.middle)

        # 2. Press down
        if self.page is not None and hasattr(self.page, "mouse"):
            await self.page.mouse.down(button=button)
        else:
            self._mouse_controller.press(btn)

        try:
            # 3. Muscle tension before motion starts (60 - 130 ms)
            await asyncio.sleep(random.uniform(0.060, 0.130))

            # 4. Generate and dispatch human trajectory while holding button
            path = self.generate_path(target_x, target_y)
            if len(path) > 0:
                t_prev = float(path[0, 2])
                for i in range(len(path)):
                    x = float(path[i, 0])
                    y = float(path[i, 1])
                    t_curr = float(path[i, 2])

                    dt = t_curr - t_prev
                    if dt > 0:
                        await asyncio.sleep(dt)

                    if self.page is not None and hasattr(self.page, "mouse"):
                        await self.page.mouse.move(x, y)
                    else:
                        self._mouse_controller.position = (int(round(x)), int(round(y)))
                    self._current_pos = (x, y)
                    t_prev = t_curr

            self._current_pos = (target_x, target_y)

            # 5. Visual alignment hesitation before release (80 - 180 ms)
            await asyncio.sleep(random.uniform(0.080, 0.180))
        finally:
            # 6. Always release button safely
            if self.page is not None and hasattr(self.page, "mouse"):
                await self.page.mouse.up(button=button)
            else:
                self._mouse_controller.release(btn)

        # 7. Post-release settle pause (30 - 70 ms)
        await asyncio.sleep(random.uniform(0.030, 0.070))
