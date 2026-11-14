"""Hashes of the policy, the tools, the kernel and the scenario files, and what they are checked against."""
import json
import shutil

import pytest

from quorum import InvalidConfiguration, Kind, Tool, integrity, new_monitor
from quorum.scenarios import tender
from quorum.scenarios.tender import POLICY, TOOLS


def test_the_lock_matches_the_code():
    """Fails when the policy, the tools, the kernel or a scenario changed and the lock did not."""
    differences = integrity.check()
    assert not differences, ("the code is not the pinned one: " + "; ".join(differences)
                             + ". If the change is intended, run `python -m quorum.integrity --write` "
                             "and commit quorum/integrity.lock.json with it.")


def test_every_scenario_is_pinned():
    lock = json.loads(integrity.LOCK.read_text(encoding="utf-8"))
    assert set(lock["scenarios"]) == set(integrity.SCENARIOS)
    for name, hashes in lock["scenarios"].items():
        assert set(hashes) == {"policy", "tools", "kernel", "scenario", "pipeline"}, name
        assert all(len(value) == 64 for value in hashes.values()), name
    assert len({hashes["pipeline"] for hashes in lock["scenarios"].values()}) == len(integrity.SCENARIOS)


WEAKER = {
    "a prefix is no longer restricted": lambda p: p.evolve(restricted=p.restricted[1:]),
    "a sink accepts a restricted source": lambda p: p.evolve(sinks={**p.sinks, "publish": ("sealed.",)}),
    "a source is endorsed to leave": lambda p: p.evolve(endorsements={"sealed.bid-2"}),
    "a quota is raised": lambda p: p.evolve(quotas={**p.quotas, "publish": 99}),
    "a quota is dropped": lambda p: p.evolve(quotas={}),
    "the high water mark is off": lambda p: p.evolve(high_water_mark=not p.high_water_mark),
    "strict mode is flipped": lambda p: p.evolve(strict_mode=not p.strict_mode),
    "a role can read more": lambda p: p.evolve(roles={
        **p.roles, "publisher": type(p.roles["publisher"])("publisher", p.roles["publisher"].tools,
                                                          (*p.roles["publisher"].reads, "sealed."),
                                                          p.roles["publisher"].writes)}),
    "a role gets another tool": lambda p: p.evolve(roles={
        **p.roles, "publisher": type(p.roles["publisher"])("publisher", (*p.roles["publisher"].tools, "open_bid"),
                                                          p.roles["publisher"].reads, p.roles["publisher"].writes)}),
}


@pytest.mark.parametrize("change", WEAKER, ids=list(WEAKER))
def test_any_change_to_a_rule_changes_the_hash_of_the_policy(change):
    assert integrity.policy_digest(WEAKER[change](POLICY)) != integrity.policy_digest(POLICY)


def test_the_hash_of_the_policy_is_about_what_it_means_and_not_how_it_is_written():
    same = POLICY.evolve(restricted=tuple(reversed(POLICY.restricted)),
                         sinks=dict(reversed(list(POLICY.sinks.items()))),
                         roles=dict(reversed(list(POLICY.roles.items()))))
    assert integrity.policy_digest(same) == integrity.policy_digest(POLICY)
    assert integrity.policy_digest(POLICY.evolve()) == integrity.policy_digest(POLICY)


def test_turning_a_declassifier_into_a_plain_tool_changes_the_hash_of_the_tools():
    demoted = [Tool(t.name, t.fn, t.description, t.params, Kind.NORMAL) if t.kind is Kind.DECLASSIFIER else t
               for t in TOOLS]
    assert integrity.tools_digest(demoted) != integrity.tools_digest(TOOLS)
    assert integrity.tools_digest(list(reversed(TOOLS))) == integrity.tools_digest(TOOLS)
    assert integrity.tools_digest(TOOLS[1:]) != integrity.tools_digest(TOOLS)


def test_the_hash_of_the_files_sees_one_changed_byte_and_ignores_line_endings_and_caches(tmp_path):
    copy = tmp_path / "tender"
    shutil.copytree(integrity.ROOT / "scenarios" / "tender", copy)
    original = integrity.files_digest(copy)
    assert original == integrity.scenario_digest("tender")

    policy = copy / "policy.toml"
    text = policy.read_text(encoding="utf-8")
    policy.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
    (copy / "__pycache__").mkdir(exist_ok=True)
    (copy / "__pycache__" / "x.pyc").write_bytes(b"\x00")
    (copy / "notes.txt").write_text("not source", encoding="utf-8")
    assert integrity.files_digest(copy) == original

    policy.write_text(text.replace("high_water_mark = true", "high_water_mark = false"), encoding="utf-8")
    assert "high_water_mark = false" in policy.read_text(encoding="utf-8")
    assert integrity.files_digest(copy) != original

    policy.write_text(text, encoding="utf-8")
    (copy / "extra.py").write_text("# a new module\n", encoding="utf-8")
    assert integrity.files_digest(copy) != original

    with pytest.raises(InvalidConfiguration):
        integrity.files_digest(tmp_path / "empty")


def test_the_fingerprint_is_sealed_in_the_log_before_any_agent_acts():
    case = tender.prepare(1, defense=True)
    found = integrity.seal(case.quorum, "tender")
    assert found == json.loads(integrity.LOCK.read_text(encoding="utf-8"))["scenarios"]["tender"]
    assert integrity.sealed(case.quorum.audit_log) == found
    for role in tender.ROLES:
        tender.ROLE_STEPS[role](case.session(role), "attack_k3")
    assert case.quorum_blocks and integrity.verify_log(case.quorum, "tender")
    event = next(e for e in case.quorum.audit_log if e["kind"] == "integrity")
    assert event["pipeline_of"] == "tender" and event["hash"] and case.quorum.audit_log.verify()


def test_a_log_whose_seal_was_edited_no_longer_verifies():
    case = tender.prepare(1, defense=True)
    integrity.seal(case.quorum, "tender")
    event = next(e for e in case.quorum.audit_log if e["kind"] == "integrity")
    event["policy"] = "0" * 64                      # somebody rewrites which policy decided
    assert not case.quorum.audit_log.verify() and not integrity.verify_log(case.quorum, "tender")


def test_a_log_sealed_by_another_policy_does_not_verify_against_this_one():
    weaker = POLICY.evolve(high_water_mark=False)
    case = tender.prepare(1, defense=True, policy=weaker)
    sealed = integrity.seal(case.quorum, "tender")
    assert sealed["policy"] != integrity.policy_digest(POLICY) and sealed["pipeline"] != integrity.fingerprint(
        POLICY, TOOLS, "tender")["pipeline"]
    assert integrity.verify_log(case.quorum, "tender")           # true to the policy that is running...
    assert integrity.sealed(case.quorum.audit_log) != integrity.fingerprint(POLICY, TOOLS, "tender")   # ...not ours


def test_the_seal_cannot_come_after_a_call_and_a_log_without_it_has_none():
    case = tender.prepare(1, defense=True)
    assert integrity.sealed(case.quorum.audit_log) is None
    case.session("registrar").call("read", key="terms.bids")
    with pytest.raises(InvalidConfiguration):
        integrity.seal(case.quorum, "tender")
    assert integrity.sealed(case.quorum.audit_log) is None and not integrity.verify_log(case.quorum, "tender")


def test_an_expected_hash_that_does_not_match_stops_the_monitor_before_it_seals_anything():
    case = tender.prepare(1, defense=True)
    events = len(case.quorum.audit_log)
    with pytest.raises(InvalidConfiguration, match="was expected"):
        integrity.seal(case.quorum, "tender", expected="f" * 64)
    assert len(case.quorum.audit_log) == events
    right = integrity.fingerprint(POLICY, TOOLS, "tender")["pipeline"]
    assert integrity.seal(case.quorum, "tender", expected=right)["pipeline"] == right


def test_a_monitor_without_a_scenario_package_is_sealed_by_its_policy_tools_and_kernel():
    quorum = new_monitor(POLICY, TOOLS)
    found = integrity.seal(quorum)
    assert set(found) == {"policy", "tools", "kernel", "pipeline"} and integrity.verify_log(quorum)


def test_the_check_names_what_changed(tmp_path):
    lock = tmp_path / "lock.json"
    pinned = integrity.current()
    lock.write_text(json.dumps(pinned), encoding="utf-8")
    assert integrity.check(lock) == [] and integrity.pinned("tender", lock)

    pinned["scenarios"]["bank"]["policy"] = "0" * 64
    lock.write_text(json.dumps(pinned), encoding="utf-8")
    assert integrity.check(lock) == ["bank: policy changed"]
    assert integrity.pinned("tender", lock) and not integrity.pinned("bank", lock)   # each scenario on its own

    pinned["kernel"] = "0" * 64
    lock.write_text(json.dumps(pinned), encoding="utf-8")
    assert not integrity.pinned("tender", lock) and any(d.startswith("kernel:") for d in integrity.check(lock))

    del pinned["scenarios"]["clinic"]
    lock.write_text(json.dumps(pinned), encoding="utf-8")
    assert "clinic: policy changed" in integrity.check(lock)

    assert not integrity.pinned("tender", tmp_path / "missing.json")
    lock.write_text("not json", encoding="utf-8")
    assert not integrity.pinned("tender", lock)


def test_the_command_exits_with_an_error_when_the_lock_is_stale(tmp_path, monkeypatch, capsys):
    integrity.main([])
    assert "ok" in capsys.readouterr().out
    stale = tmp_path / "lock.json"
    stale.write_text(json.dumps({"kernel": "0" * 64, "scenarios": {}}), encoding="utf-8")
    monkeypatch.setattr(integrity, "LOCK", stale)
    monkeypatch.setattr(integrity.check, "__defaults__", (stale,))
    with pytest.raises(SystemExit) as stop:
        integrity.main([])
    assert stop.value.code and "kernel" in capsys.readouterr().err
