"""
Example and visual verification script for stealth_mouse.

Opens a MAXIMIZED window displaying numbered bullseye targets BEFORE motion begins,
allowing you to inspect the layout and confirm that cursor trajectories land with accuracy.

Includes a '🎲 Generate Random' button (or 'r' hotkey) to generate new random
targets and repeat testing as many times as desired.

Execution:
    python example.py
"""

import time
import random
import threading
import tkinter as tk
from typing import List, Tuple
from main import click


# ==============================================================================
# INITIAL TARGET COORDINATES (Full Screen)
# Modify, add, or remove initial (X, Y) tuples as needed:
# ==============================================================================
INITIAL_TARGETS: List[Tuple[int, int]] = [
    (320, 220),    # Target 1
    (1150, 180),   # Target 2
    (1500, 580),   # Target 3
    (960, 500),    # Target 4
    (480, 750),    # Target 5
    (1300, 820),   # Target 6
]

# Human pause in seconds after hitting each target before navigating to the next
PAUSE_BETWEEN_TARGETS = 0.5


class TargetPracticeApp:
    """Maximized interactive window for visual verification of stealth_mouse."""

    def __init__(self, targets: List[Tuple[int, int]]):
        self.targets = list(targets)
        self.is_running = False

        self.root = tk.Tk()
        self.root.title("STEALTH_MOUSE - Target Practice & Visual Verification")

        # Open window maximized to cover the screen
        self.root.state("zoomed")
        self.root.configure(bg="#11111b")

        # Key bindings for quick shortcuts
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.bind("<q>", lambda e: self.root.destroy())
        self.root.bind("<r>", lambda e: self.on_generate_random_click())

        # Top frame for status bar and button
        self.top_frame = tk.Frame(self.root, bg="#181825", height=65)
        self.top_frame.pack(side=tk.TOP, fill=tk.X)
        self.top_frame.pack_propagate(False)

        # Title and status inside top frame
        self.lbl_title = tk.Label(
            self.top_frame,
            text="STEALTH_MOUSE - TARGET PRACTICE & VISUAL VERIFICATION",
            fg="#cdd6f4",
            bg="#181825",
            font=("Segoe UI", 12, "bold"),
        )
        self.lbl_title.pack(side=tk.TOP, pady=(6, 2))

        self.lbl_status = tk.Label(
            self.top_frame,
            text="Targets ready. Starting trajectory in 3 seconds...",
            fg="#f9e2af",
            bg="#181825",
            font=("Segoe UI", 10),
        )
        self.lbl_status.pack(side=tk.TOP)

        # "Generate Random" button in upper right corner
        self.btn_random = tk.Button(
            self.top_frame,
            text="🎲 Generate Random (r)",
            font=("Segoe UI", 10, "bold"),
            bg="#89b4fa",
            fg="#11111b",
            activebackground="#b4befe",
            activeforeground="#11111b",
            relief="flat",
            padx=14,
            pady=4,
            cursor="hand2",
            command=self.on_generate_random_click,
        )
        self.btn_random.place(relx=0.98, rely=0.5, anchor="e")

        # Main full-screen canvas
        self.canvas = tk.Canvas(
            self.root,
            bg="#11111b",
            highlightthickness=0,
            cursor="crosshair",
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Force update to determine canvas offset relative to monitor
        self.root.update()
        self.offset_x = self.canvas.winfo_rootx()
        self.offset_y = self.canvas.winfo_rooty()

        # Dictionary storing UI visual elements for each target
        self.targets_ui = {}

        # 1. Draw all targets BEFORE starting any movement
        self._draw_all_targets()

    def _clear_targets_canvas(self) -> None:
        """Removes all target graphic elements from the canvas."""
        self.canvas.delete("target_elem")
        self.targets_ui.clear()

    def _draw_all_targets(self) -> None:
        """Draws all numbered bullseyes on screen before cursor movement begins."""
        self._clear_targets_canvas()
        base_radius = 32

        for idx, (screen_x, screen_y) in enumerate(self.targets, start=1):
            # Convert screen coordinate to canvas coordinate
            cx = screen_x - self.offset_x
            cy = screen_y - self.offset_y

            # Outer ring
            c_ext = self.canvas.create_oval(
                cx - base_radius, cy - base_radius, cx + base_radius, cy + base_radius,
                fill="#1e1e2e", outline="#89b4fa", width=2,
                tags="target_elem",
            )
            # Middle ring
            c_med = self.canvas.create_oval(
                cx - base_radius * 0.65, cy - base_radius * 0.65, cx + base_radius * 0.65, cy + base_radius * 0.65,
                fill="#313244", outline="#cdd6f4", width=1.5,
                tags="target_elem",
            )
            # Center bullseye
            c_cen = self.canvas.create_oval(
                cx - base_radius * 0.35, cy - base_radius * 0.35, cx + base_radius * 0.35, cy + base_radius * 0.35,
                fill="#f38ba8", outline="#eba0ac", width=1.5,
                tags="target_elem",
            )
            # Crosshair dashed lines
            self.canvas.create_line(
                cx - base_radius * 1.25, cy, cx + base_radius * 1.25, cy,
                fill="#6c7086", dash=(3, 2),
                tags="target_elem",
            )
            self.canvas.create_line(
                cx, cy - base_radius * 1.25, cx, cy + base_radius * 1.25,
                fill="#6c7086", dash=(3, 2),
                tags="target_elem",
            )

            # Sequence number centered on target
            txt_num = self.canvas.create_text(
                cx, cy,
                text=str(idx),
                fill="#ffffff",
                font=("Segoe UI", 11, "bold"),
                tags="target_elem",
            )

            # Coordinate label below target
            txt_coord = self.canvas.create_text(
                cx, cy + base_radius + 14,
                text=f"Target #{idx} ({screen_x}, {screen_y})",
                fill="#a6adc8",
                font=("Consolas", 9),
                tags="target_elem",
            )

            self.targets_ui[idx] = {
                "cx": cx,
                "cy": cy,
                "c_ext": c_ext,
                "c_med": c_med,
                "c_cen": c_cen,
                "txt_num": txt_num,
                "txt_coord": txt_coord,
                "screen_x": screen_x,
                "screen_y": screen_y,
            }

        self.root.update()

    def mark_active_target(self, idx: int) -> None:
        """Highlights the target that the mouse is currently navigating towards."""
        d = self.targets_ui.get(idx)
        if not d:
            return
        self.canvas.itemconfig(d["c_ext"], outline="#f9e2af", width=3)
        self.lbl_status.config(
            text=f"Moving towards Target #{idx} at ({d['screen_x']}, {d['screen_y']})...",
            fg="#f9e2af",
        )
        self.root.update()

    def mark_hit(self, idx: int) -> None:
        """Changes target color to bright green indicating a successful hit."""
        d = self.targets_ui.get(idx)
        if not d:
            return
        self.canvas.itemconfig(d["c_ext"], outline="#a6e3a1", width=3)
        self.canvas.itemconfig(d["c_cen"], fill="#a6e3a1", outline="#94e2d5")
        self.canvas.itemconfig(d["txt_num"], text="✓", fill="#11111b", font=("Segoe UI", 12, "bold"))
        self.lbl_status.config(
            text=f"Target #{idx} HIT at ({d['screen_x']}, {d['screen_y']})!",
            fg="#a6e3a1",
        )
        self.root.update()

    def _run_thread(self) -> None:
        """Background thread execution to keep the Tkinter UI responsive."""
        self.is_running = True
        self.btn_random.config(state=tk.DISABLED, text="⏳ Moving...", bg="#6c7086")

        # 1. Visible countdown
        for sec in range(3, 0, -1):
            if not self.root.winfo_exists():
                return
            self.lbl_status.config(
                text=f"Targets visible. Starting movement in {sec} s... Release the mouse.",
                fg="#f9e2af",
            )
            self.root.update()
            time.sleep(1.0)

        # 2. Visit each coordinate
        for idx, (sx, sy) in enumerate(self.targets, start=1):
            if not self.root.winfo_exists():
                return

            self.mark_active_target(idx)

            # Move and perform human click
            click(sx, sy)

            self.mark_hit(idx)
            time.sleep(PAUSE_BETWEEN_TARGETS)

        # 3. Completion of run
        if self.root.winfo_exists():
            self.lbl_status.config(
                text=f"RUN COMPLETED! All {len(self.targets)} targets hit. Click 'Generate Random' for another round.",
                fg="#a6e3a1",
            )
            self.btn_random.config(state=tk.NORMAL, text="🎲 Generate Random (r)", bg="#89b4fa")
            self.is_running = False

    def start_run_async(self) -> None:
        """Starts movement in an independent background thread."""
        if self.is_running:
            return
        threading.Thread(target=self._run_thread, daemon=True).start()

    def on_generate_random_click(self) -> None:
        """Generates a fresh set of random targets and starts a new test run."""
        if self.is_running:
            return

        width = self.root.winfo_width()
        height = self.root.winfo_height()

        # Margins to prevent targets from clipping edges or top bar
        min_x = self.offset_x + 100
        max_x = self.offset_x + width - 100
        min_y = self.offset_y + 110
        max_y = self.offset_y + height - 100

        # Generate 5 to 7 well-distributed targets
        num_points = random.randint(5, 7)
        new_targets: List[Tuple[int, int]] = []

        attempts = 0
        while len(new_targets) < num_points and attempts < 200:
            attempts += 1
            rx = random.randint(min_x, max_x)
            ry = random.randint(min_y, max_y)

            # Ensure minimum separation of 180 px between targets
            overlap = False
            for px, py in new_targets:
                if ((rx - px) ** 2 + (ry - py) ** 2) ** 0.5 < 180:
                    overlap = True
                    break

            if not overlap:
                new_targets.append((rx, ry))

        # Relax constraint if random generation couldn't reach 5 targets
        while len(new_targets) < 5:
            new_targets.append((random.randint(min_x, max_x), random.randint(min_y, max_y)))

        self.targets = new_targets
        self._draw_all_targets()

        print(f"\n[Random] Generated {len(self.targets)} new targets:")
        for i, (x, y) in enumerate(self.targets, start=1):
            print(f"  * Target #{i} -> ({x}, {y})")

        self.start_run_async()

    def run(self) -> None:
        """Starts the Tkinter mainloop."""
        self.root.after(300, self.start_run_async)
        self.root.mainloop()


def main():
    print("=" * 70)
    print("  STEALTH_MOUSE - Continuous Target Verification")
    print("=" * 70)
    print(f"  Initial targets   : {len(INITIAL_TARGETS)} bullseyes")
    print("  * On-screen button: '🎲 Generate Random'")
    print("  * Keyboard shortcut: Press 'r' to generate new targets")
    print("  * Exit            : Press 'Esc' or 'q'")
    print("=" * 70)

    app = TargetPracticeApp(INITIAL_TARGETS)
    app.run()


if __name__ == "__main__":
    main()
