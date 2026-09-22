"""Guards for the futility-stopping mechanism in engine.run_episode (the "guide vs. give up" rethink):
default off = bit-identical to before; on = stop early ONLY when continued testing genuinely isn't converging,
never when it is (even slowly)."""
from types import SimpleNamespace

import numpy as np
import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.active.engine import Episode, run_episode  # noqa: E402


class FakeModel:
    def __init__(self, mu_m, sd_m, mu_x, sd_x):
        self.mu_m, self.sd_m, self.mu_x, self.sd_x = mu_m, sd_m, mu_x, sd_x
        self.fit = {"M": SimpleNamespace(tau=0.05), "X": SimpleNamespace(tau=0.05)}
        self.kappa = None
        self.rho = 0.0
        self.omega = 0.0
        self.rho_s = 0.0

    def params(self, ctx):
        n = len(ctx)
        return [np.full(n, self.mu_m), np.full(n, self.sd_m), np.full(n, self.mu_x), np.full(n, self.sd_x), np.full(n, 0.5)]


class FakeSlotPool:
    def __init__(self, E, truth, n_owners=None):
        no = n_owners or E.shape[-2]
        self.members = list(range(E.shape[-1]))
        self.owners = list(range(no))
        self.truth = truth
        self.E = E
        self.owner_class = [("VAV",)] * no
        self.owner_size = np.ones(no)


class FakePool:
    def __init__(self, slots, n_slices):
        self.slots = slots
        self.ctx = np.zeros((n_slices, 3))

    @property
    def n_slices(self):
        return len(self.ctx)


def _pool(rng, n_slices, n_mem, mu_m, sd_m, mu_x, sd_x, noise_only=False):
    truth = np.arange(n_mem)
    E = np.full((n_slices, 1, n_mem, n_mem), np.nan)
    for s in range(n_slices):
        for m in range(n_mem):
            for o in range(n_mem):
                if noise_only:
                    # exactly equidistant from mu_m/mu_x with equal sd -> log-likelihood ratio is EXACTLY 0 for
                    # every reading (genuinely zero information, not just "usually uninformative" -- a single
                    # lucky/unlucky draw can otherwise swing a small-H posterior hard by chance)
                    z = (mu_m + mu_x) / 2 + rng.normal(0, 0.01)
                else:
                    z = rng.normal(mu_m if o == m else mu_x, sd_m if o == m else sd_x)
                E[s, 0, o, m] = np.exp(z) - 0.05
    sp = FakeSlotPool(E, truth)
    return FakePool({"vav_zone": sp}, n_slices)


def _episode(pool, member=0, doc=0):
    return Episode(pool, "vav_zone", member, doc, member, doc != member, "ep|0", "g0", {})


def test_futility_off_by_default_is_bit_identical():
    rng = np.random.default_rng(0)
    pool = _pool(rng, 60, 8, mu_m=-0.5, sd_m=0.2, mu_x=0.8, sd_x=0.2)
    ep = _episode(pool)
    model = {0: FakeModel(-0.5, 0.2, 0.8, 0.2)}
    sl = np.arange(pool.n_slices)
    r1 = run_episode(ep, model, sl, "active", tau=0.95, nmax=24, seed=0)
    r2 = run_episode(ep, model, sl, "active", tau=0.95, nmax=24, seed=0, futility_window=0)
    assert np.allclose(r1.traj, r2.traj)
    assert r1.order == r2.order
    assert r2.futile is False


def test_futility_triggers_on_pure_noise_well_before_budget():
    rng = np.random.default_rng(1)
    # model expects strong separation (mu_m far from mu_x) but the DATA carries none -- exactly the real vav_zone
    # channel-2 situation: a confidently-wrong model applied to uninformative real evidence
    pool = _pool(rng, 200, 10, mu_m=-0.5, sd_m=0.2, mu_x=0.8, sd_x=0.2, noise_only=True)
    ep = _episode(pool)
    model = {0: FakeModel(-0.5, 0.2, 0.8, 0.2)}
    sl = np.arange(pool.n_slices)
    r = run_episode(ep, model, sl, "active", tau=0.95, nmax=24, seed=0, futility_window=4, futility_margin=0.05)
    assert r is not None
    assert r.futile is True
    assert r.stopped is False
    assert r.n_read < 24


def test_futility_does_not_trigger_on_strong_converging_signal():
    rng = np.random.default_rng(2)
    pool = _pool(rng, 200, 10, mu_m=-2.0, sd_m=0.15, mu_x=2.0, sd_x=0.15)
    ep = _episode(pool)
    model = {0: FakeModel(-2.0, 0.15, 2.0, 0.15)}
    sl = np.arange(pool.n_slices)
    r = run_episode(ep, model, sl, "active", tau=0.95, nmax=24, seed=0, futility_window=4, futility_margin=0.05)
    assert r is not None
    assert r.futile is False
    assert r.stopped is True
    assert r.p_doc >= 0.95


def test_futility_does_not_give_up_on_slow_but_genuine_convergence():
    """The exact failure mode a real walkthrough demo exposed: a genuinely converging trajectory (moving the
    right direction every read, just not fast) was being killed by the OLD bare-point-estimate extrapolation,
    which treated a short window's noisy slope as certain. Moderate (not extreme) separation, deliberately
    slow to converge -- if this still gets marked futile, the fix regressed."""
    rng = np.random.default_rng(4)
    pool = _pool(rng, 400, 10, mu_m=-0.8, sd_m=0.3, mu_x=0.8, sd_x=0.3)
    ep = _episode(pool)
    model = {0: FakeModel(-0.8, 0.3, 0.8, 0.3)}
    sl = np.arange(pool.n_slices)
    r = run_episode(ep, model, sl, "active", tau=0.95, nmax=24, seed=1, futility_window=4, futility_margin=0.05)
    assert r is not None
    assert r.futile is False


def test_futility_never_fires_before_two_windows_of_reads():
    rng = np.random.default_rng(3)
    pool = _pool(rng, 200, 10, mu_m=-0.5, sd_m=0.2, mu_x=0.8, sd_x=0.2, noise_only=True)
    ep = _episode(pool)
    model = {0: FakeModel(-0.5, 0.2, 0.8, 0.2)}
    sl = np.arange(pool.n_slices)
    r = run_episode(ep, model, sl, "active", tau=0.95, nmax=24, seed=0, futility_window=6, futility_margin=0.05)
    assert r is not None
    assert r.n_read >= 12 or r.stopped   # can't fire before 2*window=12 reads unless it genuinely converged first
