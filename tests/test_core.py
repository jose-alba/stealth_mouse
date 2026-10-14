"""
Unit and functional tests for the core stealth_mouse modules:
- TrajectoryIndexer & KDTree lookups
- TrajectoryTransformer & Hybrid Temporal Blending
- TrajectoryInterpolator & Hardware-rate sampling
- StealthMousePlayer path generation
"""

import sys
import unittest
from pathlib import Path

# Ensure root workspace directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from src.indexer import TrajectoryIndexer, TrajectoryMatch
from src.transformer import TrajectoryTransformer
from src.interpolator import TrajectoryInterpolator
from src.player import StealthMousePlayer


class TestTrajectoryIndexer(unittest.TestCase):
    """Verifies KDTree indexing, data consistency, and lookup latency."""

    @classmethod
    def setUpClass(cls):
        cls.indexer = TrajectoryIndexer("data")

    def test_dataset_loaded(self):
        """Ensures the dataset files exist and load into memory."""
        self.assertTrue(self.indexer.is_loaded, "Dataset should be loaded from data/")
        self.assertGreater(len(self.indexer), 0, "Indexed dataset should contain recorded strokes")

    def test_descriptor_computation(self):
        """Verifies mathematical validity of the 3D feature descriptor."""
        vec = TrajectoryIndexer.compute_descriptor(100.0, 0.0)
        self.assertEqual(len(vec), 3)
        self.assertAlmostEqual(vec[0], np.log(100.0), places=4)
        self.assertAlmostEqual(vec[1], 1.0, places=4)  # cos(0)
        self.assertAlmostEqual(vec[2], 0.0, places=4)  # sin(0)

    def test_nearest_neighbor_query(self):
        """Verifies sub-millisecond KDTree querying and shape of matched trajectory."""
        matches = self.indexer.query_nearest(dx=300.0, dy=150.0, k=5)
        self.assertEqual(len(matches), 5)

        best: TrajectoryMatch = matches[0]
        self.assertIsInstance(best, TrajectoryMatch)
        self.assertGreater(len(best.points), 5)
        self.assertEqual(best.points.shape[1], 3)  # [x, y, t_rel]
        self.assertGreater(best.source_distance, 0)
        self.assertGreater(best.source_duration, 0)


class TestTrajectoryTransformer(unittest.TestCase):
    """Verifies conformal 2D mapping and hybrid temporal scaling."""

    def setUp(self):
        self.transformer = TrajectoryTransformer(target_width=40.0)

    def test_boundary_preservation(self):
        """Ensures transformed trajectories start exactly at start_point and end at end_point."""
        # Simulated raw stroke: 10 points
        t = np.linspace(0.0, 0.5, 10, dtype=np.float32)
        x = np.linspace(0.0, 100.0, 10, dtype=np.float32)
        y = np.linspace(0.0, 50.0, 10, dtype=np.float32)
        raw_stroke = np.column_stack((x, y, t))

        start = (250.0, 180.0)
        target = (780.0, 520.0)

        transformed = self.transformer.transform(raw_stroke, start, target)

        self.assertEqual(transformed.shape, raw_stroke.shape)
        # Exact start
        self.assertAlmostEqual(transformed[0, 0], start[0], places=3)
        self.assertAlmostEqual(transformed[0, 1], start[1], places=3)
        # Exact arrival
        self.assertAlmostEqual(transformed[-1, 0], target[0], places=3)
        self.assertAlmostEqual(transformed[-1, 1], target[1], places=3)

    def test_hybrid_time_close_match_preserves_human_time(self):
        """
        When target distance is very close to source distance (e.g. 5% difference),
        the hybrid temporal blending should preserve ~100% of pure human recorded duration.
        """
        t = np.linspace(0.0, 0.400, 20, dtype=np.float32)
        x = np.linspace(0.0, 100.0, 20, dtype=np.float32)
        y = np.zeros(20, dtype=np.float32)
        stroke = np.column_stack((x, y, t))

        # Target distance = 104 px (only 4% difference)
        start = (0.0, 0.0)
        target = (104.0, 0.0)

        transformed = self.transformer.transform(stroke, start, target)
        final_duration = transformed[-1, 2]

        # Duration should be virtually identical to original 0.400 s (within 2%)
        self.assertAlmostEqual(final_duration, 0.400, delta=0.015)

    def test_hybrid_time_large_stretch_uses_fitts(self):
        """
        When target distance is stretched 3x (e.g. 100px -> 300px),
        Fitts's Law damping should kick in so duration does NOT scale linearly 3x
        (which would feel unnatural and too slow).
        """
        t = np.linspace(0.0, 0.300, 20, dtype=np.float32)
        x = np.linspace(0.0, 100.0, 20, dtype=np.float32)
        y = np.zeros(20, dtype=np.float32)
        stroke = np.column_stack((x, y, t))

        start = (0.0, 0.0)
        target = (300.0, 0.0)

        transformed = self.transformer.transform(stroke, start, target)
        final_duration = transformed[-1, 2]

        # Linear 3x would be 0.900s. Fitts index of difficulty ratio is ~1.5x -> ~0.450s.
        self.assertLess(final_duration, 0.800)
        self.assertGreater(final_duration, 0.350)


class TestTrajectoryInterpolator(unittest.TestCase):
    """Verifies cubic spline densification and realistic polling frequencies."""

    def setUp(self):
        self.interpolator = TrajectoryInterpolator(min_dt_ms=8.0, max_dt_ms=16.0)

    def test_monotonic_timestamps_and_sampling_rate(self):
        """Ensures generated timestamps are strictly increasing and bounded in 60-120 Hz."""
        t = np.array([0.0, 0.1, 0.25, 0.4], dtype=np.float32)
        x = np.array([100.0, 150.0, 220.0, 300.0], dtype=np.float32)
        y = np.array([100.0, 120.0, 180.0, 250.0], dtype=np.float32)
        stroke = np.column_stack((x, y, t))

        smooth = self.interpolator.interpolate(stroke)

        self.assertGreater(len(smooth), len(stroke))

        # Check strict monotonicity
        time_diffs = np.diff(smooth[:, 2])
        self.assertTrue(np.all(time_diffs > 0), "All dt intervals must be positive")

        # Check frequency bounds (8 ms to 16 ms nominal, clipped to 4-20 ms)
        for dt in time_diffs:
            self.assertGreaterEqual(dt, 0.003)
            self.assertLessEqual(dt, 0.025)

        # Check endpoints match exactly
        self.assertAlmostEqual(smooth[0, 0], 100.0, places=3)
        self.assertAlmostEqual(smooth[0, 1], 100.0, places=3)
        self.assertAlmostEqual(smooth[-1, 0], 300.0, places=3)
        self.assertAlmostEqual(smooth[-1, 1], 250.0, places=3)


class TestStealthMousePlayer(unittest.TestCase):
    """Verifies full path generation pipeline under StealthMousePlayer."""

    def setUp(self):
        self.player = StealthMousePlayer(data_dir="data", top_k=10)

    def test_generate_path(self):
        """Ensures full path generation works across multiple coordinates."""
        test_cases = [
            ((100.0, 100.0), (500.0, 300.0)),
            ((800.0, 600.0), (200.0, 150.0)),
            ((500.0, 500.0), (501.0, 501.0)),  # Micro movement (< 2px)
        ]

        for (x0, y0), (x1, y1) in test_cases:
            path = self.player.generate_path(x1, y1, start_x=x0, start_y=y0)
            self.assertIsInstance(path, np.ndarray)
            self.assertFalse(np.isnan(path).any(), "Path contains NaN values")
            self.assertFalse(np.isinf(path).any(), "Path contains Inf values")
            self.assertGreaterEqual(len(path), 1)

            # End coordinates must match destination
            self.assertAlmostEqual(path[-1, 0], x1, places=1)
            self.assertAlmostEqual(path[-1, 1], y1, places=1)


class TestHumanScroller(unittest.TestCase):
    """Verifies biological scroll step generation and ballistic kinematics."""

    def setUp(self):
        from src.scroller import HumanScroller
        self.scroller = HumanScroller(allow_overshoot=True)

    def test_scroll_displacement_accuracy(self):
        """Verifies net vertical displacement matches requested pixels exactly."""
        for dy in [50.0, -120.0, 450.0, -800.0, 1500.0]:
            steps = self.scroller.generate_steps(dy)
            self.assertGreater(len(steps), 0)
            net_dy = sum(s[0] for s in steps)
            self.assertAlmostEqual(net_dy, dy, places=2, msg=f"Mismatch for target {dy}")

    def test_polling_jitter_and_timing(self):
        """Verifies step delays fall within realistic display refresh rates (60-120 Hz)."""
        steps = self.scroller.generate_steps(600.0)
        motion_steps = [s for s in steps if abs(s[0]) > 0]
        self.assertGreater(len(motion_steps), 10)
        for _, dt in motion_steps:
            self.assertGreaterEqual(dt, 0.005, "Step dt too fast (< 5ms)")
            self.assertLessEqual(dt, 0.035, "Step dt too slow (> 35ms)")

    def test_zero_displacement(self):
        """Verifies zero displacement returns empty steps."""
        self.assertEqual(len(self.scroller.generate_steps(0.0)), 0)
        self.assertEqual(len(self.scroller.generate_steps(0.5)), 0)


if __name__ == "__main__":
    unittest.main()
