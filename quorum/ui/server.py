"""Web interface of the lab. Standard library only.

  python -m quorum.ui.server            # http://127.0.0.1:8765

Upload the bids (text, PDF or scans), choose honest or modified agents and
whether the gate enforces or only audits, and watch the episode step by step.

To open it to other machines, in .env:
  QUORUM_UI_HOST=0.0.0.0
  QUORUM_UI_PASSWORD=<access key>       # required: without it the server refuses to start
Listening on anything but loopback (which includes the container of
docker-compose.ui.yml, whatever port Compose publishes) the page always asks
for user "quorum" and that key.

State lives in memory: at start-up, and after Reset, the three agents are in
their honest version and no run is kept.

Each browser gets its own state, without accounts: the first visit receives an
anonymous random cookie (quorum_sid) and the server keeps one State per cookie.
Two people on the page at the same time each see only their own run, and Reset
only resets their own. States idle for SESSION_TTL are forgotten. With the agents
in their own containers the runs take turns, because the agents reach a single
monitor port; in one process they run at the same time.
"""
from __future__ import annotations

import base64
import hmac
import ipaddress
import json
import os
import re
import secrets
import sys
import threading
import time
from collections import OrderedDict
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from http.cookies import CookieError, SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from ..eval.attacks import side_tasks
from . import agents, documents, workflow

ROOT = Path(__file__).parent
EXAMPLES = ROOT / "examples"
MAX_BODY = 12_000_000
IMAGES = {"/logo.png": "logo.png", "/favicon.png": "favicon.png"}   # the only files served besides the page


def read_document(name: str, data: bytes) -> dict[str, Any]:
    """Extract the text of an uploaded bid and say how it was read. The value is not returned apart."""
    text, method = documents.extract(name, data)
    bid = workflow.parse_bid(text, name, method == documents.OCR)
    return {"name": name, "text": text, "preview": workflow.mask_value(text), "method": method,
            "scanned": bid.scanned, "supplier": bid.supplier, "digits": len(str(bid.value))}


COOKIE = "quorum_sid"
SESSION_TTL = 6 * 3600       # seconds a state is kept without visits
MAX_SESSIONS = 200           # beyond this the least recently used idle state is forgotten
MAX_RUNNING = 8              # episodes running at the same time, across all browsers
_SID = re.compile(r"[A-Za-z0-9_-]{32,64}")
# With the agents in containers there is one monitor port for them to reach, so one run at a time.
_CONTAINER_TURN = threading.Lock()


class State:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.run_id = 0
        self.touched = time.monotonic()
        self.waiting = False      # queued for the containers behind another browser's run
        self.reset()

    def reset(self) -> None:
        with self.lock:
            self.kind = workflow.INITIAL
            self.running = False
            self.events: list[dict[str, Any]] = []
            self.result: dict[str, Any] | None = None
            self.error: str | None = None
            self.run_id += 1   # discards a run in progress

    def view(self) -> dict[str, Any]:
        with self.lock:
            return {
                "kind": self.kind, "agents": workflow.status(self.kind),
                "running": self.running, "waiting": self.waiting, "events": list(self.events),
                "result": self.result, "error": self.error,
                "llm_available": workflow.llm_available(), "model": agents.model(),
                "containers": agents.remote(), "formats": documents.available(),
                "initial": self.kind == workflow.INITIAL and not self.events and not self.running,
            }

    def start(self, body: dict[str, Any]) -> None:
        kind = body.get("kind", workflow.INITIAL)
        workflow.k_of(kind)
        with self.lock:
            if self.running:
                raise ValueError("ya hay una corrida en curso")
            self.run_id += 1
            mine = self.run_id
            self.kind, self.running = kind, True
            self.events, self.result, self.error = [], None, None

        def emit(event: dict[str, Any]) -> None:
            with self.lock:
                if self.run_id == mine:
                    self.events.append(event)

        def episode() -> dict[str, Any]:
            return workflow.run(
                [(d.get("name", ""), d.get("text", ""), d.get("scanned", False))
                 for d in body.get("documents", [])],
                kind, defense=bool(body.get("defense", True)), engine=body.get("engine", "scripted"), emit=emit,
                side_tasks=side_tasks)   # with the model, the attacking roles get Frente 3's hidden task

        def work() -> None:
            result = error = None
            try:
                if agents.remote():
                    with self.lock:
                        self.waiting = True
                    with _CONTAINER_TURN:
                        with self.lock:
                            self.waiting = False
                            current = self.run_id == mine
                        if current:            # not reset while it waited
                            result = episode()
                else:
                    result = episode()
            except Exception as e:   # shown in the interface
                error = f"{type(e).__name__}: {e}"
            with self.lock:
                self.waiting = False
                if self.run_id == mine:
                    self.result, self.error, self.running = result, error, False

        threading.Thread(target=work, daemon=True).start()


class Sessions:
    """One State per browser, found by an anonymous cookie. No accounts, nothing stored on disk."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.states: OrderedDict[str, State] = OrderedDict()

    def get(self, sid: str | None) -> tuple[str, State, bool]:
        """(sid, state, new): the state of this cookie, or a fresh one with a new cookie."""
        now = time.monotonic()
        with self.lock:
            self._forget(now)
            if sid and _SID.fullmatch(sid) and sid in self.states:
                state = self.states[sid]
                self.states.move_to_end(sid)
                state.touched = now
                return sid, state, False
            sid = secrets.token_urlsafe(32)          # never one the browser proposed
            self.states[sid] = state = State()
            return sid, state, True

    def running(self) -> int:
        with self.lock:
            return sum(s.running for s in self.states.values())

    def _forget(self, now: float) -> None:
        idle = [sid for sid, s in self.states.items() if not s.running and now - s.touched > SESSION_TTL]
        for sid in idle:
            del self.states[sid]
        for sid in [sid for sid, s in self.states.items() if not s.running]:
            if len(self.states) < MAX_SESSIONS:
                break
            del self.states[sid]                       # oldest first: the dict is kept in use order


SESSIONS = Sessions()
PASSWORD: str | None = None      # None = no access control (only when listening on loopback)
USER = "quorum"


def is_loopback(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def access_key(host: str, environ: Mapping[str, str]) -> str | None:
    """The key the page asks for, or None for no access control.

    The decision depends only on the address this process listens on. Where
    Compose publishes the port (QUORUM_UI_BIND) says nothing about who else can
    reach it: in docker-compose.ui.yml the agents share a network with this
    container. So beyond loopback a key is required, and without one the
    server does not start.
    """
    key = (environ.get("QUORUM_UI_PASSWORD") or "").strip() or None
    if key is None and not is_loopback(host):
        raise SystemExit(f"quorum interface: refusing to listen on {host} without an access key. "
                         "Set QUORUM_UI_PASSWORD, or listen on 127.0.0.1 (QUORUM_UI_HOST).")
    return key


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        pass

    def _authorized(self) -> bool:
        if PASSWORD is None:
            return True
        header = self.headers.get("Authorization", "")
        try:
            user, _, key = base64.b64decode(header.removeprefix("Basic ")).decode().partition(":")
        except ValueError:
            user = key = ""
        # both comparisons always run, in constant time
        user_ok = hmac.compare_digest(user.encode(), USER.encode())
        key_ok = hmac.compare_digest(key.encode(), PASSWORD.encode())
        if user_ok and key_ok:
            return True
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Quorum", charset="UTF-8"')
        self.send_header("Content-Length", "0")
        self.end_headers()
        return False

    _new_sid: str | None = None

    def _state(self) -> State:
        """The state of this browser. A new one gets its cookie in the response."""
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
        except CookieError:
            pass
        sid, state, new = SESSIONS.get(cookie[COOKIE].value if COOKIE in cookie else None)
        if new:
            self._new_sid = sid
        return state

    def _send(self, body: bytes, content_type: str, code: int = 200) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if self._new_sid:
            self.send_header("Set-Cookie", f"{COOKIE}={self._new_sid}; Path=/; HttpOnly; SameSite=Strict; "
                                           f"Max-Age={SESSION_TTL}")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, data: Any, code: int = 200) -> None:
        self._send(json.dumps(data, ensure_ascii=False, default=str).encode(), "application/json; charset=utf-8", code)

    def do_GET(self) -> None:
        if not self._authorized():
            return
        if self.path in ("/", "/index.html"):
            self._state()                  # the cookie arrives with the page, before any call
            self._send((ROOT / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif self.path in IMAGES:
            self._send((ROOT / IMAGES[self.path]).read_bytes(), "image/png")
        elif self.path == "/api/state":
            self._json(self._state().view())
        elif self.path in ("/api/examples", "/api/examples/pdf"):
            files = sorted((EXAMPLES / "pdf").glob("*.pdf") if self.path.endswith("pdf")
                           else EXAMPLES.glob("oferta-*.md"))
            try:
                with ThreadPoolExecutor(max_workers=max(1, len(files))) as pool:   # the scans are read at the same time
                    self._json(list(pool.map(lambda p: read_document(p.name, p.read_bytes()), files)))
            except ValueError as e:
                self._json({"error": str(e)}, 400)
        else:
            self._json({"error": "no existe"}, 404)

    def do_POST(self) -> None:
        if not self._authorized():
            return
        size = int(self.headers.get("Content-Length") or 0)
        if size > MAX_BODY:
            return self._json({"error": "documentos demasiado grandes"}, 413)
        try:
            body = json.loads(self.rfile.read(size) or b"{}")
            if self.path == "/api/extract":
                return self._json(read_document(str(body.get("name", "")), base64.b64decode(body.get("data", ""))))
            if self.path not in ("/api/run", "/api/reset"):
                return self._json({"error": "no existe"}, 404)
            state = self._state()
            if self.path == "/api/run":
                if SESSIONS.running() >= MAX_RUNNING:
                    raise ValueError("hay demasiadas corridas en curso en este servidor; intenta en unos segundos")
                state.start(body)
            else:
                state.reset()
            self._json(state.view())
        except ValueError as e:
            self._json({"error": str(e)}, 400)


def main() -> None:
    global PASSWORD
    agents.load_env()
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("QUORUM_UI_PORT") or 8765)
    host = os.environ.get("QUORUM_UI_HOST") or "127.0.0.1"
    PASSWORD = access_key(host, os.environ)      # exits here rather than serve without a key beyond loopback
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"quorum interface at http://{host}:{port}", flush=True)
    if PASSWORD:
        print(f"access with user '{USER}' and the key in QUORUM_UI_PASSWORD", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
