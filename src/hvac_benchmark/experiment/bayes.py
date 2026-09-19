"""Exact Bernoulli Bayesian updates and binary-observation expected
information gain for the independent-edge model.

A candidate edge either exists or does not (a fixed latent Bernoulli(p)).
A "test" is a noisy binary channel with known false-positive/false-negative
rates. Everything here is exact (no sampling, no approximation) so it can be
validated against brute-force enumeration on tiny hand-built graphs.
"""

from __future__ import annotations

import math


def binary_entropy(p: float) -> float:
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))


def likelihood(observed: bool, true_state: bool, fp_rate: float, fn_rate: float) -> float:
    """P(observed | true_state)."""
    if true_state:
        return (1 - fn_rate) if observed else fn_rate
    return fp_rate if observed else (1 - fp_rate)


def update(prior: float, observed: bool, fp_rate: float, fn_rate: float) -> float:
    """Exact Bayesian posterior P(exists | observed) for one test."""
    l1 = likelihood(observed, True, fp_rate, fn_rate)
    l0 = likelihood(observed, False, fp_rate, fn_rate)
    numerator = prior * l1
    denominator = numerator + (1 - prior) * l0
    if denominator == 0.0:
        return prior
    return numerator / denominator


def update_sequence(prior: float, observations: list[bool], fp_rate: float, fn_rate: float) -> float:
    p = prior
    for obs in observations:
        p = update(p, obs, fp_rate, fn_rate)
    return p


def expected_information_gain(prior: float, fp_rate: float, fn_rate: float) -> float:
    """E[H(p) - H(p | observation)] for one more test of this edge."""
    h0 = binary_entropy(prior)
    p_obs_true = prior * (1 - fn_rate) + (1 - prior) * fp_rate
    p_obs_false = 1 - p_obs_true

    posterior_true = update(prior, True, fp_rate, fn_rate)
    posterior_false = update(prior, False, fp_rate, fn_rate)

    expected_remaining = p_obs_true * binary_entropy(posterior_true) + p_obs_false * binary_entropy(
        posterior_false
    )
    return h0 - expected_remaining
