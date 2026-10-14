"""What does each data tier buy? (PREREGISTRATION_DR.md Addendum 27.) Simulation only: a synthetic building, simulated technician; nothing about real technicians.
12 cells = 3 reliabilities x 2 cause mixes x 2 data coverages, 500 paired episodes x 5 arms (T0, T1, T2, T2+access, T3) each.
  .venv/bin/python doc_mismatch/scripts/71_troubleshoot_tiers.py                       # the pre-registered run (about a minute on 8 workers)
  .venv/bin/python doc_mismatch/scripts/71_troubleshoot_tiers.py --smoke --out DIR     # plumbing check on 2 cells x 20 episodes; gates not enforced; numbers meaningless
  .venv/bin/python doc_mismatch/scripts/71_troubleshoot_tiers.py --from-pickle         # regenerate the report from the stored raw results
Raw results are pickled first. A failed gate means NO RESULT. DO NOT RUN before the user has approved the pre-registration (Addendum 27).
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
from docmismatch.troubleshoot.v1 import study_tiers as T  # noqa: E402

REPO = ROOT.parent
OUT = REPO / "results/docmismatch/troubleshoot_tiers"
REL_TEXT = {"R0": "checks as reliable as assumed", "R1": "checks worse (25% of the way to a coin flip)", "R2": "checks much worse (50% of the way to a coin flip)"}
PAIR_TEXT = {("T1", "T0"): "T1 vs T0 (add the equipment list and the drawings' claims)", ("T2", "T1"): "T2 vs T1 (add attributes and design values)",
             ("T2+access", "T2"): "T2+access vs T2 (add control-system access, no point map)", ("T3", "T2+access"): "T3 vs T2+access (add the point map)",
             ("T3", "T2"): "T3 vs T2 (access and point map together)", ("T3", "T0"): "T3 vs T0 (everything against nothing)"}


def pct(x):
    return "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{100 * x:.0f}%"


def fmt(s, key, kind="min"):
    if s.get("n", 0) == 0:
        return "n/a"
    return {"min": f"{s[key]:.0f}", "pct": pct(s[key]), "num": f"{s[key]:.1f}"}[kind]


def cell_text(c):
    return f"{c.rel} / {c.mix} / {c.cover}"


def report(results, analyses, gates, enforced, n, wall):
    L = ["# What each data tier buys (Addendum 27)", "",
         f"A synthetic building (8 rooms, 8 boxes, 2 air handlers); complaints whose true cause is drawn from the v1 cause tree; the tool given five amounts of data (the arms). {len(analyses)} cells = 3 reliabilities x 2 "
         f"cause mixes x 2 data coverages, {n} paired episodes x 5 arms each. Answers and causes are SIMULATED from the tool's own model family; every probability and every minute is a placeholder, so only orderings and ratios "
         "mean anything, and nothing here is evidence about real technicians. Hardware / configuration-cause episodes are the ones every arm can be compared on (T0 has no drawings to be wrong).", "",
         "## Gates", "", "| gate | result | detail |", "|---|---|---|"]
    for g, (ok, d) in gates.items():
        L.append(f"| {g} | {'PASS' if ok else 'FAIL'} | {d} |")
    if not enforced:
        L += ["", "**SMOKE RUN: gates are not enforced and the numbers below are meaningless.**"]
    if enforced and not all(ok for ok, _ in gates.values()):
        return "\n".join(L + ["", "## NO RESULT (a gate failed)"])
    pc = T.cell_of(analyses, **T.PRIMARY) if any(a["cell"].is_primary for a in analyses) else analyses[0]
    L += ["", f"## The primary cell ({cell_text(pc['cell'])}): hardware / configuration-cause episodes (n = {pc['n_hw']})", "",
          "| arm | minutes | accuracy | right branch | wrong-and-confident | checks | questions asked | entries typed | concluded | stopped (nothing worth its time) | hit the check limit |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for arm in T.ARM_NAMES:
        s = pc["hw"][arm]
        L.append(f"| {arm} | {fmt(s, 'minutes')} | {fmt(s, 'accuracy', 'pct')} | {fmt(s, 'group_accuracy', 'pct')} | {fmt(s, 'wrong_confident', 'pct')} | {fmt(s, 'checks', 'num')} | {fmt(s, 'questions', 'num')} | "
                 f"{fmt(s, 'entries', 'num')} | {fmt(s, 'concluded', 'pct')} | {fmt(s, 'stopped', 'pct')} | {fmt(s, 'limit', 'pct')} |")
    L += ["", "## Each step up, over the 12 cells (the richer arm minus the poorer, on the same episodes)", "",
          "Labels are the frozen ones of Addendum 21 (IMPROVES / WORSE / TRADE / NEITHER at 5% minutes and 0.02 accuracy with paired 95% intervals). TRADE has two kinds, shown in brackets: the richer arm is "
          "faster but less accurate (F/L) or slower but more accurate (S/M). SAFETY REG is the share of cells where the wrong-and-confident rate is at least 0.02 higher with the interval clear of 0. The reading (adjacent steps only) is "
          "HELPS if IMPROVES >= 75% and WORSE + TRADE <= 10%, HURTS if WORSE + TRADE > 25%, otherwise MIXED.", "",
          "| step | IMPROVES | WORSE | TRADE (F/L, S/M) | NEITHER | SAFETY REG | reading | primary cell: d minutes | d accuracy | d wrong-and-confident |", "|---|---|---|---|---|---|---|---|---|---|"]
    readings = {}
    for pair in T.PAIRS:
        sh = T.step_shares(analyses, pair)
        c = pc["cmp"][f"{pair[0]}|{pair[1]}"]
        rd = T.step_reading(sh) if pair in T.ADJACENT else ""
        readings[pair] = rd
        L.append(f"| {PAIR_TEXT[pair]} | {pct(sh['IMPROVES'])} | {pct(sh['WORSE'])} | {pct(sh['TRADE'])} ({pct(sh['FASTER_LESS'])}, {pct(sh['SLOWER_MORE'])}) | {pct(sh['NEITHER'])} | {pct(sh['SAFETY_REGRESSION'])} | "
                 f"{'**' + rd + '**' if rd else ''} | {c['d_min']:+.1f} ({100 * c['r_min']:+.0f}%) | {c['d_acc']:+.3f} | {c['d_wc']:+.3f} |")
    L += ["", "## Every cell: minutes / accuracy / wrong-and-confident (hardware / configuration-cause episodes)", "", "| reliability / mix / coverage | " + " | ".join(T.ARM_NAMES) + " |", "|---|" + "---|" * len(T.ARM_NAMES)]
    for a in analyses:
        L.append(f"| {cell_text(a['cell'])} | " + " | ".join(f"{fmt(a['hw'][arm], 'minutes')} / {fmt(a['hw'][arm], 'accuracy', 'pct')} / {fmt(a['hw'][arm], 'wrong_confident', 'pct')}" for arm in T.ARM_NAMES) + " |")
    L += ["", "## Episodes where the drawings are wrong (T1 and up; T0 has no drawings): minutes / accuracy / wrong-and-confident", "", "| reliability / mix / coverage | n | " + " | ".join(T.ARM_NAMES[1:]) + " |", "|---|---|" + "---|" * (len(T.ARM_NAMES) - 1)]
    for a in analyses:
        n_doc = a["doc"]["T1"].get("n", 0)
        L.append(f"| {cell_text(a['cell'])} | {n_doc} | " + " | ".join(f"{fmt(a['doc'][arm], 'minutes')} / {fmt(a['doc'][arm], 'accuracy', 'pct')} / {fmt(a['doc'][arm], 'wrong_confident', 'pct')}" for arm in T.ARM_NAMES[1:]) + " |")
    if any(a["cell"].is_primary for a in analyses) and len(analyses) == len(T.all_cells()):
        L += ["", "## Predictions (written before the run; each strict)", "", "| prediction | holds | values |", "|---|---|---|"]
        for k, p in T.tier_predictions(analyses).items():
            L.append(f"| {k} | {'holds' if p['holds'] else 'does not hold'} | {p['values']} |")
    L += ["", "## Reliability, in words", ""] + [f"- {k}: {v}" for k, v in REL_TEXT.items()]
    L += ["", f"Run time {wall:.0f} s."]
    return "\n".join(L)


def write_csv(path, analyses):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cell", "rel", "mix", "cover", "subset", "arm", "n", "minutes", "accuracy", "group_accuracy", "wrong_confident", "checks", "questions", "entries", "concluded", "stopped", "limit"])
        for a in analyses:
            c = a["cell"]
            for sub in ("hw", "doc"):
                for arm in T.ARM_NAMES:
                    s = a[sub][arm]
                    w.writerow([a["idx"], c.rel, c.mix, c.cover, sub, arm, s.get("n", 0)] + [f"{s[k]:.4f}" if s.get("n", 0) else "" for k in
                               ("minutes", "accuracy", "group_accuracy", "wrong_confident", "checks", "questions", "entries", "concluded", "stopped", "limit")])


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
        results = pickle.loads((a.out / "tiers_raw.pkl").read_bytes())
    else:
        cells = list(enumerate(T.all_cells()))
        n = T.N_EPISODES
        if a.smoke:
            cells, n = cells[:2], 20
        results = T.compute_cells(cells, n, a.workers)
        (a.out / "tiers_raw.pkl").write_bytes(pickle.dumps(results))
    n = results[0]["n"]
    analyses = [T.analyze_cell(r) for r in results]
    gates = {"G1 code path": T.gate_g1(30 if not a.smoke else 6), "G2 accounting": T.gate_g2(results), "G3 honesty": (lambda ok_v: (ok_v[0], "; ".join(f"{k[0]}/{k[1]}: {v[0]:.3f} (n={v[1]})" for k, v in ok_v[1].items())))(T.gate_g3(results)),
             "G4 reproducibility": T.gate_g4(results, min(50, n)), "G5 completeness and pairing": T.gate_g5(results, expected_idx=[r["idx"] for r in results] if a.smoke else None), "G6 availability": T.gate_g6(results)}
    text = report(results, analyses, gates, not a.smoke, n, time.time() - t0)
    (a.out / "tiers_report.md").write_text(text + "\n")
    (a.out / "tiers_analysis.pkl").write_bytes(pickle.dumps(analyses))
    write_csv(a.out / "tiers_cells.csv", analyses)
    print(f"wrote {a.out / 'tiers_report.md'}; gates: " + ", ".join(f"{g.split()[0]} {'PASS' if ok else 'FAIL'}" for g, (ok, _) in gates.items()))
    if not a.smoke and not all(ok for ok, _ in gates.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
