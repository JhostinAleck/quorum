"""HTTP server: the reference monitor as a network service.

    with MonitorServer(quorum, {token: "registrar"}, admin_token=secret) as server:
        ...     # the agent in another container talks to server.url

While agents share a process with the monitor, only convention keeps them away
from the store, the audit log and each other's sessions. Behind this server
each agent runs in its own container and the protocol in docs/protocolo.md is
its only door: it can list its tools and call them. Every call still goes
through Session.call, so labels, quotas, the gate and the audit log work
exactly as they do in one process.

Identity comes from the bearer token and from nothing else. The operator maps
each token to one principal when the server is built, the policy gives that
principal its role, and no field of a request can change either. Tokens are
kept only as SHA-256 digests and every request is compared in constant time
against all of them, so a lookup does not tell which token matched, and no
token can end up in a response, an error, the audit log or a log line.

Standard library only. A request can fail, but it cannot take the server down
or get a traceback back: a failed call is returned as data, the same text
functions.execute gives a model.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import socket
import threading
import time
from collections.abc import Callable, Mapping
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from ..application import Quorum, Session
from ..domain import (
    Blocked,
    InvalidArguments,
    InvalidConfiguration,
    PermissionDenied,
    QuotaExceeded,
    ToolError,
    UnknownTool,
    is_id,
)
from .functions import to_text, tool_specs

__all__ = ["MAX_BODY", "MIN_TOKEN", "MonitorServer"]

MAX_BODY = 1024 * 1024      # bytes a request body may have
MIN_TOKEN = 16              # characters a token must have
_ADMIN = "<admin>"          # who the administration token is. Not an identifier, so never a principal
_POLL = 0.05                # seconds between checks for stop()
_LINGER = 2.0               # seconds a rejected client gets to finish sending and read its answer
# path -> (method, is it for the administration token?). None: open to anyone
_ROUTES: dict[str, tuple[str, bool | None]] = {
    "/health": ("GET", None), "/v1/tools": ("GET", False), "/v1/call": ("POST", False),
    "/v1/admin/state": ("GET", True)}
# the error types of the contract, most specific first
_CALL_ERRORS = (QuotaExceeded, PermissionDenied, InvalidArguments, UnknownTool, ToolError)


class _Failure(Exception):
    """A protocol error. It ends the request with its status and the error body of the contract."""

    def __init__(self, status: int, kind: str, message: str, headers: Mapping[str, str] | None = None) -> None:
        super().__init__(message)
        self.status, self.kind, self.headers = status, kind, dict(headers or {})


class _Hangup(Exception):
    """The client went away in the middle of its request. There is nobody to answer."""


def _error(kind: str, message: str) -> dict[str, Any]:
    return {"ok": False, "error": {"type": kind, "message": message}}


def _encode(payload: Any) -> bytes:
    # backslashreplace turns a lone surrogate into its JSON escape, so any text a tool returns can travel
    return json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8", "backslashreplace")


def _plain(value: Any) -> Any:
    """The nearest thing JSON can carry. One odd value in a trajectory must not cost the operator the state."""
    if isinstance(value, Mapping):
        return {key if key is None or isinstance(key, (str, int, float, bool)) else str(key): _plain(item)
                for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value if value is None or isinstance(value, (str, int, float, bool)) else str(value)


def _digest(token: str) -> bytes:
    return hashlib.sha256(token.encode("utf-8", "backslashreplace")).digest()


def _require_token(token: object, what: str) -> None:
    # the messages name whose token it is, never the token
    if not isinstance(token, str) or len(token) < MIN_TOKEN:
        raise InvalidConfiguration(f"{what} must be a string of at least {MIN_TOKEN} characters")
    if not token.isascii() or not token.isprintable() or " " in token:
        raise InvalidConfiguration(f"{what} must be printable ASCII without spaces, to travel in a header")


class MonitorServer:
    """Serves one monitor to its agents. tokens is {token: principal}."""

    def __init__(self, quorum: Quorum, tokens: Mapping[str, str], *, admin_token: str | None = None,
                 host: str = "127.0.0.1", port: int = 0,
                 extra_state: Callable[[], Mapping[str, Any]] | None = None) -> None:
        self._quorum, self._extra_state = quorum, extra_state
        self._identities = self._validate(quorum, tokens, admin_token)
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._serving = self._stopped = False
        self._server = _Server((host, port), _Handler)      # binds now, so the url is known before serving
        self._server.owner = self
        self.url = "http://{}:{}".format(*self._server.server_address[:2])

    @staticmethod
    def _validate(quorum: Quorum, tokens: Mapping[str, str],
                  admin_token: str | None) -> tuple[tuple[bytes, str], ...]:
        """Fail at start-up, not at the first request. Returns (digest of the token, who it is) pairs."""
        if not isinstance(tokens, Mapping) or not tokens:
            raise InvalidConfiguration("the server needs at least one agent token")
        open_sessions, identities, principals = quorum.sessions, [], set()
        for token, principal in tokens.items():
            # a session somebody already opened is served as it is; any other must be one the monitor can open
            if not isinstance(principal, str) or not (
                    principal in open_sessions or (is_id(principal) and principal in quorum.policy.roles)):
                raise InvalidConfiguration(f"a token is for {principal!r}, which is not a role of the policy")
            if principal in principals:
                raise InvalidConfiguration(f"two tokens for the same principal: {principal!r}")
            _require_token(token, f"the token of {principal!r}")
            principals.add(principal)
            identities.append((_digest(token), principal))
        if admin_token is not None:
            _require_token(admin_token, "the administration token")
            if admin_token in tokens:
                raise InvalidConfiguration("the administration token is also the token of an agent")
            identities.append((_digest(admin_token), _ADMIN))
        return tuple(identities)

    # --- life cycle -------------------------------------------------------------

    def start(self) -> None:
        """Serve from a background thread."""
        with self._lock:
            self._require_not_stopped()
            if self._thread is None:
                self._serving = True
                self._thread = threading.Thread(target=self._server.serve_forever, kwargs={"poll_interval": _POLL},
                                                name="quorum-monitor-server", daemon=True)
                self._thread.start()

    def serve_forever(self) -> None:
        """Serve from the calling thread, until stop() is called from another one."""
        with self._lock:
            self._require_not_stopped()
            self._serving = True
        try:
            self._server.serve_forever(poll_interval=_POLL)
        finally:
            self._serving = False

    def stop(self) -> None:
        """Stop serving and release the port. Calling it again does nothing."""
        with self._lock:
            thread, serving = self._thread, self._serving
            self._thread, self._serving, self._stopped = None, False, True
        if serving:     # shutdown() waits for the serving loop, so it would hang if there were none
            self._server.shutdown()
        if thread is not None:
            thread.join()
        self._server.server_close()

    def _require_not_stopped(self) -> None:
        if self._stopped:
            raise InvalidConfiguration("this server was stopped and its port released: build a new one")

    def __enter__(self) -> MonitorServer:
        self.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.stop()

    # --- the protocol -------------------------------------------------------------

    def _answer(self, method: str, path: str, authorization: str | None, body: Callable[[], Any]) -> dict[str, Any]:
        """The response to a request, or the _Failure that ends it. The body is read only for a known agent."""
        route = _ROUTES.get(path)
        if route is None:
            raise _Failure(404, "NotFound", "unknown route")
        allowed, for_admin = route
        if method != allowed:
            raise _Failure(405, "MethodNotAllowed", f"this route only accepts {allowed}", {"Allow": allowed})
        if for_admin is None:
            return {"ok": True}
        who = self._identify(authorization)
        if who is None:
            raise _Failure(401, "Unauthorized", "missing or unknown token", {"WWW-Authenticate": "Bearer"})
        if (who == _ADMIN) != for_admin:
            raise _Failure(403, "Forbidden",
                           "this route is for " + ("the administration token" if for_admin else "agent tokens"))
        if for_admin:
            return self._state()
        session = self._session(who)
        if method == "GET":
            return {"ok": True, "principal": session.principal, "role": session.role.name,
                    "tools": tool_specs(session)}
        return self._call(session, body())

    def _identify(self, authorization: str | None) -> str | None:
        """The principal behind a bearer token, _ADMIN for the administration token, None if unknown."""
        scheme, _, presented = (authorization or "").strip().partition(" ")
        digest, who = _digest(presented.strip()), None
        for known, identity in self._identities:    # no early exit: every token is compared, every time
            if hmac.compare_digest(known, digest):
                who = identity
        return who if scheme.lower() == "bearer" else None

    def _session(self, principal: str) -> Session:
        """The session of a principal. It is opened the first time its token is used."""
        with self._lock:    # two first requests at once must not open it twice
            session = self._quorum.sessions.get(principal)
            return session if session is not None else self._quorum.session(principal)

    def _call(self, session: Session, body: Any) -> dict[str, Any]:
        if not isinstance(body, dict):
            raise _Failure(400, "BadRequest", "the body must be a JSON object")
        tool, arguments = body.get("tool"), body.get("arguments")
        if not isinstance(tool, str):
            raise _Failure(400, "BadRequest", "'tool' is required and must be a string")
        if arguments is not None and not isinstance(arguments, dict):
            raise _Failure(400, "BadRequest", "'arguments' must be a JSON object")
        try:
            result = session.call(tool, **(arguments or {}))
            if isinstance(result, Blocked):
                blocked = {"tool": result.tool, "policy": result.policy, "reason": result.reason}
                return {"ok": True, "blocked": blocked, "text": str(result)}
            payload = {"ok": True, "result": result, "text": to_text(result)}
            _encode(payload)    # a result that cannot travel is an error of the call, not a broken response
            return payload
        except Exception as error:
            kind = next((c.__name__ for c in type(error).__mro__ if c in _CALL_ERRORS), "QuorumError")
            return {**_error(kind, str(error)), "text": f"ERROR: {error}"}

    def _state(self) -> dict[str, Any]:
        quorum = self._quorum
        try:
            extra = _plain(dict(self._extra_state())) if self._extra_state is not None else {}
        except Exception as error:      # a broken grader must not hide what the monitor saw
            extra = {"error": f"{type(error).__name__}: {error}"}
        return {
            "ok": True,
            "trajectories": {principal: _plain(session.trajectory)
                             for principal, session in quorum.sessions.items()},
            "emissions": [{"sink": e.sink, "principal": e.principal, "arguments": _plain(e.arguments)}
                          for e in quorum.emitted()],
            "blocks": quorum.blocks(),
            "audit_log": list(quorum.audit_log),
            "audit_log_valid": quorum.audit_log.verify(),
            "extra": extra,
        }


class _Server(ThreadingHTTPServer):
    daemon_threads = True           # a client that never finishes must not keep the process alive
    request_queue_size = 128        # agents start together, and the default backlog of 5 would turn some away
    owner: MonitorServer

    def handle_error(self, request: Any, client_address: Any) -> None:
        pass    # a dropped connection is not news, and the default prints a traceback


class _Handler(BaseHTTPRequestHandler):
    """The HTTP mechanics of one request. What to answer is decided by MonitorServer._answer.

    The protocol version stays HTTP/1.0: one request per connection, so a body
    that was left unread can never be taken for the next request.
    """
    server: _Server
    timeout = 30                    # seconds a silent client may hold a thread

    def __getattr__(self, name: str) -> Any:
        if name.startswith("do_"):  # every verb takes the same path, so an odd one gets a 405 in JSON
            return self._dispatch
        raise AttributeError(name)

    def _dispatch(self) -> None:
        self._unread = self.headers.get("Content-Length", "0") != "0" or "Transfer-Encoding" in self.headers
        headers: Mapping[str, str] = {}
        try:
            path = self.path.partition("?")[0]
            payload = self.server.owner._answer(self.command, path, self.headers.get("Authorization"), self._body)
            status, body = 200, _encode(payload)
        except _Failure as failure:
            status, body, headers = failure.status, _encode(_error(failure.kind, str(failure))), failure.headers
        except _Hangup:
            return
        except Exception as error:  # never a traceback, never a dead server
            status, body = 500, _encode(_error("InternalError", type(error).__name__))
        try:
            self._send(status, body, headers)
            if self._unread:
                self._linger()
        except OSError:
            pass                    # the client went away

    def _body(self) -> Any:
        """The JSON value of the request body. Its size is checked on the header, before reading a byte."""
        declared = self.headers.get("Content-Length")
        if declared is None:
            raise _Failure(400, "BadRequest", "a POST needs a Content-Length")
        if not (declared.isascii() and declared.isdigit()):
            raise _Failure(400, "BadRequest", "invalid Content-Length")
        if len(declared) > 12 or int(declared) > MAX_BODY:
            raise _Failure(413, "PayloadTooLarge", f"the body is larger than {MAX_BODY} bytes")
        try:
            raw = self.rfile.read(int(declared))
        except OSError:
            raise _Hangup from None
        self._unread = False
        if len(raw) < int(declared):
            raise _Failure(400, "BadRequest", "the body is shorter than its Content-Length")
        try:
            body = json.loads(raw.decode("utf-8"))
            # a lone surrogate cannot be hashed into the audit log: the tool would run and leave no event
            json.dumps(body, ensure_ascii=False).encode("utf-8")
        except (ValueError, RecursionError):
            raise _Failure(400, "BadRequest", "the body is not valid JSON in UTF-8") from None
        return body

    def _send(self, status: int, body: bytes, headers: Mapping[str, str]) -> None:
        if self.request_version == "HTTP/0.9":      # a request line with no version, or one that did not parse:
            self.request_version = "HTTP/1.0"       # without this the answer would have no status line
        self.send_response(status)
        for name, value in {"Content-Type": "application/json; charset=utf-8", "Content-Length": str(len(body)),
                            "Cache-Control": "no-store", **headers}.items():
            self.send_header(name, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _linger(self) -> None:
        """Let a client that is still sending its body read the answer.

        Closing a socket with unread input resets the connection, and the
        client would see that instead of the 401 or the 413 it was sent.
        """
        deadline = time.monotonic() + _LINGER
        self.connection.shutdown(socket.SHUT_WR)
        while (left := deadline - time.monotonic()) > 0:
            self.connection.settimeout(left)
            if not self.rfile.read1(65536):
                break

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        # only the standard library calls this, for a request it could not parse. Its own page is HTML
        # and quotes the request line
        try:
            self._send(400, _encode(_error("BadRequest", "malformed HTTP request")), {})
        except OSError:
            pass

    def version_string(self) -> str:
        return "quorum"             # the default advertises the Python version

    def log_message(self, format: str, *args: Any) -> None:
        pass    # the default writes client-controlled text to stderr. The audit log is the record
