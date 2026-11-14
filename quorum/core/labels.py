"""Provenance labels.

A label records which restricted sources (confidentiality) and which
untrusted sources (integrity) a value was derived from. Labels form a
lattice: the product of two sets ordered by inclusion.

  - join is set union: associative, commutative and idempotent.
  - PUBLIC is the bottom element.
  - a.flows_to(b) is the partial order: b is at least as restrictive as a.

This module knows no domain. Sources are opaque identifiers.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import IntEnum


class Conf(IntEnum):
    PUBLIC = 0
    RESTRICTED = 1


class Integ(IntEnum):
    UNTRUSTED = 0
    TRUSTED = 1


@dataclass(frozen=True, slots=True)
class Label:
    secrets: frozenset[str] = frozenset()      # restricted sources
    untrusted: frozenset[str] = frozenset()    # sources written by third parties

    def __post_init__(self) -> None:
        object.__setattr__(self, "secrets", frozenset(self.secrets))
        object.__setattr__(self, "untrusted", frozenset(self.untrusted))

    @property
    def conf(self) -> Conf:
        return Conf.RESTRICTED if self.secrets else Conf.PUBLIC

    @property
    def integ(self) -> Integ:
        return Integ.UNTRUSTED if self.untrusted else Integ.TRUSTED

    @property
    def sources(self) -> frozenset[str]:
        return self.secrets | self.untrusted

    def join(self, *others: Label) -> Label:
        secrets, untrusted = self.secrets, self.untrusted
        for other in others:
            secrets |= other.secrets
            untrusted |= other.untrusted
        return Label(secrets, untrusted)

    __or__ = join

    def flows_to(self, other: Label) -> bool:
        """True if a value with this label may go somewhere with the other one."""
        return self.secrets <= other.secrets and self.untrusted <= other.untrusted

    def to_dict(self) -> dict[str, list[str]]:
        return {"secrets": sorted(self.secrets), "untrusted": sorted(self.untrusted)}

    @classmethod
    def from_dict(cls, d: Mapping[str, Iterable[str]]) -> Label:
        return cls(frozenset(d.get("secrets", ())), frozenset(d.get("untrusted", ())))


PUBLIC = Label()


def restricted(*sources: str) -> Label:
    return Label(secrets=frozenset(sources))


def untrusted(*sources: str) -> Label:
    return Label(untrusted=frozenset(sources))
