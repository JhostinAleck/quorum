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
    "a prefix is no longer untrusted": lambda p: p.evolve(untrusted=p.untrusted[1:]),
    "a prefix becomes untrusted": lambda p: p.evolve(untrusted=(*p.untrusted, "terms.")),
    "a declassifier is dropped": lambda p: p.evolve(declassifiers=sorted(p.declassifiers)[1:]),
    "a declassifier is added": lambda p: p.evolve(declassifiers={*p.declassifiers, "read"}),
    "a role can write more": lambda p: p.evolve(roles={
        **p.roles, "publisher": type(p.roles["publisher"])("publisher", p.roles["publisher"].tools,
                                                          p.roles["publisher"].reads, ("registry.",))}),
    "a role is renamed inside": lambda p: p.evolve(roles={
        **p.roles, "publisher": type(p.roles["publisher"])("registrar", p.roles["publisher"].tools,
                                                          p.roles["publisher"].reads, p.roles["publisher"].writes)}),
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


# --- what a review of the first version found --------------------------------------------------

def test_a_text_where_a_list_was_meant_is_not_the_list_of_its_letters():
    role = type(POLICY.roles["publisher"])
    one = POLICY.evolve(roles={"x": role("x", "ab", "bids/")})
    other = POLICY.evolve(roles={"x": role("x", ("a", "b"), ("/", "b", "d", "i", "s"))})
    assert integrity.policy_digest(one) != integrity.policy_digest(other)


@pytest.mark.parametrize("field", ["description", "params", "rationale", "name"])
def test_every_part_of_a_tool_s_interface_is_in_its_hash(field):
    tool = next(t for t in TOOLS if t.kind is Kind.DECLASSIFIER)
    changed = Tool(tool.name, tool.fn, tool.description, tool.params, tool.kind, tool.rationale)
    if field == "params":
        changed.params = {name: text + " (otro)" for name, text in tool.params.items()}
    else:
        setattr(changed, field, getattr(tool, field) + "x")
    swapped = [changed if t is tool else t for t in TOOLS]
    assert integrity.tools_digest(swapped) != integrity.tools_digest(TOOLS)


def test_a_file_in_a_subfolder_counts(tmp_path):
    copy = tmp_path / "tender"
    shutil.copytree(integrity.ROOT / "scenarios" / "tender", copy, ignore=shutil.ignore_patterns("__pycache__"))
    original = integrity.files_digest(copy)
    (copy / "deep" / "deeper").mkdir(parents=True)
    (copy / "deep" / "deeper" / "extra.py").write_text("X = 1\n", encoding="utf-8")
    assert integrity.files_digest(copy) != original


@pytest.mark.parametrize("plant", ["compiled package", "compiled module", "linked folder", "linked file"])
def test_something_planted_to_be_imported_in_place_of_the_source_is_refused(tmp_path, plant):
    """A compiled file or a link is imported without a look at the source that the hash covers."""
    copy = tmp_path / "tender"
    shutil.copytree(integrity.ROOT / "scenarios" / "tender", copy, ignore=shutil.ignore_patterns("__pycache__"))
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "__init__.py").write_text("evaluate = None\n", encoding="utf-8")
    if plant == "compiled package":
        (copy / "rules").mkdir()
        (copy / "rules" / "__init__.pyc").write_bytes(b"\x00")
    elif plant == "compiled module":
        (copy / "rules.so").write_bytes(b"\x00")
    elif plant == "linked folder":
        (copy / "gate").symlink_to(outside, target_is_directory=True)
    else:
        (copy / "extra.py").symlink_to(outside / "__init__.py")
    with pytest.raises(InvalidConfiguration):
        integrity.files_digest(copy)
    (copy / "__pycache__").mkdir(exist_ok=True)
    (copy / "__pycache__" / "rules.cpython-313.pyc").write_bytes(b"\x00")    # the cache is where they belong


def test_the_seal_says_whether_the_gate_blocks_or_only_watches():
    """Audit mode turns the gate off without touching a file: the hashes are the same, the seal is not."""
    blocking, watching = tender.prepare(1, defense=True), tender.prepare(1, defense=False)
    same = integrity.seal(blocking.quorum, "tender")
    assert integrity.seal(watching.quorum, "tender") == same
    assert integrity.sealed_runtime(blocking.quorum.audit_log)["enforce"] is True
    assert integrity.sealed_runtime(watching.quorum.audit_log)["enforce"] is False
    assert integrity.sealed_runtime(blocking.quorum.audit_log)["rules"] and integrity.verify_log(watching.quorum,
                                                                                                "tender")
    watching.quorum.enforce = True                      # the monitor no longer runs the way it sealed
    assert not integrity.verify_log(watching.quorum, "tender")
    assert integrity.sealed_runtime(tender.prepare(2, defense=True).quorum.audit_log) is None


def test_a_monitor_without_rules_or_with_an_approver_seals_that():
    bare = new_monitor(POLICY, TOOLS, rules=(), approver=lambda request: True)
    integrity.seal(bare)
    assert integrity.sealed_runtime(bare.audit_log) == {"enforce": True, "rules": [], "approver": True}


def test_a_log_is_sealed_once():
    case = tender.prepare(1, defense=True)
    integrity.seal(case.quorum, "tender")
    with pytest.raises(InvalidConfiguration):
        integrity.seal(case.quorum, "tender")
    assert sum(event["kind"] == "integrity" for event in case.quorum.audit_log) == 1


@pytest.mark.parametrize("text", ["[]", "null", '{"scenarios": {"tender": "x"}}', '{"kernel": 3}', '"x"'])
def test_a_lock_of_the_wrong_shape_is_a_difference_and_not_a_crash(tmp_path, text):
    lock = tmp_path / "lock.json"
    lock.write_text(text, encoding="utf-8")
    assert integrity.check(lock) and not integrity.pinned("tender", lock)
    assert integrity.locked_pipeline("tender", lock) == ""


def test_the_check_compares_every_hash_the_lock_holds(tmp_path):
    lock = tmp_path / "lock.json"
    pinned = integrity.current()
    pinned["scenarios"]["tender"]["pipeline"] = "0" * 64
    lock.write_text(json.dumps(pinned), encoding="utf-8")
    assert integrity.check(lock) == ["tender: pipeline changed"] and not integrity.pinned("tender", lock)
    pinned = integrity.current()
    pinned["scenarios"]["tender"]["kernel"] = "0" * 64
    lock.write_text(json.dumps(pinned), encoding="utf-8")
    assert integrity.check(lock) == ["tender: kernel changed"]
    assert integrity.locked_pipeline("tender") == integrity.current()["scenarios"]["tender"]["pipeline"]


def test_the_service_that_gives_each_token_its_role_is_part_of_the_trusted_path():
    assert {"launch.py", "integrity.py", "__init__.py", "adapters/http_server.py"} <= set(integrity.KERNEL)
    for part in integrity.KERNEL:
        assert (integrity.ROOT / part).exists(), part


@pytest.mark.parametrize("plant", ["package of the same name", "compiled twin", "compiled twin with a tag", "link"])
def test_a_lone_module_cannot_be_shadowed_by_a_neighbour_of_the_same_name(tmp_path, plant):
    """An import prefers a package or a compiled module over the source of the same name, and only that is hashed."""
    (tmp_path / "pkg").mkdir()
    module = tmp_path / "pkg" / "http_server.py"
    module.write_text("ROLE = 'registrar'\n", encoding="utf-8")
    (tmp_path / "pkg" / "other.py").write_text("X = 1\n", encoding="utf-8")
    (tmp_path / "pkg" / "http_server_notes.txt").write_text("unrelated", encoding="utf-8")
    clean = integrity.files_digest(tmp_path, ["pkg/http_server.py"])
    if plant == "package of the same name":
        (tmp_path / "pkg" / "http_server").mkdir()
        (tmp_path / "pkg" / "http_server" / "__init__.py").write_text("ROLE = 'admin'\n", encoding="utf-8")
    elif plant == "compiled twin":
        (tmp_path / "pkg" / "http_server.so").write_bytes(b"\x00")
    elif plant == "compiled twin with a tag":
        (tmp_path / "pkg" / "http_server.cpython-313-darwin.so").write_bytes(b"\x00")
    else:
        (tmp_path / "pkg" / "http_server.pyc").symlink_to(tmp_path / "pkg" / "other.py")
    with pytest.raises(InvalidConfiguration, match="in place of http_server"):
        integrity.files_digest(tmp_path, ["pkg/http_server.py"])
    assert integrity.files_digest(tmp_path, ["pkg/other.py"]) != clean      # a neighbour by another name is fine
