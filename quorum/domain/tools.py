"""Tools: functions agents can call through the monitor.

A tool declares its kind:

  - NORMAL:       what it reads taints the caller's context.
  - SINK:         takes data out of the system. Goes through the gate.
  - DECLASSIFIER: its result is public even though it reads restricted data.
                  It must be listed in the policy and state its rationale.

The JSON schema any agent framework needs to offer the tool to a model is
derived from the function signature.
"""
from __future__ import annotations

import inspect
import types
from collections.abc import Callable, Mapping
from collections.abc import Mapping as MappingABC
from collections.abc import Sequence as SequenceABC
from enum import Enum
from typing import Any, Union, get_args, get_origin, get_type_hints

from .errors import InvalidArguments, InvalidConfiguration, is_id


class Kind(Enum):
    NORMAL = "normal"
    SINK = "sink"
    DECLASSIFIER = "declassifier"


_JSON = {str: "string", int: "integer", float: "number", bool: "boolean"}
_LISTS = (list, tuple, set, frozenset, SequenceABC)
_DICTS = (dict, MappingABC)


def _schema_of(annotation: Any) -> dict[str, Any]:
    if annotation in _JSON:
        return {"type": _JSON[annotation]}
    origin, args = get_origin(annotation), get_args(annotation)
    if annotation in _LISTS or origin in _LISTS:
        return {"type": "array", "items": _schema_of(args[0]) if args else {}}
    if annotation in _DICTS or origin in _DICTS:
        return {"type": "object", "additionalProperties": _schema_of(args[1]) if len(args) == 2 else {}}
    if origin in (Union, types.UnionType):
        options = [a for a in args if a is not type(None)]
        return _schema_of(options[0]) if len(options) == 1 else {"anyOf": [_schema_of(a) for a in options]}
    return {}


def _matches(value: Any, annotation: Any) -> bool:
    if annotation is bool:
        return isinstance(value, bool)
    if annotation is int:
        return isinstance(value, int) and not isinstance(value, bool)
    if annotation is float:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if annotation is str:
        return isinstance(value, str)
    origin, args = get_origin(annotation), get_args(annotation)
    if annotation in _LISTS or origin in _LISTS:
        return isinstance(value, (list, tuple)) and all(_matches(v, args[0]) for v in value if args)
    if annotation in _DICTS or origin in _DICTS:
        return (isinstance(value, MappingABC) and all(isinstance(k, str) for k in value)
                and all(_matches(v, args[1]) for v in value.values() if len(args) == 2))
    if origin in (Union, types.UnionType):
        return any(value is None if a is type(None) else _matches(value, a) for a in args)
    return True


class Tool:
    def __init__(self, name: str, fn: Callable[..., Any], description: str,
                 params: Mapping[str, str], kind: Kind = Kind.NORMAL, rationale: str = "") -> None:
        if not is_id(name):
            raise InvalidConfiguration(f"invalid tool name: {name!r}")
        if not description.strip():
            raise InvalidConfiguration(f"{name}: missing description")
        if kind is Kind.DECLASSIFIER and not rationale.strip():
            raise InvalidConfiguration(f"{name}: a declassifier must state why its result is public")
        signature = inspect.signature(fn)
        if not signature.parameters:
            raise InvalidConfiguration(f"{name}: the first parameter must be the call")
        own = list(signature.parameters.values())[1:]   # the first one is the Call
        for p in own:
            if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
                raise InvalidConfiguration(f"{name}: *args and **kwargs are not supported")
        if {p.name for p in own} != set(params):
            raise InvalidConfiguration(f"{name}: every parameter needs a description, no more and no fewer")
        self.name, self.fn, self.description = name, fn, description.strip()
        self.params, self.kind, self.rationale = dict(params), kind, rationale.strip()
        self.signature = signature.replace(parameters=own)
        try:
            hints = get_type_hints(fn)
        except Exception as error:
            raise InvalidConfiguration(f"{name}: could not resolve the type annotations: {error}") from None
        self._types = {p.name: hints.get(p.name, Any) for p in own}

    def bind(self, args: tuple[Any, ...], kwargs: Mapping[str, Any]) -> dict[str, Any]:
        """Validate the arguments against the signature and return them by name."""
        try:
            bound = self.signature.bind(*args, **kwargs)
        except TypeError as error:
            raise InvalidArguments(f"{self.name}: {error}") from None
        bound.apply_defaults()
        for name, value in bound.arguments.items():
            if not _matches(value, self._types[name]):
                raise InvalidArguments(
                    f"{self.name}: argument {name!r} is not of the expected type "
                    f"({getattr(self._types[name], '__name__', self._types[name])})")
        return dict(bound.arguments)

    def schema(self) -> dict[str, Any]:
        """JSON Schema of the parameters, ready for function calling."""
        properties, required = {}, []
        for p in self.signature.parameters.values():
            properties[p.name] = {**_schema_of(self._types[p.name]), "description": self.params[p.name]}
            if p.default is p.empty:
                required.append(p.name)
        return {"type": "object", "properties": properties, "required": required,
                "additionalProperties": False}

    def __repr__(self) -> str:
        return f"Tool({self.name!r}, {self.kind.value})"

    def localized(self, description: str, params: Mapping[str, str]) -> Tool:
        """The same tool with its model-facing texts in another language."""
        return Tool(self.name, self.fn, description, params, self.kind, self.rationale)


def tool(*, description: str, params: Mapping[str, str] | None = None,
         kind: Kind = Kind.NORMAL, rationale: str = "",
         name: str | None = None) -> Callable[[Callable[..., Any]], Tool]:
    """Decorator that turns a function fn(call, ...) into a Tool."""
    def decorate(fn: Callable[..., Any]) -> Tool:
        return Tool(name or fn.__name__, fn, description, params or {}, kind, rationale)
    return decorate
