"""The v1 tool against the tool as it was before (v0), on the same complaints (PREREGISTRATION_DR.md Addendum 29). Simulation only.
  .venv/bin/python doc_mismatch/scripts/73_troubleshoot_v0_vs_v1.py                       # the pre-registered run
  .venv/bin/python doc_mismatch/scripts/73_troubleshoot_v0_vs_v1.py --smoke --out DIR     # plumbing check on 2 cells x 20 episodes; gates not enforced; numbers meaningless
A failed gate means NO RESULT.
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
from docmismatch.troubleshoot.v1 import study_v0_vs_v1 as V  # noqa: E402

REPO = ROOT.parent
OUT = REPO / "results/docmismatch/troubleshoot_v0_vs_v1"


def pct(x):
    return "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{100 * x:.0f}%"


def num(s, k, kind="min"):
    if s.get("n", 0) == 0:
        return "n/a"
    return {"min": f"{s[k]:.0f}", "pct": pct(s[k]), "num": f"{s[k]:.1f}"}[kind]


def cell_text(c):
    return f"{c.rel} / {c.mix} / {c.cover}"


def wcost(e):
    v = e["wrong_cost"]
    return {"DOMINATES": "v1 ahead on both", "DOMINATED": "v0 ahead on both"}.get(e["break_even"]) or (f"{v:.0f} min (v1 wins above)" if e["break_even"] == "SLOWER-MORE" else f"{v:.0f} min (v1 wins below)")


def report(results, analyses, gates, enforced, n, wall):
    L = ["# The v1 tool against the tool as it was before (v0), on the same complaints (Addendum 29)", "",
         f"Addendum 27's episodes and simulated answers, {len(analyses)} cells x {n} episodes. `v0` is the v0-equivalent tree of v1 (the old tool: two lumps and the four v0 checks, tau 0.95, 12 checks, no bits-per-minute stop) with the data of T1; "
         "`v1` is Addendum 27's tool at T1, T2, T2+access and T3. v0 can answer only in its four lumps, so accuracy is at v0's level (the leading cause at the end, whether or not concluded); v1's exact-cause accuracy is shown for context. "
         "Everything is simulated from the tool's own model family with placeholder numbers; nothing here is evidence about real technicians.", "",
         "## Gates", "", "| gate | result | detail |", "|---|---|---|"]
    for g, (ok, d) in gates.items():
        L.append(f"| {g} | {'PASS' if ok else 'FAIL'} | {d} |")
    if not enforced:
        L += ["", "**SMOKE RUN: gates are not enforced and the numbers below are meaningless.**"]
    if enforced and not all(ok for ok, _ in gates.values()):
        return "\n".join(L + ["", "## NO RESULT (a gate failed)"])
    pc = T.cell_of(analyses, **T.PRIMARY) if any(a["cell"].is_primary for a in analyses) else analyses[0]
    S_ = pc["sum"]
    for sub, title, n_sub in (("hw", "hardware / configuration-cause episodes", pc["n_hw"]), ("doc", "episodes where the drawings are wrong", pc["n_doc"])):
        L += ["", f"## Primary cell ({cell_text(pc['cell'])}), {title} (n = {n_sub}), accuracy at v0's level", "",
              "| policy | minutes | checks | entries typed | reach 0.95 | accuracy (v0 level) | wrong-and-confident | v1 exact accuracy |", "|---|---|---|---|---|---|---|---|"]
        s = S_[("v0", sub)]
        L.append(f"| v0 (before) | {num(s, 'minutes')} | {num(s, 'checks', 'num')} | {num(s, 'entries', 'num')} | {num(s, 'concluded', 'pct')} | {num(s, 'accuracy', 'pct')} | {num(s, 'wrong_confident', 'pct')} | n/a |")
        for arm in V.V1_ARMS:
            s, e = S_[("v1", arm, sub, "v0")], S_[("v1", arm, sub, "exact")]
            L.append(f"| v1 at {arm} | {num(s, 'minutes')} | {num(s, 'checks', 'num')} | {num(s, 'entries', 'num')} | {num(s, 'concluded', 'pct')} | {num(s, 'accuracy', 'pct')} | {num(s, 'wrong_confident', 'pct')} | {num(e, 'accuracy', 'pct')} |")
        L.append(f"| constant guess 'the box acts, cause elsewhere' | | | | | {pct(S_[('baseline', sub)]['accuracy'])} | | |")
    L += ["", "## v1 minus v0 over the 12 cells (same episodes, v0's level)", "",
          "Labels are Addendum 21's (IMPROVES / WORSE / TRADE / NEITHER at 5% minutes and 0.02 accuracy, paired 95% intervals); TRADE in brackets: v1 faster but less accurate (F/L) or slower but more accurate (S/M); "
          "SAFETY REG = share of cells where v1's wrong-and-confident rate is at least 0.02 higher (GAIN: lower). Last column: break-even cost of a wrong diagnosis on the primary cell.", "",
          "| v1 arm | subset | IMPROVES | WORSE | TRADE (F/L, S/M) | NEITHER | SAFETY REG / GAIN | primary: d minutes | d checks | d accuracy | d wrong-and-confident | break-even |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for sub in V.SUBSETS:
        for arm in V.V1_ARMS:
            key = (arm, sub)
            if key not in pc["cmp"]:
                continue
            sh, e = V.shares(analyses, key), pc["cmp"][key]
            L.append(f"| {arm} | {'hardware' if sub == 'hw' else 'drawings wrong'} | {pct(sh['IMPROVES'])} | {pct(sh['WORSE'])} | {pct(sh['TRADE'])} ({pct(sh['FASTER_LESS'])}, {pct(sh['SLOWER_MORE'])}) | {pct(sh['NEITHER'])} | "
                     f"{pct(sh['SAFETY_REGRESSION'])} / {pct(sh['SAFETY_GAIN'])} | {e['d_min']:+.0f} ({100 * e['r_min']:+.0f}%) | {e['d_checks']:+.1f} | {e['d_acc']:+.3f} | {e['d_wc']:+.3f} | {wcost(e)} |")
    L += ["", "## Every cell, hardware episodes: minutes / checks / accuracy at v0's level, v0 | v1 at T1 | v1 at T3", "", "| reliability / mix / coverage | v0 | v1 at T1 | v1 at T3 |", "|---|---|---|---|"]
    for a in analyses:
        s0, s1, s3 = a["sum"][("v0", "hw")], a["sum"][("v1", "T1", "hw", "v0")], a["sum"][("v1", "T3", "hw", "v0")]
        f = lambda s: f"{num(s, 'minutes')} / {num(s, 'checks', 'num')} / {num(s, 'accuracy', 'pct')}"  # noqa: E731
        L.append(f"| {cell_text(a['cell'])} | {f(s0)} | {f(s1)} | {f(s3)} |")
    if any(a["cell"].is_primary for a in analyses) and len(analyses) == len(T.all_cells()):
        L += ["", "## Predictions (written before the run; each strict)", "", "| prediction | holds | values |", "|---|---|---|"]
        for k, p in V.predictions(analyses).items():
            L.append(f"| {k} | {'holds' if p['holds'] else 'does not hold'} | {p['values']} |")
    L += ["", f"Run time {wall:.0f} s."]
    return "\n".join(L)


def write_csv(path, analyses):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cell", "rel", "mix", "cover", "policy", "arm", "subset", "level", "n", "minutes", "accuracy", "wrong_confident", "checks", "entries", "concluded"])
        for a in analyses:
            c = a["cell"]
            for key, s in a["sum"].items():
                if s.get("n", 0) == 0 or key[0] == "baseline":
                    continue
                pol, arm, sub, level = (key[0], "T1", key[1], "v0") if key[0] == "v0" else key
                w.writerow([a["idx"], c.rel, c.mix, c.cover, pol, arm, sub, level, s["n"]] + [f"{s[k]:.4f}" for k in ("minutes", "accuracy", "wrong_confident", "checks", "entries", "concluded")])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--workers", type=int)
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    cells, n = list(enumerate(T.all_cells())), V.N_EPISODES
    if a.smoke:
        cells, n = cells[:2], 20
    results = V.compute_cells(cells, n, a.workers)
    (a.out / "v0_vs_v1_raw.pkl").write_bytes(pickle.dumps(results))
    analyses = [V.analyze_cell(r) for r in results]
    gates = {"G1 code path": V.gate_g1(results, None if a.smoke else V.RAW27), "G2 accounting": V.gate_g2(results), "G3 reproducibility": V.gate_g3(results, min(50, n)),
             "G4 completeness": V.gate_g4(results, expected_idx=[r["idx"] for r in results] if a.smoke else None)}
    text = report(results, analyses, gates, not a.smoke, n, time.time() - t0)
    (a.out / "v0_vs_v1_report.md").write_text(text + "\n")
    (a.out / "v0_vs_v1_analysis.pkl").write_bytes(pickle.dumps(analyses))
    write_csv(a.out / "v0_vs_v1_cells.csv", analyses)
    print(f"wrote {a.out / 'v0_vs_v1_report.md'}; gates: " + ", ".join(f"{g.split()[0]} {'PASS' if ok else 'FAIL'}" for g, (ok, _) in gates.items()))
    if not a.smoke and not all(ok for ok, _ in gates.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
