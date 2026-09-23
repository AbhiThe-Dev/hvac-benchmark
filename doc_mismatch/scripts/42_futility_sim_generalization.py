"""Does Addendum 7's futility stopping generalize past the one real building it was validated on? (Addendum 10)
Same frozen `futility_window=4, futility_margin=0.05` on top of Addendum 5's `exclude_struct` (channels 0+2
excluded), now run on the DR study's held-out T1-T6 simulated suites instead of the single real DEV building.
Primary metric: mean/median technician reads per episode, with vs without. Secondary: forced accuracy, to confirm
stopping early doesn't cost accuracy it would otherwise have earned. Simulation only -- an upper/lower bound on
whether the MECHANISM's logic generalizes, never evidence the real-world Addendum 7 result itself changes.
  .venv/bin/python doc_mismatch/scripts/42_futility_sim_generalization.py
"""
import pickle
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.dr import measurement_eval as ME  # noqa: E402
from docmismatch.dr.pools import DR_DIR  # noqa: E402
from docmismatch.dr.verifier_eval import make_cfg, spec_ids  # noqa: E402

OUT = DR_DIR / "measurement"
SUITES = ["T1_in_range", "T2_regime", "T3_control", "T4_topology", "T5_climate", "T6_compound"]
VARIANTS = list(ME.FUTILITY_VARIANTS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = make_cfg(("active",))
    cfg["sim_reps"] = [0]
    t0 = time.time()

    f = OUT / "futility_sim_generalization.pkl"
    if f.exists():
        out = pickle.loads(f.read_bytes())
        print("loaded from cache", flush=True)
    else:
        ids = spec_ids()
        out = ME.run_futility_sim_ceiling(cfg, ids, SUITES)
        f.write_bytes(pickle.dumps(out))
        print(f"done {time.time() - t0:.0f}s", flush=True)

    md = ["# Does futility stopping generalize past real DEV? (Addendum 10, simulation-only T1-T6)", "",
          "`vav_zone`, channels 0+2 excluded in both variants (Addendum 5's `exclude_struct`), same T1-T6 held-out "
          "DR suites as Addendum 5/6's sim ceiling. `no_futility` = full nmax=24 budget. `futility` = "
          "futility_window=4, futility_margin=0.05 (Addendum 7's exact frozen values, not retuned here). "
          "Simulation only -- see the addendum's explicit caveat.", "",
          "## Technician reads per episode (the primary metric)", "",
          "| suite | variant | n eps | mean n_read | median n_read | reads saved vs no_futility | frac futile |",
          "|---|---|---|---|---|---|---|"]
    for su in SUITES:
        if not out.get(su):
            md.append(f"| {su} | (no vav_zone episodes) | | | | | |")
            continue
        n_read = {v: np.array([r["n_read"] for r in out[su][v]]) for v in VARIANTS}
        futile = {v: np.array([r["futile"] for r in out[su][v]]) for v in VARIANTS}
        for v in VARIANTS:
            if len(n_read[v]) == 0:
                md.append(f"| {su} | {v} | 0 | | | | |")
                continue
            saved = n_read["no_futility"].mean() - n_read[v].mean() if len(n_read["no_futility"]) else float("nan")
            md.append(f"| {su} | {v} | {len(n_read[v])} | {n_read[v].mean():.1f} | {np.median(n_read[v]):.0f} | "
                       f"{saved:.1f} | {futile[v].mean():.1%} |")
    md.append("")

    md += ["## Forced accuracy per suite (point estimates, small per-suite N -- no cluster bootstrap; does stopping early cost anything?)", "",
           "| suite | variant | n eps | forced acc | diff vs no_futility |", "|---|---|---|---|---|"]
    for su in SUITES:
        if not out.get(su):
            continue
        forced = {}
        for v in VARIANTS:
            rows = out[su][v]
            if not rows:
                forced[v] = (float("nan"), 0)
                continue
            correct = np.array([bool(r["say_correct"]) == (not r["wrong"]) for r in rows])
            forced[v] = (float(correct.mean()), len(rows))
        base_acc = forced.get("no_futility", (float("nan"), 0))[0]
        for v in VARIANTS:
            acc, n = forced[v]
            diff = acc - base_acc if v != "no_futility" and n and forced.get("no_futility", (None, 0))[1] else float("nan")
            diff_s = f"{diff:+.3f}" if diff == diff else ""
            md.append(f"| {su} | {v} | {n} | {acc:.3f} | {diff_s} |")

    (OUT / "futility_sim_generalization_report.md").write_text("\n".join(md))
    print("\n".join(md))


main()
