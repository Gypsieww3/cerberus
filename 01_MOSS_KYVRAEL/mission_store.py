"""Persistent MOSS mission journal. Does not execute actions or tools."""
from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3
from uuid import uuid4

TRANSITIONS = {
    "pending": {"running", "cancelled"},
    "running": {"done", "failed", "cancelled"},
    "failed": {"pending", "cancelled"},
    "done": set(),
    "cancelled": set(),
}

def timestamp():
    return datetime.now(timezone.utc).isoformat()

class MissionStore:
    def __init__(self, path):
        self.path = Path(path)
        if str(path) == ":memory:":
            raise ValueError("Persistent file required")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript("""
              CREATE TABLE IF NOT EXISTS missions(
                id TEXT PRIMARY KEY, title TEXT NOT NULL, state TEXT NOT NULL,
                details_json TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS events(
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                mission_id TEXT NOT NULL REFERENCES missions(id),
                timestamp TEXT NOT NULL, previous TEXT, current TEXT NOT NULL, note TEXT NOT NULL);
              CREATE INDEX IF NOT EXISTS events_by_mission ON events(mission_id,seq);
            """)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(str(self.path), timeout=5)
        try:
            db.execute("PRAGMA foreign_keys=ON")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def add(self, title, details=None):
        if not isinstance(title, str) or not title.strip() or len(title) > 300:
            raise ValueError("Invalid title")
        if details is None:
            details = {}
        if not isinstance(details, dict):
            raise ValueError("Details must be a dictionary")
        payload = json.dumps(details, sort_keys=True, allow_nan=False)
        if len(payload) > 32000:
            raise ValueError("Details too large")
        mission_id = str(uuid4())
        now = timestamp()
        with self.connection() as db:
            db.execute("INSERT INTO missions VALUES(?,?,?,?,?,?)",
                       (mission_id,title.strip(),"pending",payload,now,now))
            db.execute("INSERT INTO events(mission_id,timestamp,previous,current,note) VALUES(?,?,?,?,?)",
                       (mission_id,now,None,"pending","created"))
        return mission_id

    def get(self, mission_id):
        with self.connection() as db:
            row = db.execute("SELECT id,title,state,details_json,created_at,updated_at FROM missions WHERE id=?",
                             (mission_id,)).fetchone()
        if row is None:
            raise KeyError(mission_id)
        return dict(id=row[0],title=row[1],state=row[2],details=json.loads(row[3]),
                    created_at=row[4],updated_at=row[5])

    def transition(self, mission_id, state, note=""):
        if state not in TRANSITIONS or not isinstance(note,str) or len(note)>2000:
            raise ValueError("Invalid state or note")
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT state FROM missions WHERE id=?", (mission_id,)).fetchone()
            if row is None:
                raise KeyError(mission_id)
            old=row[0]
            if state not in TRANSITIONS[old]:
                raise ValueError(f"Forbidden transition: {old} -> {state}")
            now=timestamp()
            db.execute("UPDATE missions SET state=?,updated_at=? WHERE id=?", (state,now,mission_id))
            db.execute("INSERT INTO events(mission_id,timestamp,previous,current,note) VALUES(?,?,?,?,?)",
                       (mission_id,now,old,state,note))
        return self.get(mission_id)

    def events(self, mission_id):
        self.get(mission_id)
        with self.connection() as db:
            rows=db.execute("SELECT seq,timestamp,previous,current,note FROM events WHERE mission_id=? ORDER BY seq",
                            (mission_id,)).fetchall()
        return [dict(seq=r[0], timestamp=r[1], previous=r[2], current=r[3], note=r[4]) for r in rows]

    def list(self, state=None, limit=100):
        if state is not None and state not in TRANSITIONS:
            raise ValueError("Invalid state")
        if type(limit) is not int or not 1<=limit<=1000:
            raise ValueError("Invalid limit")
        with self.connection() as db:
            ids=db.execute("SELECT id FROM missions WHERE (? IS NULL OR state=?) ORDER BY created_at DESC LIMIT ?",
                           (state,state,limit)).fetchall()
        return [self.get(r[0]) for r in ids]
