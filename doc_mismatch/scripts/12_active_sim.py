"""Sequential active verification on the simulated benchmark (hard cases of doc_mismatch/).

For each held-out topology the likelihood is fitted on the OTHER topologies only. Settings:
  hist        : readings may come from any of 48 day-slices across the year (a BAS historian pull)
  visit       : readings restricted to ONE 6-week window's 6 day-slices (a site visit; season is given, not chosen)
  visit_loso  : visit, and the likelihood is fitted WITHOUT that season's slices (unseen-season stress test)
Usage: 12_active_sim.py OUT.pkl [--quick]   (env DM_CTXMODE; DM_SEL = variant from docmismatch.active.selection, default = original; DM_PROCS = workers, default 1;
                                              DM_POLICIES = comma list overriding the policy set)
"""
import os, hashlib, json, pickle, sys, time
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.active.engine import POLICIES, Episode, run_episode
from docmismatch.active.calibrate import calibrate_beta
from docmismatch.active.model import fit_slot_models
from docmismatch.active.pools import SEASON_OF_WINDOW, load_or_build_sim
from docmismatch.active import selection as SEL
import multiprocessing as mp

TOPOS = ["sys03_psz_ac", "sys07_vav_reheat", "vav_2ahu_2loops", "vav_3ahu_2loops"]
CASES = ROOT.parent / "results" / "docmismatch" / "cases.jsonl"
QUICK = "--quick" in sys.argv
CALIB = "--nocalib" not in sys.argv
CTXM = {'full': True, 'oat': 'oat', 'mean': 'mean'}[os.environ.get('DM_CTXMODE', 'full')]   # context model for the with-context arm
REPS = (0,) if QUICK else (0, 1)
TAU = 0.95
VAR = SEL.get(os.environ.get('DM_SEL', ''))
PROCS = int(os.environ.get('DM_PROCS', '1'))
PLIST = tuple(os.environ['DM_POLICIES'].split(',')) if os.environ.get('DM_POLICIES') else tuple(POLICIES) + tuple(VAR['extra'])


def h32(s):
    return int(hashlib.sha1(s.encode()).hexdigest()[:8], 16)


def build_episodes(pools, cases):
    """positives = documented edges that are wrong (hard cases, by observability label); negatives = matched true edges."""
    eps = []
    seen = set()
    for c in cases:
        if c["difficulty"] != "hard":
            continue
        tid = c["topology_id"]
        pool = pools[tid]
        for slot, o, m in c["added"]:
            sp = pool.slots.get(slot)
            if sp is None or (tid, slot, o, m) in seen:
                continue
            seen.add((tid, slot, o, m))
            mi, di = sp.members.index(m), sp.owners.index(o)
            eps.append(Episode(pool, slot, mi, di, int(sp.truth[mi]), True, f"{tid}|{slot}|{o}>{m}|wrong", c["group_id"],
                               {"obs": c["observable"], "family": c["corruption_type"], "topo": tid, "dp": c["degree_preserving"]}))
    rng = np.random.default_rng(7)
    pos_by = defaultdict(list)
    for e in eps:
        pos_by[e.meta["topo"], e.slot].append(e)
    for (tid, slot), es in pos_by.items():
        sp = es[0].pool.slots[slot]
        wrong_members = {e.member for e in es}
        cand = [m for m in range(len(sp.members)) if m not in wrong_members] or list(range(len(sp.members)))
        for e in es:
            m = int(rng.choice(cand))
            eps.append(Episode(e.pool, slot, m, int(sp.truth[m]), int(sp.truth[m]), False, f"{tid}|{slot}|{sp.members[m]}|right|{e.ep_id}",
                               f"neg|{tid}|{slot}|{sp.members[m]}", {"obs": "n/a", "family": "clean", "topo": tid, "dp": True, "matched_to": e.meta["family"]}))
    return eps


CASE_LIST = None


def unit(arg):
    rep, test = arg
    pools = {t: load_or_build_sim(t, rep) for t in TOPOS}
    eps_all = build_episodes(pools, CASE_LIST)
    records = []
    train = [load_or_build_sim(t, r) for t in TOPOS if t != test for r in (0, 1)]
    eps = [e for e in eps_all if e.meta["topo"] == test]
    fits = {}

    def models(slot, use_ctx, drop_season):
        key = (slot, use_ctx, drop_season)
        if key not in fits:
            masks = [np.ones(p.n_slices, bool) if drop_season is None else (p.season != drop_season) for p in train]
            mod = fit_slot_models(train, slot, use_ctx, masks, **VAR["fitkw"])
            fits[key] = (mod, calibrate_beta(train, slot, use_ctx, masks, fitkw=VAR["fitkw"], runkw=VAR["runkw"]) if (mod and CALIB) else 1.0)
        return fits[key]

    for e in eps:
        # unsupported slot in training (e.g. loop_* absent from held-out topologies): reported, not scored
        for setting in ("hist", "visit", "visit_loso"):
            w = (h32(e.ep_id) + 3 * rep) % 8
            if setting == "hist":
                sl, drop = np.arange(e.pool.n_slices), None
            else:
                sl, drop = np.where(e.pool.group == w)[0], (SEASON_OF_WINDOW[w] if setting == "visit_loso" else None)
            for use_ctx in (CTXM, False):
                mod, beta = models(e.slot, use_ctx, drop)
                if not mod:
                    records.append(dict(setting=setting, ctx=bool(use_ctx), policy=None, rep=rep, ep=e.ep_id, slot=e.slot, unsupported=True, **e.meta, wrong=e.is_wrong, group=e.group))
                    continue
                for pol in PLIST:
                    for rho in ((1.0, 3.0, 10.0) if pol == "active_cost" else (3.0,)):
                        r = run_episode(e, mod, sl, pol, tau=2.0, seed=h32(e.ep_id) % 10_000 + rep, rho=rho, beta=beta, **VAR["runkw"])
                        if r is None:
                            continue
                        records.append(dict(setting=setting, ctx=bool(use_ctx), policy=pol, rho=rho, rep=rep, ep=e.ep_id, slot=e.slot, unsupported=False,
                                            beta=beta, traj=r.traj.astype(np.float32), cost_traj=r.cost_traj.astype(np.float32), info_traj=r.info_traj.astype(np.int16), k_seq=r.k_seq, wrong=e.is_wrong, group=e.group, **e.meta))
    return records, f"rep {rep} {test}: {len(eps)} episodes"


def main():
    global CASE_LIST
    out = Path(sys.argv[1])
    CASE_LIST = [json.loads(l) for l in open(CASES)]
    t0 = time.time()
    units = [(rep, test) for rep in REPS for test in TOPOS]
    if PROCS > 1:
        with mp.get_context("fork").Pool(PROCS) as P:
            res = P.map(unit, units, chunksize=1)
    else:
        res = [unit(u) for u in units]
    records = []
    for r, msg in res:
        records += r
        print(msg, flush=True)
    print(f"{len(records)} records, {time.time()-t0:.0f}s", flush=True)
    out.write_bytes(pickle.dumps(records))


main()
