"""Sequential active verification on REAL field data (ORNL RTU-VAV research facility, LBNL FDD Data Sets, CC BY 4.0).

One building, 14 days, 4 seasons. Wrong documentation = the same synthetic swaps as 08/09_real (documentation-only; the
sensor data is untouched); truth = the dataset's own point naming. Settings (likelihood always fitted on the OTHER data):
  lodo       : pool = the day's 6 four-hour blocks; likelihood excludes only that day (neighbouring days of the same season remain)
  loso       : same pool; likelihood excludes that day's whole SEASON (unseen operating regime)
  hist_loso  : pool = every block of that season (a historian pull); likelihood excludes the season
Usage: 14_active_real.py OUT.pkl      (env DM_CTXMODE = full|oat|mean; DM_SEL = variant from docmismatch.active.selection, default = original;
                                       DM_PROCS = worker processes, default 1; DM_POLICIES = comma list overriding the policy set)
"""
import os, hashlib, pickle, sys, time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import real_frp as R
from docmismatch.active.calibrate import calibrate_beta_seasons
from docmismatch.active.engine import POLICIES, Episode, run_episode
from docmismatch.active.model import fit_slot_models
from docmismatch.active.real_pool import REAL_SLOTS, load_or_build_real
from docmismatch.active import selection as SEL
import multiprocessing as mp

CTXM = {'full': True, 'oat': 'oat', 'mean': 'mean'}[os.environ.get('DM_CTXMODE', 'full')]   # context model for the with-context arm

N_WRONG, N_RIGHT = 20, 10
VAR = SEL.get(os.environ.get('DM_SEL', ''))
PROCS = int(os.environ.get('DM_PROCS', '1'))
PLIST = tuple(os.environ['DM_POLICIES'].split(',')) if os.environ.get('DM_POLICIES') else tuple(POLICIES) + tuple(VAR['extra'])


def h32(s):
    return int(hashlib.sha1(s.encode()).hexdigest()[:8], 16)


POOL = None
JOBS = []       # [(day index, [episodes])]
FITS = {}


def _fit_key(job):
    slot, use_ctx, key, mask = job
    mod = fit_slot_models([POOL], slot, use_ctx, [mask], **VAR["fitkw"])
    return (slot, use_ctx, key), (mod, calibrate_beta_seasons(POOL, slot, use_ctx, mask, fitkw=VAR["fitkw"], runkw=VAR["runkw"]) if mod else 1.0)


def _run_day(item):
    d, eps = item
    pool = POOL
    day = pool.days[d]
    season = int(pool.season[pool.group == d][0])
    records = []
    for e in eps:
        slot = e.slot
        for setting in ("lodo", "loso", "hist_loso"):
            if setting == "lodo":
                key, sl = ("d", d), np.where(pool.group == d)[0]
            elif setting == "loso":
                key, sl = ("s", season), np.where(pool.group == d)[0]
            else:
                key, sl = ("s", season), np.where(pool.season == season)[0]
            for use_ctx in (CTXM, False):
                mod, beta = FITS[(slot, use_ctx, key)]
                if not mod:
                    records.append(dict(setting=setting, ctx=bool(use_ctx), policy=None, ep=e.ep_id, slot=slot, unsupported=True, wrong=e.is_wrong, group=e.group, season=season, **e.meta))
                    continue
                for pol in PLIST:
                    if pol == "active_cost":
                        continue   # no credible cost tiers on the real data (all channels use the same two streams)
                    r = run_episode(e, mod, sl, pol, tau=2.0, seed=h32(e.ep_id) % 10_000, beta=beta, **VAR["runkw"])
                    if r is None:
                        continue
                    records.append(dict(setting=setting, ctx=bool(use_ctx), policy=pol, rho=3.0, ep=e.ep_id, slot=slot, unsupported=False, beta=beta,
                                        traj=r.traj.astype(np.float32), cost_traj=r.cost_traj.astype(np.float32), info_traj=r.info_traj.astype(np.int16), k_seq=r.k_seq,
                                        wrong=e.is_wrong, group=e.group, season=season, **e.meta))
    return records


def main():
    global POOL, JOBS
    out = Path(sys.argv[1])
    POOL = pool = load_or_build_real()
    rng = np.random.default_rng(11)
    t0 = time.time()
    for d, day in enumerate(pool.days):     # episodes are drawn sequentially so the rng stream (hence the episode set) is identical to the original script
        ser = pool.day_series[d]
        eps_day = []
        for slot in REAL_SLOTS:
            pairs = [(a, b) for a in range(10) for b in range(10) if a != b]
            wrong = [pairs[i] for i in rng.choice(len(pairs), N_WRONG, replace=False)]
            eps = [Episode(pool, slot, b, a, b, True, f"real|{day}|{slot}|{a}>{b}|wrong", f"{day}|{slot}", {}) for a, b in wrong]
            for b in rng.choice(10, N_RIGHT, replace=False):
                eps.append(Episode(pool, slot, int(b), int(b), int(b), False, f"real|{day}|{slot}|{b}|right", f"{day}|{slot}", {}))
            for e in eps:
                if e.is_wrong:
                    a, b = e.doc, e.member
                    e.meta = {"obs": R.observability(ser, R.Event(slot, min(a, b), max(a, b))), "same_floor": R.ROOMS[a][0] == R.ROOMS[b][0], "family": R.FAMILY[slot]}
                else:
                    e.meta = {"obs": "n/a", "same_floor": True, "family": "clean"}
            eps_day += eps
        JOBS.append((d, eps_day))
    fit_jobs, seen = [], set()
    for d, _ in JOBS:
        season = int(pool.season[pool.group == d][0])
        for slot in REAL_SLOTS:
            for use_ctx in (CTXM, False):
                for key, mask in ((("d", d), pool.group != d), (("s", season), pool.season != season)):
                    if (slot, use_ctx, key) not in seen:
                        seen.add((slot, use_ctx, key))
                        fit_jobs.append((slot, use_ctx, key, mask))
    ctx = mp.get_context("fork")
    if PROCS > 1:
        with ctx.Pool(PROCS) as P:
            FITS.update(dict(P.map(_fit_key, fit_jobs)))
        print(f"fits done {time.time()-t0:.0f}s", flush=True)
        with ctx.Pool(PROCS) as P:
            chunks = P.map(_run_day, JOBS, chunksize=1)
    else:
        FITS.update(dict(map(_fit_key, fit_jobs)))
        chunks = [_run_day(j) for j in JOBS]
    records = [r for c in chunks for r in c]
    print(f"{len(records)} records, {time.time()-t0:.0f}s", flush=True)
    out.write_bytes(pickle.dumps(records))


main()
