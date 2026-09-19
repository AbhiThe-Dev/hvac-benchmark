"""Structured cardinality-belief checks: the O(m^2) DP path must match
brute-force 2^m enumeration exactly, and lambda=0 must reduce to the
independent-edge model."""

from __future__ import annotations

import random

import numpy as np
import pytest

from hvac_benchmark.experiment.bayes import expected_information_gain as indep_eig
from hvac_benchmark.experiment.structured import StructuredBelief, cardinality_dp, cardinality_weight


def enumeration_marginals(qs: tuple[float, ...], lam: float) -> np.ndarray:
    qs_arr = np.asarray(qs)
    m = len(qs_arr)
    idx = np.arange(2**m)
    bits = (idx[:, None] >> np.arange(m)[None, :]) & 1
    per_bit = np.where(bits == 1, qs_arr[None, :], 1 - qs_arr[None, :])
    unnorm = per_bit.prod(axis=1)
    k = bits.sum(axis=1)
    w = cardinality_weight(k, lam)
    unnorm = unnorm * w
    z = unnorm.sum()
    probs = unnorm / z
    return (bits * probs[:, None]).sum(axis=0)


@pytest.mark.parametrize("m", [1, 2, 3, 4, 5, 8])
@pytest.mark.parametrize("lam", [0.0, 0.5, 1.0, 2.0])
def test_joint_entropy_dp_matches_enumeration(m, lam):
    rng = random.Random(42 + m * 7 + int(lam * 100))
    qs = tuple(round(rng.uniform(0.03, 0.97), 4) for _ in range(m))
    belief = StructuredBelief(qs, lam=lam)
    assert belief.joint_entropy() == pytest.approx(belief.joint_entropy_by_enumeration(), abs=1e-8)


@pytest.mark.parametrize("m", [1, 2, 3, 5, 8])
@pytest.mark.parametrize("lam", [0.0, 0.5, 1.0, 2.0])
def test_marginals_match_enumeration(m, lam):
    rng = random.Random(m * 13 + int(lam * 1000))
    qs = tuple(round(rng.uniform(0.03, 0.97), 4) for _ in range(m))
    belief = StructuredBelief(qs, lam=lam)
    expected = enumeration_marginals(qs, lam)
    np.testing.assert_allclose(belief.marginals(), expected, atol=1e-8)


def test_lambda_zero_marginals_equal_independent_priors():
    qs = (0.2, 0.5, 0.8, 0.05, 0.95)
    belief = StructuredBelief(qs, lam=0.0)
    np.testing.assert_allclose(belief.marginals(), np.asarray(qs), atol=1e-10)


def test_lambda_zero_eig_equals_independent_eig():
    qs = (0.15, 0.4, 0.65, 0.9)
    belief = StructuredBelief(qs, lam=0.0)
    for i, q in enumerate(qs):
        assert belief.expected_information_gain(i, 0.05, 0.1) == pytest.approx(
            indep_eig(q, 0.05, 0.1), abs=1e-9
        )


def test_cardinality_dp_sums_to_one():
    qs = np.array([0.1, 0.4, 0.6, 0.9])
    dp = cardinality_dp(qs)
    assert dp.sum() == pytest.approx(1.0)
    assert len(dp) == len(qs) + 1


def test_empty_group_has_zero_entropy():
    belief = StructuredBelief((), lam=1.0)
    assert belief.joint_entropy() == 0.0
    assert len(belief.marginals()) == 0


def test_with_observation_updates_only_target_edge_q():
    belief = StructuredBelief((0.3, 0.6), lam=1.0)
    updated = belief.with_observation(0, True, 0.05, 0.05)
    assert updated.qs[1] == belief.qs[1]
    assert updated.qs[0] != belief.qs[0]


def test_enumeration_cap_is_enforced():
    belief = StructuredBelief(tuple([0.5] * 25), lam=1.0, enumeration_cap=20)
    with pytest.raises(ValueError):
        belief.joint_entropy_by_enumeration()
