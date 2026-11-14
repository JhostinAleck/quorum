"""Policy: the only thing that changes from one domain to another.

A policy is four lists plus the roles:

  - restricted:    key prefixes whose data is born restricted
  - untrusted:     key prefixes whose data is written by third parties
  - sinks:         tools that take data out of the system, and which restricted
                   sources each one accepts
  - declassifiers: tools allowed to return a public result computed over
                   restricted data

The gate's decision is a pure function of (request, policy).
"""
from __future__ import annotations

import string
import tomllib
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .errors import InvalidConfiguration, is_id
from .labels import Label


@dataclass(frozen=True)
class Role:
    name: str
    tools: tuple[str, ...] = ()
    reads: tuple[str, ...] = ()      # prefixes it may read with the generic tool
    writes: tuple[str, ...] = ()     # prefixes it may write with the generic tool

    def can_read(self, key: str) -> bool:
        return key.startswith(self.reads)

    def can_write(self, key: str) -> bool:
        return key.startswith(self.writes)


@dataclass(frozen=True)
class Policy:
    restricted: tuple[str, ...] = ()
    untrusted: tuple[str, ...] = ()
    sinks: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    declassifiers: frozenset[str] = frozenset()
    endorsements: frozenset[str] = frozenset()      # sources the user allowed to leave
    quotas: Mapping[str, int] = field(default_factory=dict)   # maximum calls per agent
    strict_mode: bool = False                # turns rule P2 on
    roles: Mapping[str, Role] = field(default_factory=dict)

    def __post_init__(self) -> None:
        assign = lambda name, value: object.__setattr__(self, name, value)  # noqa: E731
        assign("restricted", tuple(self.restricted))
        assign("untrusted", tuple(self.untrusted))
        assign("sinks", MappingProxyType({k: tuple(v) for k, v in self.sinks.items()}))
        assign("declassifiers", frozenset(self.declassifiers))
        assign("endorsements", frozenset(self.endorsements))
        assign("quotas", MappingProxyType(dict(self.quotas)))
        assign("roles", MappingProxyType(dict(self.roles)))
        for tool, quota in self.quotas.items():
            if isinstance(quota, bool) or not isinstance(quota, int) or quota < 0:
                raise InvalidConfiguration(f"invalid quota for {tool!r}: {quota!r}")

    def base_label(self, key: str) -> Label:
        """The label any value stored under that key is born with."""
        return Label(
            frozenset({key}) if key.startswith(self.restricted) else frozenset(),
            frozenset({key}) if key.startswith(self.untrusted) else frozenset(),
        )

    def evolve(self, **changes: Any) -> Policy:
        return replace(self, **changes)

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> Policy:
        allowed_fields = {"restricted", "untrusted", "sinks", "declassifiers",
                          "endorsements", "quotas", "strict_mode", "roles"}
        unknown = set(d) - allowed_fields
        if unknown:  # a typo must not silently weaken the policy
            raise InvalidConfiguration(f"unknown fields in the policy: {sorted(unknown)}")
        roles = {}
        for name, r in d.get("roles", {}).items():
            extra = set(r) - {"tools", "reads", "writes"}
            if extra:
                raise InvalidConfiguration(f"unknown fields in role {name!r}: {sorted(extra)}")
            roles[name] = Role(name, tuple(r.get("tools", ())),
                               tuple(r.get("reads", ())), tuple(r.get("writes", ())))
        return cls(
            restricted=tuple(d.get("restricted", ())),
            untrusted=tuple(d.get("untrusted", ())),
            sinks=d.get("sinks", {}),
            declassifiers=frozenset(d.get("declassifiers", ())),
            endorsements=frozenset(d.get("endorsements", ())),
            quotas=d.get("quotas", {}),
            strict_mode=bool(d.get("strict_mode", False)),
            roles=roles,
        )

    @classmethod
    def from_toml(cls, path: str | Path) -> Policy:
        with open(path, "rb") as f:
            return cls.from_dict(tomllib.load(f))


# --- The gate's decision ------------------------------------------------------

@dataclass(frozen=True)
class Request:
    """A call to a sink, as the gate sees it."""
    principal: str
    role: str
    tool: str
    arguments: Mapping[str, Any]
    label: Label                # the caller's context
    approved: bool = False      # human approval obtained outside the agents


@dataclass(frozen=True)
class Decision:
    allow: bool
    policy: str | None = None
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"allow": self.allow, "policy": self.policy, "reason": self.reason}


ALLOW = Decision(True)
Rule = Callable[[Request, Policy], "Decision | None"]


def _instantiate(template: str, arguments: Mapping[str, Any]) -> str | None:
    """Fill a template such as 'client.{client}.' with the arguments.

    Only simple identifiers are accepted as values, so an agent cannot widen
    the authorized prefix with an empty value or with separators. The template
    must end with the separator, so it does not authorize by accident sources
    that merely start the same way ('client.1' and 'client.10').
    """
    values = {}
    for _, field_name, _, _ in string.Formatter().parse(template):
        if field_name is None:
            continue
        value = arguments.get(field_name)
        if not field_name.isidentifier() or isinstance(value, bool):
            return None
        if isinstance(value, int):
            value = str(value)
        if not is_id(value):
            return None
        values[field_name] = value
    return template.format(**values)


def authorized(request: Request, policy: Policy) -> tuple[str, ...]:
    """Prefixes of restricted sources this sink accepts in this call."""
    templates = policy.sinks.get(request.tool, ())
    prefixes = (_instantiate(p, request.arguments) for p in templates)
    return tuple(p for p in prefixes if p is not None)


def p1_confidentiality(s: Request, policy: Policy) -> Decision | None:
    """Nothing restricted leaves through a sink that is not authorized to receive it."""
    allowed = authorized(s, policy)
    unauthorized = sorted(f for f in s.label.secrets
                          if f not in policy.endorsements and not f.startswith(allowed))
    if unauthorized:
        return Decision(False, "P1", "restricted sources not authorized for this destination: "
                        + ", ".join(unauthorized))
    return None


def p2_integrity(s: Request, policy: Policy) -> Decision | None:
    """Strict mode: an untrusted context needs human approval to leave."""
    if policy.strict_mode and s.label.untrusted and not s.approved:
        return Decision(False, "P2", "untrusted context without human approval: "
                        + ", ".join(sorted(s.label.untrusted)))
    return None


BASE_RULES: tuple[Rule, ...] = (p1_confidentiality, p2_integrity)


def evaluate(request: Request, policy: Policy,
             rules: tuple[Rule, ...] = BASE_RULES) -> Decision:
    """Apply the rules in order. The first one that denies wins.

    If a rule raises, the answer is to deny.
    """
    for rule in rules:
        try:
            decision = rule(request, policy)
        except Exception as error:
            return Decision(False, "ERROR", f"rule {getattr(rule, '__name__', rule)!r} failed: {error}")
        if decision is not None and not decision.allow:
            return decision
    return ALLOW
