"""Stage 1 (physics_pipeline/.venv): build/extract/simulate each base topology.

  /path/to/physics_pipeline/.venv/bin/python doc_mismatch/scripts/01_simulate.py [topology ...]
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.physical import TOPOLOGIES, simulate_topology  # noqa: E402

OUT = ROOT.parent / "results" / "docmismatch" / "base"
if __name__ == "__main__":
    for tid in (sys.argv[1:] or list(TOPOLOGIES)):
        r = simulate_topology(tid, OUT)
        print(tid, r, flush=True)
