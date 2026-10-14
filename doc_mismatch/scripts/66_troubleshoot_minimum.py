"""How does the tool do with only the minimum data it needs? (PREREGISTRATION_DR.md Addendum 23.) Layouts real (Mortar Brick metadata only); errors and answers simulated.
100 cells = 2 worlds (errors local / anywhere) x 2 candidate caps (8, 40) x 25 buildings, 300 paired episodes x 6 policies each (`entropy`, `habit_A`, `habit_B` at level min = equipment list and
claims only, and level grouped = Addendum 20's setting).
  .venv/bin/python doc_mismatch/scripts/66_troubleshoot_minimum.py                 # the pre-registered run
  .venv/bin/python doc_mismatch/scripts/66_troubleshoot_minimum.py --smoke --out /some/scratch/dir    # plumbing check on 3 buildings; gates not enforced; numbers meaningless
Raw results are pickled first; the report can be regenerated from the pickle. A failed gate means NO RESULT.
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
from docmismatch.troubleshoot import study_minimum as SM  # noqa: E402
from docmismatch.troubleshoot import study_real as SR  # noqa: E402

REPO = ROOT.parent
DATA = REPO / "data_cache"
OUT = REPO / "results/docmismatch/troubleshoot_minimum"
WORLD_TEXT = {"local": "errors local", "anywhere": "errors anywhere"}


def pct(x):
    return "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{100 * x:.0f}%"


def cell_text(cells, p):
    m = lambda k: float(np.mean([a["summary"][p][k] for a in cells]))  # noqa: E731
    return f"{m('minutes'):.0f} / {pct(m('accuracy'))} / {pct(m('actionable'))} / {pct(m('wrong_confident'))} / {pct(m('unresolved'))} / {pct(m('off_list'))}"


def report(results, analyses, gates, meta, enforced, n, wall):
    L = ["# The tool with only the minimum data it needs (Addendum 23)", "",
         f"Layouts: {len(meta)} real Mortar buildings (Brick metadata only); errors and the technician's answers are SIMULATED from the tool's own model family. {len(analyses)} cells = 2 worlds x 2 candidate caps x "
         f"{len(meta)} buildings, {n} paired episodes x {len(SM.POLICIES)} policies each. Level MIN = the equipment list and the drawings' claims only: no area for any box, so the candidate list is the documented box "
         "then the other boxes in identifier order, capped at K, all equally likely. Level GROUPED = Addendum 20's setting (same air handler first, weights 1 and 0.25). The TRUE cause is drawn over ALL boxes of the "
         "building; a wrong feeder that is not on the tool's list counts as 'unlisted' for that policy (the OFF-LIST share). In the LOCAL world a wrong feeder is likely on the same air handler; in the ANYWHERE world "
         "it is equally likely to be any box. `habit_A` and `habit_B` are ASSUMED stand-ins for trial and error, not real technicians. Minutes are placeholders: only orderings and ratios mean anything. "
         "Nothing here is evidence about real technicians or real drawings.", "", "## Gates", "", "| gate | result | detail |", "|---|---|---|"]
    for g, (ok, d) in gates.items():
        L.append(f"| {g} | {'PASS' if ok else 'FAIL'} | {d} |")
    if not enforced:
        L += ["", "**SMOKE RUN: gates are not enforced and the numbers below are meaningless.**"]
    if enforced and not all(ok for ok, _ in gates.values()):
        return "\n".join(L + ["", "## NO RESULT (a gate failed)"])
    caps, worlds = list(SM.CAPS), list(SM.WORLDS)
    L += ["", "## Means over buildings: minutes / accuracy / actionable / wrong-and-confident / unresolved / off-list share", "",
          "Accuracy counts a correct 'unlisted' as right; ACTIONABLE = right and the answer names a cause (not 'unlisted'), i.e. the technician knows what to do.", "",
          "| world | cap | policy | min (equipment list + claims only) | grouped (Addendum 20's setting) |", "|---|---|---|---|---|"]
    for w in worlds:
        for c in caps:
            cells = SM.group_cells(analyses, w, c)
            for k in SM.KINDS:
                L.append(f"| {WORLD_TEXT[w]} | {c} | {k} | {cell_text(cells, SM.name_of(k, 'min'))} | {cell_text(cells, SM.name_of(k, 'grouped'))} |")
    L += ["", "## What grouping is worth to the tool (grouped against min, same episodes)", "",
          "Labels are Addendum 21's (5% minutes, 0.02 accuracy, paired intervals); IMPROVES means grouping is better. Deltas are grouped minus min, mean over buildings.", "",
          "| world | cap | IMPROVES | WORSE | TRADE | NEITHER | d minutes | d accuracy | d actionable | d off-list share |", "|---|---|---|---|---|---|---|---|---|---|"]
    for w in worlds:
        for c in caps:
            cells = SM.group_cells(analyses, w, c)
            labs = [a["grp"]["label"] for a in cells]
            fr = [labs.count(x) / len(labs) for x in ("IMPROVES", "WORSE", "TRADE", "NEITHER")]
            d = {k: float(np.mean([a["grp"][k] for a in cells])) for k in ("d_min", "d_acc", "d_act", "d_off")}
            L.append(f"| {WORLD_TEXT[w]} | {c} | " + " | ".join(pct(x) for x in fr) + f" | {d['d_min']:+.1f} | {d['d_acc']:+.3f} | {d['d_act']:+.3f} | {d['d_off']:+.3f} |")
    L += ["", "## The tool against the two habits, within a level (share of buildings; context, no verdict)", "",
          "Addendum 19's label against BOTH habits (WINS / LOSES), then against each habit: WINS / LOSES / BUYS ACCURACY (Addendum 20's secondary label).", "",
          "| world | cap | level | vs both: WINS / LOSES | vs habit_A: WINS / LOSES / BUYS ACC | vs habit_B: WINS / LOSES / BUYS ACC |", "|---|---|---|---|---|---|"]
    for w in worlds:
        for c in caps:
            cells = SM.group_cells(analyses, w, c)
            for lv in SM.LEVELS:
                wf, lf = S.map_fractions([a["ctx"][lv] for a in cells])
                per = []
                for h in ("habit_A", "habit_B"):
                    labs = [a["ctx"][f"{lv}|{h}"]["secondary"] for a in cells]
                    per.append(" / ".join(pct(labs.count(x) / len(labs)) for x in ("WINS", "LOSES", "BUYS ACCURACY")))
                L.append(f"| {WORLD_TEXT[w]} | {c} | {lv} | {pct(wf)} / {pct(lf)} | {per[0]} | {per[1]} |")
    L += ["", "## Per building, errors anywhere, K40 (level min): how coverage falls with building size", "",
          "| building | rooms | boxes | off-list share | entropy minutes / accuracy / actionable | habit_A minutes / accuracy | habit_B minutes / accuracy |", "|---|---|---|---|---|---|---|"]
    rows = sorted(((r["boxes"], a, r) for a, r in zip(analyses, results) if a["cell"].world == "anywhere" and a["cell"].cap == "K40"), key=lambda t: t[0])
    for boxes, a, r in rows:
        s = a["summary"]
        e, ha, hb = s[SM.name_of("entropy", "min")], s[SM.name_of("habit_A", "min")], s[SM.name_of("habit_B", "min")]
        L.append(f"| {a['cell'].building} | {r['rooms']} | {boxes} | {pct(e['off_list'])} | {e['minutes']:.0f} / {pct(e['accuracy'])} / {pct(e['actionable'])} | {ha['minutes']:.0f} / {pct(ha['accuracy'])} | {hb['minutes']:.0f} / {pct(hb['accuracy'])} |")
    pr = SM.min_predictions(analyses)
    txt = {"P1": "local world: entropy@min has a higher off-list share and more minutes than entropy@grouped, at each cap", "P2": "anywhere world: entropy@min is within 10% of entropy@grouped in minutes and within 0.02 in off-list share, at each cap",
           "P3": "anywhere world: the off-list share of entropy@min is at least 0.08 at K8 and lower at K40", "P4": "entropy@min has higher accuracy than habit_A@min in all four groups",
           "P5": "entropy@min takes fewer minutes than habit_B@min in all four groups"}
    L += ["", "## Predictions written before the run", "", "| | prediction | holds? | values |", "|---|---|---|---|"]
    for k, v in pr.items():
        val = v["values"]
        if k == "P1":
            vs = "; ".join(f"{c}: off-list {om:.3f} vs {og:.3f}, minutes {mm:.1f} vs {mg:.1f}" for c, (om, og, mm, mg) in val.items())
        elif k == "P2":
            vs = "; ".join(f"{c}: minutes {mm:.1f} vs {mg:.1f}, off-list {om:.3f} vs {og:.3f}" for c, (mm, mg, om, og) in val.items())
        elif k == "P3":
            vs = "; ".join(f"{c}: {x:.3f}" for c, x in val.items())
        else:
            vs = "; ".join(f"{w}/{c}: {a:.3f} vs {b:.3f}" if k == "P4" else f"{w}/{c}: {a:.1f} vs {b:.1f}" for (w, c), (a, b) in val.items())
        L.append(f"| {k} | {txt[k]} | **{'holds' if v['holds'] else 'does not hold'}** | {vs} |")
    L += ["", f"Wall clock {wall:.0f} s. Cells are classified from point estimates and a paired bootstrap; some cells are misclassified by chance and no p-value is claimed. Limitations are in Addendum 23."]
    return "\n".join(L)


def write_csv(path, analyses):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["world", "cap", "building", "cell"] + [f"{p}_{k}" for p in SM.POLICIES for k in ("minutes", "accuracy", "actionable", "wrong_confident", "unresolved", "off_list")] + ["grouped_vs_min_label"])
        for a in analyses:
            c = a["cell"]
            w.writerow([c.world, c.cap, c.building, a["idx"]] + [round(a["summary"][p][k], 4) for p in SM.POLICIES for k in ("minutes", "accuracy", "actionable", "wrong_confident", "unresolved", "off_list")] + [a["grp"]["label"]])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--n", type=int, default=None)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    n = a.n or (20 if a.smoke else SM.N_EPISODES)
    t0 = time.time()
    computed = R.eligible(DATA)
    if tuple(computed) != R.FROZEN_BUILDINGS:
        sys.exit(f"the eligible buildings differ from the frozen list: {computed}")
    layouts, meta, censuses = {}, {}, {}
    for b in R.FROZEN_BUILDINGS:
        censuses[b] = C.parse_census(DATA / f"mortar__{b}.ttl", b)
        layouts[b], meta[b] = R.layout_from_census(censuses[b])
    names = list(R.FROZEN_BUILDINGS)[:3] if a.smoke else list(R.FROZEN_BUILDINGS)
    every = SM.all_min_cells(list(R.FROZEN_BUILDINGS))
    cells = [(i, c) for i, c in enumerate(every) if c.building in names]
    raw_f = a.out / "minimum_raw.pkl"
    if raw_f.exists():
        results = pickle.loads(raw_f.read_bytes())
        print("loaded raw results from cache", flush=True)
    else:
        results = SM.compute_min_cells([(i, c, layouts[c.building]) for i, c in cells], n=n, workers=a.workers)
        raw_f.write_bytes(pickle.dumps(results))
        print(f"computed {len(results)} cells x {n} episodes in {time.time() - t0:.0f}s", flush=True)
    r0 = results[0]
    k = min(50, r0["n"])
    r1 = SM.run_min_cell(r0["idx"], r0["cell"], layouts[r0["cell"].building], n=k)
    g4 = all(np.array_equal(r1["policy"][p][key], r0["policy"][p][key][:k]) for p in SM.POLICIES for key in ("minutes", "checks", "correct", "concluded", "guess_idx", "truth_idx", "off_list", "named"))
    problems = [p for b in names for p in R.layout_problems(b, layouts[b], censuses[b])]
    gates = {"G1 code path (no grouping information: levels identical)": SM.gate_g1_min(layouts[names[0]]), "G2 accounting": SR.gate_g2_real(layouts[names[0]]),
             "G3 coverage bookkeeping": SM.gate_g3_coverage(results, layouts), "G4 reproducibility": (g4, f"cell {r0['idx']}: first {k} episodes reproduced" if g4 else "mismatch"),
             "G5 completeness and pairing": SM.g5_complete_min(results, n_cells=len(cells), expected_idx=[i for i, _ in cells]), "G6 layout fidelity": (not problems, f"{len(names)} buildings" if not problems else "; ".join(problems[:3]))}
    analyses = [SM.analyze_min_cell(r) for r in results]
    (a.out / "minimum_analysis.pkl").write_bytes(pickle.dumps(analyses))
    md = report(results, analyses, gates, {b: meta[b] for b in names}, enforced=not a.smoke, n=n, wall=time.time() - t0)
    (a.out / "minimum_report.md").write_text(md)
    write_csv(a.out / "minimum_cells.csv", analyses)
    print("gates:", {g.split(" ")[0]: v[0] for g, v in gates.items()}, "| report written", flush=True)
    if not a.smoke and not all(ok for ok, _ in gates.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
