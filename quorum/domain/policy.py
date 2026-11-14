"""Policy: the only thing that changes from one domain to another.

A policy is four lists plus the roles:

  - restricted:    key prefixes whose data is born restricted
  - untrusted:     key prefixes whose data is written by third parties
  - sinks:         tools that take data out of the system, and which restricted
                   sources each one accepts
  - declassifiers: tools allowed to return a public result computed over
                   restricted data

Two switches make the gate stricter: strict_mode (rule P2) and
high_water_mark, which closes the channels that labels on values do not see.

A policy is a value object: immutable, validated when it is built, and with
no I/O. Loading it from a file is the job of the infrastructure layer.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import Any

from .errors import InvalidConfiguration
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
    high_water_mark: bool = False            # a sink is judged with the secrets any agent has seen
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
                          "endorsements", "quotas", "strict_mode", "high_water_mark", "roles"}
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
            high_water_mark=bool(d.get("high_water_mark", False)),
            roles=roles,
        )
