"""Required acceptance check (design doc section 3, "Bayesian handoff"):
`symptom_pipeline.benchmark_adapter.run_symptom_troubleshooting_trial` must
reproduce `hvac_benchmark.experiment.troubleshooting_runner
.run_troubleshooting_trial` bit-for-bit for `symptom_source="none"` versus
`symptom_mode=False`, and `symptom_source="oracle"` versus
`symptom_mode=True`, across every reference policy, noise level, and seed.
Only `symptom_source="learned"` is new behavior, and it must never be used
for real experiments until this test passes.
"""

from __future__ import annotations

import pytest
from hvac_benchmark.config import DEFAULT_CONFIG
from hvac_benchmark.experiment.troubleshooting_runner import (
    TROUBLESHOOTING_BLIND_POLICIES,
    TROUBLESHOOTING_SYMPTOM_POLICIES,
    run_troubleshooting_trial,
)

from symptom_pipeline.benchmark_adapter import run_symptom_troubleshooting_trial

from ._fixtures import forced_fabrication_blueprint, forced_removal_blueprint, make_tg

SEEDS = (0, 1, 7)
NOISE_LEVELS = (0.0, 0.05, 0.15)


def _upstream_trajectory_tuples(result) -> list[tuple]:
    return [(p.test_number, p.n_discordant_flagged, p.n_false_positive_flags, p.n_needless_retests) for p in result.trajectory]


_SHARED_FIELDS = (
    "building_id",
    "corruption_seed",
    "requested_severity",
    "actual_severity",
    "corruption_types",
    "policy",
    "noise_level",
    "seed",
    "n_candidates",
    "n_discordant_candidates",
    "budget",
    "n_tests_performed",
    "n_tests_to_full_flag_first",
    "n_tests_to_full_flag_sustained",
)


def _assert_matches(upstream_result, adapter_result) -> None:
    for f in _SHARED_FIELDS:
        assert getattr(upstream_result, f) == getattr(adapter_result, f), f"field {f!r} diverged"
    assert _upstream_trajectory_tuples(upstream_result) == _upstream_trajectory_tuples(adapter_result)


@pytest.mark.parametrize("blueprint_fn", [forced_removal_blueprint, forced_fabrication_blueprint])
@pytest.mark.parametrize("policy_name", TROUBLESHOOTING_BLIND_POLICIES)
@pytest.mark.parametrize("noise_level", NOISE_LEVELS)
@pytest.mark.parametrize("seed", SEEDS)
def test_none_source_matches_symptom_mode_false(ontology, blueprint_fn, policy_name, noise_level, seed):
    tg = make_tg()
    bp = blueprint_fn(tg)
    upstream = run_troubleshooting_trial(
        tg, ontology, bp, policy_name=policy_name, symptom_mode=False, noise_level=noise_level, seed=seed, config=DEFAULT_CONFIG
    )
    adapter = run_symptom_troubleshooting_trial(
        tg, ontology, bp, policy_name=policy_name, symptom_source="none", noise_level=noise_level, seed=seed, config=DEFAULT_CONFIG
    )
    _assert_matches(upstream, adapter)
    assert adapter.endpoint_expansion_size == 0


@pytest.mark.parametrize("blueprint_fn", [forced_removal_blueprint, forced_fabrication_blueprint])
@pytest.mark.parametrize("policy_name", TROUBLESHOOTING_SYMPTOM_POLICIES)
@pytest.mark.parametrize("noise_level", NOISE_LEVELS)
@pytest.mark.parametrize("seed", SEEDS)
def test_oracle_source_matches_symptom_mode_true(ontology, blueprint_fn, policy_name, noise_level, seed):
    tg = make_tg()
    bp = blueprint_fn(tg)
    upstream = run_troubleshooting_trial(
        tg, ontology, bp, policy_name=policy_name, symptom_mode=True, noise_level=noise_level, seed=seed, config=DEFAULT_CONFIG
    )
    adapter = run_symptom_troubleshooting_trial(
        tg, ontology, bp, policy_name=policy_name, symptom_source="oracle", noise_level=noise_level, seed=seed, config=DEFAULT_CONFIG
    )
    _assert_matches(upstream, adapter)


def test_learned_source_requires_prediction(ontology):
    tg = make_tg()
    bp = forced_removal_blueprint(tg)
    with pytest.raises(ValueError):
        run_symptom_troubleshooting_trial(
            tg, ontology, bp, policy_name="active", symptom_source="learned", noise_level=0.0, seed=0, config=DEFAULT_CONFIG
        )


def test_unknown_symptom_source_rejected(ontology):
    tg = make_tg()
    bp = forced_removal_blueprint(tg)
    with pytest.raises(ValueError):
        run_symptom_troubleshooting_trial(
            tg, ontology, bp, policy_name="active", symptom_source="bogus", noise_level=0.0, seed=0, config=DEFAULT_CONFIG
        )


def test_fixture_matches_upstream_shape():
    """Guards against `_fixtures.py` silently drifting from the upstream
    fixture it duplicates: same node/edge counts as
    `tests/test_troubleshooting_runner.py::make_tg` at the repo root."""
    tg = make_tg()
    assert set(tg.nodes()) == {"AHU", "VAV_0", "Zone_0", "VAV_1", "Zone_1"}
    assert tg.edges_by_relation["feeds"] == {("AHU", "VAV_0"), ("VAV_0", "Zone_0"), ("AHU", "VAV_1"), ("VAV_1", "Zone_1")}
