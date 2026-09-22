"""Guards for the per-channel trust-weighted evidence mechanism (PREREGISTRATION_DR.md Addendum 8)."""
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.active import trust as T  # noqa: E402
from docmismatch.active.engine import Episode, run_episode  # noqa: E402
from docmismatch.active.measurement import ChannelValidity  # noqa: E402


class FakeModel:
    def __init__(self, mu_m=0.5, sd_m=0.2, mu_x=1.0, sd_x=0.3):
        self.mu_m, self.sd_m, self.mu_x, self.sd_x = mu_m, sd_m, mu_x, sd_x
        self.fit = {"M": SimpleNamespace(tau=0.05), "X": SimpleNamespace(tau=0.05)}
        self.kappa = None
        self.rho = 0.0
        self.omega = 0.0
        self.rho_s = 0.0

    def params(self, ctx):
        n = len(ctx)
        return [np.full(n, self.mu_m), np.full(n, self.sd_m), np.full(n, self.mu_x), np.full(n, self.sd_x), np.full(n, 0.5)]


# ---------------------------------------------------------------------------------------------- TrustWeightedModel
def test_weight_one_is_a_pure_passthrough():
    m = FakeModel(mu_m=0.5, sd_m=0.2, mu_x=1.0, sd_x=0.3)
    w = T.TrustWeightedModel(m, 1.0)
    ctx = np.zeros((4, 3))
    out = w.params(ctx)
    ref = m.params(ctx)
    assert np.allclose(out[0], ref[0]) and np.allclose(out[1], ref[1])
    assert np.allclose(out[2], ref[2]) and np.allclose(out[3], ref[3])


def test_low_weight_inflates_sd_by_the_correct_factor():
    m = FakeModel(mu_m=0.5, sd_m=0.2, mu_x=1.0, sd_x=0.3)
    w = T.TrustWeightedModel(m, 0.25)   # scale = 1/sqrt(0.25) = 2
    ctx = np.zeros((3, 3))
    mM, sM, mX, sX, pinfo = w.params(ctx)
    assert np.allclose(mM, 0.5) and np.allclose(mX, 1.0)   # means untouched
    assert np.allclose(sM, 0.4) and np.allclose(sX, 0.6)   # sds doubled


def test_weight_out_of_range_raises():
    m = FakeModel()
    with pytest.raises(ValueError):
        T.TrustWeightedModel(m, 0.0)
    with pytest.raises(ValueError):
        T.TrustWeightedModel(m, 1.5)


def test_wrapper_delegates_attributes_engine_reads_directly():
    m = FakeModel()
    m.rho, m.omega, m.rho_s, m.kappa = 0.4, 0.1, 0.2, 5.0
    w = T.TrustWeightedModel(m, 0.5)
    assert w.fit is m.fit and w.rho == 0.4 and w.omega == 0.1 and w.rho_s == 0.2 and w.kappa == 5.0


# ---------------------------------------------------------------------------------------------- trust_weight
def test_trust_weight_at_chance_is_zero():
    v = ChannelValidity("vav_zone", 0, False, 0.5, 0.4, 30, 1000, "ok")
    assert T.trust_weight(v) == 0.0


def test_trust_weight_scales_linearly_above_chance():
    v = ChannelValidity("vav_zone", 1, True, 0.75, 0.7, 30, 1000, "ok")
    assert T.trust_weight(v) == pytest.approx(0.5)


def test_trust_weight_at_perfect_accuracy_is_one():
    v = ChannelValidity("vav_zone", 1, True, 1.0, 0.95, 30, 1000, "ok")
    assert T.trust_weight(v) == 1.0


def test_trust_weight_below_chance_floors_at_zero():
    v = ChannelValidity("vav_zone", 2, False, 0.307, 0.25, 30, 1000, "below chance")
    assert T.trust_weight(v) == 0.0


def test_trust_weight_nan_point_estimate_floors():
    v = ChannelValidity("vav_zone", 0, False, np.nan, np.nan, 0, 0, "too little real evidence")
    assert T.trust_weight(v) == 0.0


# ---------------------------------------------------------------------------------------------- apply_trust_weights
def test_apply_trust_weights_drops_below_floor_wraps_above():
    mods = {0: FakeModel(), 1: FakeModel(), 2: FakeModel()}
    validity = {
        0: ChannelValidity("vav_zone", 0, False, 0.51, 0.50, 30, 1000, "ok"),     # weight 0.02, right at MIN_WEIGHT
        1: ChannelValidity("vav_zone", 1, True, 0.9, 0.85, 30, 1000, "ok"),       # weight 0.8, kept
        2: ChannelValidity("vav_zone", 2, False, 0.307, 0.25, 30, 1000, "bad"),   # weight 0, dropped
    }
    out = T.apply_trust_weights(mods, validity, min_weight=0.05)
    assert set(out) == {1}
    assert isinstance(out[1], T.TrustWeightedModel)
    assert out[1].weight == pytest.approx(0.8)


def test_apply_trust_weights_passes_through_unvalidated_channels():
    mods = {0: FakeModel()}
    out = T.apply_trust_weights(mods, {})
    assert out[0] is mods[0]


# ---------------------------------------------------------------------------------------------- behavioural, via run_episode
def _pool_two_channels(rng, n_slices=200, n_mem=8):
    """channel 0: strong real separation. channel 1: identical VALUES regardless of truth (genuinely uninformative)."""
    truth = np.arange(n_mem)
    E = np.full((n_slices, 2, n_mem, n_mem), np.nan)
    for s in range(n_slices):
        for m in range(n_mem):
            for o in range(n_mem):
                z0 = -2.0 if o == m else 2.0
                E[s, 0, o, m] = np.exp(z0 + rng.normal(0, 0.1)) - 0.05
                E[s, 1, o, m] = np.exp(0.25 + rng.normal(0, 0.01)) - 0.05   # no dependence on o==m at all
    from types import SimpleNamespace as NS

    class SP:
        def __init__(self):
            self.members = list(range(n_mem))
            self.owners = list(range(n_mem))
            self.truth = truth
            self.E = E
            self.owner_class = [("VAV",)] * n_mem
            self.owner_size = np.ones(n_mem)

    class Pool:
        def __init__(self):
            self.slots = {"vav_zone": SP()}
            self.ctx = np.zeros((n_slices, 3))

        @property
        def n_slices(self):
            return len(self.ctx)
    return Pool()


def test_low_trust_channel_is_selected_far_less_than_at_full_trust():
    rng = np.random.default_rng(0)
    pool = _pool_two_channels(rng)
    ep = Episode(pool, "vav_zone", 0, 0, 0, False, "ep|0", "g0", {})
    sl = np.arange(pool.n_slices)
    base_models = {0: FakeModel(-2.0, 0.15, 2.0, 0.15), 1: FakeModel(-2.0, 0.15, 2.0, 0.15)}   # ch1 modelled as if equally strong

    r_full = run_episode(ep, base_models, sl, "active", nmax=24, seed=0)
    frac_ch1_full = float((r_full.k_seq == 1).mean())

    weighted = dict(base_models)
    weighted[1] = T.TrustWeightedModel(base_models[1], 0.02)   # heavily distrust channel 1
    r_weighted = run_episode(ep, weighted, sl, "active", nmax=24, seed=0)
    frac_ch1_weighted = float((r_weighted.k_seq == 1).mean())

    assert frac_ch1_weighted < frac_ch1_full
    assert r_weighted.p_doc >= 0.95   # channel 0 alone still resolves it -- discounting ch1 doesn't break the answer
