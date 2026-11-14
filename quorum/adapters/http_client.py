"""HTTP client: a session on a monitor that runs in another process.

    remote = RemoteSession("http://monitor:8080", token)
    remote.open_bid("bid-2")                 # the same call an agent makes on a local Session
    RemoteAdmin("http://monitor:8080", admin_token).state()

Once the monitor and each agent live in separate containers, an agent no
longer shares a process with the store or the audit log: the protocol in
docs/protocolo.md is its only door. RemoteSession mirrors what agents use of a
local Session (call, the attribute sugar, tool_specs, execute), so the same
agent code runs in one process or spread over containers. The identity and the
role come from the token, never from the agent.

Standard library only. The token travels to the monitor and nowhere else: no
proxy is used, no redirect is followed, and the token is kept out of every
error message and repr.
"""
from __future__ import annotations

import copy
import http.client
import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from functools import partial
from typing import Any, NamedTuple

from ..domain import (
    Blocked,
    InvalidArguments,
    InvalidConfiguration,
    PermissionDenied,
    QuorumError,
    QuotaExceeded,
    ToolError,
    UnknownTool,
)

__all__ = ["RemoteAdmin", "RemoteError", "RemoteSession"]

_ERRORS: dict[str, type[QuorumError]] = {
    cls.__name__: cls for cls in (PermissionDenied, QuotaExceeded, InvalidArguments, UnknownTool, ToolError)}


class RemoteError(QuorumError):
    """The monitor could not be reached, rejected the token or broke the protocol."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        return None             # a redirect would carry the token to another host


_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect)


def _protocol_error(error: urllib.error.HTTPError) -> str:
    """The 'Type: message' of a protocol error body, or the plain HTTP reason."""
    try:
        with error:
            detail = json.loads(error.read())["error"]
        return f"{detail['type']}: {detail['message']}"
    except (OSError, http.client.HTTPException, ValueError, KeyError, TypeError, RecursionError):
        return str(error.reason)


class _Client:
    def __init__(self, base_url: str, token: str, *, timeout: float = 30.0) -> None:
        if urllib.parse.urlsplit(base_url).scheme not in ("http", "https"):
            raise InvalidConfiguration(f"the monitor URL must be http or https: {base_url!r}")
        self._base_url, self._token, self._timeout = base_url.rstrip("/"), token, timeout

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._base_url!r})"

    def _clean(self, text: object) -> str:
        """The text of an error, without the token even if the other side echoed it."""
        return str(text).replace(self._token, "***") if self._token else str(text)

    def _request(self, method: str, path: str, body: bytes | None = None) -> dict[str, Any]:
        """One round trip. Returns the JSON object of a 2xx answer; anything else is a RemoteError."""
        where = f"{method} {path}"
        headers = {"Authorization": f"Bearer {self._token}", "Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(self._base_url + path, data=body, headers=headers, method=method)
        try:
            with _OPENER.open(request, timeout=self._timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as error:
            raise RemoteError(self._clean(f"{where}: HTTP {error.code} {_protocol_error(error)}")) from None
        except (OSError, http.client.HTTPException) as error:
            reason = getattr(error, "reason", None) or error
            raise RemoteError(self._clean(f"{where}: cannot reach the monitor at {self._base_url}: {reason}")) from None
        except ValueError:      # a header value that cannot be sent; its text would quote the token
            raise RemoteError(f"{where}: the request could not be sent, check the URL and the token") from None
        try:
            payload = json.loads(raw)
        except (ValueError, RecursionError):
            raise RemoteError(f"{where}: the response is not valid JSON") from None
        if not isinstance(payload, dict):
            raise RemoteError(f"{where}: the response is not a JSON object")
        return payload


class _Identity(NamedTuple):
    principal: str
    role: str
    specs: list[dict[str, Any]]
    params: dict[str, tuple[str, ...]]      # tool -> its parameter names, in the order of the spec


class RemoteSession(_Client):
    """An agent's session on a remote monitor. It behaves like a local Session for what agents use."""

    def __init__(self, base_url: str, token: str, *, timeout: float = 30.0) -> None:
        super().__init__(base_url, token, timeout=timeout)
        self._identity: _Identity | None = None

    def _load(self) -> _Identity:
        """Who this token is and which tools it has. Asked once: both are fixed when the monitor starts."""
        if self._identity is None:
            payload = self._request("GET", "/v1/tools")
            principal, role, specs = payload.get("principal"), payload.get("role"), payload.get("tools")
            try:
                params = {spec["name"]: tuple(spec["parameters"]["properties"]) for spec in specs}
                valid = (isinstance(principal, str) and isinstance(role, str) and isinstance(specs, list)
                         and all(isinstance(name, str) for name in params))
            except (KeyError, TypeError):
                valid = False
            if not valid:
                raise RemoteError("GET /v1/tools: malformed response")
            self._identity = _Identity(principal, role, specs, params)
        return self._identity

    @property
    def principal(self) -> str:
        return self._load().principal

    @property
    def role(self) -> str:
        return self._load().role

    def tool_specs(self) -> list[dict[str, Any]]:
        """The role's tools with their JSON Schema, in the format of functions.tool_specs."""
        return copy.deepcopy(self._load().specs)

    def _invoke(self, name: str, arguments: Mapping[str, Any]) -> dict[str, Any]:
        try:
            body = json.dumps({"tool": name, "arguments": dict(arguments)}, allow_nan=False).encode()
        except (TypeError, ValueError) as error:
            raise InvalidArguments(f"{name}: the arguments cannot be sent as JSON: {error}") from None
        return self._request("POST", "/v1/call", body)

    def execute(self, name: str, arguments: Mapping[str, Any] | None = None) -> str:
        """Run the tool and return the text a model should read. Never raises."""
        try:
            text = self._invoke(name, arguments or {}).get("text")
            if not isinstance(text, str):
                raise RemoteError("POST /v1/call: malformed response")
            return text
        except Exception as error:
            return f"ERROR: {self._clean(error)}"

    def call(self, name: str, /, *args: Any, **kwargs: Any) -> Any:
        """Call a tool. Returns its result, or a Blocked if the gate stopped it.
        Raises the domain error the monitor reported, or RemoteError if the monitor did not answer."""
        if args:
            params = self._load().params.get(name)
            if params is None:      # without its spec the positional arguments have no names
                raise UnknownTool(f"unknown tool: {name!r}")
            if len(args) > len(params):
                raise InvalidArguments(f"{name}: too many positional arguments")
            for param, value in zip(params, args, strict=False):
                if param in kwargs:
                    raise InvalidArguments(f"{name}: multiple values for argument {param!r}")
                kwargs[param] = value
        payload = self._invoke(name, kwargs)
        error, blocked = payload.get("error"), payload.get("blocked")
        if isinstance(error, dict):
            kind = error.get("type")
            raise _ERRORS.get(kind if isinstance(kind, str) else "", QuorumError)(
                self._clean(error.get("message", "")))
        if isinstance(blocked, dict):
            fields = [blocked.get(field) for field in ("tool", "policy", "reason")]
            if all(isinstance(field, str) for field in fields):
                return Blocked(*fields)
        elif payload.get("ok") is True and "result" in payload:
            return payload["result"]
        raise RemoteError("POST /v1/call: malformed response")

    def __getattr__(self, name: str) -> Any:
        # sugar: remote.publish("x") is remote.call("publish", "x")
        if not name.startswith("_") and name in self._load().params:
            return partial(self.call, name)
        raise AttributeError(name)


class RemoteAdmin(_Client):
    """The operator's view of a remote monitor: it reads the state, it cannot call tools."""

    def __init__(self, base_url: str, admin_token: str, *, timeout: float = 30.0) -> None:
        super().__init__(base_url, admin_token, timeout=timeout)

    def state(self) -> dict[str, Any]:
        """Trajectories, emissions, blocks and audit log, as GET /v1/admin/state returns them."""
        payload = self._request("GET", "/v1/admin/state")
        if payload.get("ok") is not True:
            raise RemoteError("GET /v1/admin/state: malformed response")
        return payload
