"""
Recorder module for stealth_mouse.

Captures mouse coordinates and timestamps using OS-level hooks at high frequency (125-250+ Hz).
Segments strokes between clicks, prunes idle pauses, and saves clean trajectory datasets
into the data/ directory in compressed NumPy (.npz) format.
"""

import sys
import time
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field

import numpy as np
from pynput import mouse, keyboard


@dataclass
class Trajectory:
    """Represents a single recorded mouse trajectory segment."""
    points: np.ndarray  # Shape (N, 3): columns [x, y, t_rel]
    distance: float     # Euclidean distance between start and end point (px)
    path_length: float  # Cumulative trajectory length (px)
    angle: float        # Direction angle in radians atan2(dy, dx)
    duration: float     # Total duration in seconds
    is_click: bool      # True if the trajectory ended with a mouse click
    button: Optional[str] = None  # Mouse button clicked ('left', 'right', 'middle', or None)

    @property
    def descriptor(self) -> np.ndarray:
        """
        3D feature vector for KDTree indexing:
        [log(distance), cos(angle), sin(angle)]
        """
        log_dist = float(np.log(max(self.distance, 1.0)))
        return np.array([log_dist, np.cos(self.angle), np.sin(self.angle)], dtype=np.float32)


class MouseRecorder:
    """
    High-frequency mouse trajectory recorder.
    
    Captures mouse movements via OS hooks, segments continuous movements,
    filters dead pauses, and persists clean trajectory datasets.
    """

    def __init__(
        self,
        output_dir: str = "data",
        min_distance: float = 15.0,
        min_points: int = 8,
        min_duration: float = 0.04,
        pause_threshold: float = 0.35,
    ):
        """
        Args:
            output_dir: Directory where recordings will be saved.
            min_distance: Minimum euclidean distance (pixels) to qualify as a stroke.
            min_points: Minimum number of captured points required.
            min_duration: Minimum duration in seconds (40 ms).
            pause_threshold: Max idle time (seconds) before splitting a stroke.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.min_distance = min_distance
        self.min_points = min_points
        self.min_duration = min_duration
        self.pause_threshold = pause_threshold

        self.trajectories: List[Trajectory] = []
        self._current_points: List[Tuple[float, float, float]] = []
        self._last_event_time: float = 0.0

        self._mouse_listener: Optional[mouse.Listener] = None
        self._keyboard_listener: Optional[keyboard.Listener] = None
        self._is_recording: bool = False
        self._is_paused: bool = False

        # Live stats
        self.total_events_captured: int = 0
        self.start_wall_time: float = 0.0

    def _finalize_current_stroke(
        self,
        is_click: bool = False,
        button: Optional[str] = None
    ) -> Optional[Trajectory]:
        """Validates and finalizes the active point buffer into a Trajectory object."""
        if len(self._current_points) < self.min_points:
            self._current_points.clear()
            return None

        arr = np.array(self._current_points, dtype=np.float64)
        x = arr[:, 0]
        y = arr[:, 1]
        t = arr[:, 2]

        dx = float(x[-1] - x[0])
        dy = float(y[-1] - y[0])
        distance = float(np.hypot(dx, dy))

        # Check path length
        diffs = np.diff(arr[:, :2], axis=0)
        path_length = float(np.sum(np.hypot(diffs[:, 0], diffs[:, 1])))

        duration = float(t[-1] - t[0])

        # Validate trajectory thresholds
        if distance < self.min_distance or path_length < self.min_distance or duration < self.min_duration:
            self._current_points.clear()
            return None

        # Normalize timestamps relative to start (t0 = 0.0)
        t_rel = t - t[0]
        traj_points = np.column_stack((x, y, t_rel)).astype(np.float32)
        angle = float(np.atan2(dy, dx))

        traj = Trajectory(
            points=traj_points,
            distance=distance,
            path_length=path_length,
            angle=angle,
            duration=duration,
            is_click=is_click,
            button=button,
        )

        self.trajectories.append(traj)
        self._current_points.clear()
        return traj

    def _on_move(self, x: int, y: int) -> None:
        """Callback for mouse move events."""
        if not self._is_recording or self._is_paused:
            return

        now = time.perf_counter()
        self.total_events_captured += 1

        # Check for idle pause inside the movement
        if self._current_points:
            time_gap = now - self._last_event_time
            if time_gap > self.pause_threshold:
                # Idle pause detected: finalize the preceding stroke and start fresh
                self._finalize_current_stroke(is_click=False)

        self._current_points.append((float(x), float(y), now))
        self._last_event_time = now

    def _on_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        """Callback for mouse click events."""
        if not self._is_recording or self._is_paused:
            return

        now = time.perf_counter()
        self.total_events_captured += 1

        if pressed:
            # Mouse button pressed down: indicates arrival at target
            self._current_points.append((float(x), float(y), now))
            btn_name = button.name if hasattr(button, "name") else str(button)
            traj = self._finalize_current_stroke(is_click=True, button=btn_name)
            if traj:
                print(
                    f"\r[Stroke #{len(self.trajectories)}] "
                    f"Dist: {traj.distance:6.1f}px | "
                    f"Time: {traj.duration*1000:5.0f}ms | "
                    f"Pts: {len(traj.points):3d} | "
                    f"Click: {btn_name:<6}",
                    end="",
                    flush=True,
                )
        else:
            # Mouse button released: prepare start of next movement
            self._current_points.append((float(x), float(y), now))
            self._last_event_time = now

    def _on_key_press(self, key: Any) -> None:
        """Callback for keyboard events to toggle pause or finish."""
        try:
            if key == keyboard.Key.esc or (hasattr(key, "char") and key.char == "q"):
                print("\n[Stop signal received from keyboard]")
                self.stop()
            elif hasattr(key, "char") and key.char == "p":
                self._is_paused = not self._is_paused
                state = "PAUSED" if self._is_paused else "RESUMED"
                print(f"\n[Recording {state}]")
        except Exception:
            pass

    def start(self, non_blocking: bool = False) -> None:
        """
        Starts listening to OS mouse and keyboard events.
        
        Args:
            non_blocking: If True, returns immediately. If False, blocks until stopped.
        """
        self._is_recording = True
        self._is_paused = False
        self._current_points.clear()
        self.start_wall_time = time.time()
        self._last_event_time = time.perf_counter()

        self._mouse_listener = mouse.Listener(
            on_move=self._on_move,
            on_click=self._on_click,
        )
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
        )

        self._mouse_listener.start()
        self._keyboard_listener.start()

        if not non_blocking:
            try:
                while self._is_recording:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print("\n[Stop signal received: Ctrl+C]")
                self.stop()

    def stop(self) -> None:
        """Stops the recorder and tears down hooks."""
        if not self._is_recording:
            return

        self._is_recording = False

        # Finalize any pending points
        self._finalize_current_stroke(is_click=False)

        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None

        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener = None

    def save(self) -> Tuple[Path, Path]:
        """
        Saves or appends all valid recorded trajectories into two complementary files in data/:
          1. data/trajectories_index.npz  -> Descriptors [log(dist), cos(angle), sin(angle)], metadata, and offsets
          2. data/trajectories_points.npz -> Continuous raw points [x, y, t_rel] accessed by offset index
        """
        index_file = self.output_dir / "trajectories_index.npz"
        points_file = self.output_dir / "trajectories_points.npz"

        if not self.trajectories:
            print("\n[Notice] No new valid strokes captured.")
            return index_file, points_file

        # Check if existing dataset files already exist to accumulate
        existing_coords: List[np.ndarray] = []
        existing_descriptors: List[np.ndarray] = []
        existing_metadata: List[np.ndarray] = []
        existing_is_clicks: List[int] = []

        if index_file.exists() and points_file.exists():
            try:
                with np.load(index_file) as idx_data, np.load(points_file) as pts_data:
                    old_coords = pts_data["points"]
                    old_offsets = idx_data["offsets"]
                    old_descriptors = idx_data["descriptors"]
                    old_metadata = idx_data["metadata"]
                    old_is_clicks = idx_data["is_clicks"]

                    # Extract each existing trajectory to cleanly re-index offsets
                    for i in range(len(old_offsets) - 1):
                        s, e = old_offsets[i], old_offsets[i + 1]
                        existing_coords.append(old_coords[s:e])
                        existing_descriptors.append(old_descriptors[i])
                        existing_metadata.append(old_metadata[i])
                        existing_is_clicks.append(old_is_clicks[i])
            except Exception as e:
                print(f"[Notice] Could not read previous dataset ({e}), creating a fresh one.")
                existing_coords.clear()
                existing_descriptors.clear()
                existing_metadata.clear()
                existing_is_clicks.clear()

        # Append new trajectories
        all_coords = list(existing_coords)
        all_descriptors = list(existing_descriptors)
        all_metadata = list(existing_metadata)
        all_is_clicks = list(existing_is_clicks)

        for traj in self.trajectories:
            all_coords.append(traj.points)
            all_descriptors.append(traj.descriptor)
            all_metadata.append([traj.distance, traj.path_length, traj.angle, traj.duration])
            all_is_clicks.append(1 if traj.is_click else 0)

        # Build contiguous offsets
        offsets = [0]
        for c in all_coords:
            offsets.append(offsets[-1] + len(c))

        coords_array = np.vstack(all_coords).astype(np.float32)
        offsets_array = np.array(offsets, dtype=np.int32)
        descriptors_array = np.vstack(all_descriptors).astype(np.float32)
        metadata_array = np.array(all_metadata, dtype=np.float32)
        is_clicks_array = np.array(all_is_clicks, dtype=np.int8)

        # 1. Save KDTree index file (descriptors + offsets + metadata)
        np.savez_compressed(
            index_file,
            descriptors=descriptors_array,
            offsets=offsets_array,
            metadata=metadata_array,
            is_clicks=is_clicks_array,
        )

        # 2. Save contiguous coordinates bank
        np.savez_compressed(
            points_file,
            points=coords_array,
        )

        prev_count = len(existing_descriptors)
        new_count = len(self.trajectories)
        total_count = len(descriptors_array)

        print("\n" + "=" * 65)
        print("  DATASET SAVED SUCCESSFULLY TO DATA/")
        print("=" * 65)
        print(f"  1. KDTree Index    : {index_file.name} ({index_file.stat().st_size / 1024:.1f} KB)")
        print(f"  2. Coordinate Bank : {points_file.name} ({points_file.stat().st_size / 1024:.1f} KB)")
        print("-" * 65)
        print(f"  Previous strokes   : {prev_count}")
        print(f"  New strokes added  : {new_count}")
        print(f"  TOTAL accumulated  : {total_count} strokes ({len(coords_array):,} points)")
        print("=" * 65)

        return index_file, points_file


def main() -> None:
    """
    Console entrypoint to record human mouse gestures.
    Usage: python -m src.recorder
    """
    output_dir = Path("data")
    index_file = output_dir / "trajectories_index.npz"
    points_file = output_dir / "trajectories_points.npz"

    total_existing = 0
    if index_file.exists() and points_file.exists():
        try:
            with np.load(index_file) as idx_data:
                total_existing = len(idx_data["descriptors"])
        except Exception:
            total_existing = 0

    print("=" * 65)
    print("  STEALTH_MOUSE - Human Trajectory Recorder")
    print("=" * 65)
    print(f"  Destination in data/ : {index_file.name}  and  {points_file.name}")
    print(f"  Accumulated strokes  : {total_existing}")
    print("-" * 65)
    print("  INSTRUCTIONS:")
    print("  * Use your mouse naturally (browse, click, navigate, etc.)")
    print("  * Press 'p' to pause / resume")
    print("  * Press 'Esc', 'q', or Ctrl+C to stop and save")
    print("=" * 65)
    print("Starting capture... Move your mouse and click naturally:\n")

    recorder = MouseRecorder(output_dir="data")

    try:
        recorder.start(non_blocking=False)
    finally:
        recorder.save()


if __name__ == "__main__":
    main()

