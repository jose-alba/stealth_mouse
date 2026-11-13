---
name: screen-sense
description: >-
  Use this skill whenever you need to visually observe the desktop or screen state, query display
  resolution, monitor bounds, DPI scaling, or track the current mouse cursor position before or
  after executing GUI actions.
---

# Screen Sense: Agent Visual Perception & Geometry Protocol

`screen-sense` acts as the sensory visual system for AI agents. It captures screenshots of the desktop or specific regions, inspects screen resolution, checks multi-monitor geometry, and tracks the exact cursor position without permission or session errors.

## CLI Executables

The tool is located in `scripts/sense_cli.py`:
- Windows (Antigravity): `python "$env:USERPROFILE\.gemini\config\skills\screen-sense\scripts\sense_cli.py"`
- Windows (Local Repo): `python skills/screen-sense/scripts/sense_cli.py`

## Commands

### 1. Inspect Screen Geometry & Cursor
```bash
python scripts/sense_cli.py info
```
Returns:
```json
{
  "platform": "win32",
  "width": 1920,
  "height": 1080,
  "cursor_x": 960,
  "cursor_y": 540,
  "dpi_aware": true
}
```

### 2. Capture Full Screen
```bash
python scripts/sense_cli.py capture
```
Saves the screenshot to a temporary folder and outputs the file path. The agent can then inspect this image using visual analysis tools to find UI elements and determine target coordinates $(x, y)$.

### 3. Capture Specific Bounding Region
```bash
python scripts/sense_cli.py capture --region 200 150 800 600 --out "screen_crop.png"
```

## Best Practices
1. **Always Sense First**: Before executing a click or drag, run `capture` or `info` to verify the resolution and verify where the target button or window actually is.
2. **DPI Awareness**: All returned coordinates are DPI-normalized to match physical screen pixels.

