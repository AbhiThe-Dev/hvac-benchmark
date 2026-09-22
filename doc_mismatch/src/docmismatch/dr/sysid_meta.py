"""Meta-learned low-dimensional shrinkage (PREREGISTRATION_DR.md Addendum 3): the SAME shrinkage form as `sysid.py`
(`trimmed_mean * n/(n+tau)`), but (trim, tau) are chosen by leave-one-building-out cross-validation across many
simulated buildings instead of hand-picked. Two parameters only, by design -- see the addendum for why.
"""

from __future__ import annotations

import numpy as np

from ..active.model import ChannelModel, tf

TRIMS = (0.0, 0.05, 0.10, 0.20)
TAUS = (0.0, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 30.0, 50.0, 80.0, 120.0, 200.0, 350.0, 600.0)  # extended downward: the
# original grid (5..600) bottomed out at its smallest value on the first fit, so the true optimum was outside the
# searched range -- a standard, honest refinement, made before any test-suite data was touched.
FRACTIONS = (0.15, 0.35, 0.6, 1.0)


def _residuals(pool, slot: str, k: int, model: ChannelModel, slice_idx: np.ndarray) -> np.ndarray:
    """All (member, slice) residuals of the building's own physically-true pairs against the reference model, restricted to `slice_idx`."""
    sp = pool.slots[slot]
    ctx = pool.ctx[slice_idx]
    mM, _, _, _, _ = model.params(ctx)
    out = []
    for m in range(len(sp.members)):
        o = int(sp.truth[m])
        if o < 0:
            continue
        v = sp.E[slice_idx, k, o, m]
        f = np.isfinite(v)
        if not f.any():
            continue
        out.append(tf(v[f]) - mM[f])
    return np.concatenate(out) if out else np.array([])


def _trimmed(resid: np.ndarray, trim: float) -> tuple[float, int, float]:
    """(trimmed mean, n, standard error of that mean)."""
    n = len(resid)
    if n == 0:
        return 0.0, 0, np.inf
    r = np.sort(resid)
    lo, hi = int(np.floor(n * trim)), n - int(np.floor(n * trim))
    core = r[lo:hi] if hi > lo else r
    m = float(core.mean())
    se = float(core.std(ddof=1) / np.sqrt(len(core))) if len(core) > 1 else np.inf
    return m, n, se


def build_examples(buildings: dict, slot_models: dict, fractions=FRACTIONS) -> list[dict]:
    """buildings: {building_id: Pool}. slot_models: {slot: {channel k: ChannelModel}} -- ONE global (trim, tau) is fit
    pooling every (building, slot, channel, fraction) example, matching sysid.py's single global constants. One example
    per (building, slot, channel, fraction): raw residuals at every candidate trim, plus the low-noise 'full' target
    (all slices, standard trim) used as the recovery objective."""
    out = []
    for bid, pool in buildings.items():
        n_slices = pool.n_slices
        for slot, mods in slot_models.items():
            if slot not in pool.slots:
                continue
            for k, model in mods.items():
                resid_full = {t: _trimmed(_residuals(pool, slot, k, model, np.arange(n_slices)), t) for t in TRIMS}
                full_target = resid_full[0.10][0]
                if resid_full[0.10][1] < 20:
                    continue  # not enough physical readings for this (building, slot, channel): not a usable meta-training task
                rng = np.random.default_rng(abs(hash((bid, slot, k))) % (2**32))
                for frac in fractions:
                    n_pick = max(1, int(round(n_slices * frac)))
                    idx = np.sort(rng.choice(n_slices, n_pick, replace=False))
                    resid = _residuals(pool, slot, k, model, idx)
                    out.append(dict(building=bid, slot=slot, k=k, frac=frac, full_target=full_target,
                                     resid_by_trim={t: _trimmed(resid, t) for t in TRIMS}))
    return out


def _mse(examples: list[dict], trim: float, tau: float) -> tuple[float, int]:
    err, n = 0.0, 0
    for e in examples:
        m, cnt, _ = e["resid_by_trim"][trim]
        pred = m * cnt / (cnt + tau) if (cnt + tau) > 0 else 0.0
        err += (pred - e["full_target"]) ** 2
        n += 1
    return (err / n if n else np.inf), n


def fit_shrinkage(examples: list[dict]) -> dict:
    """Leave-one-building-out cross-validated grid search over (trim, tau). Returns the chosen (trim, tau), the CV curve,
    and per-fold chosen values (diagnostic: how stable the choice is across buildings)."""
    buildings = sorted({e["building"] for e in examples})
    grid = [(t, u) for t in TRIMS for u in TAUS]
    cv_mse = {g: [] for g in grid}
    fold_best = {}
    for b in buildings:
        tr = [e for e in examples if e["building"] != b]
        te = [e for e in examples if e["building"] == b]
        if not tr or not te:
            continue
        best_g, best_v = None, np.inf
        for g in grid:
            v, _ = _mse(tr, *g)
            if v < best_v:
                best_g, best_v = g, v
        fold_best[b] = best_g
        for g in grid:
            v, _ = _mse(te, *g)
            cv_mse[g].append(v)
    mean_cv = {g: float(np.mean(v)) for g, v in cv_mse.items() if v}
    chosen = min(mean_cv, key=mean_cv.get)
    hand_picked = (0.10, 30.0)
    return dict(trim=chosen[0], tau=chosen[1], cv_mse=mean_cv, chosen_mse=mean_cv[chosen], hand_picked_mse=mean_cv.get(hand_picked),
                fold_best=fold_best, n_buildings=len(buildings), n_examples=len(examples))
