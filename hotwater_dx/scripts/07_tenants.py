"""Tenant answers as soft evidence: how unreliable can they be, and what should the engine do about it? Simulation only. Run after 03_engine_stress.py.

    uv run python scripts/07_tenants.py [--out output] [--quick]
"""
import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hotwater_dx import tenants as TN  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "output"))
    ap.add_argument("--quick", action="store_true", help="tiny smoke run; numbers are not results")
    a = ap.parse_args()
    t = time.time()
    res = TN.run_all(Path(a.out), quick=a.quick)
    print("frozen hash", TN.frozen_hash())
    for k, ok, ev in res["scorecard"]:
        print(f"{k:12s} {'holds' if ok else 'FAILS':6s} {ev[:500]}")
    print(f"{time.time() - t:.0f} s; wrote {a.out}/TENANTS_REPORT.md")


if __name__ == "__main__":
    main()
