"""Calibration of the posterior's confidence on TRAINING buildings only (nested leave-one-building-out).

The pooled likelihood is overconfident when applied to a new building (the 'wrong owner' distribution depends on how
physically similar the candidates are, which is a per-building property). We temper the log-likelihood by beta in (0,1]
(posterior ~ prior * likelihood^beta), choosing beta per slot to minimise log-loss of P(doc correct) on the held-out
training building, over synthetic verification episodes read in random order at several evidence amounts.
"""

from __future__ import annotations

import numpy as np

from .engine import Episode, run_episode
from .model import fit_slot_models
from .pools import Pool, hypotheses

BETAS = (0.1, 0.2, 0.35, 0.5, 0.7, 1.0)
FALLBACK_BETA = 0.35
CHECK_AT = (1, 2, 4, 8)


def _episodes(pool: Pool, slot: str, rng) -> list[Episode]:
    sp = pool.slots[slot]
    out = []
    for m in range(len(sp.members)):
        t = int(sp.truth[m])
        out.append(Episode(pool, slot, m, t, t, False, f"{pool.name}|{slot}|{m}|r", "", {}))
        alts = [o for o in hypotheses(sp, t)[1:]]
        if alts:
            out.append(Episode(pool, slot, m, int(rng.choice(alts)), t, True, f"{pool.name}|{slot}|{m}|w", "", {}))
    return out


def calibrate_beta(train: list[Pool], slot: str, use_ctx: bool, masks: list[np.ndarray], seed: int = 0, policy: str = "random", fitkw: dict | None = None, runkw: dict | None = None) -> float:
    names = sorted({p.name.split("#")[0] for p, _ in zip(train, masks) if slot in p.slots})
    if len(names) < 3:      # need >=2 buildings to fit and 1 to hold out; with fewer, fall back to a fixed conservative value
        return FALLBACK_BETA
    rng = np.random.default_rng(seed)
    loss = {b: 0.0 for b in BETAS}
    cnt = 0
    for hold in names:
        tr = [(p, m) for p, m in zip(train, masks) if p.name.split("#")[0] != hold]
        te = [(p, m) for p, m in zip(train, masks) if p.name.split("#")[0] == hold and slot in p.slots][:1]
        mod = fit_slot_models([p for p, _ in tr], slot, use_ctx, [m for _, m in tr], **(fitkw or {}))
        if not mod or not te:
            continue
        pool, msk = te[0]
        idx = np.where(msk)[0]
        for e in _episodes(pool, slot, rng):
            for b in BETAS:
                r = run_episode(e, mod, idx, policy, tau=2.0, nmax=max(CHECK_AT), seed=len(e.ep_id), beta=b, **(runkw or {}))
                if r is None:
                    break
                for n in CHECK_AT:
                    p = float(np.clip(r.traj[n], 1e-4, 1 - 1e-4))
                    loss[b] -= np.log(1 - p if e.is_wrong else p)
            cnt += 1
    if cnt == 0:
        return FALLBACK_BETA
    return float(min(BETAS, key=lambda b: loss[b]))


def calibrate_beta_fixed_model(pool: Pool, slot: str, mod: dict, mask: np.ndarray, seed: int = 0, policy: str = "random",
                                runkw: dict | None = None, betas=BETAS, repeats: int = 5) -> tuple[float, dict]:
    """Same objective as `calibrate_beta`/`calibrate_beta_seasons` (minimise held-out log-loss of P(doc correct)),
    but for a likelihood that is ALREADY fit and held fixed (e.g. `mod` fit zero-shot on simulation, per
    Addendum 1) -- only the tempering exponent is chosen from real data, nested by SEASON so it is not fit and
    scored on the same real slices (never SEALED). Used by PREREGISTRATION_DR.md Addendum 6: the population
    likelihood stays a pure zero-shot sim transfer; only its confidence scaling is real-calibrated.
    `_episodes()` draws only one random "wrong" alternative per member, so a single seed's ~20-episode/season
    estimate is noisy (picks swing between adjacent grid points across seeds); `repeats` pools the log-loss of
    `repeats` independent draws before taking the argmin, the same "don't trust a single noisy grid search"
    discipline used elsewhere in this project. Returns (chosen beta, {beta: pooled log-loss})."""
    seasons = sorted(set(pool.season[mask]))
    if len(seasons) < 3 or not mod:
        return FALLBACK_BETA, {}
    loss = {b: 0.0 for b in betas}
    cnt = 0
    for rep in range(repeats):
        rng = np.random.default_rng(seed + rep)
        for hold in seasons:
            idx = np.where(mask & (pool.season == hold))[0]
            if len(idx) == 0:
                continue
            for e in _episodes(pool, slot, rng):
                for b in betas:
                    r = run_episode(e, mod, idx, policy, tau=2.0, nmax=max(CHECK_AT), seed=len(e.ep_id) + rep, beta=b, **(runkw or {}))
                    if r is None:
                        break
                    for n in CHECK_AT:
                        p = float(np.clip(r.traj[n], 1e-4, 1 - 1e-4))
                        loss[b] -= np.log(1 - p if e.is_wrong else p)
                cnt += 1
    chosen = float(min(betas, key=lambda b: loss[b])) if cnt else FALLBACK_BETA
    return chosen, loss


def calibrate_beta_seasons(pool: Pool, slot: str, use_ctx: bool, mask: np.ndarray, seed: int = 0, policy: str = "random", fitkw: dict | None = None, runkw: dict | None = None) -> float:
    """Same as `calibrate_beta` for the single-building real pool: the nested held-out unit is a SEASON."""
    seasons = sorted(set(pool.season[mask]))
    if len(seasons) < 3:
        return FALLBACK_BETA
    rng = np.random.default_rng(seed)
    loss = {b: 0.0 for b in BETAS}
    cnt = 0
    for hold in seasons:
        mod = fit_slot_models([pool], slot, use_ctx, [mask & (pool.season != hold)], **(fitkw or {}))
        idx = np.where(mask & (pool.season == hold))[0]
        if not mod or len(idx) == 0:
            continue
        for e in _episodes(pool, slot, rng):
            for b in BETAS:
                r = run_episode(e, mod, idx, policy, tau=2.0, nmax=max(CHECK_AT), seed=len(e.ep_id), beta=b, **(runkw or {}))
                if r is None:
                    break
                for n in CHECK_AT:
                    p = float(np.clip(r.traj[n], 1e-4, 1 - 1e-4))
                    loss[b] -= np.log(1 - p if e.is_wrong else p)
            cnt += 1
    return float(min(BETAS, key=lambda b: loss[b])) if cnt else FALLBACK_BETA
