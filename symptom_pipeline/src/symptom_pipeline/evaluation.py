"""Ranking/report metrics and paired downstream comparisons across symptom
sources and troubleshooting policies.

Metric functions are pure and operate on plain ranked-pair/label records,
so they are unit-testable without a live model or a running benchmark
trial. `run_paired_comparison` is the one function here that drives
`benchmark_adapter.run_symptom_troubleshooting_trial` across the full
symptom-source x policy x noise x seed grid, preserving paired seeds and
noise draws (the same `seed` draws the same coupled noise stream in
`hvac_benchmark.experiment.noise` regardless of symptom source or policy).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .benchmark_adapter import SYMPTOM_SOURCES, run_symptom_troubleshooting_trial
from .contracts import PredictionRecord


def pair_recall_at_k(ranked_pairs: list[tuple[str, str]], true_pairs: frozenset, k: int) -> float:
    if not true_pairs:
        return float("nan")
    top_k = set(ranked_pairs[:k])
    return len(top_k & set(true_pairs)) / len(true_pairs)


def event_coverage_at_k(events: dict[str, frozenset], ranked_pairs: list[tuple[str, str]], k: int) -> float:
    """`events` maps event_id -> its true discordant pairs; `ranked_pairs`
    is a single shared ranking (e.g. one report's candidate ranking)."""
    with_discrepancy = {eid: pairs for eid, pairs in events.items() if pairs}
    if not with_discrepancy:
        return float("nan")
    top_k = set(ranked_pairs[:k])
    covered = sum(1 for pairs in with_discrepancy.values() if pairs.issubset(top_k))
    return covered / len(with_discrepancy)


def reciprocal_rank(ranked_pairs: list[tuple[str, str]], true_pairs: frozenset) -> float:
    for i, pair in enumerate(ranked_pairs, start=1):
        if pair in true_pairs:
            return 1.0 / i
    return 0.0


def mean_reciprocal_rank(per_query: list[tuple[list[tuple[str, str]], frozenset]]) -> float:
    values = [reciprocal_rank(ranked, true) for ranked, true in per_query if true]
    return sum(values) / len(values) if values else float("nan")


def brier_score(probabilities, labels) -> float:
    probs = np.asarray(probabilities, dtype=float)
    y = np.asarray(labels, dtype=float)
    return float(np.mean((probs - y) ** 2))


def reliability_curve(probabilities, labels, n_bins: int = 10) -> dict[str, list[float]]:
    probs = np.asarray(probabilities, dtype=float)
    y = np.asarray(labels, dtype=float)
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    bin_ids = np.clip(np.digitize(probs, bin_edges) - 1, 0, n_bins - 1)
    mean_predicted, empirical, counts = [], [], []
    for b in range(n_bins):
        mask = bin_ids == b
        counts.append(int(mask.sum()))
        if mask.sum() == 0:
            mean_predicted.append(float("nan"))
            empirical.append(float("nan"))
        else:
            mean_predicted.append(float(probs[mask].mean()))
            empirical.append(float(y[mask].mean()))
    return {"mean_predicted": mean_predicted, "empirical": empirical, "counts": counts}


# --------------------------------------------------------------------------
# Paired downstream comparison
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ComparisonRow:
    symptom_source: str
    policy: str
    noise_level: float
    seed: int
    n_tests_to_full_flag_first: int | None
    n_tests_to_full_flag_sustained: int | None
    n_false_positive_flags_final: int
    n_needless_retests_final: int
    n_tests_performed: int
    budget: int
    endpoint_expansion_size: int


def run_paired_comparison(
    tg,
    ontology,
    blueprint,
    config,
    policies: tuple[str, ...],
    noise_levels: tuple[float, ...],
    seeds: tuple[int, ...],
    prediction: PredictionRecord | None = None,
) -> list[ComparisonRow]:
    """Crosses every symptom source in `SYMPTOM_SOURCES` with every
    requested (policy, noise, seed): the primary comparison the design doc
    asks for ("does active selection retain an advantage with learned
    initialization?"). `symptom_naive` is skipped under `symptom_source
    ="none"`, matching `hvac_benchmark`'s own restriction (it is undefined
    without an active symptom mechanism).
    """
    rows: list[ComparisonRow] = []
    for symptom_source in SYMPTOM_SOURCES:
        source_prediction = prediction if symptom_source == "learned" else None
        for policy in policies:
            if policy == "symptom_naive" and symptom_source == "none":
                continue
            for noise in noise_levels:
                for seed in seeds:
                    result = run_symptom_troubleshooting_trial(
                        tg,
                        ontology,
                        blueprint,
                        policy,
                        symptom_source,
                        noise,
                        seed,
                        config,
                        prediction=source_prediction,
                    )
                    last = result.trajectory[-1]
                    rows.append(
                        ComparisonRow(
                            symptom_source=symptom_source,
                            policy=policy,
                            noise_level=noise,
                            seed=seed,
                            n_tests_to_full_flag_first=result.n_tests_to_full_flag_first,
                            n_tests_to_full_flag_sustained=result.n_tests_to_full_flag_sustained,
                            n_false_positive_flags_final=last.n_false_positive_flags,
                            n_needless_retests_final=last.n_needless_retests,
                            n_tests_performed=result.n_tests_performed,
                            budget=result.budget,
                            endpoint_expansion_size=result.endpoint_expansion_size,
                        )
                    )
    return rows


def mean_tests_to_attainment(rows: list[ComparisonRow], field: str = "n_tests_to_full_flag_sustained") -> dict:
    """Never silently drops non-attaining trials from an average without
    also reporting how many were dropped (design doc: "Do not drop
    failures when averaging tests").
    """
    values = [getattr(r, field) for r in rows]
    attained = [v for v in values if v is not None]
    return {
        "n_total": len(values),
        "n_attained": len(attained),
        "non_attainment_rate": (1 - len(attained) / len(values)) if values else float("nan"),
        "mean_among_attained": (sum(attained) / len(attained)) if attained else float("nan"),
    }
