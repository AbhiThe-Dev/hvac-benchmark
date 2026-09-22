"""Sanity tests for the sequential-verification engine (synthetic pools; no simulator needed)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from docmismatch.active.engine import Episode, run_episode
from docmismatch.active.model import fit_slot_models
from docmismatch.active.pools import Pool, SlotPool


def make_pool(separation: float, seed=0, n_members=8, n_owners=3, S=24, name="b#r0"):
    rng = np.random.default_rng(seed)
    ctx = rng.normal(size=(S, 3))
    E = np.zeros((S, 3, n_owners, n_members))
    truth = rng.integers(0, n_owners, n_members)
    for m in range(n_members):
        for o in range(n_owners):
            base = 0.1 if o == truth[m] else 0.1 + separation
            for k in range(3):
                E[:, k, o, m] = np.abs(base * np.exp(rng.normal(0, 0.15, S)))
    sp = SlotPool("ahu_vav", [f"O{i}" for i in range(n_owners)], [f"M{i}" for i in range(n_members)], truth, E, [("AHU", "x", None)] * n_owners, np.ones(n_owners))
    p = Pool(name, "sim", ctx, np.arange(S) % 4, np.arange(S) // 6)
    p.slots["ahu_vav"] = sp
    return p


def fit(separation):
    train = [make_pool(separation, seed=s, name=f"t{s}#r0") for s in (1, 2, 3)]
    return train, fit_slot_models(train, "ahu_vav", False)


def episode(pool, wrong):
    sp = pool.slots["ahu_vav"]
    m = 0
    t = int(sp.truth[m])
    doc = (t + 1) % len(sp.owners) if wrong else t
    return Episode(pool, "ahu_vav", m, doc, t, wrong, "e", "g", {})


def test_separable_case_reaches_correct_confident_verdict():
    _, mod = fit(2.0)
    test = make_pool(2.0, seed=9)
    for wrong in (True, False):
        r = run_episode(episode(test, wrong), mod, np.arange(24), "active", tau=0.95, nmax=8)
        assert r.stopped and r.verdict_correct and r.n_read <= 3


def test_no_information_keeps_belief_at_prior_and_is_not_confident():
    _, mod = fit(0.0)
    test = make_pool(0.0, seed=9)
    r = run_episode(episode(test, True), mod, np.arange(24), "random", tau=0.95, nmax=12, beta=1.0)
    assert 0.02 < r.traj[-1] < 0.98 and not r.stopped


def test_stopping_can_be_derived_post_hoc():
    """An online run with threshold tau must equal truncating the never-stopped trajectory at the first crossing."""
    _, mod = fit(1.0)
    test = make_pool(1.0, seed=9)
    ep = episode(test, True)
    for pol in ("active", "random", "traversal"):
        full = run_episode(ep, mod, np.arange(24), pol, tau=2.0, nmax=12, seed=3)
        on = run_episode(ep, mod, np.arange(24), pol, tau=0.9, nmax=12, seed=3)
        hit = np.flatnonzero((full.traj >= 0.9) | (full.traj <= 0.1))
        n = int(hit[0]) if len(hit) else 12
        assert on.n_read == n and abs(on.p_doc - full.traj[n]) < 1e-9


def test_true_owner_always_in_hypotheses_and_flow_null_readings_consume_budget():
    from docmismatch.active.pools import hypotheses
    p = make_pool(1.0)
    sp = p.slots["ahu_vav"]
    for m in range(len(sp.members)):
        assert int(sp.truth[m]) in hypotheses(sp, int(sp.truth[m]))
    sp.E[:, :, :, 0] = np.nan  # member 0 never informative
    _, mod = fit(1.0)
    r = run_episode(episode(p, True), mod, np.arange(24), "active", tau=0.95, nmax=6)
    assert r.n_read == 6 and r.n_info == 0 and abs(r.p_doc - 0.5) < 1e-9
