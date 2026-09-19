"""Exact Bayesian update / expected-information-gain checks against
brute-force enumeration on tiny hand-built cases."""

from __future__ import annotations

import itertools

import pytest

from hvac_benchmark.experiment.bayes import (
    binary_entropy,
    expected_information_gain,
    likelihood,
    update,
    update_sequence,
)


def brute_force_posterior(prior: float, observed: bool, fp: float, fn: float) -> float:
    """Manually enumerate the two hidden states and renormalize."""
    joint_true = prior * likelihood(observed, True, fp, fn)
    joint_false = (1 - prior) * likelihood(observed, False, fp, fn)
    return joint_true / (joint_true + joint_false)


@pytest.mark.parametrize("prior", [0.1, 0.3, 0.5, 0.7, 0.9])
@pytest.mark.parametrize("fp,fn", [(0.0, 0.0), (0.05, 0.05), (0.15, 0.15), (0.2, 0.05)])
@pytest.mark.parametrize("observed", [True, False])
def test_update_matches_brute_force(prior, fp, fn, observed):
    assert update(prior, observed, fp, fn) == pytest.approx(brute_force_posterior(prior, observed, fp, fn))


def test_noiseless_update_is_certain():
    assert update(0.3, True, 0.0, 0.0) == pytest.approx(1.0)
    assert update(0.3, False, 0.0, 0.0) == pytest.approx(0.0)


def test_update_sequence_equals_chained_updates():
    prior = 0.4
    obs = [True, False, True, True]
    expected = prior
    for o in obs:
        expected = update(expected, o, 0.1, 0.1)
    assert update_sequence(prior, obs, 0.1, 0.1) == pytest.approx(expected)


def test_binary_entropy_extremes():
    assert binary_entropy(0.0) == 0.0
    assert binary_entropy(1.0) == 0.0
    assert binary_entropy(0.5) == pytest.approx(1.0)


def brute_force_eig(prior: float, fp: float, fn: float) -> float:
    """Full enumeration over (true_state, observation) pairs."""
    h0 = binary_entropy(prior)
    total_remaining = 0.0
    for observed in (True, False):
        p_obs = prior * likelihood(observed, True, fp, fn) + (1 - prior) * likelihood(observed, False, fp, fn)
        if p_obs > 0:
            post = brute_force_posterior(prior, observed, fp, fn)
            total_remaining += p_obs * binary_entropy(post)
    return h0 - total_remaining


@pytest.mark.parametrize("prior", [0.05, 0.2, 0.5, 0.8, 0.95])
@pytest.mark.parametrize("fp,fn", [(0.0, 0.0), (0.05, 0.05), (0.15, 0.15)])
def test_eig_matches_brute_force(prior, fp, fn):
    assert expected_information_gain(prior, fp, fn) == pytest.approx(brute_force_eig(prior, fp, fn), abs=1e-9)


def test_noiseless_eig_equals_prior_entropy():
    """A perfect test fully resolves the edge, so EIG = H(prior)."""
    for p in (0.1, 0.3, 0.5, 0.7, 0.9):
        assert expected_information_gain(p, 0.0, 0.0) == pytest.approx(binary_entropy(p))


def test_eig_is_nonnegative_and_symmetric_around_half():
    for p in (0.05, 0.2, 0.5, 0.8, 0.95):
        g = expected_information_gain(p, 0.1, 0.1)
        assert g >= -1e-12
    assert expected_information_gain(0.3, 0.1, 0.1) == pytest.approx(expected_information_gain(0.7, 0.1, 0.1))
