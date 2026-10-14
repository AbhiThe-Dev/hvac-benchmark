"""Is a one-way "the drawings are mostly right" switch worth offering? (PREREGISTRATION_DR.md Addendum 22.) Layouts real (Mortar Brick metadata only); errors and answers simulated.
600 cells = 4 stress conditions x 3 worlds (5%, 15%, 30% wrong drawings) x 2 candidate regimes x 25 buildings, 500 paired episodes x 5 policies each (`entropy` with the switch off, on and
on_mild, `habit_A`, `habit_B`).
  .venv/bin/python doc_mismatch/scripts/65_troubleshoot_switch.py                 # the pre-registered run
  .venv/bin/python doc_mismatch/scripts/65_troubleshoot_switch.py --smoke --out /some/scratch/dir    # plumbing check on 3 buildings; gates not enforced; numbers meaningless
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
from docmismatch.troubleshoot import study_rating as SG  # noqa: E402
from docmismatch.troubleshoot import study_real as SR  # noqa: E402
from docmismatch.troubleshoot import study_switch as SW  # noqa: E402

REPO = ROOT.parent
DATA = REPO / "data_cache"
OUT = REPO / "results/docmismatch/troubleshoot_switch"
ADD21 = REPO / "results/docmismatch/troubleshoot_rating/rating_analysis.pkl"
WORLD_TEXT = {w: f"{100 * p:.0f}% wrong" for w, p in SW.P_WRONG.items()}


def pct(x):
    return "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{100 * x:.0f}%"


def fs(x):
    return "none" if x is None else f"{x:.2f}"


def report(results, analyses, gates, meta, enforced, n, wall):
    regs = list(SW.REGIMES)
    L = ["# The one-way 'drawings are mostly right' switch (Addendum 22)", "",
         f"Layouts: {len(meta)} real Mortar buildings (Brick metadata only); errors and the technician's answers are SIMULATED from the tool's own model family. {len(analyses)} cells = 4 stress conditions x 3 worlds x 2 "
         f"candidate regimes x {len(meta)} buildings, {n} paired episodes x {len(SW.POLICIES)} policies each. The switch is OFF (the default prior: 15% of documented boxes wrong), ON (5%) or ON_MILD (10%, secondary). "
         "A world is the TRUE share of wrong drawings; a condition says how bad the actuators and the checks really are (X0 as assumed; X1 actuators fail 30% instead of 15%; X2 checks worse: every check except "
         "`override_room` has hit rate -0.15 and false-alarm rate +0.10; X3 both). The tool's own assumptions other than the prior never change. Minutes are placeholders: only orderings and ratios mean anything. "
         "This study is post-hoc in origin (it follows Addendum 21) and uses the same layouts and simulator, so it is a replication plus stress test, not independent evidence. "
         "Nothing here is evidence about real technicians, real drawings, or whether technicians can tell that drawings are mostly right.", "", "## Gates", "", "| gate | result | detail |", "|---|---|---|"]
    for g, (ok, d) in gates.items():
        L.append(f"| {g} | {'PASS' if ok else 'FAIL'} | {d} |")
    if not enforced:
        L += ["", "**SMOKE RUN: gates are not enforced and the numbers below are meaningless.**"]
    if enforced and not all(ok for ok, _ in gates.values()):
        return "\n".join(L + ["", "## NO RESULT (a gate failed)"])
    L += ["", "## Means over buildings: minutes / accuracy / wrong-and-confident / mean checks", "", "| condition | world | regime | " + " | ".join(SW.POLICIES) + " |", "|---|---|---|" + "---|" * len(SW.POLICIES)]
    for c in SW.CONDITIONS:
        for w in SW.WORLDS:
            for reg in regs:
                cells = SW.group_cells(analyses, c, w, reg)
                cols = []
                for p in SW.POLICIES:
                    m = lambda k: float(np.mean([a["summary"][p][k] for a in cells]))  # noqa: E731
                    cols.append(f"{m('minutes'):.0f} / {pct(m('accuracy'))} / {pct(m('wrong_confident'))} / {m('checks'):.1f}")
                L.append(f"| {c} {SW.CONDITION_TEXT[c]} | {WORLD_TEXT[w]} | {reg} | " + " | ".join(cols) + " |")
    readings = SW.group_readings(analyses)
    L += ["", "## The switch ON against OFF on the same episodes", "",
          "Label shares are over the 25 buildings of a regime or the 50 cells pooled (Addendum 21's labels: 5% minutes, 0.02 accuracy, paired 95% intervals). SAFETY REG / GAIN = cells whose wrong-and-confident rate is at least 0.02 "
          "higher / lower with the paired interval clear of 0; COST = WORSE, TRADE or a safety regression. Deltas are the mean over buildings of the paired mean difference (on minus off). Reading: the map reading where the "
          "switch is right (5% wrong), the harm reading where it is wrongly on (15%, 30%).", "",
          "| condition | world | regime | IMPROVES | WORSE | TRADE | NEITHER | safety REG / GAIN | COST | d minutes | d accuracy | d wrong-and-confident | d checks | reading |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in SW.CONDITIONS:
        for w in SW.WORLDS:
            for reg in regs + ["pooled"]:
                cells = SW.group_cells(analyses, c, w, None if reg == "pooled" else reg)
                fr, d = SG.fractions(cells, "on"), SW.mean_delta(cells, "on")
                base = float(np.mean([a["summary"][SW.tool_name(SW.BASE)]["minutes"] for a in cells]))
                L.append(f"| {c} {SW.CONDITION_TEXT[c]} | {WORLD_TEXT[w]} | {reg} | {pct(fr['IMPROVES'])} | {pct(fr['WORSE'])} | {pct(fr['TRADE'])} | {pct(fr['NEITHER'])} | {pct(fr['SAFETY_REGRESSION'])} / {pct(fr['SAFETY_GAIN'])} | "
                         f"{pct(fr['COST'])} | {d['d_min']:+.1f} ({100 * d['d_min'] / base:+.0f}%) | {d['d_acc']:+.3f} | {d['d_wc']:+.3f} | {d['d_checks']:+.2f} | {'**' + readings[(c, w)] + '**' if reg == 'pooled' else ''} |")
    L += ["", "### Secondary: ON_MILD (10%) against OFF (reported only; no verdict)", "", "| condition | world | regime | IMPROVES | WORSE | TRADE | NEITHER | safety REG | d minutes | d accuracy | d wrong-and-confident |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in SW.CONDITIONS:
        for w in SW.WORLDS:
            for reg in regs:
                cells = SW.group_cells(analyses, c, w, reg)
                fr, d = SG.fractions(cells, "on_mild"), SW.mean_delta(cells, "on_mild")
                L.append(f"| {c} | {WORLD_TEXT[w]} | {reg} | {pct(fr['IMPROVES'])} | {pct(fr['WORSE'])} | {pct(fr['TRADE'])} | {pct(fr['NEITHER'])} | {pct(fr['SAFETY_REGRESSION'])} | {d['d_min']:+.1f} | {d['d_acc']:+.3f} | {d['d_wc']:+.3f} |")
    dl = SW.deltas(analyses)
    fstar = SW.break_even_table(analyses)
    L += ["", "## How many wrong switch-ons can it take?", "",
          "The technician flips the switch on with probability s when the drawings are 5% wrong and f when they are 15% or 30% wrong. Worlds are mixed as 'equal' (1/3, 1/3, 1/3) or 'tilted' toward well-documented buildings "
          "(0.6, 0.3, 0.1). Favourable = expected minutes not above 0, expected accuracy not more than 0.01 below and expected wrong-and-confident not more than 0.01 above the default's. f* = the largest f (grid step 0.01) "
          "at which the change is favourable at every f up to it.", "", "| condition | regime | mix | f* at s = 0.5 | f* at s = 1.0 |", "|---|---|---|---|---|"]
    for c in SW.CONDITIONS:
        for reg in regs:
            for m in SW.MIXES:
                L.append(f"| {c} {SW.CONDITION_TEXT[c]} | {reg} | {m} | {fs(fstar[(c, reg, m, 0.5)])} | {fs(fstar[(c, reg, m, 1.0)])} |")
    L += ["", "Expected change at s = 1.0, equal mix, for selected false-alarm rates f (minutes / accuracy / wrong-and-confident):", "", "| condition | regime | f = 0 | f = 0.25 | f = 0.5 | f = 0.75 | f = 1.0 |", "|---|---|---|---|---|---|---|"]
    for c in SW.CONDITIONS:
        for reg in regs:
            cols = []
            for f in (0.0, 0.25, 0.5, 0.75, 1.0):
                ch = SW.expected_change(dl[c][reg], 1.0, f, SW.MIXES["equal"])
                cols.append(f"{ch['d_min']:+.1f} / {ch['d_acc']:+.3f} / {ch['d_wc']:+.3f}")
            L.append(f"| {c} | {reg} | " + " | ".join(cols) + " |")
    decision, q, cc = SW.decide(readings, fstar)
    L += ["", f"## Decision (frozen rule; about OFFERING the switch, never about shipping it): **{decision}**", "",
          f"Q (the X0 5%-wrong group reads at least HELPS IN PART): {'yes' if q else 'no'} (reads {readings[('X0', SW.RIGHT_WORLD)]}). C per condition (no wrongly-on group reads HARMFUL and f* >= {SW.F_BAR:.2f} at s = 1.0 for both "
          "mixes and both regimes): " + ", ".join(f"{c} {'holds' if v else 'fails'}" for c, v in cc.items()) + ". Wrongly-on readings: " +
          ", ".join(f"{c}/{WORLD_TEXT[w]}: {readings[(c, w)]}" for c in SW.CONDITIONS for w in SW.WRONG_WORLDS) + ". The default stays `off` either way."]
    L += ["", "## Context (no verdict): each state against the two habits", "", "Addendum 19's label against BOTH habits (WINS / LOSES share of buildings), then against each habit: WINS / LOSES / BUYS ACCURACY.", "",
          "| condition | world | regime | state | vs both: WINS / LOSES | vs habit_A: WINS / LOSES / BUYS ACC | vs habit_B: WINS / LOSES / BUYS ACC |", "|---|---|---|---|---|---|---|"]
    for c in SW.CONDITIONS:
        for w in SW.WORLDS:
            for reg in regs:
                cells = SW.group_cells(analyses, c, w, reg)
                for st in SW.STATES:
                    wf, lf = S.map_fractions([a["ctx"][st] for a in cells])
                    per = []
                    for h in SW.HABITS:
                        labs = [a["ctx"][f"{st}|{h}"]["secondary"] for a in cells]
                        per.append(" / ".join(pct(labs.count(x) / len(labs)) for x in ("WINS", "LOSES", "BUYS ACCURACY")))
                    L.append(f"| {c} | {WORLD_TEXT[w]} | {reg} | {st} | {pct(wf)} / {pct(lf)} | {per[0]} | {per[1]} |")
    if ADD21.exists():
        prev = pickle.loads(ADD21.read_bytes())
        L += ["", "## Replication: X0 here against Addendum 21 (same layouts and simulator, different seeds; means over buildings, minutes / accuracy / wrong-and-confident)", "",
              "| world | regime | OFF now | 'mixed' in Add. 21 | ON now | 'mostly_right' in Add. 21 |", "|---|---|---|---|---|---|"]
        for w in SW.WORLDS:
            for reg in regs:
                now = SW.group_cells(analyses, "X0", w, reg)
                old = [a for a in prev if a["cell"].world == w and a["cell"].regime == reg]
                f = lambda cells, p: " / ".join(f"{v:.0f}" if k == "minutes" else pct(v) for k in ("minutes", "accuracy", "wrong_confident") for v in [float(np.mean([a["summary"][p][k] for a in cells]))])  # noqa: E731
                L.append(f"| {WORLD_TEXT[w]} | {reg} | {f(now, 'entropy@off')} | {f(old, 'entropy@mixed')} | {f(now, 'entropy@on')} | {f(old, 'entropy@mostly_right')} |")
    pr = SW.switch_predictions(analyses)
    txt = {"P1": "X0, 5% wrong: `on` has lower minutes than `off` in both regimes and accuracy not more than 0.01 lower", "P2": "30% wrong: the wrong-and-confident increase from `on` is larger in X2 than in X0, in both regimes",
           "P3": "in every one of the 12 (condition, world) groups and both regimes `on` has lower mean minutes", "P4": "`on_mild` is between `off` and `on` (smaller saving at 5% wrong, smaller wrong-and-confident increase at 30%) in every condition and regime",
           "P5": "the frozen decision is CONDITIONAL ON RELIABLE CHECKS"}
    L += ["", "## Predictions written before the run", "", "| | prediction | holds? | values |", "|---|---|---|---|"]
    for k, v in pr.items():
        val = v["values"]
        if k == "P1":
            vs = "; ".join(f"{reg}: {m:+.2f} min, {a:+.4f} acc" for reg, (m, a) in val.items())
        elif k == "P2":
            vs = "; ".join(f"{reg}: X2 {x:+.4f} vs X0 {y:+.4f}" for reg, (x, y) in val.items())
        elif k == "P3":
            worst = max(val.items(), key=lambda kv: kv[1])
            vs = f"largest change in minutes: {worst[1]:+.2f} at {worst[0]}"
        elif k == "P4":
            bad = [f"{key}" for key, (mm, mo, wm, wo) in val.items() if not (mm > mo and wm < wo)]
            vs = "violations: " + (", ".join(bad) if bad else "none")
        else:
            vs = f"decision: {val}"
        L.append(f"| {k} | {txt[k]} | **{'holds' if v['holds'] else 'does not hold'}** | {vs} |")
    L += ["", f"Wall clock {wall:.0f} s. Cells are classified from point estimates and a paired bootstrap; some cells are misclassified by chance and no p-value is claimed. Limitations are in Addendum 22."]
    return "\n".join(L)


def write_csv(path, analyses):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["condition", "world", "regime", "building", "cell"] + [f"{p}_{k}" for p in SW.POLICIES for k in ("minutes", "accuracy", "checks", "wrong_confident")]
                   + [f"{s}_{k}" for s in SW.STATES if s != SW.BASE for k in ("label", "safety", "d_min", "d_acc", "d_wc")])
        for a in analyses:
            c = a["cell"]
            w.writerow([c.condition, c.world, c.regime, c.building, a["idx"]] + [round(a["summary"][p][k], 4) for p in SW.POLICIES for k in ("minutes", "accuracy", "checks", "wrong_confident")]
                       + [x for s in SW.STATES if s != SW.BASE for x in (a["cmp"][s]["label"], a["cmp"][s]["safety"], round(a["cmp"][s]["d_min"], 3), round(a["cmp"][s]["d_acc"], 4), round(a["cmp"][s]["d_wc"], 4))])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--n", type=int, default=None)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    n = a.n or (20 if a.smoke else SW.N_EPISODES)
    t0 = time.time()
    computed = R.eligible(DATA)
    if tuple(computed) != R.FROZEN_BUILDINGS:
        sys.exit(f"the eligible buildings differ from the frozen list: {computed}")
    layouts, meta, censuses = {}, {}, {}
    for b in R.FROZEN_BUILDINGS:
        censuses[b] = C.parse_census(DATA / f"mortar__{b}.ttl", b)
        layouts[b], meta[b] = R.layout_from_census(censuses[b])
    names = list(R.FROZEN_BUILDINGS)[:3] if a.smoke else list(R.FROZEN_BUILDINGS)
    every = SW.all_switch_cells(list(R.FROZEN_BUILDINGS))
    cells = [(i, c) for i, c in enumerate(every) if c.building in names]
    raw_f = a.out / "switch_raw.pkl"
    if raw_f.exists():
        results = pickle.loads(raw_f.read_bytes())
        print("loaded raw results from cache", flush=True)
    else:
        results = SW.compute_switch_cells([(i, c, layouts[c.building]) for i, c in cells], n=n, workers=a.workers)
        raw_f.write_bytes(pickle.dumps(results))
        print(f"computed {len(results)} cells x {n} episodes in {time.time() - t0:.0f}s", flush=True)
    first = layouts[names[0]]
    r0 = results[0]
    k = min(50, r0["n"])
    r1 = SW.run_switch_cell(r0["idx"], r0["cell"], layouts[r0["cell"].building], n=k)
    g4 = all(np.array_equal(r1["policy"][p][key], r0["policy"][p][key][:k]) for p in SW.POLICIES for key in ("minutes", "checks", "correct", "concluded", "guess_idx", "truth_idx"))
    problems = [p for b in names for p in R.layout_problems(b, layouts[b], censuses[b])]
    ok3, v3 = SW.g3_honesty_switch(results)
    ok_h, d_h = SW.gate_habits_independent(first)
    ok5, d5 = SW.g5_complete_switch(results, n_cells=len(cells), expected_idx=[i for i, _ in cells])
    gates = {"G1 switch states and code path": SW.gate_g1_switch(first), "G2 accounting": SR.gate_g2_real(first),
             "G3 honesty (accuracy among concluded >= 0.92 in X0: off at 15% wrong, on at 5% wrong)": (ok3, ", ".join(f"{s}/{w}/{r}: {v:.3f}" for (s, w, r), v in v3.items())),
             "G4 reproducibility": (g4, f"cell {r0['idx']}: first {k} episodes reproduced" if g4 else "mismatch"),
             "G5 completeness, pairing and habit independence": (ok5 and ok_h, f"{d5}; {d_h}"), "G6 layout fidelity": (not problems, f"{len(names)} buildings" if not problems else "; ".join(problems[:3]))}
    analyses = [SW.analyze_switch_cell(r) for r in results]
    (a.out / "switch_analysis.pkl").write_bytes(pickle.dumps(analyses))
    md = report(results, analyses, gates, {b: meta[b] for b in names}, enforced=not a.smoke, n=n, wall=time.time() - t0)
    (a.out / "switch_report.md").write_text(md)
    write_csv(a.out / "switch_cells.csv", analyses)
    print("gates:", {g.split(" ")[0]: v[0] for g, v in gates.items()}, "| report written", flush=True)
    if not a.smoke and not all(ok for ok, _ in gates.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
