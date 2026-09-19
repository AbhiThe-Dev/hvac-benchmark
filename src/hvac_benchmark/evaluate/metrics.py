"""Precision / recall / F1 / calibration from a set of posterior beliefs and
ground-truth labels over the candidate set.

All candidates are always in scope, not just tested ones: an untested
candidate's current belief (prior, or posterior marginal derived from other
tests via structured coupling) still counts toward the reconstruction, so
metrics are well defined "from step zero" before any test has been run.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PointMetrics:
    precision: float
    recall: float
    f1: float
    brier: float
    n_predicted_positive: int
    n_true_positive_total: int


def compute_metrics(
    posteriors: dict[int, float], true_labels: dict[int, bool], threshold: float = 0.5
) -> PointMetrics:
    tp = fp = fn = 0
    brier_sum = 0.0
    n_true_total = sum(1 for v in true_labels.values() if v)

    for idx, p in posteriors.items():
        label = true_labels[idx]
        predicted = p > threshold
        if predicted and label:
            tp += 1
        elif predicted and not label:
            fp += 1
        elif not predicted and label:
            fn += 1
        brier_sum += (p - (1.0 if label else 0.0)) ** 2

    n_predicted_positive = tp + fp
    precision = tp / n_predicted_positive if n_predicted_positive > 0 else float("nan")
    recall = tp / n_true_total if n_true_total > 0 else float("nan")
    if precision != precision or recall != recall or (precision + recall) == 0:
        f1 = float("nan")
    else:
        f1 = 2 * precision * recall / (precision + recall)
    brier = brier_sum / len(posteriors) if posteriors else float("nan")

    return PointMetrics(
        precision=precision,
        recall=recall,
        f1=f1,
        brier=brier,
        n_predicted_positive=n_predicted_positive,
        n_true_positive_total=n_true_total,
    )
