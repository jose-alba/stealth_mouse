"""
Transformer module for stealth_mouse.

Applies conformal 2D geometric transformation (translation, rotation, distance scaling)
and non-linear temporal remapping based on Fitts's Law to adapt human recorded trajectories
to arbitrary start and end target coordinates.
"""

from typing import Tuple, Union
import numpy as np


class TrajectoryTransformer:
    """
    Transforms recorded trajectory points to start at start_point and finish at end_point,
    preserving human kinematic micro-tremors and adapting movement duration via Fitts's Law.
    """

    def __init__(self, target_width: float = 40.0):
        """
        Args:
            target_width: Estimated target width W (in pixels) for Fitts's Law index of difficulty.
        """
        self.target_width = max(target_width, 1.0)

    def transform(
        self,
        points: np.ndarray,
        start_point: Tuple[float, float],
        end_point: Tuple[float, float],
    ) -> np.ndarray:
        """
        Conformally maps and temporally scales source points to (start_point -> end_point).

        Args:
            points: Array of shape (N, 3) representing [x, y, t_rel].
            start_point: (x0, y0) starting coordinates.
            end_point: (x1, y1) destination coordinates.

        Returns:
            Transformed points array of shape (N, 3) representing [x, y, t_new].
        """
        if len(points) < 2:
            return points.copy()

        x0, y0 = float(start_point[0]), float(start_point[1])
        x1, y1 = float(end_point[0]), float(end_point[1])

        # Target vector
        target_dx = x1 - x0
        target_dy = y1 - y0
        target_dist = float(np.hypot(target_dx, target_dy))

        if target_dist < 1e-4:
            # Degenerate: start and end are identical
            out = np.zeros_like(points)
            out[:, 0] = x0
            out[:, 1] = y0
            out[:, 2] = points[:, 2]
            return out

        target_angle = float(np.atan2(target_dy, target_dx))

        # Source vector
        src_p0 = points[0, :2]
        src_p1 = points[-1, :2]
        src_dx = float(src_p1[0] - src_p0[0])
        src_dy = float(src_p1[1] - src_p0[1])
        src_dist = float(np.hypot(src_dx, src_dy))
        src_angle = float(np.atan2(src_dy, src_dx))

        # 1. Shift to source origin (0, 0)
        coords = points[:, :2] - src_p0

        # 2. Conformal rotation to align with target direction
        delta_angle = target_angle - src_angle
        cos_a = np.cos(delta_angle)
        sin_a = np.sin(delta_angle)

        rot_x = coords[:, 0] * cos_a - coords[:, 1] * sin_a
        rot_y = coords[:, 0] * sin_a + coords[:, 1] * cos_a

        # 3. Scale distance
        scale = target_dist / max(src_dist, 1.0)
        scaled_x = rot_x * scale
        scaled_y = rot_y * scale

        # 4. Translate to target start coordinates
        final_x = x0 + scaled_x
        final_y = y0 + scaled_y

        # Guarantee exact boundary arrival at target coordinates
        final_x[0] = x0
        final_y[0] = y0
        final_x[-1] = x1
        final_y[-1] = y1

        # 5. Hybrid Temporal Adaptation (Pure Human Time <-> Fitts Damping):
        # - If distance is close to the recorded stroke (typical with KDTree),
        #   100% of original recorded human time is used, with zero synthetic formulas.
        # - If distance differs substantially (atypical stretch), Fitts's Law
        #   smoothly (exponentially) steps in to prevent unnatural velocities.
        w = self.target_width
        id_target = np.log2(1.0 + target_dist / w)
        id_src = np.log2(1.0 + max(src_dist, 1.0) / w)
        fitts_ratio = float(np.clip(id_target / max(id_src, 1e-3), 0.35, 2.50))

        # Relative distance distortion: |ln(D_target) - ln(D_src)|
        log_dist_diff = abs(float(np.log(max(target_dist, 1.0)) - np.log(max(src_dist, 1.0))))

        # Fitts weight with smooth exponential curve (inverted Gaussian):
        # - Small differences (< 15-20%): weight_fitts ~ 0.0 -> 100% pure human time
        # - Large differences (> 100%): weight_fitts -> 1.0 -> Fitts damping
        sigma = 0.35
        weight_fitts = 1.0 - float(np.exp(-(log_dist_diff / sigma) ** 2))

        # Smooth blending without sharp transitions
        blended_ratio = (1.0 - weight_fitts) * 1.0 + weight_fitts * fitts_ratio

        orig_t = points[:, 2]
        final_t = orig_t * blended_ratio

        return np.column_stack((final_x, final_y, final_t)).astype(np.float32)
