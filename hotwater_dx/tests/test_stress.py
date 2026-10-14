import numpy as np

from hotwater_dx import measurement as M
from hotwater_dx import stress as S
from hotwater_dx.matrix import THRESHOLDS, build_world


def test_matched_spec_changes_nothing():
    sp = S.Spec("m")
    assert sp.overrides() is None and sp.sev_mult == 1.0 and sp.noise == 1.0


def test_shift_interpolates_between_nominal_and_shifted_ranges():
    half = S.Spec("h", shift=0.5).overrides()
    assert half["duty"][0] == (S.NOMINAL["duty"][0] + S.SHIFT["duty"][0]) / 2


def test_composite_dial_is_monotone():
    a, b = S.composite(0.25), S.composite(0.75)
    assert a.noise < b.noise and a.sev_mult > b.sev_mult and a.p_garbage < b.p_garbage and a.latent_p < b.latent_p


def test_noise_scale_hook_is_restored_and_scales_error():
    rng = np.random.default_rng(0)
    base = np.std([M.temp(120, "probe", 70, rng) for _ in range(3000)])
    M.NOISE["scale"] = 2.0
    try:
        big = np.std([M.temp(120, "probe", 70, rng) for _ in range(3000)])
    finally:
        M.NOISE["scale"] = 1.0
    assert 1.7 < big / base < 2.3 and M.NOISE["scale"] == 1.0


def test_overrides_actually_shift_the_world():
    saved = dict(THRESHOLDS)
    THRESHOLDS.update(MIN_APPLICABLE=8, GATE_MIN=8)
    try:
        m = build_world(n_theta=30, seed=2, causes=("crossover",))
        s = build_world(n_theta=30, seed=2, causes=("crossover",), overrides=S.Spec("s", shift=1.0).overrides())
        assert np.mean([d["ua_mult"] for d in s.design]) > np.mean([d["ua_mult"] for d in m.design])
    finally:
        THRESHOLDS.clear()
        THRESHOLDS.update(saved)


def test_frozen_hash_is_stable():
    assert S.frozen_hash() == S.frozen_hash() and len(S.frozen_hash()) == 64
