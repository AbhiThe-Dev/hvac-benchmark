"""Proves step 5's hard-failure gate (`simulation.verify_intended_change`)
actually fires on a wrong case, not just passes on the happy path -- one of
this package's required acceptance checks.

Uses the REAL discordant-pair output measured from an actual
`rewire.reassign_coil` run on `baseline_sys07` (not synthetic data): moving
`Coil Heating Water 3` from the hot-water pump (`Pump Variable Speed 1`) to
the chilled-water pump (`Pump Variable Speed 2`) produced exactly
`{(hot_water_pump, coil), (chilled_water_pump, coil)}` as its
`reconcile_realized_topology` discordant-pair output (confirmed by direct
inspection while building `simulation.py`; also re-verified end to end by
the physics-marked test in `test_simulation_physics.py`). This test does
not need OpenStudio at all -- it exercises the verification function in
isolation against that real, hardcoded result.
"""

import pytest

from symptom_pipeline.simulation import IntendedChangeMismatchError, verify_intended_change

HOT_WATER_PUMP = "{4b203e68-03b3-4c78-a5f1-422e09becf05}"
CHILLED_WATER_PUMP = "{021fb487-0d27-4abb-99fa-ca3c39546934}"
TARGET_COIL = "{03f4e7f6-b452-4d9e-b3c8-13f44ba6532c}"

REAL_ACTUAL_DISCORDANT_PAIRS = frozenset(
    {
        (HOT_WATER_PUMP, TARGET_COIL),
        (CHILLED_WATER_PUMP, TARGET_COIL),
    }
)


def test_matching_expectation_passes_silently():
    verify_intended_change(REAL_ACTUAL_DISCORDANT_PAIRS, REAL_ACTUAL_DISCORDANT_PAIRS, warnings=[])


def test_wrong_expectation_missing_a_pair_is_a_hard_failure():
    """A caller who forgot the removed (old pump, coil) pair -- e.g. a bug
    that only tracked the addition -- must not pass silently."""
    wrong_expected = frozenset({(CHILLED_WATER_PUMP, TARGET_COIL)})
    with pytest.raises(IntendedChangeMismatchError) as excinfo:
        verify_intended_change(wrong_expected, REAL_ACTUAL_DISCORDANT_PAIRS, warnings=[])
    assert excinfo.value.expected == wrong_expected
    assert excinfo.value.actual == REAL_ACTUAL_DISCORDANT_PAIRS


def test_wrong_expectation_referencing_the_wrong_coil_is_a_hard_failure():
    """A caller who computed the expected change against the wrong coil
    entirely (e.g. a cross-event collision silently substituted a
    different target) must not pass silently either."""
    other_coil = "{ffffffff-ffff-ffff-ffff-ffffffffffff}"
    wrong_expected = frozenset({(HOT_WATER_PUMP, other_coil), (CHILLED_WATER_PUMP, other_coil)})
    with pytest.raises(IntendedChangeMismatchError):
        verify_intended_change(wrong_expected, REAL_ACTUAL_DISCORDANT_PAIRS, warnings=["some reconciliation note"])


def test_extra_unexpected_discordant_pair_is_also_a_hard_failure():
    """The actual diff containing MORE than intended (e.g. a collision that
    also disturbed a second coil) must fail just as hard as containing
    less."""
    actual_with_extra = REAL_ACTUAL_DISCORDANT_PAIRS | {("{some-other-pump}", "{some-other-coil}")}
    with pytest.raises(IntendedChangeMismatchError):
        verify_intended_change(REAL_ACTUAL_DISCORDANT_PAIRS, actual_with_extra, warnings=[])
