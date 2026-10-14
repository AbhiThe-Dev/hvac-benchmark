"""How does the v1 tool compare with fast trial-and-error stand-ins at each data tier? (PREREGISTRATION_DR.md Addendum 28.) Simulation only; every stand-in is my construction.
12 cells (Addendum 27's), 500 paired episodes; the tool's episodes are Addendum 27's, reproduced; three stand-ins (habit_A, fast_list, fast_confirm) work the same episodes.
  .venv/bin/python doc_mismatch/scripts/72_troubleshoot_v1_fast.py                      # the pre-registered run
  .venv/bin/python doc_mismatch/scripts/72_troubleshoot_v1_fast.py --smoke --out DIR    # plumbing check on 2 cells x 20 episodes; gates not enforced; numbers meaningless
  .venv/bin/python doc_mismatch/scripts/72_troubleshoot_v1_fast.py --from-pickle        # regenerate the report from the stored raw results
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
from docmismatch.troubleshoot.v1 import study_fast_v1 as F  # noqa: E402
from docmismatch.troubleshoot.v1 import study_tiers as T  # noqa: E402

REPO = ROOT.parent
OUT = REPO / "results/docmismatch/troubleshoot_v1_fast"
STAND_TEXT = {"habit_A": "habit_A (v0's fast stand-in)", "fast_list": "fast_list (cheapest-first checklist)", "fast_confirm": "fast_confirm (checklist, findings confirmed)"}


def pct(x):
    return "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{100 * x:.0f}%"


def num(s, k, kind="min"):
    if s.get("n", 0) == 0:
        return "n/a"
    return {"min": f"{s[k]:.0f}", "pct": pct(s[k]), "num": f"{s[k]:.1f}"}[kind]


def wcost(e):
    v = e["wrong_cost"]
    return {"DOMINATES": "tool ahead on both", "DOMINATED": "stand-in ahead on both"}.get(e["break_even"]) or (f"{v:.0f} min (tool wins above)" if e["break_even"] == "SLOWER-MORE" else f"{v:.0f} min (tool wins below)")


def cell_text(c):
    return f"{c.rel} / {c.mix} / {c.cover}"


def report(results, analyses, gates, enforced, n, wall):
    L = ["# The v1 tool against fast stand-in technicians (Addendum 28)", "",
         f"The complaints, data tiers and simulated answers of Addendum 27; the tool's episodes are Addendum 27's, reproduced. {len(analyses)} cells, {n} paired episodes each. Three stand-ins, ALL MY CONSTRUCTIONS and none a real "
         "technician: `habit_A` (v0's fast stand-in: it can answer only in v0's four lumps), `fast_list` (cheapest-first checklist of single-cause checks; the first abnormal reading concludes) and `fast_confirm` (a finding must be "
         "confirmed). They are charged the tool's own minutes, get the world's facts for free, ask nothing, and always conclude, so their wrong-and-confident rate is their whole error rate. Everything is simulated from the tool's "
         "own model family with placeholder numbers; nothing here is evidence about real technicians.", "", "## Gates", "", "| gate | result | detail |", "|---|---|---|"]
    for g, (ok, d) in gates.items():
        L.append(f"| {g} | {'PASS' if ok else 'FAIL'} | {d} |")
    if not enforced:
        L += ["", "**SMOKE RUN: gates are not enforced and the numbers below are meaningless.**"]
    if enforced and not all(ok for ok, _ in gates.values()):
        return "\n".join(L + ["", "## NO RESULT (a gate failed)"])
    pc = T.cell_of(analyses, **T.PRIMARY) if any(a["cell"].is_primary for a in analyses) else analyses[0]
    S_ = pc["sum"]
    L += ["", f"## Primary cell ({cell_text(pc['cell'])}), hardware / configuration-cause episodes (n = {pc['n_hw']}), EXACT cause", "",
          "| arm | policy | minutes | accuracy | wrong-and-confident | checks | entries typed | minutes per correct | unresolved |", "|---|---|---|---|---|---|---|---|---|"]
    for arm in T.ARM_NAMES:
        for p in ("tool", "fast_list", "fast_confirm"):
            s = S_[(p, arm, "hw", "exact")]
            L.append(f"| {arm} | {p} | {num(s, 'minutes')} | {num(s, 'accuracy', 'pct')} | {num(s, 'wrong_confident', 'pct')} | {num(s, 'checks', 'num')} | {num(s, 'entries', 'num')} | "
                     f"{num(s, 'per_correct')} | {pct(1 - s['concluded']) if p == 'tool' and s.get('n') else '0% (always concludes)'} |")
    L += ["", "## Same cell, hardware episodes, v0's LEVEL (four lumps): the level `habit_A` can answer at", "",
          "The last column is the accuracy of always guessing 'the box acts, the cause is elsewhere', the base rate any lump-level accuracy must be read against.", "",
          "| arm | tool | habit_A | fast_list | fast_confirm | constant guess |", "|---|---|---|---|---|---|"]
    for arm in T.ARM_NAMES:
        cols = [f"{num(S_[(p, arm, 'hw', 'v0')], 'minutes')} min / {num(S_[(p, arm, 'hw', 'v0')], 'accuracy', 'pct')} / {num(S_[(p, arm, 'hw', 'v0')], 'wrong_confident', 'pct')}" for p in ("tool",) + F.POLICIES]
        L.append(f"| {arm} | " + " | ".join(cols) + f" | {pct(S_[('baseline', arm, 'hw', 'v0')]['accuracy'])} |")
    L += ["", f"## Same cell, episodes where the drawings are wrong (n = {pc['n_doc']}; T1 and up): minutes / accuracy exact / accuracy at v0's level", "", "| arm | tool | habit_A | fast_list | fast_confirm |", "|---|---|---|---|---|"]
    for arm in T.ARM_NAMES[1:]:
        cols = []
        for p in ("tool",) + F.POLICIES:
            e, v = S_.get((p, arm, "doc", "exact"), dict(n=0)), S_[(p, arm, "doc", "v0")]
            cols.append(f"{num(v, 'minutes')} / {num(e, 'accuracy', 'pct') if p != 'habit_A' else 'n/a'} / {num(v, 'accuracy', 'pct')}")
        L.append(f"| {arm} | " + " | ".join(cols) + " |")
    L += ["", "## The tool against each stand-in, over the 12 cells (tool minus stand-in on the same episodes)", "",
          "Labels are Addendum 21's (IMPROVES / WORSE / TRADE / NEITHER at 5% minutes and 0.02 accuracy, paired 95% intervals); TRADE in brackets: the tool faster but less accurate (F/L) or slower but more accurate (S/M); "
          "SAFETY REG = share of cells where the tool's wrong-and-confident rate is at least 0.02 higher with the interval clear of 0 (GAIN: lower). No verdict rule. The last column is the break-even cost of a wrong diagnosis "
          "on the primary cell's means (the extra minutes it must cost before the tool's extra time pays, or the cost below which a faster, less accurate tool is ahead).", "",
          "| arm | stand-in | subset | level | IMPROVES | WORSE | TRADE (F/L, S/M) | NEITHER | SAFETY REG / GAIN | primary: d minutes | d accuracy | d wrong-and-confident | break-even wrong-diagnosis cost |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for sub in F.SUBSETS:
        for stand, level in F.combos():
            for arm in T.ARM_NAMES:
                key = (arm, stand, sub, level)
                if key not in pc["cmp"]:
                    continue
                sh, e = F.shares(analyses, key), pc["cmp"][key]
                L.append(f"| {arm} | {stand} | {'hardware' if sub == 'hw' else 'drawings wrong'} | {level} | {pct(sh['IMPROVES'])} | {pct(sh['WORSE'])} | {pct(sh['TRADE'])} ({pct(sh['FASTER_LESS'])}, {pct(sh['SLOWER_MORE'])}) | "
                         f"{pct(sh['NEITHER'])} | {pct(sh['SAFETY_REGRESSION'])} / {pct(sh['SAFETY_GAIN'])} | {e['d_min']:+.0f} ({100 * e['r_min']:+.0f}%) | {e['d_acc']:+.3f} | {e['d_wc']:+.3f} | {wcost(e)} |")
    L += ["", "## Every cell, hardware episodes, exact level: tool | fast_list | fast_confirm as minutes / accuracy / wrong-and-confident", "", "| reliability / mix / coverage | arm | tool | fast_list | fast_confirm |", "|---|---|---|---|---|"]
    for a in analyses:
        for arm in T.ARM_NAMES:
            cols = [f"{num(a['sum'][(p, arm, 'hw', 'exact')], 'minutes')} / {num(a['sum'][(p, arm, 'hw', 'exact')], 'accuracy', 'pct')} / {num(a['sum'][(p, arm, 'hw', 'exact')], 'wrong_confident', 'pct')}" for p in ("tool", "fast_list", "fast_confirm")]
            L.append(f"| {cell_text(a['cell'])} | {arm} | " + " | ".join(cols) + " |")
    if any(a["cell"].is_primary for a in analyses) and len(analyses) == len(T.all_cells()):
        L += ["", "## Predictions (written before the run; each strict)", "", "| prediction | holds | values |", "|---|---|---|"]
        for k, p in F.fast_predictions(analyses).items():
            L.append(f"| {k} | {'holds' if p['holds'] else 'does not hold'} | {p['values']} |")
    L += ["", f"Run time {wall:.0f} s."]
    return "\n".join(L)


def write_csv(path, analyses):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cell", "rel", "mix", "cover", "policy", "arm", "subset", "level", "n", "minutes", "accuracy", "wrong_confident", "checks", "entries", "concluded", "per_correct"])
        for a in analyses:
            c = a["cell"]
            for (p, arm, sub, level), s in a["sum"].items():
                if s.get("n", 0) == 0:
                    continue
                w.writerow([a["idx"], c.rel, c.mix, c.cover, p, arm, sub, level, s["n"]] + [f"{s[k]:.4f}" if k in s else "" for k in ("minutes", "accuracy", "wrong_confident", "checks", "entries", "concluded", "per_correct")])


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
        results = pickle.loads((a.out / "fast_raw.pkl").read_bytes())
    else:
        cells, n = list(enumerate(T.all_cells())), F.N_EPISODES
        if a.smoke:
            cells, n = cells[:2], 20
        results = F.compute_cells(cells, n, a.workers)
        (a.out / "fast_raw.pkl").write_bytes(pickle.dumps(results))
    n = results[0]["n"]
    analyses = [F.analyze_cell(r) for r in results]
    gates = {"G1 code path": F.gate_g1(results, None if a.smoke else F.RAW27), "G2 accounting": F.gate_g2(results), "G3 availability": F.gate_g3(results), "G4 reproducibility": F.gate_g4(results, min(50, n)),
             "G5 completeness and pairing": F.gate_g5(results, expected_idx=[r["idx"] for r in results] if a.smoke else None)}
    text = report(results, analyses, gates, not a.smoke, n, time.time() - t0)
    (a.out / "fast_report.md").write_text(text + "\n")
    (a.out / "fast_analysis.pkl").write_bytes(pickle.dumps(analyses))
    write_csv(a.out / "fast_cells.csv", analyses)
    print(f"wrote {a.out / 'fast_report.md'}; gates: " + ", ".join(f"{g.split()[0]} {'PASS' if ok else 'FAIL'}" for g, (ok, _) in gates.items()))
    if not a.smoke and not all(ok for ok, _ in gates.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
