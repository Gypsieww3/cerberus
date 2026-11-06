"""Real, bounded, read-only engineering review missions for MOSS Lab.

Runs deterministic inventory and AST audit, persists evidence to local SQLite,
and records mission transitions. Does not execute any user or model code.
"""
from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from threading import Lock

from engineering_audit import audit_sources
from engineering_tools import EngineeringBusy
from mission_store import MissionStore

CORE_DIR = Path(__file__).resolve().parents[1] / "03_CERBERUS_CORE"
import sys
sys.path.insert(0, str(CORE_DIR))
from project_matrix import inventory


def timestamp():
    return datetime.now(timezone.utc).isoformat()


class EngineeringReviews:
    def __init__(self, journal: MissionStore, database_path):
        self.journal = journal
        self.path = Path(database_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = Lock()
        with self.connection() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS reviews(
                    mission_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    report_json TEXT NOT NULL
                )
            """)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(str(self.path), timeout=10)
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def get(self, mission_id):
        with self.connection() as db:
            row = db.execute(
                "SELECT created_at,report_json FROM reviews WHERE mission_id=?",
                (mission_id,)).fetchone()
        if row is None:
            raise KeyError(mission_id)
        return {"mission_id": mission_id, "created_at": row[0],
                "report": json.loads(row[1])}

    def recent(self, limit=10):
        if type(limit) is not int or not 1 <= limit <= 50:
            raise ValueError("Limit out of range")
        with self.connection() as db:
            rows = db.execute(
                "SELECT mission_id FROM reviews ORDER BY created_at DESC, rowid DESC LIMIT ?",
                (limit,)).fetchall()
        return [self.get(row[0]) for row in rows]

    def execute(self, title, *, operator_approved=False):
        if operator_approved is not True:
            raise PermissionError("Explicit approval required to run engineering review")
        if not isinstance(title, str) or not title.strip() or len(title) > 300:
            raise ValueError("Title must contain 1..300 characters")
        if not self.lock.acquire(blocking=False):
            raise EngineeringBusy("Another review is already running")
        mission_id = None
        try:
            mission_id = self.journal.add(title.strip(), {
                "mode": "engineering_review",
                "actions": ["inspect_repository", "audit_python_ast", "report"],
                "scope": "Read-only local repository",
            })
            self.journal.transition(mission_id, "running",
                                    "Started read-only engineering review")
            project_info = inventory()
            audit = audit_sources()
            report = {
                "inventory": project_info,
                "python_audit": audit,
                "finding_count": len(audit["findings"]),
                "result": "REVIEW_REQUIRED" if audit["syntax_errors"] else "REVIEW_COMPLETE",
                "tools_executed": ["inventory", "python_ast_audit"],
                "files_modified": 0,
                "scope": "Local source inspection only, not proof of production readiness",
            }
            encoded = json.dumps(report, ensure_ascii=False, allow_nan=False)
            if len(encoded.encode("utf-8")) > 200_000:
                raise ValueError("Review output exceeds persistent report limit")
            with self.connection() as db:
                db.execute(
                    "INSERT INTO reviews(mission_id,created_at,report_json) VALUES(?,?,?)",
                    (mission_id, timestamp(), encoded))
            self.journal.transition(mission_id, "done",
                                    "Repository inventory and AST report persisted")
            return self.get(mission_id)
        except Exception:
            if mission_id is not None:
                try:
                    if self.journal.get(mission_id)["state"] == "running":
                        self.journal.transition(mission_id, "failed",
                                                "Review execution failed")
                except (ValueError, KeyError):
                    pass
            raise
        finally:
            self.lock.release()
