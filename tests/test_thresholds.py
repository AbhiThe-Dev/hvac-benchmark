"""Threshold-attainment censoring: first vs. sustained, and explicit
non-attainment (never silently converted into an apparent success)."""

from __future__ import annotations

from hvac_benchmark.evaluate.thresholds import compute_attainment
from hvac_benchmark.experiment.runner import TrajectoryPoint


def pt(n, p, r):
    return TrajectoryPoint(test_number=n, precision=p, recall=r, f1=0.0, brier=0.0)


def test_first_attainment_is_earliest_crossing():
    traj = [pt(0, 0.5, 0.5), pt(1, 0.95, 0.95), pt(2, 0.95, 0.95)]
    result = compute_attainment(traj, 0.9, 0.9)
    assert result.first_test == 1
    assert result.attained


def test_never_attained_reports_none_not_a_fabricated_value():
    traj = [pt(0, 0.5, 0.5), pt(1, 0.6, 0.7), pt(2, 0.8, 0.85)]
    result = compute_attainment(traj, 0.9, 0.9)
    assert result.first_test is None
    assert not result.attained
    assert result.sustained_test is None
    assert not result.sustained


def test_sustained_requires_holding_through_the_end():
    """Crossing once but later dropping below threshold must not count as
    sustained, even though it counts as a first attainment."""
    traj = [pt(0, 0.5, 0.5), pt(1, 0.95, 0.95), pt(2, 0.5, 0.5), pt(3, 0.5, 0.5)]
    result = compute_attainment(traj, 0.9, 0.9)
    assert result.first_test == 1
    assert result.sustained_test is None


def test_sustained_finds_earliest_point_of_the_final_unbroken_run():
    traj = [pt(0, 0.5, 0.5), pt(1, 0.95, 0.95), pt(2, 0.5, 0.5), pt(3, 0.92, 0.92), pt(4, 0.93, 0.93)]
    result = compute_attainment(traj, 0.9, 0.9)
    assert result.first_test == 1
    assert result.sustained_test == 3


def test_nan_points_never_count_as_meeting_threshold():
    nan = float("nan")
    traj = [pt(0, nan, nan), pt(1, 0.95, 0.95)]
    result = compute_attainment(traj, 0.9, 0.9)
    assert result.first_test == 1


def test_empty_trajectory_is_not_attained():
    result = compute_attainment([], 0.9, 0.9)
    assert result.first_test is None
    assert result.sustained_test is None
