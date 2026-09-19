"""Noise simulation: reproducibility and topology/edge/repeat coupling."""

from __future__ import annotations

from hvac_benchmark.experiment.noise import noise_draw, observe


def test_noise_draw_is_deterministic():
    a = noise_draw("bldg1", "s1", "t1", 0, seed=42)
    b = noise_draw("bldg1", "s1", "t1", 0, seed=42)
    assert a == b


def test_noise_draw_differs_by_key_component():
    base = noise_draw("bldg1", "s1", "t1", 0, seed=42)
    assert noise_draw("bldg2", "s1", "t1", 0, seed=42) != base
    assert noise_draw("bldg1", "s2", "t1", 0, seed=42) != base
    assert noise_draw("bldg1", "s1", "t2", 0, seed=42) != base
    assert noise_draw("bldg1", "s1", "t1", 1, seed=42) != base
    assert noise_draw("bldg1", "s1", "t1", 0, seed=43) != base


def test_draw_is_coupled_across_noise_levels_and_policies():
    """The same (topology, edge, repeat, seed) draw is reused regardless of
    which policy or noise level is asking -- so two policies testing the
    same edge at the same repeat number see the same underlying draw."""
    draw = noise_draw("b", "x", "y", 3, seed=7)
    # simulate "two policies" independently requesting the same test
    draw_again = noise_draw("b", "x", "y", 3, seed=7)
    assert draw == draw_again


def test_observe_noiseless_is_always_correct():
    assert observe(True, fp_rate=0.0, fn_rate=0.0, draw=0.5) is True
    assert observe(False, fp_rate=0.0, fn_rate=0.0, draw=0.999) is False


def test_observe_false_negative_boundary():
    # draw < fn_rate flips a true edge to observed-false
    assert observe(True, fp_rate=0.0, fn_rate=0.1, draw=0.05) is False
    assert observe(True, fp_rate=0.0, fn_rate=0.1, draw=0.15) is True


def test_observe_false_positive_boundary():
    assert observe(False, fp_rate=0.1, fn_rate=0.0, draw=0.05) is True
    assert observe(False, fp_rate=0.1, fn_rate=0.0, draw=0.15) is False


def test_draw_uniform_distribution_sanity():
    draws = [noise_draw("b", "x", "y", i, seed=0) for i in range(2000)]
    assert all(0.0 <= d < 1.0 for d in draws)
    mean = sum(draws) / len(draws)
    assert 0.45 < mean < 0.55
