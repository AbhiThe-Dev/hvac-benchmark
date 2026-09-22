"""Evaluation of excluding structurally-invalid channels (PREREGISTRATION_DR.md Addendum 5):
  (1) real DEV, plain rule + honest layer, WITH vs WITHOUT `vav_zone` channels 0/2 excluded (Addenda 5a/5b's finding).
  (2) simulation-only ceiling on the T1-T6 baseline-arm suites: the SAME ablation in simulation, where the excluded
      channels DO carry real signal -- an upper bound on the value of recovering them, never evidence the real
      transfer works (see Addendum 5's explicit caveat).
"""

from __future__ import annotations

import numpy as np

from ..active import measurement as M
from ..active import readiness as RD
from ..active import selection as SEL
from ..active import trust as T
from ..active.engine import run_episode
from ..active.nested import build_sim_episodes
from ..active.pools import SEASON_OF_WINDOW
from ..active.readiness import SimKind, h32
from ..active.reliability import Support, features_at, first_cross
from .pools import load_pool
from .sim2real_eval import real_vav_zone_episodes
from .verifier_eval import EXISTING, cases_for

SLOT = "vav_zone"
# scripts/34's actual result (Addendum 5a, run BEFORE this ablation): channel 2 is confidently WORSE than chance
# on real DEV (lb_bal_acc 0.307); channel 0 is only borderline-validated (lb_bal_acc 0.500, point 0.516) -- weak
# real signal, not confidently absent. The structural check (Addendum 5b) flags BOTH 0 and 2 as lacking their
# designed instrument (no per-box airflow documented anywhere in the corpus). Three variants let the DATA show
# which exclusion choice is worth it, rather than presupposing "0 and 2 both fail" before running either check.
VARIANTS = {"include": frozenset(), "exclude_stat": frozenset({2}), "exclude_struct": frozenset({0, 2})}


def _real_rec(e, mod, beta, cfg, runkw, support, exclude_k, futility_window=0, futility_margin=0.0):
    sl = np.where(e.pool.group == e.meta["day"])[0]
    seed = h32(e.ep_id) % 10_000
    r = run_episode(e, mod, sl, "active", tau=2.0, nmax=cfg["nmax"], seed=seed, beta=beta, diag=True, exclude_k=exclude_k,
                    futility_window=futility_window, futility_margin=futility_margin, **runkw)
    if r is None:
        return None
    crossed, n = first_cross(r.traj, cfg["tau"])
    say = bool(r.traj[n] >= 0.5)
    f = features_at(r.diag, n, support)
    return dict(policy="active", setting="real_dev", rep=0, ep=f"realday{e.meta['day']:02d}|{e.ep_id}", slot=e.slot, wrong=bool(e.is_wrong),
                cluster=e.group, unit="real_dev", crossed=crossed, n=n, say_correct=say, p_stop=float(r.traj[n]), f=f.astype(np.float32),
                season=e.meta["season"], family=e.meta["family"], obs=e.meta["obs"], n_read=int(r.n_read), futile=bool(r.futile))


def _sim_rec(e, mod, beta, cfg, runkw, support, exclude_k, tag_unit):
    w = h32(e.ep_id) % 8
    sl = np.where(e.pool.group == w)[0]
    seed = h32(e.ep_id) % 10_000
    r = run_episode(e, mod, sl, "active", tau=2.0, nmax=cfg["nmax"], seed=seed, beta=beta, diag=True, exclude_k=exclude_k, **runkw)
    if r is None:
        return None
    crossed, n = first_cross(r.traj, cfg["tau"])
    say = bool(r.traj[n] >= 0.5)
    f = features_at(r.diag, n, support) if support is not None else None
    return dict(policy="active", setting="visit", rep=0, ep=e.ep_id, slot=e.slot, wrong=bool(e.is_wrong), cluster=e.group, unit=tag_unit,
                crossed=crossed, n=n, say_correct=say, p_stop=float(r.traj[n]), f=(f.astype(np.float32) if f is not None else None),
                season="s%d" % SEASON_OF_WINDOW[w], family=e.meta.get("matched_to", e.meta["family"]), obs=e.meta["obs"])


def run_real_ablation(cfg: dict, variants=VARIANTS) -> dict:
    """Real DEV vav_zone episodes (never SEALED), plain rule + honest layer, WITH vs WITHOUT channels 0/2 excluded.
    Inner (honest-layer calibration) records use the SAME exclusion as their variant, exactly as deployed."""
    V = SEL.get(cfg["variant"])["runkw"]
    train = EXISTING
    train_pools = {t: {0: load_pool(t, 0, "legacy")} for t in train}
    sim_kind = SimKind(cfg, topos=train, pools=train_pools, cases=cases_for(train))
    tr_all = sim_kind.train(train)
    support = sim_kind.support(tr_all)
    mod, beta = sim_kind.fit_slot(tr_all, SLOT, None)
    if not mod:
        return dict(ok=False, reason="no vav_zone model")

    real_pool, real_eps = real_vav_zone_episodes()

    inner = {v: [] for v in variants}
    for h in train:
        tr_h = sim_kind.train([u for u in train if u != h])
        mod_h, beta_h = sim_kind.fit_slot(tr_h, SLOT, None)
        if not mod_h:
            continue
        eps_h = [e for e in build_sim_episodes({h: train_pools[h][0]}, [c for c in cases_for(train) if c["topology_id"] == h]) if e.slot == SLOT]
        for variant, exclude_k in variants.items():
            for e in eps_h:
                rec = _sim_rec(e, mod_h, beta_h, cfg, V, support, exclude_k, h)
                if rec is not None:
                    inner[variant].append(rec)

    layers = {v: RD._mk_layer(cfg["layer"]).fit_all(inner[v]) for v in variants}

    outer = {}
    for variant, exclude_k in variants.items():
        rows = []
        for e in real_eps:
            rec = _real_rec(e, mod, beta, cfg, V, support, exclude_k)
            if rec is not None:
                rows.append(rec)
        outer[variant] = rows

    out = {}
    for variant in variants:
        out[variant] = dict(
            none=[RD._decide("none", None, r, cfg) for r in outer[variant]],
            new=[RD._decide("new", layers[variant], r, cfg) for r in outer[variant]],
        )
    out["_n_real_episodes"] = len(real_eps)
    out["_inner_diag"] = {v: layers[v].diag for v in variants}
    return out


FUTILITY_VARIANTS = {"no_futility": dict(exclude_k=frozenset({0, 2}), futility_window=0, futility_margin=0.0),
                      "futility": dict(exclude_k=frozenset({0, 2}), futility_window=4, futility_margin=0.05)}


def run_futility_eval(cfg: dict, variants=FUTILITY_VARIANTS) -> dict:
    """Addendum 7: on top of Addendum 5's best-validated variant (channels 0+2 excluded), real DEV vav_zone
    episodes WITH vs WITHOUT the futility-stopping mechanism. Inner (honest-layer) records use the SAME
    futility setting as their variant, exactly as deployed. Reports `n_read`/`futile` per row for the technician-
    test-count comparison, alongside the usual accuracy/coverage decision rows."""
    V = SEL.get(cfg["variant"])["runkw"]
    train = EXISTING
    train_pools = {t: {0: load_pool(t, 0, "legacy")} for t in train}
    sim_kind = SimKind(cfg, topos=train, pools=train_pools, cases=cases_for(train))
    tr_all = sim_kind.train(train)
    support = sim_kind.support(tr_all)
    mod, beta = sim_kind.fit_slot(tr_all, SLOT, None)
    if not mod:
        return dict(ok=False, reason="no vav_zone model")

    real_pool, real_eps = real_vav_zone_episodes()

    inner = {v: [] for v in variants}
    for h in train:
        tr_h = sim_kind.train([u for u in train if u != h])
        mod_h, beta_h = sim_kind.fit_slot(tr_h, SLOT, None)
        if not mod_h:
            continue
        eps_h = [e for e in build_sim_episodes({h: train_pools[h][0]}, [c for c in cases_for(train) if c["topology_id"] == h]) if e.slot == SLOT]
        for variant, kw in variants.items():
            for e in eps_h:
                rec = _sim_rec(e, mod_h, beta_h, cfg, V, support, kw["exclude_k"], h)
                if rec is not None:
                    inner[variant].append(rec)

    layers = {v: RD._mk_layer(cfg["layer"]).fit_all(inner[v]) for v in variants}

    outer = {}
    for variant, kw in variants.items():
        rows = []
        for e in real_eps:
            rec = _real_rec(e, mod, beta, cfg, V, support, kw["exclude_k"], kw["futility_window"], kw["futility_margin"])
            if rec is not None:
                rows.append(rec)
        outer[variant] = rows

    out = {}
    for variant in variants:
        out[variant] = dict(
            none=[RD._decide("none", None, r, cfg) for r in outer[variant]],
            new=[RD._decide("new", layers[variant], r, cfg) for r in outer[variant]],
            raw=outer[variant],
        )
    out["_n_real_episodes"] = len(real_eps)
    return out


FUTILITY_KW = dict(futility_window=4, futility_margin=0.05)   # Addendum 7's frozen values, reused as-is here


def run_trust_eval(cfg: dict) -> dict:
    """Addendum 8: does a continuous, real-data-derived trust weight per channel (`trust.apply_trust_weights`,
    fed by `measurement.real_channel_validity`) beat Addendum 5's blunt binary exclusion (`exclude_struct`)? All
    three variants run with Addendum 7's futility stopping on (the realistic deployed configuration):
      no_adaptation : all 3 channels at full trust (the original baseline)
      exclude_struct: channels 0+2 dropped entirely (Addendum 5's best binary variant)
      trust_weighted: every channel kept, weighted by its OWN real_channel_validity point estimate
    """
    V = SEL.get(cfg["variant"])["runkw"]
    train = EXISTING
    train_pools = {t: {0: load_pool(t, 0, "legacy")} for t in train}
    sim_kind = SimKind(cfg, topos=train, pools=train_pools, cases=cases_for(train))
    tr_all = sim_kind.train(train)
    support = sim_kind.support(tr_all)
    mod, beta = sim_kind.fit_slot(tr_all, SLOT, None)
    if not mod:
        return dict(ok=False, reason="no vav_zone model")

    real_pool, real_eps = real_vav_zone_episodes()
    validity = M.real_channel_validity(real_pool, SLOT, mod)
    weighted_mod = T.apply_trust_weights(mod, validity)

    mods = {"no_adaptation": mod, "exclude_struct": mod, "trust_weighted": weighted_mod}
    exkw = {"no_adaptation": frozenset(), "exclude_struct": frozenset({0, 2}), "trust_weighted": frozenset()}
    variants = list(mods)

    inner = {v: [] for v in variants}
    for h in train:
        tr_h = sim_kind.train([u for u in train if u != h])
        mod_h, beta_h = sim_kind.fit_slot(tr_h, SLOT, None)
        if not mod_h:
            continue
        weighted_mod_h = T.apply_trust_weights(mod_h, validity)   # same real-data-derived weights, different (leave-one-out) base fit
        mods_h = {"no_adaptation": mod_h, "exclude_struct": mod_h, "trust_weighted": weighted_mod_h}
        eps_h = [e for e in build_sim_episodes({h: train_pools[h][0]}, [c for c in cases_for(train) if c["topology_id"] == h]) if e.slot == SLOT]
        for variant in variants:
            for e in eps_h:
                rec = _sim_rec(e, mods_h[variant], beta_h, cfg, {**V, **FUTILITY_KW}, support, exkw[variant], h)
                if rec is not None:
                    inner[variant].append(rec)

    layers = {v: RD._mk_layer(cfg["layer"]).fit_all(inner[v]) for v in variants}

    outer = {}
    for variant in variants:
        rows = []
        for e in real_eps:
            rec = _real_rec(e, mods[variant], beta, cfg, V, support, exkw[variant], **FUTILITY_KW)
            if rec is not None:
                rows.append(rec)
        outer[variant] = rows

    out = {}
    for variant in variants:
        out[variant] = dict(
            none=[RD._decide("none", None, r, cfg) for r in outer[variant]],
            new=[RD._decide("new", layers[variant], r, cfg) for r in outer[variant]],
            raw=outer[variant],
        )
    out["_n_real_episodes"] = len(real_eps)
    out["_weights"] = {k: T.trust_weight(v) for k, v in validity.items()}
    return out


def run_sim_ceiling(cfg: dict, ids_by_suite: dict, suites: list[str], variants=VARIANTS) -> dict:
    """Simulation-only ceiling on T1-T6 (baseline arm, plain rule only): the value of the SAME exclusion where
    the excluded channels DO carry real signal. An upper bound, not evidence the real recommendation pays off."""
    V = SEL.get(cfg["variant"])["runkw"]
    train = EXISTING
    train_pools = {t: {0: load_pool(t, 0, "legacy")} for t in train}
    sim_kind = SimKind(cfg, topos=train, pools=train_pools, cases=cases_for(train))
    tr_all = sim_kind.train(train)
    mod, beta = sim_kind.fit_slot(tr_all, SLOT, None)
    if not mod:
        return dict(ok=False, reason="no vav_zone model")

    out = {}
    for su in suites:
        test_ids = ids_by_suite[su]
        test_pools = {t: {0: load_pool(t, 0, "estimated")} for t in test_ids}
        test_cases = cases_for(test_ids)
        eps = []
        for t in test_ids:
            eps += [e for e in build_sim_episodes({t: test_pools[t][0]}, [c for c in test_cases if c["topology_id"] == t]) if e.slot == SLOT]
        rows = {}
        for variant, exclude_k in variants.items():
            recs = []
            for e in eps:
                rec = _sim_rec(e, mod, beta, cfg, V, None, exclude_k, su)
                if rec is not None:
                    recs.append(rec)
            rows[variant] = [RD._decide("none", None, r, cfg) for r in recs]
        out[su] = rows
    return out
