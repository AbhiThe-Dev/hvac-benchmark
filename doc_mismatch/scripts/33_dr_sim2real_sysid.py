"""Does system-ID hold on real data? (PREREGISTRATION_DR.md Addendum 4)
  .venv/bin/python doc_mismatch/scripts/33_dr_sim2real_sysid.py
"""
import pickle, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.dr import verifier_eval as V, sim2real_sysid_eval as S2S
from docmismatch.dr import analysis as A
from docmismatch.dr.pools import DR_DIR

OUT = DR_DIR / "sysid"
VARIANTS = list(S2S.VARIANTS)


def fmt(x):
    return f"{x['est']:.3f} [{x['lo']:.3f}, {x['hi']:.3f}]"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = V.make_cfg(("active",))
    cfg["sim_reps"] = [0]
    t0 = time.time()
    out = S2S.run_check(cfg)
    (OUT / "raw_real.pkl").write_bytes(pickle.dumps(out))
    print(f"done {time.time()-t0:.0f}s, {out['_n_real_episodes']} real vav_zone episodes across {out['_n_real_days']} days", flush=True)
    print("inner-layer fit diagnostics:", out["_inner_diag"], flush=True)

    md = ["# Does system-ID hold on real data? (Addendum 4)", "",
          f"vav_zone only, real DEV pool ({out['_n_real_days']} days, {out['_n_real_episodes']} episodes), cluster = calendar day, "
          "building-cluster (day) bootstrap (300 resamples). Model fit ONLY on simulated buildings, zero real rows in any fit.", ""]
    for layer in ("none", "new"):
        md += [f"## layer = `{layer}`", "", "| variant | n eps | answered | acc | cov |", "|---|---|---|---|---|"]
        for v in VARIANTS:
            R = A.Rows(out[v][layer])
            b = A.boot(R, names=("acc", "cov"), B=300)
            md.append(f"| {v} | {b['n_eps']} | {b['n_answered']} | {fmt(b['acc'])} | {fmt(b['cov'])} |")
        md.append("")
    (OUT / "report_real.md").write_text("\n".join(md))
    print("\n".join(md))


main()
