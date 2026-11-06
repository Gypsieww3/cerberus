"""Audited, operator-approved engineering jobs for MOSS Lab.

Only three static Python verification scripts can be run. No user-supplied
commands, paths, model text or shell arguments ever enter subprocess calls.
This is local verification, not autonomous code execution.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import sys
from threading import Lock

CORE_DIR = Path(__file__).resolve().parents[1] / "03_CERBERUS_CORE"
sys.path.insert(0, str(CORE_DIR))
from lab import JOBS, run_job  # vetted local script allowlist
from project_matrix import inventory

DESCRIPTION = {
    "engineering-tests": "Executar testes de regressão Python dos projetos (até 120 s).",
    "rv32i-reference": "Verificar programa de referência RISC-V em Python (não simula RTL).",
    "alu-reference": "Verificar operações da ALU com modelo Python.",
    "moss-syntax": "Analisar sintaxe dos módulos Python do MOSS sem os executar.",
}
MAX_LOG = 5000


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class EngineeringBusy(RuntimeError):
    """An engineering job is already being executed."""


class EngineeringRunner:
    def __init__(self, database_path):
        self.path = Path(database_path)
        if str(database_path) == ":memory:":
            raise ValueError("Persistent database path required")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        with self.connection() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS engineering_runs(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    requested_at TEXT NOT NULL,
                    finished_at TEXT,
                    duration_s REAL,
                    exit_code INTEGER,
                    stdout TEXT NOT NULL DEFAULT '',
                    stderr TEXT NOT NULL DEFAULT ''
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS engineering_runs_recent ON engineering_runs(id DESC)")
            # A previous process crash leaves an interrupted run, never a false PASS.
            db.execute(
                "UPDATE engineering_runs SET status='INTERRUPTED', finished_at=? "
                "WHERE status='RUNNING'", (utc_now(),))

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

    def jobs(self):
        return [{
            "name": name,
            "description": DESCRIPTION[name],
            "requires_approval": True,
            "max_timeout_seconds": 120,
            "script": script,
        } for name, script in JOBS.items() if name in DESCRIPTION]

    def inventory(self):
        return inventory()

    def recent(self, limit=20):
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("Limit must be between 1 and 100")
        with self.connection() as db:
            rows = db.execute(
                "SELECT id,name,status,requested_at,finished_at,duration_s,"
                "exit_code,stdout,stderr FROM engineering_runs "
                "ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [
            dict(id=r[0], name=r[1], status=r[2], requested_at=r[3],
                 finished_at=r[4], duration_s=r[5], exit_code=r[6],
                 stdout=r[7], stderr=r[8]) for r in rows
        ]

    def run(self, name, *, operator_approved=False, timeout=60):
        if not isinstance(name, str) or name not in DESCRIPTION or name not in JOBS:
            raise ValueError("Job not in verified allowlist")
        if operator_approved is not True:
            raise PermissionError("This verification job requires explicit operator approval")
        if type(timeout) not in (int, float) or not 1 <= timeout <= 120:
            raise ValueError("Timeout must be between 1 and 120 seconds")
        if not self._lock.acquire(blocking=False):
            raise EngineeringBusy("Another verification job is running")
        run_id = None
        try:
            with self.connection() as db:
                cur = db.execute(
                    "INSERT INTO engineering_runs(name,status,requested_at) VALUES(?,?,?)",
                    (name, "RUNNING", utc_now()))
                run_id = cur.lastrowid
            # lab.run_job invokes a fixed Python script with shell=False.
            result = run_job(name, timeout=timeout)
            status = result["status"]
            if status not in {"PASS", "FAIL", "TIMEOUT", "NOT_INSTALLED"}:
                raise RuntimeError("Unexpected verification result")
            with self.connection() as db:
                db.execute(
                    "UPDATE engineering_runs SET status=?, finished_at=?, duration_s=?,"
                    "exit_code=?,stdout=?,stderr=? WHERE id=?",
                    (status, utc_now(), result.get("duration_s"),
                     result.get("exit_code"), str(result.get("stdout", ""))[-MAX_LOG:],
                     str(result.get("stderr", ""))[-MAX_LOG:], run_id))
        except Exception:
            if run_id is not None:
                with self.connection() as db:
                    db.execute(
                        "UPDATE engineering_runs SET status='ERROR', finished_at=? WHERE id=?",
                        (utc_now(), run_id))
            raise
        finally:
            self._lock.release()
        return self.recent(limit=1)[0]
