"""The monitor served over HTTP: the contract of docs/protocolo.md, as seen from the wire."""
import datetime
import http.client
import json
import socket
import threading
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import replace

import mini
import pytest

from quorum import InvalidConfiguration, QuorumError, new_monitor, tool
from quorum.adapters import http_server
from quorum.adapters.functions import execute, tool_specs
from quorum.adapters.http_server import MAX_BODY, MonitorServer

# three more principals with the tools of 'agent', so that taint has somewhere to travel
POLICY = mini.POLICY.evolve(roles={
    **mini.POLICY.roles,
    **{name: replace(mini.POLICY.roles["agent"], name=name) for name in ("analyst", "publisher", "bystander")}})
TOKENS = {principal: f"token-of-{principal}-0123456789abcdef" for principal in POLICY.roles}
ADMIN = "token-of-the-operator-0123456789"
SECRETS = (*TOKENS.values(), ADMIN)
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))     # straight to the server, never a proxy


def serve(quorum, **options):
    return MonitorServer(quorum, {token: principal for principal, token in TOKENS.items()}, **options)


@pytest.fixture
def quorum():
    return mini.new(policy=POLICY)


@pytest.fixture
def server(quorum):
    with serve(quorum, admin_token=ADMIN, extra_state=lambda: {"leak": False}) as server:
        yield server


def request(server, method, path, token=None, body=None, *, raw=None, headers=None):
    """One round trip: (status, JSON body). Every answer, of any status, must be JSON in UTF-8."""
    data = raw if raw is not None else None if body is None else json.dumps(body).encode()
    headers = {**({"Authorization": f"Bearer {token}"} if token else {}), **(headers or {})}
    try:
        response = OPENER.open(urllib.request.Request(server.url + path, data, headers, method=method), timeout=10)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        assert response.headers["Content-Type"] == "application/json; charset=utf-8"
        return response.status, json.loads(response.read())


def call(server, principal, name, **arguments):
    status, answer = request(server, "POST", "/v1/call", TOKENS[principal], {"tool": name, "arguments": arguments})
    assert status == 200
    return answer


def state(server):
    status, answer = request(server, "GET", "/v1/admin/state", ADMIN)
    assert status == 200 and answer["ok"] is True
    return answer


def connection(server):
    address = urllib.parse.urlsplit(server.url)
    return http.client.HTTPConnection(address.hostname, address.port, timeout=10)


def failure(kind):
    """Matches the body of a protocol error of that type."""
    class Match:
        def __eq__(self, body):
            return (set(body) == {"ok", "error"} and body["ok"] is False and set(body["error"]) == {"type", "message"}
                    and body["error"]["type"] == kind and isinstance(body["error"]["message"], str))
    return Match()


# --- routes ---------------------------------------------------------------------

def test_health_needs_no_token(server, quorum):
    assert request(server, "GET", "/health") == (200, {"ok": True})
    assert request(server, "GET", "/health", "not-a-token-at-all") == (200, {"ok": True})
    assert quorum.sessions == {}                             # nothing is opened for a stranger


def test_tools_lists_only_the_tools_of_the_role_behind_the_token(server, quorum):
    status, answer = request(server, "GET", "/v1/tools", TOKENS["reader"])
    assert status == 200 and set(answer) == {"ok", "principal", "role", "tools"} and answer["ok"] is True
    assert (answer["principal"], answer["role"]) == ("reader", "reader")
    assert [spec["name"] for spec in answer["tools"]] == ["read"]
    assert answer["tools"] == tool_specs(quorum.sessions["reader"])
    status, answer = request(server, "GET", "/v1/tools", TOKENS["agent"])
    assert (answer["principal"], answer["role"]) == ("agent", "agent")
    assert [spec["name"] for spec in answer["tools"]] == list(POLICY.roles["agent"].tools)
    assert all(set(spec) == {"name", "description", "parameters"} for spec in answer["tools"])


def test_a_session_opens_on_first_use_and_an_open_one_is_reused():
    quorum = mini.new(policy=POLICY)
    local = quorum.session("reader")                         # opened in process, before the server exists
    helper = quorum.session("helper", "agent")               # a principal whose role has another name
    with serve(quorum) as server, MonitorServer(quorum, {"token-of-helper-0123456789": "helper"}) as second:
        assert set(quorum.sessions) == {"reader", "helper"}
        assert call(server, "reader", "read", key="board.x") == {"ok": True, "result": None, "text": "null"}
        assert quorum.sessions["reader"] is local and len(local.trajectory) == 1
        assert call(server, "analyst", "read_messages")["result"] == []
        assert set(quorum.sessions) == {"reader", "helper", "analyst"}
        status, answer = request(second, "GET", "/v1/tools", "token-of-helper-0123456789")
        assert (status, answer["principal"], answer["role"]) == (200, "helper", "agent")
        assert quorum.sessions["helper"] is helper


# --- the three shapes of a call -------------------------------------------------

def test_a_call_that_runs_returns_the_result_and_its_text(server):
    assert call(server, "agent", "length", i=0) == {"ok": True, "result": 9, "text": "9"}
    assert call(server, "agent", "reveal", i=0) == {"ok": True, "result": "ALFA-7731", "text": "ALFA-7731"}
    note = {"year": 2026, "open": True, "parts": ["a", None]}
    assert call(server, "agent", "write", key="board.note", data=note)["result"] == "Saved."
    assert call(server, "agent", "read", key="board.note") == {
        "ok": True, "result": note, "text": json.dumps(note, ensure_ascii=False)}


def test_arguments_are_optional(server):
    for body in ({"tool": "read_messages"}, {"tool": "read_messages", "arguments": {}},
                 {"tool": "read_messages", "arguments": None}):
        assert request(server, "POST", "/v1/call", TOKENS["agent"], body) == (
            200, {"ok": True, "result": [], "text": "[]"})


def test_text_travels_as_utf8(server):
    call(server, "agent", "write", key="board.note", data="licitación ñ 日本")
    body = json.dumps({"tool": "read", "arguments": {"key": "board.note"}}).encode()
    headers = {"Authorization": f"Bearer {TOKENS['agent']}"}
    with OPENER.open(urllib.request.Request(server.url + "/v1/call", body, headers), timeout=10) as response:
        raw = response.read()
    assert "licitación ñ 日本".encode() in raw and json.loads(raw)["result"] == "licitación ñ 日本"


def test_a_call_the_gate_stops_returns_the_blocked_shape(server, quorum):
    call(server, "agent", "reveal", i=0)
    answer = call(server, "agent", "emit", text="hello")
    assert set(answer) == {"ok", "blocked", "text"} and answer["ok"] is True
    assert answer["blocked"] == {"tool": "emit", "policy": "P1",
                                 "reason": "restricted sources not authorized for this destination: secret.0"}
    assert answer["text"] == f"BLOCKED by policy P1: {answer['blocked']['reason']}"
    assert quorum.emitted() == []


@pytest.mark.parametrize("principal, name, arguments, kind", [
    ("reader", "emit", {"text": "x"}, "PermissionDenied"),          # a tool of another role
    ("agent", "read", {"key": "secret.0"}, "PermissionDenied"),     # a key its role cannot read
    ("agent", "reveal", {}, "InvalidArguments"),
    ("agent", "reveal", {"i": "zero"}, "InvalidArguments"),
    ("agent", "reveal", {"i": 0, "more": 1}, "InvalidArguments"),
    ("agent", "does_not_exist", {}, "UnknownTool"),
    ("agent", "", {}, "UnknownTool"),
    ("agent", "fail", {"i": 0}, "ToolError"),
])
def test_a_call_that_is_not_valid_returns_the_error_of_the_domain(server, principal, name, arguments, kind):
    with pytest.raises(QuorumError) as local:                # what the same call raises in process
        mini.new(policy=POLICY).session(principal).call(name, **arguments)
    assert type(local.value).__name__ == kind
    assert call(server, principal, name, **arguments) == {
        "ok": False, "error": {"type": kind, "message": str(local.value)}, "text": f"ERROR: {local.value}"}


def test_a_spent_quota_is_reported_with_its_own_type():
    with serve(mini.new(policy=POLICY.evolve(quotas={"length": 1}))) as server:
        assert call(server, "agent", "length", i=0)["result"] == 9
        answer = call(server, "agent", "length", i=0)
    assert answer["ok"] is False and answer["error"]["type"] == "QuotaExceeded"
    assert answer["text"] == f"ERROR: {answer['error']['message']}" and "quota of 1" in answer["text"]


@tool(description="Fails in a way nobody planned.")
def crash(call) -> str:
    raise ZeroDivisionError("division by zero")


@tool(description="Returns something JSON cannot carry.")
def odd(call) -> dict:
    return {("a", "b"): 1}


@tool(description="Returns things JSON carries only as text.")
def stamp(call) -> dict:
    return {"when": datetime.date(2026, 1, 2), "tags": {"x"}, "half": "\ud83d"}


def test_an_unexpected_failure_is_an_error_shape_and_the_server_goes_on():
    role = replace(POLICY.roles["agent"], tools=(*POLICY.roles["agent"].tools, "crash", "odd", "stamp"))
    quorum = new_monitor(POLICY.evolve(roles={**POLICY.roles, "agent": role}), (*mini.TOOLS, crash, odd, stamp))
    with serve(quorum, admin_token=ADMIN) as server:
        assert call(server, "agent", "crash") == {
            "ok": False, "error": {"type": "QuorumError", "message": "division by zero"},
            "text": "ERROR: division by zero"}
        answer = call(server, "agent", "odd")
        assert answer["ok"] is False and answer["error"]["type"] == "QuorumError"
        assert answer["text"] == f"ERROR: {answer['error']['message']}"
        answer = call(server, "agent", "stamp")
        assert answer["result"] == {"when": "2026-01-02", "tags": "{'x'}", "half": "\ud83d"}
        assert json.loads(answer["text"]) == answer["result"]
        assert request(server, "GET", "/health") == (200, {"ok": True})
        steps = state(server)["trajectories"]["agent"]      # an odd result does not cost the operator the state
        assert [step["tool"] for step in steps] == ["crash", "odd", "stamp"]
        assert steps[1]["result"] == {"('a', 'b')": 1} and steps[2]["result"] == answer["result"]


def test_the_text_is_exactly_what_execute_returns_in_process(server):
    twin = mini.new(policy=POLICY)
    sessions = {principal: twin.session(principal) for principal in ("agent", "reader")}
    script = [
        ("reader", "emit", {"text": "x"}), ("reader", "read", {"key": "board.nothing"}),
        ("agent", "does_not_exist", {}), ("agent", "reveal", {}), ("agent", "reveal", {"i": "zero"}),
        ("agent", "read", {"key": "secret.0"}), ("agent", "emit", {"text": "clean"}),
        ("agent", "write", {"key": "board.note", "data": {"año": 2026, "ok": True}}),
        ("agent", "read", {"key": "board.note"}), ("agent", "send_message", {"recipient": "reader", "text": "hola"}),
        ("agent", "read_messages", {}), ("agent", "length", {"i": 0}), ("agent", "fail", {"i": 1}),
        ("agent", "emit", {"text": "tainted by the failed call"}), ("agent", "reveal", {"i": 0}),
    ]
    texts = [call(server, principal, name, **arguments)["text"] for principal, name, arguments in script]
    assert texts == [execute(sessions[principal], name, arguments) for principal, name, arguments in script]
    assert texts[6] == "emitted" and texts[-2].startswith("BLOCKED by policy P1")


# --- provenance and identity across the network ---------------------------------

def test_taint_crosses_between_principals_over_http(server, quorum):
    secret = call(server, "analyst", "reveal", i=0)["result"]
    assert call(server, "analyst", "write", key="board.summary", data="a paraphrase, not the secret")["ok"]
    assert call(server, "publisher", "read", key="board.summary")["result"] == "a paraphrase, not the secret"
    answer = call(server, "publisher", "emit", text="nothing that looks secret")
    assert answer["blocked"]["policy"] == "P1" and "secret.0" in answer["blocked"]["reason"]
    assert call(server, "bystander", "emit", text="hello") == {"ok": True, "result": "emitted", "text": "emitted"}
    assert [(e.principal, dict(e.arguments)) for e in quorum.emitted()] == [("bystander", {"text": "hello"})]
    assert secret == mini.SECRETS[0] and quorum.sessions["publisher"].context.secrets == {"secret.0"}
    assert quorum.sessions["bystander"].context.secrets == frozenset()


def test_a_token_always_resolves_to_its_own_principal(server, quorum):
    claims = {"principal": "agent", "role": "agent", "token": TOKENS["agent"], "authorization": TOKENS["agent"]}
    headers = {"X-Principal": "agent", "X-Role": "agent", "Cookie": f"token={TOKENS['agent']}"}
    status, answer = request(server, "POST", "/v1/call?principal=agent&role=agent", TOKENS["reader"],
                             {"tool": "emit", "arguments": {"text": "x"}, **claims}, headers=headers)
    assert status == 200 and answer["error"] == {
        "type": "PermissionDenied", "message": "role 'reader' does not have the tool 'emit'"}
    status, answer = request(server, "GET", "/v1/tools?principal=agent", TOKENS["reader"], headers=headers)
    assert (answer["principal"], answer["role"]) == ("reader", "reader")
    assert [spec["name"] for spec in answer["tools"]] == ["read"]
    assert set(quorum.sessions) == {"reader"} and quorum.emitted() == []
    assert quorum.audit_log[-1]["principal"] == "reader" and quorum.audit_log[-1]["executed"] is False
    assert TOKENS["agent"] not in json.dumps(state(server))  # the claims were ignored, not recorded


def test_every_token_is_compared_on_every_request(server, monkeypatch):
    compared = []
    real = http_server.hmac.compare_digest
    monkeypatch.setattr(http_server.hmac, "compare_digest", lambda a, b: compared.append(real(a, b)) or compared[-1])
    for token, expected in ((TOKENS["agent"], 200), (TOKENS["bystander"], 200), ("x" * 40, 401), (ADMIN, 403)):
        compared.clear()
        assert request(server, "GET", "/v1/tools", token)[0] == expected
        assert len(compared) == len(TOKENS) + 1 and sum(compared) == (expected != 401)


# --- protocol errors ------------------------------------------------------------

@pytest.mark.parametrize("method, path", [("GET", "/v1/tools"), ("POST", "/v1/call"), ("GET", "/v1/admin/state")])
@pytest.mark.parametrize("authorization", [
    None, "", "Bearer", "Bearer ", "Bearer " + "x" * 40, TOKENS["agent"], "Basic " + TOKENS["agent"],
    "Basic " + ADMIN, "Bearer " + TOKENS["agent"][:-1], "Bearer " + TOKENS["agent"] + "f",
    "Bearer " + TOKENS["agent"].upper(), f"Bearer {TOKENS['agent']} {ADMIN}"])
def test_a_missing_or_unknown_token_is_unauthorized(server, quorum, method, path, authorization):
    events = len(quorum.audit_log)
    body = {"tool": "emit", "arguments": {"text": "x"}} if method == "POST" else None
    headers = {} if authorization is None else {"Authorization": authorization}
    status, answer = request(server, method, path, body=body, headers=headers)
    assert status == 401 and answer == failure("Unauthorized")
    assert all(secret not in json.dumps(answer) for secret in SECRETS)
    assert quorum.sessions == {} and len(quorum.audit_log) == events and quorum.emitted() == []


def test_the_scheme_of_the_authorization_header_is_case_insensitive(server):
    status, answer = request(server, "GET", "/v1/tools", headers={"Authorization": f"bearer {TOKENS['reader']}"})
    assert (status, answer["principal"]) == (200, "reader")


def test_agent_and_administration_tokens_do_not_open_each_other_s_routes(server, quorum):
    assert request(server, "GET", "/v1/admin/state", TOKENS["agent"]) == (403, failure("Forbidden"))
    assert request(server, "GET", "/v1/tools", ADMIN) == (403, failure("Forbidden"))
    body = {"tool": "emit", "arguments": {"text": "x"}}
    assert request(server, "POST", "/v1/call", ADMIN, body) == (403, failure("Forbidden"))
    assert quorum.sessions == {} and quorum.emitted() == []


def test_without_an_administration_token_nobody_reads_the_state(quorum):
    with serve(quorum) as server:
        assert request(server, "GET", "/v1/admin/state", TOKENS["agent"]) == (403, failure("Forbidden"))
        assert request(server, "GET", "/v1/admin/state", ADMIN) == (401, failure("Unauthorized"))
        assert request(server, "GET", "/v1/admin/state") == (401, failure("Unauthorized"))


@pytest.mark.parametrize("path", ["/", "/v1", "/v1/", "/v1/tools/", "/v1/call/emit", "/v1/admin", "/health/x",
                                  "/V1/TOOLS", "/v2/tools", "/v1/admin/audit"])
def test_an_unknown_route_is_not_found(server, path):
    for method, token in (("GET", None), ("GET", TOKENS["agent"]), ("POST", ADMIN)):
        body = {} if method == "POST" else None
        assert request(server, method, path, token, body) == (404, failure("NotFound"))


@pytest.mark.parametrize("method, path, allowed", [
    ("POST", "/health", "GET"), ("POST", "/v1/tools", "GET"), ("GET", "/v1/call", "POST"),
    ("PUT", "/v1/call", "POST"), ("DELETE", "/v1/call", "POST"), ("PATCH", "/v1/tools", "GET"),
    ("POST", "/v1/admin/state", "GET"), ("BREW", "/health", "GET")])
def test_a_method_the_route_does_not_take_is_not_allowed(server, quorum, method, path, allowed):
    body = {"tool": "emit", "arguments": {"text": "x"}} if method in ("POST", "PUT", "PATCH") else None
    for token in (None, TOKENS["agent"], ADMIN):
        assert request(server, method, path, token, body) == (405, failure("MethodNotAllowed"))
    client = connection(server)
    client.request(method, path)
    with client.getresponse() as response:
        assert (response.status, response.headers["Allow"]) == (405, allowed)
    client.close()
    assert quorum.sessions == {}


def test_head_is_not_allowed_and_gets_no_body(server):
    client = connection(server)
    client.request("HEAD", "/health")
    with client.getresponse() as response:
        assert (response.status, response.read()) == (405, b"")
    client.close()


@pytest.mark.parametrize("raw", [
    b"", b"{", b"not json", b"\xff\xfe{}", b'{"tool": "read_messages"} trailing',
    b"[]", b'["read_messages"]', b'"read_messages"', b"7", b"null",
    b"{}", b'{"arguments": {}}', b'{"tool": null}', b'{"tool": 7}', b'{"tool": ["read_messages"]}',
    b'{"tool": "read_messages", "arguments": []}', b'{"tool": "read_messages", "arguments": "x"}',
    b'{"tool": "read_messages", "arguments": 0}',
    b'{"tool": "write", "arguments": {"key": "board.x", "data": "\\ud800"}}',
    b"[" * 100_000 + b"]" * 100_000,
], ids=lambda raw: raw[:40].decode("latin-1"))
def test_a_malformed_body_is_a_bad_request(server, quorum, raw):
    call(server, "agent", "read_messages")                   # the session is open: only the body is at stake
    events = len(quorum.audit_log)
    assert request(server, "POST", "/v1/call", TOKENS["agent"], raw=raw) == (400, failure("BadRequest"))
    assert len(quorum.audit_log) == events and quorum.store.get("board.x") is None
    assert call(server, "agent", "read_messages")["ok"] is True


@pytest.mark.parametrize("length", [None, "many", "-1", "1.5", "0x10", ""])
def test_a_post_without_a_usable_content_length_is_a_bad_request(server, length):
    client = connection(server)
    client.putrequest("POST", "/v1/call")
    client.putheader("Authorization", f"Bearer {TOKENS['agent']}")
    if length is not None:
        client.putheader("Content-Length", length)
    client.endheaders()
    with client.getresponse() as response:
        assert (response.status, json.loads(response.read())) == (400, failure("BadRequest"))
    client.close()


def test_a_body_cut_short_is_a_bad_request(server, quorum):
    with socket.create_connection(urllib.parse.urlsplit(server.url).netloc.split(":"), timeout=10) as client:
        client.sendall(f"POST /v1/call HTTP/1.1\r\nAuthorization: Bearer {TOKENS['agent']}\r\n"
                       "Content-Length: 500\r\n\r\n".encode() + b'{"tool": "emit", "arguments": {"text": "x"}}')
        client.shutdown(socket.SHUT_WR)
        answer = b"".join(iter(lambda: client.recv(65536), b""))
    assert answer.startswith(b"HTTP/1.0 400 ") and json.loads(answer.split(b"\r\n\r\n")[1]) == failure("BadRequest")
    assert quorum.emitted() == []


def test_a_body_over_the_limit_is_too_large(server, quorum):
    padding = MAX_BODY - len(b'{"tool": "read_messages"}')
    assert request(server, "POST", "/v1/call", TOKENS["agent"], raw=b'{"tool": "read_messages"}' + b" " * padding) == (
        200, {"ok": True, "result": [], "text": "[]"})          # exactly at the limit
    events = len(quorum.audit_log)
    raw = b'{"tool": "emit", "arguments": {"text": "' + b"x" * MAX_BODY + b'"}}'
    assert request(server, "POST", "/v1/call", TOKENS["agent"], raw=raw) == (413, failure("PayloadTooLarge"))
    assert len(quorum.audit_log) == events and quorum.emitted() == []


@pytest.mark.parametrize("length", [str(MAX_BODY + 1), str(10 ** 12), "9" * 5000])
def test_the_size_is_checked_on_the_header_before_reading_the_body(server, length):
    client = connection(server)
    client.putrequest("POST", "/v1/call")
    client.putheader("Authorization", f"Bearer {TOKENS['agent']}")
    client.putheader("Content-Length", length)
    client.endheaders()                                      # not one byte of body is sent
    with client.getresponse() as response:
        assert (response.status, json.loads(response.read())) == (413, failure("PayloadTooLarge"))
    client.close()


def test_a_request_that_is_not_http_gets_a_json_answer(server):
    for line in (b"GET /health HTTP/9.9\r\n\r\n", b"nonsense\r\n\r\n", b"GET /health HTTP/1.1 extra\r\n\r\n"):
        with socket.create_connection(urllib.parse.urlsplit(server.url).netloc.split(":"), timeout=10) as client:
            client.sendall(line)
            answer = b"".join(iter(lambda: client.recv(65536), b""))
        head, _, body = answer.partition(b"\r\n\r\n")
        assert head.startswith(b"HTTP/1.0 400 ") and b"application/json; charset=utf-8" in head
        assert json.loads(body) == failure("BadRequest")
    assert request(server, "GET", "/health") == (200, {"ok": True})


def test_a_failure_inside_the_server_is_a_json_500_without_a_traceback(server, quorum, monkeypatch, capfd):
    monkeypatch.setattr(quorum, "blocks", lambda: 1 / 0)
    status, answer = request(server, "GET", "/v1/admin/state", ADMIN)
    assert status == 500 and answer == {"ok": False, "error": {"type": "InternalError", "message": "ZeroDivisionError"}}
    assert request(server, "GET", "/health") == (200, {"ok": True})
    assert capfd.readouterr() == ("", "")


# --- the administration state -----------------------------------------------------

def test_the_administration_state_shows_what_the_monitor_saw(server, quorum):
    call(server, "analyst", "reveal", i=0)
    call(server, "analyst", "write", key="board.summary", data="summary")
    call(server, "publisher", "read", key="board.summary")
    blocked = call(server, "publisher", "emit", text="leak")
    call(server, "bystander", "emit", text="fine")
    call(server, "reader", "emit", text="denied by role, which is not a block of the gate")
    answer = state(server)
    assert set(answer) == {"ok", "trajectories", "emissions", "blocks", "audit_log", "audit_log_valid", "extra"}
    assert set(answer["trajectories"]) == {"analyst", "publisher", "bystander", "reader"}
    assert answer["trajectories"] == {p: s.trajectory for p, s in quorum.sessions.items()}
    assert answer["trajectories"]["publisher"] == [
        {"tool": "read", "args": {"key": "board.summary"}, "result": "summary"},
        {"tool": "emit", "args": {"text": "leak"}, "result": blocked["text"]}]
    assert answer["emissions"] == [{"sink": "emit", "principal": "bystander", "arguments": {"text": "fine"}}]
    assert [(b["principal"], b["tool"], b["decision"]["policy"]) for b in answer["blocks"]] == [
        ("publisher", "emit", "P1")]
    assert answer["blocks"] == quorum.blocks() and answer["audit_log"] == list(quorum.audit_log)
    assert answer["audit_log_valid"] is True and answer["extra"] == {"leak": False}
    quorum.audit_log[0]["key"] = "tampered"
    assert state(server)["audit_log_valid"] is False


def test_extra_is_empty_by_default_and_a_failing_extra_does_not_hide_the_rest(quorum):
    def broken():
        raise RuntimeError("the grader is down")
    for extra_state, expected in ((None, {}), (broken, {"error": "RuntimeError: the grader is down"}),
                                  (lambda: {("leak", 1): True}, {"('leak', 1)": True}),
                                  (lambda: ["not", "a", "mapping"], None),
                                  (lambda: {"at": datetime.date(2026, 1, 2)}, {"at": "2026-01-02"})):
        with serve(quorum, admin_token=ADMIN, extra_state=extra_state) as server:
            call(server, "bystander", "emit", text="fine")
            answer = state(server)
        assert answer["extra"] == expected or (expected is None and set(answer["extra"]) == {"error"})
        assert answer["audit_log_valid"] is True and answer["emissions"] and answer["trajectories"]["bystander"]


def test_no_token_appears_in_the_state_the_audit_log_or_the_output(server, quorum, capfd):
    call(server, "analyst", "reveal", i=0)
    call(server, "analyst", "emit", text="x")
    call(server, "reader", "emit", text="x")
    request(server, "POST", "/v1/call", TOKENS["agent"], raw=b"{")
    request(server, "GET", f"/nowhere?token={ADMIN}", TOKENS["agent"])
    request(server, "DELETE", "/v1/tools", TOKENS["agent"])
    request(server, "GET", "/v1/admin/state", TOKENS["agent"])
    request(server, "GET", "/v1/tools", ADMIN)
    answers = [request(server, "GET", "/v1/tools", TOKENS["agent"][:-1] + "0"), request(server, "GET", "/v1/tools")]
    seen = json.dumps([answers, state(server)]) + quorum.audit_log.to_jsonl() + repr(server) + repr(vars(server))
    assert all(secret not in seen for secret in SECRETS)
    assert capfd.readouterr() == ("", "")                    # and nothing was logged at all


def test_concurrent_calls_do_not_break_the_audit_log(server, quorum):
    principals, workers, rounds = ("agent", "analyst", "publisher", "bystander"), 12, 8
    events, start, failures = len(quorum.audit_log), threading.Barrier(workers), []

    def work(n):
        principal = principals[n % len(principals)]
        try:
            start.wait(timeout=10)
            for i in range(rounds):
                assert call(server, principal, "write", key=f"board.{n}", data=i)["result"] == "Saved."
                assert call(server, principal, "read", key=f"board.{n}")["result"] == i
        except Exception as error:
            failures.append(error)

    threads = [threading.Thread(target=work, args=(n,)) for n in range(workers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    assert not failures and not any(thread.is_alive() for thread in threads)
    answer = state(server)
    assert answer["audit_log_valid"] is True and quorum.audit_log.verify()
    assert [event["n"] for event in answer["audit_log"]] == list(range(len(answer["audit_log"])))
    # every principal was opened once, although its first requests raced, and every call left one event
    assert [e["principal"] for e in answer["audit_log"] if e["kind"] == "session"].count("agent") == 1
    assert len(answer["audit_log"]) == events + len(principals) + workers * rounds * 2
    assert sum(len(steps) for steps in answer["trajectories"].values()) == workers * rounds * 2


# --- construction and life cycle --------------------------------------------------

GOOD = "0123456789abcdef"                                    # sixteen characters: the shortest token


@pytest.mark.parametrize("tokens, admin_token", [
    ({}, None), (None, None), ([(GOOD, "agent")], None),
    ({"": "agent"}, None), ({GOOD[:-1]: "agent"}, None), ({GOOD.encode(): "agent"}, None),
    ({GOOD + " with a space": "agent"}, None), ({GOOD + "ñ": "agent"}, None), ({GOOD + "\n": "agent"}, None),
    ({GOOD + "1": "agent", GOOD + "2": "agent"}, None),
    ({GOOD: "nobody"}, None), ({GOOD: ""}, None), ({GOOD: None}, None), ({GOOD: "agent", GOOD + "2": "Agent"}, None),
    ({GOOD: "agent"}, GOOD), ({GOOD: "agent"}, ""), ({GOOD: "agent"}, "too-short"), ({GOOD: "agent"}, 16),
], ids=repr)
def test_the_constructor_rejects_a_bad_configuration(tokens, admin_token):
    with pytest.raises(InvalidConfiguration) as caught:
        MonitorServer(mini.new(), tokens, admin_token=admin_token)
    for secret in (*(tokens if isinstance(tokens, dict) else ()), admin_token):
        assert not secret or not isinstance(secret, str) or secret not in str(caught.value)


def test_the_shortest_valid_configuration_is_accepted():
    quorum = mini.new()
    with MonitorServer(quorum, {GOOD: "agent"}, admin_token=GOOD[::-1]) as server:
        assert server.url.startswith("http://127.0.0.1:") and int(server.url.rsplit(":", 1)[1]) > 0
        assert request(server, "GET", "/v1/tools", GOOD)[1]["principal"] == "agent"
        assert request(server, "GET", "/v1/admin/state", GOOD[::-1])[0] == 200


def test_stop_releases_the_port_and_leaves_no_thread_behind(quorum):
    server = serve(quorum)
    server.stop()                                            # never started: nothing to wait for
    server = serve(quorum)
    server.start()
    server.start()                                           # already serving
    assert request(server, "GET", "/health") == (200, {"ok": True})
    server.stop()
    server.stop()
    assert not [thread for thread in threading.enumerate() if thread.name == "quorum-monitor-server"]
    with pytest.raises(urllib.error.URLError):
        request(server, "GET", "/health")
    for restart in (server.start, server.serve_forever):
        with pytest.raises(InvalidConfiguration):
            restart()


def test_serve_forever_runs_in_the_calling_thread_until_stop(quorum):
    server = serve(quorum)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    assert call(server, "bystander", "emit", text="hello")["result"] == "emitted"
    server.stop()
    thread.join(timeout=10)
    assert not thread.is_alive()
