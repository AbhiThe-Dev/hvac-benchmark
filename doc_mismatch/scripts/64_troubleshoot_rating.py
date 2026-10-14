"""Does telling the tool how far to trust the drawings make it better? (PREREGISTRATION_DR.md Addendum 21.) Layouts real (Mortar Brick metadata only); errors and answers simulated.
250 cells = 5 worlds x 2 candidate regimes x 25 buildings, 500 paired episodes x 5 policies each (`entropy` under three ratings, `habit_A`, `habit_B`).
  .venv/bin/python doc_mismatch/scripts/64_troubleshoot_rating.py                 # the pre-registered run
  .venv/bin/python doc_mismatch/scripts/64_troubleshoot_rating.py --smoke --out /some/scratch/dir    # plumbing check on 3 buildings; gates not enforced; numbers meaningless
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

REPO = ROOT.parent
DATA = REPO / "data_cache"
OUT = REPO / "results/docmismatch/troubleshoot_rating"
WORLD_TEXT = {w: f"{100 * c.p_wrong:.0f}% wrong" for w, c in SG.WORLDS.items()}
SCEN_TEXT = {"S1": "matched-low", "S2": "matched-high", "S3": "over-sure by 1", "S4": "over-sure by 2", "S5": "too cautious by 1", "S6": "too cautious by 2"}


def pct(x):
    return "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{100 * x:.0f}%"


def qs(x):
    return "none" if x is None else f"{x:.2f}"


def report(results, analyses, gates, meta, enforced, n, wall):
    L = ["# Telling the tool how far to trust the drawings (Addendum 21)", "",
         f"Layouts: {len(meta)} real Mortar buildings (Brick metadata only); errors and the technician's answers are SIMULATED from the tool's own model family. {len(analyses)} cells = 5 worlds x 2 candidate regimes x "
         f"{len(meta)} buildings, {n} paired episodes x {len(SG.POLICIES)} policies each. The technician's rating sets the tool's prior that the documented box is wrong (mostly_right 5%, mixed 15% = the default, poor 30%; "
         "ASSUMED levels). A world is the TRUE share of wrong drawings; everything else in the world is as the tool assumes. Minutes are placeholders: only orderings and ratios mean anything. "
         "A prior that is true helps mechanically in a world built from the tool's own model, so the informative numbers are the SIZE of the gain, the cost when the rating is wrong and the break-even rating accuracy. "
         "Nothing here is evidence about real technicians, real drawings, or whether technicians can rate drawings.", "", "## Gates", "", "| gate | result | detail |", "|---|---|---|"]
    for g, (ok, d) in gates.items():
        L.append(f"| {g} | {'PASS' if ok else 'FAIL'} | {d} |")
    if not enforced:
        L += ["", "**SMOKE RUN: gates are not enforced and the numbers below are meaningless.**"]
    if enforced and not all(ok for ok, _ in gates.values()):
        return "\n".join(L + ["", "## NO RESULT (a gate failed)"])
    regs = list(SG.REGIMES)
    L += ["", "## Means over buildings: minutes / accuracy / wrong-and-confident / mean checks (the TOOL under each rating, then the habits)", "",
          "| world | regime | " + " | ".join(SG.POLICIES) + " |", "|---|---|" + "---|" * len(SG.POLICIES)]
    for w in SG.WORLDS:
        for reg in regs:
            cells = SG.scenario_cells(analyses, w, reg)
            cols = []
            for p in SG.POLICIES:
                m = lambda k: float(np.mean([a["summary"][p][k] for a in cells]))  # noqa: E731
                cols.append(f"{m('minutes'):.0f} / {pct(m('accuracy'))} / {pct(m('wrong_confident'))} / {m('checks'):.1f}")
            L.append(f"| {WORLD_TEXT[w]} | {reg} | " + " | ".join(cols) + " |")
    L += ["", "## The scenarios: a rating against the default rating (`mixed`) on the same episodes", "",
          "Label shares are over the 25 buildings of a regime or the 50 cells pooled. IMPROVES / WORSE / TRADE / NEITHER are the frozen labels (5% minutes, 0.02 accuracy, paired 95% intervals); SAFETY = cells whose wrong-and-confident "
          "rate is at least 0.02 higher (REG) or lower (GAIN) with the paired interval clear of 0; COST = WORSE, TRADE or a safety regression. Deltas are the mean over buildings of the paired mean difference (rating minus default).", "",
          "| scenario | world / rating | regime | IMPROVES | WORSE | TRADE | NEITHER | safety REG / GAIN | COST | d minutes | d accuracy | d wrong-and-confident | d checks | reading |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    readings = {}
    for s, (w, r) in SG.SCENARIOS.items():
        for reg in regs + ["pooled"]:
            cells = SG.scenario_cells(analyses, w, None if reg == "pooled" else reg)
            fr, d = SG.fractions(cells, r), SG.mean_delta(cells, r)
            base = float(np.mean([a["summary"][SG.tool_name(SG.BASE)]["minutes"] for a in cells]))
            rd = SG.matched_reading(fr) if s in SG.MATCHED_SCENARIOS else SG.harm_reading(fr)
            if reg == "pooled":
                readings[s] = rd
            L.append(f"| {s} {SCEN_TEXT[s]} | {WORLD_TEXT[w]} / {r} | {reg} | {pct(fr['IMPROVES'])} | {pct(fr['WORSE'])} | {pct(fr['TRADE'])} | {pct(fr['NEITHER'])} | {pct(fr['SAFETY_REGRESSION'])} / {pct(fr['SAFETY_GAIN'])} | "
                     f"{pct(fr['COST'])} | {d['d_min']:+.1f} ({100 * d['d_min'] / base:+.0f}%) | {d['d_acc']:+.3f} | {d['d_wc']:+.3f} | {d['d_checks']:+.2f} | {'**' + rd + '**' if reg == 'pooled' else ''} |")
    L += ["", "(In the world with 15% wrong drawings the matched rating IS the default, so it is a control; every difference there is exactly zero.)", "",
          "### Secondary: worlds between the rating levels (reported only; no verdict)", "", "| world | rating | regime | IMPROVES | WORSE | TRADE | NEITHER | safety REG | d minutes | d accuracy | d wrong-and-confident |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for w, r in SG.SECONDARY:
        for reg in regs:
            cells = SG.scenario_cells(analyses, w, reg)
            fr, d = SG.fractions(cells, r), SG.mean_delta(cells, r)
            L.append(f"| {WORLD_TEXT[w]} | {r} | {reg} | {pct(fr['IMPROVES'])} | {pct(fr['WORSE'])} | {pct(fr['TRADE'])} | {pct(fr['NEITHER'])} | {pct(fr['SAFETY_REGRESSION'])} | {d['d_min']:+.1f} | {d['d_acc']:+.3f} | {d['d_wc']:+.3f} |")
    dl = SG.deltas_by_regime(analyses)
    L += ["", "## Break-even rating accuracy", "",
          "The technician rates correctly with probability q and otherwise picks either other level with equal probability; the three primary worlds (5%, 15%, 30% wrong) are equally weighted (placeholder). Expected change against always "
          "using the default prior; favourable = minutes not above, accuracy not below, wrong-and-confident not above the default's.", "",
          "| regime | q | d minutes | d accuracy | d wrong-and-confident | favourable |", "|---|---|---|---|---|---|"]
    for reg in regs:
        for q in SG.Q_REPORT:
            c = SG.expected_change(dl[reg], q)
            L.append(f"| {reg} | {q:.2f} | {c['d_min']:+.2f} | {c['d_acc']:+.4f} | {c['d_wc']:+.4f} | {'yes' if SG.favourable(c) else 'no'} |")
    L += ["", "| regime | metric | smallest favourable q | largest favourable q | favourable at q = 1 |", "|---|---|---|---|---|"]
    be = {}
    for reg in regs:
        for name, met in (("minutes", "d_min"), ("accuracy", "d_acc"), ("wrong-and-confident", "d_wc"), ("ALL THREE (joint)", None)):
            b = SG.break_even(dl[reg], met)
            if met is None:
                be[reg] = b
            L.append(f"| {reg} | {name} | {qs(b['q_star'])} | {qs(b['q_max'])} | {'yes' if b['at_one'] else 'no'} |")
    dec = SG.decision(readings, be)
    L += ["", f"## Decision (frozen rule; about OFFERING the setting, never about shipping it): **{dec}**", "",
          f"S1 reads {readings['S1']}, S2 reads {readings['S2']}; joint q* = " + ", ".join(f"{reg}: {qs(be[reg]['q_star'])}" for reg in regs) + f" against the bar of {SG.Q_BAR:.2f}. The default stays `mixed` either way."]
    L += ["", "## Context (no verdict): the tool under each rating against the two habits, in the primary worlds", "",
          "Addendum 19's label against BOTH habits (WINS / LOSES share of buildings), then against each habit: WINS / LOSES / BUYS ACCURACY (Addendum 20's secondary label).", "",
          "| world | regime | rating | vs both: WINS / LOSES | vs habit_A: WINS / LOSES / BUYS ACC | vs habit_B: WINS / LOSES / BUYS ACC |", "|---|---|---|---|---|---|"]
    for w in SG.PRIMARY:
        for reg in regs:
            cells = SG.scenario_cells(analyses, w, reg)
            for r in SG.RATINGS:
                wf, lf = S.map_fractions([a["ctx"][r] for a in cells])
                per = []
                for h in SG.HABITS:
                    labs = [a["ctx"][f"{r}|{h}"]["secondary"] for a in cells]
                    per.append(" / ".join(pct(labs.count(x) / len(labs)) for x in ("WINS", "LOSES", "BUYS ACCURACY")))
                L.append(f"| {WORLD_TEXT[w]} | {reg} | {r}{' (matched)' if SG.MATCHED[w] == r else ''} | {pct(wf)} / {pct(lf)} | {per[0]} | {per[1]} |")
    pr = SG.rating_predictions(analyses)
    txt = {"P1": "S1: minutes lower than the default in both regimes and accuracy not more than 0.01 lower", "P2": "S2: wrong-and-confident lower in both regimes and accuracy not lower",
           "P3": "S4: wrong-and-confident at least 0.02 higher in both regimes", "P4": "S6: minutes higher in both regimes", "P5": "at q = 0.70 the expected change is favourable on all three metrics in both regimes"}
    L += ["", "## Predictions written before the run", "", "| | prediction | holds? | values (per regime) |", "|---|---|---|---|"]
    for k, v in pr.items():
        vals = "; ".join(f"{reg}: " + (", ".join(f"{x:.3f}" for x in val) if isinstance(val, tuple) else f"{val:.3f}") for reg, val in v["values"].items())
        L.append(f"| {k} | {txt[k]} | **{'holds' if v['holds'] else 'does not hold'}** | {vals} |")
    L += ["", f"Wall clock {wall:.0f} s. Cells are classified from point estimates and a paired bootstrap; some cells are misclassified by chance and no p-value is claimed. Limitations are in Addendum 21."]
    return "\n".join(L)


def write_csv(path, analyses):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["world", "regime", "building", "cell"] + [f"{p}_{k}" for p in SG.POLICIES for k in ("minutes", "accuracy", "checks", "wrong_confident")]
                   + [f"{r}_{k}" for r in SG.RATINGS if r != SG.BASE for k in ("label", "safety", "d_min", "d_acc", "d_wc")])
        for a in analyses:
            c = a["cell"]
            w.writerow([c.world, c.regime, c.building, a["idx"]] + [round(a["summary"][p][k], 4) for p in SG.POLICIES for k in ("minutes", "accuracy", "checks", "wrong_confident")]
                       + [x for r in SG.RATINGS if r != SG.BASE for x in (a["cmp"][r]["label"], a["cmp"][r]["safety"], round(a["cmp"][r]["d_min"], 3), round(a["cmp"][r]["d_acc"], 4), round(a["cmp"][r]["d_wc"], 4))])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--n", type=int, default=None)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    n = a.n or (20 if a.smoke else SG.N_EPISODES)
    t0 = time.time()
    computed = R.eligible(DATA)
    if tuple(computed) != R.FROZEN_BUILDINGS:
        sys.exit(f"the eligible buildings differ from the frozen list: {computed}")
    layouts, meta, censuses = {}, {}, {}
    for b in R.FROZEN_BUILDINGS:
        censuses[b] = C.parse_census(DATA / f"mortar__{b}.ttl", b)
        layouts[b], meta[b] = R.layout_from_census(censuses[b])
    names = list(R.FROZEN_BUILDINGS)[:3] if a.smoke else list(R.FROZEN_BUILDINGS)
    every = SG.all_rating_cells(list(R.FROZEN_BUILDINGS))
    cells = [(i, c) for i, c in enumerate(every) if c.building in names]
    raw_f = a.out / "rating_raw.pkl"
    if raw_f.exists():
        results = pickle.loads(raw_f.read_bytes())
        print("loaded raw results from cache", flush=True)
    else:
        results = SG.compute_rating_cells([(i, c, layouts[c.building]) for i, c in cells], n=n, workers=a.workers)
        raw_f.write_bytes(pickle.dumps(results))
        print(f"computed {len(results)} cells x {n} episodes in {time.time() - t0:.0f}s", flush=True)
    first = layouts[names[0]]
    r0 = results[0]
    k = min(50, r0["n"])
    r1 = SG.run_rating_cell(r0["idx"], r0["cell"], layouts[r0["cell"].building], n=k)
    g4 = all(np.array_equal(r1["policy"][p][key], r0["policy"][p][key][:k]) for p in SG.POLICIES for key in ("minutes", "checks", "correct", "concluded", "guess_idx", "truth_idx"))
    problems = [p for b in names for p in R.layout_problems(b, layouts[b], censuses[b])]
    ok3, v3 = SG.g3_honesty_rating(results)
    ok_h, d_h = SG.gate_habits_independent(first)
    ok5, d5 = SG.g5_complete_rating(results, n_cells=len(cells), expected_idx=[i for i, _ in cells])
    gates = {"G1 default-off and code path": SG.gate_g1_default_off(first), "G2 accounting": SR.gate_g2_real(first),
             "G3 honesty (accuracy among concluded >= 0.92, matched rating, each primary world and regime)": (ok3, ", ".join(f"{w}/{r}: {v:.3f}" for (w, r), v in v3.items())),
             "G4 reproducibility": (g4, f"cell {r0['idx']}: first {k} episodes reproduced" if g4 else "mismatch"),
             "G5 completeness, pairing and habit independence": (ok5 and ok_h, f"{d5}; {d_h}"), "G6 layout fidelity": (not problems, f"{len(names)} buildings" if not problems else "; ".join(problems[:3]))}
    analyses = [SG.analyze_rating_cell(r) for r in results]
    (a.out / "rating_analysis.pkl").write_bytes(pickle.dumps(analyses))
    md = report(results, analyses, gates, {b: meta[b] for b in names}, enforced=not a.smoke, n=n, wall=time.time() - t0)
    (a.out / "rating_report.md").write_text(md)
    write_csv(a.out / "rating_cells.csv", analyses)
    print("gates:", {g.split(" ")[0]: v[0] for g, v in gates.items()}, "| report written", flush=True)
    if not a.smoke and not all(ok for ok, _ in gates.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
