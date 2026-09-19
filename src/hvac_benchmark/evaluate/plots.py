"""Per-topology plots: recovery curves, threshold-cost distributions, and
paired savings. Every plot is scoped to one topology (or one synthetic
graph) -- seed/noise variability is shown as a spread *within* that
topology, never pooled across topologies into a band that would imply
cross-building generalization.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from ..config import BenchmarkConfig
from ..experiment.runner import TrialResult
from .aggregate import PairedSaving
from .thresholds import compute_attainment

POLICY_COLORS = {
    "active": "#1b9e77",
    "random": "#7570b3",
    "traversal": "#d95f02",
    "rule_based": "#e7298a",
    "frozen_initial": "#666666",
}


def plot_recovery_curves(
    results_by_policy: dict[str, list[TrialResult]], title: str, out_path: Path
) -> None:
    """Median recall vs. test number per policy, with a within-topology
    min-max band across seeds."""
    fig, ax = plt.subplots(figsize=(6, 4))
    for policy, results in results_by_policy.items():
        if not results:
            continue
        max_len = max(len(r.trajectory) for r in results)
        recalls = np.full((len(results), max_len), np.nan)
        for i, r in enumerate(results):
            for point in r.trajectory:
                recalls[i, point.test_number] = point.recall
        # forward-fill NaNs (trials that ended early keep their last value)
        for i in range(recalls.shape[0]):
            last = np.nan
            for j in range(recalls.shape[1]):
                if np.isnan(recalls[i, j]):
                    recalls[i, j] = last
                else:
                    last = recalls[i, j]
        median = np.nanmedian(recalls, axis=0)
        lo = np.nanmin(recalls, axis=0)
        hi = np.nanmax(recalls, axis=0)
        x = np.arange(max_len)
        color = POLICY_COLORS.get(policy, None)
        ax.plot(x, median, label=policy, color=color)
        ax.fill_between(x, lo, hi, alpha=0.15, color=color)
    ax.set_xlabel("tests performed")
    ax.set_ylabel("recall (within-topology seed range shaded)")
    ax.set_title(title)
    ax.legend(fontsize=8)
    ax.set_ylim(-0.02, 1.02)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def plot_threshold_cost_distribution(
    results_by_policy: dict[str, list[TrialResult]],
    precision_target: float,
    recall_target: float,
    title: str,
    out_path: Path,
) -> None:
    """Box-style distribution of tests-to-first-attainment per policy
    (within one topology); policies with 0 attaining seeds get an empty box
    and are annotated rather than silently omitted."""
    fig, ax = plt.subplots(figsize=(6, 4))
    labels = []
    data = []
    rates = []
    for policy, results in results_by_policy.items():
        vals = []
        for r in results:
            a = compute_attainment(r.trajectory, precision_target, recall_target)
            if a.first_test is not None:
                vals.append(a.first_test)
        labels.append(policy)
        data.append(vals if vals else [np.nan])
        rates.append(len(vals) / len(results) if results else 0.0)

    bp = ax.boxplot(data, tick_labels=labels, showmeans=True)
    for i, rate in enumerate(rates):
        ax.text(i + 1, ax.get_ylim()[1] * 0.02, f"{rate:.0%} attained", ha="center", fontsize=7, rotation=90)
    ax.set_ylabel(f"tests to first reach P>={precision_target:.0%}, R>={recall_target:.0%}")
    ax.set_title(title)
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def plot_paired_savings(savings: list[PairedSaving], title: str, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    seeds = [s.seed for s in savings]
    values = [s.savings if s.savings is not None else np.nan for s in savings]
    colors = ["#1b9e77" if (v == v and v >= 0) else ("#d95f02" if v == v else "#cccccc") for v in values]
    ax.bar(range(len(seeds)), [0 if v != v else v for v in values], color=colors)
    n_missing = sum(1 for v in values if v != v)
    ax.set_xlabel(f"seed (paired within topology; {n_missing} seed(s) without a valid comparison omitted from bars)")
    ax.set_ylabel("tests saved by active vs. baseline (+ = active needed fewer)")
    ax.set_title(title)
    ax.axhline(0, color="black", linewidth=0.8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
