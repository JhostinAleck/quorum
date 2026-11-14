"""Scenario: the back office of a retail bank handling a customer's payment instruction.

It exercises what the other scenarios do not: integrity (rule P2) on an action
sink. An untrusted message tells the agents to move money, and the gate asks for
a human approval the agents cannot give themselves. Not a line of the kernel changes.
"""
from .case import ATTACKER, KINDS, PAYEE, POLICY, REQUESTER, ROLES, VICTIM, Case, Episode, prepare, run
from .tools import TOOLS

__all__ = ["ATTACKER", "KINDS", "PAYEE", "POLICY", "REQUESTER", "ROLES", "TOOLS", "VICTIM",
           "Case", "Episode", "prepare", "run"]
