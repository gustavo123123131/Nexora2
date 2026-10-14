"""Durable JSON records in local SQLite (passwords are never stored here)."""
import json
import sqlite3
import threading
from pathlib import Path


class Database:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "nexora.sqlite3"
        self.lock = threading.RLock()
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("CREATE TABLE IF NOT EXISTS records (kind TEXT NOT NULL, id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        if not self.one("settings", "settings"):
            self.save("settings", {"id": "settings", "max_active": 3, "warn_duplicate_proxy": True})

    def connect(self):
        db = sqlite3.connect(str(self.path), timeout=30)
        db.row_factory = sqlite3.Row
        return db

    def all(self, kind):
        with self.lock, self.connect() as db:
            rows = db.execute("SELECT payload FROM records WHERE kind=? ORDER BY rowid DESC", (kind,)).fetchall()
        return [json.loads(r["payload"]) for r in rows]

    def one(self, kind, identifier):
        with self.lock, self.connect() as db:
            row = db.execute("SELECT payload FROM records WHERE kind=? AND id=?", (kind, identifier)).fetchone()
        return json.loads(row["payload"]) if row else None

    def save(self, kind, data):
        if kind not in ("profiles", "proxies", "settings"):
            raise ValueError("Invalid record kind")
        with self.lock, self.connect() as db:
            db.execute("INSERT INTO records(kind,id,payload) VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload", (kind, data["id"], json.dumps(data, ensure_ascii=False)))
        return data

    def remove(self, kind, identifier):
        with self.lock, self.connect() as db:
            return db.execute("DELETE FROM records WHERE kind=? AND id=?", (kind, identifier)).rowcount > 0

    def settings(self):
        return self.one("settings", "settings")
