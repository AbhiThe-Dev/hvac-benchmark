"""What remains genuinely unimplemented (or deliberately out of scope) in
`simulation.py`, after the reconciliation logic and the `reassign_coil`
causal-experiment path were implemented.

`reconcile_realized_topology` no longer raises `NotImplementedError` --
see `tests/test_reconciliation.py`. `run_single_intervention_experiment`
is implemented for `rewire_kind="reassign_coil"` -- see
`tests/test_simulation_physics.py` (physics-marked, runs real OpenStudio/
EnergyPlus). What's tested here is the part that is STILL, deliberately,
not attempted: every other `rewire_kind`, rejected explicitly via
`UnsupportedInterventionError` rather than a bare `NotImplementedError` --
see `simulation.py`'s "KNOWN LIMITATIONS" docstring section for why each
one destroys real equipment on every one of the 10 current archetypes.

These run without OpenStudio installed at all: `run_single_intervention_
experiment` checks `rewire_kind` before importing `physics_pipeline` or
`openstudio`, precisely so this rejection path stays testable in the
default (non-`physics`) environment.
"""

import pytest

from symptom_pipeline.simulation import (
    OUT_OF_SCOPE_REWIRE_KINDS,
    SUPPORTED_REWIRE_KINDS,
    SingleInterventionSpec,
    UnsupportedInterventionError,
    run_single_intervention_experiment,
)


def test_only_reassign_coil_is_supported_in_this_pass():
    """Documents the actual v1 scope in a way that fails loudly if someone
    widens `SUPPORTED_REWIRE_KINDS` without updating this test (and,
    ideally, without re-running the reversal/verification checks a new
    kind would need)."""
    assert SUPPORTED_REWIRE_KINDS == frozenset({"reassign_coil"})


@pytest.mark.parametrize(
    "rewire_kind",
    [
        "remove_zone_service",
        "remove_coil_service",
        "reassign_terminal",
        "add_extra_service",
        "set_ahu_direct_service",
        "clone_terminal_for_zone",
    ],
)
def test_zone_destructive_kinds_are_explicitly_rejected(rewire_kind):
    assert rewire_kind in OUT_OF_SCOPE_REWIRE_KINDS  # every case above must have a documented reason
    spec = SingleInterventionSpec(building_id="sys07_vav_reheat", zone_id="unused", rewire_kind=rewire_kind)
    with pytest.raises(UnsupportedInterventionError) as excinfo:
        run_single_intervention_experiment(spec)
    assert excinfo.value.rewire_kind == rewire_kind
    assert excinfo.value.reason == OUT_OF_SCOPE_REWIRE_KINDS[rewire_kind]


def test_unrecognized_rewire_kind_is_rejected():
    spec = SingleInterventionSpec(building_id="sys07_vav_reheat", zone_id="unused", rewire_kind="not_a_real_function")
    with pytest.raises(UnsupportedInterventionError):
        run_single_intervention_experiment(spec)


def test_reassign_coil_requires_coil_and_pump_ids():
    spec = SingleInterventionSpec(building_id="sys07_vav_reheat", zone_id="unused", rewire_kind="reassign_coil")
    with pytest.raises(ValueError):
        run_single_intervention_experiment(spec)
