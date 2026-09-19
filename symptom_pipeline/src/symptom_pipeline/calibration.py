"""Probability calibration and suspect-prefix selection.

Two distinct jobs, kept in one module because the design doc's module table
groups them: (1) turn a model's raw score into a calibrated probability
(`Calibrator`), and (2) choose the smallest ranked prefix meeting the
v1 target -- 95% mean event coverage on validation data, frozen before test
evaluation (`select_suspect_prefix`).

This is explicitly NOT the Bayesian noise-rate calibration the design doc
warns against conflating (section 4, "Noise-rate calibration is a separate
experiment"): nothing in this module ever touches `fp_rate`/`fn_rate`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.isotonic import IsotonicRegression

CALIBRATION_VERSION = "1.0.0"


@dataclass
class Calibrator:
    isotonic: IsotonicRegression
    version: str = CALIBRATION_VERSION

    def apply(self, raw_scores) -> np.ndarray:
        return self.isotonic.predict(np.asarray(raw_scores, dtype=float))


def fit_calibrator(raw_scores, labels) -> Calibrator:
    """Fits on a held-out calibration split, never on the training split
    the raw model was fit on (isotonic regression overfits badly otherwise)."""
    iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    iso.fit(np.asarray(raw_scores, dtype=float), np.asarray(labels, dtype=int))
    return Calibrator(isotonic=iso)


# --------------------------------------------------------------------------
# Suspect-prefix selection
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class EventValidationRecord:
    """One validation event: its candidates ranked by calibrated
    probability (descending), the true discordant pair(s) for that event
    (both pairs, for a misattribution), and the size of its candidate
    universe (for reporting how much of the universe a prefix actually is).
    """

    event_id: str
    ranked_pairs: tuple[tuple[str, str], ...]
    true_pairs: frozenset[tuple[str, str]]
    universe_size: int


def event_covered_at_k(record: EventValidationRecord, k: int) -> bool:
    """An event is covered at k only if ALL its true discordant pairs are
    within the top k -- a misattribution with only one of its two discordant
    pairs surfaced does not count as covered.
    """
    if not record.true_pairs:
        return True
    top_k = set(record.ranked_pairs[:k])
    return record.true_pairs.issubset(top_k)


def mean_event_coverage(records: list[EventValidationRecord], k: int) -> float:
    """Mean coverage over events that actually have a discordant pair to
    find; an event with none (a topology-intact case) contributes nothing
    to this metric and should be reported separately.
    """
    with_discrepancy = [r for r in records if r.true_pairs]
    if not with_discrepancy:
        return float("nan")
    return sum(event_covered_at_k(r, k) for r in with_discrepancy) / len(with_discrepancy)


@dataclass(frozen=True)
class SuspectPrefixSelection:
    k: int
    mean_event_coverage: float
    target_coverage: float
    universe_fraction: float
    met_target: bool


def select_suspect_prefix(
    records: list[EventValidationRecord], target_coverage: float = 0.95
) -> SuspectPrefixSelection:
    """Smallest k meeting `target_coverage` on validation data. If no k up
    to the full candidate universe reaches the target, returns the full
    universe size with `met_target=False` -- callers must check
    `met_target` and `universe_fraction` and report, per the design doc,
    that the model provides little useful narrowing rather than silently
    accepting a near-universe prefix as a win.
    """
    if not records:
        raise ValueError("no validation events supplied")
    max_k = max(len(r.ranked_pairs) for r in records)
    best_k = max_k
    best_cov = mean_event_coverage(records, max_k)
    for k in range(1, max_k + 1):
        cov = mean_event_coverage(records, k)
        if cov >= target_coverage:
            best_k = k
            best_cov = cov
            break
    mean_universe = sum(r.universe_size for r in records) / len(records)
    return SuspectPrefixSelection(
        k=best_k,
        mean_event_coverage=best_cov,
        target_coverage=target_coverage,
        universe_fraction=(best_k / mean_universe) if mean_universe else float("nan"),
        met_target=best_cov >= target_coverage,
    )
