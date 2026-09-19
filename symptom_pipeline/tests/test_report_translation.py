import inspect

from symptom_pipeline import report_translation
from symptom_pipeline.contracts import (
    AirflowAnswer,
    OperatingContext,
    ProblemDirection,
    SimulatedObservables,
    SupplyAirFeel,
    ZoneObservableSeries,
)
from symptom_pipeline.report_translation import DEFAULT_THRESHOLDS, degrade_report, translate_clean


def _observables() -> SimulatedObservables:
    primary = ZoneObservableSeries(
        node_id="Zone_0",
        baseline_mean_temp_c=22.0,
        changed_mean_temp_c=26.5,  # +4.5C -> too_hot
        baseline_setpoint_c=22.0,
        changed_setpoint_c=22.0,
        baseline_supply_air_temp_c=13.0,
        changed_supply_air_temp_c=15.0,  # +2C -> warm
        baseline_airflow_frac_of_design=0.95,
        changed_airflow_frac_of_design=0.5,  # -> weak
    )
    remote = ZoneObservableSeries(
        node_id="Zone_1",
        baseline_mean_temp_c=22.0,
        changed_mean_temp_c=23.5,  # +1.5C -> counts as affected
        baseline_setpoint_c=22.0,
        changed_setpoint_c=22.0,
        baseline_supply_air_temp_c=13.0,
        changed_supply_air_temp_c=13.0,
        baseline_airflow_frac_of_design=0.95,
        changed_airflow_frac_of_design=0.95,
    )
    unaffected = ZoneObservableSeries(
        node_id="Zone_2",
        baseline_mean_temp_c=22.0,
        changed_mean_temp_c=22.1,
        baseline_setpoint_c=22.0,
        changed_setpoint_c=22.0,
        baseline_supply_air_temp_c=13.0,
        changed_supply_air_temp_c=13.0,
        baseline_airflow_frac_of_design=0.95,
        changed_airflow_frac_of_design=0.95,
    )
    return SimulatedObservables(
        event_id="evt-1",
        per_node=(primary, remote, unaffected),
        demand_mode=OperatingContext.COOLING,
        outside_air_temp_unusual=False,
        quality_ok=True,
    )


def test_no_translation_function_reads_intervention_truth():
    """Design doc invariant: fault identity must not directly determine a
    reported answer. Enforced structurally: no public function in this
    module may declare a parameter of type InterventionTruth."""
    for name, fn in inspect.getmembers(report_translation, inspect.isfunction):
        sig = inspect.signature(fn)
        for param in sig.parameters.values():
            assert "InterventionTruth" not in str(param.annotation), (
                f"{name} must not accept InterventionTruth: {param}"
            )


def test_translate_clean_derives_answers_from_observables():
    answers = translate_clean(_observables(), primary_node_id="Zone_0", thresholds=DEFAULT_THRESHOLDS)
    assert answers.direction == ProblemDirection.TOO_HOT
    assert answers.airflow == AirflowAnswer.WEAK
    assert answers.supply_air_feel == SupplyAirFeel.WARM
    assert answers.other_spaces_affected == ("Zone_1",)
    assert answers.operating_context == OperatingContext.COOLING


def test_translate_clean_respects_other_spaces_not_checked():
    answers = translate_clean(_observables(), primary_node_id="Zone_0", other_spaces_checked=False)
    assert answers.other_spaces_checked is False
    assert answers.other_spaces_affected == ()


def test_degrade_report_is_reproducible():
    clean = translate_clean(_observables(), primary_node_id="Zone_0")
    a = degrade_report(clean, event_id="evt-1", error_seed=42, error_level=0.4)
    b = degrade_report(clean, event_id="evt-1", error_seed=42, error_level=0.4)
    assert a == b


def test_degrade_report_zero_error_level_is_identity():
    clean = translate_clean(_observables(), primary_node_id="Zone_0")
    degraded = degrade_report(clean, event_id="evt-1", error_seed=42, error_level=0.0)
    assert degraded == clean
