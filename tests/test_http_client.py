"""The HTTP client, tested against a fake monitor that answers what docs/protocolo.md says.

The fake serves canned responses, so these tests do not depend on the real
server. The last test runs against the real one and skips itself while
quorum.adapters.http_server does not exist.
"""
import asyncio
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import mini
import pytest

from quorum import (
    Blocked,
    InvalidArguments,
    InvalidConfiguration,
    PermissionDenied,
    Policy,
    QuorumError,
    QuotaExceeded,
    Role,
    ToolError,
    UnknownTool,
    new_monitor,
    tool,
)
from quorum.adapters import functions
from quorum.adapters.http_client import RemoteAdmin, RemoteError, RemoteSession

AGENT, READER, ADMIN = "agent-token-5f1c-27d0", "reader-token-c4a1-88e3", "admin-token-9b2e-61fa"


def _spec(name, **params):
    properties = {p: {"type": kind, "description": f"The {p}."} for p, kind in params.items()}
    return {"name": name, "description": f"Tool {name}.",
            "parameters": {"type": "object", "properties": properties, "required": list(params),
                           "additionalProperties": False}}


SPECS = [_spec("open_bid", ref="string"), _spec("write", key="string", data="string"),
         _spec("publish", awardee="string", text="string"), _spec("read_messages")]
REASON = "restricted sources not authorized for this destination: sealed.bid-2"
CALLS = {
    "open_bid": {"ok": True, "result": 487311902, "text": "487311902"},
    "write": {"ok": True, "result": "stored", "text": "stored"},
    "read_messages": {"ok": True, "result": None, "text": "null"},
    "publish": {"ok": True, "blocked": {"tool": "publish", "policy": "P1", "reason": REASON},
                "text": f"BLOCKED by policy P1: {REASON}"},
}
STATE = {"ok": True, "trajectories": {"registrar": [{"tool": "open_bid", "args": {"ref": "bid-2"}, "result": 1}]},
         "emissions": [], "blocks": [], "audit_log": [], "audit_log_valid": True, "extra": {"leak": False}}


def _failure(kind, message="nope"):
    return {"ok": False, "error": {"type": kind, "message": message}, "text": f"ERROR: {message}"}


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, status, payload):
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _fail(self, status, kind, message):
        self._send(status, {"ok": False, "error": {"type": kind, "message": message}})

    def _handle(self):
        fake = self.server
        length = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(length)) if length else None
        fake.seen.append((self.command, self.path, body))
        token = (self.headers.get("Authorization") or "").removeprefix("Bearer ")
        if fake.raw is not None:
            self._send(200, fake.raw)
        elif token not in (AGENT, ADMIN):
            # ruder than the real server, which never echoes a token
            self._fail(401, "Unauthorized", f"unknown token {token}")
        elif (token == ADMIN) != self.path.startswith("/v1/admin/"):
            self._fail(403, "Forbidden", "this token cannot use this route")
        elif (self.command, self.path) == ("GET", "/v1/tools"):
            self._send(200, {"ok": True, "principal": "registrar-1", "role": "registrar", "tools": SPECS})
        elif (self.command, self.path) == ("POST", "/v1/call"):
            self._send(200, fake.calls.get(body["tool"], _failure("UnknownTool", f"unknown tool: {body['tool']!r}")))
        elif (self.command, self.path) == ("GET", "/v1/admin/state"):
            self._send(200, STATE)
        else:
            self._fail(404, "NotFound", "unknown route")

    do_GET = do_POST = _handle


class FakeMonitor(ThreadingHTTPServer):
    def __init__(self):
        super().__init__(("127.0.0.1", 0), _Handler)
        self.url = f"http://127.0.0.1:{self.server_address[1]}"
        self.calls = dict(CALLS)    # tool -> canned answer of /v1/call
        self.raw = None             # bytes: every route answers 200 with this body
        self.seen = []              # (method, path, JSON body) of every request

    def count(self, path):
        return sum(1 for _, seen, _ in self.seen if seen == path)


@pytest.fixture
def fake():
    server = FakeMonitor()
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()
    thread.join()


@pytest.fixture
def remote(fake):
    return RemoteSession(fake.url, AGENT, timeout=5)


@pytest.fixture
def dead_url():
    with socket.socket() as probe:      # a port nobody listens on
        probe.bind(("127.0.0.1", 0))
        return f"http://127.0.0.1:{probe.getsockname()[1]}"


# --- identity and tools ---------------------------------------------------------

def test_principal_and_role_come_from_the_token_and_are_asked_once(fake, remote):
    assert fake.seen == []                                    # nothing is asked until it is needed
    assert (remote.principal, remote.role) == ("registrar-1", "registrar")
    assert (remote.principal, remote.role) == ("registrar-1", "registrar")
    assert fake.seen == [("GET", "/v1/tools", None)]


def test_tool_specs_are_the_ones_the_server_sends(fake, remote):
    specs = remote.tool_specs()
    assert specs == SPECS
    specs[0]["name"] = "changed"                              # the caller's copy does not reach the cache
    assert remote.tool_specs() == SPECS and fake.count("/v1/tools") == 1


def test_the_base_url_may_end_with_a_slash_and_must_be_http(fake):
    assert RemoteSession(fake.url + "/", AGENT, timeout=5).principal == "registrar-1"
    for url in ("file:///etc/passwd", "monitor:8080", ""):
        with pytest.raises(InvalidConfiguration):
            RemoteSession(url, AGENT)


# --- execute --------------------------------------------------------------------

def test_execute_returns_the_text_of_a_result_a_block_and_an_error(fake, remote):
    fake.calls["open_bid_denied"] = _failure("PermissionDenied", "role 'reader' does not have the tool")
    assert remote.execute("open_bid", {"ref": "bid-2"}) == "487311902"
    assert fake.seen == [("POST", "/v1/call", {"tool": "open_bid", "arguments": {"ref": "bid-2"}})]
    assert remote.execute("read_messages") == "null"
    assert fake.seen[-1][2] == {"tool": "read_messages", "arguments": {}}
    assert remote.execute("publish", {"awardee": "x", "text": "y"}) == f"BLOCKED by policy P1: {REASON}"
    assert remote.execute("open_bid_denied", {}) == "ERROR: role 'reader' does not have the tool"
    assert remote.execute("does_not_exist", {}) == "ERROR: unknown tool: 'does_not_exist'"


def test_execute_never_raises(fake, dead_url):
    down = RemoteSession(dead_url, AGENT, timeout=5)
    stranger = RemoteSession(fake.url, "not-a-token", timeout=5)
    remote = RemoteSession(fake.url, AGENT, timeout=5)
    assert down.execute("open_bid", {"ref": "bid-2"}).startswith("ERROR: ")
    assert "401" in stranger.execute("open_bid", {"ref": "bid-2"})
    assert remote.execute("open_bid", {"ref": object()}).startswith("ERROR: ")       # not JSON
    assert remote.execute("open_bid", ["bid-2"]).startswith("ERROR: ")               # not a mapping
    assert remote.execute("open_bid", {"ref": float("nan")}).startswith("ERROR: ")
    assert fake.count("/v1/call") == 1                        # only the stranger reached the server
    for raw in (b"<html>not json</html>", b"\xff\xfe", b"[1, 2]", b'{"ok": true, "result": 1}',
                b'{"ok": true, "result": 1, "text": 7}'):
        fake.raw = raw
        assert remote.execute("open_bid", {"ref": "bid-2"}).startswith("ERROR: "), raw


# --- call -----------------------------------------------------------------------

def test_call_returns_the_result_as_the_tool_gave_it(fake, remote):
    fake.calls["score"] = {"ok": True, "result": {"bid-1": [1, 2.5, None]}, "text": "..."}
    assert remote.call("open_bid", ref="bid-2") == 487311902
    assert remote.call("read_messages") is None
    assert remote.call("score") == {"bid-1": [1, 2.5, None]}


def test_call_returns_a_blocked_when_the_gate_stops_it(remote):
    outcome = remote.call("publish", awardee="x", text="y")
    assert outcome == Blocked("publish", "P1", REASON)
    assert str(outcome) == f"BLOCKED by policy P1: {REASON}"


@pytest.mark.parametrize("kind, error", [
    ("PermissionDenied", PermissionDenied), ("QuotaExceeded", QuotaExceeded),
    ("InvalidArguments", InvalidArguments), ("UnknownTool", UnknownTool), ("ToolError", ToolError),
    ("QuorumError", QuorumError), ("SomethingNew", QuorumError), ("RemoteError", QuorumError),
    ("InvalidConfiguration", QuorumError), (None, QuorumError), (["PermissionDenied"], QuorumError)])
def test_call_raises_the_domain_error_the_server_names(fake, remote, kind, error):
    fake.calls["open_bid"] = _failure(kind, "the reason the server gave")
    with pytest.raises(QuorumError) as caught:
        remote.call("open_bid", ref="bid-2")
    assert type(caught.value) is error and str(caught.value) == "the reason the server gave"


def test_positional_arguments_take_the_names_of_the_spec_in_order(fake, remote):
    assert remote.call("write", "registry.notes", "x") == "stored"
    assert remote.call("write", "registry.notes", data="y") == "stored"
    assert remote.call("publish", "acme", text="hello") == Blocked("publish", "P1", REASON)
    assert [body for _, path, body in fake.seen if path == "/v1/call"] == [
        {"tool": "write", "arguments": {"key": "registry.notes", "data": "x"}},
        {"tool": "write", "arguments": {"key": "registry.notes", "data": "y"}},
        {"tool": "publish", "arguments": {"awardee": "acme", "text": "hello"}}]


def test_arguments_that_cannot_be_named_or_sent_fail_without_reaching_the_server(fake, remote):
    with pytest.raises(InvalidArguments, match="too many positional"):
        remote.call("open_bid", "bid-2", "extra")
    with pytest.raises(InvalidArguments, match="too many positional"):
        remote.call("read_messages", 1)
    with pytest.raises(InvalidArguments, match="multiple values for argument 'ref'"):
        remote.call("open_bid", "bid-2", ref="bid-3")
    with pytest.raises(UnknownTool, match="does_not_exist"):
        remote.call("does_not_exist", "x")
    with pytest.raises(InvalidArguments, match="JSON"):
        remote.call("open_bid", ref={1, 2})
    assert fake.count("/v1/call") == 0


def test_a_tool_outside_the_specs_called_by_name_is_left_to_the_monitor(fake, remote):
    # the monitor tells a tool of another role from one that does not exist, and audits the attempt
    fake.calls["score_bids"] = _failure("PermissionDenied", "role 'registrar' does not have the tool 'score_bids'")
    with pytest.raises(PermissionDenied, match="score_bids"):
        remote.call("score_bids", refs=["bid-1"])
    with pytest.raises(UnknownTool):
        remote.call("does_not_exist")
    assert fake.count("/v1/call") == 2


def test_attribute_sugar_calls_the_tool(fake, remote):
    assert remote.open_bid("bid-2") == 487311902
    assert remote.write("registry.notes", data="x") == "stored"
    assert remote.publish(awardee="x", text="y") == Blocked("publish", "P1", REASON)
    assert fake.seen[1] == ("POST", "/v1/call", {"tool": "open_bid", "arguments": {"ref": "bid-2"}})


def test_attribute_sugar_exists_only_for_tools_of_the_specs(fake, remote):
    with pytest.raises(AttributeError):
        _ = remote.score_bids
    assert not hasattr(remote, "tools") and hasattr(remote, "open_bid")
    assert fake.count("/v1/tools") == 1


def test_private_names_never_reach_the_server_nor_recurse(fake, remote):
    with pytest.raises(AttributeError):
        _ = remote._open_bid
    assert not hasattr(remote, "__deepcopy__")
    assert fake.seen == []
    hollow = RemoteSession.__new__(RemoteSession)             # as copy or pickle build it, without __init__
    with pytest.raises(AttributeError):
        _ = hollow.open_bid


# --- transport and protocol failures --------------------------------------------

def test_a_monitor_that_is_down_raises_remote_error(dead_url):
    down = RemoteSession(dead_url, AGENT, timeout=5)
    for attempt in (lambda: down.principal, lambda: down.role, down.tool_specs,
                    lambda: down.call("open_bid", ref="bid-2"), lambda: down.open_bid("bid-2")):
        with pytest.raises(RemoteError, match="cannot reach the monitor"):
            attempt()
    assert issubclass(RemoteError, QuorumError)


def test_a_rejected_token_raises_remote_error(fake):
    stranger = RemoteSession(fake.url, "not-a-token", timeout=5)
    with pytest.raises(RemoteError, match="401 Unauthorized"):
        stranger.call("open_bid", ref="bid-2")
    with pytest.raises(RemoteError, match="401 Unauthorized"):
        stranger.tool_specs()
    with pytest.raises(RemoteError, match="403 Forbidden"):
        RemoteSession(fake.url, ADMIN, timeout=5).call("open_bid", ref="bid-2")


@pytest.mark.parametrize("raw", [
    b"<html>not json</html>", b"", b"\xff\xfe", b"[1, 2]", b"null", b'{"ok": true}', b'{"ok": false, "error": "x"}',
    b'{"ok": false, "result": 1, "text": "1"}', b'{"ok": true, "blocked": {"tool": "publish"}, "text": "x"}',
    b'{"ok": true, "result": 1, "blocked": {"tool": "publish", "policy": 1, "reason": "x"}, "text": "x"}'])
def test_an_answer_that_breaks_the_protocol_raises_remote_error(fake, remote, raw):
    fake.raw = raw
    with pytest.raises(RemoteError):
        remote.call("open_bid", ref="bid-2")


@pytest.mark.parametrize("raw", [
    b"not json", b'{"ok": true}', b'{"ok": true, "principal": "a", "role": "a", "tools": null}',
    b'{"ok": true, "principal": "a", "role": 7, "tools": []}',
    b'{"ok": true, "principal": "a", "role": "a", "tools": [{"name": "x"}]}',
    b'{"ok": true, "principal": "a", "role": "a", "tools": ["x"]}'])
def test_malformed_specs_raise_remote_error(fake, remote, raw):
    fake.raw = raw
    with pytest.raises(RemoteError):
        remote.tool_specs()
    with pytest.raises(RemoteError):
        remote.open_bid("bid-2")


def test_a_redirect_is_not_followed(fake):
    class Redirect(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            self.send_response(307)
            self.send_header("Location", fake.url + self.path)
            self.send_header("Content-Length", "0")
            self.end_headers()

    with ThreadingHTTPServer(("127.0.0.1", 0), Redirect) as door:
        threading.Thread(target=door.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True).start()
        try:
            with pytest.raises(RemoteError, match="307"):
                RemoteSession(f"http://127.0.0.1:{door.server_address[1]}", AGENT, timeout=5).tool_specs()
        finally:
            door.shutdown()
    assert fake.seen == []                                    # the token did not travel to the second host


# --- the token stays secret -----------------------------------------------------

def test_the_token_is_not_in_any_repr_or_error(fake, dead_url):
    secret = "tok-51b0c7e2-secret"
    stranger, down = RemoteSession(fake.url, secret, timeout=5), RemoteSession(dead_url, secret, timeout=5)
    admin = RemoteAdmin(fake.url, secret, timeout=5)
    texts = [repr(stranger), str(stranger), repr(down), repr(admin),
             stranger.execute("open_bid", {"ref": "bid-2"}), down.execute("open_bid", {"ref": "bid-2"})]
    for attempt in (stranger.tool_specs, lambda: stranger.call("open_bid", ref="bid-2"), lambda: stranger.principal,
                    down.tool_specs, lambda: down.call("open_bid", ref="bid-2"), admin.state,
                    RemoteAdmin(dead_url, secret, timeout=5).state):
        with pytest.raises(RemoteError) as caught:
            attempt()
        texts += [str(caught.value), repr(caught.value)]
        assert caught.value.__cause__ is None and caught.value.__suppress_context__
    assert fake.seen and "401" in texts[4]                    # the fake did echo the token back
    assert not any(secret in text for text in texts), texts
    assert repr(stranger) == f"RemoteSession({fake.url!r})" and repr(admin) == f"RemoteAdmin({fake.url!r})"


def test_a_domain_error_does_not_carry_the_token_either(fake, remote):
    fake.calls["open_bid"] = _failure("ToolError", f"could not process {AGENT}")
    with pytest.raises(ToolError) as caught:
        remote.call("open_bid", ref="bid-2")
    assert AGENT not in str(caught.value)


@pytest.mark.parametrize("token", ["s3cr3t\nX-Injected: 1", "s3cr3t\r\n", "s3cr3t-" + chr(0xE1) + chr(0x4E2D)])
def test_a_token_that_cannot_go_in_a_header_fails_without_being_quoted(fake, token):
    session = RemoteSession(fake.url, token, timeout=5)
    with pytest.raises(RemoteError) as caught:
        session.tool_specs()
    assert "s3cr3t" not in str(caught.value) and caught.value.__cause__ is None
    assert "s3cr3t" not in session.execute("open_bid", {"ref": "bid-2"})


# --- administration -------------------------------------------------------------

def test_remote_admin_reads_the_state(fake):
    assert RemoteAdmin(fake.url, ADMIN, timeout=5).state() == STATE
    assert fake.seen == [("GET", "/v1/admin/state", None)]


def test_remote_admin_fails_with_remote_error(fake, dead_url):
    with pytest.raises(RemoteError, match="403 Forbidden"):
        RemoteAdmin(fake.url, AGENT, timeout=5).state()
    with pytest.raises(RemoteError, match="401 Unauthorized"):
        RemoteAdmin(fake.url, "not-a-token", timeout=5).state()
    with pytest.raises(RemoteError, match="cannot reach the monitor"):
        RemoteAdmin(dead_url, ADMIN, timeout=5).state()
    for raw in (b"not json", b'{"ok": false}', b"[]"):
        fake.raw = raw
        with pytest.raises(RemoteError):
            RemoteAdmin(fake.url, ADMIN, timeout=5).state()


# --- the adapters take a local or a remote session ------------------------------

def test_the_generic_adapter_delegates_to_a_remote_session(fake, remote, dead_url):
    assert functions.tool_specs(remote) == SPECS
    assert functions.execute(remote, "open_bid", {"ref": "bid-2"}) == "487311902"
    assert functions.execute(remote, "read_messages") == "null"
    assert functions.execute(remote, "publish", {"awardee": "x", "text": "y"}).startswith("BLOCKED by policy P1")
    assert functions.execute(remote, "does_not_exist", {}).startswith("ERROR: ")
    assert functions.execute(RemoteSession(dead_url, AGENT, timeout=5), "open_bid", {}).startswith("ERROR: ")
    assert fake.count("/v1/call") == 4


def test_the_generic_adapter_keeps_working_with_a_local_session():
    session = mini.new().session("agent")
    assert [s["name"] for s in functions.tool_specs(session)] == list(mini.POLICY.roles["agent"].tools)
    assert functions.execute(session, "reveal", {"i": 0}) == mini.SECRETS[0]
    assert functions.execute(session, "emit", {"text": "x"}).startswith("BLOCKED by policy P1")
    assert functions.execute(session, "does_not_exist", {}).startswith("ERROR: ")


def test_a_local_tool_named_like_an_adapter_function_is_not_mistaken_for_one():
    @tool(description="Runs a job.", params={"job": "Job name."})
    def execute(call, job: str) -> str:
        return f"ran {job}"

    @tool(description="Lists the specs.")
    def tool_specs(call) -> list[str]:
        return ["a spec"]

    policy = Policy.from_dict({"roles": {"agent": {"tools": ["execute", "tool_specs"]}}})
    session = new_monitor(policy, [execute, tool_specs]).session("agent")
    assert [s["name"] for s in functions.tool_specs(session)] == ["execute", "tool_specs"]
    assert functions.execute(session, "execute", {"job": "x"}) == "ran x"
    assert functions.execute(session, "tool_specs") == '["a spec"]'


def test_inspect_tools_with_a_remote_session(fake, remote):
    pytest.importorskip("inspect_ai")
    from inspect_ai.tool import ToolDef

    from quorum.adapters.inspect_ai import inspect_tools

    definitions = [ToolDef(t) for t in inspect_tools(remote)]
    assert [d.name for d in definitions] == [spec["name"] for spec in SPECS]
    by_name = {d.name: d for d in definitions}
    open_bid = by_name["open_bid"]
    assert open_bid.description == "Tool open_bid." and open_bid.parameters.required == ["ref"]
    assert open_bid.parameters.properties["ref"].type == "string"
    assert by_name["read_messages"].parameters.required == []
    assert asyncio.run(open_bid.tool(ref="bid-2")) == "487311902"
    assert fake.seen[-1] == ("POST", "/v1/call", {"tool": "open_bid", "arguments": {"ref": "bid-2"}})
    assert asyncio.run(by_name["publish"].tool(awardee="x", text="y")).startswith("BLOCKED by policy P1")
    fake.calls.pop("open_bid")
    assert asyncio.run(open_bid.tool(ref="bid-2")).startswith("ERROR: ")


# --- against the real server ----------------------------------------------------

def test_two_agents_and_the_operator_through_the_real_server():
    http_server = pytest.importorskip("quorum.adapters.http_server")
    # the reader of mini only reads; here it also gets the sink, so the gate has something to stop
    roles = {**mini.POLICY.roles, "reader": Role("reader", ("read", "emit"), reads=("board.",))}
    quorum = mini.new(policy=mini.POLICY.evolve(roles=roles))
    tokens = {AGENT: "agent", READER: "reader"}
    with http_server.MonitorServer(quorum, tokens, admin_token=ADMIN) as server:
        agent = RemoteSession(server.url, AGENT, timeout=5)
        reader = RemoteSession(server.url, READER, timeout=5)
        assert (agent.principal, agent.role) == ("agent", "agent")
        assert (reader.principal, reader.role) == ("reader", "reader")
        assert [s["name"] for s in reader.tool_specs()] == ["read", "emit"]
        assert agent.tool_specs() == functions.tool_specs(quorum.sessions["agent"])

        assert agent.reveal(0) == mini.SECRETS[0]                         # positional, named by the spec
        agent.write("board.x", "a note written after reading the secret")
        assert reader.read("board.x") == "a note written after reading the secret"
        outcome = reader.emit("hello")
        assert isinstance(outcome, Blocked) and (outcome.tool, outcome.policy) == ("emit", "P1")
        assert "secret.0" in outcome.reason
        assert functions.execute(reader, "emit", {"text": "hello"}) == str(outcome)
        with pytest.raises(PermissionDenied):
            reader.call("reveal", i=0)                                    # a tool of the other role
        with pytest.raises(InvalidArguments):
            agent.call("reveal", i="zero")
        assert reader.execute("reveal", {"i": 0}).startswith("ERROR: ")
        with pytest.raises(RemoteError):
            RemoteSession(server.url, "not-a-token", timeout=5).tool_specs()
        with pytest.raises(RemoteError):
            RemoteAdmin(server.url, AGENT, timeout=5).state()

        state = RemoteAdmin(server.url, ADMIN, timeout=5).state()
        assert [step["tool"] for step in state["trajectories"]["agent"]][:2] == ["reveal", "write"]
        assert [step["tool"] for step in state["trajectories"]["reader"]][:2] == ["read", "emit"]
        assert state["emissions"] == [] and len(state["blocks"]) == 2 and state["audit_log_valid"] is True
    assert quorum.emitted() == []
