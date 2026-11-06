"""SQLite private lexical notes; never accesses personal files automatically."""
from __future__ import annotations
from contextlib import contextmanager
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import re
import sqlite3

TOKENS=re.compile(r"[^\W_]+", re.UNICODE)
def tokenize(text):
    return Counter(x.lower() for x in TOKENS.findall(text))

class MemoryIndex:
    def __init__(self, path):
        self.path=Path(path)
        if str(path)==":memory:":
            raise ValueError("Persistent file required")
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connection() as db:
            db.execute("CREATE TABLE IF NOT EXISTS notes(id INTEGER PRIMARY KEY,content TEXT NOT NULL,source TEXT NOT NULL,added_at TEXT NOT NULL)")
    @contextmanager
    def connection(self):
        db=sqlite3.connect(str(self.path),timeout=5)
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()
    def insert(self, content, source="manual"):
        if not isinstance(content,str) or not content.strip() or len(content)>20000:
            raise ValueError("Invalid note")
        if not isinstance(source,str) or not source.strip() or len(source)>200:
            raise ValueError("Invalid source")
        with self.connection() as db:
            cursor=db.execute("INSERT INTO notes(content,source,added_at) VALUES(?,?,?)",
                              (content,source,datetime.now(timezone.utc).isoformat()))
            return cursor.lastrowid
    def search(self, query, k=5):
        if not isinstance(query,str) or not query.strip() or type(k) is not int or not 1<=k<=50:
            raise ValueError("Invalid query or limit")
        targets=tokenize(query)
        with self.connection() as db:
            rows=db.execute("SELECT id,content,source FROM notes ORDER BY id DESC LIMIT 10000").fetchall()
        scored=[]
        for identifier,content,source in rows:
            words=tokenize(content)
            score=sum(min(n,words[word]) for word,n in targets.items())
            if score: scored.append((score,identifier,content,source))
        scored.sort(key=lambda x:(-x[0],-x[1]))
        return [dict(score=x[0],id=x[1],content=x[2],source=x[3]) for x in scored[:k]]
    def delete(self, identifier):
        if type(identifier) is not int or identifier<1:
            raise ValueError("Invalid identifier")
        with self.connection() as db:
            return db.execute("DELETE FROM notes WHERE id=?", (identifier,)).rowcount==1
