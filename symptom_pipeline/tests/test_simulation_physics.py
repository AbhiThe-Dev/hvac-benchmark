"""Real, OpenStudio/EnergyPlus-backed tests of `simulation
.run_single_intervention_experiment`. Slow (each test runs one or more real
EnergyPlus simulations, ~15-30s each) and requires the `physics` extra
(`uv sync --extra physics`) plus the `physics_pipeline` sibling checkout
with its vendored EnergyPlus binary -- excluded by default
(`-m "not physics"`; see pyproject.toml).

Covers the two required acceptance checks the design doc calls out before
any batch generation counts as validated:

1. The step-5 verification fires on a genuinely wrong case -- proven
   directly, without OpenStudio, in `test_intended_change_verification.py`
   (the underlying `verify_intended_change` function is the SAME one this
   module's real run also goes through, so that separate proof already
   covers the "can it fail" half; this file's job is proving the happy
   path is REAL, not asserted).
2. The reversal sanity check: re-running the same case with the
   intervention NOT applied must make the measured effect disappear (or
   materially shrink). Implemented here as an actual independent third
   model load + simulation, not a re-use of the intervention run's own
   baseline object -- so it is a genuine test of "no intervention", not a
   restatement of the same computation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from symptom_pipeline.contracts import CorruptionKind, OperatingContext
from symptom_pipeline.simulation import SingleInterventionSpec, run_single_intervention_experiment

pytestmark = pytest.mark.physics

OUT_DIR = Path(__file__).resolve().parents[1] / "output" / "test_runs"

# Coil Heating Water 3 (VAV Reheat terminal 2's reheat coil, serving Thermal
# Zone 7) moved from the hot-water pump onto the chilled-water pump --
# confirmed by direct inspection (see simulation.py's docstring and this
# package's CHANGELOG) to be the one archetype/coil pair with a genuinely
# different-medium alternate pump available.
SYS07_SPEC = SingleInterventionSpec(
    building_id="sys07_vav_reheat",
    zone_id="",
    rewire_kind="reassign_coil",
    coil_id="{03f4e7f6-b452-4d9e-b3c8-13f44ba6532c}",
    target_pump_id="{021fb487-0d27-4abb-99fa-ca3c39546934}",
    event_id="test_sys07_coil3_to_chw_pump",
)
TARGET_ZONE_ID = "{031e6acf-0ee5-4aae-a351-e3f43b69f2fe}"  # Thermal Zone 7


@pytest.fixture(scope="module")
def experiment_result():
    return run_single_intervention_experiment(SYS07_SPEC, out_dir=OUT_DIR)


def test_intervention_produces_a_correctly_labeled_misattribution_event(experiment_result):
    truth, observables, event = experiment_result

    assert event.corruption_kind == CorruptionKind.MISATTRIBUTED
    assert event.target_id == SYS07_SPEC.coil_id
    assert set(pair[1] for pair in event.discordant_pairs) == {SYS07_SPEC.coil_id}
    assert set(pair[0] for pair in event.discordant_pairs) == {
        "{4b203e68-03b3-4c78-a5f1-422e09becf05}",  # true (documented) hot-water pump
        SYS07_SPEC.target_pump_id,  # actual (realized) chilled-water pump
    }

    assert truth.changed_connection == (SYS07_SPEC.target_pump_id, SYS07_SPEC.coil_id, "feeds")
    assert truth.corruption_kind == CorruptionKind.MISATTRIBUTED
    assert observables.demand_mode == OperatingContext.HEATING


def test_effect_is_measured_across_all_zones_not_just_the_target(experiment_result):
    """Design doc: "Measure symptom effects across ALL relevant zones, not
    just the intervention target." sys07 has 10 zones; this building's
    architecture is one dedicated VAV+reheat-coil per zone off a shared AHU,
    so no large remote effect is physically expected on OTHER zones from one
    reheat coil going cold -- but the point is that this is MEASURED, not
    assumed, for every zone, and the target zone's own effect must be large.
    """
    _, observables, _ = experiment_result

    assert len(observables.per_node) == 10  # sys07 has 10 zones; all must be represented, not just the target

    by_zone = {z.node_id: z for z in observables.per_node}
    target = by_zone[TARGET_ZONE_ID]
    target_deviation = target.changed_mean_temp_c - target.baseline_mean_temp_c
    assert target_deviation < -2.0, f"expected the target zone to cool measurably, got {target_deviation:.2f}C"

    other_deviations = [
        abs(z.changed_mean_temp_c - z.baseline_mean_temp_c) for zid, z in by_zone.items() if zid != TARGET_ZONE_ID
    ]
    # Reported, not asserted-away: other zones may show some small coupling
    # through the shared AHU's return air, but none should approach the
    # target zone's own deviation magnitude.
    assert max(other_deviations) < abs(target_deviation) / 2


def test_reversal_sanity_check_effect_disappears_without_the_intervention(experiment_result):
    """The design doc's required acceptance check: re-run the same case
    with the intervention NOT applied and confirm the measured effect
    disappears or materially shrinks. Implemented as a genuinely
    independent third model load (not the intervention run's own baseline
    object) simulated over the identical window, compared against that
    SAME baseline run -- if reloading and re-simulating the untouched model
    shows anything but ~0 deviation, that would mean the measurement
    itself (not the intervention) is the source of the apparent effect.
    """
    from symptom_pipeline.simulation import _query_series, import_physics_pipeline

    import_physics_pipeline()
    import openstudio
    from physics_pipeline.buildings import ENERGYPLUS_BIN, ENERGYPLUS_IDD, WEATHER_FILE, get_building
    from physics_pipeline import simulate as sim_mod

    _, observables, _ = experiment_result
    by_zone = {z.node_id: z for z in observables.per_node}
    target = by_zone[TARGET_ZONE_ID]
    intervention_deviation = target.changed_mean_temp_c - target.baseline_mean_temp_c

    building = get_building(SYS07_SPEC.building_id)
    translator = openstudio.osversion.VersionTranslator()
    reversal_model = translator.loadModel(openstudio.path(str(building.osm_path))).get()
    sim_mod.set_scoped_output(reversal_model, 1, 1, 1, 3)
    ws = sim_mod.forward_translate(reversal_model)
    idf = OUT_DIR / "reversal_check.idf"
    sim_mod.save_workspace_as_idf(ws, idf)
    reversal_result = sim_mod.run_energyplus(idf, WEATHER_FILE, OUT_DIR / "reversal_check_run", ENERGYPLUS_BIN, ENERGYPLUS_IDD)
    assert reversal_result.success

    reversal_series = _query_series(reversal_result.output_dir / "eplusout.sql", "Zone Mean Air Temperature", "THERMAL ZONE 7")
    reversal_mean = sum(reversal_series) / len(reversal_series)
    reversal_deviation = reversal_mean - target.baseline_mean_temp_c

    print(f"\n--- reversal sanity check (Thermal Zone 7 mean air temp, degC) ---")
    print(f"baseline (documented, no intervention):        {target.baseline_mean_temp_c:.3f}")
    print(f"changed (reassign_coil applied):                {target.changed_mean_temp_c:.3f}  (deviation {intervention_deviation:+.3f})")
    print(f"reversal (independent reload, NOT applied):     {reversal_mean:.3f}  (deviation {reversal_deviation:+.3f})")

    assert abs(reversal_deviation) < 0.05, (
        f"reloading and re-simulating the UNCHANGED model should show ~0 deviation from its own baseline, "
        f"got {reversal_deviation:.4f}C -- this would indicate the measurement itself is noisy, not the intervention"
    )
    assert intervention_deviation < -2.0
    if reversal_deviation != 0:
        assert abs(intervention_deviation) > 20 * abs(reversal_deviation)
