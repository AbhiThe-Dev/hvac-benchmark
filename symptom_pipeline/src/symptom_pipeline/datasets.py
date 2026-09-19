"""Dataset assembly: causal experiment outputs -> labeled, split, versioned
training/evaluation records.

The record type and grouped-split logic here are real and independently
testable today; only the upstream data source
(`simulation.run_single_intervention_experiment`) is not implemented yet
(see `simulation.py`). Building splitting/labeling against real
`DatasetRecord`s is future work once `simulation.py` exists, but the split
invariants below (grouped by lineage, no cross-split report-variant leakage)
are exactly the design doc's required acceptance checks, so they are worth
having -- and enforced by tests -- before any data exists to run them on.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .contracts import DiscrepancyEvent, DiscrepancyLabel, SymptomReport


@dataclass(frozen=True)
class DatasetRecord:
    event: DiscrepancyEvent
    report: SymptomReport
    labels: tuple[DiscrepancyLabel, ...]
    # Groups related archetype configurations that share geometry or
    # construction lineage -- ten archetypes do not establish ten
    # independent real-building samples (design doc section 4).
    building_lineage_id: str
    split: str  # "train" | "val" | "test" | "architecture_holdout"


def group_split(
    lineage_ids: list[str],
    seed: int,
    train_frac: float = 0.6,
    val_frac: float = 0.2,
) -> dict[str, str]:
    """Grouped split by independent building/model lineage -- never by
    individual event or report -- so every report variant of one physical
    event, and every archetype configuration sharing lineage, lands in the
    same split. `train_frac`/`val_frac` are fractions of *lineages*, not of
    records; remaining lineages go to "test".
    """
    unique = sorted(set(lineage_ids))
    if not unique:
        return {}
    rng = np.random.RandomState(seed)
    order = rng.permutation(len(unique))
    n_train = max(1, int(round(len(unique) * train_frac)))
    n_val = max(1, int(round(len(unique) * val_frac))) if len(unique) > 2 else 0
    assignment: dict[str, str] = {}
    for rank, idx in enumerate(order):
        lineage = unique[idx]
        if rank < n_train:
            assignment[lineage] = "train"
        elif rank < n_train + n_val:
            assignment[lineage] = "val"
        else:
            assignment[lineage] = "test"
    return assignment


def assert_no_split_leakage(records: list[DatasetRecord]) -> None:
    """Report variants of the same physical event must never cross split
    boundaries (design doc, required acceptance check). Raises
    `AssertionError` naming the offending event on the first violation.
    """
    split_by_event: dict[str, str] = {}
    for r in records:
        prev = split_by_event.get(r.event.event_id)
        if prev is not None and prev != r.split:
            raise AssertionError(f"event {r.event.event_id!r} appears in both split {prev!r} and {r.split!r}")
        split_by_event[r.event.event_id] = r.split


def assert_no_lineage_leakage(records: list[DatasetRecord]) -> None:
    """A building lineage must never appear in more than one split --
    the stronger, lineage-level version of the same acceptance check."""
    split_by_lineage: dict[str, str] = {}
    for r in records:
        prev = split_by_lineage.get(r.building_lineage_id)
        if prev is not None and prev != r.split:
            raise AssertionError(
                f"lineage {r.building_lineage_id!r} appears in both split {prev!r} and {r.split!r}"
            )
        split_by_lineage[r.building_lineage_id] = r.split
