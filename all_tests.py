"""
Universal Test Runner for stealth_mouse.

Provides a unified single-command entrypoint to run:
1. Complete Visual Interactive Tour (live Chromium browser & desktop UI).
2. Fast Headless Automated Test Suite (20 pytest unit and integration tests).
3. Individual specialized visual challenges (reCAPTCHA v3, Turnstile, DataDome Slider, etc.).

Usage:
    python all_tests.py                 # Interactive visual menu
    python all_tests.py --all           # Runs all 5 visual stages in sequence
    python all_tests.py --fast          # Runs all 20 automated tests in terminal (headless)
    python all_tests.py --recaptcha     # Live Google reCAPTCHA v3 (Score 0.9)
    python all_tests.py --slider        # Live DataDome / GeeTest slider drag puzzle
    python all_tests.py --turnstile     # Live Cloudflare Turnstile challenge
    python all_tests.py --sandbox       # Live Biometric Telemetry Sandbox
    python all_tests.py --targets       # Desktop Target Practice
"""

import sys
import asyncio
import argparse
import subprocess
from pathlib import Path

# Ensure root workspace directory is in sys.path
WORKSPACE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(WORKSPACE_DIR))

from tests.test_interactive_browser import (
    run_all_sequentially,
    run_telemetry_sandbox,
    run_recaptcha_v3_test,
    run_cloudflare_turnstile_test,
    run_slider_puzzle_test,
    run_target_practice_demo,
)


def run_fast_headless_tests() -> int:
    """Runs the 20 automated pytest tests in headless mode."""
    print("\n" + "=" * 70)
    print("  RUNNING FAST HEADLESS TEST SUITE (PYTEST - 20 TESTS)")
    print("=" * 70)
    print("  * Testing Core: KDTree lookups, Conformal transforms, Splines, Scroller")
    print("  * Testing Kinematics: FFT 8-14 Hz tremor, Anti-replay entropy, Bell curves")
    print("  * Testing Browser: Click, Drag, Scroll, and Google reCAPTCHA v3 score")
    print("-" * 70 + "\n")

    cmd = [sys.executable, "-m", "pytest", "-v", "tests"]
    result = subprocess.run(cmd, cwd=str(WORKSPACE_DIR))
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="Stealth Mouse Universal Test Runner")
    parser.add_argument("--all", "-a", action="store_true", help="Run all 5 visual interactive tests sequentially")
    parser.add_argument("--fast", "-f", "--headless", "--ci", action="store_true", help="Run 20 automated tests in background (headless)")
    parser.add_argument("--recaptcha", action="store_true", help="Run live Google reCAPTCHA v3 evaluation in browser")
    parser.add_argument("--slider", action="store_true", help="Run live DataDome / GeeTest biometric slider challenge")
    parser.add_argument("--turnstile", action="store_true", help="Run live Cloudflare Turnstile challenge")
    parser.add_argument("--sandbox", action="store_true", help="Run live biometric telemetry sandbox")
    parser.add_argument("--targets", action="store_true", help="Run desktop full-screen target practice demo")

    args = parser.parse_args()

    # Direct CLI flags
    if args.fast:
        sys.exit(run_fast_headless_tests())
    elif args.all:
        asyncio.run(run_all_sequentially())
    elif args.recaptcha:
        asyncio.run(run_recaptcha_v3_test())
    elif args.slider:
        asyncio.run(run_slider_puzzle_test())
    elif args.turnstile:
        asyncio.run(run_cloudflare_turnstile_test())
    elif args.sandbox:
        asyncio.run(run_telemetry_sandbox())
    elif args.targets:
        run_target_practice_demo()
    else:
        # Interactive selection menu
        print("=" * 70)
        print("  STEALTH_MOUSE - UNIVERSAL TEST RUNNER")
        print("=" * 70)
        print("  1. Full Visual Tour (All 5 live demos in real browser & desktop)")
        print("  2. Google reCAPTCHA v3 Live Scoring (Official Google Demo - Score 0.9)")
        print("  3. DataDome / GeeTest Biometric Slider (Drag & Drop physics)")
        print("  4. Cloudflare Turnstile Challenge (Real Web Challenge)")
        print("  5. Anti-Bot Telemetry Sandbox (Canvas trail & Biometric score)")
        print("  6. Desktop Full-Screen Target Range (Pynput bullseye navigation)")
        print("  7. Fast Headless Suite (Pytest - 20 automated tests in terminal)")
        print("=" * 70)

        choice = input("Select an option [1-7] (default 1): ").strip()

        if choice == "2":
            asyncio.run(run_recaptcha_v3_test())
        elif choice == "3":
            asyncio.run(run_slider_puzzle_test())
        elif choice == "4":
            asyncio.run(run_cloudflare_turnstile_test())
        elif choice == "5":
            asyncio.run(run_telemetry_sandbox())
        elif choice == "6":
            run_target_practice_demo()
        elif choice == "7":
            sys.exit(run_fast_headless_tests())
        else:
            asyncio.run(run_all_sequentially())


if __name__ == "__main__":
    main()
