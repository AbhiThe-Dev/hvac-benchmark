"""Check of per-building system identification against BOTH decision layers: `none` (the plain 0.95 stopping rule)
and `new` (the calibrated reliability layer that answers only when its own leave-one-building-out record supports
the stated confidence). Baseline arm only, rep 0, policy `active`, all six T1-T6 suites, `estimated` test telemetry --
same episodes/seeds scored under three variants: unadapted, Addendum 2's hand-picked shrinkage, Addendum 3's
meta-learned shrinkage.

The reliability layer must be fit SEPARATELY per variant: its inner (leave-one-training-building-out) records need
the SAME adaptation applied to the held-out training building as would be applied to a real new building, or its
calibration would not reflect that variant's actual error pattern.
"""

from __future__ import annotations

import numpy as np

from ..active import readiness as RD
from ..active import selection as SEL
from ..active.engine import run_episode
from ..active.nested import build_sim_episodes
from ..active.pools import SEASON_OF_WINDOW
from ..active.readiness import SimKind, h32
from ..active.reliability import Support, features_at, first_cross
from . import sysid as SID
from .pools import load_pool
from .verifier_eval import EXISTING, cases_for

POLICY = "active"
VARIANTS = {"base": None, "hand": dict(trim=0.10, prior_n=30), "meta": dict(trim=0.10, prior_n=0.5)}  # meta: see sysid_meta fit


def _slice_idx(e, rep: int):
    """The 'visit' setting used throughout this DR study: one 6-week window's day-slices."""
    w = (h32(e.ep_id) + 3 * rep) % 8
    return np.where(e.pool.group == w)[0], w


def _adapted(mod: dict, pool, slot: str, member: int, shrink_kw: dict, cache: dict, diags: dict, tag: str):
    key = (id(pool), slot, member)
    if key not in cache:
        adj, diag = SID.adapt_models(pool, mod, slot, exclude_member=member, **shrink_kw)
        cache[key] = adj
        diags[f"{tag}|{slot}|m{member}"] = diag
    return cache[key]


def _rec(e, mod, beta, cfg, runkw, support: Support, unit) -> dict | None:
    sl, w = _slice_idx(e, 0)
    seed = h32(e.ep_id) % 10_000
    r = run_episode(e, mod, sl, POLICY, tau=2.0, nmax=cfg["nmax"], seed=seed, beta=beta, diag=True, **runkw)
    if r is None:
        return None
    crossed, n = first_cross(r.traj, cfg["tau"])
    say = bool(r.traj[n] >= 0.5)
    f = features_at(r.diag, n, support)
    return dict(policy=POLICY, setting="visit", rep=0, ep=e.ep_id, slot=e.slot, wrong=bool(e.is_wrong), cluster=e.group, unit=unit,
                crossed=crossed, n=n, say_correct=say, p_stop=float(r.traj[n]), f=f.astype(np.float32),
                season="s%d" % SEASON_OF_WINDOW[w], family=e.meta.get("matched_to", e.meta["family"]), obs=e.meta["obs"])


def _score(eps, sim_kind, tr, cfg, support, unit, shrink_kw, fits_cache: dict, adapt_cache: dict, diags: dict, tag: str):
    rows = []
    for e in eps:
        if e.slot not in fits_cache:
            fits_cache[e.slot] = sim_kind.fit_slot(tr, e.slot, None)
        mod, beta = fits_cache[e.slot]
        if not mod:
            continue
        use = _adapted(mod, e.pool, e.slot, e.member, shrink_kw, adapt_cache, diags, tag) if shrink_kw is not None else mod
        rec = _rec(e, use, beta, cfg, SEL.get(cfg["variant"])["runkw"], support, unit)
        if rec is not None:
            rows.append(rec)
    return rows


def run_baseline_check(cfg: dict, ids_by_suite: dict, suites: list[str], variants: dict = VARIANTS) -> dict:
    """Fits on the existing (non-DR) topologies. For each variant: builds inner leave-one-training-building-out
    records (that variant's adaptation applied to the held-out building exactly as it would be to a new one), fits
    the reliability layer on them, then scores every test-suite episode under BOTH the plain rule and that layer."""
    train = EXISTING
    train_pools = {t: {0: load_pool(t, 0, "legacy")} for t in train}
    sim_kind = SimKind(cfg, topos=train, pools=train_pools, cases=cases_for(train))
    tr_all = sim_kind.train(train)
    support = sim_kind.support(tr_all)

    inner, diags = {v: [] for v in variants}, {}
    for h in train:
        tr_h = sim_kind.train([u for u in train if u != h])
        eps_h = build_sim_episodes({h: train_pools[h][0]}, [c for c in cases_for(train) if c["topology_id"] == h])
        fits_h: dict = {}
        for variant, shrink_kw in variants.items():
            inner[variant] += _score(eps_h, sim_kind, tr_h, cfg, support, h, shrink_kw, fits_h, {}, diags, f"inner|{h}|{variant}")

    layers = {v: RD._mk_layer(cfg["layer"]).fit_all(inner[v]) for v in variants}

    out = {}
    for su in suites:
        test_ids = ids_by_suite[su]
        test_pools = {t: {0: load_pool(t, 0, "estimated")} for t in test_ids}
        test_cases = cases_for(test_ids)
        eps = []
        for t in test_ids:
            eps += build_sim_episodes({t: test_pools[t][0]}, [c for c in test_cases if c["topology_id"] == t])
        fits_su: dict = {}
        outer = {}
        for variant, shrink_kw in variants.items():
            outer[variant] = _score(eps, sim_kind, tr_all, cfg, support, su, shrink_kw, fits_su, {}, diags, f"outer|{su}|{variant}")
        rows = {}
        for variant in variants:
            rows[variant] = dict(
                none=[RD._decide("none", None, r, cfg) for r in outer[variant]],
                new=[RD._decide("new", layers[variant], r, cfg) for r in outer[variant]],
            )
        out[su] = rows
    out["_inner_diag"] = {v: layers[v].diag for v in variants}
    out["_bias_diag"] = diags
    return out
