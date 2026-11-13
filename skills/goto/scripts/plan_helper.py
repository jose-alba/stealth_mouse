#!/usr/bin/env python3
"""
Goto Plan Helper: Session tracking and state coordinator for autonomous GUI navigation.
"""

import os
import sys
import json
import time
from pathlib import Path


class GotoSession:
    def __init__(self, goal: str):
        self.goal = goal
        self.start_time = time.time()
        self.steps = []
        self.status = "in_progress"

    def add_step(self, step_idx: int, description: str, action: str, target: str, status: str = "pending"):
        self.steps.append({
            "index": step_idx,
            "description": description,
            "action": action,
            "target": target,
            "status": status,
            "timestamp": time.time(),
        })

    def to_dict(self):
        return {
            "goal": self.goal,
            "duration_s": round(time.time() - self.start_time, 2),
            "status": self.status,
            "total_steps": len(self.steps),
            "steps": self.steps,
        }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: plan_helper.py <init|summary> [args]"}, indent=2))
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "init":
        goal = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Navigation Goal"
        session = GotoSession(goal)
        print(json.dumps({"session_initialized": True, "goal": goal}, indent=2))
    elif cmd == "check":
        print(json.dumps({"ready": True, "skills": ["screen-sense", "screen-actor"]}, indent=2))
    else:
        print(json.dumps({"cmd": cmd, "status": "ok"}, indent=2))


if __name__ == "__main__":
    main()

