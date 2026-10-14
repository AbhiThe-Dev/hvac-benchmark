"""How does the id-weighted tool compare with the fast trial-and-error stand-in when both get the same information? (PREREGISTRATION_DR.md Addendum 26.)
Cached Mortar Brick metadata and simulation only; no download, no external data. The habits are stand-ins I wrote, not real technicians.
250 cells = 5 worlds x 2 caps x 25 buildings of 300 paired episodes x 6 policies: `entropy` on the arbitrary first-K list and on the id-near list weighted by id distance, and `habit_A` (fast)
and `habit_B` (slow, careful) on the first-K list and on the id-near list.
  .venv/bin/python doc_mismatch/scripts/69_troubleshoot_fast.py                 # the pre-registered run
  .venv/bin/python doc_mismatch/scripts/69_troubleshoot_fast.py --smoke --out /some/scratch/dir    # plumbing check on 3 buildings; gates not enforced; numbers meaningless
Raw results are pickled first; the report can be regenerated from the pickle. A failed gate means NO RESULT. Needs Addenda 23 and 25's raw results.
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
from docmismatch.troubleshoot import study_fast as FA  # noqa: E402
from docmismatch.troubleshoot import study_real as SR  # noqa: E402

REPO = ROOT.parent
DATA = REPO / "data_cache"
OUT = REPO / "results/docmismatch/troubleshoot_fast"
A23 = REPO / "results/docmismatch/troubleshoot_minimum/minimum_raw.pkl"
A25 = REPO / "results/docmismatch/troubleshoot_idweight/idweight_raw.pkl"
WORLD_TEXT = {"local": "errors local (same air handler)", "anywhere": "errors anywhere", "idlocal2": "ASSUMED adjacent-room errors (lambda 2)", "idlocal4": "ASSUMED nearby-room errors (lambda 4)",
              "idlocal8": "ASSUMED nearby-room errors (lambda 8)"}


def pct(x):
    return "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{100 * x:.0f}%"


def report(analyses, gates, enforced, n, wall):
    caps = list(FA.CAPS)
    L = ["# The id-weighted tool against the fast and the slow stand-in technician (Addendum 26)", "",
         f"25 real Mortar buildings (Brick metadata only, cached; no download); {len(analyses)} cells = 5 worlds x 2 caps x 25 buildings, {n} paired episodes x {len(FA.POLICIES)} policies. "
         "**HABIT_A ('the fast technician') and HABIT_B ('the slow, careful technician') are stand-ins I wrote, not real technicians**: they use no symptoms and no knowledge of the building beyond the ORDER of the candidate "
         "list, and stop at the first yes. To be fair they get the same candidates as the tool: on the id-near list ('idnear') they check the nearest boxes first; on the arbitrary list ('min') the first boxes of the "
         "equipment list. The tool with the id-weighted list is 'idw4' (weight decay 4, a placeholder). The tool stops after 12 checks and the habits run to exhaustion, which flatters the tool on minutes in visits that "
         "no list resolves. The three ASSUMED worlds put wrong feeders near the documented box in id order and favour id-ordered lists BY CONSTRUCTION, for the habits as much as for the tool. Minutes and hit rates are "
         "placeholders. Nothing here is evidence about real technicians.", "", "## Gates", "", "| gate | result | detail |", "|---|---|---|"]
    for g, (ok, d) in gates.items():
        L.append(f"| {g} | {'PASS' if ok else 'FAIL'} | {d} |")
    if not enforced:
        L += ["", "**SMOKE RUN: gates are not enforced and the numbers below are meaningless.**"]
    if enforced and not all(ok for ok, _ in gates.values()):
        return "\n".join(L + ["", "## NO RESULT (a gate failed)"])
    L += ["", "## Means over buildings: minutes / accuracy / actionable / wrong-and-confident / unresolved / mean checks", "",
          "ACTIONABLE = right and names a cause (not 'unlisted'); accuracy counts a correct 'unlisted' as right.", "", "| world | cap | " + " | ".join(FA.POLICIES) + " |", "|---|---|" + "---|" * len(FA.POLICIES)]
    for w in FA.WORLDS:
        for c in caps:
            cells = FA.group_cells(analyses, w, c)
            cols = []
            for p in FA.POLICIES:
                m = lambda k: FA.gmean(cells, p, k)  # noqa: E731
                cols.append(f"{m('minutes'):.0f} / {pct(m('accuracy'))} / {pct(m('actionable'))} / {pct(m('wrong_confident'))} / {pct(m('unresolved'))} / {m('checks'):.1f}")
            L.append(f"| {WORLD_TEXT[w]} | {c} | " + " | ".join(cols) + " |")
    L += ["", "## The tool against each habit (share of buildings; Addendum 19's classification and Addendum 20's BUYS ACCURACY label)", "",
          "WINS = the tool is at least 10% faster at no less than 0.02 lower accuracy; LOSES = at least 10% slower with no accuracy gain of 0.02; BUYS ACCURACY = at least 10% slower but at least 0.05 more accurate "
          "with the paired interval above 0. r = the tool's minutes relative to the habit's (mean over buildings; negative = the tool is faster).", "",
          "| world | cap | comparison | WINS | LOSES | BUYS ACCURACY | NEITHER | r minutes | d accuracy |", "|---|---|---|---|---|---|---|---|---|"]
    for w in FA.WORLDS:
        for c in caps:
            cells = FA.group_cells(analyses, w, c)
            for t, h in FA.PAIRS:
                labs = [a["cmp"][f"{t}|{h}"]["secondary"] for a in cells]
                r = float(np.mean([a["cmp"][f"{t}|{h}"]["r_min"] for a in cells]))
                d = float(np.mean([a["cmp"][f"{t}|{h}"]["d_acc"] for a in cells]))
                L.append(f"| {WORLD_TEXT[w]} | {c} | {t} vs {h} | " + " | ".join(pct(labs.count(x) / len(labs)) for x in ("WINS", "LOSES", "BUYS ACCURACY", "NEITHER")) + f" | {100 * r:+.0f}% | {d:+.3f} |")
    L += ["", "## Against BOTH habits (Addendum 19's `combine`: WINS only if it wins against each, LOSES if it loses against either), share of buildings", "",
          "| world | cap | " + " | ".join(FA.COMBOS) + " |", "|---|---|" + "---|" * len(FA.COMBOS)]
    for w in FA.WORLDS:
        for c in caps:
            cells = FA.group_cells(analyses, w, c)
            cols = []
            for k in FA.COMBOS:
                labs = [a["combo"][k] for a in cells]
                cols.append(" / ".join(f"{pct(labs.count(x) / len(labs))} {x.lower()}" for x in ("WINS", "LOSES", "NEITHER")))
            L.append(f"| {WORLD_TEXT[w]} | {c} | " + " | ".join(cols) + " |")
    L += ["", "## What the habits gain from the id-near list (habit on idnear minus habit on min; means over buildings)", "", "| world | cap | habit | d minutes | d accuracy | d actionable |", "|---|---|---|---|---|---|"]
    for w in FA.WORLDS:
        for c in caps:
            cells = FA.group_cells(analyses, w, c)
            for a_, b_ in FA.GAINS:
                key = f"{a_}|{b_}"
                d = {k: float(np.mean([x["gain"][key][k] for x in cells])) for k in ("d_min", "d_acc", "d_act")}
                L.append(f"| {WORLD_TEXT[w]} | {c} | {a_.split('@')[0]} | {d['d_min']:+.1f} | {d['d_acc']:+.3f} | {d['d_act']:+.3f} |")
    pr = FA.fast_predictions(analyses)
    txt = {"P1": "the fast stand-in (habit_A on the id-near list) is faster than the tool (idw4) in all 10 groups", "P2": "the tool is more accurate than habit_A@idnear in all 10 groups",
           "P3": "the tool's wrong-and-confident rate is at least 0.05 below habit_A@idnear's in all 10 groups", "P4": "the tool is faster than the slow stand-in (habit_B@idnear) in all 10 groups",
           "P5": "in the lambda 2 world at both caps habit_A@idnear's actionable rate is at least 0.03 above habit_A@min's"}
    L += ["", "## Predictions written before the run", "", "| | prediction | holds? | values |", "|---|---|---|---|"]
    for k, v in pr.items():
        val = v["values"]
        if k == "P5":
            vs = "; ".join(f"{c}: {a:.3f} vs {b:.3f}" for c, (a, b) in val.items())
        else:
            margin = {"P1": lambda a, b: b - a, "P2": lambda a, b: a - b, "P3": lambda a, b: b - a, "P4": lambda a, b: b - a}[k]      # positive = as predicted
            worst = min(val.items(), key=lambda kv: margin(*kv[1]))
            vs = f"smallest margin {margin(*worst[1]):+.3f} at {worst[0][0]}/{worst[0][1]} ({worst[1][0]:.3f} vs {worst[1][1]:.3f})"
        L.append(f"| {k} | {txt[k]} | **{'holds' if v['holds'] else 'does not hold'}** | {vs} |")
    L += ["", f"Wall clock {wall:.0f} s. Cells are classified from point estimates and a paired bootstrap; some cells are misclassified by chance and no p-value is claimed. Limitations are in Addendum 26."]
    return "\n".join(L)


def write_csv(path, analyses):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["world", "cap", "building", "cell"] + [f"{p}_{k}" for p in FA.POLICIES for k in ("minutes", "accuracy", "actionable", "wrong_confident", "unresolved", "checks")] + [f"{t}_vs_{h}" for t, h in FA.PAIRS])
        for a in analyses:
            c = a["cell"]
            w.writerow([c.world, c.cap, c.building, a["idx"]] + [round(a["summary"][p][k], 4) for p in FA.POLICIES for k in ("minutes", "accuracy", "actionable", "wrong_confident", "unresolved", "checks")]
                       + [a["cmp"][f"{t}|{h}"]["secondary"] for t, h in FA.PAIRS])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--n", type=int, default=None)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    n = a.n or (20 if a.smoke else FA.N_EPISODES)
    t0 = time.time()
    computed = R.eligible(DATA)
    if tuple(computed) != R.FROZEN_BUILDINGS:
        sys.exit(f"the eligible buildings differ from the frozen list: {computed}")
    layouts, censuses = {}, {}
    for b in R.FROZEN_BUILDINGS:
        censuses[b] = C.parse_census(DATA / f"mortar__{b}.ttl", b)
        layouts[b], _ = R.layout_from_census(censuses[b])
    names = list(R.FROZEN_BUILDINGS)[:3] if a.smoke else list(R.FROZEN_BUILDINGS)
    every = FA.all_fast_cells(list(R.FROZEN_BUILDINGS))
    cells = [(i, c) for i, c in enumerate(every) if c.building in names]
    raw_f = a.out / "fast_raw.pkl"
    if raw_f.exists():
        results = pickle.loads(raw_f.read_bytes())
        print("loaded raw results from cache", flush=True)
    else:
        results = FA.compute_fast_cells([(i, c, layouts[c.building]) for i, c in cells], n=n, workers=a.workers)
        raw_f.write_bytes(pickle.dumps(results))
        print(f"computed {len(results)} cells x {n} episodes in {time.time() - t0:.0f}s", flush=True)
    a23 = pickle.loads(A23.read_bytes()) if A23.exists() else []
    a25 = pickle.loads(A25.read_bytes()) if A25.exists() else []
    r0 = results[0]
    k = min(50, r0["n"])
    r1 = FA.run_fast_cell(r0["idx"], r0["cell"], layouts[r0["cell"].building], n=k)
    g4 = all(np.array_equal(r1["policy"][p][key], r0["policy"][p][key][:k]) for p in FA.POLICIES for key in ("minutes", "checks", "correct", "concluded", "guess_idx", "truth_idx", "off_list", "named"))
    problems = [p for b in names for p in R.layout_problems(b, layouts[b], censuses[b])]
    ok25, d25 = FA.gate_g1_a25(results, a25) if a25 else (False, "Addendum 25's raw results are missing")
    ok23, d23 = FA.gate_g1_a23(results, a23) if a23 else (False, "Addendum 23's raw results are missing")
    okw, dw = FA.gate_habits_ignore_weights(layouts[names[0]])
    okr, dr = SR.gate_g1_real(layouts[names[0]])
    gates = {"G1 code path (tool reproduces Addendum 25, habits reproduce Addendum 23, habits ignore weights)": (ok25 and ok23 and okw and okr, f"{d25}; {d23}; {dw}; {dr}"), "G2 accounting": SR.gate_g2_real(layouts[names[0]]),
             "G3 coverage bookkeeping": FA.gate_g3(results, layouts), "G4 reproducibility": (g4, f"cell {r0['idx']}: first {k} episodes reproduced" if g4 else "mismatch"),
             "G5 completeness and pairing": FA.g5_complete_fast(results, n_cells=len(cells), expected_idx=[i for i, _ in cells]), "G6 layout fidelity": (not problems, f"{len(names)} buildings" if not problems else "; ".join(problems[:3]))}
    analyses = [FA.analyze_fast_cell(r) for r in results]
    (a.out / "fast_analysis.pkl").write_bytes(pickle.dumps(analyses))
    md = report(analyses, gates, enforced=not a.smoke, n=n, wall=time.time() - t0)
    (a.out / "fast_report.md").write_text(md)
    write_csv(a.out / "fast_cells.csv", analyses)
    print("gates:", {g.split(" ")[0]: v[0] for g, v in gates.items()}, "| report written", flush=True)
    if not a.smoke and not all(ok for ok, _ in gates.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
