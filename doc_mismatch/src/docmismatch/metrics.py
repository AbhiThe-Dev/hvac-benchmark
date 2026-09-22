from __future__ import annotations

import numpy as np


def auroc_pairs(y: np.ndarray, s: np.ndarray) -> tuple[float, float]:
    """(concordant pair credit, number of pos-neg pairs); ties count 1/2."""
    pos, neg = s[y == 1], s[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return 0.0, 0.0
    d = pos[:, None] - neg[None, :]
    return float((d > 0).sum() + 0.5 * (d == 0).sum()), float(len(pos) * len(neg))


def auroc(y, s) -> float:
    c, n = auroc_pairs(np.asarray(y), np.asarray(s))
    return c / n if n else float("nan")


def _average_precision(y: np.ndarray, s: np.ndarray, w: np.ndarray) -> float:
    """Step-wise AP over distinct score thresholds (ties are one threshold, so a constant
    score gives AP = prevalence rather than depending on array order)."""
    o = np.argsort(-s, kind="stable")
    s, y, w = s[o], y[o], w[o]
    tps, fps = np.cumsum(w * (y == 1)), np.cumsum(w * (y == 0))
    idx = np.r_[np.flatnonzero(np.diff(s)), len(s) - 1]
    tps, fps = tps[idx], fps[idx]
    precision = tps / (tps + fps)
    recall = tps / tps[-1]
    return float(np.sum(np.diff(np.r_[0.0, recall]) * precision))


def auprc(y, s) -> float:
    y, s = np.asarray(y), np.asarray(s)
    if y.sum() == 0:
        return float("nan")
    return _average_precision(y, s, np.ones(len(y)))


def f1_at(y, s, thr: float) -> float:
    y, s = np.asarray(y), np.asarray(s)
    pred = s >= thr
    tp = float((pred & (y == 1)).sum())
    fp = float((pred & (y == 0)).sum())
    fn = float((~pred & (y == 1)).sum())
    return 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0


def best_f1_threshold(y, s) -> float:
    y, s = np.asarray(y), np.asarray(s)
    cands = np.unique(s)
    if len(cands) > 200:
        cands = np.quantile(s, np.linspace(0, 1, 200))
    best, thr = -1.0, float(np.median(s))
    for c in cands:
        f = f1_at(y, s, c)
        if f > best:
            best, thr = f, float(c)
    return thr


def fpr_at(y, s, thr: float) -> float:
    y, s = np.asarray(y), np.asarray(s)
    neg = s[y == 0]
    return float((neg >= thr).mean()) if len(neg) else float("nan")


def auprc_balanced(y, s) -> float:
    """Average precision with negatives up-weighted so prevalence is 50% (chance = 0.5).
    Raw AUPRC is dominated by prevalence here (hard:clean is about 4:1)."""
    y, s = np.asarray(y), np.asarray(s)
    npos, nneg = float((y == 1).sum()), float((y == 0).sum())
    if npos == 0 or nneg == 0:
        return float("nan")
    return _average_precision(y, s, np.where(y == 1, 1.0, npos / nneg))


def f1_balanced(y, s, thr: float) -> float:
    y, s = np.asarray(y), np.asarray(s)
    npos, nneg = float((y == 1).sum()), float((y == 0).sum())
    pred = s >= thr
    tp = float((pred & (y == 1)).sum())
    fn = float((~pred & (y == 1)).sum())
    fp = float((pred & (y == 0)).sum()) * (npos / nneg if nneg else 0.0)
    return 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
