"""This project must not depend on the HVAC projects in the repository."""
import ast
from pathlib import Path

FORBIDDEN = {"docmismatch", "hvac_benchmark", "symptom_pipeline", "physics_pipeline"}
ROOT = Path(__file__).resolve().parents[1]


def test_no_forbidden_imports():
    for path in list((ROOT / "src").rglob("*.py")) + list((ROOT / "tests").rglob("*.py")) + list((ROOT / "scripts").rglob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.split(".")[0]]
            assert not (set(names) & FORBIDDEN), f"{path} imports {names}"


def test_pyproject_does_not_depend_on_siblings():
    text = (ROOT / "pyproject.toml").read_text()
    assert not any(n.replace("_", "-") in text for n in FORBIDDEN)
