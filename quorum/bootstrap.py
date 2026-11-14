"""Composition root: the one place that wires the layers together."""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .application.monitor import Quorum
from .domain.policy import Policy
from .domain.repositories import Store
from .domain.tools import Tool
from .infrastructure.stores import MemoryStore


def new_monitor(policy: Policy, tools: Iterable[Tool], *, store: Store | None = None, **options: Any) -> Quorum:
    """Build a monitor. Without a store it uses an in-memory one.

    options are passed to Quorum: enforce, rules and approver.
    """
    return Quorum(policy, tools, store if store is not None else MemoryStore(), **options)
