"""Aggregate per-seed trial results within one topology into medians,
ranges, and attainment rates. Never pools across topologies into a single
number that would imply cross-building generalization -- aggregation here
is always within one (topology, relation, experiment, policy, noise, ...)
group, i.e. seed/noise variability *within* a topology.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config import BenchmarkConfig
from ..experiment.runner import TrialResult
from .thresholds import AttainmentResult, compute_attainment


@dataclass(frozen=True)
class ValueSummary:
    median: float | None
    lo: float | None
    hi: float | None
    n: int


def summarize(values: list[float]) -> ValueSummary:
    clean = sorted(v for v in values if v == v)  # drop NaN
    if not clean:
        return ValueSummary(None, None, None, 0)
    n = len(clean)
    mid = n // 2
    median = clean[mid] if n % 2 == 1 else (clean[mid - 1] + clean[mid]) / 2
    return ValueSummary(median=median, lo=clean[0], hi=clean[-1], n=n)


@dataclass
class GroupSummary:
    building_id: str
    relation: str
    experiment: str
    policy: str
    noise_level: float
    lam: float | None
    prior_kind: str
    n_seeds: int
    final_precision: ValueSummary
    final_recall: ValueSummary
    final_f1: ValueSummary
    final_brier: ValueSummary
    primary_first: ValueSummary
    primary_first_attainment_rate: float
    primary_sustained: ValueSummary
    primary_sustained_attainment_rate: float
    secondary_first: ValueSummary
    secondary_first_attainment_rate: float
    secondary_sustained: ValueSummary
    secondary_sustained_attainment_rate: float
    total_parent_count_violations: int


def summarize_group(results: list[TrialResult], config: BenchmarkConfig) -> GroupSummary:
    assert results, "cannot summarize an empty group"
    r0 = results[0]

    final_p = [r.trajectory[-1].precision for r in results]
    final_r = [r.trajectory[-1].recall for r in results]
    final_f1 = [r.trajectory[-1].f1 for r in results]
    final_brier = [r.trajectory[-1].brier for r in results]

    primary_attainments: list[AttainmentResult] = [
        compute_attainment(r.trajectory, config.primary_precision, config.primary_recall) for r in results
    ]
    secondary_attainments: list[AttainmentResult] = [
        compute_attainment(r.trajectory, config.secondary_precision, config.secondary_recall) for r in results
    ]

    primary_first_vals = [a.first_test for a in primary_attainments if a.first_test is not None]
    primary_sustained_vals = [a.sustained_test for a in primary_attainments if a.sustained_test is not None]
    secondary_first_vals = [a.first_test for a in secondary_attainments if a.first_test is not None]
    secondary_sustained_vals = [a.sustained_test for a in secondary_attainments if a.sustained_test is not None]

    n = len(results)
    return GroupSummary(
        building_id=r0.building_id,
        relation=r0.relation,
        experiment=r0.experiment,
        policy=r0.policy,
        noise_level=r0.noise_level,
        lam=r0.lam,
        prior_kind=r0.prior_kind,
        n_seeds=n,
        final_precision=summarize([float(v) for v in final_p]),
        final_recall=summarize([float(v) for v in final_r]),
        final_f1=summarize([float(v) for v in final_f1]),
        final_brier=summarize([float(v) for v in final_brier]),
        primary_first=summarize([float(v) for v in primary_first_vals]),
        primary_first_attainment_rate=len(primary_first_vals) / n,
        primary_sustained=summarize([float(v) for v in primary_sustained_vals]),
        primary_sustained_attainment_rate=len(primary_sustained_vals) / n,
        secondary_first=summarize([float(v) for v in secondary_first_vals]),
        secondary_first_attainment_rate=len(secondary_first_vals) / n,
        secondary_sustained=summarize([float(v) for v in secondary_sustained_vals]),
        secondary_sustained_attainment_rate=len(secondary_sustained_vals) / n,
        total_parent_count_violations=sum(r.true_parent_count_violations for r in results),
    )


@dataclass(frozen=True)
class PairedSaving:
    seed: int
    active_tests: int | None
    baseline_tests: int | None
    savings: int | None  # baseline - active, only when both attained


def paired_savings(
    active_results: list[TrialResult],
    baseline_results: list[TrialResult],
    config: BenchmarkConfig,
) -> list[PairedSaving]:
    active_by_seed = {r.seed: r for r in active_results}
    baseline_by_seed = {r.seed: r for r in baseline_results}
    out = []
    for seed in sorted(set(active_by_seed) & set(baseline_by_seed)):
        a = compute_attainment(active_by_seed[seed].trajectory, config.primary_precision, config.primary_recall)
        b = compute_attainment(baseline_by_seed[seed].trajectory, config.primary_precision, config.primary_recall)
        savings = (b.first_test - a.first_test) if (a.first_test is not None and b.first_test is not None) else None
        out.append(PairedSaving(seed=seed, active_tests=a.first_test, baseline_tests=b.first_test, savings=savings))
    return out
