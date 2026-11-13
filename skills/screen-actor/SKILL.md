---
name: screen-actor
description: >-
  Use this skill whenever you need to physically interact with the operating system, desktop, or
  browser window by moving the mouse with human physiological kinematics, clicking, dragging,
  scrolling, or typing keystrokes with stealth keystroke dynamics.
---

# Screen Actor: Humanoid Kinematic Execution Protocol

`screen-actor` executes physical mouse and keyboard actions with authentic human kinematics. Powered by real human movement recordings, conformal transformations, and cubic spline interpolation, all cursor trajectories evade anti-bot biometric ML models (Turnstile, DataDome, reCAPTCHA v3) and deliver natural UI interactions.

## CLI Executables

The tool is located in `scripts/actor_cli.py`:
- Windows (Antigravity): `python "$env:USERPROFILE\.gemini\config\skills\screen-actor\scripts\actor_cli.py"`
- Windows (Local Repo): `python skills/screen-actor/scripts/actor_cli.py`

## Commands

### 1. Human-like Mouse Movement & Clicks
```bash
python scripts/actor_cli.py move <X> <Y> [--capture]
python scripts/actor_cli.py click <X> <Y> [--button left|right|middle] [--capture]
```
Passing `--capture` auto-captures a verification screenshot after the action in the same execution turn.

### 2. Realistic Drag & Drop
```bash
python scripts/actor_cli.py drag <TARGET_X> <TARGET_Y> [--start_x X] [--start_y Y] [--capture]
```

### 3. Biological Scrolling
```bash
python scripts/actor_cli.py scroll <DELTA_Y> [--capture]
# Positive: scroll down (e.g. 500)
# Negative: scroll up (e.g. -300)
```

### 4. Human Stealth Typing & Hotkeys
```bash
# Types with authentic neuromuscular dwell times and inter-word pauses
python scripts/actor_cli.py type "youtube.com" [--capture]

# Keyboard shortcuts (enter, tab, ctrl+c, esc, win)
python scripts/actor_cli.py key enter [--capture]
python scripts/actor_cli.py key ctrl+t [--capture]
```
