"""Addendum 42 (PREREGISTRATION_DR.md): if the answers to the tool's checks are MORE reliable than the tool assumes, how much more accurate is it, and does a lower `tau` become safe?

The nine R0 cells of Addendum 30 x b in {0, 0.5, 1.0} (0 = the world as assumed; 1.0 = every check deterministic, a ceiling) x T3-noattr and T3 x tool_joint and the routine x tau in
{0.95, 0.90, 0.85, 0.80, 0.75}, `min_rate` fixed at 0.02, the same events as Addendum 41. Simulation only; nothing here changes the tool.

  .venv/bin/python doc_mismatch/scripts/93_reliability_sweep.py                 # full run
  .venv/bin/python doc_mismatch/scripts/93_reliability_sweep.py --from-pickle   # regenerate the report from the stored raw results
  .venv/bin/python doc_mismatch/scripts/93_reliability_sweep.py --smoke         # two cells, 30 events: plumbing only

Outputs: results/docmismatch/troubleshoot_rel/ (report.md, summary.json, cells.csv, raw.pkl).
"""

from __future__ import annotations

import argparse
import csv
import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from docmismatch.troubleshoot.v2 import study_rel as R  # noqa: E402

OUT = ROOT.parent / "results" / "docmismatch" / "troubleshoot_rel"


def write_cells_csv(analyses: list[dict], path: Path) -> None:
    with open(path, "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["cell", "shared", "map", "b", "tier", "policy", "tau", "subset", "n", "minutes", "checks", "accuracy", "wrong_confident", "concluded", "label_vs_tau0.95", "safety_vs_tau0.95",
                     "label_vs_b0", "d_acc_vs_b0"])
        for a in analyses:
            c = a["cell"]
            for key, s in sorted(a["sum"].items(), key=lambda kv: tuple(str(x) for x in kv[0])):
                b, tier, pol, tau, sub = key
                if s["n"] == 0:
                    continue
                ct, cr = a["cmp"].get(("tau", b, tier, pol, tau, sub)), a["cmp"].get(("rel", b, tier, pol, tau, sub))
                wr.writerow([a["idx"], c.shared, c.map, b, tier, pol, tau, sub, s["n"], f"{s['minutes']:.3f}", f"{s['checks']:.3f}", f"{s['accuracy']:.4f}", f"{s['wrong_confident']:.4f}",
                             f"{s['concluded']:.4f}", ct["label"] if ct else "", ct["safety"] if ct else "", cr["label"] if cr else "", f"{cr['d_acc']:.4f}" if cr else ""])


def finish(results: list[dict], extra_gates: list, from_pickle: bool) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    analyses = [R.analyze_cell(r) for r in results]
    gates = [("G1", *R.gate_g1(results)), *extra_gates]
    preds = R.predictions(analyses)
    ok = all(g[1] for g in gates)
    text = R.report(analyses, results, gates, preds, results[0]["n"])
    if not ok:
        text = "# NO RESULT: a gate failed (see Gates below); nothing here is a finding.\n\n" + text
    (OUT / "report.md").write_text(text + "\n")
    t, p = R.PRIMARY_TIER, R.PRIMARY_POLICY
    summary = dict(gates={g: dict(passed=bool(o), detail=d) for g, o, d in gates}, predictions={k: dict(held=bool(v[0]), detail=v[1]) for k, v in sorted(preds.items())},
                   lowest_passing_tau={str(b): R.lowest_passing(analyses, b) for b in R.B_LEVELS},
                   cell_means={f"b{b}|tau{tau}": R.cell_means(analyses, b, t, p, tau) for b in R.B_LEVELS for tau in R.TAU_GRID},
                   breakdown={str(b): R.breakdown(results, b) for b in R.B_LEVELS})
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True, default=str))
    write_cells_csv(analyses, OUT / "cells.csv")
    if not from_pickle:
        (OUT / "raw.pkl").write_bytes(pickle.dumps(results))
    print(text)
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--from-pickle", action="store_true")
    ap.add_argument("--workers", type=int, default=None)
    a = ap.parse_args()
    if a.smoke:
        res = R.compute_cells(R.CELLS[:2], n=30, workers=1)
        for r in res:
            an = R.analyze_cell(r, B=50)
            for b in (0.5, 1.0):
                e = an["cmp"][("rel", b, R.PRIMARY_TIER, R.PRIMARY_POLICY, 0.95, "all")]
                print(r["idx"], r["cell"], f"b={b}", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in e.items() if k in ("r_min", "d_acc", "d_wc", "label")})
        print("smoke ok (plumbing only; no gates)")
        return 0
    if a.from_pickle:
        results = pickle.loads((OUT / "raw.pkl").read_bytes())
        prev = json.loads((OUT / "summary.json").read_text())
        return finish(results, [(g, v["passed"], v["detail"]) for g, v in prev["gates"].items() if g != "G1"], True)
    results = R.compute_cells(R.CELLS, workers=a.workers)
    again = R.compute_cells([R.CELLS[0], R.CELLS[4], R.CELLS[8]], workers=1)
    pick = [results[0], results[4], results[8]]
    gates = [("G2", *R.gate_g2(results)), ("G3", *R.gate_g3()), ("G4", *R.gate_g4()), ("G5", *R.gate_g5(pick, again))]
    return finish(results, gates, False)


if __name__ == "__main__":
    sys.exit(main())
