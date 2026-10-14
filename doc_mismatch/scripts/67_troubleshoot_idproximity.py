"""Do the identifiers of real campus buildings carry location information, and what would an id-neighbour candidate list buy? (PREREGISTRATION_DR.md Addendum 24.)
Cached Mortar Brick metadata and simulation only; no download, no external data.
Part A (descriptive): name consistency of the documented claims and the air-handler lift of id neighbours, per building.
Part B: exact coverage of wrong feeders by three candidate lists in four worlds, and 200 cells = 4 worlds x 2 caps x 25 buildings of 300 paired episodes x 3 policies (`entropy` with the
min / idnear / grouped list).
  .venv/bin/python doc_mismatch/scripts/67_troubleshoot_idproximity.py                 # the pre-registered run
  .venv/bin/python doc_mismatch/scripts/67_troubleshoot_idproximity.py --smoke --out /some/scratch/dir    # plumbing check on 3 buildings; gates not enforced; numbers meaningless
Raw results are pickled first; the report can be regenerated from the pickle. A failed gate means NO RESULT. Needs Addendum 23's raw results (results/docmismatch/troubleshoot_minimum).
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
from docmismatch.troubleshoot import idproximity as ID  # noqa: E402
from docmismatch.troubleshoot import realmaps as R  # noqa: E402
from docmismatch.troubleshoot import study_minimum as SM  # noqa: E402
from docmismatch.troubleshoot import study_real as SR  # noqa: E402

REPO = ROOT.parent
DATA = REPO / "data_cache"
OUT = REPO / "results/docmismatch/troubleshoot_idproximity"
A23 = REPO / "results/docmismatch/troubleshoot_minimum/minimum_raw.pkl"
WORLD_TEXT = {"local": "errors local (same air handler)", "anywhere": "errors anywhere", "idlocal2": "ASSUMED adjacent-room errors (lambda 2)", "idlocal8": "ASSUMED nearby-room errors (lambda 8)"}


def pct(x):
    return "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{100 * x:.0f}%"


def report(results, analyses, gates, part_a, meta, cov, enforced, n, wall):
    caps, levels = list(ID.CAPS), list(ID.LEVELS)
    L = ["# Do identifiers carry location, and what would an id-neighbour list buy? (Addendum 24)", "",
         f"{len(meta)} real Mortar buildings (Brick metadata only, cached; no download). Part A describes the identifiers of the layouts; Part B compares three candidate lists for the tool: MIN (the documented box, then "
         "the first K - 1 boxes of the equipment list), IDNEAR (the documented box, then the K - 1 boxes nearest to it in natural id order; still only the equipment list and the claims) and GROUPED (same air handler "
         "first; needs the box -> air handler claims too). The true cause is drawn over ALL boxes of the building; a wrong feeder that is not on a list counts as 'unlisted' for that policy (OFF-LIST). Worlds: "
         "LOCAL and ANYWHERE are Addendum 23's; the two ADJACENCY worlds are ASSUMED (a wrong feeder is likely a neighbour in id order) and favour IDNEAR BY CONSTRUCTION: they bound what id neighbours could buy if "
         f"errors were that local, they do not show that errors are. {len(analyses)} cells x {n} paired episodes x {len(ID.POLICIES)} policies. Minutes are placeholders. Nothing here is evidence about real "
         "technicians or real documentation errors.", "", "## Gates", "", "| gate | result | detail |", "|---|---|---|"]
    for g, (ok, d) in gates.items():
        L.append(f"| {g} | {'PASS' if ok else 'FAIL'} | {d} |")
    if not enforced:
        L += ["", "**SMOKE RUN: gates are not enforced and the numbers below are meaningless.**"]
    if enforced and not all(ok for ok, _ in gates.values()):
        return "\n".join(L + ["", "## NO RESULT (a gate failed)"])
    tot_c, tot_n = sum(v["consistent"] for v in part_a.values()), sum(v["total"] for v in part_a.values())
    L += ["", "## Part A: what the identifiers carry", "",
          f"**Name consistency**: {tot_c} of {tot_n} documented (box, zone) claims ({pct(tot_c / tot_n)}) have the zone id inside the box id. If this is near 100%, the claims in these buildings are name-derived: the documented "
          "box and its room share a name by construction, so the claims say nothing about whether the drawings are right.", "",
          "**Handler lift** (buildings with at least 2 documented handlers; K = 8): the share of a box's 7 id-nearest boxes that hang on its own air handler (id), the same for the first 7 boxes of the equipment order "
          "(first), the share a random list would give (random), and lift = id / random. Buildings with at most 8 boxes with a handler have full lists and lift 1 by construction.", "",
          "| building | rooms | boxes | handlers | claims consistent | id | first | random | lift |", "|---|---|---|---|---|---|---|---|---|"]
    for b, v in part_a.items():
        lf = v["lift"]
        L.append(f"| {b} | {meta[b].rooms} | {meta[b].boxes} | {meta[b].handlers} | {v['consistent']}/{v['total']} | " + (" | ".join([pct(lf["s_id"]), pct(lf["s_first"]), pct(lf["base"]), f"{lf['lift']:.2f}"]) if lf else "- | - | - | -") + " |")
    use = [v["lift"] for v in part_a.values() if v["lift"] is not None and v["lift"]["n_handled"] > ID.LIFT_K]
    if use:
        L += ["", f"Over the {len(use)} buildings with at least 2 handlers and more than 8 boxes with a handler: id beats first in {pct(float(np.mean([x['s_id'] > x['s_first'] for x in use])))} of them; mean id {pct(float(np.mean([x['s_id'] for x in use])))}, "
              f"mean first {pct(float(np.mean([x['s_first'] for x in use])))}, mean random {pct(float(np.mean([x['base'] for x in use])))}, mean lift {float(np.mean([x['lift'] for x in use])):.2f}."]
    L += ["", "## Part B: coverage of wrong feeders by each list (exact; mean over the buildings)", "",
          "Coverage = the share of the wrong-feeder weight (over all other boxes, in the world's weights) that lies on the list. Expected off-list share of visits = 0.135 x (1 - coverage).", "",
          "| world | cap | coverage min / idnear / grouped | expected off-list share min / idnear / grouped | simulated off-list share min / idnear / grouped |", "|---|---|---|---|---|"]
    for w in ID.WORLDS:
        for c in caps:
            cs = [ID.mean_cov(cov, w, c, lv) for lv in levels]
            sims = [ID.gmean(ID.group_cells(analyses, w, c), lv, "off_list") for lv in levels]
            L.append(f"| {WORLD_TEXT[w]} | {c} | " + " / ".join(pct(x) for x in cs) + " | " + " / ".join(f"{ID.expected_off_list(x):.3f}" for x in cs) + " | " + " / ".join(f"{x:.3f}" for x in sims) + " |")
    L += ["", "## The tool with each list: minutes / accuracy / actionable / wrong-and-confident / unresolved / off-list share (means over buildings)", "",
          "| world | cap | " + " | ".join(levels) + " |", "|---|---|" + "---|" * len(levels)]
    for w in ID.WORLDS:
        for c in caps:
            cells = ID.group_cells(analyses, w, c)
            cols = []
            for lv in levels:
                m = lambda k: ID.gmean(cells, lv, k)  # noqa: E731
                cols.append(f"{m('minutes'):.0f} / {pct(m('accuracy'))} / {pct(m('actionable'))} / {pct(m('wrong_confident'))} / {pct(m('unresolved'))} / {pct(m('off_list'))}")
            L.append(f"| {WORLD_TEXT[w]} | {c} | " + " | ".join(cols) + " |")
    L += ["", "## What each list is worth against MIN (same episodes; Addendum 21's labels; deltas are treatment minus min, means over buildings)", "",
          "| world | cap | list | IMPROVES | WORSE | TRADE | NEITHER | d minutes | d accuracy | d actionable | d off-list share |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for w in ID.WORLDS:
        for c in caps:
            cells = ID.group_cells(analyses, w, c)
            for lv in ("idnear", "grouped"):
                labs = [a["cmp"][lv]["label"] for a in cells]
                d = {k: float(np.mean([a["cmp"][lv][k] for a in cells])) for k in ("d_min", "d_acc", "d_act", "d_off")}
                L.append(f"| {WORLD_TEXT[w]} | {c} | {lv} | " + " | ".join(pct(labs.count(x) / len(labs)) for x in ("IMPROVES", "WORSE", "TRADE", "NEITHER")) + f" | {d['d_min']:+.1f} | {d['d_acc']:+.3f} | {d['d_act']:+.3f} | {d['d_off']:+.3f} |")
    L += ["", "## Per building, errors local (same air handler), K8: exact coverage of the wrong feeder", "", "| building | boxes | handlers | min | idnear | grouped |", "|---|---|---|---|---|---|"]
    for b in sorted(meta, key=lambda x: meta[x].boxes):
        L.append(f"| {b} | {meta[b].boxes} | {meta[b].handlers} | " + " | ".join(pct(cov[(b, 'local', 'K8', lv)]) for lv in levels) + " |")
    pr = ID.id_predictions(analyses, part_a, cov)
    txt = {"P1": "at least 90% of documented claims have the zone id inside the box id", "P2": "id-nearest boxes share the air handler more often than the first-K list in at least 70% of the buildings, mean lift at least 1.5",
           "P3": "local world: coverage idnear > min at both caps and grouped >= idnear", "P4": "local world: expected off-list shares of min and grouped differ by at most 0.015 at each cap",
           "P5": "adjacent-room world (lambda 2), K8: expected off-list share of idnear at most 0.4 x that of min (by construction)", "P6": "local, lambda 2 and lambda 8 worlds, both caps: actionable rate of idnear above min"}
    L += ["", "## Predictions written before the run", "", "| | prediction | holds? | values |", "|---|---|---|---|"]
    for k, v in pr.items():
        val = v["values"]
        if k == "P1":
            vs = f"{val:.3f}"
        elif k == "P2":
            vs = f"id beats first in {val[0]:.2f} of {val[2]} buildings; mean lift {val[1]:.2f}"
        elif k == "P3":
            vs = "; ".join(f"{c}: {a:.3f} / {b:.3f} / {g:.3f}" for c, (a, b, g) in val.items())
        elif k == "P4":
            vs = "; ".join(f"{c}: {a:.3f} vs {g:.3f}" for c, (a, g) in val.items())
        elif k == "P5":
            vs = f"{val[0]:.3f} vs {val[1]:.3f}"
        else:
            vs = "; ".join(f"{w}/{c}: {i:.3f} vs {m:.3f}" for (w, c), (i, m) in val.items())
        L.append(f"| {k} | {txt[k]} | **{'holds' if v['holds'] else 'does not hold'}** | {vs} |")
    L += ["", f"Wall clock {wall:.0f} s. Cells are classified from point estimates and a paired bootstrap; some cells are misclassified by chance and no p-value is claimed. Limitations are in Addendum 24."]
    return "\n".join(L)


def write_csv(path, analyses):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["world", "cap", "building", "cell"] + [f"{p}_{k}" for p in ID.POLICIES for k in ("minutes", "accuracy", "actionable", "wrong_confident", "unresolved", "off_list")] + ["idnear_vs_min", "grouped_vs_min"])
        for a in analyses:
            c = a["cell"]
            w.writerow([c.world, c.cap, c.building, a["idx"]] + [round(a["summary"][p][k], 4) for p in ID.POLICIES for k in ("minutes", "accuracy", "actionable", "wrong_confident", "unresolved", "off_list")]
                       + [a["cmp"]["idnear"]["label"], a["cmp"]["grouped"]["label"]])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--n", type=int, default=None)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    n = a.n or (20 if a.smoke else ID.N_EPISODES)
    t0 = time.time()
    computed = R.eligible(DATA)
    if tuple(computed) != R.FROZEN_BUILDINGS:
        sys.exit(f"the eligible buildings differ from the frozen list: {computed}")
    layouts, meta, censuses, part_a = {}, {}, {}, {}
    for b in R.FROZEN_BUILDINGS:
        censuses[b] = C.parse_census(DATA / f"mortar__{b}.ttl", b)
        layouts[b], meta[b] = R.layout_from_census(censuses[b])
    names = list(R.FROZEN_BUILDINGS)[:3] if a.smoke else list(R.FROZEN_BUILDINGS)
    for b in names:
        cons, tot = ID.name_consistency(censuses[b].pairs["vav_zone"])
        part_a[b] = dict(consistent=cons, total=tot, lift=ID.handler_lift(layouts[b]))
    cov = {}
    for b in names:
        for (w, c, lv), v in ID.coverage_table(layouts[b]).items():
            cov[(b, w, c, lv)] = v
    every = ID.all_id_cells(list(R.FROZEN_BUILDINGS))
    cells = [(i, c) for i, c in enumerate(every) if c.building in names]
    raw_f = a.out / "idproximity_raw.pkl"
    if raw_f.exists():
        results = pickle.loads(raw_f.read_bytes())
        print("loaded raw results from cache", flush=True)
    else:
        results = ID.compute_id_cells([(i, c, layouts[c.building]) for i, c in cells], n=n, workers=a.workers)
        raw_f.write_bytes(pickle.dumps(results))
        print(f"computed {len(results)} cells x {n} episodes in {time.time() - t0:.0f}s", flush=True)
    a23 = pickle.loads(A23.read_bytes()) if A23.exists() else []
    r0 = results[0]
    k = min(50, r0["n"])
    r1 = ID.run_id_cell(r0["idx"], r0["cell"], layouts[r0["cell"].building], n=k)
    g4 = all(np.array_equal(r1["policy"][p][key], r0["policy"][p][key][:k]) for p in ID.POLICIES for key in ("minutes", "checks", "correct", "concluded", "guess_idx", "truth_idx", "off_list", "named"))
    problems = [p for b in names for p in R.layout_problems(b, layouts[b], censuses[b])]
    ok1, d1 = ID.gate_g1_idnear(layouts[names[0]])
    ok1b, d1b = ID.gate_g1_a23(results, a23) if a23 else (False, "Addendum 23's raw results are missing")
    ok3, d3 = ID.gate_g3_coverage(results, layouts)
    ok3b, d3b = ID.gate_g3_exact(cov, a23) if a23 else (False, "Addendum 23's raw results are missing")
    gates = {"G1 code path (id-near lists; min and grouped reproduce Addendum 23)": (ok1 and ok1b, f"{d1}; {d1b}"), "G2 accounting": SR.gate_g2_real(layouts[names[0]]),
             "G3 coverage bookkeeping (and exact = simulated)": (ok3 and ok3b, f"{d3}; {d3b}"), "G4 reproducibility": (g4, f"cell {r0['idx']}: first {k} episodes reproduced" if g4 else "mismatch"),
             "G5 completeness and pairing": ID.g5_complete_id(results, n_cells=len(cells), expected_idx=[i for i, _ in cells]), "G6 layout fidelity": (not problems, f"{len(names)} buildings" if not problems else "; ".join(problems[:3]))}
    analyses = [ID.analyze_id_cell(r) for r in results]
    (a.out / "idproximity_analysis.pkl").write_bytes(pickle.dumps(dict(analyses=analyses, part_a=part_a, cov=cov)))
    md = report(results, analyses, gates, part_a, {b: meta[b] for b in names}, cov, enforced=not a.smoke, n=n, wall=time.time() - t0)
    (a.out / "idproximity_report.md").write_text(md)
    write_csv(a.out / "idproximity_cells.csv", analyses)
    print("gates:", {g.split(" ")[0]: v[0] for g, v in gates.items()}, "| report written", flush=True)
    if not a.smoke and not all(ok for ok, _ in gates.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
