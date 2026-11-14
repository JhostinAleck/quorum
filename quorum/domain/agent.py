"""The agent as the monitor sees it.

Agent is the entity that carries the taint. Its invariant is the heart of the
defense: the context label only grows. Nothing an agent does, and nothing a
tool does on its behalf, can remove a source from it, change its role or
rename it.
"""
from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any

from .labels import PUBLIC, Label
from .policy import Role


class Agent:
    def __init__(self, principal: str, role: Role, context: Label = PUBLIC) -> None:
        self._principal = principal
        self._role = role
        self._context = context
        self._trajectory: list[dict[str, Any]] = []

    @property
    def principal(self) -> str:
        return self._principal

    @property
    def role(self) -> Role:
        return self._role

    @property
    def context(self) -> Label:
        """Label of everything the agent has read so far."""
        return self._context

    @property
    def trajectory(self) -> list[dict[str, Any]]:
        """What a monitor would see: tool, arguments and outcome of each step. No labels."""
        return list(self._trajectory)

    def absorb(self, label: Label) -> None:
        """Join a label into the context. There is no operation that shrinks it."""
        self._context = self._context.join(label)

    def record(self, tool: str, arguments: Mapping[str, Any], **outcome: Any) -> None:
        """Append a step to the trajectory."""
        self._trajectory.append({"tool": tool, "args": copy.deepcopy(dict(arguments)),
                                 **copy.deepcopy(outcome)})
