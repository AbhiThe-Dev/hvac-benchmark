"""The troubleshooting tool on the documented layouts of 25 real Mortar buildings (PREREGISTRATION_DR.md Addendum 20). Layouts real (Brick metadata only); errors and answers simulated.
150 cells = 3 worlds x 2 candidate regimes x 25 buildings, 500 paired episodes x 5 policies each.
  .venv/bin/python doc_mismatch/scripts/63_troubleshoot_real_maps.py                 # the pre-registered run
  .venv/bin/python doc_mismatch/scripts/63_troubleshoot_real_maps.py --smoke --out /some/scratch/dir    # plumbing check on 3 buildings; gates not enforced; numbers meaningless
Raw results are pickled first; the report can be regenerated from the pickle. A failed gate means NO MAP.
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
from docmismatch import census as C  # noqa: E402
from docmismatch.troubleshoot import realmaps as R  # noqa: E402
from docmismatch.troubleshoot import study as S  # noqa: E402
from docmismatch.troubleshoot import study_real as SR  # noqa: E402

REPO = ROOT.parent
DATA = REPO / "data_cache"
OUT = REPO / "results/docmismatch/troubleshoot_real"


def pct(x):
    return "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{100 * x:.0f}%"


def report(results, analyses, gates, meta, enforced, n, wall):
    L = ["# The troubleshooting tool on real documented layouts (Addendum 20)", "",
         f"Layouts: {len(meta)} real Mortar buildings (Brick metadata only); errors and the technician's answers are SIMULATED from the tool's own model family. {len(analyses)} cells = 3 worlds x 2 candidate regimes x "
         f"{len(meta)} buildings, {n} paired episodes x {len(S.POLICIES)} policies each. The tool always runs on its ASSUMED default settings; every policy is charged the TRUE minutes. `habit_A` and `habit_B` are ASSUMED stand-ins "
         "for trial and error. Minutes are placeholders: only orderings and ratios mean anything. The Brick graphs carry no location, so 'same air handler' stands in for 'nearby' and identifier order stands in for adjacency. "
         "Nothing here is evidence about real technicians or real documentation errors.", "", "## Gates", "", "| gate | result | detail |", "|---|---|---|"]
    for g, (ok, d) in gates.items():
        L.append(f"| {g} | {'PASS' if ok else 'FAIL'} | {d} |")
    if not enforced:
        L += ["", "**SMOKE RUN: gates are not enforced and the numbers below are meaningless.**"]
    if enforced and not all(ok for ok, _ in gates.values()):
        return "\n".join(L + ["", "## NO MAP (a gate failed)"])
    g = SR.groups(analyses)
    L += ["", "## The map, per (world, regime) and tool policy (against BOTH habits; Addendum 19's rule)", "", "| world | regime | policy | WINS | LOSES | NEITHER | reading |", "|---|---|---|---|---|---|---|"]
    for (w, r), grp in g.items():
        for t in S.TOOL:
            wf, lf, lab = SR.group_reading(grp, t)
            L.append(f"| {w} | {r} | {t} | {pct(wf)} | {pct(lf)} | {pct(1 - wf - lf)} | {lab} |")
    L += ["", "All cells pooled:", "", "| policy | WINS | LOSES | reading |", "|---|---|---|---|"]
    for t in S.TOOL:
        wf, lf = S.map_fractions([a["label"][t] for a in analyses])
        L.append(f"| {t} | {pct(wf)} | {pct(lf)} | **{S.map_reading(wf, lf)}** |")
    L += ["", "## Against each habit separately, with the secondary BUYS ACCURACY label (fraction of buildings)", "", "| world | regime | policy | vs habit_A: WINS / LOSES / BUYS ACCURACY | vs habit_B: WINS / LOSES / BUYS ACCURACY |", "|---|---|---|---|---|"]
    for (w, r), grp in g.items():
        for t in ("entropy", "split_half"):
            cells = []
            for h in S.HABITS:
                labs = [SR.secondary_label(a["cmp"][f"{t}|{h}"]) for a in grp]
                cells.append(" / ".join(pct(labs.count(x) / len(labs)) for x in ("WINS", "LOSES", "BUYS ACCURACY")))
            L.append(f"| {w} | {r} | {t} | {cells[0]} | {cells[1]} |")
    L += ["", "## Means over buildings: minutes / accuracy / wrong-and-confident / unresolved / entries", "", "| world | regime | " + " | ".join(S.POLICIES) + " |", "|---|---|" + "---|" * len(S.POLICIES)]
    for (w, r), grp in g.items():
        cols = []
        for p in S.POLICIES:
            m = lambda k: float(np.mean([a["summary"][p][k] for a in grp]))  # noqa: E731
            cols.append(f"{m('minutes'):.0f} / {pct(m('accuracy'))} / {pct(m('wrong_confident'))} / {pct(m('unresolved'))} / {m('entries'):.1f}")
        L.append(f"| {w} | {r} | " + " | ".join(cols) + " |")
    L += ["", "## Per building, W_default: rooms, boxes, handlers; mean candidates; minutes / accuracy of entropy, habit_A, habit_B; label (vs both)", "",
          "| building | rooms | boxes | handlers | regime | K | entropy | habit_A | habit_B | label |", "|---|---|---|---|---|---|---|---|---|---|"]
    by_cell = {(a["cell"].world, a["cell"].regime, a["cell"].building): (a, r) for a, r in zip(analyses, results)}
    for b in meta:
        for reg in SR.REGIMES:
            if ("W_default", reg, b) not in by_cell:
                continue
            a, r = by_cell[("W_default", reg, b)]
            s = a["summary"]
            m = meta[b]
            L.append(f"| {b} | {m.rooms} | {m.boxes} | {m.handlers} | {reg} | {r['K'].mean():.1f} | " + " | ".join(f"{s[p]['minutes']:.0f} / {pct(s[p]['accuracy'])}" for p in ("entropy", "habit_A", "habit_B")) + f" | {a['label']['entropy']} |")
    L += ["", "## Candidates and minutes (mean over cells; entropy, minutes)", "", "| regime | mean candidates | cells | entropy | habit_A | habit_B |", "|---|---|---|---|---|---|"]
    for reg in SR.REGIMES:
        rows = [(r["K"].mean(), a) for a, r in zip(analyses, results) if a["cell"].regime == reg]
        for lo, hi in ((0, 8.5), (8.5, 20.5), (20.5, 41)):
            sel = [a for k, a in rows if lo < k <= hi]
            if sel:
                L.append(f"| {reg} | {lo:.0f}-{hi:.0f} | {len(sel)} | " + " | ".join(f"{np.mean([a['summary'][p]['minutes'] for a in sel]):.0f}" for p in ("entropy", "habit_A", "habit_B")) + " |")
    pr = SR.real_predictions(analyses)
    txt = {"P1": "entropy WINS in 0% of buildings in each of W_default and W_stress x both regimes", "P2": "vs habit_B alone, entropy's WINS fraction is higher in W_documented than in W_default and W_stress",
           "P3": "vs habit_B alone, entropy's WINS fraction is higher in R_wide than in R_narrow", "P4": "entropy's wrong-and-confident rate is higher in W_stress than in W_default, in both regimes",
           "P5": "entropy's accuracy exceeds habit_A's in each of the six groups"}
    L += ["", "## Predictions written before the run", "", "| | prediction | holds? | values |", "|---|---|---|---|"]
    for k, v in pr.items():
        vals = "; ".join(f"{kk}: {vv if not isinstance(vv, (float, tuple)) else (f'{vv:.3f}' if isinstance(vv, float) else tuple(round(float(x), 3) for x in vv))}" for kk, vv in v["values"].items())
        L.append(f"| {k} | {txt[k]} | **{'holds' if v['holds'] else 'does not hold'}** | {vals} |")
    L += ["", f"Wall clock {wall:.0f} s. Cells are classified from point estimates and a paired bootstrap on minutes; some cells are misclassified by chance and no p-value is claimed. Limitations are in Addendum 20."]
    return "\n".join(L)


def write_csv(path, analyses, results):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["world", "regime", "building", "cell", "mean_K"] + [f"{p}_{k}" for p in S.POLICIES for k in ("minutes", "accuracy", "checks", "concluded")] + [f"label_{t}" for t in S.TOOL])
        for a, r in zip(analyses, results):
            c = a["cell"]
            w.writerow([c.world, c.regime, c.building, a["idx"], round(float(r["K"].mean()), 2)] + [round(a["summary"][p][k], 4) for p in S.POLICIES for k in ("minutes", "accuracy", "checks", "concluded")] + [a["label"][t] for t in S.TOOL])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--n", type=int, default=None)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    n = a.n or (20 if a.smoke else SR.N_EPISODES)
    t0 = time.time()
    computed = R.eligible(DATA)
    if tuple(computed) != R.FROZEN_BUILDINGS:
        sys.exit(f"the eligible buildings differ from the frozen list: {computed}")
    layouts, meta, censuses = {}, {}, {}
    for b in R.FROZEN_BUILDINGS:
        censuses[b] = C.parse_census(DATA / f"mortar__{b}.ttl", b)
        layouts[b], meta[b] = R.layout_from_census(censuses[b])
    names = list(R.FROZEN_BUILDINGS)[:3] if a.smoke else list(R.FROZEN_BUILDINGS)
    every = SR.all_real_cells(list(R.FROZEN_BUILDINGS))
    cells = [(i, c) for i, c in enumerate(every) if c.building in names]
    raw_f = a.out / "real_raw.pkl"
    if raw_f.exists():
        results = pickle.loads(raw_f.read_bytes())
        print("loaded raw results from cache", flush=True)
    else:
        results = SR.compute_real_cells([(i, c, layouts[c.building]) for i, c in cells], n=n, workers=a.workers)
        raw_f.write_bytes(pickle.dumps(results))
        print(f"computed {len(results)} cells x {n} episodes in {time.time() - t0:.0f}s", flush=True)
    first = layouts[names[0]]
    r0 = results[0]
    k = min(50, r0["n"])
    r1 = SR.run_real_cell(r0["idx"], r0["cell"], layouts[r0["cell"].building], n=k)
    g4 = all(np.array_equal(r1["policy"][p][key], r0["policy"][p][key][:k]) for p in S.POLICIES for key in ("minutes", "checks", "correct", "concluded", "guess_idx", "truth_idx"))
    problems = [p for b in names for p in R.layout_problems(b, layouts[b], censuses[b])]
    ok3, v3 = SR.g3_honesty_real(results)
    gates = {"G1 code path": SR.gate_g1_real(first), "G2 accounting": SR.gate_g2_real(first), "G3 honesty (accuracy among concluded >= 0.92, W_default, each regime)": (ok3, ", ".join(f"{r}: {v:.3f}" for r, v in v3.items())),
             "G4 reproducibility": (g4, f"cell {r0['idx']}: first {k} episodes reproduced" if g4 else "mismatch"), "G5 completeness and pairing": S.g5_complete(results, n_cells=len(cells), expected_idx=[i for i, _ in cells]),
             "G6 layout fidelity": (not problems, f"{len(names)} buildings" if not problems else "; ".join(problems[:3]))}
    analyses = [S.analyze_cell(r) for r in results]
    (a.out / "real_analysis.pkl").write_bytes(pickle.dumps(analyses))
    md = report(results, analyses, gates, {b: meta[b] for b in names}, enforced=not a.smoke, n=n, wall=time.time() - t0)
    (a.out / "real_report.md").write_text(md)
    write_csv(a.out / "real_cells.csv", analyses, results)
    print("gates:", {g.split(" ")[0]: v[0] for g, v in gates.items()}, "| report written", flush=True)
    if not a.smoke and not all(ok for ok, _ in gates.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
