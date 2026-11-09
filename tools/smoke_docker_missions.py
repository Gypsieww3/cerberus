"""Owner-only real Docker smoke for allowlisted CERBERUS missions.

Usage: py -3 tools/smoke_docker_missions.py --task robotics_static
Runs an exact fixed task; it does not accept arbitrary commands or paths.
"""
import argparse
from pathlib import Path
import sys
from threading import Event
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03_CERBERUS_CORE"))
from mission_engine import TASKS, docker_runner

def main():
    parser = argparse.ArgumentParser(description="Run one allowlisted Docker check")
    parser.add_argument("--task", choices=sorted(TASKS), default="robotics_static")
    args = parser.parse_args()
    task = TASKS[args.task]
    result = docker_runner(task, str(uuid4()), Event(), repo=ROOT)
    print("Task:", args.task)
    print("Result:", result.state, "exit", result.exit_code)
    print("Output tail:", result.output[-1400:])
    return 0 if result.state == "PASSED" else 1

if __name__ == "__main__":
    sys.exit(main())
