"""Sensitivity analysis of the engine (simulation only). Run after 03_engine_stress.py.

    uv run python scripts/04_engine_sensitivity.py [--out output]
"""
import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hotwater_dx import sensitivity as SN  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "output"))
    a = ap.parse_args()
    t = time.time()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    res = SN.run_all(out)
    sc = SN.write(out, res)
    print("config hash", SN.config_hash(), "| baseline", {k: round(v, 3) for k, v in res["base"].items()}, "| noise floor", {k: round(v, 4) for k, v in res["floor"].items()})
    for k, ok, ev in sc:
        print(f"{k:4s} {'holds' if ok else 'FAILS':6s} {ev}")
    print(f"{time.time() - t:.0f} s; wrote {a.out}/ENGINE_SENSITIVITY_REPORT.md")


if __name__ == "__main__":
    main()
