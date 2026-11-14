"""The dependency rule of the layered, domain-driven layout.

    domain          imports only the standard library and itself
    application     imports the domain
    infrastructure  imports the domain
    adapters        import the application and the domain (plus their framework)
    scenarios       may use every layer, but not each other

The kernel (domain, application, infrastructure) knows no scenario.
"""
import ast
import sys
from pathlib import Path

import quorum

ROOT = Path(quorum.__file__).parent
KERNEL = ("domain", "application", "infrastructure")
ALLOWED = {                       # layer -> layers it may import
    "domain": {"domain"},
    "application": {"application", "domain"},
    "infrastructure": {"infrastructure", "domain"},
    "adapters": {"adapters", "application", "domain"},
}
FRAMEWORKS = {"adapters": {"inspect_ai", "openai"}}
DOMAIN_WORDS = ("tender", "licitaci", "supplier", "proveedor", "citizen", "ciudadano", "ticket", "helpdesk",
                "sealed", "inspect_ai", "openai")


def files(layer):
    return sorted((ROOT / layer).glob("*.py"))


def imports(path):
    """Yield (layer or None, top-level module) for every import in the file."""
    layer = path.parent.name
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom):
            if node.level == 1:
                yield layer, None                                   # from .x import y
            elif node.level == 2:
                yield (node.module or "").split(".")[0], None       # from ..layer.x import y
            elif node.level > 2:
                yield "outside-the-package", None
            elif node.module.split(".")[0] == "quorum":
                yield ([*node.module.split("."), ""])[1], None
            else:
                yield None, node.module.split(".")[0]
        elif isinstance(node, ast.Import):
            for alias in node.names:
                yield None, alias.name.split(".")[0]


def test_every_layer_exists_and_has_code():
    assert len(files("domain")) >= 8 and len(files("application")) >= 3 and len(files("infrastructure")) >= 3


def test_dependencies_point_inwards():
    for layer, allowed in ALLOWED.items():
        for path in files(layer):
            for target, module in imports(path):
                if target is not None:
                    assert target in allowed, f"{layer}/{path.name} imports from {target}"
                else:
                    third_party_ok = module in FRAMEWORKS.get(layer, ())
                    assert module in sys.stdlib_module_names or third_party_ok, f"{layer}/{path.name}: {module}"


def test_the_domain_does_no_io():
    forbidden = {"sqlite3", "tomllib", "pathlib", "os", "socket", "subprocess", "urllib", "http"}
    for path in files("domain"):
        used = {module for target, module in imports(path) if target is None}
        assert not used & forbidden, f"domain/{path.name} uses {sorted(used & forbidden)}"


def test_the_kernel_does_not_mention_any_scenario():
    for layer in KERNEL:
        for path in files(layer):
            text = path.read_text(encoding="utf-8").lower()
            for word in DOMAIN_WORDS:
                assert word not in text, f"{layer}/{path.name} mentions {word!r}"


def test_scenarios_do_not_know_each_other():
    scenarios = ROOT / "scenarios"
    for folder in (c for c in scenarios.iterdir() if c.is_dir() and not c.name.startswith("_")):
        others = [c.name for c in scenarios.iterdir() if c.is_dir() and c.name not in (folder.name, "__pycache__")]
        for path in folder.glob("*.py"):
            text = path.read_text(encoding="utf-8")
            assert not any(other in text for other in others), f"{path} mentions another scenario"
