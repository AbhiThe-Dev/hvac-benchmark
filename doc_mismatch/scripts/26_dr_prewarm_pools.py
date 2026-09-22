"""Build (and cache) all reading pools the S-V study needs, in parallel."""
import sys, time
import multiprocessing as mp
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.dr import verifier_eval as V
from docmismatch.dr.pools import load_pool

def job(a):
    t, r, tel = a
    t0 = time.time(); load_pool(t, r, tel); return a, time.time() - t0

def main():
    ids, A = V.spec_ids(), V.arms()
    jobs = set()
    for arm, a in A.items():
        for t in a["train"]:
            for r in V.REPS:
                jobs.add((t, r, a["tel"]))
    for su in ("T1_in_range", "T2_regime", "T3_control", "T4_topology", "T5_climate", "T6_compound"):
        for t in ids[su]:
            for r in V.REPS:
                for tel in ("estimated", "legacy", "wide", "wide_distractors"):
                    jobs.add((t, r, tel))
    jobs = sorted(jobs, key=lambda x: -len(x[0]))
    print(len(jobs), "pools", flush=True)
    t0 = time.time()
    with mp.get_context("fork").Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 8) as P:
        for i, (a, dt) in enumerate(P.imap_unordered(job, jobs, chunksize=1)):
            if dt > 20 or (i + 1) % 50 == 0: print(i + 1, a, f"{dt:.0f}s", flush=True)
    print(f"done {time.time() - t0:.0f}s")
main()
