"""Guards for the physical/manual verification action type (the "does it have to be sensor data" gap)."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.active import physical as P  # noqa: E402


# ---------------------------------------------------------------------------------------------- update_posterior
def test_yes_outcome_on_documented_owner_confirms_it():
    post = np.array([0.5, 0.3, 0.2])
    test = P.PhysicalTestType("t", 0.98, 0.02, 1.0, "d")
    out = P.update_posterior(post, 0, True, test)
    assert out[0] > post[0]
    assert np.isclose(out.sum(), 1.0)


def test_no_outcome_on_documented_owner_refutes_it():
    post = np.array([0.5, 0.3, 0.2])
    test = P.PhysicalTestType("t", 0.98, 0.02, 1.0, "d")
    out = P.update_posterior(post, 0, False, test)
    assert out[0] < post[0]


def test_yes_outcome_on_an_alternative_pulls_mass_away_from_documented():
    post = np.array([0.5, 0.3, 0.2])
    test = P.PhysicalTestType("t", 0.98, 0.02, 1.0, "d")
    out = P.update_posterior(post, 1, True, test)
    assert out[1] > post[1]
    assert out[0] < post[0]


def test_perfect_test_drives_posterior_to_a_vertex():
    post = np.array([0.4, 0.35, 0.25])
    perfect = P.PhysicalTestType("perfect", 1.0, 0.0, 1.0, "d")
    out = P.update_posterior(post, 1, True, perfect)
    assert np.isclose(out[1], 1.0)
    assert np.isclose(out[0], 0.0) and np.isclose(out[2], 0.0)


# ---------------------------------------------------------------------------------------------- physical_eig
def test_perfect_test_on_documented_owner_recovers_full_prior_entropy():
    post = np.array([0.5, 0.3, 0.2])
    perfect = P.PhysicalTestType("perfect", 1.0, 0.0, 1.0, "d")
    eig = P.physical_eig(post, 0, perfect)
    assert eig == pytest.approx(P._hbin(0.5), abs=1e-9)


def test_useless_test_has_zero_eig():
    post = np.array([0.5, 0.3, 0.2])
    useless = P.PhysicalTestType("useless", 0.5, 0.5, 1.0, "d")   # TPR == FPR: outcome uninformative
    eig = P.physical_eig(post, 0, useless)
    assert eig == pytest.approx(0.0, abs=1e-9)


def test_eig_is_nonnegative_across_a_grid_of_priors_and_targets():
    rng = np.random.default_rng(0)
    test = P.PhysicalTestType("t", 0.9, 0.1, 1.0, "d")
    for _ in range(20):
        h = rng.integers(2, 6)
        post = rng.dirichlet(np.ones(h))
        j = rng.integers(0, h)
        assert P.physical_eig(post, j, test) >= -1e-9


# ---------------------------------------------------------------------------------------------- best_physical_test
def test_best_physical_test_picks_higher_eig_per_cost():
    post = np.array([0.5, 0.5])
    hyps = [10, 20]
    cheap_ok = P.PhysicalTestType("cheap", 0.9, 0.1, 1.0, "d")
    expensive_better = P.PhysicalTestType("expensive", 0.99, 0.01, 100.0, "d")   # much better EIG, but not per-cost
    rec = P.best_physical_test(post, hyps, test_types=(cheap_ok, expensive_better))
    assert rec.test.name == "cheap"


def test_best_physical_test_returns_the_real_owner_id_not_a_position_index():
    post = np.array([0.2, 0.2, 0.6])
    hyps = [7, 42, 3]   # position 2 (owner id 3) has the most mass to confirm/refute
    rec = P.best_physical_test(post, hyps)
    assert rec.owner in hyps


def test_best_physical_test_none_for_empty_hypotheses():
    assert P.best_physical_test(np.array([]), []) is None
