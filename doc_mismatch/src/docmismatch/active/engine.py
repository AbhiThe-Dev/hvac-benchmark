"""Sequential verification of ONE documented connection.

Question: "is owner `doc` really the owner of member `m`?"  Hypotheses = the hard-filter-compatible owners
of m (index 0 = the documented one). Belief = exact categorical posterior. An action is a reading
(channel k, candidate owner j, slice s); its outcome likelihood comes from `model.ChannelModel` and depends
on the slice's operating context. The decision variable is D = [owner == doc]; readings are chosen by
expected information gain on D (optionally per unit cost) and the episode stops when P(D) leaves
(1-tau, tau) or the reading budget runs out.

Reuse from hvac_benchmark.experiment (unchanged): ActivePolicy (argmax-EIG with fixed tie-break priority),
RandomPolicy, FrozenInitialPolicy (EIG frozen at step 0), make_tiebreak, _seeded_tiebreak_sort, and the
retirement rule "stop when p >= conf or p <= 1 - conf". New here: categorical belief, continuous-outcome
EIG, context-conditional likelihood with pair random effects, reading costs.

Options added for the real-data selection fix (all default OFF = original behaviour, bit-identical trajectories; see `selection.py` and
`active_selection_report.md`): online_info (slice-level informativeness learned from earlier readings), shared_pair (pair random effect
shared across channels, factor integrated out exactly), policies random_info / random_oracle (stronger baselines), "custom" (fixed order,
analysis hook). Probed and NOT adopted (no gain on real data; kept for reproducibility): tau_scale / tau_min / tauM_min (inflate the pair
effect), pair_cap (max informative readings per candidate owner), sel_pooled (EIG on slice-averaged class separation).
"""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import numpy as np
from hvac_benchmark.experiment.policies import (ActivePolicy, FrozenInitialPolicy, RandomPolicy, _seeded_tiebreak_sort,
                                                 make_tiebreak)

from .model import ChannelModel, static_dprime, tf
from .pools import Pool, hypotheses

_GH_X, _GH_W = np.polynomial.hermite_e.hermegauss(15)
_GH_W = _GH_W / _GH_W.sum()
LOG2PI = np.log(2 * np.pi)

POLICIES = ("active", "active_cost", "frozen", "random", "traversal", "rule_based")
EXTRA_POLICIES = ("random_info", "random_oracle", "traversal_block")   # stronger baselines (not in POLICIES so existing runs are unchanged)


def _h(p):
    p = np.clip(p, 1e-12, 1 - 1e-12)
    return -(p * np.log2(p) + (1 - p) * np.log2(1 - p))


# ------------------------------------------------------------------ reading costs (qualitative tiers, NOT measured)
_BAS_ONLY = {("ahu_vav", 0), ("vav_zone", 1), ("loop_branch", 0), ("loop_source", 0)}  # channels that read temperatures / BAS points only


def channel_cost(slot: str, k: int, rho: float) -> float:
    """Tier 1 = read from existing BAS temperature/point trends. Tier rho = also needs a flow / power / energy trend
    (an instrument or a metered trend). The two tiers are an assumption; rho is swept, never fitted."""
    return 1.0 if (slot, k) in _BAS_ONLY else float(rho)


@dataclass
class Episode:
    pool: Pool
    slot: str
    member: int
    doc: int
    truth_owner: int
    is_wrong: bool
    ep_id: str
    group: str
    meta: dict


@dataclass
class Result:
    n_read: int
    n_info: int
    cost: float
    p_doc: float
    stopped: bool       # left the (1-tau, tau) band before the budget ran out
    verdict_correct: bool  # P(doc)>=0.5 says "correct" and that is right
    traj: np.ndarray    # P(doc) after 0..nmax readings (held after stopping)
    order: list
    cost_traj: np.ndarray = None   # cumulative reading cost after 0..nmax readings
    info_traj: np.ndarray = None   # cumulative informative (non-null) readings
    k_seq: np.ndarray = None       # channel index of each reading taken, in order (cost can be recomputed under any tier ratio)
    diag: dict = None              # only when run_episode(diag=True): per-reading diagnostics + posterior history (see reliability.py)
    futile: bool = False           # only True when futility_window stopped the episode early (see run_episode)


class _Actions:
    """All readings available in one episode, as flat arrays."""

    def __init__(self, ep: Episode, models: dict[int, ChannelModel], hyps: list[int], sl_idx: np.ndarray, rho: float):
        sp = ep.pool.slots[ep.slot]
        ks = sorted(models)
        A = len(ks) * len(hyps) * len(sl_idx)
        self.k = np.empty(A, int); self.j = np.empty(A, int); self.s = np.empty(A, int); self.spos = np.empty(A, int)
        self.mM = np.empty(A); self.sM = np.empty(A); self.mX = np.empty(A); self.sX = np.empty(A)
        self.pinfo = np.empty(A); self.y = np.empty(A); self.cost = np.empty(A)
        i = 0
        ctx = ep.pool.ctx[sl_idx]
        par = {k: models[k].params(ctx) for k in ks}
        for si, s in enumerate(sl_idx):
            for jj, o in enumerate(hyps):
                for k in ks:
                    self.k[i], self.j[i], self.s[i], self.spos[i] = k, jj, s, si
                    mM, sM, mX, sX, pi = par[k]
                    self.mM[i], self.sM[i], self.mX[i], self.sX[i], self.pinfo[i] = mM[si], sM[si], mX[si], sX[si], pi[si]
                    v = sp.E[s, k, o, ep.member]
                    self.y[i] = tf(v) if np.isfinite(v) else np.nan
                    self.cost[i] = channel_cost(ep.slot, k, rho)
                    i += 1
        self.n = A
        self.ks = ks


def _gauss_logpdf(y, m, v):
    return -0.5 * (np.log(v) + (y - m) ** 2 / v + LOG2PI)


def run_episode(ep: Episode, models: dict[int, ChannelModel], slice_idx: np.ndarray, policy: str, *, tau: float = 0.95,
                nmax: int = 24, prior_doc: float = 0.5, seed: int = 0, rho: float = 3.0, beta: float = 1.0,
                use_re: bool = True, online_info: bool = False, tau_scale: float = 1.0, tau_min: float = 0.0, tauM_min: float = 0.0, shared_pair: bool = False, pair_cap: int = 0, sel_pooled: bool = False, diag: bool = False, slice_effect: bool = False,
                exclude_k: frozenset = frozenset(), futility_window: int = 0, futility_margin: float = 0.0, **selkw) -> Result | None:
    """exclude_k: channel indices to drop before the action set is built -- e.g. channels `measurement.py` found
    structurally untrustworthy on this real building. Default empty = original behaviour, bit-identical trajectories.

    futility_window: 0 = off (default, bit-identical trajectories); else must be >= 3. A "will more testing
    plausibly reach tau at all" check (conditional-power futility, the same shape as a clinical trial's interim
    analysis), run every step once at least 2*futility_window readings have been taken. Fits a linear trend of
    the DECISION entropy H(p)=-(p log2 p + (1-p) log2(1-p)) over the trailing `futility_window` readings,
    together with the trend's OWN standard error (not just its point estimate -- a short window's slope is
    noisy, and extrapolating the bare point estimate over a much longer remaining horizon amplifies that noise
    into false "give up" calls on genuinely, if slowly, converging cases). Extrapolates the OPTIMISTIC end of
    that trend (point estimate minus 1.645 SE, ~90% one-sided) to the remaining budget; only stops and marks the
    result `futile=True` if even that optimistic projection would still sit above H(tau) + `futility_margin`.
    Distinct from `stopped` (confidence reached) and from running out of budget. This is about WHETHER to keep
    testing, never about WHICH reading to take next (EIG selection is unchanged); see `active/measurement.py`
    for what to tell the technician when this fires."""
    sp = ep.pool.slots[ep.slot]
    hyps = hypotheses(sp, ep.doc)
    if exclude_k:
        models = {k: m for k, m in models.items() if k not in exclude_k}
    if len(hyps) < 2 or not models:
        return None
    H = len(hyps)
    acts = _Actions(ep, models, hyps, slice_idx, rho)
    ks = acts.ks
    kpos = {k: i for i, k in enumerate(ks)}
    K = len(ks)
    tau_z = np.maximum(np.array([[models[k].fit["M"].tau, models[k].fit["X"].tau] for k in ks]) * tau_scale, tau_min) * (1.0 if use_re else 0.0)
    tau_z[:, 0] = np.maximum(tau_z[:, 0], tauM_min) * (1.0 if use_re else 0.0)
    kap = np.array([(models[k].kappa if models[k].kappa is not None else np.inf) for k in acts.k]) if online_info else None
    S_pos = len(slice_idx)
    sl_n = np.zeros(S_pos); sl_res = np.zeros(S_pos)     # per slice: readings taken so far, and sum of (informative - predicted informative)

    if sel_pooled:
        # selection-side context robustness: the reading's *predicted separation* is averaged over the slices on offer (so EIG cannot chase
        # the slices where the fitted context regression predicts the largest -- and least trustworthy -- class gap); the slice is then
        # chosen by informativeness (and the shared tie-break). The belief update still uses the slice-specific parameters.
        sel = {}
        for k in ks:
            w = np.array([acts.pinfo[i] for i in range(acts.n) if acts.k[i] == k and acts.j[i] == 0])
            m = np.array([[acts.mM[i], acts.mX[i], acts.sM[i], acts.sX[i]] for i in range(acts.n) if acts.k[i] == k and acts.j[i] == 0])
            sel[k] = (m * w[:, None]).sum(0) / w.sum()
        selM = np.array([sel[k][0] for k in acts.k]); selX = np.array([sel[k][1] for k in acts.k])
        selsM = np.array([sel[k][2] for k in acts.k]); selsX = np.array([sel[k][3] for k in acts.k])
    else:
        selM, selX, selsM, selsX = acts.mM, acts.mX, acts.sM, acts.sX

    def pinfo_now():
        """Predicted probability that each reading is informative, updated with what earlier readings in the same slice turned out to be."""
        if kap is None:
            return acts.pinfo
        return np.clip(acts.pinfo + sl_res[acts.spos] / (kap + sl_n[acts.spos]), 0.02, 0.98)

    logprior = np.log(np.r_[prior_doc, np.full(H - 1, (1 - prior_doc) / (H - 1))])
    # sufficient statistics per (candidate j, channel k, class z): n, sum log sigma^2, A, a_r, Q
    n = np.zeros((H, K, 2)); L = np.zeros((H, K, 2)); Aw = np.zeros((H, K, 2)); ar = np.zeros((H, K, 2)); Q = np.zeros((H, K, 2))
    rho = float(models[ks[0]].rho) if shared_pair else 0.0   # share of a pair's random effect common to all its channels
    t2s = tau_z ** 2 * (1.0 - rho)                          # channel-specific part of the pair effect (K,2)
    sh = tau_z * np.sqrt(rho)                               # loading on the shared part (K,2)

    # ---- optional slice-member effect (all default-off): exact joint-Gaussian belief over the readings taken so far
    joint = bool(slice_effect) and any(getattr(models[k], "omega", 0.0) > 0 for k in ks)
    rd_a: list[int] = []
    kpos_arr = np.array([kpos[k] for k in acts.k])
    if joint:
        om = np.array([models[k].omega for k in ks]); rho_s = float(models[ks[0]].rho_s)
        inv_om2 = np.where(om > 0, 1.0 / np.maximum(om, 1e-9) ** 2, np.inf)
        off_num = np.zeros((S_pos, K)); off_den = np.zeros((S_pos, K))

    def pair_terms():
        """Per (candidate, channel, class) log-likelihood pieces after integrating out the channel-specific pair effect, plus the
        quadratic-in-shared-effect coefficients (A, B) per (candidate, class). rho=0 reduces to independent channel-wise effects."""
        d = 1 + t2s[None] * Aw
        a_, b_ = Aw / d, ar / d
        c_ = Q - t2s[None] * ar ** 2 / d
        base = L + np.log(d) + n * LOG2PI
        A = (sh[None] ** 2 * a_).sum(1)            # (H,2)
        B = (sh[None] * b_).sum(1)
        return d, base, c_, A, B

    def ll_pair():
        d, base, c_, A, B = pair_terms()
        return -0.5 * (base.sum(1) + c_.sum(1) - B ** 2 / (1 + A) + np.log1p(A))    # (H,2)

    def posterior_joint():
        if not rd_a:
            p = np.exp(logprior - logprior.max())
            return p / p.sum()
        a = np.array(rd_a)
        j, kc, sl, y = acts.j[a], kpos_arr[a], acts.spos[a], acts.y[a]
        Rm, Rx = y - acts.mM[a], y - acts.mX[a]
        same_c = j[:, None] == j[None, :]
        kk = kc[:, None] == kc[None, :]
        cs = np.where(kk, 1.0, rho)
        tM, tX = tau_z[kc, 0], tau_z[kc, 1]
        PCM = tM[:, None] * tM[None, :] * cs * same_c
        PCX = tX[:, None] * tX[None, :] * cs * same_c
        SL = (sl[:, None] == sl[None, :]) * om[kc][:, None] * om[kc][None, :] * np.where(kk, 1.0, rho_s)
        zH = j[None, :] == np.arange(H)[:, None]                      # (H,N): reading i is of the owner under hypothesis h
        Sig = np.where(zH[:, :, None] & same_c[None], PCM[None], PCX[None]) + SL[None]
        N = len(a)
        Sig = Sig + np.einsum("hn,nm->hnm", np.where(zH, acts.sM[a][None] ** 2, acts.sX[a][None] ** 2), np.eye(N)) + 1e-9 * np.eye(N)[None]
        r = np.where(zH, Rm[None], Rx[None])
        Lc = np.linalg.cholesky(Sig)
        u = np.linalg.solve(Lc, r[:, :, None])[:, :, 0]
        ll = -0.5 * (u ** 2).sum(1) - np.log(np.diagonal(Lc, axis1=1, axis2=2)).sum(1)
        lp = logprior + beta * ll
        lp -= lp.max()
        p = np.exp(lp)
        return p / p.sum()

    def posterior():
        if joint:
            return posterior_joint()
        l = ll_pair()
        lm, lx = l[:, 0], l[:, 1]
        lp = logprior + beta * (lx.sum() - lx + lm)
        lp -= lp.max()
        p = np.exp(lp)
        return p / p.sum()

    def eig_all(post):
        kk = np.array([kpos[k] for k in acts.k])
        jj = acts.j
        d, _, _, A, B = pair_terms()
        zhat, zvar = B / (1 + A), 1.0 / (1 + A)   # posterior of the shared pair effect, (H,2)
        ts = t2s[kk]                               # (A_,2)
        dj = d[jj, kk]                             # (A_,2)  = 1 + t2s * Aw
        shk = sh[kk]
        mean_sh = (shk / dj) * zhat[jj]
        var_sh = (shk / dj) ** 2 * zvar[jj]
        mM = selM + ts[:, 0] * ar[jj, kk, 0] / dj[:, 0] + mean_sh[:, 0]
        mX = selX + ts[:, 1] * ar[jj, kk, 1] / dj[:, 1] + mean_sh[:, 1]
        vM = selsM ** 2 + ts[:, 0] / dj[:, 0] + var_sh[:, 0]
        vX = selsX ** 2 + ts[:, 1] / dj[:, 1] + var_sh[:, 1]
        if joint:   # plug-in estimate of the slice effect from the readings already taken in the same (slice, channel), treating them as class X
            den_ = inv_om2[kk] + off_den[acts.spos, kk]
            ah, va = off_num[acts.spos, kk] / den_, 1.0 / den_
            mM, mX, vM, vX = mM + ah, mX + ah, vM + va, vX + va
        bj, bd = post[jj], post[0]
        is_doc = jj == 0
        gain = np.zeros(acts.n)
        for comp, wcomp in ((0, bj), (1, 1 - bj)):
            m_, v_ = (mM, vM) if comp == 0 else (mX, vX)
            y = m_[:, None] + np.sqrt(v_)[:, None] * _GH_X[None, :]                  # (A,G)
            lM = _gauss_logpdf(y, mM[:, None], vM[:, None])
            lX = _gauss_logpdf(y, mX[:, None], vX[:, None])
            pM, pX = np.exp(beta * lM), np.exp(beta * lX)   # hypothetical update uses the same tempered likelihood as the belief
            num_doc = np.where(is_doc[:, None], bd * pM, bd * pX)
            den = bj[:, None] * pM + (1 - bj[:, None]) * pX
            bd2 = num_doc / np.maximum(den, 1e-300)
            gain += wcomp * (_GH_W[None, :] * _h(bd2)).sum(1)
        return (_h(bd) - gain) * pinfo_now()

    def observe(a: int):
        y = acts.y[a]
        if not np.isfinite(y):
            return False
        j, kc = acts.j[a], kpos[acts.k[a]]
        for z, (m_, s_) in enumerate(((acts.mM[a], acts.sM[a]), (acts.mX[a], acts.sX[a]))):
            w = 1.0 / s_ ** 2
            r = y - m_
            n[j, kc, z] += 1; L[j, kc, z] += 2 * np.log(s_); Aw[j, kc, z] += w; ar[j, kc, z] += r * w; Q[j, kc, z] += r * r * w
        if joint:
            rd_a.append(int(a))
            wx = 1.0 / acts.sX[a] ** 2
            off_num[acts.spos[a], kc] += (y - acts.mX[a]) * wx; off_den[acts.spos[a], kc] += wx
        return True

    tiebreak = make_tiebreak(acts.n, seed)
    order_fixed = None
    post = posterior()
    if policy == "random":
        order_fixed = list(RandomPolicy().initial_ranking(None, None, tiebreak))
    elif policy == "traversal":
        # technician sweep: per visit slice in time order, documented owner first then alternatives, channels in index order
        keys = [(-acts.spos[a], -acts.j[a], -acts.k[a]) for a in range(acts.n)]
        order_fixed = _seeded_tiebreak_sort(keys, tiebreak)
    elif policy == "traversal_block":
        # informative-block-aware sweep: the technician first visits the slices that are expected to have live data (model-predicted
        # informativeness >= 0.5, a slice-level property), in time order, documented owner first, then the other slices
        keys = [(float(acts.pinfo[a] >= 0.5), -acts.spos[a], -acts.j[a], -acts.k[a]) for a in range(acts.n)]
        order_fixed = _seeded_tiebreak_sort(keys, tiebreak)
    elif policy == "rule_based":
        dp = static_dprime(models)   # context-blind fixed channel ranking, best discriminating channel first
        keys = [(dp[acts.k[a]], -acts.spos[a], -acts.j[a]) for a in range(acts.n)]
        order_fixed = _seeded_tiebreak_sort(keys, tiebreak)
    elif policy == "frozen":
        g0 = eig_all(post)
        order_fixed = FrozenInitialPolicy().initial_ranking(SimpleNamespace(candidates=list(range(acts.n))), None, tiebreak, eig_fn=lambda i: g0[i])
    elif policy == "custom":     # analysis hook: fixed action order supplied by the caller (indices into the episode's flat action array)
        order_fixed = list(selkw["order"])
    elif policy not in ("active", "active_cost") + EXTRA_POLICIES:
        raise ValueError(policy)
    post_hist = [post.copy()] if diag else None
    rng_sel = np.random.default_rng(seed + 12345)

    used = np.zeros(acts.n, bool)
    cnt_j = np.zeros(H, int)   # informative readings taken per candidate owner
    traj = [float(post[0])]
    cost_traj = [0.0]
    info_traj = [0]
    order = []
    n_info = 0
    cost = 0.0
    stopped = False
    futile = False
    active = ActivePolicy()
    cursor = 0

    def _hbin(p):
        p = min(max(p, 1e-12), 1 - 1e-12)
        return -(p * np.log2(p) + (1 - p) * np.log2(1 - p))

    H_tau = _hbin(tau)

    def is_futile():
        """Conditional-power-style futility: only give up if even an OPTIMISTIC read of the trend so far
        wouldn't reach tau in the remaining budget -- not just the point-estimate trend. A short window's slope
        is itself noisy; extrapolating its bare point estimate over a much longer remaining horizon amplifies
        that noise into false "give up" calls on genuinely (if slowly) converging cases. Requires w>=3 points to
        estimate the slope's own uncertainty at all; with fewer, there is nothing reliable to judge, so it never
        fires (the same "refuse rather than guess" rule used elsewhere in this project, e.g. ReliabilityLayer's
        min_clusters gate)."""
        w = futility_window
        n = len(traj) - 1   # readings taken so far
        if w < 3 or n < 2 * w or n >= nmax:
            return False
        xs = np.arange(w, dtype=float)
        ys = np.array([_hbin(traj[n - w + 1 + i]) for i in range(w)])
        try:
            coeffs, cov = np.polyfit(xs, ys, 1, cov=True)
        except (np.linalg.LinAlgError, ValueError):
            return False
        slope, se_slope = float(coeffs[0]), float(np.sqrt(max(cov[0, 0], 0.0)))
        if not np.isfinite(se_slope):
            return False
        optimistic_slope = slope - 1.645 * se_slope   # one-sided ~90% CI toward faster convergence
        projected = ys[-1] + optimistic_slope * (nmax - n)
        return projected > H_tau + futility_margin

    while len(order) < nmax and not used.all():
        if post[0] >= tau or post[0] <= 1 - tau:
            stopped = True
            break
        if is_futile():
            futile = True
            break
        if order_fixed is not None:
            while used[order_fixed[cursor]]:
                cursor += 1
            a = order_fixed[cursor]
        elif policy in EXTRA_POLICIES:
            # random among the readings predicted informative (random_info; deployable, uses the informativeness model) or that ARE
            # informative (random_oracle; NOT deployable, analysis only)
            ok_ = np.isfinite(acts.y) if policy == "random_oracle" else pinfo_now() >= 0.5
            pool_ = np.flatnonzero(~used & ok_)
            if len(pool_) == 0:
                pool_ = np.flatnonzero(~used)
            a = int(rng_sel.choice(pool_))
        else:
            g = eig_all(post)
            if policy == "active_cost":
                g = g / acts.cost
            unresolved = list(np.flatnonzero(~used))
            if pair_cap:   # coverage: at most `pair_cap` informative readings per candidate owner before any other owner is exhausted
                capped = np.array([cnt_j[acts.j[i]] >= pair_cap for i in unresolved])
                if capped.any() and not capped.all():
                    unresolved = [i for i, c in zip(unresolved, capped) if not c]
            a = active.next_index(unresolved, lambda i: g[i], tiebreak)
        used[a] = True
        order.append(int(a))
        cost += acts.cost[a]
        sl_n[acts.spos[a]] += 1
        sl_res[acts.spos[a]] += float(np.isfinite(acts.y[a])) - acts.pinfo[a]
        if observe(a):
            cnt_j[acts.j[a]] += 1
            n_info += 1
            post = posterior()
        traj.append(float(post[0]))
        if diag:
            post_hist.append(post.copy())
        cost_traj.append(cost)
        info_traj.append(n_info)
    if not stopped and (post[0] >= tau or post[0] <= 1 - tau):
        stopped = True
    pad = nmax + 1 - len(traj)
    traj += [traj[-1]] * pad
    cost_traj += [cost_traj[-1]] * pad
    info_traj += [info_traj[-1]] * pad
    p_doc = float(post[0])
    dg = None
    if diag:
        post_hist += [post_hist[-1]] * pad
        oa = np.array(order, int)
        y_ = acts.y[oa]
        fin = np.isfinite(y_)
        yy = np.where(fin, y_, 0.0)
        zM = (yy - acts.mM[oa]) / acts.sM[oa]
        zX = (yy - acts.mX[oa]) / acts.sX[oa]
        llr = _gauss_logpdf(yy, acts.mM[oa], acts.sM[oa] ** 2) - _gauss_logpdf(yy, acts.mX[oa], acts.sX[oa] ** 2)
        dg = dict(post=np.array(post_hist, dtype=np.float32), H=H, hyps=list(hyps), j=acts.j[oa].astype(np.int16), k=acts.k[oa].astype(np.int8),
                  s=acts.s[oa].astype(np.int32), info=fin, zM=np.where(fin, zM, 0.0).astype(np.float32), zX=np.where(fin, zX, 0.0).astype(np.float32),
                  llr=np.where(fin, llr, 0.0).astype(np.float32), ctx=ep.pool.ctx[acts.s[oa]].astype(np.float32), n_actions=int(acts.n))
    return Result(len(order), n_info, cost, p_doc, stopped, (p_doc >= 0.5) == (not ep.is_wrong), np.array(traj), order, np.array(cost_traj), np.array(info_traj), np.array([acts.k[a] for a in order], dtype=np.int8), dg, futile)
