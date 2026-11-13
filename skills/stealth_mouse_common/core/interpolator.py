"""
Interpolator module for stealth_mouse.

Converts transformed trajectory points into smooth continuous cubic splines
and samples coordinates at realistic hardware/monitor frequencies (60 Hz to 120 Hz, ~8-16 ms)
with micro-temporal jitter to replicate physical display and mouse polling events.
"""

from typing import Tuple, List, Optional
import numpy as np
from scipy.interpolate import CubicSpline


class TrajectoryInterpolator:
    """
    Interpolates trajectory points into continuous cubic splines and generates high-fidelity
    event sequences evaluated at variable refresh rates (60-120 Hz) with subtle temporal jitter.
    """

    def __init__(
        self,
        min_dt_ms: float = 8.0,
        max_dt_ms: float = 16.0,
        jitter_std_ms: float = 1.0,
    ):
        """
        Args:
            min_dt_ms: Minimum time step in milliseconds (~120 Hz polling).
            max_dt_ms: Maximum time step in milliseconds (~60 Hz polling).
            jitter_std_ms: Standard deviation of temporal jitter (ms).
        """
        self.min_dt = min_dt_ms / 1000.0
        self.max_dt = max_dt_ms / 1000.0
        self.jitter_std = jitter_std_ms / 1000.0

    def interpolate(self, trajectory: np.ndarray) -> np.ndarray:
        """
        Fits a cubic spline to the trajectory and samples at variable refresh intervals.

        Args:
            trajectory: Array of shape (N, 3) representing [x, y, t].

        Returns:
            Smoothly sampled array of shape (M, 3) representing [x, y, t].
        """
        if len(trajectory) < 2:
            return trajectory.copy()

        x = trajectory[:, 0]
        y = trajectory[:, 1]
        t = trajectory[:, 2].copy()

        # Ensure timestamps are strictly monotonically increasing
        eps = 1e-4
        for i in range(1, len(t)):
            if t[i] <= t[i - 1]:
                t[i] = t[i - 1] + eps

        total_time = float(t[-1] - t[0])
        if total_time <= 0.005:
            # Trajectory too short for multi-step spline
            return trajectory.copy()

        # Fit cubic splines for x(t) and y(t)
        # If very few points (e.g. 2 or 3), linear/natural boundary handles it
        spline_x = CubicSpline(t, x, bc_type="natural")
        spline_y = CubicSpline(t, y, bc_type="natural")

        # Generate variable-frequency timestamps between 0 and total_time
        sample_times = [float(t[0])]
        curr_t = float(t[0])
        end_t = float(t[-1])

        while curr_t < end_t:
            # Random step within 60-120 Hz range + micro-jitter
            base_dt = np.random.uniform(self.min_dt, self.max_dt)
            jitter = np.random.normal(0, self.jitter_std)
            step = float(np.clip(base_dt + jitter, 0.004, 0.020))

            next_t = curr_t + step
            if next_t >= end_t - 0.004:
                # Close enough to target endpoint
                break
            sample_times.append(next_t)
            curr_t = next_t

        sample_times.append(end_t)
        sample_t = np.array(sample_times, dtype=np.float64)

        # Evaluate coordinates along continuous spline
        sampled_x = spline_x(sample_t)
        sampled_y = spline_y(sample_t)

        # Ensure exact start and finish coordinates
        sampled_x[0] = x[0]
        sampled_y[0] = y[0]
        sampled_x[-1] = x[-1]
        sampled_y[-1] = y[-1]

        return np.column_stack((sampled_x, sampled_y, sample_t)).astype(np.float32)
