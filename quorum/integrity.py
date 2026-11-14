"""Hashes of what decides: the policy, the tools, the kernel and the files that define each pipeline.

The gate is only as good as the policy it is given and the code that runs it.
Whoever can edit `policy.toml`, the tools of a scenario or the kernel can turn
the gate off without touching an agent. This module makes such a change
visible, in three places:

  1. A lock file, `quorum/integrity.lock.json`, pins the hashes. A test fails
     when the code and the lock disagree, so a change to the policy, the tools
     or the kernel shows up in the same review as the lock that accepts it.
  2. The monitor service checks the lock before it serves and refuses to start
     on a mismatch. An operator can also hand it the expected pipeline hash
     from outside the repository (QUORUM_EXPECT_PIPELINE).
  3. The fingerprint is sealed in the audit log before any agent acts. The log
     is chained with hashes, so every decision in it is bound to the policy
     and the code that made it.

Four hashes, and one that sums them up:

  policy    what the policy means, not how the file is written: comments, order
            and spacing do not change it, any rule does
  tools     the interface of every tool a role can call: name, kind,
            description, parameters and rationale
  kernel    every source file on the trusted path: the domain, the application
            and the infrastructure, the composition roots, the service that
            turns a token into a role, and this module
  scenario  every source and policy file of the scenario's package: where the
            pipeline is defined
  pipeline  the hash of the four above

The seal also says how the monitor runs: whether the gate blocks or only
audits, which rules it applies and whether an approver is plugged in. Those
are not in the code, so no file hash would show them.

What this does not do: it is not a signature. Somebody who can rewrite the
code, the lock and the expected hash at once is not stopped by it; the hash
that an auditor compares against has to live somewhere that person cannot
write. It reads source files: a compiled file or a link planted next to them
is reported, but the bytecode cache and the interpreter are trusted.

    python -m quorum.integrity            check the lock; exit 1 on any difference
    python -m quorum.integrity --write    accept the current code as the pinned one
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from .application.monitor import Quorum
from .domain.errors import InvalidConfiguration
from .domain.policy import Policy
from .domain.tools import Tool

__all__ = ["KERNEL", "LOCK", "SCENARIOS", "check", "current", "files_digest", "fingerprint", "kernel_digest",
           "locked_pipeline", "pinned", "planted", "policy_digest", "runtime", "scenario_digest", "seal", "sealed",
           "sealed_runtime", "tools_digest", "verify_log", "write"]

ROOT = Path(__file__).resolve().parent
LOCK = ROOT / "integrity.lock.json"
KERNEL = ("domain", "application", "infrastructure", "bootstrap.py", "launch.py", "integrity.py", "__init__.py",
          "adapters/__init__.py", "adapters/http_server.py", "adapters/http_client.py", "adapters/functions.py",
          "scenarios/__init__.py", "scenarios/spanish.py")
SCENARIOS = ("tender", "helpdesk", "clinic", "bank", "lawfirm", "tender_rubric")
_SOURCES = (".py", ".toml")
_COMPILED = (".pyc", ".pyo", ".so", ".pyd", ".dylib")
_PARTS = ("policy", "tools", "kernel", "scenario", "pipeline")


def _sha256(value: Any) -> str:
    """The hash of a JSON value in its one canonical form."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def policy_digest(policy: Policy) -> str:
    """The hash of what the policy means. Two files that say the same thing give the same hash."""
    return _sha256({
        "restricted": sorted(policy.restricted), "untrusted": sorted(policy.untrusted),
        "sinks": {sink: sorted(sources) for sink, sources in policy.sinks.items()},
        "declassifiers": sorted(policy.declassifiers), "endorsements": sorted(policy.endorsements),
        "quotas": dict(policy.quotas), "strict_mode": policy.strict_mode, "high_water_mark": policy.high_water_mark,
        # the order of a role's tools is the order the agent sees them in, not a rule: it is left out
        "roles": {name: {"name": role.name, "tools": _listed(role.tools), "reads": _listed(role.reads),
                         "writes": _listed(role.writes)} for name, role in policy.roles.items()},
    })


def _listed(value: Any) -> Any:
    """A role's field in canonical form. A bare text is kept apart from a list of its letters."""
    return {"text": value} if isinstance(value, str) else sorted(value)


def tools_digest(tools: Iterable[Tool]) -> str:
    """The hash of the tools' interface: what each one is called, what kind it is and what it says it does."""
    return _sha256(sorted(
        ({"name": tool.name, "kind": tool.kind.value, "description": tool.description,
          "params": dict(tool.params), "rationale": tool.rationale} for tool in tools),
        key=lambda item: item["name"]))


def files_digest(root: Path, parts: Iterable[str] = (".",)) -> str:
    """The hash of every source and policy file under `parts` of `root`, with its path. Line endings do not count."""
    found: dict[str, str] = {}
    for part in parts:
        path = root / part
        if path.is_file():      # a lone module: a folder or a compiled file of the same name would be imported instead
            for other in path.parent.iterdir():
                if other != path and other.name.split(".")[0] == path.stem and (
                        other.is_dir() or other.suffix in _COMPILED or other.is_symlink()):
                    raise InvalidConfiguration(f"{other.relative_to(root).as_posix()}: it would be imported in "
                                               f"place of {path.name}")
        for file in ([path] if path.is_file() else sorted(path.rglob("*"))):
            strays = planted(file)
            if strays:      # something that would be imported instead of the source that is hashed
                raise InvalidConfiguration(f"{file.relative_to(root).as_posix()}: {strays}")
            if file.is_file() and file.suffix in _SOURCES:
                content = file.read_bytes().replace(b"\r\n", b"\n")
                found[file.relative_to(root).as_posix()] = hashlib.sha256(content).hexdigest()
    if not found:
        raise InvalidConfiguration(f"nothing to hash under {root}")
    return _sha256(found)


def planted(file: Path) -> str:
    """Why a file next to the sources cannot be trusted, or '' if it can.

    Python imports a link or a compiled module without looking at the source this module hashes.
    """
    if file.is_symlink():
        return "a link: what it points to is outside what is hashed"
    if file.suffix in _COMPILED and file.parent.name != "__pycache__":
        return "a compiled file outside the cache: it would be imported in place of the source"
    return ""


def kernel_digest() -> str:
    return files_digest(ROOT, KERNEL)


def scenario_digest(scenario: str) -> str:
    return files_digest(ROOT / "scenarios" / scenario)


def fingerprint(policy: Policy, tools: Iterable[Tool], scenario: str = "") -> dict[str, str]:
    """The hashes of a pipeline. `scenario` names the package that defines it, when there is one."""
    parts = {"policy": policy_digest(policy), "tools": tools_digest(tools), "kernel": kernel_digest()}
    if scenario:
        parts["scenario"] = scenario_digest(scenario)
    return {**parts, "pipeline": _sha256(parts)}


def _tools_of(quorum: Quorum) -> list[Tool]:
    """The tools some role can call. One that no role has cannot be reached by any agent."""
    return [quorum.tool(name) for name in sorted({name for role in quorum.policy.roles.values()
                                                  for name in role.tools})]


def runtime(quorum: Quorum) -> dict[str, Any]:
    """How the monitor runs, which no file says: does the gate block, with which rules, is there an approver."""
    return {"enforce": bool(quorum.enforce),
            "rules": [getattr(rule, "__qualname__", repr(rule)) for rule in quorum._rules],
            "approver": quorum._approver is not None}


def seal(quorum: Quorum, scenario: str = "", *, expected: str = "") -> dict[str, str]:
    """Write the fingerprint of a monitor in its audit log, before any agent acts, and return it.

    `expected` is the pipeline hash the operator trusts: if it is given and it is not the one found,
    nothing is sealed and InvalidConfiguration is raised. A log is sealed once.
    """
    if any(event.get("kind") in ("call", "integrity") for event in quorum.audit_log):
        raise InvalidConfiguration("the audit log already has calls or a seal: the fingerprint is sealed once, "
                                   "before any agent acts")
    found = fingerprint(quorum.policy, _tools_of(quorum), scenario)
    if expected and expected != found["pipeline"]:
        raise InvalidConfiguration(f"the pipeline hash is {found['pipeline']} and {expected} was expected: "
                                   "the policy, the tools or the code are not the ones that were approved")
    quorum.audit_log.record(kind="integrity", pipeline_of=scenario, runtime=runtime(quorum), **found)
    return found


def sealed(events: Iterable[Mapping[str, Any]]) -> dict[str, str] | None:
    """The fingerprint sealed in an audit log, or None if there is none before the first call."""
    for event in events:
        if event.get("kind") == "call":
            return None
        if event.get("kind") == "integrity":
            return {key: event[key] for key in _PARTS if key in event}
    return None


def sealed_runtime(events: Iterable[Mapping[str, Any]]) -> dict[str, Any] | None:
    """How the monitor said it ran when it sealed the log, or None if the log has no seal before the first call."""
    for event in events:
        if event.get("kind") == "call":
            return None
        if event.get("kind") == "integrity":
            return dict(event.get("runtime") or {})
    return None


def verify_log(quorum: Quorum, scenario: str = "") -> bool:
    """Whether the log is intact and was sealed by the policy, the tools and the code that are here now."""
    return (quorum.audit_log.verify()
            and sealed(quorum.audit_log) == fingerprint(quorum.policy, _tools_of(quorum), scenario)
            and sealed_runtime(quorum.audit_log) == runtime(quorum))


def current() -> dict[str, Any]:
    """What the lock should say for the code as it is now."""
    scenarios = {}
    for name in SCENARIOS:
        module = importlib.import_module(f"{__package__}.scenarios.{name}")
        scenarios[name] = fingerprint(module.POLICY, module.TOOLS, name)
    return {"kernel": kernel_digest(), "scenarios": scenarios}


def check(lock: Path = LOCK) -> list[str]:
    """Every difference between the lock and the code. An empty list means they agree."""
    try:
        pinned_values = json.loads(lock.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return [f"the lock cannot be read: {error}"]
    try:
        now = current()
    except InvalidConfiguration as error:       # a planted file: nothing under it can be vouched for
        return [f"kernel: {error}"]
    locked = pinned_values.get("scenarios") if isinstance(pinned_values, Mapping) else None
    if not isinstance(locked, Mapping) or not all(isinstance(hashes, Mapping) for hashes in locked.values()):
        return ["the lock cannot be read: it does not have the expected shape"]
    differences = []
    if pinned_values.get("kernel") != now["kernel"]:
        differences.append("kernel: the code of the trusted path changed")
    for name in sorted(set(locked) | set(now["scenarios"])):
        before, after = locked.get(name) or {}, now["scenarios"].get(name) or {}
        for part in _PARTS:
            if part != "kernel" and before.get(part) != after.get(part):
                differences.append(f"{name}: {part} changed")
        if before.get("kernel") != after.get("kernel") and pinned_values.get("kernel") == now["kernel"]:
            differences.append(f"{name}: kernel changed")       # the top entry agrees and this copy of it does not
    return differences


def pinned(scenario: str, lock: Path = LOCK) -> bool:
    """Whether the kernel and that scenario are exactly the ones the lock accepts."""
    name = f"{scenario}:"
    return not [d for d in check(lock) if d.startswith(("kernel:", "the lock", name))]


def locked_pipeline(scenario: str, lock: Path = LOCK) -> str:
    """The pipeline hash the lock accepts for that scenario, or '' if it has none."""
    try:
        value = json.loads(lock.read_text(encoding="utf-8"))["scenarios"][scenario]["pipeline"]
    except (OSError, ValueError, KeyError, TypeError):
        return ""
    return value if isinstance(value, str) else ""


def write(lock: Path = LOCK) -> None:
    lock.write_text(json.dumps(current(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m quorum.integrity", description=__doc__.split("\n\n")[0])
    parser.add_argument("--write", action="store_true", help="accept the current code: rewrite the lock")
    parser.add_argument("--show", action="store_true", help="print the current hashes")
    args = parser.parse_args(argv)
    if args.write:
        write()
        print(f"lock written to {LOCK.relative_to(ROOT.parent)}")
        return
    if args.show:
        print(json.dumps(current(), indent=2, sort_keys=True))
        return
    differences = check()
    if differences:
        print("the code is not the pinned one:", *differences, sep="\n  ", file=sys.stderr)
        sys.exit("run `python -m quorum.integrity --write` if the change is intended, and commit the lock with it")
    print(f"ok: the kernel and {len(SCENARIOS)} scenarios match the lock")


if __name__ == "__main__":
    main()
