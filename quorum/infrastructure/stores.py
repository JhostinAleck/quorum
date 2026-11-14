"""Backends of the Store port.

Any backend that satisfies the protocol works: memory, SQLite, Redis, a
database. The rest of the system only uses get, put and keys.
"""
from __future__ import annotations

import copy
import json
import sqlite3
import threading

from ..domain.labels import Label
from ..domain.repositories import Value


class MemoryStore:
    """In-memory backend. It copies on the way in and on the way out, so nobody
    can modify a stored value without going through the monitor."""

    def __init__(self) -> None:
        self._data: dict[str, Value] = {}

    def get(self, key: str) -> Value | None:
        value = self._data.get(key)
        return None if value is None else Value(copy.deepcopy(value.data), value.label)

    def put(self, key: str, value: Value) -> None:
        self._data[key] = Value(copy.deepcopy(value.data), value.label)

    def keys(self, prefix: str = "") -> list[str]:
        return sorted(k for k in self._data if k.startswith(prefix))


class SQLiteStore:
    """Persistent backend. Values must be JSON serializable."""

    def __init__(self, path: str = ":memory:") -> None:
        self._db = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self._lock = threading.Lock()
        self._db.execute("CREATE TABLE IF NOT EXISTS entries ("
                         "name TEXT PRIMARY KEY, data TEXT NOT NULL, label TEXT NOT NULL)")

    def get(self, key: str) -> Value | None:
        with self._lock:
            row = self._db.execute("SELECT data, label FROM entries WHERE name = ?", (key,)).fetchone()
        if row is None:
            return None
        return Value(json.loads(row[0]), Label.from_dict(json.loads(row[1])))

    def put(self, key: str, value: Value) -> None:
        data = json.dumps(value.data, ensure_ascii=False)
        label = json.dumps(value.label.to_dict(), ensure_ascii=False)
        with self._lock:
            self._db.execute(
                "INSERT INTO entries (name, data, label) VALUES (?, ?, ?) "
                "ON CONFLICT(name) DO UPDATE SET data = excluded.data, label = excluded.label",
                (key, data, label))

    def keys(self, prefix: str = "") -> list[str]:
        with self._lock:  # substr rather than LIKE: LIKE is case-insensitive
            rows = self._db.execute(
                "SELECT name FROM entries WHERE substr(name, 1, ?) = ? ORDER BY name",
                (len(prefix), prefix)).fetchall()
        return [row[0] for row in rows]
