"""Metrics for the "is the engine too cautious?" check (PREREGISTRATION_DR.md Addendum 12). Pure functions over per-episode rows:
each row = dict(ep, wrong (documented owner is wrong), crossed (belief left (1-tau, tau) within the budget), n (reads at the crossing / budget end), correct (verdict right)).
"""

from __future__ import annotations

import numpy as np


def summarize(rows: list[dict]) -> dict:
    """Resolved fraction, class-balanced accuracy among resolved verdicts, wrong-and-confident rate over ALL episodes, mean reads among resolved."""
    n = len(rows)
    if n == 0:
        return dict(n=0, resolved=float("nan"), n_resolved=0, acc_resolved=float("nan"), wrong_confident=float("nan"), mean_reads=float("nan"))
    res = [r for r in rows if r["crossed"]]
    accs = []
    for cls in (True, False):
        sub = [r for r in res if bool(r["wrong"]) == cls]
        if sub:
            accs.append(np.mean([bool(r["correct"]) for r in sub]))
    return dict(n=n, resolved=len(res) / n, n_resolved=len(res), acc_resolved=float(np.mean(accs)) if accs else float("nan"),
                wrong_confident=sum(1 for r in res if not r["correct"]) / n,
                mean_reads=float(np.mean([r["n"] for r in res])) if res else float("nan"))


def flips(base: list[dict], other: list[dict]) -> dict:
    """Per-episode changes of `other` relative to `base` (matched on `ep`)."""
    b = {r["ep"]: r for r in base}
    out = dict(gained=0, lost=0, correct_to_wrong=0, wrong_to_correct=0, common=0)
    for r in other:
        if r["ep"] not in b:
            continue
        q = b[r["ep"]]
        out["common"] += 1
        if r["crossed"] and not q["crossed"]:
            out["gained"] += 1
        elif q["crossed"] and not r["crossed"]:
            out["lost"] += 1
        elif r["crossed"] and q["crossed"] and bool(r["correct"]) != bool(q["correct"]):
            out["correct_to_wrong" if q["correct"] else "wrong_to_correct"] += 1
    return out


def verdict(base: dict, other: dict, min_gain: float = 0.10, min_acc: float = 0.90) -> str:
    """Addendum 12's frozen reading rule for one slot and lever."""
    d = other["resolved"] - base["resolved"]
    if d >= min_gain:
        return "WORTH PURSUING" if other["acc_resolved"] >= min_acc else "REJECTED (accuracy among resolved below %.2f)" % min_acc
    return "INERT"
