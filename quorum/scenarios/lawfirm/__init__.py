"""Scenario: a law firm's litigation team preparing a court filing.

Two exits with different authorizations: the report to the client may carry
that client's own privileged file, the court filing may carry none.
It is a policy file, eight tools and scripted episodes. The kernel is untouched.
"""
from .case import (
    CLIENT,
    DOCUMENT,
    INJECTION,
    INJECTION_MARK,
    KINDS,
    MATTER,
    POLICY,
    ROLES,
    VICTIM,
    Case,
    Episode,
    play,
    prepare,
    run,
)
from .tools import TOOLS

__all__ = ["CLIENT", "DOCUMENT", "INJECTION", "INJECTION_MARK", "KINDS", "MATTER", "POLICY", "ROLES", "TOOLS",
           "VICTIM", "Case", "Episode", "play", "prepare", "run"]
