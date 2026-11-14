"""A minimal, abstract scenario to test the core without any domain."""
from quorum.core import BASE_TOOLS, Kind, Policy, Quorum, ToolError, tool

POLICY = Policy.from_dict({
    "restricted": ["secret."],
    "untrusted": ["external."],
    "sinks": {"emit": []},
    "declassifiers": ["length", "fail"],
    "roles": {
        "agent": {"tools": ["read", "write", "send_message", "read_messages", "reveal",
                            "read_external", "length", "fail", "emit"],
                  "reads": ["board."], "writes": ["board."]},
        "reader": {"tools": ["read"], "reads": ["board."]},
    },
})


@tool(description="Reveals a secret.", params={"i": "Secret number."})
def reveal(call, i: int) -> str:
    return call.read(f"secret.{i}")


@tool(description="Reads an external text.", params={"i": "Text number."})
def read_external(call, i: int) -> str:
    return call.read(f"external.{i}")


@tool(kind=Kind.DECLASSIFIER, description="Length of a secret.",
      params={"i": "Secret number."}, rationale="Only reveals the length.")
def length(call, i: int) -> int:
    return len(call.read(f"secret.{i}"))


@tool(kind=Kind.DECLASSIFIER, description="Reads a secret and fails.",
      params={"i": "Secret number."}, rationale="Exercises the error path.")
def fail(call, i: int) -> int:
    raise ToolError(f"could not process {call.read(f'secret.{i}')}")


@tool(kind=Kind.SINK, description="Sends a text out of the system.", params={"text": "Text."})
def emit(call, text: str) -> str:
    return "emitted"


TOOLS = (*BASE_TOOLS, reveal, read_external, length, fail, emit)
SECRETS = ("ALFA-7731", "BETA-4402", "GAMA-9958")


def new(*, enforce=True, policy=None, store=None, secrets=SECRETS, **options) -> Quorum:
    q = Quorum(policy or POLICY, TOOLS, enforce=enforce, store=store, **options)
    for i, secret in enumerate(secrets):
        q.ingest(f"secret.{i}", secret)
        q.ingest(f"external.{i}", f"external text {i}")
    return q
