from symptom_pipeline.calibration import (
    EventValidationRecord,
    event_covered_at_k,
    fit_calibrator,
    mean_event_coverage,
    select_suspect_prefix,
)


def test_fit_calibrator_is_monotonic_and_bounded():
    raw = [0.1, 0.2, 0.4, 0.6, 0.8, 0.9]
    labels = [0, 0, 0, 1, 1, 1]
    cal = fit_calibrator(raw, labels)
    calibrated = cal.apply(raw)
    assert all(0.0 <= p <= 1.0 for p in calibrated)
    assert list(calibrated) == sorted(calibrated)


def test_event_covered_at_k_requires_both_misattribution_pairs():
    record = EventValidationRecord(
        event_id="evt-1",
        ranked_pairs=(("A", "B"), ("C", "D"), ("E", "F")),
        true_pairs=frozenset({("A", "B"), ("C", "D")}),
        universe_size=10,
    )
    assert event_covered_at_k(record, k=1) is False  # only ("A","B") in top-1
    assert event_covered_at_k(record, k=2) is True


def test_event_with_no_discrepancy_is_trivially_covered_but_excluded_from_mean():
    clean = EventValidationRecord(event_id="evt-clean", ranked_pairs=(("A", "B"),), true_pairs=frozenset(), universe_size=5)
    assert event_covered_at_k(clean, k=0) is True
    assert mean_event_coverage([clean], k=0) != mean_event_coverage([clean], k=0)  # nan (no denominator)


def test_select_suspect_prefix_finds_smallest_k_meeting_target():
    records = [
        EventValidationRecord("e1", (("A", "B"), ("C", "D")), frozenset({("A", "B")}), universe_size=10),
        EventValidationRecord("e2", (("C", "D"), ("A", "B")), frozenset({("C", "D")}), universe_size=10),
    ]
    selection = select_suspect_prefix(records, target_coverage=1.0)
    assert selection.k == 1
    assert selection.mean_event_coverage == 1.0
    assert selection.met_target is True
    assert selection.universe_fraction == 1 / 10


def test_select_suspect_prefix_reports_failure_to_meet_target():
    records = [
        EventValidationRecord("e1", (("X", "Y"), ("A", "B")), frozenset({("A", "B")}), universe_size=2),
    ]
    selection = select_suspect_prefix(records, target_coverage=0.99)
    # k=2 (the full universe) covers, but target_coverage cannot be exceeded further --
    # this case DOES meet target at k=2; construct one that structurally cannot.
    assert selection.met_target is True

    unreachable = [
        EventValidationRecord("e2", (("X", "Y"),), frozenset({("A", "B")}), universe_size=1),
    ]
    selection2 = select_suspect_prefix(unreachable, target_coverage=0.5)
    assert selection2.met_target is False
    assert selection2.k == 1
