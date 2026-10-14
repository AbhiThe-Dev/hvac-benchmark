"""Does investigating several complaints together save technician time? (PREREGISTRATION_DR.md Addendum 30.) Simulation only; nothing here is evidence about real technicians.
18 cells (shared-cause rate x map faults x check reliability), events per cell as frozen (N_EPISODES), both data tiers on the same events, seven policies.
  .venv/bin/python doc_mismatch/scripts/74_troubleshoot_joint.py                      # the pre-registered run
  .venv/bin/python doc_mismatch/scripts/74_troubleshoot_joint.py --smoke --out DIR    # plumbing check on 2 cells x 20 events; gates not enforced; numbers meaningless
  .venv/bin/python doc_mismatch/scripts/74_troubleshoot_joint.py --from-pickle        # regenerate the report from the stored raw results
Raw results are pickled first. A failed gate means NO RESULT.
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
from docmismatch.troubleshoot.v2 import policies as P  # noqa: E402
from docmismatch.troubleshoot.v2 import study_joint as J  # noqa: E402

REPO = ROOT.parent
OUT = REPO / "results/docmismatch/troubleshoot_joint"
SUB_TEXT = {"all": "all events", "shared": "shared-cause events (two or more complaints from one upstream fault)", "multi": "several complaints, no shared cause", "single": "one complaint"}
COMP_TEXT = {"A": "joint - ticket (what exists today)", "B": "joint - ticket_memo (the routine that reuses readings)  [PRIMARY]", "C": "ticket_memo - ticket", "D": "ticket_nb - ticket (the neighbour question alone)",
             "E": "joint - fast_parent (an obvious human rule)", "F": "joint - fast_ticket (a checklist per complaint)", "G": "joint_la2 - joint (two-step look-ahead against one-step)"}


def pct(x):
    return "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{100 * x:.0f}%"


def pct1(x):
    return "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{100 * x:.1f}%"


def cell_text(c):
    return f"shared {c.shared} / {c.map} / {c.rel}"


def wcost(e):
    v = e["wrong_cost"]
    return {"DOMINATES": "joint ahead on both", "DOMINATED": "other ahead on both"}.get(e["break_even"]) or (f"{v:.0f} min (joint wins above)" if e["break_even"] == "SLOWER-MORE" else f"{v:.0f} min (joint wins below)")


def sumrow(s):
    return "n/a" if s.get("n", 0) == 0 else f"{s['minutes']:.0f} min / {pct(s['accuracy'])} / {pct1(s['wrong_confident'])} / {s['checks']:.1f}"


def report(results, analyses, gates, enforced, n, wall):
    L = ["# Investigating several complaints together (Addendum 30)", "",
         f"A synthetic well-documented building (3 air handlers x 8 boxes and rooms); visits with one or several complaints drawn from a generative model; {len(analyses)} cells, {n} events each, both tiers on the same events. "
         "Seven policies: the v1 tool ticket by ticket (`tool_ticket`; `tool_ticket_nb` with the neighbour-informed prior; `tool_ticket_memo` which also reuses air handler readings), the joint session (`tool_joint`, and "
         "`tool_joint_la2` with two-step look-ahead), and two stand-ins that are MY CONSTRUCTIONS (`fast_ticket`, `fast_parent`). Everything is simulated from the tool's own model family with placeholder numbers; nothing here is "
         "evidence about real technicians, buildings, or how often shared causes happen.", "", "## Gates", "", "| gate | result | detail |", "|---|---|---|"]
    for g, (ok, d) in gates.items():
        L.append(f"| {g} | {'PASS' if ok else 'FAIL'} | {d} |")
    if not enforced:
        L += ["", "**SMOKE RUN: gates are not enforced and the numbers below are meaningless.**"]
    if enforced and not all(ok for ok, _ in gates.values()):
        return "\n".join(L + ["", "## NO RESULT (a gate failed)"])
    pc = J.cell_of(analyses, **J.PRIMARY) if any(a["cell"].is_primary for a in analyses) else analyses[0]
    S_ = pc["sum"]
    L += ["", f"## What the visits look like in the primary cell ({cell_text(pc['cell'])})", "",
          f"Mean complaints per visit {pc['mean_complaints']:.2f}; visits by kind: " + ", ".join(f"{k} {pc['counts'][k]}" for k in J.SUBSETS) + f" (of {pc['n']}).", ""]
    for tier in J.TIERS:
        L += ["", f"## Primary cell, tier {tier}: minutes per visit / share of complaints diagnosed correctly / wrong-and-confident / checks per visit", "",
              "| policy | all events | shared-cause | several, no shared cause | one complaint |", "|---|---|---|---|---|"]
        for pol in P.POLICIES:
            if (tier, pol, "all") not in S_:
                continue
            L.append(f"| {pol} | " + " | ".join(sumrow(S_[(tier, pol, sub)]) for sub in J.SUBSETS) + " |")
    L += ["", "## Every comparison over the cells", "",
          "Labels are Addendum 21's (IMPROVES / WORSE / TRADE / NEITHER at 5% minutes and 0.02 accuracy, paired 95% intervals) for the FIRST policy minus the second on the same events; TRADE in brackets: faster but less accurate "
          "(F/L) or slower but more accurate (S/M). SAFETY REG / GAIN = share of cells where the first policy's wrong-and-confident rate is at least 0.02 higher / lower with the interval clear of 0. The last columns are the "
          "primary cell's deltas and, for E and F, the break-even cost of a wrong diagnosis.", "",
          "| comparison | tier | subset | cells | IMPROVES | WORSE | TRADE (F/L, S/M) | NEITHER | SAFETY REG / GAIN | primary: d minutes | d accuracy | d wrong-and-confident | break-even |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name in J.COMPS:
        for sub in J.SUBSETS:
            for tier in J.TIERS:
                key = (tier, name, sub)
                sh = J.shares(analyses, key)
                if sh["n_cells"] == 0:
                    continue
                e = pc["cmp"].get(key)
                prim = f"{e['d_min']:+.1f} ({100 * e['r_min']:+.0f}%) | {e['d_acc']:+.3f} | {e['d_wc']:+.3f} | {wcost(e) if name in ('E', 'F') else ''}" if e else "n/a | n/a | n/a | "
                L.append(f"| {name}: {COMP_TEXT[name]} | {tier} | {SUB_TEXT[sub]} | {sh['n_cells']} | {pct(sh['IMPROVES'])} | {pct(sh['WORSE'])} | {pct(sh['TRADE'])} ({pct(sh['FASTER_LESS'])}, {pct(sh['SLOWER_MORE'])}) | "
                         f"{pct(sh['NEITHER'])} | {pct(sh['SAFETY_REGRESSION'])} / {pct(sh['SAFETY_GAIN'])} | {prim} |")
    L += ["", "## Every cell, all events: minutes / accuracy / wrong-and-confident for the tool policies and stand-ins (T2 | T3)", "",
          "| cell | policy | T2 | T3 |", "|---|---|---|---|"]
    for a in analyses:
        for pol in P.POLICIES:
            if ("T2", pol, "all") not in a["sum"]:
                continue
            L.append(f"| {cell_text(a['cell'])} | {pol} | " + " | ".join(
                f"{a['sum'][(t, pol, 'all')]['minutes']:.0f} / {pct(a['sum'][(t, pol, 'all')]['accuracy'])} / {pct1(a['sum'][(t, pol, 'all')]['wrong_confident'])}" for t in J.TIERS) + " |")
    if any(a["cell"].is_primary for a in analyses) and len(analyses) == len(J.all_cells()):
        L += ["", "## Predictions (written before the run; each strict)", "", "| prediction | holds | values |", "|---|---|---|"]
        for k, (ok, det) in J.joint_predictions(analyses).items():
            L.append(f"| {k} | {'holds' if ok else 'does not hold'} | {det} |")
        L += ["", f"## Frozen decision: {J.decision(analyses)}"]
    L += ["", f"Run time {wall:.0f} s."]
    return "\n".join(L)


def write_csv(path, analyses):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cell", "shared", "map", "rel", "tier", "policy", "subset", "n", "minutes", "checks", "accuracy", "accuracy_complaint_weighted", "wrong_confident", "concluded", "complaints"])
        for a in analyses:
            c = a["cell"]
            for (tier, pol, sub), s in a["sum"].items():
                if s.get("n", 0) == 0:
                    continue
                w.writerow([a["idx"], c.shared, c.map, c.rel, tier, pol, sub, s["n"]] + [f"{s[k]:.4f}" for k in ("minutes", "checks", "accuracy", "accuracy_c", "wrong_confident", "concluded", "complaints")])


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
        results = pickle.loads((a.out / "joint_raw.pkl").read_bytes())
    else:
        cells, n = list(enumerate(J.all_cells())), J.N_EPISODES
        if a.smoke:
            cells, n = cells[:2], 20
        results = J.compute_cells(cells, n, a.workers)
        (a.out / "joint_raw.pkl").write_bytes(pickle.dumps(results))
    n = results[0]["n"]
    analyses = [J.analyze_cell(r) for r in results]
    gates = {"G1 exactness": J.gate_g1(40 if a.smoke else 200), "G2 code path": J.gate_g2(6 if a.smoke else 25), "G3 replay": J.gate_g3(results), "G4 reproducibility": J.gate_g4(results, min(30, n)),
             "G5 completeness and pairing": J.gate_g5(results, expected_idx=[r["idx"] for r in results] if a.smoke else None, n=n), "G6 world sanity": J.gate_g6(results)}
    text = report(results, analyses, gates, not a.smoke, n, time.time() - t0)
    (a.out / "joint_report.md").write_text(text + "\n")
    (a.out / "joint_analysis.pkl").write_bytes(pickle.dumps(analyses))
    write_csv(a.out / "joint_cells.csv", analyses)
    print(f"wrote {a.out / 'joint_report.md'}; gates: " + ", ".join(f"{g.split()[0]} {'PASS' if ok else 'FAIL'}" for g, (ok, _) in gates.items()))
    if not a.smoke and not all(ok for ok, _ in gates.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
