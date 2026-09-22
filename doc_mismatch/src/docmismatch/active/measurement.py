"""Detect channels whose passively-logged real-building evidence cannot be trusted, and recommend the specific
active measurement a technician could take instead (PREREGISTRATION_DR.md Addendum 5).

Motivation: a channel can be *available* (finite readings, no dropout) yet still carry no real signal for THIS
building, because its simulated definition depends on a physical quantity (airflow, a metered rate, power) that
the real BAS never logs for that equipment -- e.g. real `vav_zone` channels 0/2 need per-box airflow, which the
ORNL RTU-VAV building does not have; the real data substitutes a different proxy (reheat power), and a
likelihood fitted on simulation's airflow-based statistics does not transfer to it (see Addendum 1/4). This is a
DIFFERENT failure mode from the existing `pinfo` dropout model in `model.py`/`engine.py`, which predicts whether a
reading comes back at all -- these channels always come back finite, they are just miscalibrated.

Two pieces:
  * `real_channel_validity`: honest, cluster-robust (by calendar day) check of whether a channel's sim-fitted
    likelihood actually discriminates true from false pairs on REAL DEV data (never SEALED). Mirrors the
    reliability layer's discipline (leave enough independent days, refuse rather than guess).
  * `recommend_missing_measurement`: for channels that fail that check AND are not BAS-only (`engine._BAS_ONLY`),
    a human-readable instruction naming the physical quantity to instrument -- reusing `evidence.NEEDS`, the
    SAME metadata that already governs which channels get masked NaN in simulation. A BAS-only channel failing
    the check is a modelling problem (nothing to install), so it gets no recommendation.

What this does NOT establish: whether a technician-run measurement campaign would actually reproduce the
statistics simulation assumes. No real campaign-collected replacement data exists anywhere in this project; that
question is evaluated only as a simulation ceiling (scripts/35), never claimed as a validated real-world result.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..evidence import NEEDS as SIM_CHANNEL_NEEDS
from .engine import _BAS_ONLY
from .model import ChannelModel, tf
from .pools import Pool, hypotheses

LOG2PI = np.log(2 * np.pi)

INSTRUMENT_DEVICE = {
    "flow": "a temporary airflow (CFM) logger",
    "rate": "a temporary flow / heat-rate meter",
    "kw": "a temporary power meter",
}
WHO_DESC = {"o": "the documented owner", "m": "the member stream"}


def _gauss_logpdf(y, m, v):
    return -0.5 * (np.log(v) + (y - m) ** 2 / v + LOG2PI)


def requires_instrument(slot: str, k: int, *, tg=None, ontology=None, owner_node: str | None = None) -> bool:
    """True if this channel needs instrumentation THIS BUILDING doesn't already have. With a Brick graph
    (`tg`/`ontology` from `brick_bridge.load_real_topologies`, `owner_node` = that building's equipment node),
    grounds the answer in what the building's OWN documentation says it already has -- e.g. a building whose VAV
    boxes DO carry a documented airflow point needs no recommendation, even though the channel is not BAS-only
    in general. Falls back to the static simulation-wide tier (`engine._BAS_ONLY`) with no graph, or when the
    graph can't determine it (an undetermined point class -- see `brick_bridge.equipment_has_signal`)."""
    if tg is not None and ontology is not None:
        from .brick_bridge import structural_requirement_met
        met = structural_requirement_met(tg, ontology, owner_node, None, slot, k)
        if met is not None:
            return not met
    return (slot, k) not in _BAS_ONLY


def channel_requirement(slot: str, k: int) -> list[tuple[str, str]]:
    """[(who, signal), ...] this channel's simulated definition depends on (from `evidence.NEEDS`); [] if uncatalogued."""
    return list(SIM_CHANNEL_NEEDS.get(slot, {}).get(k, []))


def describe_requirement(slot: str, k: int, *, tg=None, ontology=None, owner_node: str | None = None) -> str | None:
    """Human-readable instrumentation instruction, or None if this building doesn't need one (BAS-only in
    general, or -- with a Brick graph -- already documented as having the point)."""
    if not requires_instrument(slot, k, tg=tg, ontology=ontology, owner_node=owner_node):
        return None
    req = channel_requirement(slot, k)
    instr = [(w, sig) for w, sig in req if sig in INSTRUMENT_DEVICE]
    devices = sorted({INSTRUMENT_DEVICE[sig] for _, sig in instr})
    who = sorted({WHO_DESC.get(w, w) for w, _ in instr})
    if not devices:
        devices = ["a supplemental instrument (its exact physical requirement is not catalogued for this channel)"]
    return f"channel {k} of `{slot}` is not BAS-only; it needs {' or '.join(devices)} on {', '.join(who) or 'this equipment'} to be trustworthy on this building"


# ---------------------------------------------------------------------------------------------- real-domain validity
@dataclass
class ChannelValidity:
    slot: str
    k: int
    validated: bool
    point_bal_acc: float   # class-balanced accuracy of sign(llr) at predicting true vs false pair, pooled
    lb_bal_acc: float      # one-sided (q) cluster (day) bootstrap lower bound of the same
    n_days: int
    n_rows: int
    reason: str


def _balanced_acc(ok: np.ndarray, is_m: np.ndarray, w: np.ndarray | None = None) -> float:
    w = np.ones(len(ok)) if w is None else w
    r = []
    for c in (True, False):
        m = is_m == c
        d = w[m].sum()
        r.append(w[m & ok].sum() / d if d > 0 else np.nan)
    return float(np.nanmean(r)) if not all(np.isnan(x) for x in r) else np.nan


def _cluster_boot_lb(ok: np.ndarray, is_m: np.ndarray, cluster: np.ndarray, q: float, B: int, seed: int):
    ub = np.unique(cluster)
    idx = {u: np.flatnonzero(cluster == u) for u in ub}
    rng = np.random.default_rng(seed)
    point = _balanced_acc(ok, is_m)
    vals = np.empty(B)
    for i in range(B):
        pick = rng.choice(ub, len(ub))
        w = np.zeros(len(ok))
        for u in pick:
            w[idx[u]] += 1
        vals[i] = _balanced_acc(ok, is_m, w)
    lb = float(np.nanpercentile(vals, 100 * q)) if np.isfinite(vals).any() else np.nan
    return point, lb, len(ub)


def real_channel_validity(pool: Pool, slot: str, models: dict[int, ChannelModel], *, min_clusters: int = 6,
                           min_rows: int = 30, q: float = 0.10, min_gt: float = 0.5, B: int = 1000, seed: int = 0) -> dict[int, ChannelValidity]:
    """For each fitted channel, score EVERY (slice, member, candidate-owner) reading of `pool` under that
    channel's sim-fitted likelihood: llr = log p(y|M) - log p(y|X). A reading is "correct" if the sign of the
    evidence favours the truth (llr>0 for the true owner, llr<0 for an alternative). `validated` requires the
    class-balanced accuracy's day-cluster bootstrap lower bound to clear `min_gt` (chance) with >= `min_clusters`
    independent days -- refuses rather than guesses when there is too little real evidence, mirroring
    `reliability.ReliabilityLayer`. Uses only `pool`'s own labels (real DEV truth or simulated truth); never
    fits anything here -- `models` must already be fitted (e.g. zero-shot from simulation, as in Addendum 1)."""
    out = {}
    for k, model in models.items():
        sp = pool.slots.get(slot)
        if sp is None:
            out[k] = ChannelValidity(slot, k, False, np.nan, np.nan, 0, 0, "slot not in pool")
            continue
        ok_rows, is_m_rows, cl_rows = [], [], []
        for s in range(pool.n_slices):
            mM, sM, mX, sX, _ = model.params(pool.ctx[s:s + 1])
            mM, sM, mX, sX = float(mM[0]), float(sM[0]), float(mX[0]), float(sX[0])
            for m in range(len(sp.members)):
                t = int(sp.truth[m])
                if t < 0:
                    continue
                for o in hypotheses(sp, t):
                    v = sp.E[s, k, o, m]
                    if not np.isfinite(v):
                        continue
                    y = tf(v)
                    llr = _gauss_logpdf(y, mM, sM ** 2) - _gauss_logpdf(y, mX, sX ** 2)
                    is_m = o == t
                    ok_rows.append(bool((llr > 0) if is_m else (llr < 0)))
                    is_m_rows.append(is_m)
                    cl_rows.append(int(pool.group[s]))
        ok = np.array(ok_rows, bool)
        is_m = np.array(is_m_rows, bool)
        cl = np.array(cl_rows)
        n_days = len(set(cl.tolist()))
        if len(ok) < min_rows or n_days < min_clusters:
            out[k] = ChannelValidity(slot, k, False, np.nan, np.nan, n_days, len(ok), f"too little real evidence (n={len(ok)}, days={n_days})")
            continue
        point, lb, n_days = _cluster_boot_lb(ok, is_m, cl, q, B, seed)
        validated = np.isfinite(lb) and lb > min_gt
        reason = "ok" if validated else f"day-cluster lower-bound balanced accuracy {lb:.3f} does not clear chance ({min_gt})"
        out[k] = ChannelValidity(slot, k, validated, point, lb, n_days, len(ok), reason)
    return out


# ---------------------------------------------------------------------------------------------- recommendation
@dataclass
class Recommendation:
    slot: str
    k: int
    text: str


def recommend_missing_measurement(slot: str, invalid_ks, *, tg=None, ontology=None, owner_node: str | None = None) -> list[Recommendation]:
    """For channels that failed `real_channel_validity` AND need extra instrumentation THIS BUILDING doesn't
    already have (not BAS-only, and -- with a Brick graph -- not already documented): a human-readable "go
    measure this" instruction. Channels needing no new device are silently skipped (nothing to recommend)."""
    out = []
    for k in sorted(invalid_ks):
        d = describe_requirement(slot, k, tg=tg, ontology=ontology, owner_node=owner_node)
        if d is not None:
            out.append(Recommendation(slot, k, d))
    return out


# ---------------------------------------------------------------------------------------------- graceful output
@dataclass
class TestStatus:
    """What to actually tell the technician -- replaces a bare FLAGGED-with-nothing. `reason` distinguishes WHY
    testing stopped: "confident" (the normal, unchanged case), "futile" (engine.py's futility_window fired --
    more of this evidence type was not going to help, so testing stopped early to save technician time), or
    "exhausted" (ran the full budget without resolving -- still possible when futility is off or its margin is
    conservative). `recommendations` is only populated for the non-confident cases."""
    verdict: str          # "CONFIRMED" | "REFUTED" | "UNCERTAIN"
    p: float              # current best-guess P(documented owner correct), whatever confidence stopped testing
    n_read: int            # actual technician tests taken -- the number this whole mechanism is trying to shrink
    reason: str
    recommendations: list
    physical_recommendation: object = None   # a physical.PhysicalRecommendation, only when it beats the
    # sensor-reading rate actually achieved (or, with zero sensor evidence, any positive-EIG physical test)


def diagnose_connection(pool, slot: str, member: int, doc: int, models: dict, validity: dict | None = None, *,
                         slice_idx=None, tau: float = 0.95, nmax: int = 24, futility_window: int = 4,
                         futility_margin: float = 0.05, beta: float = 1.0, seed: int = 0,
                         tg=None, ontology=None, owner_node: str | None = None):
    """The end-to-end entry point: technician points at ONE vent (`member`) and what the blueprint claims feeds
    it (`doc`); this decides the efficient sequence of tests (trust-weighted EIG selection, exclude_k'd if no
    validity is given), runs them (futility-aware), and returns an honest, actionable report -- instead of
    separately calling trust.apply_trust_weights / engine.run_episode / explain_result by hand. `validity`:
    {channel: ChannelValidity} from `real_channel_validity`, or None to use every channel at full trust."""
    from .engine import Episode, run_episode
    from .physical import _hbin, best_physical_test
    from .pools import hypotheses
    from .trust import apply_trust_weights

    sp = pool.slots[slot]
    truth = int(sp.truth[member])
    use_models = apply_trust_weights(models, validity) if validity else dict(models)
    if slice_idx is None:
        slice_idx = np.arange(pool.n_slices)
    ep = Episode(pool, slot, member, doc, truth, doc != truth, f"diagnose|{slot}|{member}|{doc}", "", {})
    hyps = hypotheses(sp, doc)
    if len(hyps) < 2:
        return TestStatus("CONFIRMED", 1.0, 0, "only one physically plausible owner -- nothing to test", []), None
    r = run_episode(ep, use_models, slice_idx, "active", tau=tau, nmax=nmax, seed=seed, beta=beta, diag=True,
                     futility_window=futility_window, futility_margin=futility_margin)
    if r is None:
        status = TestStatus("UNCERTAIN", 0.5, 0, "no usable evidence at all for this slot", [])
        status.physical_recommendation = best_physical_test(np.full(len(hyps), 1.0 / len(hyps)), hyps)
        return status, None
    invalid_ks = {k for k, v in (validity or {}).items() if not v.validated}
    status = explain_result(r, slot, invalid_ks, tg=tg, ontology=ontology, owner_node=owner_node)
    if status.verdict == "UNCERTAIN":
        final_post = r.diag["post"][r.n_read]
        sensor_rate = (_hbin(0.5) - _hbin(r.p_doc)) / r.cost if r.cost > 0 else 0.0
        rec = best_physical_test(final_post, r.diag["hyps"])
        if rec is not None and rec.eig_per_cost > sensor_rate:
            status.physical_recommendation = rec
    return status, r


def explain_result(r, slot: str, invalid_ks=(), *, tg=None, ontology=None, owner_node: str | None = None) -> TestStatus:
    """Build the honest, always-something status from an `engine.run_episode` Result: a confident verdict
    (unchanged behaviour), or -- instead of silence -- the current best guess plus why testing stopped and what
    would actually resolve it."""
    if r.stopped:
        return TestStatus("CONFIRMED" if r.p_doc >= 0.5 else "REFUTED", r.p_doc, r.n_read, "confident", [])
    reason = "futile: this evidence type was not converging -- more tests of it would not have helped" if r.futile \
        else "exhausted the reading budget without reaching confidence"
    recs = recommend_missing_measurement(slot, invalid_ks, tg=tg, ontology=ontology, owner_node=owner_node)
    return TestStatus("UNCERTAIN", r.p_doc, r.n_read, reason, recs)
