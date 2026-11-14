"""The core must not depend on any domain or any agent framework."""
import ast
import sys
from pathlib import Path

import quorum.core

CORE_FILES = sorted(Path(quorum.core.__file__).parent.glob("*.py"))
DOMAIN_WORDS = ("tender", "licitaci", "supplier", "proveedor", "citizen", "ciudadano", "ticket", "helpdesk",
                "sealed", "inspect_ai", "openai")


def test_the_core_only_imports_the_standard_library_and_itself():
    assert len(CORE_FILES) >= 8
    for path in CORE_FILES:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom):
                assert node.level <= 1, f"{path.name} imports from outside the core"
                if node.level == 0:
                    assert node.module.split(".")[0] in sys.stdlib_module_names, f"{path.name}: {node.module}"
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] in sys.stdlib_module_names, f"{path.name}: {alias.name}"


def test_the_core_does_not_mention_any_domain():
    for path in CORE_FILES:
        text = path.read_text(encoding="utf-8").lower()
        for word in DOMAIN_WORDS:
            assert word not in text, f"{path.name} mentions {word!r}"


def test_scenarios_do_not_know_each_other():
    scenarios = Path(quorum.core.__file__).parent.parent / "scenarios"
    for folder in (c for c in scenarios.iterdir() if c.is_dir() and not c.name.startswith("_")):
        others = [c.name for c in scenarios.iterdir() if c.is_dir() and c.name not in (folder.name, "__pycache__")]
        for path in folder.glob("*.py"):
            text = path.read_text(encoding="utf-8")
            assert not any(other in text for other in others), f"{path} mentions another scenario"
