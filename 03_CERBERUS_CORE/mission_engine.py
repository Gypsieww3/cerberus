"""Supervised, predefined CERBERUS engineering checks in a locked-down Docker sandbox.

No user supplied command, image, path, URL, environment variable or arguments.
One job at a time. Explicit one-use approval tickets. SQLite audit history.
"""
from __future__ import annotations

from collections import deque
from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import secrets
import sqlite3
import subprocess
from threading import Event, Lock, Thread
import time
from uuid import uuid4, UUID

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = Path.home() / ".cerberus" / "control_plane" / "missions.sqlite3"
IMAGE = "python:3.12-alpine"
TASKS = {
    "engineering_tests": {
        "title": "Regressões do laboratório",
        "description": "Testes Python existentes no portefólio, em Docker sem rede",
        "args": ("python", "tools/test_engineering.py"), "limit": 60
    },
    "riscv_reference": {
        "title": "Referência RISC-V",
        "description": "Verificador de instruções de referência, não validação física de chip",
        "args": ("python", "09_HARDWARE/RV32I_TRACE/tools/verify_reference.py"), "limit": 20
    },
    "robotics_static": {
        "title": "Modelo estático de robótica",
        "description": "Cálculo sintético de torque, sem controlo de motores",
        "args": ("python", "07_ROBOTICA/calcular.py",
                 "--mass-kg", "2", "--lever-m", "0.2", "--gear-ratio", "10",
                 "--efficiency", "0.6"), "limit": 20
    }
}

def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def catalog():
    return [{"id": key, "title": t["title"], "description": t["description"],
             "timeout_seconds": t["limit"], "isolation": "Docker: no network, read-only"}
            for key, t in TASKS.items()]

@dataclass(frozen=True)
class Result:
    state: str
    exit_code: int | None
    output: str

def _bounded_output(text):
    # Best-effort redaction of common token formats (not a secrets audit).
    value = re.sub(r"(?i)(Bearer[ ]+)[^\s]+", r"\1[REDACTED]", text)
    value = re.sub(r"(?:gh[opusr]_[A-Za-z0-9_]{15,}|sk-[A-Za-z0-9_-]{15,})", "[REDACTED]", value)
    return value[-5000:]

def docker_runner(task, mission_id, cancelled, *, repo=ROOT):
    """Run an approved fixed command in Docker; never fall back to host execution."""
    if cancelled.is_set():
        return Result("CANCELLED", None, "Cancelado antes do início")
    name = "cerberus-test-" + mission_id.replace("-", "")[:18]
    argv = [
        "docker", "run", "--rm", "--pull=never", "--name", name,
        "--network", "none", "--read-only",
        "--cpus", "1", "--memory", "384m", "--memory-swap", "384m",
        "--pids-limit", "64", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--user", "65534:65534", "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m",
        "--mount", "type=bind,source=" + str(repo) + ",target=/workspace,readonly",
        "--workdir", "/workspace",
        "--env", "PYTHONDONTWRITEBYTECODE=1", "--env", "HOME=/tmp",
        IMAGE, *task["args"]
    ]
    try:
        process = subprocess.Popen(argv, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
    except (OSError, ValueError):
        return Result("FAILED", None, "Docker não foi iniciado. Verifica a instalação local.")

    # Continuously drain output with bounded memory. A faulty test cannot fill
    # the host's RAM by printing unbounded logs.
    tail = deque(maxlen=8)
    def collect_output():
        try:
            while True:
                block = process.stdout.read(2048)
                if not block:
                    break
                tail.append(block)
        finally:
            process.stdout.close()

    reader = Thread(target=collect_output, daemon=True)
    reader.start()
    deadline = time.monotonic() + task["limit"]
    outcome = None
    try:
        while True:
            if cancelled.is_set():
                outcome = "CANCELLED"
                break
            if time.monotonic() >= deadline:
                outcome = "TIMED_OUT"
                break
            try:
                process.wait(timeout=0.25)
                break
            except subprocess.TimeoutExpired:
                continue
        if outcome is not None:
            # Terminate the named container, not only the Docker CLI process.
            try:
                subprocess.run(["docker", "rm", "-f", name],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               timeout=4, check=False)
            except (OSError, subprocess.TimeoutExpired):
                pass
        else:
            outcome = "PASSED" if process.returncode == 0 else "FAILED"
        return_code = process.poll()
        reader.join(timeout=2)
        return Result(outcome, return_code, _bounded_output(b"".join(tail).decode("utf-8", "replace")))
    finally:
        if process.poll() is None:
            process.kill()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass
        reader.join(timeout=2)

class JobSupervisor:
    def __init__(self, db_path=DEFAULT_DB, runner=docker_runner):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.runner = runner
        self._lock = Lock()
        self._tickets = {}
        self._active = None
        self._cancel_event = None
        self._thread = None
        with self._db() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS missions (
                id TEXT PRIMARY KEY, task_id TEXT NOT NULL, state TEXT NOT NULL,
                created TEXT NOT NULL, finished TEXT, exit_code INTEGER,
                output TEXT NOT NULL DEFAULT ''
            )""")
            conn.execute("UPDATE missions SET state='INTERRUPTED', finished=? WHERE state IN ('RUNNING','CANCELLING')",
                         (utcnow(),))

    @contextmanager
    def _db(self):
        with closing(sqlite3.connect(str(self.db_path), timeout=5)) as conn:
            with conn:
                yield conn

    def prepare(self, task_id):
        if type(task_id) is not str or task_id not in TASKS:
            raise ValueError("Missão desconhecida")
        ticket = secrets.token_urlsafe(32)
        with self._lock:
            # Discard stale tickets and avoid an unbounded in-memory queue.
            now = time.monotonic()
            self._tickets = {k: v for k, v in self._tickets.items() if v[1] > now}
            if len(self._tickets) >= 16:
                raise RuntimeError("Demasiadas confirmações pendentes")
            self._tickets[ticket] = (task_id, now + 90)
        return {"ticket": ticket, "task_id": task_id, "task": next(
            item for item in catalog() if item["id"] == task_id
        ), "expires_in_seconds": 90}

    def start(self, ticket, approved):
        if approved is not True or not isinstance(ticket, str):
            raise ValueError("Confirmação explícita necessária")
        with self._lock:
            item = self._tickets.pop(ticket, None)
            if item is None or item[1] <= time.monotonic():
                raise ValueError("Confirmação inválida ou expirada")
            if self._active is not None:
                raise RuntimeError("Já existe uma missão em execução")
            mission_id = str(uuid4())
            self._active = mission_id
            self._cancel_event = Event()
            with self._db() as conn:
                conn.execute("INSERT INTO missions(id,task_id,state,created) VALUES(?,?,?,?)",
                             (mission_id, item[0], "RUNNING", utcnow()))
            self._thread = Thread(target=self._execute, args=(mission_id, item[0], self._cancel_event),
                                  daemon=True, name="cerberus-mission")
            self._thread.start()
            return self.get(mission_id)

    def _execute(self, mission_id, task_id, stop):
        try:
            result = self.runner(TASKS[task_id], mission_id, stop)
            state = "CANCELLED" if stop.is_set() else result.state
            if state not in ("PASSED", "FAILED", "TIMED_OUT", "CANCELLED"):
                state = "FAILED"
            code, output = result.exit_code, _bounded_output(result.output)
        except Exception:
            state, code, output = "FAILED", None, "Falha interna na execução da missão"
        with self._lock:
            with self._db() as conn:
                conn.execute("UPDATE missions SET state=?, finished=?, exit_code=?, output=? WHERE id=?",
                             (state, utcnow(), code, output, mission_id))
            if self._active == mission_id:
                self._active = None
                self._cancel_event = None

    def cancel(self, mission_id):
        try:
            UUID(mission_id)
        except (TypeError, ValueError, AttributeError):
            raise ValueError("Identificador inválido")
        with self._lock:
            if self._active != mission_id:
                raise ValueError("Missão não está em execução")
            self._cancel_event.set()
            with self._db() as conn:
                conn.execute("UPDATE missions SET state='CANCELLING' WHERE id=?", (mission_id,))
        return {"id": mission_id, "state": "CANCELLING"}

    def shutdown(self, timeout=8):
        """Request cancellation of the active mission on a graceful server exit."""
        with self._lock:
            mission_id = self._active
            if mission_id is not None and self._cancel_event is not None:
                self._cancel_event.set()
            thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=timeout)

    def get(self, mission_id):
        try:
            UUID(mission_id)
        except (TypeError, ValueError, AttributeError):
            raise ValueError("Identificador inválido")
        with self._db() as conn:
            conn.row_factory = sqlite3.Row
            record = conn.execute("SELECT id,task_id,state,created,finished,exit_code,output FROM missions WHERE id=?",
                                  (mission_id,)).fetchone()
        return dict(record) if record else None

    def recent(self):
        with self._db() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT id,task_id,state,created,finished,exit_code,output FROM missions ORDER BY created DESC, rowid DESC LIMIT 15").fetchall()
        return [dict(row) for row in rows]
