"""Does futility stopping actually save technician tests without costing accuracy? (PREREGISTRATION_DR.md Addendum 7)
On top of Addendum 5's best-validated variant (vav_zone channels 0+2 excluded), real DEV episodes WITH vs WITHOUT
futility_window=4/futility_margin=0.05 (frozen before this run, same values already used in the unit tests).
Primary metric: mean/median technician reads per episode. Secondary: forced accuracy, to confirm stopping early
doesn't cost accuracy it would otherwise have earned.
  .venv/bin/python doc_mismatch/scripts/39_futility_eval.py
"""
import pickle
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.dr import analysis as A  # noqa: E402
from docmismatch.dr import measurement_eval as ME  # noqa: E402
from docmismatch.dr.pools import DR_DIR  # noqa: E402
from docmismatch.dr.verifier_eval import make_cfg  # noqa: E402

OUT = DR_DIR / "measurement"
VARIANTS = list(ME.FUTILITY_VARIANTS)


def fmt(x):
    return f"{x['est']:.3f} [{x['lo']:.3f}, {x['hi']:.3f}]"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = make_cfg(("active",))
    cfg["sim_reps"] = [0]
    t0 = time.time()

    out = ME.run_futility_eval(cfg)
    (OUT / "futility_eval.pkl").write_bytes(pickle.dumps(out))
    print(f"done {time.time() - t0:.0f}s, n_real_episodes={out.get('_n_real_episodes')}", flush=True)

    md = ["# Does futility stopping save technician tests without costing accuracy? (Addendum 7)", "",
          f"real DEV vav_zone episodes (n={out.get('_n_real_episodes')}), channels 0+2 excluded in both variants "
          "(Addendum 5's `exclude_struct`). `no_futility` = full nmax=24 budget every time (the existing baseline). "
          "`futility` = futility_window=4, futility_margin=0.05 (frozen before this run). Building/day-cluster bootstrap "
          "(300 resamples).", "", "## Technician reads per episode (the actual target of this addendum)", "",
          "| variant | mean n_read | median n_read | reads saved vs no_futility | frac futile |", "|---|---|---|---|---|"]
    n_read = {v: np.array([r["n_read"] for r in out[v]["raw"]]) for v in VARIANTS}
    futile = {v: np.array([r["futile"] for r in out[v]["raw"]]) for v in VARIANTS}
    for v in VARIANTS:
        saved = n_read["no_futility"].mean() - n_read[v].mean()
        md.append(f"| {v} | {n_read[v].mean():.1f} | {np.median(n_read[v]):.0f} | {saved:.1f} | {futile[v].mean():.1%} |")
    md.append("")

    md += ["## Forced accuracy (does stopping early cost anything?)", "",
           "| variant (layer) | n eps | answered | acc | cov | forced acc | diff forced vs no_futility |", "|---|---|---|---|---|---|---|"]
    for layer in ("none", "new"):
        rows = {v: A.Rows(out[v][layer]) for v in VARIANTS}
        boots = {v: A.boot(rows[v], names=("acc", "cov", "forced"), B=300) for v in VARIANTS}
        diffs = {v: A.boot_diff(rows[v], rows["no_futility"], "forced", B=300) for v in VARIANTS if v != "no_futility"}
        for v in VARIANTS:
            b = boots[v]
            extra = fmt(diffs[v]) if v != "no_futility" else ""
            md.append(f"| {v} ({layer}) | {b['n_eps']} | {b['n_answered']} | {fmt(b['acc'])} | {fmt(b['cov'])} | {fmt(b['forced'])} | {extra} |")

    (OUT / "futility_eval_report.md").write_text("\n".join(md))
    print("\n".join(md))


main()
