"""Healthy-ensemble checks and calibration anchors. Run before 02_build_matrix.py; if the anchors fail the matrix is not built.

    uv run python scripts/01_validate_model.py
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hotwater_dx.matrix import THRESHOLDS  # noqa: E402
from hotwater_dx.plant import build_plant  # noqa: E402
from hotwater_dx.sampling import design_matrix, substream  # noqa: E402
from hotwater_dx.solve import has_complaint, solve  # noqa: E402


def main() -> int:
    n, seed = THRESHOLDS["N_THETA"], THRESHOLDS["SEED"]
    plants = [build_plant(d, substream(seed, 1, j)) for j, d in enumerate(design_matrix(n, seed))]
    nonconv = worst_e = worst_f = 0.0
    spread, w_apt, complaint = [], [], 0
    for P in plants:
        for load in (0.0, 1.0):
            s = solve(P, load, True)
            nonconv += not s.converged
            worst_e = max(worst_e, s.energy_residual)
            if not P.thermal:
                worst_f = max(worst_f, s.flow_residual)
        s0 = solve(P, 0.0, True)
        spread.append(max(s0.T_E) - min(s0.T_E))
        w_apt.append(500 * s0.Qs * (s0.Ts - s0.T_cm) * 0.29307 / 32)
        complaint += has_complaint(P)
    print(f"healthy plants: {n}; non-converged solves: {int(nonconv)}; worst enthalpy residual {worst_e:.2e}; worst hydraulic residual {worst_f:.2e}")
    print(f"healthy complaint rate: {complaint / n:.3f}  (should be ~0)")
    print(f"riser-top spread F: median {np.median(spread):.1f}, p95 {np.percentile(spread, 95):.1f}  (anchor PGE24: balanced within 2-5 F)")
    w = np.array(w_apt)
    print(f"loop loss W/apartment (32 apts assumed): median {np.median(w):.0f}, p5-p95 {np.percentile(w, 5):.0f}-{np.percentile(w, 95):.0f}  (anchor ETCC 24-100, mean 62.5; model runs high)")
    ok = nonconv == 0 and worst_e < 1e-3 and complaint / n < 0.02 and np.percentile(spread, 95) <= 5.0
    print("ANCHORS", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
