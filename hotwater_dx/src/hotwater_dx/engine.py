"""Sequential diagnosis engine: rank causes, pick the next check by expected information per minute, update after every reading, stop when confident.

Hypotheses: the 17 single causes, the pairs of causes the research notes report as interacting (multi-fault support), and "other" (anything not modelled).
Likelihoods are Gaussians per (hypothesis, check) *fitted from the simulator* (`fit`), so the engine is exactly as good as the model that produced them; the stress test
(stress.py) measures how that degrades when the world differs from the model. Nothing here is field evidence.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

import numpy as np

from . import causes as C
from . import checks as K
from .matrix import THRESHOLDS, World, _reads
from .sampling import substream

ENGINE_CONFIG = {
    "TAU": 0.90,              # stop when the leading hypothesis reaches this posterior
    "MIN_RATE": 0.02,         # bits per minute: below this no remaining check is worth its time (PLACEHOLDER, same order as the HVAC tool's tuned value)
    "MAX_CHECKS": 12,
    "PRIOR_SINGLE": 0.80,     # total prior mass on single causes (uniform among them)
    "PRIOR_PAIR": 0.15,       # on the seeded pairs (uniform among them)
    "PRIOR_OTHER": 0.05,      # on "other"
    "FIT_REPS": 8,            # simulated readings per plant per (hypothesis, check) when fitting
    "OTHER_SD_MULT": 1.5,     # 'other' likelihood: pooled mean, pooled spread x this
    "VARIANT_B": {"var_inflate": 2.0, "PRIOR_OTHER": 0.10, "TAU": 0.95},   # robust variant: wider likelihoods, more mass on 'other', higher bar
    "SKIP_MIN": 3.0,          # minutes lost when a check turns out not to be possible
    "TRAVEL_MIN": {("DOOR", "MR"): 5.0, ("DOOR", "RS"): 8.0, ("DOOR", "FX"): 8.0, ("MR", "RS"): 4.0, ("MR", "FX"): 6.0, ("RS", "FX"): 3.0},   # ANALYST
}


def _strkeys(o):
    if isinstance(o, dict):
        return {str(k): _strkeys(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_strkeys(v) for v in o]
    return o


def config_hash() -> str:
    return hashlib.sha256(json.dumps(_strkeys(ENGINE_CONFIG), sort_keys=True, default=str).encode()).hexdigest()


ENGINE_CHECKS = tuple(c.id for c in K.CHECKS if c.physics_readable)
PAIRS = tuple(f"{i['a']}+{i['b']}" for i in C.INTERACTIONS)
OTHER = "other"


def parts(h: str) -> tuple[str, ...]:
    return () if h == OTHER else tuple(h.split("+"))


def travel(a: str, b: str) -> float:
    if a == b or b in ("INT", "BAS"):
        return 0.0
    return ENGINE_CONFIG["TRAVEL_MIN"].get((a, b)) or ENGINE_CONFIG["TRAVEL_MIN"].get((b, a), 6.0)


@dataclass
class Likelihoods:
    hyps: list
    checks: list
    mean: np.ndarray           # [H, C]
    sd: np.ndarray             # [H, C]
    thermal_only: dict         # check id -> True if it applies only to thermal-valve plants, False if only to fixed-orifice, absent otherwise
    grids: dict = field(default_factory=dict)   # cache shared by every engine built from these likelihoods


def fit(w: World, reps: int | None = None) -> Likelihoods:
    """Fit Gaussian reading distributions per (hypothesis, check) from a simulated world. Singles use the world's faulty plants; pairs apply two causes to the same plants."""
    reps = reps or ENGINE_CONFIG["FIT_REPS"]
    singles = list(w.cause_plants)
    hyps = singles + [p for p in PAIRS if all(x in w.cause_plants for x in parts(p))]
    mean = np.zeros((len(hyps) + 1, len(ENGINE_CHECKS)))
    sd = np.zeros_like(mean)
    ctxs = {}
    for cid in singles:
        g = w.cause_gated[cid]
        keep = g if g.sum() >= THRESHOLDS["GATE_MIN"] else np.ones(len(g), bool)
        ctxs[cid] = [(j, w.cause_ctx[cid][j]) for j in np.where(keep)[0]]
    for pi, h in enumerate([p for p in PAIRS if p in hyps]):
        a, b = (C.BY_ID[x] for x in parts(h))
        lst = []
        for j, P in enumerate(w.plants):
            da, db = a.draw(substream(w.seed, 7, pi, j, 0), P), b.draw(substream(w.seed, 7, pi, j, 1), P)
            lst.append((j, K.Ctx(b.apply(a.apply(P, da), db))))
        ctxs[h] = lst
    for hi, h in enumerate(hyps):
        for ci, cid in enumerate(ENGINE_CHECKS):
            ch = K.BY_ID[cid]
            vals = []
            for j, ctx in ctxs[h]:
                if not ch.applies(w.plants[j]):
                    continue
                vals.append(_reads(ch, ctx, ch.tool, substream(w.seed, 8, hi, ci, j), (THRESHOLDS["REPS_BINARY"] // 8) if ch.binary else reps))
            v = np.concatenate(vals) if vals else np.array([0.0, 1.0])
            mean[hi, ci], sd[hi, ci] = float(v.mean()), max(float(v.std()), ch.sigma_min)
    # "other": pooled mean, broad spread
    ho = len(hyps)
    mean[ho] = mean[:ho].mean(axis=0)
    sd[ho] = np.sqrt((sd[:ho] ** 2).mean(axis=0) + mean[:ho].var(axis=0)) * ENGINE_CONFIG["OTHER_SD_MULT"]
    return Likelihoods(hyps + [OTHER], list(ENGINE_CHECKS), mean, sd, {"K12": True, "K13": False})


# ------------------------------------------------------------------------------------------------ engine
class Engine:
    def __init__(self, lk: Likelihoods, thermal: bool, tau: float | None = None, min_rate: float | None = None, max_checks: int | None = None,
                 var_inflate: float = 1.0, prior_other: float | None = None, prior_pair: float | None = None, allow_isolation: bool = True, selection: str = "info",
                 fixed_order: tuple[str, ...] = (), rng: np.random.Generator | None = None, prior_vec: dict | None = None, assumed_minutes: dict | None = None,
                 allowed: frozenset | None = None, q_eps: float = 0.0):
        cfg = ENGINE_CONFIG
        self.lk, self.thermal = lk, thermal
        self.tau = cfg["TAU"] if tau is None else tau
        self.min_rate = cfg["MIN_RATE"] if min_rate is None else min_rate
        self.max_checks = cfg["MAX_CHECKS"] if max_checks is None else max_checks
        self.var_inflate, self.allow_isolation, self.selection, self.fixed_order = var_inflate, allow_isolation, selection, fixed_order
        self.assumed_minutes = assumed_minutes or {}      # what the engine *believes* a check takes (selection only); true minutes are always K.BY_ID[...].do_min
        self.allowed = allowed                            # None = every check; else only these check ids (toolkit tiers, leave-one-out)
        self.q_eps = q_eps                                # soft evidence: tenant-question likelihood = (1-eps) * hypothesis density + eps * the broad 'other' density (0 = off)
        self.rng = rng or np.random.default_rng(0)
        H = len(lk.hyps)
        n_single = sum(1 for h in lk.hyps if h != OTHER and "+" not in h)
        n_pair = sum(1 for h in lk.hyps if "+" in h)
        po = cfg["PRIOR_OTHER"] if prior_other is None else prior_other
        pp = cfg["PRIOR_PAIR"] if prior_pair is None else prior_pair
        ps = 1.0 - po - pp
        if prior_vec:                                     # explicit case-mix prior over the single causes (normalised); pair and other masses unchanged
            tot = sum(prior_vec.get(h, 0.0) for h in lk.hyps if h != OTHER and "+" not in h) or 1.0
            single = {h: ps * prior_vec.get(h, 0.0) / tot for h in lk.hyps if h != OTHER and "+" not in h}
        else:
            single = {h: ps / n_single for h in lk.hyps if h != OTHER and "+" not in h}
        prior = np.array([po if h == OTHER else (pp / max(n_pair, 1) if "+" in h else single[h]) for h in lk.hyps])
        with np.errstate(divide="ignore"):
            self.logp = np.log(prior / prior.sum())
        self.done: list[str] = []
        self.unavailable: set[str] = set()
        self.location = "DOOR"
        self.minutes = 0.0
        self.trace: list[dict] = []

    # ---- posterior
    def posterior(self) -> np.ndarray:
        p = np.exp(self.logp - self.logp.max())
        return p / p.sum()

    def top(self) -> tuple[str, float]:
        p = self.posterior()
        i = int(np.argmax(p))
        return self.lk.hyps[i], float(p[i])

    def marginal(self) -> dict:
        p = self.posterior()
        out: dict[str, float] = {}
        for h, x in zip(self.lk.hyps, p):
            for c in parts(h):
                out[c] = out.get(c, 0.0) + float(x)
        return out

    # ---- likelihood grid per check (cached)
    def _grid(self, ci: int):
        eps = self.q_eps if self.lk.checks[ci].startswith("Q") else 0.0
        key = (ci, round(self.var_inflate, 4)) if eps == 0.0 else (ci, round(self.var_inflate, 4), round(eps, 4))
        if key in self.lk.grids:
            return self.lk.grids[key]
        mu = self.lk.mean[:, ci]
        sd = self.lk.sd[:, ci] * np.sqrt(self.var_inflate)
        ys = np.unique(np.concatenate([m + s * np.linspace(-4.5, 4.5, 31) for m, s in zip(mu, sd)]))
        w = np.gradient(ys)
        pdf = np.exp(-0.5 * ((ys[None, :] - mu[:, None]) / sd[:, None]) ** 2) / (sd[:, None] * np.sqrt(2 * np.pi))
        if eps > 0.0:
            pdf = (1.0 - eps) * pdf + eps * pdf[-1][None, :]      # the last hypothesis is "other": pooled mean, broad spread
        self.lk.grids[key] = (ys, w, pdf, np.log2(np.maximum(pdf, 1e-300)))
        return self.lk.grids[key]

    def gain(self, cid: str) -> float:
        """Expected information gain in bits about which hypothesis is true."""
        ci = self.lk.checks.index(cid)
        ys, w, pdf, lpdf = self._grid(ci)
        p = self.posterior()
        mix = p @ pdf + 1e-300
        term = pdf * (lpdf - np.log2(mix)[None, :])
        return float(max((p[:, None] * term * w[None, :]).sum(), 0.0))

    def available(self) -> list[str]:
        out = []
        for cid in self.lk.checks:
            ch = K.BY_ID[cid]
            if cid in self.done or cid in self.unavailable:
                continue
            if cid in self.lk.thermal_only and self.lk.thermal_only[cid] != self.thermal:
                continue
            if not self.allow_isolation and ch.safety == "isolation_lockout":
                continue
            if self.allowed is not None and cid not in self.allowed:
                continue
            out.append(cid)
        return out

    def check_minutes(self, cid: str) -> float:
        """True minutes (time + travel from where the technician is)."""
        return K.BY_ID[cid].do_min + travel(self.location, K.BY_ID[cid].location)

    def believed_minutes(self, cid: str) -> float:
        return self.assumed_minutes.get(cid, K.BY_ID[cid].do_min) + travel(self.location, K.BY_ID[cid].location)

    def next_check(self) -> tuple[str | None, float, float]:
        """(check id, expected gain bits, minutes). None when nothing is available."""
        cands = self.available()
        if not cands:
            return None, 0.0, 0.0
        if self.selection == "fixed":
            for cid in self.fixed_order:
                if cid in cands:
                    return cid, self.gain(cid), self.believed_minutes(cid)
            return None, 0.0, 0.0
        if self.selection == "random":
            cid = cands[int(self.rng.integers(len(cands)))]
            return cid, self.gain(cid), self.believed_minutes(cid)
        best = max(((self.gain(c) / max(self.believed_minutes(c), 0.5), c) for c in cands))
        cid = best[1]
        return cid, self.gain(cid), self.believed_minutes(cid)

    def update(self, cid: str, value: float) -> None:
        ci = self.lk.checks.index(cid)
        mu = self.lk.mean[:, ci]
        sd = self.lk.sd[:, ci] * np.sqrt(self.var_inflate)
        if self.q_eps > 0.0 and cid.startswith("Q"):
            pdf = np.exp(-0.5 * ((value - mu) / sd) ** 2) / (sd * np.sqrt(2 * np.pi))
            self.logp = self.logp + np.log((1.0 - self.q_eps) * pdf + self.q_eps * pdf[-1] + 1e-300)
        else:
            self.logp = self.logp + (-0.5 * ((value - mu) / sd) ** 2 - np.log(sd))
        self.logp -= self.logp.max()
        ch = K.BY_ID[cid]
        self.minutes += self.check_minutes(cid)
        if ch.location not in ("INT", "BAS"):
            self.location = ch.location
        self.done.append(cid)

    def mark_unavailable(self, cid: str) -> None:
        self.unavailable.add(cid)
        self.minutes += ENGINE_CONFIG["SKIP_MIN"]

    def stop_reason(self, gain_rate: float | None = None) -> str | None:
        h, p = self.top()
        if p >= self.tau:
            return "confident"
        if len(self.done) >= self.max_checks:
            return "max_checks"
        if not self.available():
            return "no_checks_left"
        if gain_rate is not None and gain_rate < self.min_rate and self.selection == "info":
            return "not_worth_it"
        return None


@dataclass
class CaseResult:
    truth: tuple
    top: str
    top_p: float
    reason: str
    n_checks: int
    minutes: float
    checks: list
    marginal: dict
    correct: bool            # top hypothesis equals the truth (for pair truths: the same pair)
    hit: bool                # the top hypothesis names at least one true component
    wrong_conf: bool         # stopped 'confident' and the top hypothesis shares no component with the truth


def run_case(lk: Likelihoods, ctx: K.Ctx, truth: tuple, rng: np.random.Generator, thermal: bool, p_skip: float = 0.0, p_garbage: float = 0.0,
             garbage_lk: Likelihoods | None = None, p_tenant: float = 0.0, **eng_kw) -> CaseResult:
    """A simulated visit: the engine asks, the 'technician' reads the simulated plant with the instrument error model, sometimes can't do the check or reads it wrongly.
    `garbage_lk` (default: the engine's own likelihoods) is where wrong readings are drawn from; pass one fixed set when comparing engines fitted differently.
    `p_tenant`: chance that the answer to a tenant question (Q1-Q3) is unrelated to the plant (drawn like a wrong reading), on top of everything else; 0 changes nothing."""
    eng = Engine(lk, thermal, rng=rng, **eng_kw)
    gl = garbage_lk or lk
    reason = None
    while True:
        cid, g, mins = eng.next_check()
        reason = eng.stop_reason(None if cid is None else g / max(mins, 0.5))
        if reason or cid is None:
            reason = reason or "no_checks_left"
            break
        if rng.random() < p_skip:
            eng.mark_unavailable(cid)
            continue
        ch = K.BY_ID[cid]
        val = ch.read(ctx, rng, ch.tool)
        if p_tenant > 0.0 and cid.startswith("Q") and rng.random() < p_tenant:
            hi = int(rng.integers(len(gl.hyps)))
            val = float(rng.normal(gl.mean[hi, gl.checks.index(cid)], gl.sd[hi, gl.checks.index(cid)]))
        elif rng.random() < p_garbage:                     # a misread or mis-performed check: a reading from some other hypothesis
            hi = int(rng.integers(len(gl.hyps)))
            ci = gl.checks.index(cid)
            val = float(rng.normal(gl.mean[hi, ci], gl.sd[hi, ci]))
        eng.update(cid, val)
    h, p = eng.top()
    tset = set(truth)
    hp = set(parts(h))
    correct = (h == "+".join(truth)) if len(truth) == 2 else (h == truth[0])
    hit = bool(hp & tset)
    return CaseResult(truth=truth, top=h, top_p=p, reason=reason, n_checks=len(eng.done), minutes=eng.minutes, checks=list(eng.done), marginal=eng.marginal(),
                      correct=correct, hit=hit, wrong_conf=(reason == "confident" and not hit))
