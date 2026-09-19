import pytest

from symptom_pipeline.contracts import CorruptionKind, DiscrepancyEvent, DiscrepancyLabel, StructuredAnswers, SymptomReport
from symptom_pipeline.contracts import AirflowAnswer, Onset, OperatingContext, Persistence, ProblemDirection, SupplyAirFeel
from symptom_pipeline.datasets import DatasetRecord, assert_no_lineage_leakage, assert_no_split_leakage, group_split


def _answers() -> StructuredAnswers:
    return StructuredAnswers(
        reported_locations=("Zone_0",),
        direction=ProblemDirection.TOO_HOT,
        airflow=AirflowAnswer.WEAK,
        supply_air_feel=SupplyAirFeel.WARM,
        persistence=Persistence.CONSTANT_WHILE_OCCUPIED,
        onset=Onset.SEVERAL_DAYS,
        other_spaces_checked=True,
        other_spaces_affected=(),
        operating_context=OperatingContext.COOLING,
        outside_conditions_unusual=False,
    )


def _record(event_id: str, lineage: str, split: str, reporting_error_seed=None) -> DatasetRecord:
    event = DiscrepancyEvent(event_id, CorruptionKind.MISSING, (("A", "B"),), "B")
    report = SymptomReport(f"{event_id}-report", "bldg", _answers(), reporting_error_seed=reporting_error_seed)
    label = DiscrepancyLabel("A", "B", "feeds", True, event_id)
    return DatasetRecord(event, report, (label,), lineage, split)


def test_group_split_is_deterministic():
    lineages = [f"lineage_{i}" for i in range(10)]
    a = group_split(lineages, seed=1)
    b = group_split(lineages, seed=1)
    assert a == b


def test_group_split_respects_fractions_roughly():
    lineages = [f"lineage_{i}" for i in range(10)]
    assignment = group_split(lineages, seed=1, train_frac=0.6, val_frac=0.2)
    counts = {"train": 0, "val": 0, "test": 0}
    for split in assignment.values():
        counts[split] += 1
    assert counts["train"] == 6
    assert counts["val"] == 2
    assert counts["test"] == 2


def test_assert_no_split_leakage_passes_when_consistent():
    records = [_record("evt-1", "lineage_a", "train"), _record("evt-1", "lineage_a", "train", reporting_error_seed=1)]
    assert_no_split_leakage(records)  # should not raise


def test_assert_no_split_leakage_catches_a_variant_crossing_splits():
    records = [_record("evt-1", "lineage_a", "train"), _record("evt-1", "lineage_a", "val", reporting_error_seed=1)]
    with pytest.raises(AssertionError):
        assert_no_split_leakage(records)


def test_assert_no_lineage_leakage_catches_a_lineage_split_across_two_splits():
    records = [_record("evt-1", "lineage_a", "train"), _record("evt-2", "lineage_a", "test")]
    with pytest.raises(AssertionError):
        assert_no_lineage_leakage(records)
