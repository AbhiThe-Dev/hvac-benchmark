"""Guards for the per-building system-ID module (PREREGISTRATION_DR.md Addendum 2)."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.dr import sysid as SID  # noqa: E402


class FakeModel:
    """Minimal ChannelModel stand-in: params(ctx) is a fixed (mu_M, sd_M, mu_X, sd_X, pinfo), plus extra attrs
    a real ChannelModel carries that engine.py reads directly (fit/kappa/rho/omega/rho_s)."""

    def __init__(self, mu_m=0.5, sd_m=0.2, mu_x=1.0, sd_x=0.3):
        self.mu_m, self.sd_m, self.mu_x, self.sd_x = mu_m, sd_m, mu_x, sd_x
        self.fit = {"M": object(), "X": object()}
        self.kappa = None
        self.rho = 0.0
        self.omega = 0.0
        self.rho_s = 0.0

    def params(self, ctx):
        n = len(ctx)
        return [np.full(n, self.mu_m), np.full(n, self.sd_m), np.full(n, self.mu_x), np.full(n, self.sd_x), np.full(n, 0.5)]


class FakeSlotPool:
    def __init__(self, E, truth):
        self.members = list(range(E.shape[-1]))
        self.owners = list(range(E.shape[-2]))
        self.truth = truth
        self.E = E


class FakePool:
    def __init__(self, slots, n_slices):
        self.slots = slots
        self.ctx = np.zeros((n_slices, 3))


def test_zero_bias_is_a_pure_passthrough():
    m = FakeModel()
    wrapped = SID.BiasAdaptedModel(m, 0.0)
    ctx = np.zeros((4, 3))
    # bias 0.0 goes through adapt_models' "== 0.0 -> return original" path; params() itself must also be identity
    out = wrapped.params(ctx)
    ref = m.params(ctx)
    assert np.allclose(out[0], ref[0]) and np.allclose(out[2], ref[2])


def test_nonzero_bias_shifts_both_class_means_only():
    m = FakeModel(mu_m=0.5, sd_m=0.2, mu_x=1.0, sd_x=0.3)
    wrapped = SID.BiasAdaptedModel(m, 0.7)
    ctx = np.zeros((3, 3))
    mM, sM, mX, sX, pinfo = wrapped.params(ctx)
    assert np.allclose(mM, 1.2) and np.allclose(mX, 1.7)
    assert np.allclose(sM, 0.2) and np.allclose(sX, 0.3)  # sd/pinfo untouched


def test_wrapper_delegates_attributes_engine_reads_directly():
    m = FakeModel()
    m.rho, m.omega, m.rho_s, m.kappa = 0.4, 0.1, 0.2, 5.0
    w = SID.BiasAdaptedModel(m, 0.3)
    assert w.fit is m.fit and w.rho == 0.4 and w.omega == 0.1 and w.rho_s == 0.2 and w.kappa == 5.0


def test_bias_estimate_recovers_a_known_offset():
    rng = np.random.default_rng(0)
    n_slices, n_mem = 200, 6
    truth = np.arange(n_mem)
    E = np.full((n_slices, 1, n_mem, n_mem), np.nan)
    mu_m, true_offset = -0.5, 0.6   # in tf()-space: tf(e) = log(e + 0.05)
    base_e = np.exp(mu_m + true_offset) - 0.05
    for m in range(n_mem):
        E[:, 0, m, m] = base_e * np.exp(rng.normal(0, 0.02, n_slices))  # small multiplicative noise, tf(base_e) stays ~mu_m+true_offset
    sp = FakeSlotPool(E, truth)
    pool = FakePool({"vav_zone": sp}, n_slices)
    model = FakeModel(mu_m=mu_m, sd_m=0.2)
    bias, n = SID.estimate_bias(pool, "vav_zone", 0, model, exclude_member=0)
    assert n >= SID.MIN_N
    # shrunk toward 0 by n/(n+PRIOR_N), so expect a bit less than the true offset, same sign, not near 0
    assert 0.3 < bias < true_offset


def test_excluded_member_never_contributes():
    rng = np.random.default_rng(1)
    n_slices, n_mem = 100, 4
    truth = np.arange(n_mem)
    E = np.full((n_slices, 1, n_mem, n_mem), np.nan)
    mu_m = -0.5
    base_e = np.exp(mu_m) - 0.05  # tf(base_e) == mu_m, so a well-behaved member contributes ~0 residual
    for m in range(n_mem):
        E[:, 0, m, m] = base_e * np.exp(rng.normal(0, 0.01, n_slices))
    E[:, 0, 3, 3] = 5000.0  # member 3 is a wild outlier (tf() far from mu_m); if excluded, must not move the estimate
    sp = FakeSlotPool(E, truth)
    pool = FakePool({"vav_zone": sp}, n_slices)
    model = FakeModel(mu_m=mu_m, sd_m=0.2)
    bias_excl, n_excl = SID.estimate_bias(pool, "vav_zone", 0, model, exclude_member=3, min_n=10)
    assert abs(bias_excl) < 0.05


def test_too_few_residuals_falls_back_to_zero():
    E = np.full((5, 1, 2, 2), np.nan)
    E[:, 0, 0, 0] = 0.5
    sp = FakeSlotPool(E, np.array([0, -1]))
    pool = FakePool({"vav_zone": sp}, 5)
    model = FakeModel(mu_m=0.5, sd_m=0.2)
    bias, n = SID.estimate_bias(pool, "vav_zone", 0, model, exclude_member=None, min_n=20)
    assert bias == 0.0 and n < 20


def test_adapt_models_is_deterministic_and_covers_all_channels():
    rng = np.random.default_rng(2)
    n_slices, n_mem = 60, 5
    truth = np.arange(n_mem)
    E = np.full((n_slices, 2, n_mem, n_mem), np.nan)
    for k in range(2):
        for m in range(n_mem):
            E[:, k, m, m] = 0.5 + 0.3 * (k + 1) + rng.normal(0, 0.02, n_slices)
    sp = FakeSlotPool(E, truth)
    pool = FakePool({"vav_zone": sp}, n_slices)
    mods = {0: FakeModel(mu_m=0.5), 1: FakeModel(mu_m=0.5)}
    out1, diag1 = SID.adapt_models(pool, mods, "vav_zone")
    out2, diag2 = SID.adapt_models(pool, mods, "vav_zone")
    assert set(out1) == {0, 1}
    assert diag1[0] == diag2[0] and diag1[1] == diag2[1]
    assert diag1[1][0] > diag1[0][0]  # channel 1 had a bigger true offset baked in above
