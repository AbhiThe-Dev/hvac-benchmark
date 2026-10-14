"""Fit the engine on a matched simulated world and stress-test it on mismatched worlds. Simulation only.

    uv run python scripts/03_engine_stress.py [--out output]
"""
import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hotwater_dx import stress as S  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "output"))
    a = ap.parse_args()
    t = time.time()
    info = S.run_all(Path(a.out))
    print("frozen hash", S.frozen_hash())
    for k, ok, ev in S.scorecard(info["rows"]):
        print(f"{k:12s} {'holds' if ok else 'FAILS':6s} {ev}")
    print(f"{time.time() - t:.0f} s; wrote {a.out}/ENGINE_STRESS_REPORT.md")


if __name__ == "__main__":
    main()
