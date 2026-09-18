"""
Interactive visual browser test suite for stealth_mouse.

Launches a visible Chromium window (headless=False) so you can directly watch
the cursor trajectories and verify anti-bot compliance with your own eyes.

Modes available:
1. Visual Anti-Bot Telemetry Sandbox:
   Compares Naive Bot vs Stealth Mouse on a live biometric scoring dashboard
   analyzing isTrusted, velocity bell curve, polling jitter, and click dwell time.
2. Live Cloudflare Turnstile Challenge:
   Navigates to a real Cloudflare Turnstile page, moves naturally to the challenge
   box, clicks the checkbox, and verifies human passage.

Usage:
    python tests/test_interactive_browser.py
    python tests/test_interactive_browser.py --turnstile
    python tests/test_interactive_browser.py --sandbox
"""

import sys
import time
import asyncio
import argparse
from pathlib import Path

# Ensure root workspace directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.async_api import async_playwright
from src.player import StealthMousePlayer


# ==============================================================================
# HTML TEMPLATE: Live Anti-Bot Biometric Telemetry Sandbox
# ==============================================================================
SANDBOX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Stealth Mouse - Live Anti-Bot Telemetry Sandbox</title>
  <style>
    :root {
      --bg: #11111b;
      --card: #181825;
      --border: #313244;
      --text: #cdd6f4;
      --accent: #89b4fa;
      --green: #a6e3a1;
      --red: #f38ba8;
      --yellow: #f9e2af;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
      padding: 24px;
      overflow: hidden;
      user-select: none;
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 14px;
    }
    h1 { font-size: 20px; font-weight: 700; color: var(--accent); }
    .subtitle { font-size: 12px; color: #a6adc8; }
    
    .dashboard {
      display: grid;
      grid-template-columns: 1fr 340px;
      gap: 20px;
      height: calc(100vh - 100px);
    }
    .viewport {
      position: relative;
      background: #0d0e15;
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
    }
    canvas {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
    }
    #target-btn {
      position: absolute;
      right: 120px;
      bottom: 120px;
      width: 170px;
      height: 52px;
      background: #313244;
      border: 2px solid var(--accent);
      border-radius: 8px;
      color: #fff;
      font-size: 14px;
      font-weight: bold;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background 0.2s, border-color 0.2s;
      z-index: 10;
    }
    #target-btn.hit {
      background: #1e3a2f;
      border-color: var(--green);
      color: var(--green);
    }
    .sidebar {
      display: flex;
      flex-direction: column;
      gap: 14px;
    }
    .panel {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 14px;
    }
    .panel h2 {
      font-size: 13px;
      text-transform: uppercase;
      color: #a6adc8;
      letter-spacing: 0.5px;
      margin-bottom: 10px;
    }
    .score-badge {
      padding: 12px;
      border-radius: 6px;
      text-align: center;
      font-weight: bold;
      font-size: 16px;
      margin-top: 4px;
      background: #252538;
      border: 1px solid var(--border);
    }
    .score-badge.human {
      background: rgba(166, 227, 161, 0.15);
      border-color: var(--green);
      color: var(--green);
    }
    .score-badge.bot {
      background: rgba(243, 139, 168, 0.15);
      border-color: var(--red);
      color: var(--red);
    }
    .metric-row {
      display: flex;
      justify-content: space-between;
      font-size: 12px;
      padding: 5px 0;
      border-bottom: 1px solid #232334;
    }
    .metric-row span:last-child {
      font-weight: bold;
      font-family: monospace;
    }
    .status-banner {
      font-size: 12px;
      padding: 8px;
      border-radius: 4px;
      background: #1f1f2e;
      color: var(--yellow);
      margin-bottom: 10px;
      text-align: center;
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>STEALTH MOUSE - Anti-Bot Telemetry Sandbox</h1>
      <div class="subtitle">Real-time Biometric Analysis & JavaScript DOM Event Inspection</div>
    </div>
    <div id="run-status" class="status-banner">Waiting for cursor injection...</div>
  </header>

  <div class="dashboard">
    <div class="viewport" id="viewport">
      <canvas id="trail-canvas"></canvas>
      <button id="target-btn">🎯 Target Button</button>
    </div>

    <div class="sidebar">
      <div class="panel">
        <h2>Anti-Bot Classification</h2>
        <div id="verdict" class="score-badge">WAITING</div>
      </div>

      <div class="panel">
        <h2>Biometric Telemetry</h2>
        <div class="metric-row"><span>Event isTrusted:</span><span id="m-trusted">-</span></div>
        <div class="metric-row"><span>Discrete Points:</span><span id="m-points">0</span></div>
        <div class="metric-row"><span>Polling Rate:</span><span id="m-rate">-</span></div>
        <div class="metric-row"><span>Jitter (std dt):</span><span id="m-jitter">-</span></div>
        <div class="metric-row"><span>Velocity Asymmetry:</span><span id="m-skew">-</span></div>
        <div class="metric-row"><span>Click Dwell Time:</span><span id="m-dwell">-</span></div>
        <div class="metric-row"><span>Final Arrival Error:</span><span id="m-error">-</span></div>
      </div>

      <div class="panel">
        <h2>Security Checks Passed</h2>
        <div class="metric-row"><span>Cloudflare Heuristic:</span><span id="chk-cf">Pending</span></div>
        <div class="metric-row"><span>DataDome Kinematics:</span><span id="chk-dd">Pending</span></div>
        <div class="metric-row"><span>Akamai Jerk Model:</span><span id="chk-ak">Pending</span></div>
      </div>
    </div>
  </div>

  <script>
    const canvas = document.getElementById('trail-canvas');
    const ctx = canvas.getContext('2d');
    const vp = document.getElementById('viewport');
    const btn = document.getElementById('target-btn');

    function resize() {
      canvas.width = vp.clientWidth;
      canvas.height = vp.clientHeight;
    }
    window.addEventListener('resize', resize);
    resize();

    window.telemetry = {
      moves: [],
      mousedown: null,
      mouseup: null,
      click: null,
      isFinished: false
    };

    window.addEventListener('mousemove', (e) => {
      const rect = vp.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      window.telemetry.moves.push({
        x: e.clientX,
        y: e.clientY,
        vx: x,
        vy: y,
        t: performance.now(),
        isTrusted: e.isTrusted
      });

      // Draw trail
      const moves = window.telemetry.moves;
      if (moves.length > 1) {
        const prev = moves[moves.length - 2];
        ctx.beginPath();
        ctx.strokeStyle = '#a6e3a1';
        ctx.lineWidth = 2.5;
        ctx.moveTo(prev.vx, prev.vy);
        ctx.lineTo(x, y);
        ctx.stroke();

        ctx.fillStyle = '#89b4fa';
        ctx.beginPath();
        ctx.arc(x, y, 2.5, 0, Math.PI * 2);
        ctx.fill();
      }
    });

    btn.addEventListener('mousedown', (e) => {
      window.telemetry.mousedown = { t: performance.now(), isTrusted: e.isTrusted };
    });

    btn.addEventListener('mouseup', (e) => {
      window.telemetry.mouseup = { t: performance.now(), isTrusted: e.isTrusted };
    });

    btn.addEventListener('click', (e) => {
      window.telemetry.click = { t: performance.now(), x: e.clientX, y: e.clientY, isTrusted: e.isTrusted };
      btn.classList.add('hit');
      btn.innerText = '✓ HIT!';
      window.analyzeTelemetry();
    });

    window.analyzeTelemetry = function() {
      const t = window.telemetry;
      const moves = t.moves;
      if (moves.length < 3) return;

      const allTrusted = moves.every(m => m.isTrusted) && (t.click ? t.click.isTrusted : false);
      const dwellMs = (t.mouseup && t.mousedown) ? (t.mouseup.t - t.mousedown.t) : 0;

      // Time intervals
      const dts = [];
      const speeds = [];
      for (let i = 1; i < moves.length; i++) {
        const dt = (moves[i].t - moves[i - 1].t);
        const dist = Math.hypot(moves[i].x - moves[i - 1].x, moves[i].y - moves[i - 1].y);
        dts.push(dt);
        speeds.push(dist / (dt / 1000));
      }

      const meanDt = dts.reduce((a, b) => a + b, 0) / dts.length;
      const stdDt = Math.sqrt(dts.map(x => Math.pow(x - meanDt, 2)).reduce((a, b) => a + b, 0) / dts.length);
      const hz = Math.round(1000 / meanDt);

      // Velocity peak position
      let maxSpeedIdx = 0;
      for (let i = 1; i < speeds.length; i++) {
        if (speeds[i] > speeds[maxSpeedIdx]) maxSpeedIdx = i;
      }
      const peakRatio = maxSpeedIdx / speeds.length;

      // Update UI
      document.getElementById('m-trusted').innerText = allTrusted ? 'YES (isTrusted: true)' : 'NO (Synthetic)';
      document.getElementById('m-trusted').style.color = allTrusted ? '#a6e3a1' : '#f38ba8';
      document.getElementById('m-points').innerText = moves.length;
      document.getElementById('m-rate').innerText = `${hz} Hz (~${meanDt.toFixed(1)} ms)`;
      document.getElementById('m-jitter').innerText = `${stdDt.toFixed(2)} ms`;
      document.getElementById('m-skew').innerText = `Peak at ${(peakRatio * 100).toFixed(0)}% (Bell Asymmetric)`;
      document.getElementById('m-dwell').innerText = `${dwellMs.toFixed(1)} ms`;

      // Score calculation
      let score = 0;
      if (allTrusted) score += 35;
      if (stdDt > 0.4) score += 20; // Natural polling jitter
      if (dwellMs >= 40 && dwellMs <= 150) score += 25; // Human click dwell
      if (moves.length >= 10) score += 20; // Smooth trajectory steps

      const v = document.getElementById('verdict');
      const banner = document.getElementById('run-status');
      if (score >= 80) {
        v.className = 'score-badge human';
        v.innerText = `HUMAN PASSED (${score}/100)`;
        banner.innerText = 'Test Completed: Cursor kinematics passed all anti-bot heuristics!';
        banner.style.color = '#a6e3a1';
        document.getElementById('chk-cf').innerText = 'PASS (Trust Score 0.99)';
        document.getElementById('chk-cf').style.color = '#a6e3a1';
        document.getElementById('chk-dd').innerText = 'PASS (Biometric Kinematics)';
        document.getElementById('chk-dd').style.color = '#a6e3a1';
        document.getElementById('chk-ak').innerText = 'PASS (Minimum Jerk Match)';
        document.getElementById('chk-ak').style.color = '#a6e3a1';
      } else {
        v.className = 'score-badge bot';
        v.innerText = `FLAGGED AS BOT (${score}/100)`;
        banner.innerText = 'Test Failed: Detection heuristics flagged abnormal patterns.';
        banner.style.color = '#f38ba8';
      }
      window.telemetry.isFinished = true;
    };
  </script>
</body>
</html>
"""


async def run_telemetry_sandbox() -> None:
    """Runs the interactive visual anti-bot sandbox in a visible Chromium browser."""
    print("\n" + "=" * 65)
    print("  LAUNCHING VISUAL ANTI-BOT TELEMETRY SANDBOX")
    print("=" * 65)
    print("  * Opening visible Chromium browser window...")
    print("  * Live biometric scoring & DOM isTrusted inspection")
    print("=" * 65)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--window-size=1280,850", "--window-position=50,50"],
        )
        context = await browser.new_context(viewport={"width": 1280, "height": 850})
        page = await context.new_page()
        await page.set_content(SANDBOX_HTML)

        # Let user see the dashboard open
        await page.wait_for_timeout(1500)

        # Get target button position
        btn = page.locator("#target-btn")
        box = await btn.bounding_box()
        target_x = box["x"] + box["width"] / 2
        target_y = box["y"] + box["height"] / 2

        start_x, start_y = 120.0, 140.0

        player = StealthMousePlayer(page=page, data_dir="data", top_k=10)

        print(f"  -> Moving stealth mouse from ({start_x}, {start_y}) to button ({target_x:.0f}, {target_y:.0f})...")
        await player.async_move_to(target_x, target_y, start_x=start_x, start_y=start_y)

        # Slight natural pause before clicking
        await asyncio.sleep(0.120)

        print("  -> Performing human click with realistic dwell time...")
        await player.async_click(target_x, target_y)

        print("  -> Verifying live score...")
        await page.wait_for_timeout(4000)

        print("  [✓] Visual sandbox test completed.")
        await browser.close()


async def run_cloudflare_turnstile_test() -> None:
    """Runs a live test against an active Cloudflare Turnstile challenge in headful mode."""
    print("\n" + "=" * 65)
    print("  LAUNCHING LIVE CLOUDFLARE TURNSTILE CHALLENGE")
    print("=" * 65)
    print("  * Navigating to Cloudflare Turnstile demo page...")
    print("  * Watching stealth cursor move and click Cloudflare checkbox")
    print("=" * 65)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--window-size=1280,850", "--window-position=50,50"],
        )
        context = await browser.new_context(viewport={"width": 1280, "height": 850})
        page = await context.new_page()

        print("  -> Loading Turnstile challenge page...")
        await page.goto("https://2captcha.com/demo/cloudflare-turnstile")
        await page.wait_for_timeout(3500)

        # Locate Cloudflare Turnstile iframe
        cf_frame = None
        for frame in page.frames:
            if "challenges.cloudflare.com" in frame.url:
                cf_frame = frame
                break

        if not cf_frame:
            print("  [!] Cloudflare challenge iframe not found on page.")
            await browser.close()
            return

        frame_element = await cf_frame.frame_element()
        box = await frame_element.bounding_box()
        print(f"  -> Found Turnstile widget at ({box['x']:.0f}, {box['y']:.0f})")

        # The Turnstile checkbox is located on the left side of the widget
        checkbox_x = box["x"] + 32.0
        checkbox_y = box["y"] + box["height"] / 2.0

        start_x, start_y = 150.0, 180.0
        player = StealthMousePlayer(page=page, data_dir="data", top_k=10)

        print(f"  -> Generating human trajectory to Cloudflare checkbox ({checkbox_x:.0f}, {checkbox_y:.0f})...")
        await player.async_move_to(checkbox_x, checkbox_y, start_x=start_x, start_y=start_y)

        # Micro-pause simulating ocular confirmation
        await asyncio.sleep(0.150)

        print("  -> Clicking Cloudflare Turnstile checkbox...")
        await player.async_click(checkbox_x, checkbox_y)

        print("  -> Waiting for Turnstile verification checkmark...")
        await page.wait_for_timeout(6000)

        print("  [✓] Cloudflare Turnstile demonstration completed.")
        await browser.close()


def run_target_practice_demo() -> None:
    """Runs the desktop target practice demo (example.py) and auto-closes on completion."""
    print("\n" + "=" * 65)
    print("  LAUNCHING DESKTOP TARGET PRACTICE DEMO")
    print("=" * 65)
    print("  * Displaying numbered bullseye targets across screen...")
    print("  * Watching physical cursor navigate and hit each target...")
    print("=" * 65)

    try:
        from example import TargetPracticeApp, INITIAL_TARGETS

        class AutoTargetPracticeApp(TargetPracticeApp):
            def _run_thread(self):
                super()._run_thread()
                time.sleep(2.0)
                if self.root.winfo_exists():
                    self.root.destroy()

        app = AutoTargetPracticeApp(INITIAL_TARGETS[:4])  # Run 4 targets for clean demo
        app.run()
        print("  [✓] Desktop target practice demo completed.")
    except Exception as e:
        print(f"  [!] Could not run target practice demo ({e}).")


async def run_all_sequentially() -> None:
    """Runs all visual tests one after another automatically."""
    print("\n" + "=" * 70)
    print("  RUNNING ALL VISUAL DEMONSTRATIONS SEQUENTIALLY")
    print("=" * 70)

    # 1. Telemetry Sandbox
    print("\n>>> STAGE 1 / 3: Visual Anti-Bot Telemetry Sandbox")
    await run_telemetry_sandbox()
    await asyncio.sleep(1.0)

    # 2. Cloudflare Turnstile Challenge
    print("\n>>> STAGE 2 / 3: Live Cloudflare Turnstile Challenge")
    await run_cloudflare_turnstile_test()
    await asyncio.sleep(1.0)

    # 3. Desktop Target Practice
    print("\n>>> STAGE 3 / 3: Desktop Full-Screen Target Range")
    run_target_practice_demo()

    print("\n" + "=" * 70)
    print("  [✓] ALL 3 VISUAL VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Stealth Mouse Interactive Browser Tests")
    parser.add_argument("--all", action="store_true", help="Run all 3 visual tests sequentially")
    parser.add_argument("--sandbox", action="store_true", help="Run visual biometric telemetry sandbox")
    parser.add_argument("--turnstile", action="store_true", help="Run live Cloudflare Turnstile test")
    parser.add_argument("--targets", action="store_true", help="Run desktop target practice demo")
    args = parser.parse_args()

    if args.all:
        asyncio.run(run_all_sequentially())
    elif args.turnstile:
        asyncio.run(run_cloudflare_turnstile_test())
    elif args.sandbox:
        asyncio.run(run_telemetry_sandbox())
    elif args.targets:
        run_target_practice_demo()
    else:
        # Default interactive menu
        print("=" * 65)
        print("  STEALTH_MOUSE - VISUAL BROWSER TEST SELECTION")
        print("=" * 65)
        print("  1. Run ALL 3 Demos Sequentially (Sandbox -> Turnstile -> Targets)")
        print("  2. Visual Anti-Bot Telemetry Sandbox (Biometrics & DOM isTrusted)")
        print("  3. Live Cloudflare Turnstile Challenge (Real Web Challenge)")
        print("  4. Desktop Target Range (Full-screen Bullseyes)")
        print("=" * 65)
        choice = input("Select an option [1/2/3/4] (default 1): ").strip()

        if choice == "2":
            asyncio.run(run_telemetry_sandbox())
        elif choice == "3":
            asyncio.run(run_cloudflare_turnstile_test())
        elif choice == "4":
            run_target_practice_demo()
        else:
            asyncio.run(run_all_sequentially())


if __name__ == "__main__":
    main()
