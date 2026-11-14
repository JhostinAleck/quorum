"""The gate: the domain service that decides whether a sink call may go out.

The decision is a pure function of (request, policy). It reads no prose, calls
no model and keeps no state, so the same request always gets the same answer.
"""
from __future__ import annotations

import string
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from .errors import is_id
from .labels import Label
from .policy import Policy


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


# --- Outcomes of a sink call ---------------------------------------------------

@dataclass(frozen=True)
class Blocked:
    """What a sink call returns when the gate did not let it run."""
    tool: str
    policy: str
    reason: str

    def __str__(self) -> str:
        return f"BLOCKED by policy {self.policy}: {self.reason}"


@dataclass(frozen=True)
class Emission:
    """Something that left the system through a sink."""
    sink: str
    principal: str
    arguments: Mapping[str, Any]
