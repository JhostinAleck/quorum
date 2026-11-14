"""Append-only audit log, chained with hashes.

Every event includes the hash of the previous one. If somebody changes,
deletes or reorders an event, verify() detects it. Agents have no tool that
writes here: only the monitor records.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from typing import Any

_GENESIS = "0" * 64


def _canonical(event: dict[str, Any]) -> str:
    """The one text form of an event. It never fails: an event that cannot be recorded would be a hole in the log."""
    try:
        text = json.dumps(event, sort_keys=True, ensure_ascii=False, default=repr)
    except (TypeError, ValueError, RecursionError):     # odd keys, a cycle, too deep: keep what can be told
        text = json.dumps({str(k): v if v is None or isinstance(v, (str, int, float, bool)) else repr(v)
                           for k, v in event.items()}, sort_keys=True, ensure_ascii=False)
    # a lone surrogate cannot be encoded: it becomes its JSON escape, so the text can be hashed and saved
    return text.encode("utf-8", "backslashreplace").decode("utf-8")


class AuditLog:
    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []
        self._last = _GENESIS

    def record(self, **event: Any) -> dict[str, Any]:
        # round trip through JSON: the event is detached from the original objects
        body = json.loads(_canonical({"n": len(self._events), **event, "prev_hash": self._last}))
        body["hash"] = hashlib.sha256(_canonical(body).encode()).hexdigest()
        self._events.append(body)
        self._last = body["hash"]
        return body

    def verify(self) -> bool:
        previous = _GENESIS
        for n, event in enumerate(self._events):
            body = {k: v for k, v in event.items() if k != "hash"}
            if (event.get("n") != n or event.get("prev_hash") != previous
                    or event.get("hash") != hashlib.sha256(_canonical(body).encode()).hexdigest()):
                return False
            previous = event["hash"]
        return True

    def to_jsonl(self) -> str:
        return "\n".join(_canonical(e) for e in self._events)

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self._events)

    def __len__(self) -> int:
        return len(self._events)

    def __getitem__(self, i: int) -> dict[str, Any]:
        return self._events[i]
