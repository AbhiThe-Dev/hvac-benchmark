"""Reading pools for the DEV expansion topologies only (dev_E..H), reps 0 and 1. Sealed pools are never built here.

  .venv/bin/python doc_mismatch/scripts/21_build_dev_pools.py [tid rep]      (no args: all dev topologies x reps, in parallel)
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.active.sim_data import DEV_TOPOLOGIES, load_dev_sim  # noqa: E402

if __name__ == "__main__":
    if len(sys.argv) == 3:
        t0 = time.time()
        p = load_dev_sim(sys.argv[1], int(sys.argv[2]))
        print(sys.argv[1], sys.argv[2], "slices", p.n_slices, {s: sp.E.shape for s, sp in p.slots.items()}, f"{time.time() - t0:.0f}s", flush=True)
    else:
        procs = [subprocess.Popen([sys.executable, __file__, t, str(r)]) for t in DEV_TOPOLOGIES for r in (0, 1)]
        sys.exit(max(p.wait() for p in procs))
