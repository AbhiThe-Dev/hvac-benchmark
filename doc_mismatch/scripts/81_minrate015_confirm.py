"""Does the live default (min_rate = 0.015, chosen by the user beyond Addendum 35's confirmed 0.01) hold up across tiers and the other cells? (PREREGISTRATION_DR.md Addendum 36.)
Simulation only; no LLM. Needs Addendum 30's raw results (scripts/74) as a comparison partner.
  .venv/bin/python doc_mismatch/scripts/81_minrate015_confirm.py                      # the pre-registered run (18 cells x 1000 events)
  .venv/bin/python doc_mismatch/scripts/81_minrate015_confirm.py --smoke --out DIR    # plumbing check on 3 cells x 20 events; gates not enforced; numbers meaningless
  .venv/bin/python doc_mismatch/scripts/81_minrate015_confirm.py --from-pickle        # regenerate the report from the stored raw results
"""
import argparse
import csv
import pickle
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.troubleshoot.v2 import study_joint as J  # noqa: E402
from docmismatch.troubleshoot.v2 import study_minrate2 as M  # noqa: E402

REPO = ROOT.parent
OUT = REPO / "results/docmismatch/troubleshoot_minrate2"
SUB_TEXT = {"all": "all events", "shared": "shared-cause events", "multi": "several complaints, no shared cause", "single": "one complaint"}


def pct(x):
    return "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{100 * x:.0f}%"


def pct1(x):
    return "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{100 * x:.1f}%"


def cell_text(c):
    return f"shared {c.shared} / {c.map} / {c.rel}"


def sumrow(s):
    return "n/a" if s.get("n", 0) == 0 else f"{s['minutes']:.0f} min / {pct(s['accuracy'])} / {pct1(s['wrong_confident'])} / {s['checks']:.1f}"


def report(analyses, gates, enforced, n, wall) -> str:
    L = ["# Does the live default (min_rate = 0.015) hold up across tiers and cells? (Addendum 36)", "",
         f"Addendum 30's 18 cells, {n} events each, both tiers; the routine (`tool_ticket_memo2`) at its default check-value bar (`min_rate` = 0.003) against the live tool's current default "
         "(`min_rate` = 0.015, chosen by the user beyond Addendum 35's confirmed 0.01); `tau` unchanged at 0.95; identical answers to identical questions (`TableOracle`). No LLM is run here. "
         "Simulation only, from the tool's own model family with placeholder numbers.", "", "## Gates", "", "| gate | result | detail |", "|---|---|---|"]
    for g, (ok, d) in gates.items():
        L.append(f"| {g} | {'PASS' if ok else 'FAIL'} | {d} |")
    if not enforced:
        L += ["", "**SMOKE RUN: gates are not enforced and the numbers below are meaningless.**"]
    if enforced and not all(ok for ok, _ in gates.values()):
        return "\n".join(L + ["", "## NO RESULT (a gate failed)"])
    if not any(a["cell"].is_primary for a in analyses):
        return "\n".join(L + ["", "## (smoke run: the primary cell is not in this subset; per-cell table skipped)"])
    pc = M.cell_of(analyses, **J.PRIMARY)
    S_ = pc["sum"]
    for tier in M.TIERS:
        L += ["", f"## Primary cell ({cell_text(pc['cell'])}), tier {tier}: minutes per visit / share diagnosed exactly right / wrong-and-confident / checks per visit", "",
              "| min_rate | all events | shared-cause | several, no shared cause | one complaint |", "|---|---|---|---|---|"]
        for mr in M.GRID:
            if (tier, mr, "all") in S_:
                mark = " (baseline)" if mr == M.BASE_MIN_RATE else " (live default)" if mr == M.CHALLENGER else ""
                L.append(f"| {mr:g}{mark} | " + " | ".join(sumrow(S_[(tier, mr, sub)]) for sub in M.SUBSETS) + " |")
    L += ["", "## Every cell, both tiers: challenger (min_rate=0.015) minus baseline (min_rate=0.003), `all` events", "",
          "| cell | tier | d minutes | d accuracy | d wrong-and-confident | time / accuracy | label | safety |", "|---|---|---|---|---|---|---|---|"]
    for a in analyses:
        for tier in M.TIERS:
            key = (tier, M.CHALLENGER, "all")
            if key not in a["cmp"]:
                continue
            e = a["cmp"][key]
            L.append(f"| {cell_text(a['cell'])} | {tier} | {e['d_min']:+.1f} ({100 * e['r_min']:+.0f}%) | {e['d_acc']:+.3f} | {e['d_wc']:+.3f} | {e['time']} / {e['acc']} | {e['label']} | {e['safety']} |")
    L += ["", "## Shares of the 18 cells (challenger vs baseline, `all` events)", "", "| tier | IMPROVES | WORSE | TRADE | NEITHER | SAFETY REGRESSION | SAFETY GAIN |", "|---|---|---|---|---|---|---|"]
    for tier in M.TIERS:
        sh = M.shares(analyses, (tier, M.CHALLENGER, "all"))
        L.append(f"| {tier} | {pct(sh['IMPROVES'])} | {pct(sh['WORSE'])} | {pct(sh['TRADE'])} | {pct(sh['NEITHER'])} | {pct(sh['SAFETY_REGRESSION'])} | {pct(sh['SAFETY_GAIN'])} |")
    p6_ok, p6_detail = M.check_p6(analyses)
    L += ["", "## Predictions (written before the run; each strict)", "", "| prediction | holds | values |", "|---|---|---|"]
    for k, (ok, det) in M.predictions(analyses).items():
        L.append(f"| {k} | {'holds' if ok else 'does not hold'} | {det} |")
    L.append(f"| P6 | {'holds' if p6_ok else 'does not hold'} | {p6_detail} |")
    L += ["", f"## Frozen decision: {M.decision(analyses, p6_ok)}", "", f"Run time {wall:.0f} s."]
    return "\n".join(L)


def write_csv(path, analyses):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cell", "shared", "map", "rel", "tier", "min_rate", "subset", "n", "minutes", "checks", "accuracy", "accuracy_c", "wrong_confident", "concluded", "complaints"])
        for a in analyses:
            c = a["cell"]
            for (tier, mr, sub), s in a["sum"].items():
                if s.get("n", 0) == 0:
                    continue
                w.writerow([a["idx"], c.shared, c.map, c.rel, tier, mr, sub, s["n"]] + [f"{s[k]:.4f}" for k in ("minutes", "checks", "accuracy", "accuracy_c", "wrong_confident", "concluded", "complaints")])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--workers", type=int)
    ap.add_argument("--from-pickle", action="store_true")
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    if a.from_pickle:
        results = pickle.loads((a.out / "minrate2_raw.pkl").read_bytes())
    else:
        cells, n = list(enumerate(J.all_cells())), M.N_EPISODES
        if a.smoke:
            cells, n = cells[:3], 20
        results = M.compute_cells(cells, n, a.workers)
        (a.out / "minrate2_raw.pkl").write_bytes(pickle.dumps(results))
    n = results[0]["n"]
    analyses = [M.analyze_cell(r) for r in results]
    g5_idx = [i for i in range(min(3, len(results)))]
    g5_check = M.compute_cells([(results[i]["idx"], results[i]["cell"]) for i in g5_idx], n, a.workers)
    gates = {"G1 regression": M.gate_g1(results, 8 if a.smoke else 50), "G2 baseline reproduces Addendum 31": M.gate_g2(analyses), "G3 answer table": M.gate_g3(),
             "G4 reproduces the 0.015 reference (P6)": M.gate_g4(analyses), "G5 reproducibility (first 3 cells re-run)": M.gate_g5([results[i] for i in g5_idx], g5_check)}
    text = report(analyses, gates, not a.smoke, n, time.time() - t0)
    (a.out / "minrate2_report.md").write_text(text + "\n")
    (a.out / "minrate2_analysis.pkl").write_bytes(pickle.dumps(analyses))
    write_csv(a.out / "minrate2_cells.csv", analyses)
    print(f"wrote {a.out / 'minrate2_report.md'}; gates: " + ", ".join(f"{g.split()[0]} {'PASS' if ok else 'FAIL'}" for g, (ok, _) in gates.items()))
    if not a.smoke and not all(ok for ok, _ in gates.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
