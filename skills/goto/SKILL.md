---
name: goto
description: >-
  Use this skill whenever the user triggers `/goto: <prompt>` or asks you to autonomously
  navigate across the desktop, open an app, click a specific button, or reach a goal on screen.
  Creates an initial step-by-step navigation plan, uses `screen-sense` and `screen-actor`
  iteratively, and dynamically corrects course if unexpected states or popups appear.
---

# Goto: Autonomous Screen Navigation & Visual Task Orchestrator

`/goto` is the autonomous navigator for desktop and GUI automation. Given a high-level goal (e.g. `/goto: open Chrome and search for quantum computing papers`, `/goto: click on the download button in this window`), it:
1. Synthesizes the objective into an **initial step-by-step roadmap** (approximate milestones).
2. Executes an **Iterative Sense-Act-Verify Loop** combining `screen-sense` (vision) and `screen-actor` (stealth kinematics).
3. **Corrects course dynamically** if popups, misaligned windows, or unexpected screen states occur.

---

## Command Syntax

```text
/goto: <objective or navigation prompt>
```

### Examples
- `/goto: open settings and switch theme to dark`
- `/goto: focus the browser tab and click on the submit button`
- `/goto: scroll down until the pricing table is visible and click Start Free`

---

## 4-Phase Navigation Protocol

### Phase 1: Objective Framing & Initial Step Breakdown
When the user triggers `/goto: <prompt>`:
1. **Define the Destination:** State in 1 sentence what the finished state looks like.
2. **Draft the Approximate Step Plan:** Outline 3 to 6 logical milestones. Example:
   * *Paso 1:* Capturar pantalla y verificar si la ventana objetivo está activa o en la barra de tareas.
   * *Paso 2:* Si no está activa, abrirla o enfocarla mediante click en icono o atajo de teclado (`key win` o `key alt+tab`).
   * *Paso 3:* Localizar las coordenadas $(X, Y)$ del control o campo de texto con `screen-sense`.
   * *Paso 4:* Moverse con cinemática humana y clickear con `screen-actor`.
   * *Paso 5:* Introducir texto o navegar y verificar pantalla final.

### Phase 2: Sensory Inspection (`screen-sense`)
Before making any physical movement:
```bash
python "$env:USERPROFILE\.gemini\config\skills\screen-sense\scripts\sense_cli.py" capture
# (Or local: python skills/screen-sense/scripts/sense_cli.py capture)
```
- Inspect the generated PNG image.
- Identify the bounding box and central $(X, Y)$ coordinate of the target element.
- Note any unexpected obstacles (dialogs, cookie banners, unfocused windows).

### Phase 3: Kinematic Execution (`screen-actor`)
Execute the planned step using authentic human kinematics:
```bash
# Move and click
python "$env:USERPROFILE\.gemini\config\skills\screen-actor\scripts\actor_cli.py" click <X> <Y>

# Or type if entering text
python "$env:USERPROFILE\.gemini\config\skills\screen-actor\scripts\actor_cli.py" type "query text"
python "$env:USERPROFILE\.gemini\config\skills\screen-actor\scripts\actor_cli.py" key enter
```

### Phase 4: State Verification & Dynamic Course Correction
After each action:
1. Re-run `screen-sense capture` to confirm the state transition.
2. **If the screen matches expectation:** Proceed to the next milestone in the roadmap.
3. **If deviated (popup appeared, element did not trigger, or scrolled past):**
   * Do NOT panic or give up.
   * Announce course correction: *"Se detectó una ventana emergente / la página tardó en cargar. Ajustando trayectoria..."*
   * Execute corrective action (e.g. dismiss dialog, scroll slightly, or re-click).
4. Once the final target is reached, output a brief completion summary with the screenshot proof.

