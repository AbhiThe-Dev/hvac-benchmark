"""Does excluding structurally-invalid `vav_zone` channels help (PREREGISTRATION_DR.md Addendum 5)?
(1) real DEV: plain rule + honest layer, `include` vs `exclude_stat` (channel 2 only, Addendum 5a's statistical
    finding) vs `exclude_struct` (channels 0+2, Addendum 5b's structural finding) -- paired day-cluster bootstrap.
(2) simulation-only ceiling on T1-T6 (baseline arm, plain rule): the SAME ablation where the channels DO carry
    real signal -- an upper bound on the value of recovering them, NOT evidence the real recommendation pays off.
  .venv/bin/python doc_mismatch/scripts/35_measurement_reco_eval.py
"""
import pickle
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.dr import analysis as A  # noqa: E402
from docmismatch.dr import measurement_eval as ME  # noqa: E402
from docmismatch.dr.pools import DR_DIR  # noqa: E402
from docmismatch.dr.verifier_eval import make_cfg, spec_ids  # noqa: E402

SUITES = ["T1_in_range", "T2_regime", "T3_control", "T4_topology", "T5_climate", "T6_compound"]
OUT = DR_DIR / "measurement"
VARIANTS = list(ME.VARIANTS)


def fmt(x):
    return f"{x['est']:.3f} [{x['lo']:.3f}, {x['hi']:.3f}]"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = make_cfg(("active",))
    cfg["sim_reps"] = [0]
    t0 = time.time()

    real_f, ceiling_f = OUT / "real_ablation.pkl", OUT / "sim_ceiling.pkl"
    if real_f.exists():
        real = pickle.loads(real_f.read_bytes())
        print(f"real ablation loaded from cache, n_real_episodes={real.get('_n_real_episodes')}", flush=True)
    else:
        real = ME.run_real_ablation(cfg)
        real_f.write_bytes(pickle.dumps(real))
        print(f"real ablation done {time.time() - t0:.0f}s, n_real_episodes={real.get('_n_real_episodes')}", flush=True)

    md = ["# Missing-measurement recommendation: does excluding it help? (Addendum 5)", "",
          f"real DEV vav_zone episodes (n={real.get('_n_real_episodes')}), building-cluster (day) bootstrap (300 resamples). "
          "`include`=all 3 channels, `exclude_stat`=channel 2 dropped (Addendum 5a), `exclude_struct`=channels 0+2 dropped (Addendum 5b).",
          "", "## Real DEV", ""]
    for layer in ("none", "new"):
        md += ["| variant | n eps | answered | acc | cov | forced acc | diff acc vs include | diff forced vs include |",
               "|---|---|---|---|---|---|---|---|"]
        rows = {v: A.Rows(real[v][layer]) for v in VARIANTS}
        boots = {v: A.boot(rows[v], names=("acc", "cov", "forced"), B=300) for v in VARIANTS}
        diffs = {v: A.boot_diff(rows[v], rows["include"], "acc", B=300) for v in VARIANTS if v != "include"}
        diffs_f = {v: A.boot_diff(rows[v], rows["include"], "forced", B=300) for v in VARIANTS if v != "include"}
        for v in VARIANTS:
            b = boots[v]
            extra = fmt(diffs[v]) if v != "include" else ""
            extra_f = fmt(diffs_f[v]) if v != "include" else ""
            md.append(f"| {v} ({layer}) | {b['n_eps']} | {b['n_answered']} | {fmt(b['acc'])} | {fmt(b['cov'])} | {fmt(b['forced'])} | {extra} | {extra_f} |")
        md.append("")

    if ceiling_f.exists():
        ceiling = pickle.loads(ceiling_f.read_bytes())
        print("sim ceiling loaded from cache", flush=True)
    else:
        ids = spec_ids()
        ceiling = ME.run_sim_ceiling(cfg, ids, SUITES)
        ceiling_f.write_bytes(pickle.dumps(ceiling))
        print(f"sim ceiling done {time.time() - t0:.0f}s", flush=True)

    md += ["## Simulation-only ceiling (T1-T6, baseline arm, plain rule) -- upper bound, NOT a real-world claim", "",
           "| suite | variant | n eps | answered | acc | cov | forced acc | diff acc vs include | diff forced vs include |",
           "|---|---|---|---|---|---|---|---|---|"]
    for su in SUITES:
        if not ceiling.get(su):
            continue
        rows = {v: A.Rows(ceiling[su][v]) for v in VARIANTS}
        boots = {v: A.boot(rows[v], names=("acc", "cov", "forced"), B=300) for v in VARIANTS}
        diffs = {v: A.boot_diff(rows[v], rows["include"], "acc", B=300) for v in VARIANTS if v != "include"}
        diffs_f = {v: A.boot_diff(rows[v], rows["include"], "forced", B=300) for v in VARIANTS if v != "include"}
        for v in VARIANTS:
            b = boots[v]
            extra = fmt(diffs[v]) if v != "include" else ""
            extra_f = fmt(diffs_f[v]) if v != "include" else ""
            md.append(f"| {su} | {v} | {b['n_eps']} | {b['n_answered']} | {fmt(b['acc'])} | {fmt(b['cov'])} | {fmt(b['forced'])} | {extra} | {extra_f} |")
    (OUT / "measurement_reco_report.md").write_text("\n".join(md))
    print("\n".join(md))


main()
