"""Abstention / tiered output for the sequential verifier: do not emit a confident verdict where the evidence cannot support one.

The verifier's stopping rule ("P(doc) >= tau or <= 1-tau") is a statement about the MODEL. It is not evidence that the
model is right for this kind of case (near-twin candidates, slots whose channels barely separate match from mismatch, ...).
This module adds a decision-time layer that is fitted on TRAINING data only and outputs one of

  CONFIRMED / REFUTED   confident verdict, and the training data say confident verdicts of this kind are reliable
  LOW_CONFIDENCE        the posterior crossed the threshold but the reliability of such verdicts is not demonstrated
                        (cell reliability lower bound below target, cell never seen in training, or unstable trajectory)
  UNRESOLVED_NO_POWER   the (slot) reaches a confident verdict on too small a fraction of TRAINING episodes:
                        the reading pool lacks resolving power, so the tool declines a priori
  UNRESOLVED_BUDGET     no threshold crossing within the reading budget (this was already the tool's "unresolved")

Inputs the rule may use at decision time: the slot (a documentation category, known), the sign of the verdict, the
never-stopped P(doc) trajectory up to the stopping point (number of readings, how often the belief flipped side of 0.5).
It never sees the benchmark observability label, the ground-truth flag, or any held-out outcome. The rule is fitted from
records with the same format as the outer pickles produced on TRAINING units (see nested.py).

Reliability of a cell = (slot, verdict sign): class-balanced accuracy of confident verdicts on training episodes, with
a cluster-aware Beta lower bound (effective n = number of distinct training clusters, not episodes/settings/replicates).
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np

CONFIRMED, REFUTED, LOW_CONFIDENCE = "CONFIRMED", "REFUTED", "LOW_CONFIDENCE"
UNRESOLVED_NO_POWER, UNRESOLVED_BUDGET = "UNRESOLVED_NO_POWER", "UNRESOLVED_BUDGET"
CAP = 24
STATES = (CONFIRMED, REFUTED, LOW_CONFIDENCE, UNRESOLVED_NO_POWER, UNRESOLVED_BUDGET)


def beta_quantile(a: float, b: float, q: float) -> float:
    """q-quantile of Beta(a, b) by numerical integration on a grid (no scipy)."""
    x = np.linspace(1e-6, 1 - 1e-6, 4001)
    logpdf = (a - 1) * np.log(x) + (b - 1) * np.log1p(-x)
    pdf = np.exp(logpdf - logpdf.max())
    cdf = np.cumsum(pdf)
    cdf /= cdf[-1]
    return float(np.interp(q, cdf, x))


def episode_features(traj, tau: float) -> dict:
    """Decision-time features of one never-stopped trajectory under the stopping rule at threshold tau."""
    t = np.asarray(traj, float)
    hit = np.flatnonzero((t >= tau) | (t <= 1 - tau))
    if len(hit) == 0:
        return dict(crossed=False, n=CAP, say_correct=bool(t[-1] >= 0.5), flips=int(np.sum(np.diff((t >= 0.5).astype(int)) != 0)))
    n = int(hit[0])
    return dict(crossed=True, n=n, say_correct=bool(t[n] >= 0.5), flips=int(np.sum(np.diff((t[: n + 1] >= 0.5).astype(int)) != 0)))


@dataclass
class Decision:
    state: str
    reason: str
    n: int
    say_correct: bool


@dataclass
class AbstentionRule:
    tau: float = 0.95
    target: float = 0.90          # required reliability (lower bound) of a confident verdict cell
    q: float = 0.50               # quantile of the reliability posterior used as the lower bound
    min_cov: float = 0.10         # slots whose TRAINING confident-answer coverage is below this are declined a priori
    by_sign: bool = True          # reliability cells keyed by (slot, verdict sign) instead of the slot alone
    max_flips: int = 1            # trajectories that changed side of 0.5 more than this before stopping are flagged
    cells: dict = field(default_factory=dict)   # (slot, say_correct) -> dict(acc, n_eff, lb)
    cov: dict = field(default_factory=dict)     # slot -> training coverage (class-balanced)
    n_train: dict = field(default_factory=dict)

    # ------------------------------------------------------------------ fitting (training records only)
    def fit(self, records: list[dict], weight_by_class: bool = True) -> "AbstentionRule":
        per_slot = defaultdict(list)
        for r in records:
            per_slot[r["slot"]].append(r)
        for slot, rs in per_slot.items():
            feats = [episode_features(r["traj"], self.tau) for r in rs]
            wrong = np.array([bool(r["wrong"]) for r in rs])
            crossed = np.array([f["crossed"] for f in feats])
            self.n_train[slot] = len(rs)
            covs = [crossed[wrong == c].mean() for c in (True, False) if (wrong == c).any()]
            self.cov[slot] = float(np.mean(covs))
            # reliability = P(verdict correct | slot, verdict sign) under a balanced prior: each episode is weighted by
            # 1/(2 * number of training episodes of its class), so a 2:1 class mix in the training data does not tilt it
            n_cls = {c: max(int((wrong == c).sum()), 1) for c in (True, False)} if weight_by_class else {True: 1, False: 1}
            for sc in (True, False):
                sel = [i for i, f in enumerate(feats) if f["crossed"] and f["say_correct"] == sc]
                if not sel:
                    continue
                w = np.array([0.5 / n_cls[bool(wrong[i])] if weight_by_class else 1.0 for i in sel])
                ok = np.array([sc == (not rs[i]["wrong"]) for i in sel], float)
                acc = float((w * ok).sum() / w.sum())
                n_eff = len({rs[i]["group"] for i in sel})
                lb = beta_quantile(1 + acc * n_eff, 1 + (1 - acc) * n_eff, self.q)
                self.cells[(slot, sc)] = dict(acc=acc, n_eff=n_eff, lb=lb, n=len(sel))
            sel = [i for i, f in enumerate(feats) if f["crossed"]]
            if sel:
                w = np.array([0.5 / n_cls[bool(wrong[i])] if weight_by_class else 1.0 for i in sel])
                ok = np.array([feats[i]["say_correct"] == (not rs[i]["wrong"]) for i in sel], float)
                acc = float((w * ok).sum() / w.sum())
                n_eff = len({rs[i]["group"] for i in sel})
                self.cells[(slot, None)] = dict(acc=acc, n_eff=n_eff, lb=beta_quantile(1 + acc * n_eff, 1 + (1 - acc) * n_eff, self.q), n=len(sel))
        return self

    # ------------------------------------------------------------------ decision (available at decision time)
    def decide(self, slot: str, traj) -> Decision:
        f = episode_features(traj, self.tau)
        sc = f["say_correct"]
        if slot not in self.cov:
            return Decision(LOW_CONFIDENCE if f["crossed"] else UNRESOLVED_BUDGET, "slot never seen in training", f["n"], sc)
        if self.cov[slot] < self.min_cov:
            return Decision(UNRESOLVED_NO_POWER, f"training coverage {self.cov[slot]:.2f} < {self.min_cov}", f["n"], sc)
        if not f["crossed"]:
            return Decision(UNRESOLVED_BUDGET, "no threshold crossing within budget", f["n"], sc)
        c = self.cells.get((slot, sc if self.by_sign else None))
        if c is None:
            return Decision(LOW_CONFIDENCE, "no training evidence for this verdict type", f["n"], sc)
        if c["lb"] < self.target:
            return Decision(LOW_CONFIDENCE, f"training reliability LB {c['lb']:.2f} < {self.target}", f["n"], sc)
        if f["flips"] > self.max_flips:
            return Decision(LOW_CONFIDENCE, f"belief changed side {f['flips']}x before stopping", f["n"], sc)
        return Decision(CONFIRMED if sc else REFUTED, "ok", f["n"], sc)

    def with_params(self, **kw) -> "AbstentionRule":
        """Copy sharing the fitted training statistics but with different decision thresholds (for sweeps)."""
        import copy
        new = copy.copy(self)
        for k, v in kw.items():
            setattr(new, k, v)
        return new


# ---------------------------------------------------------------------------------------------- nested selection of the target
TARGET_GRID = (0.0, 0.5, 0.7, 0.8, 0.85, 0.9, 0.93, 0.95, 0.97, 1.01)   # 1.01 = decline every confident verdict


def balanced_cov_acc(records: list[dict], decisions: list[Decision]) -> tuple[float, float]:
    """class-balanced (coverage, accuracy among confident) of confident decisions; accuracy is nan when nothing is confident."""
    covs, accs = [], []
    for cls in (True, False):
        idx = [i for i, r in enumerate(records) if bool(r["wrong"]) == cls]
        if not idx:
            continue
        conf = [i for i in idx if decisions[i].state in (CONFIRMED, REFUTED)]
        covs.append(len(conf) / len(idx))
        if conf:
            accs.append(np.mean([decisions[i].say_correct == (not records[i]["wrong"]) for i in conf]))
    return float(np.mean(covs)) if covs else 0.0, float(np.mean(accs)) if accs else float("nan")


def slot_worst_case(records, decisions, min_groups: int = 5):
    """lowest per-slot class-balanced accuracy among confident decisions, over slots with >= min_groups distinct confident clusters."""
    worst = 1.0
    for slot in {r["slot"] for r in records}:
        idx = [i for i, r in enumerate(records) if r["slot"] == slot]
        conf = [i for i in idx if decisions[i].state in (CONFIRMED, REFUTED)]
        if len({records[i]["group"] for i in conf}) < min_groups:
            continue
        _, acc = balanced_cov_acc([records[i] for i in idx], [decisions[i] for i in idx])
        if not np.isnan(acc):
            worst = min(worst, acc)
    return worst


def nested_select(inner: list[dict], policy: str, tau: float = 0.95, goal: float = 0.95, grid=TARGET_GRID, by_sign_opts=(True, False),
                  slot_slack: float = 0.05, **rule_kw) -> dict:
    """Choose (target, by_sign) for ONE outer unit from its training data only.

    `inner` = inner-run records for that outer unit (each has `inner` = the training unit it was run on). Leave one
    training unit out: fit the rule on the other training units' records, apply it to the held-out training unit's
    records, pool over folds. Pick the setting with the highest coverage whose pooled class-balanced accuracy among
    confident verdicts is >= goal AND whose worst slot (>=5 confident clusters) is >= goal - slot_slack (a pooled bound alone is
    satisfied by averaging strong slots over weak ones) (a conformal-flavoured 'largest coverage that still meets the error bound'); the
    `target=1.01` candidate declines every confident verdict and is always feasible."""
    recs = [r for r in inner if r["policy"] == policy]
    units = sorted({r["inner"] for r in recs}, key=str)
    table, worst, lbs = {}, {}, {}
    for bs in by_sign_opts:
        folds = []
        for h in units:
            tr = [r for r in recs if r["inner"] != h]
            te = [r for r in recs if r["inner"] == h]
            if not tr or not te:
                continue
            folds.append((AbstentionRule(tau=tau, by_sign=bs, **rule_kw).fit(tr), te))
        for t in grid:
            te_all, dec_all = [], []
            for rule, te in folds:
                rt = rule.with_params(target=t)
                te_all += te
                dec_all += [rt.decide(r["slot"], r["traj"]) for r in te]
            cov, acc = balanced_cov_acc(te_all, dec_all) if te_all else (0.0, float("nan"))
            worst[(t, bs)] = slot_worst_case(te_all, dec_all) if te_all else 1.0
            ng = len({r["group"] for r, d in zip(te_all, dec_all) if d.state in (CONFIRMED, REFUTED)})
            lbs[(t, bs)] = 1.0 if ng == 0 else beta_quantile(1 + acc * ng, 1 + (1 - acc) * ng, 0.2)   # demonstrated, not just observed, accuracy
            table[(t, bs)] = (cov, acc)
    feas = [(k, v) for k, v in table.items() if (np.isnan(v[1]) or v[1] >= goal) and worst[k] >= goal - slot_slack and lbs[k] >= goal - slot_slack]
    best = max(feas, key=lambda kv: (kv[1][0], -abs(kv[0][0] - 0.9)))[0]
    return dict(target=best[0], by_sign=best[1], cv_cov=table[best][0], cv_acc=table[best][1], cv_worst_slot=worst[best], cv_acc_lb=lbs[best], table={f"{k[0]}|{k[1]}": v for k, v in table.items()})
