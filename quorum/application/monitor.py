"""The Quorum reference monitor.

Every call an agent makes to a tool goes through here. The monitor:

  1. checks that the agent's role has that tool and that quota remains,
  2. validates the arguments,
  3. if the tool is a sink, asks the gate,
  4. runs the tool, giving it access to the store only through a Call, which
     records the label of everything that is read,
  5. joins those labels into the agent's context (except for a declassifier),
  6. appends the event to the audit log.

Tools cannot forget to propagate a label, because they never touch the store
directly. This is the application layer: it orchestrates the domain (labels,
policy, gate, agent) and talks to the outside only through the Store port.
"""
from __future__ import annotations

import copy
import threading
from collections.abc import Callable, Iterable, Mapping
from dataclasses import replace
from functools import partial
from typing import Any

from ..domain.agent import Agent
from ..domain.audit_log import AuditLog
from ..domain.errors import (
    InvalidArguments,
    InvalidConfiguration,
    PermissionDenied,
    QuorumError,
    QuotaExceeded,
    UnknownTool,
    is_id,
)
from ..domain.gate import BASE_RULES, Blocked, Decision, Emission, Request, Rule, evaluate
from ..domain.labels import PUBLIC, Label
from ..domain.policy import Policy, Role
from ..domain.repositories import Store, Value
from ..domain.tools import Kind, Tool

_ACCESS_CONTROL = {"ROLE", "QUOTA", "ARGUMENTS"}   # denials that do not come from the gate


class Call:
    """What a tool can do while it runs.

    It is the only door to the store. Every read accumulates its label in
    `seen`, and every write is stored with the label of the agent's context,
    plus what was read in this call, plus the one the policy assigns to the key.
    """

    def __init__(self, quorum: Quorum, session: Session) -> None:
        self._quorum, self._session = quorum, session
        self._base = session.context
        self.seen = PUBLIC

    @property
    def principal(self) -> str:
        return self._session.principal

    @property
    def role(self) -> Role:
        return self._session.role

    def read(self, key: str) -> Any:
        value = self._quorum.store.get(key)
        if value is None:
            return None
        self.seen = self.seen.join(value.label)
        return value.data

    def exists(self, key: str) -> bool:
        return self._quorum.store.get(key) is not None

    def write(self, key: str, data: Any) -> None:
        label = self._base.join(self.seen, self._quorum.policy.base_label(key))
        self._quorum.store.put(key, Value(data, label))

    def keys(self, prefix: str) -> list[str]:
        return self._quorum.store.keys(prefix)

    def require_read(self, key: str) -> None:
        if not self.role.can_read(key):
            raise PermissionDenied(f"role {self.role.name!r} cannot read {key!r}")

    def require_write(self, key: str) -> None:
        if not self.role.can_write(key):
            raise PermissionDenied(f"role {self.role.name!r} cannot write {key!r}")


class Session(Agent):
    """An agent's handle on the monitor. Every call it makes goes through here."""

    def __init__(self, quorum: Quorum, principal: str, role: Role, context: Label) -> None:
        super().__init__(principal, role, context)
        self._quorum = quorum

    def call(self, name: str, /, *args: Any, **kwargs: Any) -> Any:
        """Call a tool. Returns its result, or a Blocked if the gate stopped it.
        Raises QuorumError if the call is not valid."""
        return self._quorum._call(self, name, args, kwargs)

    def __getattr__(self, name: str) -> Any:
        # sugar: session.publish("x") is session.call("publish", "x")
        quorum = self.__dict__.get("_quorum")
        if quorum is not None and not name.startswith("_") and name in quorum._tools:
            return partial(self.call, name)
        raise AttributeError(name)

    def tools(self) -> list[Tool]:
        """The tools of its role, in the order declared in the policy."""
        return [self._quorum.tool(name) for name in self.role.tools]

    def spawn(self, principal: str, role: str | None = None) -> Session:
        """Create a subagent. It inherits the label: delegating does not clean the context."""
        return self._quorum.session(principal, role, inherits=self.context)


class Quorum:
    def __init__(self, policy: Policy, tools: Iterable[Tool], store: Store, *,
                 enforce: bool = True,
                 rules: tuple[Rule, ...] = BASE_RULES,
                 approver: Callable[[Request], bool] | None = None) -> None:
        """
        enforce=True   the gate blocks.
        enforce=False  audit only: nothing is blocked, but the decision is
                       written to the audit log. Lets you measure without
                       altering the episode.
        approver       trusted function, outside the agents, that stands for
                       the human approval required by rule P2.
        """
        self.policy = policy
        self.store = store
        self.enforce = enforce
        self.audit_log = AuditLog()
        self.emissions: list[Emission] = []
        self._rules, self._approver = tuple(rules), approver
        self._tools: dict[str, Tool] = {}
        for tool in tools:
            if tool.name in self._tools:
                raise InvalidConfiguration(f"duplicate tool: {tool.name!r}")
            self._tools[tool.name] = tool
        self._sessions: dict[str, Session] = {}
        self._uses: dict[tuple[str, str], int] = {}
        self._lock = threading.RLock()
        self._validate()

    def _validate(self) -> None:
        """Fail at start-up if the policy and the tools do not match."""
        def of_kind(kind: Kind) -> set[str]:
            return {name for name, tool in self._tools.items() if tool.kind is kind}
        for what, declared, actual in (
                ("sinks", set(self.policy.sinks), of_kind(Kind.SINK)),
                ("declassifiers", set(self.policy.declassifiers), of_kind(Kind.DECLASSIFIER))):
            if declared != actual:
                raise InvalidConfiguration(
                    f"the policy declares {what} {sorted(declared)} but the tools "
                    f"of that kind are {sorted(actual)}")
        for role in self.policy.roles.values():
            missing = set(role.tools) - set(self._tools)
            if missing:
                raise InvalidConfiguration(f"role {role.name!r} uses tools that do not exist: {sorted(missing)}")
        missing = set(self.policy.quotas) - set(self._tools)
        if missing:
            raise InvalidConfiguration(f"there are quotas for tools that do not exist: {sorted(missing)}")

    # --- set-up (done by the system, not by the agents) -----------------------

    def ingest(self, key: str, data: Any) -> None:
        """Trusted ingestion of a value. The policy assigns the label from the key."""
        with self._lock:
            label = self.policy.base_label(key)
            self.store.put(key, Value(data, label))
            self.audit_log.record(kind="ingest", key=key, label=label.to_dict())

    def session(self, principal: str, role: str | None = None, *, inherits: Label = PUBLIC) -> Session:
        """Open an agent's session. Without a role, the role named like the agent is used."""
        with self._lock:
            if not is_id(principal):
                raise InvalidConfiguration(f"invalid agent name: {principal!r}")
            if principal in self._sessions:
                raise InvalidConfiguration(f"a session for {principal!r} already exists")
            if (role or principal) not in self.policy.roles:
                raise InvalidConfiguration(f"unknown role: {(role or principal)!r}")
            session = Session(self, principal, self.policy.roles[role or principal], inherits)
            self._sessions[principal] = session
            self.audit_log.record(kind="session", principal=principal, role=session.role.name,
                                  label=inherits.to_dict())
            return session

    # --- queries --------------------------------------------------------------

    def tool(self, name: str) -> Tool:
        try:
            return self._tools[name]
        except KeyError:
            raise UnknownTool(f"unknown tool: {name!r}") from None

    @property
    def sessions(self) -> Mapping[str, Session]:
        return dict(self._sessions)

    def emitted(self, sink: str | None = None) -> list[Emission]:
        """What left the system, optionally filtered by sink."""
        return [s for s in self.emissions if sink is None or s.sink == sink]

    def blocks(self) -> list[dict[str, Any]]:
        """Sink calls the gate rejected, whether or not the rejection was enforced."""
        return [e for e in self.audit_log
                if e.get("tool_kind") == Kind.SINK.value and e.get("decision")
                and not e["decision"]["allow"] and e["decision"]["policy"] not in _ACCESS_CONTROL]

    # --- the path of every call -----------------------------------------------

    def _call(self, session: Session, name: str, args: tuple[Any, ...], kwargs: Mapping[str, Any]) -> Any:
        with self._lock:
            tool = self.tool(name)
            before = session.context

            def deny(code: str, reason: str, error: type[QuorumError]) -> None:
                # failed attempts are also visible to the monitors
                self._log(session, tool, kwargs, before, Decision(False, code, reason), executed=False)
                session.record(name, kwargs, error=reason)
                raise error(reason)

            if name not in session.role.tools:
                deny("ROLE", f"role {session.role.name!r} does not have the tool {name!r}", PermissionDenied)
            try:
                arguments = tool.bind(args, kwargs)
            except InvalidArguments as error:
                deny("ARGUMENTS", str(error), InvalidArguments)
            quota, usage = self.policy.quotas.get(name), (session.principal, name)
            if quota is not None and self._uses.get(usage, 0) >= quota:
                deny("QUOTA", f"{session.principal!r} used up its quota of {quota} calls to {name!r}", QuotaExceeded)
            self._uses[usage] = self._uses.get(usage, 0) + 1

            decision = None
            if tool.kind is Kind.SINK:
                decision = self._decide(session, tool, arguments)
                if not decision.allow and self.enforce:
                    blocked = Blocked(name, decision.policy or "?", decision.reason)
                    self._log(session, tool, arguments, before, decision, executed=False)
                    session.record(name, arguments, result=str(blocked))
                    return blocked

            call = Call(self, session)
            try:
                result = tool.fn(call, **arguments)
            except Exception as error:
                # on failure nothing is declassified: what was read taints the context
                session.absorb(call.seen)
                text = f"{type(error).__name__}: {error}"
                self._log(session, tool, arguments, before, decision, executed=False, error=text)
                session.record(name, arguments, error=text)
                raise
            if tool.kind is not Kind.DECLASSIFIER:
                session.absorb(call.seen)
            if tool.kind is Kind.SINK:
                self.emissions.append(Emission(name, session.principal, copy.deepcopy(arguments)))
            self._log(session, tool, arguments, before, decision, executed=True)
            session.record(name, arguments, result=result)
            return result

    def _decide(self, session: Session, tool: Tool, arguments: Mapping[str, Any]) -> Decision:
        request = Request(session.principal, session.role.name, tool.name, arguments, session.context)
        if self.policy.strict_mode and session.context.untrusted and self._approver is not None:
            try:
                approved = bool(self._approver(request))
            except Exception:
                approved = False
            request = replace(request, approved=approved)
        return evaluate(request, self.policy, self._rules)

    def _log(self, session: Session, tool: Tool, arguments: Mapping[str, Any], before: Label,
             decision: Decision | None, *, executed: bool, error: str | None = None) -> None:
        self.audit_log.record(
            kind="call", principal=session.principal, role=session.role.name,
            tool=tool.name, tool_kind=tool.kind.value, args=dict(arguments),
            label_before=before.to_dict(), label_after=session.context.to_dict(),
            decision=None if decision is None else decision.to_dict(),
            executed=executed, error=error)
