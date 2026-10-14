# Stealth Mouse

Human-like mouse trajectory generation and conformal transformation designed for modern anti-bot evasion (Cloudflare Turnstile, DataDome, Kasada, Akamai).

<p align="center">
  <img src="demo.gif" alt="Stealth Mouse Pipeline Animation" width="100%">
</p>

Instead of generating synthetic mathematical curves (such as Bézier or Perlin noise, which lack natural physiological tremor and exhibit detectable statistical regularities), **Stealth Mouse** retrieves real recorded human gestures and applies conformal transformations to fit arbitrary target coordinates while preserving micro-corrections and biomechanical kinematics.

---

## 1. Record Dataset (Recorder)

Record your own daily mouse movements to populate or expand your database:

```bash
python -m src.recorder
```

* **Save & Exit:** Press `Ctrl` + `C` + `P` simultaneously.

Strokes are automatically segmented click-to-click, idle dead pauses are discarded, and data is accumulated into two complementary files in `data/`:
1. `data/trajectories_index.npz`: 3D descriptors `[log(d), cos(θ), sin(θ)]` and offsets for the KDTree.
2. `data/trajectories_points.npz`: Contiguous high-frequency coordinate bank `[x, y, t]` accessed in $O(1)$ time.

---

## 2. Minimalist Public API (`move`, `click`, `scroll`, `drag`)

### Python API:

```python
from main import move, click, scroll, drag

# 1. Moves cursor from its current position to (x, y) with human kinematics
move(800, 450)

# 2. Moves to (x, y), performs pre-click hesitation, and clicks with human dwell time
click(800, 450)                  # Defaults to left click
click(800, 450, button="right")  # Right click

# 3. Biological scrolling with multi-flick bursts, friction decay, and rebound
scroll(600)   # Scrolls down 600px
scroll(-300)  # Scrolls up 300px

# 4. Realistic human drag-and-drop (captcha sliders, puzzle pieces, canvas)
drag(800, 450)                                # Drag from current cursor position
drag(800, 450, start_x=200, start_y=450)     # Drag from (200, 450) to (800, 450)
```

### Direct CLI Usage:

```bash
python main.py 800 450
python main.py click 800 450
python main.py click 800 450 right
python main.py scroll 600
python main.py drag 200 450 800 450
```

---

## 3. Interactive Visual Verification

To verify that the cursor moves realistically and hits coordinates with pin-point accuracy, launch the maximized visual target range:

```bash
python example.py
```

* **Pre-rendered numbered bullseyes:** Targets appear on screen **before** motion begins so you can verify accuracy.
* **Random rounds:** Click the **`🎲 Generate Random`** button (or press `r`) to generate new non-overlapping targets on the fly.

---

## 4. Architecture & How It Works

```mermaid
graph TD
    UserReq["Call: move(target_x, target_y)"] --> ReadPos["Read current mouse position (x0, y0)"]
    ReadPos --> Compute["Compute displacement vector & 3D descriptor"]
    Compute --> KDTree["Query cKDTree (< 0.1 ms) and retrieve top 10 matches"]
    KDTree --> RandomPick["Sample 1 random candidate (anti-deterministic replay)"]
    RandomPick --> Transform["2D Conformal Transform + Hybrid Timing Adaptation"]
    Transform --> Spline["Generate continuous Cubic Spline"]
    Spline --> TimeSample["Sample at 60-120 Hz with temporal micro-jitter"]
    TimeSample --> Dispatch["Dispatch hardware-level events with isTrusted: true"]
```

### Key Technical Innovations:

1. **3D Spatial Descriptor:** Each stroke is indexed as $[\log(\text{distance}),\ \cos(\theta),\ \sin(\theta)]$. Using $(\cos,\sin)$ eliminates periodic angular discontinuity ($0^\circ \leftrightarrow 360^\circ$), while $\log(\text{distance})$ ensures scale-invariant proportional matching.
2. **Hybrid Temporal Adaptation:**
   * **Close matches ($<15\%$ distance difference):** Uses **100% pure human recorded time**, without synthetic formulas.
   * **Large stretches ($2\times, 3\times$ distance disparity):** Applies smooth exponential damping via **Fitts's Law** ($MT \propto \log_2(1 + D/W)$) to prevent hyperspeed or slow-motion artifacts.
3. **Continuous Spline Densification:** Evaluates coordinates at realistic display refresh rates (60–120 Hz / 8–16 ms intervals) with subtle temporal jitter, replicating native hardware polling.
4. **Browser & Native OS Ready:** Compatible with native desktop automation (`pynput`) as well as headless/stealth browser frameworks (`Playwright` / CDP) with `isTrusted: true` event dispatch.

---

## 5. Testing & Verification Suite

A complete verification suite is provided under [`tests/`](file:///d:/stealth_mouse/tests) to mathematically and functionally prove anti-bot evasion properties:

```bash
# 1. Universal Interactive & Visual Launcher:
python all_tests.py              # Interactive visual menu (options 1 to 7)
python all_tests.py --all        # Runs all 5 visual stages sequentially in real browser
python all_tests.py --fast       # Runs 20 automated tests in background (headless)

# 2. Or run specialized tests directly:
python all_tests.py --recaptcha  # Live Google reCAPTCHA v3 (Score 0.9 evaluation)
python all_tests.py --slider     # Live DataDome / GeeTest biometric slider challenge
python all_tests.py --turnstile  # Live Cloudflare Turnstile challenge
python all_tests.py --sandbox    # Live biometric telemetry dashboard
python all_tests.py --targets    # Desktop full-screen target range

# 3. Direct Pytest runner:
pytest -v tests
```

* **`all_tests.py` / `tests/test_interactive_browser.py`:** Opens a **visible Chromium window (`headless=False`)** to directly watch cursor trajectories in real time:
  * **Google reCAPTCHA v3:** Evaluates live against Google's servers, demonstrating pure human score $\ge 0.7 - 0.9$ without image puzzles.
  * **DataDome / GeeTest Biometric Slider:** Evaluates static breakaway friction delay, $\pm Y$ micro-tremor, and smooth drag physics.
  * **Cloudflare Turnstile:** Navigates to a real Cloudflare challenge and passes with biometric click.
  * **Telemetry Sandbox:** Live biometric scoring dashboard with canvas trail, speed bell curve, and `isTrusted` check.
  * **Desktop Target Range:** Full-screen multi-target bullseye accuracy demonstration.
* **`tests/test_kinematics.py`:** Benchmarks against synthetic Bézier curves, including **FFT spectral analysis** proving the presence of biological neuromuscular tremor (8–14 Hz band) and **stochastic entropy** guaranteeing zero deterministic replay signatures.
* **`tests/test_browser.py`:** Tests headless Playwright integration for `click`, `scroll`, `drag`, and live Google reCAPTCHA v3 scoring.

### Biometric Validation (Synthetic Bézier vs. Stealth Mouse):

<p align="center">
  <img src="tests/kinematics_comparison.png" alt="Kinematic Comparison: Synthetic Bézier vs Stealth Mouse" width="100%">
</p>

* **Velocity Profile $v(t)$:** Bézier curves are unnaturally symmetric, whereas Stealth Mouse exhibits human-like rapid acceleration followed by a prolonged deceleration phase with terminal micro-corrections.
* **Sampling Interval $\Delta t$:** Naive scrapers use fixed delays (zero variance), while Stealth Mouse models authentic hardware polling jitter (60–120 Hz / 8–16 ms).
* **Kinematic Phase Plane:** Anti-bot ML classifiers detect the rigid geometric regularity of Bézier math on $(dx, dy)$ scatter plots, whereas real human tremor displays physiological dispersion.

---

## Installation

```bash
pip install -r requirements.txt
```

### Dependencies:
* `numpy` (vectorized matrix operations & conformal transformations)
* `scipy` (`cKDTree` spatial index in C++ and continuous `CubicSpline`)
* `pynput` (OS-level low-level mouse and keyboard hooks)
* `playwright` (async browser automation driver)
* `matplotlib` (visual target suite and kinematic analysis)