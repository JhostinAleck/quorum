"""Policies stored as TOML files."""
from __future__ import annotations

import tomllib
from pathlib import Path

from ..domain.policy import Policy


def load_policy(path: str | Path) -> Policy:
    """Read a policy from a TOML file. Validation happens in Policy.from_dict."""
    with open(path, "rb") as f:
        return Policy.from_dict(tomllib.load(f))
