"""First and sustained precision/recall threshold attainment, computed
after a trial's trajectory is complete -- never used to decide when a trial
stops (see `experiment/runner.py`, which runs to budget regardless).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..experiment.runner import TrajectoryPoint


@dataclass(frozen=True)
class AttainmentResult:
    first_test: int | None
    sustained_test: int | None

    @property
    def attained(self) -> bool:
        return self.first_test is not None

    @property
    def sustained(self) -> bool:
        return self.sustained_test is not None


def _meets(point: TrajectoryPoint, precision_target: float, recall_target: float) -> bool:
    return (
        point.precision == point.precision  # not NaN
        and point.recall == point.recall
        and point.precision >= precision_target
        and point.recall >= recall_target
    )


def compute_attainment(
    trajectory: list[TrajectoryPoint], precision_target: float, recall_target: float
) -> AttainmentResult:
    first_test = None
    for point in trajectory:
        if _meets(point, precision_target, recall_target):
            first_test = point.test_number
            break

    sustained_test = None
    if trajectory and _meets(trajectory[-1], precision_target, recall_target):
        sustained_test = trajectory[-1].test_number
        for point in reversed(trajectory[:-1]):
            if _meets(point, precision_target, recall_target):
                sustained_test = point.test_number
            else:
                break

    return AttainmentResult(first_test=first_test, sustained_test=sustained_test)
