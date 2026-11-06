"""MOSS Lab command line — local, auditable, read-only mission previews.

This is a separate safe prototype, not the full original MOSS/KYVRAEL.
No shell, live trading, browsing, PC automation or remote access.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

from mission_store import MissionStore
from mission_preview import create_preview, complete_preview
from mission_recovery import recover_stale, request_retry
from lexical_memory import MemoryIndex
from safe_workflow import Step

def output(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))

def parser_factory():
    parser = argparse.ArgumentParser(description="MOSS Lab: local mission and memory journal")
    parser.add_argument("--data-dir", type=Path, default=Path.home() / ".cerberus" / "moss_lab",
                        help="Local state folder (never uploaded to GitHub)")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("new", help="Create a pending journal mission")
    create.add_argument("title")
    sub.add_parser("list", help="List missions (up to 100)")
    sub.add_parser("status", help="Count journal state categories")
    preview = sub.add_parser("preview", help="Queue sequential read-only plan preview")
    preview.add_argument("title")
    preview.add_argument("--actions", default="inspect,validate,report",
                         help="Comma-delimited read-only actions")
    finish = sub.add_parser("complete-preview")
    finish.add_argument("mission_id")
    recover = sub.add_parser("recover", help="Mark stale running missions failed")
    recover.add_argument("--older-than", type=float, default=3600.0,
                         help="Seconds since last state update")
    retry = sub.add_parser("retry", help="Requeue failed mission without executing it")
    retry.add_argument("mission_id")
    retry.add_argument("--approve", action="store_true",
                       help="Required explicit acknowledgement")
    note = sub.add_parser("memory-add")
    note.add_argument("text")
    search = sub.add_parser("memory-search")
    search.add_argument("query")
    return parser

def main(argv=None):
    args = parser_factory().parse_args(argv)
    # Stateful commands are explicit; never silently import project data.
    state = Path(args.data_dir)
    try:
        if args.command in {"new", "list", "status", "preview",
                            "complete-preview", "recover", "retry"}:
            db = MissionStore(state / "missions.sqlite3")
            if args.command == "new":
                output({"mission_id": db.add(args.title), "state": "pending"})
            elif args.command == "list":
                output(db.list(limit=100))
            elif args.command == "status":
                output({"states": dict(Counter(x["state"] for x in db.list(limit=1000))),
                        "scope": "Local mission journal only"})
            elif args.command == "preview":
                actions = [x.strip() for x in args.actions.split(",")]
                if any(x not in {"inspect", "summarize", "validate", "report"} for x in actions):
                    raise ValueError("Preview actions must be read-only")
                if not 1 <= len(actions) <= 128:
                    raise ValueError("Between 1 and 128 actions required")
                steps = [
                    Step(f"step-{i+1}", action,
                         (f"step-{i}",) if i else ())
                    for i, action in enumerate(actions)
                ]
                output(create_preview(db, args.title, steps))
            elif args.command == "complete-preview":
                output(complete_preview(db, args.mission_id))
            elif args.command == "recover":
                output({"marked_failed": recover_stale(db, args.older_than),
                        "automatic_retry": False})
            elif args.command == "retry":
                output(request_retry(db, args.mission_id, operator_approved=args.approve))
        elif args.command in {"memory-add", "memory-search"}:
            db = MemoryIndex(state / "memory.sqlite3")
            if args.command == "memory-add":
                output({"note_id": db.insert(args.text, source="explicit_cli")})
            else:
                output(db.search(args.query))
    except (ValueError, KeyError, PermissionError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
