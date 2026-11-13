---
name: screen-sense
description: >-
  Use this skill whenever you need to visually observe the desktop or screen state, query display
  resolution, monitor bounds, DPI scaling, generate targeting reticle/crosshair previews,
  or track the current mouse cursor position before or after executing GUI actions.
---

# Screen Sense: Agent Visual Perception & Geometry Protocol

`screen-sense` acts as the sensory visual system for AI agents. It captures screenshots of the desktop, generates dynamic ~1/4 screen context crosshair previews, inspects screen resolution, and tracks cursor coordinates without session or permission errors.

## CLI Executables

The tool is located in `scripts/sense_cli.py`:
- Windows (Antigravity): `python "$env:USERPROFILE\.gemini\config\skills\screen-sense\scripts\sense_cli.py"`
- Windows (Local Repo): `python skills/screen-sense/scripts/sense_cli.py`

## Commands

### 1. Dynamic Context Aim Preview (~1/4 Screen with Crosshair)
```bash
python scripts/sense_cli.py aim <X> <Y> [--scale 0.5]
```
Generates a generous crop (half width, half height of screen) centered on $(X, Y)$ with a large, double-stroke high-contrast crosshair, targeting ring, and coordinate badge. Allows the LLM to verify accuracy before physically clicking.

### 2. Capture Full Screen
```bash
python scripts/sense_cli.py capture [--out path.png]
```
Saves screenshot to a temporary folder and outputs file path and resolution.

### 3. Inspect Screen Geometry & Cursor
```bash
python scripts/sense_cli.py info
python scripts/sense_cli.py pos
```
