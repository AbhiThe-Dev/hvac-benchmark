"""Tests for the selection/model options added for the real-data fix (informativeness model + online learning, shared pair effect across
channels, context clamping, random_info baseline, custom-order hook). Defaults must reproduce the original engine exactly."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from docmismatch.active import selection as SEL
from docmismatch.active.engine import Episode, run_episode, _Actions
from docmismatch.active.model import _info_icc, _logit_fit, estimate_rho, fit_slot_models
from docmismatch.active.pools import Pool, SlotPool, hypotheses


def make_pool(separation=1.5, seed=0, n_members=8, n_owners=4, S=36, name="b#r0", nan_when_off=True, chan_corr=0.0):
    """ctx = (oat, swing, occupancy). Occupancy 0 slices are all-NaN (fan off): informativeness is a function of the context the OAT-only
    mean model does not see. Pair offsets are shared across channels with correlation `chan_corr`."""
    rng = np.random.default_rng(seed)
    occ = np.tile([0.0, 0.25, 0.5, 1.0, 1.0, 0.5], S // 6 + 1)[:S]
    ctx = np.column_stack([rng.normal(size=S), rng.normal(size=S), occ])
    E = np.zeros((S, 3, n_owners, n_members))
    truth = rng.integers(0, n_owners, n_members)
    for m in range(n_members):
        for o in range(n_owners):
            base = 0.1 if o == truth[m] else 0.1 + separation
            shared = rng.normal(0, 0.4)
            for k in range(3):
                off = np.sqrt(chan_corr) * shared + np.sqrt(1 - chan_corr) * rng.normal(0, 0.4)
                E[:, k, o, m] = np.abs(base * np.exp(rng.normal(0, 0.15, S) + off))
    if nan_when_off:
        E[occ == 0.0] = np.nan
    sp = SlotPool("ahu_vav", [f"O{i}" for i in range(n_owners)], [f"M{i}" for i in range(n_members)], truth, E, [("AHU", "x", None)] * n_owners, np.ones(n_owners))
    p = Pool(name, "sim", ctx, np.arange(S) % 4, np.arange(S) // 6)
    p.slots["ahu_vav"] = sp
    return p


def ep_for(pool, wrong=True, m=0):
    sp = pool.slots["ahu_vav"]
    t = int(sp.truth[m])
    return Episode(pool, "ahu_vav", m, (t + 1) % len(sp.owners) if wrong else t, t, wrong, "e", "g", {})


def train(chan_corr=0.0, sep=1.5, **fitkw):
    pools = [make_pool(separation=sep, seed=s, name=f"t{s}#r0", chan_corr=chan_corr) for s in (1, 2, 3)]
    return pools, fit_slot_models(pools, "ahu_vav", "oat", **fitkw)


def test_defaults_unchanged_by_new_flags_when_they_reduce_to_the_original_model():
    _, mod = train()
    test = make_pool(seed=9)
    ep = ep_for(test)
    a = run_episode(ep, mod, np.arange(36), "active", tau=2.0, nmax=10, seed=4)
    for m in mod.values():
        assert m.rho == 0.0 and m.kappa is None and m.info_mode is None and not m.clip_ctx
    b = run_episode(ep, mod, np.arange(36), "active", tau=2.0, nmax=10, seed=4, shared_pair=True)   # rho = 0 -> identical
    assert np.allclose(a.traj, b.traj) and a.order == b.order


def test_info_icc_detects_all_or_nothing_flag_per_unit():
    rng = np.random.default_rng(0)
    unit = np.repeat(np.arange(60), 8)
    shared = np.repeat(rng.random(60) < 0.5, 8)
    assert _info_icc(shared, unit) > 0.9
    assert _info_icc(rng.random(len(unit)) < 0.5, unit) < 0.15


def test_logit_fit_recovers_probability_structure():
    rng = np.random.default_rng(1)
    x = rng.normal(size=4000)
    y = (rng.random(4000) < 1 / (1 + np.exp(-(0.5 + 2 * x)))).astype(float)
    w = _logit_fit(np.column_stack([np.ones(4000), x]), y)
    assert abs(w[0] - 0.5) < 0.2 and abs(w[1] - 2.0) < 0.3


def test_informativeness_model_sees_occupancy_and_online_update_skips_dead_slices():
    _, m_old = train()
    _, m_new = train(info_mode="info", online_info=True)
    ctx = np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
    p_old = m_old[0].params(ctx)[-1]
    p_new = m_new[0].params(ctx)[-1]
    assert abs(p_old[0] - p_old[1]) < 0.15          # OAT-only model cannot tell the dead slice from the live one
    assert p_new[0] <= 0.05 and p_new[1] >= 0.9     # the informativeness model can
    assert m_new[0].kappa is not None
    test = make_pool(seed=9, nan_when_off=True)
    test.ctx[:, :2] = 0.0            # equal context everywhere: only informativeness differs between slices
    ep = ep_for(test)
    idx = np.concatenate([np.where(test.ctx[:, 2] == 0.0)[0], np.where(test.ctx[:, 2] == 1.0)[0][:6]])   # half the slices on offer are dead
    frac = {}
    for name, mod, kw in (("old", m_old, {}), ("new", m_new, dict(online_info=True))):
        frac[name] = np.mean([(lambda r: r.n_info / r.n_read)(run_episode(ep, mod, idx, "active", tau=2.0, nmax=8, seed=sd, **kw)) for sd in range(6)])
    assert frac["new"] > frac["old"] + 0.2 and frac["new"] >= 0.9


def test_online_info_learns_from_an_empty_reading_in_the_same_slice():
    """A slice whose streams turn out flat should stop being offered, even where the context model cannot tell (sim pool with NaN slices
    that are NOT a function of context)."""
    pools = [make_pool(seed=s, name=f"t{s}#r0", nan_when_off=False) for s in (1, 2, 3)]
    rng = np.random.default_rng(0)
    for p in pools:                       # random slices dead for all pairs: pure slice-level structure, invisible to the context
        dead = rng.random(p.n_slices) < 0.4
        p.slots["ahu_vav"].E[dead] = np.nan
    mod = fit_slot_models(pools, "ahu_vav", "oat", info_mode="info", online_info=True)
    assert mod[0].kappa < 2.0             # high intra-slice correlation of the flag -> strong pooling
    test = make_pool(seed=9, nan_when_off=False)
    test.ctx[:, :] = 0.0
    dead = np.zeros(36, bool); dead[::2] = True
    test.slots["ahu_vav"].E[dead] = np.nan
    ep = ep_for(test)
    on = np.mean([run_episode(ep, mod, np.arange(36), "active", tau=2.0, nmax=8, seed=sd, online_info=True).n_info for sd in range(8)])
    off = np.mean([run_episode(ep, mod, np.arange(36), "active", tau=2.0, nmax=8, seed=sd).n_info for sd in range(8)])
    assert on > off + 1.0


def test_shared_pair_effect_makes_extra_channels_of_the_same_pair_worth_less():
    """Pair offsets fully shared across channels: rho is estimated high; reading the doc pair on all three channels then moves the belief
    less than under independent per-channel effects."""
    _, mod = train(chan_corr=0.9, sep=0.4, shared_pair=True)
    rho = mod[0].rho
    assert rho > 0.4
    test = make_pool(separation=0.4, seed=9, chan_corr=0.9)
    ep = ep_for(test, wrong=True)
    acts_order = None
    sl = np.array([i for i in range(36) if test.ctx[i, 2] > 0])
    hy = hypotheses(test.slots["ahu_vav"], ep.doc)
    acts = _Actions(ep, mod, hy, sl, 3.0)
    order = [int(np.flatnonzero((acts.j == 0) & (acts.k == k) & (acts.spos == 0))[0]) for k in (0, 1, 2)]
    ind = run_episode(ep, mod, sl, "custom", tau=2.0, nmax=3, order=order, shared_pair=False)
    shr = run_episode(ep, mod, sl, "custom", tau=2.0, nmax=3, order=order, shared_pair=True)
    lo = lambda p: abs(np.log(p / (1 - p)))   # noqa: E731
    assert lo(shr.traj[3]) < lo(ind.traj[3])


def test_estimate_rho_zero_for_independent_channels():
    _, mod = train(chan_corr=0.0, shared_pair=True)
    assert mod[0].rho < 0.35


def test_clip_ctx_freezes_regression_outside_training_range():
    _, mod = train(clip_ctx=True)
    m = mod[0]
    hi = m.scaler.hi
    inside = m.params(hi[None, :])
    far = m.params((hi + np.array([50.0, 0.0, 0.0]))[None, :])
    assert all(np.allclose(a, b) for a, b in zip(inside, far))
    _, mod2 = train(clip_ctx=False)
    a, b = mod2[0].params(m.scaler.hi[None, :]), mod2[0].params((m.scaler.hi + np.array([50.0, 0.0, 0.0]))[None, :])
    assert not np.allclose(a[0], b[0])


def test_random_info_only_reads_predicted_informative_and_custom_order_is_honoured():
    _, mod = train(info_mode="info", online_info=True)
    test = make_pool(seed=9)
    ep = ep_for(test)
    r = run_episode(ep, mod, np.arange(36), "random_info", tau=2.0, nmax=12, seed=5, online_info=True)
    assert r.n_info == r.n_read                                  # never spends a reading on the dead (occupancy 0) slices
    r2 = run_episode(ep, mod, np.arange(36), "custom", tau=2.0, nmax=4, order=[5, 3, 9, 1])
    assert r2.order == [5, 3, 9, 1]


def test_stopping_derivable_post_hoc_with_new_options():
    kw = dict(online_info=True, shared_pair=True)
    _, mod = train(chan_corr=0.5, info_mode="info", online_info=True, shared_pair=True)
    test = make_pool(seed=9, chan_corr=0.5)
    ep = ep_for(test)
    for pol in ("active", "random_info"):
        full = run_episode(ep, mod, np.arange(36), pol, tau=2.0, nmax=12, seed=3, **kw)
        on = run_episode(ep, mod, np.arange(36), pol, tau=0.9, nmax=12, seed=3, **kw)
        hit = np.flatnonzero((full.traj >= 0.9) | (full.traj <= 0.1))
        n = int(hit[0]) if len(hit) else 12
        assert on.n_read == n and abs(on.p_doc - full.traj[n]) < 1e-9


def test_variants_registry_defaults_are_empty_and_sel_enables_new_options():
    assert SEL.get("") == dict(fitkw={}, runkw={}, extra=())
    v = SEL.get("sel")
    assert v["fitkw"]["shared_pair"] and v["fitkw"]["online_info"] and v["runkw"]["shared_pair"] and "random_info" in v["extra"]
