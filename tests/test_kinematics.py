"""
Kinematic comparison and biometric validation tests for stealth_mouse.

Compares stealth_mouse against traditional synthetic Bézier curve generation across:
1. Asymmetric bell-shaped velocity profile (human acceleration vs deceleration phases).
2. Hardware polling jitter (variance in dt intervals vs synthetic fixed sleeps).
3. Target arrival precision.
"""

import sys
import unittest
from pathlib import Path

# Ensure root workspace directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from src.player import StealthMousePlayer


def generate_synthetic_bezier(
    start: tuple[float, float],
    end: tuple[float, float],
    duration: float = 0.400,
    steps: int = 40,
) -> np.ndarray:
    """Generates a standard cubic Bézier curve commonly used by naive bot scrapers."""
    x0, y0 = start
    x3, y3 = end

    # Random control points with synthetic curvature
    dx = x3 - x0
    dy = y3 - y0
    x1, y1 = x0 + 0.3 * dx - 0.2 * dy, y0 + 0.3 * dy + 0.2 * dx
    x2, y2 = x0 + 0.7 * dx + 0.1 * dy, y0 + 0.7 * dy - 0.1 * dx

    t_vals = np.linspace(0.0, 1.0, steps)
    t_times = np.linspace(0.0, duration, steps)  # Fixed intervals, zero variance

    bx = (1 - t_vals) ** 3 * x0 + 3 * (1 - t_vals) ** 2 * t_vals * x1 + 3 * (1 - t_vals) * t_vals ** 2 * x2 + t_vals ** 3 * x3
    by = (1 - t_vals) ** 3 * y0 + 3 * (1 - t_vals) ** 2 * t_vals * y1 + 3 * (1 - t_vals) * t_vals ** 2 * y2 + t_vals ** 3 * y3

    return np.column_stack((bx, by, t_times)).astype(np.float32)


def compute_velocity_profile(trajectory: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Computes speeds (px/s) along trajectory timestamps."""
    coords = trajectory[:, :2]
    timestamps = trajectory[:, 2]

    diffs = np.diff(coords, axis=0)
    dt = np.diff(timestamps)
    dt = np.where(dt <= 1e-5, 1e-5, dt)

    step_dist = np.hypot(diffs[:, 0], diffs[:, 1])
    speeds = step_dist / dt
    time_mid = (timestamps[:-1] + timestamps[1:]) / 2.0
    return time_mid, speeds


class TestKinematics(unittest.TestCase):
    """Verifies that stealth_mouse produces biologically authentic human motion."""

    @classmethod
    def setUpClass(cls):
        cls.player = StealthMousePlayer(data_dir="data", top_k=10)
        cls.start = (200.0, 200.0)
        cls.target = (950.0, 680.0)

    def test_polling_interval_has_hardware_jitter(self):
        """
        Naive bots use fixed time delays (dt = 10ms with variance 0).
        Human movements polled by real hardware must show natural jitter.
        """
        stealth_path = self.player.generate_path(self.target[0], self.target[1], self.start[0], self.start[1])
        stealth_dt = np.diff(stealth_path[:, 2])

        bezier_path = generate_synthetic_bezier(self.start, self.target)
        bezier_dt = np.diff(bezier_path[:, 2])

        # Bézier has 0 std dev (fixed artificial time step)
        self.assertAlmostEqual(float(np.std(bezier_dt)), 0.0, places=5)

        # stealth_mouse has non-zero micro-jitter replicating display/mouse interrupts
        self.assertGreater(float(np.std(stealth_dt)), 0.0005, "Stealth mouse must have natural temporal jitter")

    def test_asymmetric_velocity_profile(self):
        """
        Human reaching movements exhibit asymmetric velocity curves with variable peak locations
        and physiological acceleration/deceleration phases (unlike synthetic curves with fixed peaks).
        """
        peak_ratios = []
        for _ in range(5):
            stealth_path = self.player.generate_path(self.target[0], self.target[1], self.start[0], self.start[1])
            t_mid, speeds = compute_velocity_profile(stealth_path)
            total_time = stealth_path[-1, 2]
            peak_idx = int(np.argmax(speeds))
            peak_time = t_mid[peak_idx]
            peak_ratios.append(peak_time / total_time)

        # Human strokes vary naturally, within realistic physical bounds (15% to 85% of movement)
        for pr in peak_ratios:
            self.assertGreater(pr, 0.15, f"Peak velocity too early: {pr:.2f}")
            self.assertLess(pr, 0.85, f"Peak velocity too late: {pr:.2f}")

        # Human strokes must exhibit variation across runs (anti-deterministic replay)
        self.assertGreater(float(np.std(peak_ratios)), 0.0, "Multiple trajectories must vary organically")

    def test_target_arrival_precision(self):
        """Stealth mouse must hit target coordinates within sub-pixel precision."""
        path = self.player.generate_path(self.target[0], self.target[1], self.start[0], self.start[1])
        last_pt = path[-1, :2]
        dist_error = float(np.hypot(last_pt[0] - self.target[0], last_pt[1] - self.target[1]))
        self.assertLess(dist_error, 0.5, "Target arrival should have sub-pixel accuracy")


def run_visual_benchmark() -> None:
    """Generates comparison plot between Bézier and stealth_mouse and saves to tests/."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("[!] Matplotlib not available for visual benchmark plot.")
        return

    player = StealthMousePlayer(data_dir="data", top_k=10)
    start = (150.0, 150.0)
    target = (900.0, 600.0)

    stealth_path = player.generate_path(target[0], target[1], start[0], start[1])
    bezier_path = generate_synthetic_bezier(start, target, duration=stealth_path[-1, 2], steps=len(stealth_path))

    t_stealth, v_stealth = compute_velocity_profile(stealth_path)
    t_bezier, v_bezier = compute_velocity_profile(bezier_path)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.patch.set_facecolor("#11111b")
    for ax in axes.flat:
        ax.set_facecolor("#181825")
        ax.tick_params(colors="#cdd6f4")
        for spine in ax.spines.values():
            spine.set_color("#45475a")

    # 1. 2D Trajectory
    axes[0, 0].set_title("2D Trajectory Path", color="#cdd6f4", fontweight="bold")
    axes[0, 0].plot(bezier_path[:, 0], bezier_path[:, 1], "--", color="#f38ba8", label="Synthetic Bézier (Bot)", lw=2)
    axes[0, 0].plot(stealth_path[:, 0], stealth_path[:, 1], "-", color="#a6e3a1", label="Stealth Mouse (Human)", lw=2)
    axes[0, 0].scatter([start[0], target[0]], [start[1], target[1]], color="#89b4fa", zorder=5)
    axes[0, 0].legend(facecolor="#1e1e2e", edgecolor="#45475a", labelcolor="#cdd6f4")

    # 2. Velocity Profile
    axes[0, 1].set_title("Velocity Profile v(t)", color="#cdd6f4", fontweight="bold")
    axes[0, 1].plot(t_bezier, v_bezier, "--", color="#f38ba8", label="Bézier (Symmetric)", lw=2)
    axes[0, 1].plot(t_stealth, v_stealth, "-", color="#a6e3a1", label="Stealth Mouse (Asymmetric Bell)", lw=2)
    axes[0, 1].set_xlabel("Time (s)", color="#cdd6f4")
    axes[0, 1].set_ylabel("Speed (px/s)", color="#cdd6f4")
    axes[0, 1].legend(facecolor="#1e1e2e", edgecolor="#45475a", labelcolor="#cdd6f4")

    # 3. Time Delta Distribution
    axes[1, 0].set_title("Sampling Interval Delta t (ms)", color="#cdd6f4", fontweight="bold")
    axes[1, 0].plot(np.diff(bezier_path[:, 2]) * 1000, "--", color="#f38ba8", label="Bézier (Zero jitter)", lw=2)
    axes[1, 0].plot(np.diff(stealth_path[:, 2]) * 1000, "-", color="#a6e3a1", label="Stealth Mouse (60-120Hz jitter)", lw=2)
    axes[1, 0].set_ylabel("Interval dt (ms)", color="#cdd6f4")
    axes[1, 0].legend(facecolor="#1e1e2e", edgecolor="#45475a", labelcolor="#cdd6f4")

    # 4. Trajectory Curvature / Micro-variations
    diff_s = np.diff(stealth_path[:, :2], axis=0)
    diff_b = np.diff(bezier_path[:, :2], axis=0)
    axes[1, 1].set_title("Step Displacement dy vs dx", color="#cdd6f4", fontweight="bold")
    axes[1, 1].scatter(diff_b[:, 0], diff_b[:, 1], color="#f38ba8", alpha=0.6, label="Bézier (Artificial regularities)", s=25)
    axes[1, 1].scatter(diff_s[:, 0], diff_s[:, 1], color="#a6e3a1", alpha=0.8, label="Stealth Mouse (Human tremor)", s=25)
    axes[1, 1].legend(facecolor="#1e1e2e", edgecolor="#45475a", labelcolor="#cdd6f4")

    plt.tight_layout()
    out_path = Path("tests/kinematics_comparison.png")
    plt.savefig(out_path, dpi=120, facecolor=fig.get_facecolor())
    plt.close()
    print(f"\n[+] Visual kinematic comparison graph saved to: {out_path.resolve()}")


if __name__ == "__main__":
    unittest.main(exit=False)
    run_visual_benchmark()
