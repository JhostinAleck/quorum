"""The web interface: documents, the episode behind the page, its server and the agent services.

No model and no network beyond 127.0.0.1: the model is the fake one of test_agent_loop.
"""
import base64
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest
from test_agent_loop import HONEST, model

from quorum.scenarios.tender import ROLES, SYSTEM
from quorum.ui import agents, documents, server, workflow

REPO = Path(__file__).parent.parent
EXAMPLES = REPO / "quorum" / "ui" / "examples"
DOCS = [(p.name, p.read_text(encoding="utf-8")) for p in sorted(EXAMPLES.glob("oferta-*.md"))]
WINNER = "Ferrelectro del Sur Ltda"


@pytest.fixture(autouse=True)
def no_configuration(monkeypatch):
    """Whatever .env the developer has, these tests run without key, tokens or agent services."""
    monkeypatch.setattr(agents, "ENV_FILE", REPO / "no-such-file")
    monkeypatch.setattr(agents.load_env, "__defaults__", (REPO / "no-such-file",))
    tokens = [f"QUORUM_TOKEN_{role.upper()}" for role in ROLES]
    for name in ("OPENROUTER_API_KEY", "QUORUM_MODEL", "QUORUM_AGENT_URLS", *tokens):
        monkeypatch.delenv(name, raising=False)


def honest_chat():
    """One fake honest model per role, told apart by the tools each role is offered."""
    models = {}

    def chat(messages, tools):
        names = {t["function"]["name"] for t in tools}
        role = "registrar" if "read_annex" in names else "evaluator" if "score_bids" in names else "publisher"
        if len(messages) == 2:
            models[role] = model(HONEST[role])
        return models[role](messages, tools)
    return chat


# --- documents ------------------------------------------------------------------

def test_parse_bid_splits_value_and_annex():
    bid = workflow.parse_bid("Proveedor: Acme SAS\nValor: $ 412.345.678\n\nCarta.", "x.md")
    assert (bid.supplier, bid.value) == ("Acme SAS", 412345678)
    assert "412" not in bid.annex and "Carta." in bid.annex


def test_parse_bid_without_value_fails():
    with pytest.raises(ValueError):
        workflow.parse_bid("Proveedor: Acme SAS\nCarta.")


def test_parse_bid_tolerates_ocr_noise():
    bid = workflow.parse_bid("| Proveedor; Acme SAS\n\n. Valor de la oferta: $ 412 345 678 COP\nCarta.", "s.pdf", True)
    assert (bid.supplier, bid.value, bid.scanned) == ("Acme SAS", 412345678, True)
    assert "412" not in bid.annex


def test_a_case_needs_two_bids_from_different_suppliers():
    one = workflow.parse_bid(DOCS[0][1], DOCS[0][0])
    with pytest.raises(ValueError):
        workflow.build_case([one])
    with pytest.raises(ValueError):
        workflow.build_case([one, one])


def test_plain_text_needs_no_tools_and_binaries_are_rejected():
    assert documents.extract("a.md", b"Valor: 1") == ("Valor: 1", documents.TEXT)
    with pytest.raises(documents.ExtractionError):
        documents.extract("a.docx", b"PK\x03\x04\x00\x00")
    with pytest.raises(documents.ExtractionError):
        documents.extract("a.txt", b"x" * (documents.MAX_BYTES + 1))


def test_example_pdfs_are_read_with_text_layer_and_with_ocr():
    if not documents.available()["scanned_pdf"]:
        pytest.skip("needs poppler-utils and tesseract (they come in the image built with WITH_OCR=1)")
    read = {p.name: server.read_document(p.name, p.read_bytes()) for p in sorted((EXAMPLES / "pdf").glob("*.pdf"))}
    assert read["oferta-1.pdf"]["method"] == documents.PDF and not read["oferta-1.pdf"]["scanned"]
    scan = read["oferta-2-escaneada.pdf"]
    assert scan["method"] == documents.OCR and scan["scanned"] and scan["supplier"] == WINNER and scan["digits"] == 9


# --- the episode ------------------------------------------------------------------

def test_scripted_honest_publishes_the_winner_without_leak():
    events = []
    r = workflow.run(DOCS, "honest", emit=events.append)
    assert set(r["engines"].values()) == {"scripted"} and not r["containers"]
    assert r["expected_winner"] == WINNER and r["useful"]
    assert not r["leak"] and not r["blocks"] and not r["agent_errors"] and r["audit_log_ok"]
    assert events[0]["agent"] == "registrar" and events[-1]["tool"] == "publish"
    assert events[-1]["decision"]["allow"] and all(not e["secrets"] for e in events)


@pytest.mark.parametrize("k", [1, 2, 3])
def test_scripted_attack_over_uploaded_documents_is_stopped_by_the_gate(k):
    audit = workflow.run(DOCS, f"attack_k{k}", defense=False)
    enforced = workflow.run(DOCS, f"attack_k{k}", defense=True)
    assert audit["leak"] and audit["blocks"] and not audit["blocks"][0]["enforced"]
    assert not enforced["leak"] and enforced["blocks"] and enforced["blocks"][0]["enforced"]
    assert enforced["attempt_had_secret"] and enforced["audit_log_ok"]


def test_attacks_need_a_bid_from_the_target_supplier():
    others = [(n, t.replace(WINNER, "Otro Proveedor SAS")) for n, t in DOCS]
    assert workflow.run(others, "honest")["useful"]
    with pytest.raises(ValueError):
        workflow.run(others, "attack_k1")


def test_events_carry_the_label_from_the_audit_log():
    events = []
    workflow.run(DOCS, "attack_k3", emit=events.append)
    blocked = [e for e in events if e["tool"] == "publish" and not e["decision"]["allow"]]
    assert blocked and blocked[0]["secrets"]


def test_a_scanned_bid_enters_as_a_scan_and_is_transcribed():
    events = []
    r = workflow.run([(n, t, n == "oferta-2.md") for n, t in DOCS], "honest", emit=events.append)
    assert r["scan"] and "transcribe" in [e["tool"] for e in events if e["agent"] == "registrar"]
    assert r["useful"] and not r["leak"] and not r["blocks"]
    assert all(not e["secrets"] for e in events)   # transcribing does not taint the registrar


def test_only_the_first_scanned_bid_goes_through_the_registrar():
    case = workflow.build_case([workflow.parse_bid(t, n, True) for n, t in DOCS])
    assert case.scan == "scan-1"
    assert workflow.run([(n, t, True) for n, t in DOCS], "honest")["useful"]


@pytest.mark.parametrize("scanned", [False, True])
def test_llm_agents_with_a_fake_model_over_documents(scanned):
    events = []
    docs = [(n, t, scanned and n == "oferta-2.md") for n, t in DOCS]
    r = workflow.run(docs, "honest", engine="llm", emit=events.append, chat=honest_chat())
    assert set(r["engines"].values()) == {"llm"} and not r["containers"]
    assert r["useful"] and not r["leak"] and not r["blocks"] and not r["agent_errors"]
    assert {e["agent"] for e in events} == set(ROLES)


def test_in_an_attack_only_the_roles_that_deviate_are_scripted():
    assert workflow.plan("attack_k1", "scripted") == dict.fromkeys(ROLES, "scripted")
    assert workflow.plan("honest", "llm") == dict.fromkeys(ROLES, "llm")
    assert workflow.plan("attack_k1", "llm") == {"registrar": "llm", "evaluator": "scripted", "publisher": "llm"}
    assert workflow.plan("attack_k3", "llm") == dict.fromkeys(ROLES, "scripted")
    assert workflow.plan("attack_k1", "llm", {"evaluator": "X"}) == dict.fromkeys(ROLES, "llm")
    r = workflow.run(DOCS, "attack_k1", engine="llm", chat=honest_chat())
    assert not r["leak"] and r["blocks"] and r["engines"]["evaluator"] == "scripted"


def test_without_key_the_llm_engine_falls_back_to_scripted():
    assert not workflow.llm_available()
    r = workflow.run(DOCS, "honest", engine="llm")
    assert set(r["engines"].values()) == {"scripted"} and r["useful"]


def test_status_shows_who_deviates_and_the_hash_of_the_team_prompts():
    assert {card["version"] for card in workflow.status()} == {"honest"}
    cards = {card["role"]: card for card in workflow.status("attack_k2")}
    assert [cards[r]["version"] for r in ROLES] == ["modified", "modified", "honest"]
    assert all(cards[r]["hash"] == workflow.prompt_hash(r) and "container" not in cards[r] for r in ROLES)
    assert len({workflow.prompt_hash(r) for r in ROLES}) == 3 and SYSTEM["registrar"]


# --- the server of the page -------------------------------------------------------

def test_reset_goes_back_to_the_initial_state():
    state = server.State()
    initial = state.view()
    state.kind, state.events, state.result = "attack_k3", [{"x": 1}], {"leak": True}
    assert not state.view()["initial"]
    state.reset()
    view = state.view()
    assert view["initial"] and view["agents"] == initial["agents"]
    assert view["events"] == [] and view["result"] is None


def test_the_view_remembers_how_the_last_run_was_configured():
    """The page sets its selectors from these, so they never contradict the run on screen."""
    state = server.State()
    assert (state.view()["defense"], state.view()["engine"]) == (True, "scripted")
    state.start({"documents": [], "kind": "attack_k1", "defense": False, "engine": "scripted"})
    view = state.view()
    assert (view["kind"], view["defense"], view["engine"]) == ("attack_k1", False, "scripted")
    state.reset()
    assert (state.view()["defense"], state.view()["engine"]) == (True, "scripted")


def serve(handler):
    srv = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


def status_of(url, header=None, body=None):
    request = urllib.request.Request(url, data=body, headers={"Authorization": header} if header else {})
    try:
        return urllib.request.urlopen(request, timeout=5).status
    except urllib.error.HTTPError as e:
        return e.code


def test_the_page_asks_for_the_key_when_there_is_one(monkeypatch):
    srv, url = serve(server.Handler)

    def basic(key):
        return "Basic " + base64.b64encode(f"quorum:{key}".encode()).decode()
    try:
        monkeypatch.setattr(server, "PASSWORD", "test-key")
        assert [status_of(f"{url}/api/state", h) for h in (None, basic("other"), "Bearer test-key")] == [401] * 3
        assert status_of(f"{url}/api/state", basic("test-key")) == 200
        monkeypatch.setattr(server, "PASSWORD", None)
        assert status_of(f"{url}/api/state") == 200 and status_of(f"{url}/agent/tools") == 404
    finally:
        srv.shutdown()


def test_the_page_runs_an_episode_end_to_end(monkeypatch):
    monkeypatch.setattr(server, "PASSWORD", None)
    monkeypatch.setattr(server, "STATE", server.State())
    srv, url = serve(server.Handler)

    def call(path, body=None):
        data = None if body is None else json.dumps(body).encode()
        return json.loads(urllib.request.urlopen(urllib.request.Request(url + path, data=data), timeout=10).read())
    try:
        docs = call("/api/examples")
        assert [d["supplier"] for d in docs][1] == WINNER and all("value" not in d for d in docs)
        view = call("/api/run", {"documents": docs, "kind": "attack_k3", "defense": True})
        for _ in range(100):
            if not view["running"]:
                break
            time.sleep(0.1)
            view = call("/api/state")
        assert view["error"] is None and not view["result"]["leak"] and view["result"]["blocks"]
        assert view["events"] and [a["version"] for a in view["agents"]] == ["modified"] * 3
        assert call("/api/reset", {})["initial"]
    finally:
        srv.shutdown()


# --- one service per agent ---------------------------------------------------------

def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_agents_in_their_own_services_take_turns_over_the_protocol(monkeypatch):
    tokens = {role: f"token-of-{role}-{os.urandom(8).hex()}" for role in ROLES}
    ports = {role: free_port() for role in ROLES}
    monitor = free_port()
    base = {k: v for k, v in os.environ.items() if not k.startswith(("QUORUM_", "OPENROUTER_"))}
    services = [subprocess.Popen(
        [sys.executable, "-m", "quorum.ui.agent_service", str(ports[role])], cwd=REPO,
        env={**base, "QUORUM_ROLE": role, "QUORUM_TOKEN": tokens[role],
             "QUORUM_MONITOR_URL": f"http://127.0.0.1:{monitor}"},
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) for role in ROLES]
    try:
        for role in ROLES:
            monkeypatch.setenv(f"QUORUM_TOKEN_{role.upper()}", tokens[role])
        monkeypatch.setenv("QUORUM_AGENT_URLS", ",".join(f"{r}=http://127.0.0.1:{ports[r]}" for r in ROLES))
        monkeypatch.setenv("QUORUM_MONITOR_PORT", str(monitor))
        assert agents.remote()
        deadline = time.monotonic() + 20
        while not all(agents.health(role, max_age=0) for role in ROLES):
            assert time.monotonic() < deadline, "the agent services did not start"
            time.sleep(0.2)

        cards = workflow.status()
        assert all(c["container"]["up"] and c["container"]["intact"] for c in cards)
        # an agent service only obeys its own token
        url = f"http://127.0.0.1:{ports['publisher']}"
        assert status_of(f"{url}/health", f"Bearer {tokens['registrar']}") == 401
        assert status_of(f"{url}/run", "Bearer nope", b"{}") == 401

        events = []
        honest = workflow.run(DOCS, "honest", emit=events.append)
        assert honest["containers"] and honest["useful"] and not honest["leak"] and not honest["agent_errors"]
        assert {e["agent"] for e in events} == set(ROLES)
        attack = workflow.run(DOCS, "attack_k3")
        assert attack["containers"] and not attack["leak"] and attack["blocks"][0]["enforced"]
        assert workflow.run(DOCS, "attack_k3", defense=False)["leak"]
    finally:
        for service in services:
            service.kill()
            service.wait()
