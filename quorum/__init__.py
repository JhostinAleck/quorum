"""Quorum: a deterministic provenance gate for multi-agent systems.

The package follows a layered, domain-driven layout:

  quorum.domain          the model: labels, policy, gate, agent, audit log, ports
  quorum.application     the reference monitor (the use case) and generic tools
  quorum.infrastructure  stores and policy files
  quorum.adapters        bridges to agent frameworks
  quorum.scenarios       bounded contexts that use the kernel (tender, helpdesk)

Dependencies point inwards: adapters, scenarios and infrastructure know the
domain; the domain knows nobody. Everything below is the public API.
"""
from .application import BASE_TOOLS, Call, Quorum, Session, read, read_messages, send_message, write
from .bootstrap import new_monitor
from .domain import (
    ALLOW,
    BASE_RULES,
    PUBLIC,
    Agent,
    AuditLog,
    Blocked,
    Conf,
    Decision,
    Emission,
    Integ,
    InvalidArguments,
    InvalidConfiguration,
    Kind,
    Label,
    PermissionDenied,
    Policy,
    QuorumError,
    QuotaExceeded,
    Request,
    Role,
    Rule,
    Store,
    Tool,
    ToolError,
    UnknownTool,
    Value,
    authorized,
    evaluate,
    is_id,
    p1_confidentiality,
    p2_integrity,
    require_id,
    restricted,
    tool,
    untrusted,
)
from .infrastructure import MemoryStore, SQLiteStore, load_policy

__all__ = [
    "ALLOW", "BASE_RULES", "BASE_TOOLS", "PUBLIC",
    "Agent", "AuditLog", "Blocked", "Call", "Conf", "Decision", "Emission", "Integ", "InvalidArguments",
    "InvalidConfiguration", "Kind", "Label", "MemoryStore", "PermissionDenied", "Policy", "Quorum",
    "QuorumError", "QuotaExceeded", "Request", "Role", "Rule", "SQLiteStore", "Session", "Store",
    "Tool", "ToolError", "UnknownTool", "Value",
    "authorized", "evaluate", "is_id", "load_policy", "new_monitor", "p1_confidentiality", "p2_integrity",
    "read", "read_messages", "require_id", "restricted", "send_message", "tool", "untrusted", "write",
]
