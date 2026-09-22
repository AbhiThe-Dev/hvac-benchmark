"""Zero-shot sim-to-real transfer (PREREGISTRATION_DR.md Addendum): fit vav_zone on each arm's SIM buildings only, score on real DEV vav_zone episodes.
  .venv/bin/python doc_mismatch/scripts/30_dr_sim2real.py --procs 4
"""
import json, pickle, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.dr import verifier_eval as V, sim2real_eval as S2R
from docmismatch.dr.pools import DR_DIR

PROCS = int(sys.argv[sys.argv.index("--procs") + 1]) if "--procs" in sys.argv else 1
OUT = DR_DIR / "sim2real"


def main():
    cfg = V.make_cfg(("active", "random"))
    pool, eps = S2R.real_vav_zone_episodes()
    print(f"real vav_zone episodes: {len(eps)} across {len(pool.days)} days", flush=True)
    for arm, a in V.arms().items():
        f = OUT / f"rows_{arm}.pkl"
        if f.exists():
            print("cached", arm); continue
        t0 = time.time()
        pools = {t: {r: V.load_pool(t, r, a["tel"]) for r in V.REPS} for t in a["train"]}
        out = S2R.run_arm(a["train"], a["tel"], pools, cfg, pool, eps, procs=PROCS)
        f.write_bytes(pickle.dumps(out))
        print(arm, "ok" if out["ok"] else out.get("reason"), f"{time.time()-t0:.0f}s", flush=True)


main()
