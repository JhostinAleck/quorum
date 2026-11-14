"""Ports of the domain: what it needs from the outside world.

Store is the repository of labelled values. The domain and the application
only know this protocol. Concrete backends live in the infrastructure layer.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from .labels import PUBLIC, Label


@dataclass(frozen=True)
class Value:
    """A piece of data together with the label that says where it came from."""
    data: Any
    label: Label = PUBLIC


@runtime_checkable
class Store(Protocol):
    def get(self, key: str) -> Value | None: ...
    def put(self, key: str, value: Value) -> None: ...
    def keys(self, prefix: str = "") -> list[str]: ...
