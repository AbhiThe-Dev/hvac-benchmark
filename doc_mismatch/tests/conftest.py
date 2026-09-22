import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
RES = ROOT.parent / "results" / "docmismatch"


@pytest.fixture(scope="session")
def cases():
    p = RES / "cases.jsonl"
    if not p.exists():
        pytest.skip("run scripts/01_simulate.py and 02_build.py first")
    return [json.loads(l) for l in p.open()]


@pytest.fixture(scope="session")
def bases(cases):
    from docmismatch.data import load_base
    return {t: load_base(t) for t in {c["topology_id"] for c in cases}}
