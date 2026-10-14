"""Build the cause x check matrix (physics-model output). Run 01_validate_model.py first.

    uv run python scripts/02_build_matrix.py [--n 200] [--out output]
"""
import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hotwater_dx import matrix as MX  # noqa: E402
from hotwater_dx.report import write_all, write_model_limits  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=MX.THRESHOLDS["N_THETA"])
    ap.add_argument("--out", default=str(ROOT / "output"))
    a = ap.parse_args()
    t0 = time.time()
    w = MX.build_world(n_theta=a.n)
    cells = MX.build_matrix(w)
    pairs = MX.pair_confusion(w)
    inter = MX.interactions(w)
    info = write_all(Path(a.out), w, cells, pairs, inter)
    # exploratory only: how much do the class counts move if the separation threshold moves by +-20%?
    sens = {}
    base_z = MX.THRESHOLDS["Z_SEP"]
    for z in (0.8 * base_z, base_z, 1.2 * base_z):
        MX.THRESHOLDS["Z_SEP"] = z
        sens[f"Z_SEP={z:.1f}"] = dict(__import__("collections").Counter(c.cls for c in MX.build_matrix(w, tools_alt=False)))
    MX.THRESHOLDS["Z_SEP"] = base_z
    (Path(a.out) / "threshold_sensitivity.json").write_text(__import__("json").dumps(sens, indent=1) + "\n")
    print("threshold sensitivity (exploratory):", sens)
    write_model_limits(Path(a.out), len(MX.C.INTERACTIONS))
    print(f"thresholds sha256 {MX.thresholds_hash()}")
    print(dict(info["counts"]), f"| uncertain cells {info['n_unc']} | {time.time() - t0:.0f} s | wrote {a.out}")


if __name__ == "__main__":
    main()
