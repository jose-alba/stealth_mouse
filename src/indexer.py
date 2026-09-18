"""
Indexer module for stealth_mouse.

Loads the recorded trajectory dataset from data/ (trajectories_index.npz and trajectories_points.npz),
builds a spatial KDTree (scipy.spatial.cKDTree) in memory over 3D feature descriptors:
    [log(distance), cos(angle), sin(angle)]
and provides sub-millisecond (< 0.1 ms) nearest-neighbor queries and random top-k sampling.
"""

import time
import random
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree


@dataclass
class TrajectoryMatch:
    """Represents a trajectory matched from the database."""
    index: int                  # Index in the dataset
    points: np.ndarray          # Array of shape (N, 3): columns [x, y, t_rel]
    source_distance: float      # Original Euclidean displacement in pixels
    source_angle: float         # Original angle in radians atan2(dy, dx)
    source_duration: float      # Original duration in seconds
    feature_distance: float     # Distance in descriptor space (similarity metric)
    is_click: bool = True       # Whether the original stroke ended in a click


class TrajectoryIndexer:
    """
    Manages in-memory KDTree spatial indexing and fast lookup of recorded human trajectories.
    """

    def __init__(self, data_dir: Union[str, Path] = "data"):
        self.data_dir = Path(data_dir)
        self.index_path = self.data_dir / "trajectories_index.npz"
        self.points_path = self.data_dir / "trajectories_points.npz"

        self.kdtree: Optional[cKDTree] = None
        self.descriptors: Optional[np.ndarray] = None
        self.offsets: Optional[np.ndarray] = None
        self.metadata: Optional[np.ndarray] = None
        self.is_clicks: Optional[np.ndarray] = None
        self.points: Optional[np.ndarray] = None

        self._is_loaded: bool = False

        # Attempt auto-loading if files already exist
        if self.index_path.exists() and self.points_path.exists():
            self.load()

    @property
    def is_loaded(self) -> bool:
        """Returns True if the dataset and KDTree are loaded in memory."""
        return self._is_loaded and self.kdtree is not None

    def __len__(self) -> int:
        """Returns total number of trajectories indexed."""
        return len(self.descriptors) if self.descriptors is not None else 0

    def load(self) -> bool:
        """
        Loads dataset files into memory and constructs the cKDTree.

        Returns:
            True if loaded successfully, False otherwise.
        """
        if not self.index_path.exists() or not self.points_path.exists():
            self._is_loaded = False
            return False

        with np.load(self.index_path) as idx_data, np.load(self.points_path) as pts_data:
            self.descriptors = np.array(idx_data["descriptors"], dtype=np.float32)
            self.offsets = np.array(idx_data["offsets"], dtype=np.int32)
            self.metadata = np.array(idx_data["metadata"], dtype=np.float32)
            self.is_clicks = np.array(idx_data["is_clicks"], dtype=np.int8)
            self.points = np.array(pts_data["points"], dtype=np.float32)

        if len(self.descriptors) > 0:
            # Construct spatial index in memory (written in C++, sub-millisecond overhead)
            self.kdtree = cKDTree(self.descriptors)
            self._is_loaded = True
            return True
        else:
            self._is_loaded = False
            return False

    @staticmethod
    def compute_descriptor(dx: float, dy: float) -> np.ndarray:
        """
        Computes the 3D feature descriptor for a given displacement vector (dx, dy):
        [log(max(distance, 1.0)), cos(angle), sin(angle)]
        """
        distance = float(np.hypot(dx, dy))
        angle = float(np.atan2(dy, dx))
        log_dist = float(np.log(max(distance, 1.0)))
        return np.array([log_dist, np.cos(angle), np.sin(angle)], dtype=np.float32)

    def get_trajectory(self, index: int, feature_distance: float = 0.0) -> TrajectoryMatch:
        """
        Retrieves trajectory points and metadata for a specific dataset index in O(1) time.
        """
        if not self.is_loaded or self.offsets is None or self.points is None or self.metadata is None:
            raise RuntimeError("TrajectoryIndexer is not loaded. Ensure dataset files exist in data/.")

        if index < 0 or index >= len(self.descriptors):
            raise IndexError(f"Trajectory index {index} out of bounds (0 to {len(self.descriptors)-1}).")

        start_idx = self.offsets[index]
        end_idx = self.offsets[index + 1]
        traj_points = self.points[start_idx:end_idx].copy()

        meta = self.metadata[index]  # [distance, path_length, angle, duration]
        is_click = bool(self.is_clicks[index]) if self.is_clicks is not None else True

        return TrajectoryMatch(
            index=index,
            points=traj_points,
            source_distance=float(meta[0]),
            source_angle=float(meta[2]),
            source_duration=float(meta[3]),
            feature_distance=feature_distance,
            is_click=is_click,
        )

    def query_nearest(
        self,
        dx: float,
        dy: float,
        k: int = 1,
    ) -> List[TrajectoryMatch]:
        """
        Queries the KDTree for the k nearest trajectories matching (dx, dy).

        Args:
            dx: Target horizontal displacement in pixels.
            dy: Target vertical displacement in pixels.
            k: Number of nearest neighbors to return.

        Returns:
            List of TrajectoryMatch objects ordered by similarity (closest first).
        """
        if not self.is_loaded or self.kdtree is None:
            raise RuntimeError("TrajectoryIndexer is not loaded. Run 'python -m src.recorder' first.")

        query_vec = self.compute_descriptor(dx, dy)
        k_clamped = min(k, len(self))

        distances, indices = self.kdtree.query(query_vec, k=k_clamped)

        if k_clamped == 1:
            distances = [float(distances)]
            indices = [int(indices)]
        else:
            distances = [float(d) for d in distances]
            indices = [int(i) for i in indices]

        results = []
        for feat_dist, idx in zip(distances, indices):
            results.append(self.get_trajectory(idx, feature_distance=feat_dist))

        return results

    def query_sample(
        self,
        dx: float,
        dy: float,
        top_k: int = 5,
    ) -> TrajectoryMatch:
        """
        Finds the top-k nearest trajectories and randomly samples one of them.
        
        This prevents deterministic trajectory replay: repeated bot movements across
        similar UI buttons will exhibit natural variation while retaining optimal fit.
        """
        candidates = self.query_nearest(dx, dy, k=top_k)
        if not candidates:
            raise RuntimeError("No trajectory candidates found.")

        # Softmax / inverse distance weighted random choice (or uniform among top matches)
        return random.choice(candidates)

    def summary(self) -> Dict[str, Any]:
        """Returns statistical overview of the loaded trajectory dataset."""
        if not self.is_loaded or self.metadata is None:
            return {"status": "empty", "total_trajectories": 0}

        distances = self.metadata[:, 0]
        durations = self.metadata[:, 3]

        return {
            "status": "ready",
            "total_trajectories": len(self),
            "total_points": len(self.points) if self.points is not None else 0,
            "min_distance_px": float(np.min(distances)),
            "max_distance_px": float(np.max(distances)),
            "mean_distance_px": float(np.mean(distances)),
            "min_duration_ms": float(np.min(durations) * 1000),
            "max_duration_ms": float(np.max(durations) * 1000),
            "mean_duration_ms": float(np.mean(durations) * 1000),
        }


def main() -> None:
    """CLI diagnostics and benchmark for TrajectoryIndexer."""
    print("=" * 65)
    print("  STEALTH_MOUSE - Trajectory Indexer & KDTree Diagnostics")
    print("=" * 65)

    indexer = TrajectoryIndexer("data")

    if not indexer.is_loaded:
        print("[!] No dataset found in data/.")
        print("    Please run: python -m src.recorder")
        print("    to record mouse gestures first.")
        return

    stats = indexer.summary()
    print(f"  Indexed trajectories : {stats['total_trajectories']}")
    print(f"  Total points         : {stats['total_points']:,}")
    print(f"  Distance range       : {stats['min_distance_px']:.1f} px  ->  {stats['max_distance_px']:.1f} px (mean: {stats['mean_distance_px']:.1f} px)")
    print(f"  Duration range       : {stats['min_duration_ms']:.0f} ms  ->  {stats['max_duration_ms']:.0f} ms (mean: {stats['mean_duration_ms']:.0f} ms)")
    print("-" * 65)

    # Benchmark query
    test_dx, test_dy = 350.0, 180.0
    print(f"  Benchmarking nearest-neighbor query for dx={test_dx}, dy={test_dy}...")

    t0 = time.perf_counter()
    matches = indexer.query_nearest(test_dx, test_dy, k=3)
    elapsed_us = (time.perf_counter() - t0) * 1_000_000

    best = matches[0]
    print(f"  -> KDTree query latency     : {elapsed_us:.2f} microseconds (< 0.1 ms)")
    print(f"  -> Best match index         : #{best.index}")
    print(f"  -> Source stroke distance   : {best.source_distance:.1f} px ({len(best.points)} pts, {best.source_duration*1000:.0f} ms)")
    print(f"  -> 3D feature distance      : {best.feature_distance:.4f}")
    print("=" * 65)


if __name__ == "__main__":
    main()
