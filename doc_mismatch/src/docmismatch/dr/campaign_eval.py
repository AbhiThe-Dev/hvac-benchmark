"""Wiring the setpoint-dither campaign into the verdict logic (PREREGISTRATION_DR.md Addendum 15, Part B). numpy only; the frozen `active/*.py` engine is not touched.

The campaign is an ESCALATION stage after the passive engine. Its evidence about zone m is the score vector S(m, .) over the candidate boxes (`dr.perturbation`); it enters the
belief through a one-parameter conditional-logit link, `post_j  ∝  post_passive_j * exp(kappa * S(m, box_j))`, with `kappa` fitted by maximum likelihood on TRAINING buildings only.
A verdict follows the engine's own rule: P(doc) >= tau CONFIRMED, <= 1 - tau REFUTED, otherwise unresolved (FLAGGED, the vocabulary of `dr.layer_eval`).
"""

from __future__ import annotations

import numpy as np

from .layer_eval import summarize

KAPPA_GRID = (1, 2, 3, 5, 7, 10, 15, 20, 30, 50, 75, 100, 150, 200)


def log_softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=-1, keepdims=True)
    return z - np.log(np.exp(z).sum(axis=-1, keepdims=True))


def fit_kappa(S_list: list[np.ndarray], truth_list: list[np.ndarray], grid=KAPPA_GRID) -> tuple[float, bool]:
    """Maximum-likelihood link strength: kappa maximising sum over zones of log softmax(kappa * S_zone)[true box], over the frozen grid.
    S_list[i] is (zones, boxes), truth_list[i] the true box index of each zone. Ties go to the smaller kappa. Returns (kappa, unbounded): `unbounded` = the likelihood at the top of the grid is no worse than at the chosen kappa (a
    perfectly separated training set has no finite maximum-likelihood link)."""
    ll = [sum(float(log_softmax(k * np.asarray(S))[np.arange(len(t)), np.asarray(t, int)].sum()) for S, t in zip(S_list, truth_list)) for k in grid]   # softmax over each building's OWN boxes
    best = int(np.argmax(ll))                                   # first grid value reaching the maximum
    return float(grid[best]), ll[-1] >= ll[best] - 1e-9         # flag: the likelihood is still (numerically) no worse at the top of the grid, i.e. the ML link is not finite


def combine(post: np.ndarray, box_idx: np.ndarray, s_row: np.ndarray, kappa: float) -> np.ndarray:
    """Posterior over the engine's H candidate owners after the campaign. `post` (H,) is the passive posterior, `box_idx[j]` the box column of candidate j,
    `s_row` (boxes,) the campaign scores of this zone."""
    lp = np.log(np.clip(np.asarray(post, float), 1e-300, None)) + kappa * np.asarray(s_row, float)[np.asarray(box_idx, int)]
    return np.exp(log_softmax(lp))


def engine_prior(H: int, prior_doc: float = 0.5) -> np.ndarray:
    """The engine's own prior over candidates: `prior_doc` on the documented owner (index 0), the rest split equally."""
    return np.r_[prior_doc, np.full(H - 1, (1.0 - prior_doc) / (H - 1))]


def verdict(post: np.ndarray, tau: float = 0.95) -> str:
    p = float(post[0])
    return "CONFIRMED" if p >= tau else ("REFUTED" if p <= 1 - tau else "FLAGGED")


def make_row(post: np.ndarray, truth_j: int, is_wrong: bool, cluster: str, tau: float = 0.95, **extra) -> dict:
    """One decision row: `state`, `say_correct` (P(doc) >= 0.5), `wrong` (documentation is wrong), `localised` (the most probable candidate is the true owner)."""
    return dict(state=verdict(post, tau), say_correct=bool(post[0] >= 0.5), wrong=bool(is_wrong), cluster=cluster,
                localised=bool(int(np.argmax(post)) == int(truth_j)), p_doc=float(post[0]), **extra)


def resolved_fraction(rows: list[dict]) -> float:
    return sum(r["state"] != "FLAGGED" for r in rows) / len(rows) if rows else float("nan")


def localisation(rows: list[dict]) -> float:
    """Among documentation-WRONG rows: fraction whose most probable owner is the true one (whether or not the verdict crossed tau)."""
    w = [r for r in rows if r["wrong"]]
    return float(np.mean([r["localised"] for r in w])) if w else float("nan")


def cluster_boot(rows: list[dict], stat, B: int = 500, seed: int = 0) -> tuple[float, float]:
    """95% interval of `stat(rows)` by resampling whole clusters (buildings)."""
    rng = np.random.default_rng(seed)
    cl = sorted({r["cluster"] for r in rows}, key=str)
    if len(cl) < 2:
        return float("nan"), float("nan")
    by = {c: [r for r in rows if r["cluster"] == c] for c in cl}
    vals = []
    for _ in range(B):
        pick = rng.integers(0, len(cl), len(cl))
        v = stat([r for i in pick for r in by[cl[i]]])
        if np.isfinite(v):
            vals.append(v)
    return (float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))) if vals else (float("nan"), float("nan"))


def policy_verdict(rows: list[dict], resolved_min: float = 0.70, partial_min: float = 0.30, acc_min: float = 0.90, fa_max: float = 0.10) -> str:
    """Addendum 15's frozen reading rule for one policy. Resolved fraction = answered rows / all rows; accuracy among resolved is class-balanced (`layer_eval.summarize`)."""
    if not rows:
        return "FAILS"
    s = summarize(rows)
    res, acc = s["n_answered"] / s["n"], s["acc_answered"]
    if res >= resolved_min:
        if acc >= acc_min and s["false_alarm"] <= fa_max:
            return "PASSES"
        return "RESOLVES BUT IS DISHONEST" if not acc >= acc_min else "FAILS"
    return "HONEST BUT PARTIAL" if (res >= partial_min and acc >= acc_min) else "FAILS"


def overall(verdicts: dict[str, tuple[str, dict[str, str]]]) -> str:
    """Overall reading. `verdicts[policy] = (pooled verdict, {season: verdict})`."""
    if any(p == "PASSES" and all(v == "PASSES" for v in ss.values()) for p, ss in verdicts.values()):
        return "wiring HELPS `vav_zone` (in simulation)"
    if any(p == "PASSES" for p, _ in verdicts.values()):
        return "wiring HELPS IN ONE SEASON ONLY"
    return "wiring does NOT help"
