"""Core errors. They all inherit from QuorumError."""
from __future__ import annotations

import re

_ID = re.compile(r"[A-Za-z0-9_-]+")


class QuorumError(Exception):
    """Base class of every Quorum error."""


class InvalidConfiguration(QuorumError, ValueError):
    """The policy, the roles or the tools are not consistent with each other."""


class UnknownTool(QuorumError, LookupError):
    """A tool that is not registered was requested."""


class InvalidArguments(QuorumError, TypeError):
    """The arguments do not match the tool's signature."""


class PermissionDenied(QuorumError, PermissionError):
    """The agent's role does not allow that call or that key."""


class QuotaExceeded(PermissionDenied):
    """The number of calls allowed for a tool was exceeded."""


class ToolError(QuorumError):
    """The tool rejected the call for a domain reason."""


def is_id(text: object) -> bool:
    """A simple identifier: letters, digits, hyphen and underscore."""
    return isinstance(text, str) and _ID.fullmatch(text) is not None


def require_id(text: object, what: str = "identifier") -> str:
    if not is_id(text):
        raise ToolError(f"invalid {what}: {text!r}")
    return text  # type: ignore[return-value]
