"""Guards for the meta-learned shrinkage grid search (PREREGISTRATION_DR.md Addendum 3)."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.dr import sysid_meta as SM  # noqa: E402


class FakeModel:
    def __init__(self, k=0, mu_m=0.0):
        self.k = k
        self.mu_m = mu_m

    def params(self, ctx):
        n = len(ctx)
        return [np.full(n, self.mu_m), np.full(n, 0.2), np.full(n, 1.0), np.full(n, 0.3), np.full(n, 0.5)]


class FakeSlotPool:
    def __init__(self, E, truth):
        self.members = list(range(E.shape[-1]))
        self.owners = list(range(E.shape[-2]))
        self.truth = truth
        self.E = E


class FakePool:
    def __init__(self, slots, n_slices):
        self.slots = slots
        self.n_slices = n_slices
        self.ctx = np.zeros((n_slices, 3))


def _building(true_bias, n_slices=100, n_mem=6, noise=0.05, seed=0):
    rng = np.random.default_rng(seed)
    truth = np.arange(n_mem)
    base_e = np.exp(true_bias) - 0.05
    E = np.full((n_slices, 1, n_mem, n_mem), np.nan)
    for m in range(n_mem):
        E[:, 0, m, m] = base_e * np.exp(rng.normal(0, noise, n_slices))
    return FakePool({"vav_zone": FakeSlotPool(E, truth)}, n_slices)


def test_trimmed_matches_manual_computation():
    x = np.array([1.0, 2.0, 3.0, 4.0, 100.0])
    m, n, se = SM._trimmed(x, trim=0.2)
    assert n == 5
    assert np.isclose(m, np.mean([2.0, 3.0, 4.0]))  # drop 1 from each tail


def test_build_examples_skips_thin_buildings():
    buildings = {"tiny": _building(0.3, n_slices=5, n_mem=1)}  # 5 residuals total: far below the min_n=20 floor
    mods = {"vav_zone": {0: FakeModel(k=0)}}
    ex = SM.build_examples(buildings, mods, fractions=(1.0,))
    assert ex == []


def test_build_examples_produces_one_row_per_building_slot_channel_fraction():
    buildings = {"b1": _building(0.3), "b2": _building(-0.2)}
    mods = {"vav_zone": {0: FakeModel(k=0)}}
    ex = SM.build_examples(buildings, mods, fractions=(0.5, 1.0))
    assert len(ex) == 2 * 2  # 2 buildings x 2 fractions (one slot, one channel)
    assert {e["building"] for e in ex} == {"b1", "b2"}


def test_fit_shrinkage_recovers_a_sane_tau_when_signal_is_clean():
    # many clean buildings with a real, low-noise offset: shrinkage should end up trusting the estimate (large tau not needed,
    # small-to-moderate tau is fine since n is large relative to any reasonable tau in the grid)
    buildings = {f"b{i}": _building(0.4, noise=0.03, seed=i) for i in range(12)}
    mods = {"vav_zone": {0: FakeModel(k=0)}}
    ex = SM.build_examples(buildings, mods)
    fit = SM.fit_shrinkage(ex)
    assert fit["trim"] in SM.TRIMS and fit["tau"] in SM.TAUS
    assert fit["chosen_mse"] <= fit["hand_picked_mse"] + 1e-9  # the search must never do worse than the one grid point it also evaluated
    assert fit["n_buildings"] == 12


def test_fit_shrinkage_is_deterministic():
    buildings = {f"b{i}": _building(0.4 if i % 2 else -0.4, seed=i) for i in range(10)}
    mods = {"vav_zone": {0: FakeModel(k=0)}}
    ex1 = SM.build_examples(buildings, mods)
    ex2 = SM.build_examples(buildings, mods)
    f1, f2 = SM.fit_shrinkage(ex1), SM.fit_shrinkage(ex2)
    assert f1["trim"] == f2["trim"] and f1["tau"] == f2["tau"]


def test_fit_shrinkage_handles_pure_noise_by_shrinking_hard():
    # no real building-level offset at all (residuals are noise around 0): the fit should not prefer trusting the raw
    # estimate strongly for every building -- i.e. some meaningful shrinkage (tau not at the extreme "no shrinkage" end)
    buildings = {f"b{i}": _building(0.0, noise=0.5, seed=i) for i in range(15)}
    mods = {"vav_zone": {0: FakeModel(k=0)}}
    ex = SM.build_examples(buildings, mods)
    fit = SM.fit_shrinkage(ex)
    assert fit["tau"] > SM.TAUS[0]
