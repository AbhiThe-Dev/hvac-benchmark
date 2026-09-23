"""Reading likelihood: p(reading | hypothesis, operating context).

For one (slot, channel) the reading y = log(e + EPS) of a candidate pair is modelled, separately for the
two pair classes z in {M (candidate IS the owner), X (candidate is NOT the owner)}, as

    y = mu_z(c) + u + eps,   eps ~ N(0, sigma_z(c)^2),   u ~ N(0, tau_z^2)   (u shared by repeated readings of one pair)

where c is the operating context of the slice (outdoor temp, its diurnal swing, building load) and
mu_z, sigma_z are ridge regressions on phi(c). The pair-level random effect u is what stops repeated
readings of one pair (which share its systematic offset) from being counted as independent evidence.
`use_ctx=False` replaces phi(c) by a constant: ONE pooled distribution per class -- the "single fixed clean
baseline" assumption whose failure motivated this whole design; it is the with/without-context ablation.
The probability that a channel is informative at all (not flat / not enough samples) is also context-dependent.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .pools import Pool, compatible

EPS = 0.05
SD_FLOOR = 0.25   # y-space; keeps a spiky class (e.g. exact-zero errors) from producing unbounded likelihood ratios
TAU_FLOOR = 0.10
RIDGE = 1.0
MIN_TRAIN = 40
import os
BUILDING_SHIFT = os.environ.get('DM_BSHIFT', '1') == '1'


def tf(e):
    return np.log(np.maximum(e, 0.0) + EPS)


class Scaler:
    def __init__(self, ctx: np.ndarray):
        self.m = ctx.mean(0)
        self.s = ctx.std(0) + 1e-9
        self.lo = ctx.min(0)
        self.hi = ctx.max(0)

    def phi(self, ctx: np.ndarray, use_ctx, for_sd: bool = False) -> np.ndarray:
        """use_ctx: False = one pooled distribution | True = quadratic-in-OAT mean + context-dependent sd |
        'mean' = linear mean on all context features, pooled sd | 'oat' = linear mean on outdoor temp only, pooled sd."""
        if not use_ctx or (for_sd and use_ctx in ("mean", "oat", "info")):
            return np.ones((len(ctx), 1))
        z = (ctx - self.m) / self.s
        if use_ctx == "info":   # informativeness features only: all context columns, plus squares of oat and load (the schedule is non-monotone)
            return np.column_stack([np.ones(len(z)), z, z[:, :1] ** 2, z[:, -1:] ** 2])
        if use_ctx == "oat":
            return np.column_stack([np.ones(len(z)), z[:, :1]])
        if use_ctx == "mean":
            return np.column_stack([np.ones(len(z)), z])
        return np.column_stack([np.ones(len(z)), z, z[:, :1] ** 2])


def _ridge(P: np.ndarray, y: np.ndarray, lam: float = RIDGE, w: np.ndarray | None = None) -> np.ndarray:
    R = lam * np.eye(P.shape[1])
    R[0, 0] = 0.0
    if w is None:
        return np.linalg.solve(P.T @ P + R, P.T @ y)
    Pw = P * w[:, None]
    return np.linalg.solve(Pw.T @ P + R, Pw.T @ y)


def _logit_fit(X: np.ndarray, y: np.ndarray, lam: float = 1.0, iters: int = 25) -> np.ndarray:
    """Ridge-penalised logistic regression (Newton); intercept unpenalised."""
    w = np.zeros(X.shape[1])
    R = lam * np.eye(X.shape[1]); R[0, 0] = 0.0
    for _ in range(iters):
        p = 1.0 / (1.0 + np.exp(-np.clip(X @ w, -30, 30)))
        g = X.T @ (p - y) + R @ w
        H = (X.T * (p * (1 - p) + 1e-6)) @ X + R
        step = np.linalg.solve(H, g)
        w -= step
        if np.abs(step).max() < 1e-8:
            break
    return w


def _info_icc(ok: np.ndarray, unit: np.ndarray) -> float:
    """One-way ANOVA intraclass correlation of the informative flag within units (a slice x member): how strongly readings taken
    in the same slice share their informativeness (flat / powered-off stream). ~0 = independent, ~1 = all-or-nothing."""
    ug, inv = np.unique(unit, return_inverse=True)
    n_g = np.bincount(inv).astype(float)
    keep = n_g[inv] >= 2
    if keep.sum() < 20:
        return 0.0
    y, inv2 = ok[keep].astype(float), np.unique(inv[keep], return_inverse=True)[1]
    n_g = np.bincount(inv2).astype(float)
    mean_g = np.bincount(inv2, weights=y) / n_g
    k = len(n_g)
    n0 = (n_g.sum() - (n_g ** 2).sum() / n_g.sum()) / (k - 1) if k > 1 else n_g.mean()
    msb = (n_g * (mean_g - y.mean()) ** 2).sum() / max(k - 1, 1)
    msw = ((y - mean_g[inv2]) ** 2).sum() / max(len(y) - k, 1)
    return float(np.clip((msb - msw) / (msb + (n0 - 1) * msw + 1e-12), 0.0, 0.98))


@dataclass
class ClassFit:
    bm: np.ndarray
    bs: np.ndarray
    tau: float


@dataclass
class ChannelModel:
    slot: str
    k: int
    use_ctx: bool
    scaler: Scaler
    fit: dict          # "M"/"X" -> ClassFit
    binfo: np.ndarray  # informativeness regression
    n_train: int
    info_mode: str | None = None   # None: informativeness = linear regression on phi(ctx, use_ctx) (original). "info": logistic on all context features
    kappa: float | None = None     # None: no online informativeness learning. else beta-binomial prior strength for the slice-level informativeness update
    clip_ctx: bool = False         # True: clamp the context to the training range before evaluating the regressions (no linear extrapolation)
    rho: float = 0.0               # correlation of a pair's random effect across the slot's channels (0 = independent channels, the original model)
    cells: dict | None = None      # (pair id, unit) -> (standardised mean residual, n): used only to estimate rho across channels
    omega: float = 0.0             # sd of the slice-member effect: a common offset shared by ALL candidates' readings of one member in one slice (one channel). 0 = none (original model)
    rho_s: float = 0.0             # correlation of that slice effect across the slot's channels

    def params(self, ctx: np.ndarray):
        """(mu_M, sd_M, mu_X, sd_X, p_info) at each row of ctx."""
        if self.clip_ctx:
            ctx = np.clip(ctx, self.scaler.lo, self.scaler.hi)
        P = self.scaler.phi(ctx, self.use_ctx)
        Ps = self.scaler.phi(ctx, self.use_ctx, for_sd=True)
        out = []
        for z in ("M", "X"):
            f = self.fit[z]
            out += [P @ f.bm, np.maximum(SD_FLOOR, np.sqrt(np.pi / 2) * (Ps @ f.bs))]
        if self.info_mode is None:
            out.append(np.clip(P @ self.binfo, 0.03, 0.97))
        else:
            out.append(np.clip(1.0 / (1.0 + np.exp(-(self.scaler.phi(ctx, self.info_mode) @ self.binfo))), 0.03, 0.97))
        return out


def _training_rows(pools: list[Pool], slot: str, k: int, slice_masks: list[np.ndarray]):
    """Flatten labelled pair readings from training pools: (y, ctx row, class 0/1, group id, informative flag)."""
    ys, cs, zs, gs, ok, ts, us = [], [], [], [], [], [], []
    gid = 0
    for pi, (pool, sm) in enumerate(zip(pools, slice_masks)):
        sp = pool.slots.get(slot)
        if sp is None or k >= sp.E.shape[1]:
            continue
        idx = np.where(sm)[0]
        for m in range(len(sp.members)):
            t = sp.truth[m]
            for o in range(len(sp.owners)):
                if o != t and not compatible(sp, o, t):
                    continue
                v = sp.E[idx, k, o, m]
                fin = np.isfinite(v)
                ys.append(np.where(fin, tf(np.nan_to_num(v)), np.nan))
                cs.append(pool.ctx[idx])
                zs.append(np.full(len(idx), 0 if o == t else 1))
                gs.append(np.full(len(idx), gid))
                ok.append(fin)
                us.append(((pi * 100000 + idx) * 1000 + m).astype(np.int64))   # (pool, slice, member) unit: readings of one member in one slice
                ts.append(np.array([f's{x}' for x in pool.season[idx]], dtype=object) if pool.kind == 'real' else np.full(len(idx), pool.name.split('#')[0], dtype=object))
                gid += 1
    if not ys:
        return None
    return tuple(np.concatenate(a) for a in (ys, cs, zs, gs, ok, ts, us))


def fit_channel(pools: list[Pool], slot: str, k: int, use_ctx: bool, slice_masks: list[np.ndarray] | None = None, info_mode: str | None = None,
                online_info: bool = False, clip_ctx: bool = False) -> ChannelModel | None:
    if slice_masks is None:
        slice_masks = [np.ones(p.n_slices, dtype=bool) for p in pools]
    rows = _training_rows(pools, slot, k, slice_masks)
    if rows is None:
        return None
    y, c, z, g, ok, topo, units = rows
    sc = Scaler(np.concatenate([p.ctx[m] for p, m in zip(pools, slice_masks)]))
    P_all = sc.phi(c, use_ctx)
    Ps_all = sc.phi(c, use_ctx, for_sd=True)
    if info_mode is None:
        binfo = _ridge(P_all, ok.astype(float))
    else:
        binfo = _logit_fit(sc.phi(c, info_mode), ok.astype(float))
    kappa = None
    if online_info:
        # slice-level informativeness learning: the flag is shared across the readings of one (slice, member); prior strength from the ICC
        icc = _info_icc(ok, units)
        kappa = float(np.clip((1.0 - icc) / max(icc, 1e-3), 0.2, 50.0))
    fit = {}
    cell_acc: dict = {}
    for zi, name in ((0, "M"), (1, "X")):
        sel = ok & (z == zi)
        if sel.sum() < MIN_TRAIN:
            return None
        P, Ps, yy, gg = P_all[sel], Ps_all[sel], y[sel], g[sel]
        # every training building counts equally (a building with 10 alternatives per member must not dominate the class fit)
        tsel = topo[sel]
        cnt = {t: (tsel == t).sum() for t in np.unique(tsel)}
        w = np.array([1.0 / cnt[t] for t in tsel]); w *= len(w) / w.sum()
        bm = _ridge(P, yy, w=w)
        r = yy - P @ bm
        bs = _ridge(Ps, np.abs(r), w=w)
        sd = np.maximum(SD_FLOOR, np.sqrt(np.pi / 2) * (Ps @ bs))
        # pair-level random effect by method of moments on group-mean residuals
        ug, inv = np.unique(gg, return_inverse=True)
        n_g = np.bincount(inv)
        mean_r = np.bincount(inv, weights=r) / n_g
        exp_within = np.bincount(inv, weights=sd ** 2) / n_g ** 2
        tau2 = max(TAU_FLOOR ** 2, float(np.mean(mean_r ** 2 - exp_within)))
        # building-level shift: spread of per-building mean residuals (cannot be averaged away by repeating readings)
        tm = [r[topo[sel] == t].mean() for t in np.unique(topo[sel])]
        om2 = float(np.var(tm, ddof=1)) if (BUILDING_SHIFT and len(tm) >= 2) else 0.0
        fit[name] = ClassFit(bm, bs, float(np.sqrt(tau2 + om2)))
        zr = r / sd
        gt = np.array([f"{a}|{b}" for a, b in zip(gg, tsel)])
        for cell in np.unique(gt):
            mm = gt == cell
            cell_acc[cell] = (float(zr[mm].mean()), int(mm.sum()))
    return ChannelModel(slot, k, use_ctx, sc, fit, binfo, int(ok.sum()), info_mode, kappa, clip_ctx, 0.0, cell_acc)


def estimate_rho(models: dict[int, "ChannelModel"], min_n: int = 2) -> float:
    """Average correlation, across the slot's channels, of the pair-level mean residual (standardised; cells = pair x training unit with
    >= min_n readings in both channels). This is the share of a pair's offset that is common to all its channels (they are computed from
    the same two streams), so reading the same pair on another channel is NOT an independent look."""
    ks = sorted(models)
    cs = []
    for i, a in enumerate(ks):
        for b in ks[i + 1:]:
            ca, cb = models[a].cells, models[b].cells
            keys = [c for c in ca.keys() & cb.keys() if ca[c][1] >= min_n and cb[c][1] >= min_n]
            if len(keys) >= 12:
                x = np.array([[ca[c][0], cb[c][0]] for c in keys])
                if x.std(0).min() > 1e-6:
                    cs.append(np.corrcoef(x.T)[0, 1])
    return float(np.clip(np.mean(cs), 0.0, 0.9)) if cs else 0.0


def estimate_slice_effect(models: dict[int, "ChannelModel"], pools, slot, slice_masks=None) -> tuple[dict[int, float], float]:
    """Slice-member effect a_{s,m,k}: the readings of ONE member in ONE slice (channel k) by different candidate owners share a common offset (they use the same
    member stream over the same window). Method of moments on the class-mean residuals of training pairs, using cross-products of DIFFERENT candidates only (so the
    pair effect u, which is shared by readings of one pair, does not contaminate it): omega_k^2 = E[r_o r_o'] within a (pool, slice, member) group, and the
    cross-channel correlation rho_s from E[r^k_o r^l_o']. Returns ({k: omega_k}, rho_s)."""
    ks = sorted(models)
    num = {(a, b): 0.0 for a in ks for b in ks if a <= b}
    den = {(a, b): 0.0 for a in ks for b in ks if a <= b}
    if slice_masks is None:
        slice_masks = [np.ones(p.n_slices, dtype=bool) for p in pools]
    for pool, sm in zip(pools, slice_masks):
        sp = pool.slots.get(slot)
        if sp is None or max(ks, default=-1) >= sp.E.shape[1]:
            continue
        idx = np.where(sm)[0]
        if len(idx) == 0:
            continue
        par = {k: models[k].params(pool.ctx[idx]) for k in ks}
        for m in range(len(sp.members)):
            t = sp.truth[m]
            cand = [o for o in range(len(sp.owners)) if o == t or compatible(sp, o, t)]
            R = np.full((len(ks), len(idx), len(cand)), np.nan)
            for ki, k in enumerate(ks):
                mM, _, mX, _, _ = par[k]
                for ci, o in enumerate(cand):
                    v = sp.E[idx, k, o, m]
                    fin = np.isfinite(v)
                    R[ki, fin, ci] = tf(v[fin]) - (mM[fin] if o == t else mX[fin])
            fin = np.isfinite(R)
            R0 = np.where(fin, R, 0.0)
            n_ = fin.sum(-1).astype(float)                    # (K, S)
            S1 = R0.sum(-1)
            for ai, a in enumerate(ks):
                for bi, b in enumerate(ks):
                    if a > b:
                        continue
                    both = (fin[ai] & fin[bi]).sum(-1).astype(float)
                    cross = (R0[ai] * R0[bi]).sum(-1)
                    num[(a, b)] += float((S1[ai] * S1[bi] - cross).sum())
                    den[(a, b)] += float((n_[ai] * n_[bi] - both).sum())
    cov = {key: (num[key] / den[key] if den[key] > 20 else 0.0) for key in num}
    omega = {k: float(np.sqrt(max(cov[(k, k)], 0.0))) for k in ks}
    rs = [cov[(a, b)] / (omega[a] * omega[b]) for a in ks for b in ks if a < b and omega[a] > 1e-6 and omega[b] > 1e-6]
    return omega, float(np.clip(np.mean(rs), 0.0, 0.95)) if rs else 0.0


def fit_slot_models(pools, slot, use_ctx, slice_masks=None, shared_pair: bool = False, slice_effect: bool = False,
                     max_channel: int = 2, **fitkw) -> dict[int, ChannelModel]:
    """max_channel: 2 = original 3 channels (default, bit-identical to before Addendum 9). 3 = also fit channel 3
    (evidence.closure_channel, loop_branch only) -- opt-in only; PREREGISTRATION_DR.md Addendum 9 found this does
    NOT help loop_branch's resolution rate, so no caller in this codebase passes 3 by default."""
    out = {}
    for k in range(max_channel + 1):
        m = fit_channel(pools, slot, k, use_ctx, slice_masks, **fitkw)
        if m is not None:
            out[k] = m
    if shared_pair and len(out) >= 2:
        rho = estimate_rho(out)
        for m in out.values():
            m.rho = rho
    if slice_effect and out:
        om, rs = estimate_slice_effect(out, pools, slot, slice_masks)
        for k, m in out.items():
            m.omega, m.rho_s = om[k], rs
    return out


def static_dprime(models: dict[int, ChannelModel]) -> dict[int, float]:
    """Context-blind discriminability of each channel, for the fixed 'rule-based' ordering."""
    out = {}
    for k, m in models.items():
        c0 = np.zeros((1, m.scaler.m.shape[0])) + m.scaler.m
        mm, sm, mx, sx, _ = m.params(c0)
        out[k] = float(abs(mm[0] - mx[0]) / np.sqrt((sm[0] ** 2 + sx[0] ** 2) / 2))
    return out
