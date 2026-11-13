---
name: screen-actor
description: >-
  Use this skill whenever you need to physically interact with the operating system, desktop, or
  browser window by moving the mouse with human physiological kinematics, clicking, dragging,
  scrolling, or typing keystrokes.
---

# Screen Actor: Humanoid Kinematic Execution Protocol

`screen-actor` executes physical mouse and keyboard actions with authentic human kinematics. Powered by real human movement recordings, conformal transformations, and cubic spline interpolation, all cursor trajectories evade anti-bot biometric ML models (Turnstile, DataDome, reCAPTCHA v3) and deliver natural UI interactions.

## CLI Executables

The tool is located in `scripts/actor_cli.py`:
- Windows (Antigravity): `python "$env:USERPROFILE\.gemini\config\skills\screen-actor\scripts\actor_cli.py"`
- Windows (Local Repo): `python skills/screen-actor/scripts/actor_cli.py`

## Commands

### 1. Human-like Mouse Movement
```bash
python scripts/actor_cli.py move <X> <Y>
```
Executes a natural biological trajectory with acceleration, neuromuscular tremor (8–14 Hz), and smooth deceleration into $(X, Y)$.

### 2. Click with Pre-Click Hesitation & Settle
```bash
python scripts/actor_cli.py click <X> <Y> [--button left|right|middle]
```
Moves to coordinates, pauses naturally, presses button, holds dwell time, releases, and settles.

### 3. Realistic Drag & Drop
```bash
python scripts/actor_cli.py drag <TARGET_X> <TARGET_Y> [--start_x X] [--start_y Y]
```
Simulates breakaway friction, holds button down along curve, and releases with terminal alignment.

### 4. Biological Scrolling
```bash
python scripts/actor_cli.py scroll <DELTA_Y>
# Positive: scroll down (e.g. 500)
# Negative: scroll up (e.g. -300)
```
Simulates multi-flick finger bursts, friction decay, and micro-rebound.

### 5. Keyboard Typing & Hotkeys
```bash
python scripts/actor_cli.py type "Hello world"
python scripts/actor_cli.py key enter
python scripts/actor_cli.py key ctrl+c
```

## Best Practices
1. **Combine with `screen-sense`:** Always query coordinates with `screen-sense` before moving or clicking.
2. **Atomic Verification:** After a click that triggers a screen change, capture another screenshot to confirm the action took effect.

