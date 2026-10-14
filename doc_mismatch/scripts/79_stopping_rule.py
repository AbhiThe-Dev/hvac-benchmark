"""Does a less conservative stopping rule, on its own, recover the language model's T2 speed edge over the routine? (PREREGISTRATION_DR.md Addendum 34.) A parameter sweep of the tool's own
engine; no LLM. Simulation only.
  .venv/bin/python doc_mismatch/scripts/79_stopping_rule.py                    # the pre-registered run (1000 events)
  .venv/bin/python doc_mismatch/scripts/79_stopping_rule.py --smoke --out DIR  # plumbing check on 50 events; gates not enforced; numbers meaningless
"""
import argparse
import csv
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.troubleshoot.v2 import study_stop as ST  # noqa: E402

REPO = ROOT.parent
OUT = REPO / "results/docmismatch/troubleshoot_stop"


def pct(x):
    return f"{100 * x:+.0f}%"


def row(v):
    s, c = v["sum"], v["cmp"]
    return (f"{s['minutes']:.1f} min / {s['accuracy']:.0%} / {s['wrong_confident']:.1%} / {s['checks']:.1f} | "
            f"{c['d_min']:+.1f} ({pct(c['r_min'])}) [{c['ci_min'][0]:+.0f}, {c['ci_min'][1]:+.0f}] | {c['d_acc']:+.3f} [{c['ci_acc'][0]:+.2f}, {c['ci_acc'][1]:+.2f}] | "
            f"{c['d_wc']:+.3f} | {c['time']} / {c['acc']} | {c['label']}")


def matched_wc(an: dict, target: float):
    """Exploratory (not registered): the tau in the grid whose wrong-and-confident rate is closest to `target`, and what it costs/buys."""
    best = min(an["tau"].items(), key=lambda kv: abs(kv[1]["sum"]["wrong_confident"] - target))
    return best


def report(an: dict, gates: dict, enforced: bool, n: int, wall: float) -> str:
    L = ["# Does the routine's stopping rule, on its own, explain the LLM's T2 speed edge? (Addendum 34)", "",
         f"A parameter sweep of the routine's own engine (`tau`, `min_rate`) on Addendum 30's primary cell, tier T2, {n} events (identical answers to identical questions, `TableOracle`); "
         "no LLM is run here. Simulation only, from the tool's own model family with placeholder numbers.", "", "## Gates", "", "| gate | result | detail |", "|---|---|---|"]
    for g, (ok, d) in gates.items():
        L.append(f"| {g} | {'PASS' if ok else 'FAIL'} | {d} |")
    if not enforced:
        L += ["", "**SMOKE RUN: gates are not enforced and the numbers below are meaningless.**"]
    if enforced and not all(ok for ok, _ in gates.values()):
        return "\n".join(L + ["", "## NO RESULT (a gate failed)"])
    L += ["", "## Primary sweep: `tau` (min_rate fixed at 0.003), T2, all visits", "",
          "| tau | minutes / accuracy / wrong-and-confident / checks | d minutes (vs tau=0.95) | d accuracy | d wrong-and-confident | time / accuracy | label |", "|---|---|---|---|---|---|---|"]
    for t in sorted(ST.TAU_GRID, reverse=True):
        mark = " (baseline)" if t == ST.BASE_TAU else ""
        L.append(f"| {t:.2f}{mark} | " + row(an["tau"][t]) + " |")
    L += ["", "## Secondary, exploratory sweep: `min_rate` (tau fixed at 0.95), T2, all visits", "",
          "| min_rate | minutes / accuracy / wrong-and-confident / checks | d minutes (vs min_rate=0.003) | d accuracy | d wrong-and-confident | time / accuracy | label |", "|---|---|---|---|---|---|---|"]
    for r in sorted(ST.MIN_RATE_GRID):
        mark = " (baseline)" if r == ST.BASE_MIN_RATE else ""
        L.append(f"| {r:g}{mark} | " + row(an["min_rate"][r]) + " |")
    llm_wc = 0.16  # Addendum 33, T2, all complaints, wrong-and-confident
    t_match, v_match = matched_wc(an, llm_wc)
    L += ["", "## Exploratory, not registered: matching the language model's own wrong-and-confident rate",
          f"The language model's wrong-and-confident rate at T2 was about {llm_wc:.0%} of complaints (Addendum 33). The closest `tau` in this grid is **{t_match:.2f}** "
          f"(wrong-and-confident {v_match['sum']['wrong_confident']:.1%}), where minutes are {pct(v_match['cmp']['r_min'])} against the baseline stopping rule "
          f"({v_match['cmp']['d_min']:+.1f} minutes). This is not the frozen decision (which respects the safety tolerance); it asks what a stopping rule with the LLM's own error profile would cost or buy.",
          "", "## Predictions (written before the run; each strict)", "", "| prediction | holds | values |", "|---|---|---|"]
    for k, (ok, det) in ST.predictions(an).items():
        L.append(f"| {k} | {'holds' if ok else 'does not hold'} | {det} |")
    L += ["", f"## Frozen decision: {ST.decision(an)}", "", f"Run time {wall:.0f} s."]
    return "\n".join(L)


def write_csv(path: Path, an: dict) -> None:
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["axis", "value", "minutes", "accuracy", "wrong_confident", "checks", "d_minutes", "r_minutes", "d_accuracy", "d_wrong_confident", "label"])
        for axis, grid in (("tau", ST.TAU_GRID), ("min_rate", ST.MIN_RATE_GRID)):
            for k in grid:
                v = an[axis][k]
                s, c = v["sum"], v["cmp"]
                w.writerow([axis, k, f"{s['minutes']:.4f}", f"{s['accuracy']:.4f}", f"{s['wrong_confident']:.4f}", f"{s['checks']:.4f}", f"{c['d_min']:.4f}", f"{c['r_min']:.4f}",
                            f"{c['d_acc']:.4f}", f"{c['d_wc']:.4f}", c["label"]])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    n = 50 if a.smoke else ST.N_EPISODES
    _, wp, events = ST.world()
    events = events[:n]
    sweep = ST.run_sweep(events=events, wp=wp, n=n)
    an = ST.analyze(sweep)
    gates = {"G1 events": ST.gate_g1(events, min(50, n)), "G2 baseline reproduces Addendum 31": ST.gate_g2(an), "G3 answer table": ST.gate_g3(), "G4 direction sanity": ST.gate_g4(an),
             "G5 reproducibility": ST.gate_g5(sweep, ST.run_sweep(events=events, wp=wp, n=n))}
    text = report(an, gates, not a.smoke, n, time.time() - t0)
    (a.out / "stop_report.md").write_text(text + "\n")
    write_csv(a.out / "stop_sweep.csv", an)
    print(f"wrote {a.out / 'stop_report.md'}; gates: " + ", ".join(f"{g.split()[0]} {'PASS' if ok else 'FAIL'}" for g, (ok, _) in gates.items()))
    if not a.smoke and not all(ok for ok, _ in gates.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
