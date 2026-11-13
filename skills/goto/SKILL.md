---
name: goto
description: >-
  Use this skill whenever the user triggers `/goto: <prompt>` or asks you to autonomously
  navigate across the desktop, open an app, click a specific button, or reach a goal on screen.
  Operates reactively: captures screen state, verifies ambiguous targets with dynamic ~1/4 screen
  crosshairs, executes actions using stealth kinematics, and chains auto-captures to finish in seconds.
---

# Goto: Reactive Autonomous Screen Navigator

`/goto` provides lightning-fast, reactive GUI navigation across the operating system without bureaucratic upfront planning. Like a human operator, it looks at the current screen, acts on the most direct visible path, and verifies steps in a tight, fluid loop.

---

## Command Syntax

```text
/goto: <prompt>
```

### Examples
- `/goto: canal de youtube smart enough`
- `/goto: open settings and switch theme to dark`
- `/goto: click on the download button in this window`

---

## 3-Rule Reactive Navigation Protocol

### 1. Zero-Bureaucracy Start (Turn 1: Look First)
Do **NOT** write long multi-phase waterfall plans. Immediately start by looking at what is on screen:
```bash
python "$env:USERPROFILE\.gemini\config\skills\screen-sense\scripts\sense_cli.py" capture
```

### 2. Aim Before Firing on Tricky/Small Targets (`aim <X> <Y>`)
If you need to verify an icon, small button, or link before making a physical click on the OS, generate a **dynamic ~1/4 screen context preview** with a large, high-contrast targeting reticle:
```bash
python "$env:USERPROFILE\.gemini\config\skills\screen-sense\scripts\sense_cli.py" aim <X> <Y>
```
- Returns a generous crop (half screen width & half screen height centered on the target).
- Features a bold outer ring, coordinate badge `[+] TARGET (X, Y)`, and crosshairs with a central open gap so the underlying icon/text remains visible.
- Check the preview:
  - If the reticle is centered: Proceed to fire.
  - If off-center by a few pixels: Adjust $(X, Y)$ immediately without having clicked blindly in the OS.

### 3. Pipeline Compuesto (Action + Auto-Capture in 1 Turn)
Whenever executing an action, pass the `--capture` flag:
```bash
# Click & immediately get follow-up screenshot in the same turn
python "$env:USERPROFILE\.gemini\config\skills\screen-actor\scripts\actor_cli.py" click <X> <Y> --capture

# Human stealth typing (digraph intervals, space thinking pauses) + auto-capture
python "$env:USERPROFILE\.gemini\config\skills\screen-actor\scripts\actor_cli.py" type "query text"
python "$env:USERPROFILE\.gemini\config\skills\screen-actor\scripts\actor_cli.py" key enter --capture
```

### 4. Human-like Behavior (Don't Be a Robot)
- **Use Visible Shortcuts:** If a browser new-tab page has a YouTube shortcut button, click that button directly rather than typing long URLs.
- **Never Type Query URLs:** Humans do not type `https://youtube.com/results?search_query=...`. They open the site, click the search bar, type their search terms with stealth kinematics, and press Enter.
