"""
Scroller module for stealth_mouse.

Implements human biological mouse wheel scrolling with:
1. Multi-flick burst decomposition (segmenting large scrolls with finger repositioning pauses).
2. Asymmetric velocity curves (rapid finger stroke acceleration followed by exponential friction decay).
3. Realistic polling jitter synchronized with display refresh intervals (60-120 Hz / 8-16 ms).
4. Stochastic overshoot and corrective rebound (visual target confirmation adjustment).
"""

import time
import random
import asyncio
from typing import List, Tuple, Optional, Any

import numpy as np


class HumanScroller:
    """
    Biological mouse scroll generator and dispatcher.
    """

    def __init__(self, allow_overshoot: bool = True):
        self.allow_overshoot = allow_overshoot

    def generate_steps(self, delta_y: float) -> List[Tuple[float, float]]:
        """
        Generates a sequence of (step_delta_y, delay_seconds) simulating human wheel physics.
        
        Args:
            delta_y: Total vertical displacement in pixels.
                     Positive: scroll down (page content moves up).
                     Negative: scroll up (page content moves down).
                     
        Returns:
            List of (dy_step, dt_step) tuples.
        """
        if abs(delta_y) < 1.0:
            return []

        sign = 1.0 if delta_y > 0 else -1.0
        total_dist = abs(delta_y)

        # 1. Determine if overshoot occurs (typical on medium to large scrolls)
        overshoot_dist = 0.0
        if self.allow_overshoot and total_dist >= 200.0 and random.random() < 0.28:
            overshoot_dist = random.uniform(30.0, min(75.0, total_dist * 0.12))

        target_dist = total_dist + overshoot_dist

        # 2. Decompose into finger flicks/bursts
        if target_dist <= 250:
            splits = [1.0]
        elif target_dist <= 650:
            r = random.uniform(0.48, 0.58)
            splits = [r, 1.0 - r]
        else:
            num_flicks = min(5, max(3, int(np.ceil(target_dist / 350.0))))
            weights = [random.uniform(0.8, 1.2) for _ in range(num_flicks)]
            s = sum(weights)
            splits = [w / s for w in weights]

        steps: List[Tuple[float, float]] = []

        # 3. Simulate each flick with ballistic physics
        for flick_idx, fraction in enumerate(splits):
            flick_dist = target_dist * fraction
            duration = random.uniform(0.16, 0.32) * (1.0 + 0.3 * (flick_dist / 350.0))
            duration = min(0.45, max(0.12, duration))

            dt_base = random.uniform(0.009, 0.015)
            num_steps = max(8, int(duration / dt_base))
            t = np.linspace(0.0, 1.0, num_steps)

            # Asymmetric velocity curve: rapid rise, prolonged exponential decay
            peak_pos = random.uniform(0.18, 0.28)
            v = (t / peak_pos) * np.exp(1.0 - (t / peak_pos))
            v[v < 0] = 0.0

            v_sum = float(np.sum(v))
            if v_sum <= 0:
                step_distances = np.full(num_steps, flick_dist / num_steps)
            else:
                step_distances = (v / v_sum) * flick_dist

            for d in step_distances:
                jittered_dt = dt_base + random.uniform(-0.002, 0.003)
                steps.append((float(sign * d), float(max(0.006, jittered_dt))))

            # Inter-flick pause (lifting finger and repositioning onto wheel)
            if flick_idx < len(splits) - 1:
                pause = random.uniform(0.09, 0.19)
                steps.append((0.0, float(pause)))

        # 4. Corrective rebound if overshoot occurred
        if overshoot_dist > 0.0:
            rebound_pause = random.uniform(0.15, 0.28)
            steps.append((0.0, float(rebound_pause)))

            rebound_dist = overshoot_dist
            rebound_duration = random.uniform(0.12, 0.22)
            dt_base = random.uniform(0.010, 0.016)
            num_steps = max(6, int(rebound_duration / dt_base))
            t = np.linspace(0.0, 1.0, num_steps)
            v = (t / 0.25) * np.exp(1.0 - (t / 0.25))
            v_sum = float(np.sum(v))
            step_distances = (v / v_sum) * rebound_dist if v_sum > 0 else np.full(num_steps, rebound_dist / num_steps)

            for d in step_distances:
                jittered_dt = dt_base + random.uniform(-0.002, 0.003)
                steps.append((float(-sign * d), float(max(0.006, jittered_dt))))

        return steps

    def scroll(
        self,
        delta_y: float,
        mouse_controller: Optional[Any] = None,
        page: Optional[Any] = None,
    ) -> None:
        """
        Synchronously dispatches realistic human scroll events.
        """
        steps = self.generate_steps(delta_y)
        if not steps:
            return

        if page is not None and hasattr(page, "mouse"):
            # Playwright synchronous (if in sync API) or fallback
            for dy, dt in steps:
                if dt > 0:
                    time.sleep(dt)
                if abs(dy) > 0:
                    page.mouse.wheel(0, dy)
        else:
            if mouse_controller is None:
                from pynput.mouse import Controller
                mouse_controller = Controller()

            # In pynput / Windows, 1 wheel notch ~ 100px.
            # Negative dy scrolls DOWN, positive scrolls UP.
            # We accumulate fractional notches to preserve smooth sub-pixel wheel delta.
            accumulated_notches = 0.0
            for dy, dt in steps:
                if dt > 0:
                    time.sleep(dt)
                if abs(dy) > 0:
                    # Invert sign for OS-level mouse controller: down is negative dy
                    notch_delta = -dy / 100.0
                    accumulated_notches += notch_delta
                    # Dispatch integer or fine notch step
                    notch_step = int(accumulated_notches)
                    if notch_step != 0:
                        mouse_controller.scroll(0, notch_step)
                        accumulated_notches -= notch_step

            # Dispatch any remaining fraction if significant
            final_step = int(round(accumulated_notches))
            if final_step != 0:
                mouse_controller.scroll(0, final_step)

    async def async_scroll(
        self,
        delta_y: float,
        page: Optional[Any] = None,
        mouse_controller: Optional[Any] = None,
    ) -> None:
        """
        Asynchronously dispatches realistic human scroll events for Playwright / asyncio.
        """
        steps = self.generate_steps(delta_y)
        if not steps:
            return

        if page is not None and hasattr(page, "mouse"):
            for dy, dt in steps:
                if dt > 0:
                    await asyncio.sleep(dt)
                if abs(dy) > 0:
                    await page.mouse.wheel(0, dy)
        else:
            if mouse_controller is None:
                from pynput.mouse import Controller
                mouse_controller = Controller()

            accumulated_notches = 0.0
            for dy, dt in steps:
                if dt > 0:
                    await asyncio.sleep(dt)
                if abs(dy) > 0:
                    notch_delta = -dy / 100.0
                    accumulated_notches += notch_delta
                    notch_step = int(accumulated_notches)
                    if notch_step != 0:
                        mouse_controller.scroll(0, notch_step)
                        accumulated_notches -= notch_step

            final_step = int(round(accumulated_notches))
            if final_step != 0:
                mouse_controller.scroll(0, final_step)
