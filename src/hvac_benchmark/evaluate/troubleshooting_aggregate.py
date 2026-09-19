"""Aggregation for the troubleshooting-against-a-blueprint evaluation mode.

Mirrors the within-topology-only aggregation discipline of
`evaluate/aggregate.py` (never pools across topologies) but summarizes
troubleshooting-specific metrics (tests-to-full-flag, false-positive rate,
needless retests) instead of precision/recall.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..experiment.troubleshooting_runner import TroubleshootingTrialResult
from .aggregate import ValueSummary, summarize


@dataclass
class TroubleshootingGroupSummary:
    building_id: str
    policy: str
    symptom_mode: bool
    noise_level: float
    n_trials: int
    tests_to_full_flag_first: ValueSummary
    first_attainment_rate: float
    tests_to_full_flag_sustained: ValueSummary
    sustained_attainment_rate: float
    final_false_positive_rate: ValueSummary
    final_needless_retests: ValueSummary


def summarize_troubleshooting_group(results: list[TroubleshootingTrialResult]) -> TroubleshootingGroupSummary:
    assert results, "cannot summarize an empty group"
    r0 = results[0]
    n = len(results)

    first_vals = [r.n_tests_to_full_flag_first for r in results if r.n_tests_to_full_flag_first is not None]
    sustained_vals = [
        r.n_tests_to_full_flag_sustained for r in results if r.n_tests_to_full_flag_sustained is not None
    ]

    fp_rates = []
    for r in results:
        n_correct_claimed = r.n_candidates - r.n_discordant_candidates
        final = r.trajectory[-1]
        fp_rates.append(final.n_false_positive_flags / n_correct_claimed if n_correct_claimed > 0 else float("nan"))

    needless = [float(r.trajectory[-1].n_needless_retests) for r in results]

    return TroubleshootingGroupSummary(
        building_id=r0.building_id,
        policy=r0.policy,
        symptom_mode=r0.symptom_mode,
        noise_level=r0.noise_level,
        n_trials=n,
        tests_to_full_flag_first=summarize([float(v) for v in first_vals]),
        first_attainment_rate=len(first_vals) / n,
        tests_to_full_flag_sustained=summarize([float(v) for v in sustained_vals]),
        sustained_attainment_rate=len(sustained_vals) / n,
        final_false_positive_rate=summarize(fp_rates),
        final_needless_retests=summarize(needless),
    )
