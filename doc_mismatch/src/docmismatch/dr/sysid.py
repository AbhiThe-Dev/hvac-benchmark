"""Per-building system identification (PREREGISTRATION_DR.md Addendum 2): a fixed additive per-(building, slot, channel) mean
correction, estimated at test time from that building's OWN evidence, no ground-truth labels, no access to the tested member.
Orthogonal to domain randomization: DR widens the TRAINING distribution; this adapts the FITTED model to the specific
building it is being applied to, using only what a real deployment would have (that building's own historical readings).
"""

from __future__ import annotations

import numpy as np

from ..active.model import ChannelModel, tf

MIN_N = 20      # below this many residuals, no correction (falls back to the unadapted population model)
PRIOR_N = 30    # shrinkage pseudo-count: bias *= n / (n + PRIOR_N)
TRIM = 0.10     # fraction trimmed from each tail before averaging (robustness to the few other members with their own injected error)


class BiasAdaptedModel:
    """Wraps a fitted ChannelModel, adding a fixed scalar to both class means. Delegates every other attribute
    (fit, kappa, rho, omega, rho_s, ...) to the wrapped model so it is a drop-in replacement in engine.run_episode."""

    def __init__(self, base: ChannelModel, bias: float):
        self._base = base
        self.bias = float(bias)

    def __getattr__(self, name):
        return getattr(self._base, name)

    def params(self, ctx: np.ndarray):
        mM, sM, mX, sX, pinfo = self._base.params(ctx)
        return [mM + self.bias, sM, mX + self.bias, sX, pinfo]


def _trimmed_shrunk_mean(resid: np.ndarray, trim: float = TRIM, prior_n: int = PRIOR_N) -> tuple[float, int]:
    n = len(resid)
    if n == 0:
        return 0.0, 0
    r = np.sort(resid)
    lo, hi = int(np.floor(n * trim)), n - int(np.floor(n * trim))
    core = r[lo:hi] if hi > lo else r
    m = float(core.mean())
    return m * n / (n + prior_n), n


def estimate_bias(pool, slot: str, k: int, model: ChannelModel, exclude_member: int | None = None,
                   min_n: int = MIN_N, prior_n: int = PRIOR_N, trim: float = TRIM) -> tuple[float, int]:
    """Robust, shrunk mean residual of the building's OWN (physically true) pairs against the fitted match-class mean,
    across ALL of the building's slices (its available "BAS history"), excluding `exclude_member`. Returns (bias, n_used);
    bias is 0.0 and n_used < min_n means "not enough data, fall back to the unadapted model" (the caller decides)."""
    sp = pool.slots[slot]
    mM, _, _, _, _ = model.params(pool.ctx)
    resid = []
    for m in range(len(sp.members)):
        if m == exclude_member:
            continue
        o = int(sp.truth[m])
        if o < 0:
            continue
        v = sp.E[:, k, o, m]
        f = np.isfinite(v)
        if not f.any():
            continue
        resid.append(tf(v[f]) - mM[f])
    resid = np.concatenate(resid) if resid else np.array([])
    bias, n = _trimmed_shrunk_mean(resid, trim, prior_n)
    return (bias, n) if n >= min_n else (0.0, n)


def adapt_models(pool, mods: dict[int, ChannelModel], slot: str, exclude_member: int | None = None,
                  min_n: int = MIN_N, prior_n: int = PRIOR_N, trim: float = TRIM) -> tuple[dict, dict]:
    """(adapted models dict, diagnostics dict k -> (bias, n_used)). `min_n`/`prior_n`/`trim` are exposed so a
    meta-learned (trim, tau) (see sysid_meta.py, PREREGISTRATION_DR.md Addendum 3) can replace the hand-picked defaults."""
    out, diag = {}, {}
    for k, mod in mods.items():
        bias, n = estimate_bias(pool, slot, k, mod, exclude_member=exclude_member, min_n=min_n, prior_n=prior_n, trim=trim)
        out[k] = BiasAdaptedModel(mod, bias) if bias != 0.0 else mod
        diag[k] = (bias, n)
    return out, diag
