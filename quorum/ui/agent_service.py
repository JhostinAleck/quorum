"""One agent as a long-running service, so the interface can run episode after episode.

`python -m quorum.launch agent` runs one agent once and exits. This is the same
agent kept alive: it waits to be told that it is its turn, then does exactly
what launch does, with a RemoteSession on the monitor (docs/protocolo.md).

  QUORUM_ROLE=registrar QUORUM_MONITOR_URL=http://lab:8080 python -m quorum.ui.agent_service

  GET  /health   role, model and hash of its system prompt
  POST /run      {"mode": "llm" | "scripted", "kind": str, "side_task": str}

Both need this agent's own token (QUORUM_TOKEN), the only one it has.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from ..adapters.agent_loop import run_agent
from ..adapters.http_client import RemoteSession
from ..scenarios.tender import KINDS, ROLE_STEPS, ROLES, SYSTEM, TASK
from . import agents

ROLE = ""
MONITOR = ""
TOKEN = ""


def prompt_hash(role: str) -> str:
    return hashlib.sha256(SYSTEM[role].encode("utf-8")).hexdigest()[:12]


def run(mode: str, kind: str, side_task: str = "") -> dict[str, Any]:
    if kind not in KINDS:
        raise ValueError(f"unknown episode kind: {kind!r}")
    session = RemoteSession(MONITOR, TOKEN)
    if session.role != ROLE:        # the identity comes from the token, not from the configuration
        raise RuntimeError(f"this token belongs to the role {session.role!r}, not to {ROLE!r}")
    if mode == "scripted":
        ROLE_STEPS[ROLE](session, kind)
        return {"role": ROLE, "mode": mode}
    system = SYSTEM[ROLE] if not side_task else f"{SYSTEM[ROLE]}\n\n{side_task}"
    messages = run_agent(session, agents.default_chat(), system=system, task=TASK[ROLE])
    calls = sum(len(m.get("tool_calls") or ()) for m in messages if m.get("role") == "assistant")
    return {"role": ROLE, "mode": "llm", "model": agents.model(), "tool_calls": calls}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        pass

    def _json(self, data: Any, code: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        given = self.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        if given and hmac.compare_digest(given.encode(), TOKEN.encode()):
            return True
        self._json({"error": "no autorizado"}, 401)
        return False

    def do_GET(self) -> None:
        if not self._authorized():
            return
        if self.path == "/health":
            self._json({"role": ROLE, "model": agents.model(), "has_key": agents.api_key() is not None,
                        "hash": prompt_hash(ROLE)})
        else:
            self._json({"error": "no existe"}, 404)

    def do_POST(self) -> None:
        if not self._authorized():
            return
        if self.path != "/run":
            return self._json({"error": "no existe"}, 404)
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
            self._json(run(str(body.get("mode", "scripted")), str(body.get("kind", "honest")),
                           str(body.get("side_task", ""))))
        except Exception as error:
            self._json({"error": f"{type(error).__name__}: {error}"}, 500)


def main() -> None:
    global ROLE, MONITOR, TOKEN
    agents.load_env()
    ROLE = os.environ.get("QUORUM_ROLE", "").strip()
    MONITOR = (os.environ.get("QUORUM_MONITOR_URL") or "http://127.0.0.1:8080").rstrip("/")
    # in a container the agent only has QUORUM_TOKEN; outside Docker one .env holds the three
    TOKEN = os.environ.get("QUORUM_TOKEN", "").strip() or (agents.token(ROLE) or "" if ROLE in ROLES else "")
    if ROLE not in ROLES or not TOKEN:
        sys.exit("set QUORUM_ROLE (registrar, evaluator or publisher) and its token in QUORUM_TOKEN")
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("QUORUM_AGENT_PORT") or 8000)
    host = os.environ.get("QUORUM_AGENT_HOST") or "127.0.0.1"
    print(f"quorum agent {ROLE!r} waiting for its turn on http://{host}:{port}, monitor at {MONITOR}", flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
