"""Nested TRAINING-data runs for the abstention rule (no held-out outcomes are used).

For an outer held-out unit O (a topology in simulation, a season in the real data) the abstention rule may only use
data from the other units. To learn how reliable confident verdicts are we therefore re-run the sequential verifier on
those training units in an INNER leave-one-unit-out fashion: hold out training unit H, fit the likelihood on the units
that are neither O nor H, run verification episodes on H. The resulting records (same format as the outer pickles)
are pure training data for O. Nothing here reads a held-out outcome of O. The only thing borrowed from the outer
pickle is the tempering factor beta (which the deployed configuration selected from training units only), so the inner
runs use the deployed calibration rather than the 2-unit fallback; pass beta_lookup=None to use the library default.

Read-only reuse of the engine / model / pools; nothing there is modified.
"""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

import os

from .engine import Episode, run_episode
from .selection import get as _get_variant
from .model import fit_slot_models
from .pools import SEASON_OF_WINDOW, Pool, load_or_build_sim

TOPOS = ["sys03_psz_ac", "sys07_vav_reheat", "vav_2ahu_2loops", "vav_3ahu_2loops"]
CASES = Path(__file__).resolve().parents[4] / "results" / "docmismatch" / "cases.jsonl"


def h32(s: str) -> int:
    return int(hashlib.sha1(s.encode()).hexdigest()[:8], 16)


def build_sim_episodes(pools: dict, cases: list) -> list[Episode]:
    """Same construction as scripts/12_active_sim.py: hard wrong edges + matched correct edges."""
    eps, seen = [], set()
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


def _var() -> dict:
    """selection variant of the deployed run being evaluated (env DM_SEL, as in scripts 12/14); default = original behaviour"""
    return _get_variant(os.environ.get("DM_SEL", ""))


def sim_inner(outer: str, inner: str, policies=("active",), ctx="oat", settings=("hist", "visit", "visit_loso"),
              reps=(0, 1), beta_lookup: dict | None = None, fallback_beta: float = 0.35) -> list[dict]:
    """Verification episodes on training topology `inner`, likelihood fitted on topologies other than (outer, inner)."""
    cases = [json.loads(l) for l in open(CASES)]
    train = [load_or_build_sim(t, r) for t in TOPOS if t not in (outer, inner) for r in (0, 1)]
    out, fits = [], {}
    for rep in reps:
        pools = {t: load_or_build_sim(t, rep) for t in TOPOS}
        eps = [e for e in build_sim_episodes(pools, cases) if e.meta["topo"] == inner]
        for e in eps:
            for setting in settings:
                w = (h32(e.ep_id) + 3 * rep) % 8
                if setting == "hist":
                    sl, drop = np.arange(e.pool.n_slices), None
                else:
                    sl, drop = np.where(e.pool.group == w)[0], (SEASON_OF_WINDOW[w] if setting == "visit_loso" else None)
                key = (e.slot, drop)
                if key not in fits:
                    masks = [np.ones(p.n_slices, bool) if drop is None else (p.season != drop) for p in train]
                    fits[key] = fit_slot_models(train, e.slot, ctx, masks, **_var()["fitkw"])
                mod = fits[key]
                if not mod:
                    continue
                beta = fallback_beta if beta_lookup is None else beta_lookup.get((setting, e.slot), beta_lookup.get(("*", e.slot), fallback_beta))
                for pol in policies:
                    r = run_episode(e, mod, sl, pol, tau=2.0, seed=h32(e.ep_id) % 10_000 + rep, rho=3.0, beta=beta, **_var()["runkw"])
                    if r is None:
                        continue
                    out.append(dict(setting=setting, policy=pol, rep=rep, ep=e.ep_id, slot=e.slot, beta=beta, traj=r.traj.astype(np.float32),
                                    wrong=e.is_wrong, group=e.group, outer=outer, inner=inner, **e.meta))
    return out


def real_inner(outer_season: int, inner_season: int, policies=("active",), ctx="oat", settings=("loso", "hist_loso"),
               beta_lookup: dict | None = None, fallback_beta: float = 0.35, n_wrong: int = 20, n_right: int = 10) -> list[dict]:
    from .. import real_frp as R
    from .real_pool import REAL_SLOTS, load_or_build_real
    pool = load_or_build_real()
    mask = (pool.season != outer_season) & (pool.season != inner_season)
    fits, out = {}, []
    for d, day in enumerate(pool.days):
        season = int(pool.season[pool.group == d][0])
        if season != inner_season:
            continue
        ser = pool.day_series[d]
        for slot in REAL_SLOTS:
            if slot not in fits:
                fits[slot] = fit_slot_models([pool], slot, ctx, [mask], **_var()["fitkw"])
            mod = fits[slot]
            if not mod:
                continue
            sp = pool.slots[slot]
            rng = np.random.default_rng(1000 + d * 7 + REAL_SLOTS.index(slot))
            pairs = [(a, b) for a in range(10) for b in range(10) if a != b]
            wrong = [pairs[i] for i in rng.choice(len(pairs), n_wrong, replace=False)]
            eps = [Episode(pool, slot, b, a, b, True, f"real|{day}|{slot}|{a}>{b}|wrong", f"{day}|{slot}", {}) for a, b in wrong]
            for b in rng.choice(10, n_right, replace=False):
                eps.append(Episode(pool, slot, int(b), int(b), int(b), False, f"real|{day}|{slot}|{b}|right", f"{day}|{slot}", {}))
            for e in eps:
                if e.is_wrong:
                    a, b = e.doc, e.member
                    e.meta = {"obs": R.observability(ser, R.Event(slot, min(a, b), max(a, b))), "family": R.FAMILY[slot]}
                else:
                    e.meta = {"obs": "n/a", "family": "clean"}
                for setting in settings:
                    sl = np.where(pool.group == d)[0] if setting == "loso" else np.where(pool.season == season)[0]
                    beta = fallback_beta if beta_lookup is None else beta_lookup.get((setting, slot), beta_lookup.get(("*", slot), fallback_beta))
                    for pol in policies:
                        r = run_episode(e, mod, sl, pol, tau=2.0, seed=h32(e.ep_id) % 10_000, beta=beta, **_var()["runkw"])
                        if r is None:
                            continue
                        out.append(dict(setting=setting, policy=pol, ep=e.ep_id, slot=slot, beta=beta, traj=r.traj.astype(np.float32), wrong=e.is_wrong,
                                        group=e.group, season=season, outer=outer_season, inner=inner_season, **e.meta))
    return out


# ---------------------------------------------------------------------------------------------- batch drivers
def beta_table(records: list[dict], unit_key: str) -> dict:
    """{(unit, setting, slot): median deployed beta}: the tempering factor the deployed configuration chose for that
    held-out unit (selected from training units only). Read from an outer pickle purely as a parameter."""
    d = defaultdict(list)
    for r in records:
        if r.get("ctx") and not r.get("unsupported") and r.get("beta") is not None and r["policy"] is not None:
            d[(r[unit_key], r["setting"], r["slot"])].append(r["beta"])
    return {k: float(np.median(v)) for k, v in d.items()}


def _sim_job(a):
    o, i, bl, pols, ctx = a
    return sim_inner(o, i, policies=pols, ctx=ctx, beta_lookup=bl)


def _real_job(a):
    o, i, bl, pols, ctx = a
    return real_inner(o, i, policies=pols, ctx=ctx, beta_lookup=bl)


def run_inner_all(sim_records, real_records, policies, ctx="oat", workers=8):
    """Inner training runs for every outer unit. Returns (sim_inner_records, real_inner_records)."""
    from concurrent.futures import ProcessPoolExecutor
    out = []
    for records, key, job, units in ((sim_records, "topo", _sim_job, [(o, i) for o in TOPOS for i in TOPOS if i != o]),
                                     (real_records, "season", _real_job, [(o, i) for o in range(4) for i in range(4) if i != o])):
        if records is None:
            out.append([])
            continue
        bt = beta_table(records, key)
        jobs = [(o, i, {k[1:]: v for k, v in bt.items() if k[0] == o}, tuple(policies), ctx) for o, i in units]
        with ProcessPoolExecutor(workers) as ex:
            out.append([x for r in ex.map(job, jobs) for x in r])
    return out[0], out[1]
