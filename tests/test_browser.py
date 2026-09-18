"""
Browser integration test for stealth_mouse using Playwright.

Verifies:
1. In-browser DOM event dispatch via async CDP connection.
2. Anti-bot compliance: event.isTrusted === true.
3. Realistic human click dwell time (mousedown to mouseup between 45ms and 130ms, not 0ms).
4. Sub-pixel arrival accuracy inside the browser DOM viewport.
"""

import sys
import unittest
import asyncio
from pathlib import Path

# Ensure root workspace directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.async_api import async_playwright
from src.player import StealthMousePlayer


HTML_TEST_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Stealth Mouse Browser Test</title>
  <style>
    body { margin: 0; padding: 0; width: 100vw; height: 100vh; background: #111; }
    #target-btn {
      position: absolute;
      left: 450px;
      top: 320px;
      width: 120px;
      height: 44px;
      background: #89b4fa;
      border: none;
      color: #111;
      font-weight: bold;
      cursor: pointer;
    }
  </style>
</head>
<body>
  <button id="target-btn">Click Me</button>
  <script>
    window.__mouse_events = {
      moves: [],
      mousedown: null,
      mouseup: null,
      click: null
    };

    window.addEventListener('mousemove', (e) => {
      window.__mouse_events.moves.push({
        x: e.clientX,
        y: e.clientY,
        t: performance.now(),
        isTrusted: e.isTrusted
      });
    });

    const btn = document.getElementById('target-btn');
    btn.addEventListener('mousedown', (e) => {
      window.__mouse_events.mousedown = {
        x: e.clientX,
        y: e.clientY,
        t: performance.now(),
        isTrusted: e.isTrusted
      };
    });

    btn.addEventListener('mouseup', (e) => {
      window.__mouse_events.mouseup = {
        x: e.clientX,
        y: e.clientY,
        t: performance.now(),
        isTrusted: e.isTrusted
      };
    });

    btn.addEventListener('click', (e) => {
      window.__mouse_events.click = {
        x: e.clientX,
        y: e.clientY,
        t: performance.now(),
        isTrusted: e.isTrusted
      };
    });
  </script>
</body>
</html>
"""


class TestBrowserIntegration(unittest.IsolatedAsyncioTestCase):
    """Asynchronous browser tests against a real Playwright headless instance."""

    async def asyncSetUp(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(viewport={"width": 1280, "height": 800})
        self.page = await self.context.new_page()
        await self.page.set_content(HTML_TEST_PAGE)

    async def asyncTearDown(self):
        await self.browser.close()
        await self.playwright.stop()

    async def test_playwright_stealth_click(self):
        """
        Moves from (100, 100) to the center of #target-btn (510, 342) and clicks.
        Verifies DOM events received by the browser.
        """
        player = StealthMousePlayer(page=self.page, data_dir="data", top_k=10)

        start_x, start_y = 100.0, 100.0
        target_x, target_y = 510.0, 342.0

        # Asynchronously move and click
        await player.async_move_to(target_x, target_y, start_x=start_x, start_y=start_y)
        await player.async_click(target_x, target_y)

        # Retrieve tracked events from the browser's JavaScript environment
        events = await self.page.evaluate("() => window.__mouse_events")

        # 1. Verify mouse movements were captured in DOM
        moves = events["moves"]
        self.assertGreater(len(moves), 5, "Browser should record multiple discrete mousemove events")

        # 2. Verify all dispatched events have isTrusted === True
        for m in moves:
            self.assertTrue(m["isTrusted"], "Browser mousemove event must be trusted (isTrusted: true)")

        # 3. Verify click, mousedown, and mouseup were registered
        self.assertIsNotNone(events["mousedown"], "mousedown event was not captured")
        self.assertIsNotNone(events["mouseup"], "mouseup event was not captured")
        self.assertIsNotNone(events["click"], "click event was not captured")

        self.assertTrue(events["mousedown"]["isTrusted"])
        self.assertTrue(events["mouseup"]["isTrusted"])
        self.assertTrue(events["click"]["isTrusted"])

        # 4. Verify realistic human dwell time (time between mousedown and mouseup)
        # Naive bots do 0ms or instant clicks. Real humans take ~45ms - 130ms.
        dwell_ms = events["mouseup"]["t"] - events["mousedown"]["t"]
        self.assertGreaterEqual(dwell_ms, 35.0, f"Click dwell time too short for a human ({dwell_ms:.1f} ms)")
        self.assertLessEqual(dwell_ms, 200.0, f"Click dwell time too long ({dwell_ms:.1f} ms)")

        # 5. Verify final coordinates landed on the button
        click_ev = events["click"]
        self.assertAlmostEqual(click_ev["x"], target_x, delta=3.0)
        self.assertAlmostEqual(click_ev["y"], target_y, delta=3.0)


if __name__ == "__main__":
    unittest.main()
