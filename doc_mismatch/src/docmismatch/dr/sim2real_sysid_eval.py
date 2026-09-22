"""Does the system-ID fix (Addenda 2-3) hold on real data? (PREREGISTRATION_DR.md Addendum 4)

vav_zone likelihood fit ONLY on simulated buildings (Addendum 1's zero-shot setup, same F->C context fix), scored
against the real DEV building's own vav_zone episodes, under three variants: unadapted / hand-picked shrinkage /
meta-learned shrinkage. The bias-adaptation mechanism (sysid.estimate_bias) is applied to the REAL pool exactly as
to a simulated one -- no special-casing, since Pool/SlotPool are shared structures. The reliability layer is fit
ONLY on sim inner records (real data never enters calibration, only scoring).
"""

from __future__ import annotations

import numpy as np

from ..active import readiness as RD
from ..active.nested import build_sim_episodes
from ..active.reliability import Support, features_at, first_cross
from ..active.engine import run_episode
from ..active.readiness import SimKind, h32
from . import sysid as SID
from .pools import load_pool
from .sim2real_eval import real_vav_zone_episodes
from .sysid_eval import VARIANTS
from .verifier_eval import EXISTING, cases_for

SLOT = "vav_zone"


def _sim_rec(e, mod, beta, cfg, runkw, support, unit, shrink_kw, adapt_cache, diags, tag):
    from ..active.pools import SEASON_OF_WINDOW
    w = (h32(e.ep_id) + 0) % 8
    sl = np.where(e.pool.group == w)[0]
    use = mod
    if shrink_kw is not None:
        key = (id(e.pool), SLOT, e.member)
        if key not in adapt_cache:
            adj, diag = SID.adapt_models(e.pool, mod, SLOT, exclude_member=e.member, **shrink_kw)
            adapt_cache[key] = adj
            diags[f"{tag}|m{e.member}"] = diag
        use = adapt_cache[key]
    seed = h32(e.ep_id) % 10_000
    r = run_episode(e, use, sl, "active", tau=2.0, nmax=cfg["nmax"], seed=seed, beta=beta, diag=True, **runkw)
    if r is None:
        return None
    crossed, n = first_cross(r.traj, cfg["tau"])
    say = bool(r.traj[n] >= 0.5)
    f = features_at(r.diag, n, support)
    return dict(policy="active", setting="visit", rep=0, ep=e.ep_id, slot=e.slot, wrong=bool(e.is_wrong), cluster=e.group, unit=unit,
                crossed=crossed, n=n, say_correct=say, p_stop=float(r.traj[n]), f=f.astype(np.float32),
                season="s%d" % SEASON_OF_WINDOW[w], family=e.meta.get("matched_to", e.meta["family"]), obs=e.meta["obs"])


def _real_rec(e, mod, beta, cfg, runkw, support, shrink_kw, adapt_cache, diags):
    sl = np.where(e.pool.group == e.meta["day"])[0]
    use = mod
    if shrink_kw is not None:
        key = (id(e.pool), SLOT, e.member)
        if key not in adapt_cache:
            adj, diag = SID.adapt_models(e.pool, mod, SLOT, exclude_member=e.member, **shrink_kw)
            adapt_cache[key] = adj
            diags[f"real|m{e.member}"] = diag
        use = adapt_cache[key]
    seed = h32(e.ep_id) % 10_000
    r = run_episode(e, use, sl, "active", tau=2.0, nmax=cfg["nmax"], seed=seed, beta=beta, diag=True, **runkw)
    if r is None:
        return None
    crossed, n = first_cross(r.traj, cfg["tau"])
    say = bool(r.traj[n] >= 0.5)
    f = features_at(r.diag, n, support)
    return dict(policy="active", setting="real_dev", rep=0, ep=f"realday{e.meta['day']:02d}|{e.ep_id}", slot=e.slot, wrong=bool(e.is_wrong),
                cluster=e.group, unit="real_dev", crossed=crossed, n=n, say_correct=say, p_stop=float(r.traj[n]), f=f.astype(np.float32),
                season=e.meta["season"], family=e.meta["family"], obs=e.meta["obs"])


def run_check(cfg: dict, variants: dict = VARIANTS) -> dict:
    from ..active import selection as SEL
    V = SEL.get(cfg["variant"])["runkw"]
    train = EXISTING
    train_pools = {t: {0: load_pool(t, 0, "legacy")} for t in train}
    sim_kind = SimKind(cfg, topos=train, pools=train_pools, cases=cases_for(train))
    tr_all = sim_kind.train(train)
    support = sim_kind.support(tr_all)
    mod, beta = sim_kind.fit_slot(tr_all, SLOT, None)
    if not mod:
        return dict(ok=False, reason="no vav_zone model")

    # inner: leave-one-sim-training-building-out, slot=vav_zone only (real data never touches this)
    inner, diags = {v: [] for v in variants}, {}
    for h in train:
        tr_h = sim_kind.train([u for u in train if u != h])
        mod_h, beta_h = sim_kind.fit_slot(tr_h, SLOT, None)
        if not mod_h:
            continue
        eps_h = [e for e in build_sim_episodes({h: train_pools[h][0]}, [c for c in cases_for(train) if c["topology_id"] == h]) if e.slot == SLOT]
        for variant, shrink_kw in variants.items():
            cache = {}
            for e in eps_h:
                rec = _sim_rec(e, mod_h, beta_h, cfg, V, support, h, shrink_kw, cache, diags, f"inner|{h}|{variant}")
                if rec is not None:
                    inner[variant].append(rec)

    layers = {v: RD._mk_layer(cfg["layer"]).fit_all(inner[v]) for v in variants}

    real_pool, real_eps = real_vav_zone_episodes()
    outer = {}
    for variant, shrink_kw in variants.items():
        cache = {}
        rows = []
        for e in real_eps:
            rec = _real_rec(e, mod, beta, cfg, V, support, shrink_kw, cache, diags)
            if rec is not None:
                rows.append(rec)
        outer[variant] = rows

    out = {}
    for variant in variants:
        out[variant] = dict(
            none=[RD._decide("none", None, r, cfg) for r in outer[variant]],
            new=[RD._decide("new", layers[variant], r, cfg) for r in outer[variant]],
        )
    out["_inner_diag"] = {v: layers[v].diag for v in variants}
    out["_bias_diag"] = diags
    out["_n_real_episodes"] = len(real_eps)
    out["_n_real_days"] = len(real_pool.days)
    return out
