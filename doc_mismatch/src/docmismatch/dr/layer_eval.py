"""Metrics and frozen reading rules for "does the reliability layer remove the overconfidence?" (PREREGISTRATION_DR.md Addendum 14). Pure functions over
decision rows (`readiness.apply_layers` output): each row has layer, ep, slot, wrong (documentation is wrong), state (CONFIRMED / REFUTED / FLAGGED), say_correct, cluster.

A verdict is CORRECT when it agrees with the truth: CONFIRMED on a right document, REFUTED on a wrong one.
"""

from __future__ import annotations

import numpy as np

ANSWERED = ("CONFIRMED", "REFUTED")


def _ans(r) -> bool:
    return r["state"] in ANSWERED


def _right(r) -> bool:
    return bool(r["say_correct"]) == (not bool(r["wrong"]))


def summarize(rows: list[dict]) -> dict:
    """Coverage, accuracy among answered (both class-balanced over is_wrong / is_right episodes), wrong-and-confident over ALL episodes,
    false-alarm rate (REFUTED among documentation-right episodes), missed-fault rate (CONFIRMED among documentation-wrong episodes)."""
    n = len(rows)
    nan = float("nan")
    if n == 0:
        return dict(n=0, n_answered=0, coverage=nan, acc_answered=nan, wrong_confident=nan, false_alarm=nan, missed_fault=nan, n_right_docs=0, n_wrong_docs=0)
    ans = [r for r in rows if _ans(r)]
    cov, acc = [], []
    for cls in (True, False):
        sub = [r for r in rows if bool(r["wrong"]) == cls]
        if not sub:
            continue
        cov.append(sum(_ans(r) for r in sub) / len(sub))
        a = [r for r in sub if _ans(r)]
        if a:
            acc.append(np.mean([_right(r) for r in a]))
    docs_right = [r for r in rows if not r["wrong"]]
    docs_wrong = [r for r in rows if r["wrong"]]
    return dict(n=n, n_answered=len(ans), coverage=float(np.mean(cov)), acc_answered=float(np.mean(acc)) if acc else nan,
                wrong_confident=sum(1 for r in ans if not _right(r)) / n,
                false_alarm=(sum(1 for r in docs_right if r["state"] == "REFUTED") / len(docs_right)) if docs_right else nan,
                missed_fault=(sum(1 for r in docs_wrong if r["state"] == "CONFIRMED") / len(docs_wrong)) if docs_wrong else nan,
                n_right_docs=len(docs_right), n_wrong_docs=len(docs_wrong))


def n_answered_correct(rows: list[dict]) -> int:
    return sum(1 for r in rows if _ans(r) and _right(r))


def retained(layer_rows: list[dict], plain_rows: list[dict]) -> float:
    """(answered-and-correct under the layer) / (answered-and-correct under the plain rule); nan when the plain rule got none right."""
    d = n_answered_correct(plain_rows)
    return n_answered_correct(layer_rows) / d if d else float("nan")


def boot_acc_answered(rows: list[dict], B: int = 1000, seed: int = 0) -> tuple[float, float]:
    """Cluster bootstrap 95% interval of the class-balanced accuracy among answered verdicts (resamples whole `cluster`s)."""
    rng = np.random.default_rng(seed)
    cl = sorted({r["cluster"] for r in rows}, key=str)
    if len(cl) < 2:
        return float("nan"), float("nan")
    by = {c: [r for r in rows if r["cluster"] == c] for c in cl}
    vals = []
    for _ in range(B):
        pick = rng.integers(0, len(cl), len(cl))
        s = summarize([r for i in pick for r in by[cl[i]]])["acc_answered"]
        if np.isfinite(s):
            vals.append(s)
    return (float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))) if vals else (float("nan"), float("nan"))


def slot_verdict(plain: list[dict], layer: list[dict], min_answered: int = 10, honest: float = 0.90, keep: float = 0.30) -> str:
    """Addendum 14's frozen reading rule for one target slot (layer `new` against the plain rule of the same slot)."""
    p_acc, s = summarize(plain)["acc_answered"], summarize(layer)
    if np.isfinite(p_acc) and p_acc >= honest:
        return "NO PROBLEM TO FIX"
    ret = retained(layer, plain)
    if s["n_answered"] < min_answered:
        return "ABSTAINS -- too few answers to judge (honest but empty)"
    if s["acc_answered"] < honest:
        return "DOES NOT FIX"
    return "FIXES" if (np.isfinite(ret) and ret >= keep) else "HONEST BUT EMPTY"


def overall(verdicts: list[str]) -> str:
    """Overall reading over the target slots' verdicts."""
    if sum(v == "NO PROBLEM TO FIX" for v in verdicts) >= 2:
        return "the overconfidence was mostly an artefact of the defect"
    if sum(v == "FIXES" for v in verdicts) >= 2:
        return "the layer REMOVES THE OVERCONFIDENCE"
    if sum(v.startswith("HONEST BUT EMPTY") or v.startswith("ABSTAINS") for v in verdicts) >= 2:
        return "the layer SILENCES RATHER THAN FIXES"
    return "the layer does NOT remove the overconfidence"
