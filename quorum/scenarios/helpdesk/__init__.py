"""Scenario: a help desk that replies to citizens.

It exists to check that the core is domain-agnostic: it uses the same engine
and the same gate as the other scenario, without touching a line of the kernel.
"""
from .case import KINDS, POLICY, REQUESTER, ROLES, VICTIM, Case, Episode, prepare, run
from .tools import TOOLS

__all__ = ["KINDS", "POLICY", "REQUESTER", "ROLES", "TOOLS", "VICTIM",
           "Case", "Episode", "prepare", "run"]
