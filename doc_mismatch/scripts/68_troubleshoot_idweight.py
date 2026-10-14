"""Does weighting the candidates by their distance in id order help the tool find wrong feeders, and is it harmless where errors are not id-local? (PREREGISTRATION_DR.md Addendum 25.)
Cached Mortar Brick metadata and simulation only; no download, no external data.
250 cells = 5 worlds x 2 caps x 25 buildings of 300 paired episodes x 6 policies (`entropy` with the min / idnear / idw2 / idw4 / idw8 / grouped candidate lists).
  .venv/bin/python doc_mismatch/scripts/68_troubleshoot_idweight.py                 # the pre-registered run
  .venv/bin/python doc_mismatch/scripts/68_troubleshoot_idweight.py --smoke --out /some/scratch/dir    # plumbing check on 3 buildings; gates not enforced; numbers meaningless
Raw results are pickled first; the report can be regenerated from the pickle. A failed gate means NO RESULT. Needs Addendum 24's raw results (results/docmismatch/troubleshoot_idproximity).
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
from docmismatch.troubleshoot import study_idweight as IW  # noqa: E402
from docmismatch.troubleshoot import study_real as SR  # noqa: E402

REPO = ROOT.parent
DATA = REPO / "data_cache"
OUT = REPO / "results/docmismatch/troubleshoot_idweight"
A24 = REPO / "results/docmismatch/troubleshoot_idproximity/idproximity_raw.pkl"
WORLD_TEXT = {"local": "errors local (same air handler)", "anywhere": "errors anywhere", "idlocal2": "ASSUMED adjacent-room errors (lambda 2)", "idlocal4": "ASSUMED nearby-room errors (lambda 4)",
              "idlocal8": "ASSUMED nearby-room errors (lambda 8)"}
LEVEL_TEXT = {"min": "min (first K, equal weights)", "idnear": "idnear (id-near list, equal weights)", "idw2": "idw2 (id-near, weight decay 2)", "idw4": "idw4 (id-near, weight decay 4; PRIMARY)",
              "idw8": "idw8 (id-near, weight decay 8)", "grouped": "grouped (same air handler first)"}


def pct(x):
    return "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{100 * x:.0f}%"


def report(results, analyses, gates, enforced, n, wall):
    caps = list(IW.CAPS)
    L = ["# Weighting candidates by id distance (Addendum 25)", "",
         f"25 real Mortar buildings (Brick metadata only, cached; no download); {len(analyses)} cells = 5 worlds x 2 caps x 25 buildings, {n} paired episodes x {len(IW.POLICIES)} policies. The tool's new option "
         "`nearness = 'id'` lists the documented box and the K - 1 boxes nearest to it in natural id order and weights each candidate exp(-distance / decay); IDNEAR is the same list with equal weights (so IDNEAR vs IDW isolates "
         "the weighting); MIN is the arbitrary first-K list; GROUPED needs the air-handler claims too. The true cause is drawn over ALL boxes; a wrong feeder off a policy's list counts as 'unlisted' (OFF-LIST). The three "
         "ASSUMED worlds put wrong feeders near the documented box in id order and favour the id levels BY CONSTRUCTION: they bound what id weighting could buy if errors were that local; they do not show that errors are. "
         "The tool's decay is a placeholder. Minutes are placeholders. Nothing here is evidence about real technicians or real documentation errors.", "", "## Gates", "", "| gate | result | detail |", "|---|---|---|"]
    for g, (ok, d) in gates.items():
        L.append(f"| {g} | {'PASS' if ok else 'FAIL'} | {d} |")
    if not enforced:
        L += ["", "**SMOKE RUN: gates are not enforced and the numbers below are meaningless.**"]
    if enforced and not all(ok for ok, _ in gates.values()):
        return "\n".join(L + ["", "## NO RESULT (a gate failed)"])
    pr = IW.idw_predictions(analyses)
    verdict = IW.decision(pr)
    L += ["", f"## Decision (frozen rule; about keeping the option, never about shipping it): **{verdict}**", "",
          "Kept if P1 (weighting fixes the long list), P3 (harmless when errors are anywhere) and P6 (safe) all hold; P2, P4 and P5 carry no verdict.",
          "", "## The tool with each candidate list: minutes / accuracy / actionable / wrong-and-confident / unresolved / mean checks (means over buildings)", "",
          "ACTIONABLE = right and names a cause (not 'unlisted'); accuracy counts a correct 'unlisted' as right.", "", "| world | cap | " + " | ".join(IW.LEVELS) + " |", "|---|---|" + "---|" * len(IW.LEVELS)]
    for w in IW.WORLDS:
        for c in caps:
            cells = IW.group_cells(analyses, w, c)
            cols = []
            for lv in IW.LEVELS:
                m = lambda k: IW.gmean(cells, lv, k)  # noqa: E731
                cols.append(f"{m('minutes'):.0f} / {pct(m('accuracy'))} / {pct(m('actionable'))} / {pct(m('wrong_confident'))} / {pct(m('unresolved'))} / {m('checks'):.1f}")
            L.append(f"| {WORLD_TEXT[w]} | {c} | " + " | ".join(cols) + " |")
    L += ["", "## Each treatment against its baseline on the same episodes (Addendum 21's labels; deltas are treatment minus baseline, means over buildings)", "",
          "| world | cap | treatment vs baseline | IMPROVES | WORSE | TRADE | NEITHER | d minutes | d accuracy | d actionable | d off-list share |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for w in IW.WORLDS:
        for c in caps:
            cells = IW.group_cells(analyses, w, c)
            for t, b in IW.PAIRS:
                key = f"{t}|{b}"
                labs = [a["cmp"][key]["label"] for a in cells]
                d = {k: float(np.mean([a["cmp"][key][k] for a in cells])) for k in ("d_min", "d_acc", "d_act", "d_off")}
                L.append(f"| {WORLD_TEXT[w]} | {c} | {t} vs {b} | " + " | ".join(pct(labs.count(x) / len(labs)) for x in ("IMPROVES", "WORSE", "TRADE", "NEITHER"))
                         + f" | {d['d_min']:+.1f} | {d['d_acc']:+.3f} | {d['d_act']:+.3f} | {d['d_off']:+.3f} |")
    txt = {"P1": "at K40 in each adjacency world, idw4's actionable rate is above idnear's", "P2": "at K40 in lambda 2 and 4, idw4's actionable rate is at least 0.04 above min's",
           "P3": "anywhere world, both caps: idw4 within 0.01 of min in actionable and at most 0.01 above in wrong-and-confident", "P4": "local world, both caps: idw4's actionable rate is at least idnear's minus 0.005",
           "P5": "at K40 in each adjacency world, idw2 and idw8 also beat idnear in actionable", "P6": "in all 10 (world, cap) groups idw4's wrong-and-confident rate is at most 0.01 above idnear's"}
    L += ["", "## Predictions written before the run", "", "| | prediction | holds? | values |", "|---|---|---|---|"]
    for k, v in pr.items():
        val = v["values"]
        if k == "P1":
            vs = "; ".join(f"{w}: {a:.3f} vs {b:.3f}" for w, (a, b) in val.items())
        elif k == "P2":
            vs = "; ".join(f"{w}: {a:.3f} vs {b:.3f}" for w, (a, b) in val.items())
        elif k == "P3":
            vs = "; ".join(f"{c}: actionable {a:.3f} vs {b:.3f}, wrong-and-confident {wa:.3f} vs {wb:.3f}" for c, (a, b, wa, wb) in val.items())
        elif k == "P4":
            vs = "; ".join(f"{c}: {a:.3f} vs {b:.3f}" for c, (a, b) in val.items())
        elif k == "P5":
            vs = "; ".join(f"{w}: idw2 {a:.3f}, idw8 {b:.3f}, idnear {i:.3f}" for w, (a, b, i) in val.items())
        else:
            worst = max(val.items(), key=lambda kv: kv[1][0] - kv[1][1])
            vs = f"largest excess {worst[1][0] - worst[1][1]:+.4f} at {worst[0]}"
        L.append(f"| {k} | {txt[k]} | **{'holds' if v['holds'] else 'does not hold'}** | {vs} |")
    L += ["", f"Wall clock {wall:.0f} s. Cells are classified from point estimates and a paired bootstrap; some cells are misclassified by chance and no p-value is claimed. Limitations are in Addendum 25."]
    return "\n".join(L)


def write_csv(path, analyses):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["world", "cap", "building", "cell"] + [f"{p}_{k}" for p in IW.POLICIES for k in ("minutes", "accuracy", "actionable", "wrong_confident", "unresolved", "off_list", "checks")]
                   + [f"{t}_vs_{b}" for t, b in IW.PAIRS])
        for a in analyses:
            c = a["cell"]
            w.writerow([c.world, c.cap, c.building, a["idx"]] + [round(a["summary"][p][k], 4) for p in IW.POLICIES for k in ("minutes", "accuracy", "actionable", "wrong_confident", "unresolved", "off_list", "checks")]
                       + [a["cmp"][f"{t}|{b}"]["label"] for t, b in IW.PAIRS])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--n", type=int, default=None)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    n = a.n or (20 if a.smoke else IW.N_EPISODES)
    t0 = time.time()
    computed = R.eligible(DATA)
    if tuple(computed) != R.FROZEN_BUILDINGS:
        sys.exit(f"the eligible buildings differ from the frozen list: {computed}")
    layouts, censuses = {}, {}
    for b in R.FROZEN_BUILDINGS:
        censuses[b] = C.parse_census(DATA / f"mortar__{b}.ttl", b)
        layouts[b], _ = R.layout_from_census(censuses[b])
    names = list(R.FROZEN_BUILDINGS)[:3] if a.smoke else list(R.FROZEN_BUILDINGS)
    every = IW.all_idw_cells(list(R.FROZEN_BUILDINGS))
    cells = [(i, c) for i, c in enumerate(every) if c.building in names]
    raw_f = a.out / "idweight_raw.pkl"
    if raw_f.exists():
        results = pickle.loads(raw_f.read_bytes())
        print("loaded raw results from cache", flush=True)
    else:
        results = IW.compute_idw_cells([(i, c, layouts[c.building]) for i, c in cells], n=n, workers=a.workers)
        raw_f.write_bytes(pickle.dumps(results))
        print(f"computed {len(results)} cells x {n} episodes in {time.time() - t0:.0f}s", flush=True)
    a24 = pickle.loads(A24.read_bytes()) if A24.exists() else []
    r0 = results[0]
    k = min(50, r0["n"])
    r1 = IW.run_idw_cell(r0["idx"], r0["cell"], layouts[r0["cell"].building], n=k)
    g4 = all(np.array_equal(r1["policy"][p][key], r0["policy"][p][key][:k]) for p in IW.POLICIES for key in ("minutes", "checks", "correct", "concluded", "guess_idx", "truth_idx", "off_list", "named"))
    problems = [p for b in names for p in R.layout_problems(b, layouts[b], censuses[b])]
    ok1, d1 = IW.gate_g1_idw(layouts[names[0]])
    ok1b, d1b = IW.gate_g1_a24(results, a24) if a24 else (False, "Addendum 24's raw results are missing")
    ok3, d3 = IW.gate_g3(results, layouts)
    gates = {"G1 code path (id-mode cases; min, idnear and grouped reproduce Addendum 24)": (ok1 and ok1b, f"{d1}; {d1b}"), "G2 accounting": SR.gate_g2_real(layouts[names[0]]),
             "G3 coverage bookkeeping and world ordering": (ok3, d3), "G4 reproducibility": (g4, f"cell {r0['idx']}: first {k} episodes reproduced" if g4 else "mismatch"),
             "G5 completeness and pairing": IW.g5_complete_idw(results, n_cells=len(cells), expected_idx=[i for i, _ in cells]), "G6 layout fidelity": (not problems, f"{len(names)} buildings" if not problems else "; ".join(problems[:3]))}
    analyses = [IW.analyze_idw_cell(r) for r in results]
    (a.out / "idweight_analysis.pkl").write_bytes(pickle.dumps(analyses))
    md = report(results, analyses, gates, enforced=not a.smoke, n=n, wall=time.time() - t0)
    (a.out / "idweight_report.md").write_text(md)
    write_csv(a.out / "idweight_cells.csv", analyses)
    print("gates:", {g.split(" ")[0]: v[0] for g, v in gates.items()}, "| report written", flush=True)
    if not a.smoke and not all(ok for ok, _ in gates.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
