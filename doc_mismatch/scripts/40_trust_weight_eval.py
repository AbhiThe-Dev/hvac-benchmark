"""Does a continuous, per-channel trust weight beat the binary exclude_struct? (PREREGISTRATION_DR.md Addendum 8)
All three variants run with Addendum 7's futility stopping on (the realistic deployed configuration):
  no_adaptation : all 3 channels full trust
  exclude_struct: channels 0+2 dropped entirely (Addendum 5's binary best)
  trust_weighted: every channel kept, weighted by its own real_channel_validity point estimate
  .venv/bin/python doc_mismatch/scripts/40_trust_weight_eval.py
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
VARIANTS = ["no_adaptation", "exclude_struct", "trust_weighted"]


def fmt(x):
    return f"{x['est']:.3f} [{x['lo']:.3f}, {x['hi']:.3f}]"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = make_cfg(("active",))
    cfg["sim_reps"] = [0]
    t0 = time.time()

    out = ME.run_trust_eval(cfg)
    (OUT / "trust_eval.pkl").write_bytes(pickle.dumps(out))
    print(f"done {time.time() - t0:.0f}s, n_real_episodes={out.get('_n_real_episodes')}", flush=True)
    print(f"per-channel trust weights (from real_channel_validity): {out.get('_weights')}", flush=True)

    md = ["# Continuous trust weight vs. binary exclusion (Addendum 8)", "",
          f"real DEV vav_zone episodes (n={out.get('_n_real_episodes')}), futility stopping on in all three "
          f"variants (window=4, margin=0.05). Trust weights derived from real_channel_validity: `{out.get('_weights')}`.",
          "", "## Technician reads", "", "| variant | mean n_read | median n_read |", "|---|---|---|"]
    n_read = {v: np.array([r["n_read"] for r in out[v]["raw"]]) for v in VARIANTS}
    for v in VARIANTS:
        md.append(f"| {v} | {n_read[v].mean():.1f} | {np.median(n_read[v]):.0f} |")
    md.append("")

    md += ["## Forced accuracy", "",
           "| variant (layer) | n eps | forced acc | diff vs exclude_struct |", "|---|---|---|---|"]
    for layer in ("none", "new"):
        rows = {v: A.Rows(out[v][layer]) for v in VARIANTS}
        boots = {v: A.boot(rows[v], names=("acc", "cov", "forced"), B=300) for v in VARIANTS}
        diffs = {v: A.boot_diff(rows[v], rows["exclude_struct"], "forced", B=300) for v in VARIANTS if v != "exclude_struct"}
        for v in VARIANTS:
            b = boots[v]
            extra = fmt(diffs[v]) if v != "exclude_struct" else ""
            md.append(f"| {v} ({layer}) | {b['n_eps']} | {fmt(b['forced'])} | {extra} |")

    (OUT / "trust_eval_report.md").write_text("\n".join(md))
    print("\n".join(md))


main()
