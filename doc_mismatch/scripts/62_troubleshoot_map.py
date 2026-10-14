"""Sensitivity map of the technician-guided troubleshooting tool against trial-and-error stand-ins (PREREGISTRATION_DR.md Addendum 19). Simulation only.
486 truth cells x 500 paired episodes x 5 policies (entropy, split_half, random, habit_A, habit_B); the tool always runs on its assumed default settings.
  .venv/bin/python doc_mismatch/scripts/62_troubleshoot_map.py                 # the pre-registered run (about 5-15 minutes on several cores; run in the background)
  .venv/bin/python doc_mismatch/scripts/62_troubleshoot_map.py --smoke --out /some/scratch/dir    # plumbing check on a few cells; gates are NOT enforced; the numbers are meaningless
Raw results are pickled first; the report can be regenerated from the pickle. A failed gate means NO MAP.
"""
import argparse
import csv
import pickle
import sys
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.troubleshoot import model as M  # noqa: E402
from docmismatch.troubleshoot import sim  # noqa: E402
from docmismatch.troubleshoot import study as S  # noqa: E402

OUT = ROOT.parent / "results/docmismatch/troubleshoot"
DEFAULT_CELL = S.Cell(6, S.DEFAULT["p_wrong"], S.DEFAULT["p_act"], S.DEFAULT["near"], S.DEFAULT["rates"], S.DEFAULT["costs"])


# ---------------------------------------------------------------------------------------------- gates evaluated at run time
def gate_g1(n: int = 30) -> tuple[bool, str]:
    """G1 code path: with truth == assumptions the study runners reproduce sim.simulate / sim.simulate_habit on the same seeds."""
    assumed, real, tm = S.make_world(DEFAULT_CELL)
    rng = np.random.default_rng(0)
    truths = [sim.sample_truth(real, rng) for _ in range(n)]
    for seed, t in enumerate(truths):
        for strat in S.TOOL:
            a, b = S.run_tool(assumed, t, np.random.default_rng(seed), tm, strat), sim.simulate(assumed, t, strat, np.random.default_rng(seed))
            if (a["guess"], a["n_checks"], a["concluded"]) != (b["guess"], b["n_checks"], b["concluded"]) or not np.isclose(a["minutes"], b["minutes"]):
                return False, f"{strat} differs from sim.simulate at seed {seed}"
        a, b = S.run_habit_A(assumed, t, np.random.default_rng(seed), tm), sim.simulate_habit(assumed, t, np.random.default_rng(seed))
        if (a["guess"], a["n_checks"]) != (b["guess"], b["n_checks"]) or not np.isclose(a["minutes"], b["minutes"]):
            return False, f"habit_A differs from sim.simulate_habit at seed {seed}"
    return True, f"{n} episodes x 4 runners identical"


def gate_g2(n: int = 20) -> tuple[bool, str]:
    """G2 accounting: true minutes are charged as hand-summed, and never change which check is chosen or what is answered."""
    assumed, real, tm1 = S.make_world(DEFAULT_CELL)
    _, _, tm3 = S.make_world(replace(DEFAULT_CELL, costs="access_x3"))
    rng = np.random.default_rng(2)
    for seed in range(n):
        t = sim.sample_truth(real, rng)
        for pol in S.POLICIES:
            a, b = S.RUNNERS[pol](assumed, t, np.random.default_rng(seed), tm1), S.RUNNERS[pol](assumed, t, np.random.default_rng(seed), tm3)
            at, tot = None, 0.0
            for name, tgt in b["sequence"]:
                tot += tm3[name].minutes(at, tgt)
                at = tgt
            if a["sequence"] != b["sequence"] or a["guess"] != b["guess"] or not np.isclose(tot, b["minutes"]) or not b["minutes"] > a["minutes"]:
                return False, f"{pol} seed {seed}"
    return True, f"{n} episodes x {len(S.POLICIES)} policies"


def gate_g4(results: list, n_check: int = 50) -> tuple[bool, str]:
    """G4 reproducibility: re-running the first assumptions-correct cell with a shorter list of episodes reproduces the stored first episodes (truths and outcome seeds are prefix-stable)."""
    r0 = next(r for r in results if r["cell"].assumptions_correct)
    k = min(n_check, r0["n"])
    r1 = S.run_cell(r0["idx"], r0["cell"], n=k)
    for name in S.POLICIES:
        for key in ("minutes", "checks", "correct", "concluded", "guess_idx", "truth_idx"):
            if not np.array_equal(r1["policy"][name][key], r0["policy"][name][key][:k]):
                return False, f"cell {r0['idx']} {name} {key} differs"
    return True, f"cell {r0['idx']}: first {k} episodes reproduced"


# ---------------------------------------------------------------------------------------------- the report
def pct(x):
    return "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{100 * x:.0f}%"


def report(results: list, analyses: list, gates: dict, enforced: bool, n: int, wall: float) -> str:
    cells = [a["cell"] for a in analyses]
    lab = {t: [a["label"][t] for a in analyses] for t in S.TOOL}
    spec = [not c.assumptions_correct for c in cells]
    L = ["# Sensitivity map: technician-guided tool vs trial-and-error stand-ins (Addendum 19)", "",
         f"Simulation only. {len(cells)} truth cells x {n} paired episodes x {len(S.POLICIES)} policies; the tool always runs on its ASSUMED default settings, the simulated technician answers from the TRUE numbers and every policy "
         "is charged the TRUE minutes. `habit_A` and `habit_B` are ASSUMED stand-ins for trial and error, not observed behaviour. All minutes are placeholders: only orderings and ratios mean anything. "
         "Nothing here is evidence about real technicians.", "",
         "## Gates", "", "| gate | result | detail |", "|---|---|---|"]
    for g, (ok, detail) in gates.items():
        L.append(f"| {g} | {'PASS' if ok else 'FAIL'} | {detail} |")
    if not enforced:
        L += ["", "**SMOKE RUN: gates are not enforced and the numbers below are meaningless.**"]
    if not all(ok for ok, _ in gates.values()) and enforced:
        return "\n".join(L + ["", "## NO MAP (a gate failed)"])
    L += ["", "## The map, per tool policy (against BOTH habits: WINS only if it wins against each, LOSES if it loses against either)", "",
          "| policy | WINS | LOSES | NEITHER | of which trade-off | reading |", "|---|---|---|---|---|---|"]
    for t in S.TOOL:
        w, l = S.map_fractions(lab[t])
        trade = sum(a["tradeoff"][t] for a in analyses)
        L.append(f"| {t} | {pct(w)} | {pct(l)} | {pct(1 - w - l)} | {trade} cells | **{S.map_reading(w, l)}** |")
    L += ["", "Against each habit separately (WINS / LOSES fraction of cells):", "", "| policy | vs habit_A | vs habit_B |", "|---|---|---|"]
    for t in S.TOOL:
        row = []
        for h in S.HABITS:
            w, l = S.map_fractions([a["cmp"][f"{t}|{h}"]["label"] for a in analyses])
            row.append(f"{pct(w)} / {pct(l)}")
        L.append(f"| {t} | {row[0]} | {row[1]} |")
    ac = [i for i, c in enumerate(cells) if c.assumptions_correct]
    L += ["", "## Best case (the tool's assumptions exactly right) and robustness (at least one assumption wrong)", "", "| policy | assumptions-correct cells (K = 3, 6, 10) | cells with a misspecified factor |", "|---|---|---|"]
    for t in S.TOOL:
        best = [analyses[i]["label"][t] for i in ac]
        rest = [x for x, s in zip(lab[t], spec) if s]
        w, l = S.map_fractions(rest)
        L.append(f"| {t} | {', '.join(best)} | WINS {pct(w)}, LOSES {pct(l)} |")
    L += ["", "## Marginals: WINS / LOSES by level of each factor (strength: WINS >= 80%; weakness: LOSES >= 25%)", ""]
    for t in ("entropy", "split_half"):
        L += [f"### {t}", "", "| factor | level | WINS | LOSES | cells | |", "|---|---|---|---|---|---|"]
        for f in S.FACTORS:
            for lv, (w, l, k) in S.marginals(cells, lab[t], f).items():
                flag = "strength" if w >= S.STRENGTH_W else ("weakness" if l >= S.WEAKNESS_L else "")
                L.append(f"| {f} | {lv} | {pct(w)} | {pct(l)} | {k} | {flag} |")
        L.append("")
    both = list(zip(lab["entropy"], lab["split_half"], spec))
    m = [(e, s) for e, s, sp in both if sp]
    L += ["## `split_half` against `entropy` in the misspecified cells", "", "| | cells |", "|---|---|",
          f"| both WIN | {sum(e == 'WINS' and s == 'WINS' for e, s in m)} |", f"| only split_half WINS | {sum(e != 'WINS' and s == 'WINS' for e, s in m)} |",
          f"| only entropy WINS | {sum(e == 'WINS' and s != 'WINS' for e, s in m)} |", f"| neither WINS | {sum(e != 'WINS' and s != 'WINS' for e, s in m)} |",
          f"| entropy LOSES, split_half does not | {sum(e == 'LOSES' and s != 'LOSES' for e, s in m)} |", f"| split_half LOSES, entropy does not | {sum(s == 'LOSES' and e != 'LOSES' for e, s in m)} |", ""]
    pr = S.predictions(cells, lab)
    L += ["## Predictions written before the run", "", "| | prediction | holds? | values |", "|---|---|---|---|"]
    txt = {"P1": "the advantage grows with K (WINS at K = 10 vs K = 3)", "P2": "it shrinks as P(documented feeder wrong) falls (WINS at 0.30 vs 0.05)",
           "P3": "entropy loses ground to split_half as the truth departs from the tool's prior (W_entropy - W_split_half at 3 departures vs 0)",
           "P4": "expensive access widens the lead (WINS at access x 3 vs as assumed)", "P5": "with degraded hit rates split_half wins at least as often as entropy (split_half vs entropy)"}
    for k, v in pr.items():
        L.append(f"| {k} | {txt[k]} | **{'holds' if v['holds'] else 'does not hold'}** | {v['values'][0]:.3f} vs {v['values'][1]:.3f} |")
    d = next((r for r in results if r["cell"] == DEFAULT_CELL), None)
    if d is not None:
        L += ["", "## By true cause, the default cell (K = 6, everything as assumed)", "", "| true cause | episodes | " + " | ".join(f"{p}: min / acc" for p in S.POLICIES) + " |", "|---|---|" + "---|" * len(S.POLICIES)]
        for ci, cause in enumerate(d["causes"]):
            mask = d["policy"]["entropy"]["truth_idx"] == ci
            if mask.any():
                cols = [f"{d['policy'][p]['minutes'][mask].mean():.0f} / {pct(d['policy'][p]['correct'][mask].mean())}" for p in S.POLICIES]
                L.append(f"| {' '.join(map(str, cause))} | {int(mask.sum())} | " + " | ".join(cols) + " |")
    L += ["", "## Input burden, honesty and secondary metrics (means over cells)", "", "| policy | entries per session | unresolved | wrong-and-confident | accuracy | minutes | minutes per correct (median over cells) |", "|---|---|---|---|---|---|---|"]
    for p in S.POLICIES:
        ss = [a["summary"][p] for a in analyses]
        L.append(f"| {p} | {np.mean([s['entries'] for s in ss]):.1f} | {pct(np.mean([s['unresolved'] for s in ss]))} | {pct(np.mean([s['wrong_confident'] for s in ss]))} | "
                 f"{pct(np.mean([s['accuracy'] for s in ss]))} | {np.mean([s['minutes'] for s in ss]):.0f} | {np.median([s['per_correct'] for s in ss]):.0f} |")
    L += ["", f"Wall clock {wall:.0f} s. Cells are classified from point estimates and a paired bootstrap on minutes; with {len(cells)} cells x 2 policies some cells are misclassified by chance, and no p-value is claimed. "
          "Limitations are listed in Addendum 19 (independent answer noise, truths drawn from the tool's own model family, assumed habits, placeholder minutes, no parallel waiting, one connection type)."]
    return "\n".join(L)


def write_csv(path: Path, analyses: list) -> None:
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        head = list(S.FACTORS) + ["cell"] + [f"{p}_{k}" for p in S.POLICIES for k in ("minutes", "accuracy", "checks", "concluded")] + [f"label_{t}" for t in S.TOOL]
        w.writerow(head)
        for a in analyses:
            c = a["cell"]
            w.writerow([getattr(c, f) for f in S.FACTORS] + [a["idx"]] + [round(a["summary"][p][k], 4) for p in S.POLICIES for k in ("minutes", "accuracy", "checks", "concluded")] + [a["label"][t] for t in S.TOOL])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--n", type=int, default=None)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    n = a.n or (20 if a.smoke else S.N_EPISODES)
    every = list(enumerate(S.all_cells()))
    cells = [e for e in every if e[0] in (0, 1, 2, 3, 100, 200, 300, 485) or e[1].assumptions_correct] if a.smoke else every
    t0 = time.time()
    raw_f = a.out / "map_raw.pkl"
    if raw_f.exists():
        results = pickle.loads(raw_f.read_bytes())
        print("loaded raw results from cache", flush=True)
    else:
        results = S.compute_cells(cells, n=n, workers=a.workers)
        raw_f.write_bytes(pickle.dumps(results))
        print(f"computed {len(results)} cells x {n} episodes in {time.time() - t0:.0f}s", flush=True)
    gates = {"G1 code path": gate_g1(), "G2 accounting": gate_g2(), "G3 honesty (accuracy among concluded >= 0.92, assumptions-correct cells)": None,
             "G4 reproducibility": gate_g4(results), "G5 completeness and pairing": S.g5_complete(results, n_cells=len(cells), expected_idx=[i for i, _ in cells])}
    ok3, vals = S.g3_honesty(results)
    gates["G3 honesty (accuracy among concluded >= 0.92, assumptions-correct cells)"] = (ok3, ", ".join(f"K={k}: {v:.3f}" for k, v in sorted(vals.items())))
    analyses = [S.analyze_cell(r) for r in results]
    (a.out / "map_analysis.pkl").write_bytes(pickle.dumps(analyses))
    md = report(results, analyses, gates, enforced=not a.smoke, n=n, wall=time.time() - t0)
    (a.out / "map_report.md").write_text(md)
    write_csv(a.out / "map_cells.csv", analyses)
    passed = all(ok for ok, _ in gates.values())
    print("gates:", {k.split(" ")[0]: v[0] for k, v in gates.items()}, "| report written", flush=True)
    if not a.smoke and not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
