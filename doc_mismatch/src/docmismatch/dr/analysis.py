"""Metrics + building-cluster bootstrap for the S-V decision rows (see PREREGISTRATION_DR.md sec 6/7)."""

from __future__ import annotations

import numpy as np

CONF, REF = "CONFIRMED", "REFUTED"


def building(ep: str) -> str:
    return ep.split("|")[0]


class Rows:
    """decision rows of one (layer, policy) as arrays"""

    def __init__(self, rows: list[dict]):
        self.n = len(rows)
        self.ep = np.array([r["ep"] for r in rows])
        self.b = np.array([building(r["ep"]) for r in rows])
        self.wrong = np.array([bool(r["wrong"]) for r in rows])
        st = np.array([r["state"] for r in rows])
        self.ans = (st == CONF) | (st == REF)
        say = np.where(st == CONF, True, np.where(st == REF, False, np.array([bool(r["say_correct"]) for r in rows])))
        self.say = say                                       # "the documented connection is right"
        self.correct = self.say == (~self.wrong)
        self.conf = np.array([r.get("conf", np.nan) for r in rows], float)
        self.p = np.array([r["p_stop"] for r in rows], float)
        self.season = np.array([r["season"] for r in rows])
        self.family = np.array([r["family"] for r in rows])
        self.obs = np.array([r["obs"] for r in rows])
        self.unit = np.array([r["unit"] for r in rows])
        self.rep = np.array([r["rep"] for r in rows])
        self.n_read = np.array([r["n"] for r in rows], float)

    def sel(self, mask) -> "Rows":
        o = object.__new__(Rows)
        for k, v in self.__dict__.items():
            o.__dict__[k] = v[mask] if isinstance(v, np.ndarray) else v
        o.n = int(mask.sum())
        return o


def _bal(num, den):
    """class-balanced ratio: mean over the two classes of num_c/den_c (nan if a class has den 0)"""
    return num, den


def stat_acc_bal(R: Rows, w: np.ndarray | None = None) -> float:
    w = np.ones(R.n) if w is None else w
    r = []
    for c in (True, False):
        m = R.wrong == c
        a = w[m & R.ans].sum()
        r.append(w[m & R.ans & R.correct].sum() / a if a > 0 else np.nan)
    return float(np.nanmean(r)) if not all(np.isnan(r)) else np.nan


def stat_cov_bal(R: Rows, w=None) -> float:
    w = np.ones(R.n) if w is None else w
    r = []
    for c in (True, False):
        m = R.wrong == c
        d = w[m].sum()
        r.append(w[m & R.ans].sum() / d if d > 0 else np.nan)
    return float(np.nanmean(r))


def stat_forced_bal(R: Rows, w=None) -> float:
    w = np.ones(R.n) if w is None else w
    r = []
    for c in (True, False):
        m = R.wrong == c
        d = w[m].sum()
        r.append(w[m & R.correct].sum() / d if d > 0 else np.nan)
    return float(np.nanmean(r))


def stat_ece(R: Rows, w=None, bins=10) -> float:
    """expected calibration error of the posterior over ALL episodes (confidence = max(p, 1-p) in the verdict said), class-balanced"""
    w = np.ones(R.n) if w is None else w
    conf = np.maximum(R.p, 1 - R.p)
    cw = np.where(R.wrong, 0.5 / max(w[R.wrong].sum(), 1e-9), 0.5 / max(w[~R.wrong].sum(), 1e-9)) * w
    edges = np.linspace(0.5, 1.0, bins + 1)
    e = 0.0
    for i in range(bins):
        m = (conf >= edges[i]) & (conf <= edges[i + 1] if i == bins - 1 else conf < edges[i + 1])
        if cw[m].sum() > 0:
            e += cw[m].sum() * abs((cw[m] * R.correct[m]).sum() / cw[m].sum() - (cw[m] * conf[m]).sum() / cw[m].sum())
    return float(e)


def stat_stated_gap(R: Rows, w=None) -> float:
    """mean stated confidence of answered verdicts minus their realised accuracy (positive = overconfident), class-balanced"""
    w = np.ones(R.n) if w is None else w
    g = []
    for c in (True, False):
        m = (R.wrong == c) & R.ans
        if w[m].sum() > 0:
            g.append((w[m] * np.where(np.isfinite(R.conf[m]), R.conf[m], np.maximum(R.p[m], 1 - R.p[m]))).sum() / w[m].sum() - (w[m] * R.correct[m]).sum() / w[m].sum())
    return float(np.mean(g)) if g else np.nan


def stat_mean_reads(R: Rows, w=None) -> float:
    m = R.ans
    return float(R.n_read[m].mean()) if m.any() else np.nan


STATS = dict(acc=stat_acc_bal, cov=stat_cov_bal, forced=stat_forced_bal, ece=stat_ece, gap=stat_stated_gap)


def boot(R: Rows, names=("acc", "cov", "forced", "ece", "gap"), B: int = 1000, seed: int = 0, cluster: str = "b") -> dict:
    """point estimate + 95% building-cluster bootstrap CI for each statistic"""
    keys = getattr(R, cluster)
    ub = np.unique(keys)
    idx = {u: np.flatnonzero(keys == u) for u in ub}
    rng = np.random.default_rng(seed)
    out = {n: [STATS[n](R)] for n in names}
    for _ in range(B):
        pick = rng.choice(ub, len(ub))
        counts = {u: int((pick == u).sum()) for u in ub}
        w = np.zeros(R.n)
        for u, c in counts.items():
            w[idx[u]] = c
        for n in names:
            out[n].append(STATS[n](R, w))
    res = {}
    for n, v in out.items():
        v = np.array(v, float)
        res[n] = dict(est=float(v[0]), lo=float(np.nanpercentile(v[1:], 2.5)) if np.isfinite(v[1:]).any() else np.nan,
                      hi=float(np.nanpercentile(v[1:], 97.5)) if np.isfinite(v[1:]).any() else np.nan)
    res["n_eps"], res["n_answered"], res["n_bldg"] = R.n, int(R.ans.sum()), len(ub)
    return res


def boot_diff(RA: Rows, RB: Rows, name: str = "acc", B: int = 1000, seed: int = 0) -> dict:
    """paired building-cluster bootstrap of stat(A) - stat(B); buildings resampled jointly (both sides cover the same buildings)"""
    ub = np.unique(np.concatenate([RA.b, RB.b]))
    ia = {u: np.flatnonzero(RA.b == u) for u in ub}
    ib = {u: np.flatnonzero(RB.b == u) for u in ub}
    rng = np.random.default_rng(seed)
    f = STATS[name]
    est = f(RA) - f(RB)
    v = []
    for _ in range(B):
        pick = rng.choice(ub, len(ub))
        wa, wb = np.zeros(RA.n), np.zeros(RB.n)
        for u in ub:
            c = int((pick == u).sum())
            wa[ia[u]] = c
            wb[ib[u]] = c
        v.append(f(RA, wa) - f(RB, wb))
    v = np.array(v)
    return dict(est=float(est), lo=float(np.nanpercentile(v, 2.5)), hi=float(np.nanpercentile(v, 97.5)), n_bldg=len(ub))
