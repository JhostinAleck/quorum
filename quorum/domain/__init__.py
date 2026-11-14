"""Domain layer: the model of the defense.

Value objects (Label, Policy, Role, Request, Decision, Value), the Agent
entity, the gate (a domain service) and the audit log. Pure Python: no I/O, no
framework, no knowledge of any scenario. Its only door to the outside is the
Store port in repositories.py.
"""
from .agent import Agent
from .audit_log import AuditLog
from .errors import (
    InvalidArguments,
    InvalidConfiguration,
    PermissionDenied,
    QuorumError,
    QuotaExceeded,
    ToolError,
    UnknownTool,
    is_id,
    require_id,
)
from .gate import (
    ALLOW,
    BASE_RULES,
    Blocked,
    Decision,
    Emission,
    Request,
    Rule,
    authorized,
    evaluate,
    p1_confidentiality,
    p2_integrity,
)
from .labels import PUBLIC, Conf, Integ, Label, restricted, untrusted
from .policy import Policy, Role
from .repositories import Store, Value
from .tools import Kind, Tool, tool

__all__ = [
    "ALLOW", "BASE_RULES", "PUBLIC",
    "Agent", "AuditLog", "Blocked", "Conf", "Decision", "Emission", "Integ", "InvalidArguments",
    "InvalidConfiguration", "Kind", "Label", "PermissionDenied", "Policy", "QuorumError", "QuotaExceeded",
    "Request", "Role", "Rule", "Store", "Tool", "ToolError", "UnknownTool", "Value",
    "authorized", "evaluate", "is_id", "p1_confidentiality", "p2_integrity", "require_id", "restricted",
    "tool", "untrusted",
]
