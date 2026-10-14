"""Does letting a reading that bears on the air handler count for the whole group change the verdict of Addendum 30? (PREREGISTRATION_DR.md Addendum 31.) Simulation only; nothing here is
evidence about real technicians. Needs Addendum 30's raw results (scripts/74) as comparison partners.
  .venv/bin/python doc_mismatch/scripts/75_troubleshoot_joint2.py                      # the pre-registered run
  .venv/bin/python doc_mismatch/scripts/75_troubleshoot_joint2.py --smoke --out DIR    # plumbing check on 2 cells x 20 events; gates not enforced; numbers meaningless
  .venv/bin/python doc_mismatch/scripts/75_troubleshoot_joint2.py --from-pickle        # regenerate the report from the stored raw results
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
from docmismatch.troubleshoot.v2 import study_joint2 as J2  # noqa: E402

REPO = ROOT.parent
OUT = REPO / "results/docmismatch/troubleshoot_joint2"
SUB_TEXT = {"all": "all events", "shared": "shared-cause events", "multi": "several complaints, no shared cause", "single": "one complaint"}
COMP_TEXT = {"H": "joint2 - ticket_memo2 (the machinery against the routine, both repaired)  [PRIMARY]", "I": "joint2 - joint (what the repair did for the joint tool)",
             "J": "ticket_memo2 - ticket_memo (what it did for the routine)", "K": "joint2 - fast_parent (an obvious human rule)", "L": "joint2 - ticket (what exists today)",
             "M": "joint2_la2 - joint2 (two-step look-ahead against one-step)", "N": "joint3 - ticket_memo2 (SECONDARY: repaired, air-handler rate threshold unscaled)",
             "O": "joint3 - joint2 (what unscaling the air-handler threshold did)"}
SHOW = ("tool_ticket", "tool_ticket_memo", "tool_ticket_memo2", "tool_joint", "tool_joint2", "tool_joint2_la2", "tool_joint3", "fast_parent")


def pct(x):
    return "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{100 * x:.0f}%"


def pct1(x):
    return "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{100 * x:.1f}%"


def cell_text(c):
    return f"shared {c.shared} / {c.map} / {c.rel}"


def wcost(e):
    v = e["wrong_cost"]
    return {"DOMINATES": "joint2 ahead on both", "DOMINATED": "other ahead on both"}.get(e["break_even"]) or (f"{v:.0f} min (joint2 wins above)" if e["break_even"] == "SLOWER-MORE" else f"{v:.0f} min (joint2 wins below)")


def sumrow(s):
    return "n/a" if s.get("n", 0) == 0 else f"{s['minutes']:.0f} min / {pct(s['accuracy'])} / {pct1(s['wrong_confident'])} / {s['checks']:.1f}"


def report(analyses, gates, enforced, n, wall):
    L = ["# The group-informing rule (Addendum 31)", "",
         f"Addendum 30's world, cells and events ({len(analyses)} cells, {n} events each, both tiers); three new policies with the repaired conclusion rule (`tool_ticket_memo2`, `tool_joint2`, `tool_joint2_la2`) compared with "
         "Addendum 30's stored results (same events, different answer draws). Everything is simulated from the tool's own model family with placeholder numbers; the stand-in is my construction; nothing here is evidence "
         "about real technicians, buildings, or how often shared causes happen.", "", "## Gates", "", "| gate | result | detail |", "|---|---|---|"]
    for g, (ok, d) in gates.items():
        L.append(f"| {g} | {'PASS' if ok else 'FAIL'} | {d} |")
    if not enforced:
        L += ["", "**SMOKE RUN: gates are not enforced and the numbers below are meaningless.**"]
    if enforced and not all(ok for ok, _ in gates.values()):
        return "\n".join(L + ["", "## NO RESULT (a gate failed)"])
    pc = J2.cell_of(analyses, **J.PRIMARY) if any(a["cell"].is_primary for a in analyses) else analyses[0]
    S_ = pc["sum"]
    for tier in J.TIERS:
        L += ["", f"## Primary cell ({cell_text(pc['cell'])}), tier {tier}: minutes per visit / share of complaints diagnosed correctly / wrong-and-confident / checks per visit", "",
              "| policy | all events | shared-cause | several, no shared cause | one complaint |", "|---|---|---|---|---|"]
        for pol in SHOW:
            if (tier, pol, "all") in S_:
                L.append(f"| {pol} | " + " | ".join(sumrow(S_[(tier, pol, sub)]) for sub in J.SUBSETS) + " |")
    L += ["", "## Every comparison over the cells", "",
          "Labels are Addendum 21's for the FIRST policy minus the second on the same events (TRADE in brackets: faster but less accurate (F/L) or slower but more accurate (S/M)); SAFETY REG / GAIN = share of cells where the "
          "first policy's wrong-and-confident rate is at least 0.02 higher / lower with the interval clear of 0. The last columns are the primary cell's deltas and, for K, the break-even cost of a wrong diagnosis.", "",
          "| comparison | tier | subset | cells | IMPROVES | WORSE | TRADE (F/L, S/M) | NEITHER | SAFETY REG / GAIN | primary: d minutes | d accuracy | d wrong-and-confident | break-even |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name in J2.COMPS2:
        for sub in J.SUBSETS:
            for tier in J.TIERS:
                key = (tier, name, sub)
                sh = J2.shares(analyses, key)
                if sh["n_cells"] == 0:
                    continue
                e = pc["cmp"].get(key)
                prim = f"{e['d_min']:+.1f} ({100 * e['r_min']:+.0f}%) | {e['d_acc']:+.3f} | {e['d_wc']:+.3f} | {wcost(e) if name == 'K' else ''}" if e else "n/a | n/a | n/a | "
                L.append(f"| {name}: {COMP_TEXT[name]} | {tier} | {SUB_TEXT[sub]} | {sh['n_cells']} | {pct(sh['IMPROVES'])} | {pct(sh['WORSE'])} | {pct(sh['TRADE'])} ({pct(sh['FASTER_LESS'])}, {pct(sh['SLOWER_MORE'])}) | "
                         f"{pct(sh['NEITHER'])} | {pct(sh['SAFETY_REGRESSION'])} / {pct(sh['SAFETY_GAIN'])} | {prim} |")
    L += ["", "## Every cell, all events: minutes / accuracy / wrong-and-confident (T2 | T3)", "", "| cell | policy | T2 | T3 |", "|---|---|---|---|"]
    for a in analyses:
        for pol in SHOW:
            if ("T2", pol, "all") not in a["sum"]:
                continue
            L.append(f"| {cell_text(a['cell'])} | {pol} | " + " | ".join(
                f"{a['sum'][(t, pol, 'all')]['minutes']:.0f} / {pct(a['sum'][(t, pol, 'all')]['accuracy'])} / {pct1(a['sum'][(t, pol, 'all')]['wrong_confident'])}" for t in J.TIERS) + " |")
    if any(a["cell"].is_primary for a in analyses) and len(analyses) == len(J.all_cells()):
        L += ["", "## Predictions (written before the run; each strict)", "", "| prediction | holds | values |", "|---|---|---|"]
        for k, (ok, det) in J2.predictions2(analyses).items():
            L.append(f"| {k} | {'holds' if ok else 'does not hold'} | {det} |")
        L += ["", f"## Frozen decision: {J2.decision2(analyses)}"]
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
    ap.add_argument("--raw30", type=Path, default=J2.RAW30)
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    if not a.raw30.exists():
        sys.exit(f"Addendum 30's raw results are needed: {a.raw30}")
    raw30 = pickle.loads(a.raw30.read_bytes())
    t0 = time.time()
    if a.from_pickle:
        results = pickle.loads((a.out / "joint2_raw.pkl").read_bytes())
    else:
        cells, n = list(enumerate(J.all_cells())), J2.N_EPISODES
        if a.smoke:
            cells, n = cells[:2], 20
        results = J2.compute_cells2(cells, n, a.workers)
        (a.out / "joint2_raw.pkl").write_bytes(pickle.dumps(results))
    n = results[0]["n"]
    old = {r["idx"]: r for r in raw30}
    analyses = [J2.analyze_cell2(J2.merged(r, old[r["idx"]])) for r in results]
    gates = {"G1 regression": J2.gate_g1(results, raw30, 8 if a.smoke else J2.G1_EVENTS), "G2 the rule": J2.gate_g2(30 if a.smoke else 100), "G3 replay": J2.gate_g3(results),
             "G4 reproducibility": J2.gate_g4(results, min(30, n)), "G5 completeness and pairing": J2.gate_g5(results, expected_idx=[r["idx"] for r in results] if a.smoke else None, n=n),
             "G6 the tool's settings": J2.gate_g6(results, raw30)}
    text = report(analyses, gates, not a.smoke, n, time.time() - t0)
    (a.out / "joint2_report.md").write_text(text + "\n")
    (a.out / "joint2_analysis.pkl").write_bytes(pickle.dumps(analyses))
    write_csv(a.out / "joint2_cells.csv", analyses)
    print(f"wrote {a.out / 'joint2_report.md'}; gates: " + ", ".join(f"{g.split()[0]} {'PASS' if ok else 'FAIL'}" for g, (ok, _) in gates.items()))
    if not a.smoke and not all(ok for ok, _ in gates.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
