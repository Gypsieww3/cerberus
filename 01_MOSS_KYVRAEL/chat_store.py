"""Local SQLite dialogue log for MOSS Lab; no network or background execution."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

MAX_STORED_MESSAGE = 12_000


class ChatStore:
    def __init__(self, path):
        self.path = Path(path)
        if str(path) == ":memory:":
            raise ValueError("Use persistent storage")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL CHECK(role IN ('user','assistant')),
                    content TEXT NOT NULL,
                    model TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS chat_by_id ON chat_messages(id)")

    @contextmanager
    def connection(self):
        db = sqlite3.connect(str(self.path), timeout=5)
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def append_exchange(self, prompt: str, reply: str, *, model: str, mode: str):
        for value in (prompt, reply):
            if not isinstance(value, str) or not 1 <= len(value) <= MAX_STORED_MESSAGE:
                raise ValueError("Invalid message length")
        if not isinstance(model, str) or not 1 <= len(model) <= 100:
            raise ValueError("Invalid model")
        if mode not in {"engineering", "research", "general"}:
            raise ValueError("Invalid chat mode")
        created = datetime.now(timezone.utc).isoformat()
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            for role, content in (("user", prompt), ("assistant", reply)):
                db.execute(
                    "INSERT INTO chat_messages(role,content,model,mode,created_at) VALUES(?,?,?,?,?)",
                    (role, content, model, mode, created)
                )

    def history(self, limit: int = 40):
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("Invalid history limit")
        with self.connection() as db:
            rows = db.execute(
                "SELECT id,role,content,model,mode,created_at "
                "FROM chat_messages ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(id=r[0], role=r[1], content=r[2], model=r[3],
                     mode=r[4], created_at=r[5]) for r in reversed(rows)]

    def context(self, max_messages=12, char_budget=12000):
        """Keep complete pairs and bound Ollama conversation context."""
        if type(max_messages) is not int or not 2 <= max_messages <= 24:
            raise ValueError("Invalid conversation window")
        if type(char_budget) is not int or not 500 <= char_budget <= 24000:
            raise ValueError("Invalid context budget")
        recent = self.history(limit=max_messages)
        result = []
        used = 0
        for item in reversed(recent):
            chars = len(item["content"])
            if used + chars > char_budget:
                break
            result.append({"role": item["role"], "content": item["content"]})
            used += chars
        return list(reversed(result))

    def clear(self):
        with self.connection() as db:
            db.execute("DELETE FROM chat_messages")
