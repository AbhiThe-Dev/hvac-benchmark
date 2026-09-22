"""Per-building system identification, three-way comparison: unadapted / hand-picked shrinkage (Addendum 2) /
meta-learned shrinkage (Addendum 3). Both decision layers. Baseline arm, rep 0, policy active, all six T1-T6 suites.
  .venv/bin/python doc_mismatch/scripts/31_dr_sysid.py
"""
import pickle, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.dr import verifier_eval as V, sysid_eval as SE
from docmismatch.dr import analysis as A
from docmismatch.dr.pools import DR_DIR

SUITES = ["T1_in_range", "T2_regime", "T3_control", "T4_topology", "T5_climate", "T6_compound"]
OUT = DR_DIR / "sysid"
VARIANTS = list(SE.VARIANTS)


def fmt(x):
    return f"{x['est']:.3f} [{x['lo']:.3f}, {x['hi']:.3f}]"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = V.make_cfg(("active",))
    cfg["sim_reps"] = [0]
    ids = V.spec_ids()
    t0 = time.time()
    out = SE.run_baseline_check(cfg, ids, SUITES)
    (OUT / "raw_3way.pkl").write_bytes(pickle.dumps(out))
    print(f"done {time.time()-t0:.0f}s", flush=True)
    print("inner-layer fit diagnostics:", {v: out["_inner_diag"][v] for v in VARIANTS}, flush=True)

    md = ["# Per-building system identification: three-way comparison", "",
          "Baseline arm, policy `active`, building-cluster bootstrap (300 resamples). `base`=unadapted, "
          "`hand`=Addendum 2 (trim=0.10, tau=30, hand-picked), `meta`=Addendum 3 (trim=0.10, tau=0.5, "
          "chosen by leave-one-building-out CV across 40 simulated buildings). `none`=plain rule, "
          "`new`=calibrated reliability layer (fit per variant on that variant's own inner records).", ""]
    for layer in ("none", "new"):
        md += [f"## layer = `{layer}`", "", "| suite | variant | n eps | answered | acc | cov | diff acc vs base | diff acc meta vs hand |", "|---|---|---|---|---|---|---|---|"]
        for su in SUITES:
            rows = {v: A.Rows(out[su][v][layer]) for v in VARIANTS}
            boots = {v: A.boot(rows[v], names=("acc", "cov"), B=300) for v in VARIANTS}
            d_base = {v: A.boot_diff(rows[v], rows["base"], "acc", B=300) for v in ("hand", "meta")}
            d_hm = A.boot_diff(rows["meta"], rows["hand"], "acc", B=300)
            for v in VARIANTS:
                b = boots[v]
                extra = f"{fmt(d_base[v])}" if v != "base" else ""
                extra2 = fmt(d_hm) if v == "meta" else ""
                md.append(f"| {su} | {v} | {b['n_eps']} | {b['n_answered']} | {fmt(b['acc'])} | {fmt(b['cov'])} | {extra} | {extra2} |")
        md.append("")
    (OUT / "report_3way.md").write_text("\n".join(md))
    print("\n".join(md))


main()
