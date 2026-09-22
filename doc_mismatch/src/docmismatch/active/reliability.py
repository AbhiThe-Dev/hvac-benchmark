"""Case-level reliability layer: a learned, calibrated model of P(verdict correct | decision-time features).

Replaces the slot/season-level abstention of `abstain.py` (which is kept unchanged, and remains available as the "legacy" layer for
before/after comparisons). Everything here is fitted on TRAINING-unit runs only (inner leave-one-unit-out runs of the verifier, see
`readiness.py`) and uses only quantities available at decision time: the posterior history, the readings taken and how they scored
under the fitted likelihood, and the operating context of those readings relative to the data the likelihood was fitted on. It never
uses `wrong`, the benchmark `obs` label, or any outcome of the held-out unit as an input (`wrong` enters only as the training target of
TRAINING records).

Pipeline (per policy):
  1. features at the stopping point (first crossing of the posterior threshold; if none, the verdict is FLAGGED "insufficient evidence")
  2. ridge-logistic score s = P(correct | features), class-balanced weights, fitted on the inner records
  3. leave-one-inner-unit-out out-of-fold scores  ->  isotonic calibration  +  a cluster-aware conservative lower bound of the
     accuracy of the answered set {s >= t}; the answer threshold t is the largest answered set (scanning from the top, contiguous) whose
     lower bound >= the nominal level. Per-slot tightening (never loosening) from the slot's own out-of-fold record.
  4. answered verdicts carry the calibrated probability; everything else is FLAGGED with a reason.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .abstain import beta_quantile

FEATURES = ("logit_abs", "gap12", "n", "n_info", "info_frac", "n_owners_info", "n_slices_info", "n_info_doc", "agree", "agree_slices",
            "zmin_mean", "zmin_max", "zmin_frac3", "oat_excess", "nn_dist", "say_correct", "n_info_alt", "log_h", "slot_power")
FI = {f: i for i, f in enumerate(FEATURES)}
NOMINAL = 0.95
CAP = 24
FLAG_STATES = ("FLAGGED",)
CONFIRMED, REFUTED, FLAGGED = "CONFIRMED", "REFUTED", "FLAGGED"


# ---------------------------------------------------------------------------------------------- regime support
@dataclass
class Support:
    """Operating-context coverage of the data a likelihood was fitted on (standardised context of the training slices)."""
    mean: np.ndarray
    std: np.ndarray
    lo: np.ndarray
    hi: np.ndarray
    pts: np.ndarray

    @classmethod
    def from_ctx(cls, ctx: np.ndarray) -> "Support":
        ctx = np.asarray(ctx, float)
        m, s = ctx.mean(0), ctx.std(0) + 1e-9
        return cls(m, s, ctx.min(0), ctx.max(0), (ctx - m) / s)

    def oat_excess(self, ctx: np.ndarray) -> np.ndarray:
        """how far (in training SDs) the outdoor temperature lies outside the training range; 0 inside"""
        o = ctx[:, 0]
        return np.maximum(0.0, np.maximum(self.lo[0] - o, o - self.hi[0])) / self.std[0]

    def nn_dist(self, ctx: np.ndarray) -> np.ndarray:
        z = (ctx - self.mean) / self.std
        d = np.sqrt(((z[:, None, :] - self.pts[None, :, :]) ** 2).sum(-1))
        return d.min(1)


# ---------------------------------------------------------------------------------------------- decision-time features
def first_cross(traj, tau: float = 0.95) -> tuple[bool, int]:
    t = np.asarray(traj, float)
    hit = np.flatnonzero((t >= tau) | (t <= 1 - tau))
    return (True, int(hit[0])) if len(hit) else (False, CAP)


def features_at(dg: dict, n: int, support: Support, slot_power: float = 0.5) -> np.ndarray:
    """Feature vector of the belief state after the first `n` readings of one episode (`dg` = Result.diag)."""
    post = dg["post"][min(n, len(dg["post"]) - 1)].astype(float)
    H = dg["H"]
    pd = float(np.clip(post[0], 1e-9, 1 - 1e-9))
    logit = np.log(pd / (1 - pd))
    srt = np.sort(post)[::-1]
    gap12 = np.log(max(srt[0], 1e-12) / max(srt[1], 1e-12)) if H > 1 else 0.0
    say = pd >= 0.5
    j, info, s = dg["j"][:n], dg["info"][:n], dg["s"][:n]
    ii = np.flatnonzero(info)
    n_info = len(ii)
    n_owners = len(set(j[ii].tolist()))
    n_slices = len(set(s[ii].tolist()))
    doc = ii[j[ii] == 0]
    # evidence FOR "the documented owner is the owner" from each informative reading: llr if the reading was of the documented pair, else -llr
    ev = np.where(j[ii] == 0, 1.0, -1.0) * dg["llr"][:n][ii]
    if n_info:
        agree = float(np.mean((ev > 0) if say else (ev < 0)))
        sl = np.unique(s[ii])
        sm = np.array([ev[s[ii] == u].mean() for u in sl])
        agree_sl = float(np.mean((sm > 0) if say else (sm < 0)))
        zmin = np.minimum(np.abs(dg["zM"][:n][ii]), np.abs(dg["zX"][:n][ii]))
        ctx = dg["ctx"][:n][ii]
        exc, nn = float(support.oat_excess(ctx).max()), float(support.nn_dist(ctx).mean())
        zm, zx, z3 = float(zmin.mean()), float(zmin.max()), float((zmin > 3).mean())
    else:
        agree, agree_sl, zm, zx, z3, exc, nn = 0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0
    alt_rank = np.argsort(-post[1:])[0] + 1 if H > 1 else 0
    n_alt = int(np.sum(j[ii] == alt_rank)) if H > 1 else 0
    f = np.array([min(abs(logit), 12.0), min(gap12, 12.0), n, n_info, n_info / max(n, 1), n_owners, n_slices, len(doc), agree, agree_sl,
                  zm, min(zx, 12.0), z3, exc, nn, float(say), n_alt, np.log(H), slot_power], float)
    return f


# ---------------------------------------------------------------------------------------------- small numerics
def _logit_fit(X, y, w, lam=3.0, iters=40):
    beta = np.zeros(X.shape[1])
    R = lam * np.eye(X.shape[1]); R[0, 0] = 0.0
    for _ in range(iters):
        p = 1.0 / (1.0 + np.exp(-np.clip(X @ beta, -30, 30)))
        g = X.T @ (w * (p - y)) + R @ beta
        Hm = (X.T * (w * p * (1 - p) + 1e-6)) @ X + R
        step = np.linalg.solve(Hm, g)
        beta -= step
        if np.abs(step).max() < 1e-7:
            break
    return beta


def pav(x, y, w):
    """isotonic (non-decreasing) regression by pool-adjacent-violators; returns (x knots, fitted values) sorted by x."""
    o = np.argsort(x, kind="stable")
    xs, ys, ws = np.asarray(x)[o], np.asarray(y, float)[o], np.asarray(w, float)[o]
    blocks = []
    for xi, yi, wi in zip(xs, ys, ws):
        blocks.append([yi * wi, wi, xi, xi])
        while len(blocks) > 1 and blocks[-2][0] / blocks[-2][1] >= blocks[-1][0] / blocks[-1][1]:
            a = blocks.pop(); b = blocks.pop()
            blocks.append([a[0] + b[0], a[1] + b[1], b[2], a[3]])
    kx, kv = [], []
    for sy, sw, lo, hi in blocks:
        kx += [lo, hi]; kv += [sy / sw, sy / sw]
    return np.array(kx), np.array(kv)


def balanced_weights(wrong: np.ndarray) -> np.ndarray:
    """each class (wrong-documentation / correct-documentation) contributes half of the total weight"""
    w = np.ones(len(wrong))
    for c in (True, False):
        m = wrong == c
        if m.any():
            w[m] = 0.5 / m.sum()
    return w * len(w) / w.sum()


def prior_balanced_acc(ok, wrong, answered, w_ep=None):
    """P(verdict right | answered) under a balanced prior over episode classes: (sum_c ok_c/N_c)/(sum_c ans_c/N_c) with N_c = class episode counts.
    `answered` marks episodes with a verdict; `ok` is only read where answered."""
    num = den = 0.0
    for c in (True, False):
        m = wrong == c
        if not m.any():
            continue
        num += (ok & answered & m).sum() / m.sum()
        den += (answered & m).sum() / m.sum()
    return num / den if den > 0 else np.nan


def design_effect(ok, cluster, mask):
    """Kish-style design effect of the correctness indicator within clusters (one-way ANOVA ICC), floored at 1."""
    y = ok[mask].astype(float)
    if len(y) < 20:
        return 1.0
    cl = np.asarray(cluster)[mask]
    ug, inv = np.unique(cl, return_inverse=True)
    if len(ug) < 2:
        return 1.0
    ng = np.bincount(inv).astype(float)
    mg = np.bincount(inv, weights=y) / ng
    k = len(ug)
    n0 = (ng.sum() - (ng ** 2).sum() / ng.sum()) / (k - 1)
    msb = (ng * (mg - y.mean()) ** 2).sum() / (k - 1)
    msw = ((y - mg[inv]) ** 2).sum() / max(len(y) - k, 1)
    icc = float(np.clip((msb - msw) / (msb + (n0 - 1) * msw + 1e-12), 0.0, 1.0))
    return float(max(1.0, 1 + (ng.mean() - 1) * icc))


def conservative_lb(acc, n_ep, n_clusters, deff, q=0.10):
    """Beta lower bound with an effective sample size that accounts for within-cluster correlation (never above the number of episodes,
    never below the number of clusters)."""
    n_eff = float(np.clip(n_ep / max(deff, 1.0), min(n_clusters, n_ep), n_ep))
    return beta_quantile(1 + acc * n_eff, 1 + (1 - acc) * n_eff, q)


# ---------------------------------------------------------------------------------------------- the layer
@dataclass
class Verdict:
    state: str          # CONFIRMED | REFUTED | FLAGGED
    reason: str
    conf: float         # calibrated P(verdict correct) for answered verdicts; nan for flags
    score: float


@dataclass
class ReliabilityLayer:
    nominal: float = NOMINAL
    q: float = 0.10               # one-sided level of the lower bound
    lb_floor: float = 0.90        # required lower bound of the answered tail's accuracy (its point estimate must reach `nominal`)
    lam: float = 3.0
    min_clusters: int = 6         # OOF clusters required in the answered tail
    slot_min_clusters: int = 6
    per_slot: bool = True
    features: tuple = FEATURES    # subset used by the score (ablations)
    use_slot_power: bool = True
    # fitted
    mu: np.ndarray = None
    sd: np.ndarray = None
    lo: np.ndarray = None
    hi: np.ndarray = None
    coef: np.ndarray = None
    iso: tuple = None
    t_global: float = np.inf
    t_slot: dict = field(default_factory=dict)
    slot_pow: dict = field(default_factory=dict)
    diag: dict = field(default_factory=dict)

    # -- helpers
    def _cols(self):
        cols = [FI[f] for f in self.features if f != "slot_power" or self.use_slot_power]
        return cols

    def _X(self, F):
        Fc = np.clip(F, self.lo, self.hi)
        Z = (Fc - self.mu) / self.sd
        return np.column_stack([np.ones(len(Z)), Z[:, self._cols()]])

    def _fit_score(self, F, y, w):
        self.lo, self.hi = F.min(0), F.max(0)
        self.mu, self.sd = F.mean(0), F.std(0) + 1e-9
        self.coef = _logit_fit(self._X(F), y, w, self.lam)

    def raw_score(self, F):
        return 1.0 / (1.0 + np.exp(-np.clip(self._X(np.atleast_2d(F)) @ self.coef, -30, 30)))

    # -- fitting
    @staticmethod
    def slot_power_table(recs, exclude_unit=None):
        """training coverage (class-balanced share of episodes that cross the threshold) of each slot, optionally leaving a unit out"""
        out = {}
        for slot in {r["slot"] for r in recs}:
            rs = [r for r in recs if r["slot"] == slot and r["unit"] != exclude_unit]
            if not rs:
                continue
            wr = np.array([r["wrong"] for r in rs]); cr = np.array([r["crossed"] for r in rs])
            out[slot] = float(np.mean([cr[wr == c].mean() for c in (True, False) if (wr == c).any()]))
        return out

    def fit_all(self, recs_all: list[dict]) -> "ReliabilityLayer":
        """Fit from ALL inner (training-unit) records, crossed or not. Record keys: f (feature vector at the stop), crossed, say_correct, wrong (TARGET,
        training records only), slot, unit (inner unit id), cluster."""
        self._all = recs_all
        self.slot_pow = self.slot_power_table(recs_all)
        n_cross = sum(r["crossed"] for r in recs_all)
        if n_cross < 30 or len({r["unit"] for r in recs_all if r["crossed"]}) < 2:
            self.t_global, self.mu = np.inf, None
            self.diag = dict(reason="too little training data", n=n_cross)
            return self
        units = sorted({r["unit"] for r in recs_all}, key=str)
        spt = {u: self.slot_power_table(recs_all, exclude_unit=u) for u in units}   # slot power for a training row excludes the row's own unit
        F = np.array([[*np.array(r["f"], float)[:FI["slot_power"]], spt[r["unit"]].get(r["slot"], 0.5)] for r in recs_all])
        cm = np.array([r["crossed"] for r in recs_all])
        ok = np.array([bool(r["crossed"]) and r["say_correct"] == (not r["wrong"]) for r in recs_all])
        wrong = np.array([r["wrong"] for r in recs_all])
        w = balanced_weights(wrong)
        cl = np.array([r["cluster"] for r in recs_all]); un = np.array([r["unit"] for r in recs_all], dtype=object)
        sl_all = np.array([r["slot"] for r in recs_all])
        oof = np.full(len(recs_all), np.nan)
        for u in units:
            tr, te = cm & (un != u), un == u
            if tr.sum() < 20:
                continue
            sub = ReliabilityLayer(features=self.features, use_slot_power=self.use_slot_power, lam=self.lam)
            sub._fit_score(F[tr], ok[tr].astype(float), w[tr])
            oof[te] = np.where(cm[te], sub.raw_score(F[te]), -1.0)
        have = np.isfinite(oof)
        if (have & cm).sum() < 30:
            self.t_global, self.mu = np.inf, None
            self.diag = dict(reason="no out-of-fold scores")
            return self
        self._fit_score(F[cm], ok[cm].astype(float), w[cm])
        hc = have & cm
        self.iso = pav(oof[hc], ok[hc].astype(float), w[hc])
        deff = design_effect(ok, cl, hc)
        self.diag = dict(n_oof=int(hc.sum()), deff=deff, n_units=len(units), n_all=int(have.sum()))
        s_, o_, w_, c_ = oof[have], ok[have], wrong[have], cl[have]
        self.t_global, tail = self._scan(s_, o_, w_, c_, deff)
        self.diag["oof_tail"] = tail
        self.t_slot = {}
        if self.per_slot:
            sv = sl_all[have]
            for sname in sorted(set(sv)):
                m = sv == sname
                ncl = len(set(c_[m & (s_ >= 0)]))
                if ncl < self.slot_min_clusters or (m & (s_ >= 0)).sum() < 15:
                    continue                       # too thin to say anything slot-specific: the global threshold applies
                st = self._tail_stats(s_[m], o_[m], w_[m], c_[m], self.t_global, deff) if np.isfinite(self.t_global) else None
                if st is None or st[0] < self.lb_floor or st[1] < self.nominal:      # the slot's own leave-unit-out record does not support answering at the global cut
                    ts, tl = self._scan(s_[m], o_[m], w_[m], c_[m], deff, min_clusters=self.slot_min_clusters)
                    self.t_slot[sname] = max(ts, self.t_global)
                    self.diag.setdefault("slot_tail", {})[sname] = tl
        self._oof = (s_, o_, w_, sv if self.per_slot else sl_all[have])
        return self

    def _tail_stats(self, s, ok, wrong, cl, t, deff):
        m = s >= t
        if m.sum() == 0:
            return None
        acc = prior_balanced_acc(ok, wrong, m)
        if np.isnan(acc):
            return None
        return conservative_lb(acc, int(m.sum()), len(set(cl[m])), deff, self.q), acc, int(m.sum()), len(set(cl[m]))

    def _scan(self, s, ok, wrong, cl, deff, min_clusters=None):
        """scan candidate cuts from the top score downwards; keep going while the answered tail's lower bound stays >= nominal; return the last good cut.
        Episodes that never crossed carry score -1 (never answered) but count in the class totals of the balanced accuracy."""
        min_clusters = min_clusters or self.min_clusters
        pos = s[s >= 0]
        if len(pos) == 0:
            return np.inf, None
        cuts = np.unique(np.quantile(pos, np.linspace(0.0, 0.99, 100)))[::-1]
        best, tail = np.inf, None
        for t in cuts:
            st = self._tail_stats(s, ok, wrong, cl, t, deff)
            if st is None:
                continue
            lb, acc, n, ncl = st
            if lb >= self.lb_floor and acc >= self.nominal:
                if ncl >= min_clusters:
                    best, tail = t, dict(lb=lb, acc=acc, n=n, clusters=ncl)
            elif ncl >= min_clusters and acc < self.nominal:
                break                     # contiguous from the top: do not reach past a region whose accuracy is itself below nominal (a merely small sample is not a failure)
        return best, tail

    # -- prediction
    def calibrated(self, score):
        if self.iso is None:
            return float("nan")
        return float(np.interp(score, self.iso[0], self.iso[1]))

    def decide(self, rec: dict) -> Verdict:
        if not rec["crossed"]:
            return Verdict(FLAGGED, "insufficient evidence: no verdict within the reading budget", np.nan, np.nan)
        if self.mu is None or not np.isfinite(self.t_global):
            return Verdict(FLAGGED, "no honest confidence level demonstrated by out-of-unit runs", np.nan, np.nan)
        f = np.array(rec["f"], float).copy()
        f[FI["slot_power"]] = self.slot_pow.get(rec["slot"], np.nan)
        if not np.isfinite(f[FI["slot_power"]]):
            return Verdict(FLAGGED, "slot never seen in training", np.nan, np.nan)
        sc = float(self.raw_score(f)[0])
        t = max(self.t_slot.get(rec["slot"], self.t_global), self.t_global)
        if sc >= t:
            return Verdict(CONFIRMED if rec["say_correct"] else REFUTED, "ok", self.calibrated(sc), sc)
        return Verdict(FLAGGED, self._reason(f, rec, sc, t), np.nan, sc)

    def _reason(self, f, rec, sc, t):
        if rec["slot"] in self.t_slot and sc >= self.t_global:
            return "slot not reliable in leave-unit-out runs"
        if f[FI["oat_excess"]] > 0.25 or f[FI["nn_dist"]] > 1.5:
            return "out-of-support operating regime"
        if f[FI["agree"]] < 0.7 or f[FI["agree_slices"]] < 0.7:
            return "conflicting evidence across readings/slices"
        if f[FI["n_owners_info"]] < 3 or f[FI["gap12"]] < 2.0:
            return "near-twin / candidates not separated"
        if f[FI["zmin_frac3"]] > 0.15:
            return "readings unlikely under both classes"
        return "reliability score below the honest-confidence cut"
