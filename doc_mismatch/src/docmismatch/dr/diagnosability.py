"""Model-free diagnosability ladder (PREREGISTRATION_DR.md Addendum 11).

Question: with the CURRENT pair-consistency channels, can true-owner pairs be told apart from alternative-owner pairs at all --
and if not, is that because the signal is structurally absent (even noise-free), because telemetry hides it, or because a
channel's input signal is not instrumented? Nothing is fitted here, so the answer does not depend on the sim-to-real
calibration of any likelihood model. Every metric is an upper bound on what these channels' statistics can do, never a proof
that no passive statistic could do better.
"""

from __future__ import annotations

import numpy as np

from ..active.model import tf
from ..active.pools import DAYS_PER_WINDOW_PICK
from ..data import SLOTS, Base
from ..evidence import make_context, make_evidence, pair_errors, window_truth

LEVELS = ("truth", "legacy", "estimated")
N_CH = 3


# ---------------------------------------------------------------------------------------------- pure metrics
def _avg_ranks(x: np.ndarray) -> np.ndarray:
    _, inv, cnt = np.unique(x, return_inverse=True, return_counts=True)
    return (np.cumsum(cnt) - (cnt - 1) / 2.0)[inv]


def auroc_x_above_m(y_m: np.ndarray, y_x: np.ndarray) -> float:
    """P(y_X > y_M) + 0.5 P(tie): 1.0 = alternative-owner pairs always show a larger error than true-owner pairs (perfect), 0.5 = chance."""
    y_m, y_x = np.asarray(y_m, float), np.asarray(y_x, float)
    nm, nx = len(y_m), len(y_x)
    if nm == 0 or nx == 0:
        return float("nan")
    r = _avg_ranks(np.concatenate([y_m, y_x]))
    return float((r[nm:].sum() - nx * (nx + 1) / 2.0) / (nm * nx))


def dprime(y_m: np.ndarray, y_x: np.ndarray) -> float:
    y_m, y_x = np.asarray(y_m, float), np.asarray(y_x, float)
    if len(y_m) < 2 or len(y_x) < 2:
        return float("nan")
    sd = np.sqrt((y_m.var(ddof=1) + y_x.var(ddof=1)) / 2.0)
    return float((y_x.mean() - y_m.mean()) / sd) if sd > 1e-12 else float("nan")


def class_rows(E: np.ndarray, truth: np.ndarray, cands: list, k: int) -> tuple[np.ndarray, np.ndarray]:
    """tf(e) of channel k for every finite (slice, member, candidate) reading, split into true-owner pairs (M) and alternatives (X)."""
    ym, yx = [], []
    for m, cs in enumerate(cands):
        for o in cs:
            v = E[:, k, o, m]
            v = tf(v[np.isfinite(v)])
            (ym if o == truth[m] else yx).append(v)
    cat = lambda a: np.concatenate(a) if a else np.array([])  # noqa: E731
    return cat(ym), cat(yx)


def rank1_accuracy(E: np.ndarray, truth: np.ndarray, cands: list, group: np.ndarray, channels: tuple, pooled: bool = False) -> dict:
    """Identification accuracy of "the lowest-error candidate is the true owner".

    Per (group, member): each channel's tf(e) is averaged over the group's slices (finite readings only), standardised across the
    member's candidates, and averaged over the channels present; ties count as 1/#tied (expected value under random tie-breaking).
    `pooled=True` uses one group holding every slice. A unit is skipped if any candidate has no finite reading in any channel.
    Returns accuracy, chance (mean 1/|candidates|, over the same units), and the number of units used/skipped."""
    groups = [np.arange(len(group))] if pooled else [np.where(group == g)[0] for g in np.unique(group)]
    hit, chance = [], []
    skipped = 0
    for idx in groups:
        for m, cs in enumerate(cands):
            if len(cs) < 2 or truth[m] not in cs:
                continue
            z = np.full((len(channels), len(cs)), np.nan)
            for ci, k in enumerate(channels):
                y = np.array([np.nanmean(tf(E[idx, k, o, m])) if np.isfinite(E[idx, k, o, m]).any() else np.nan for o in cs])
                if np.isfinite(y).all():
                    sd = y.std()
                    z[ci] = (y - y.mean()) / sd if sd > 1e-12 else 0.0
            ok = np.isfinite(z).all(axis=1)
            if not ok.any():
                skipped += 1
                continue
            score = z[ok].mean(axis=0)
            tied = np.isclose(score, score.min(), atol=1e-9)
            hit.append(tied[cs.index(truth[m])] / tied.sum())
            chance.append(1.0 / len(cs))
    return dict(acc=float(np.mean(hit)) if hit else float("nan"), chance=float(np.mean(chance)) if chance else float("nan"),
                n_units=len(hit), n_skipped=skipped)


# ---------------------------------------------------------------------------------------------- building evidence at each level
def slice_list() -> list[tuple[int, int]]:
    return [(w, d) for w in range(8) for d in DAYS_PER_WINDOW_PICK]


def level_evidence(base: Base, level: str, rep: int = 0, sensor: dict | None = None) -> dict:
    """{window: series dict} of the requested telemetry level. `truth` = noise-free true series; `legacy` = the original hard-coded
    noise (same seeds as the cached legacy pools); `estimated` = the DR study's real-DEV-estimated telemetry (`sensor` from dr.pools.sensor_setting)."""
    if level == "truth":
        return {w: window_truth(base, w) for w in range(8)}
    if level == "legacy":
        return {w: make_evidence(base, w, seed=9000 + 97 * rep + w) for w in range(8)}
    if level == "estimated":
        return {w: make_evidence(base, w, seed=9000 + 97 * rep + w, sensor=sensor) for w in range(8)}
    raise ValueError(level)


def slot_layout(base: Base, slot: str):
    """(owners, members, truth (M,), cands: per member list of candidate owner indices (truth + same-class owners))."""
    spec = SLOTS[slot]
    owners = base.ids(*spec["owner"])
    members = sorted({m for _, m in base.slot_edges[slot]})
    oi = {o: i for i, o in enumerate(owners)}
    truth = np.full(len(members), -1)
    for o, m in base.slot_edges[slot]:
        truth[members.index(m)] = oi[o]
    cands = [[o for o in range(len(owners)) if o == truth[m] or base.cls(owners[o]) == base.cls(owners[truth[m]])] for m in range(len(members))]
    return owners, members, truth, cands


def build_E(base: Base, evs: dict, slot: str) -> np.ndarray:
    """E[s, k, o, m] of the three channels over the standard 48 day-slices, masking OFF (raw separation), like `active.pools.build_sim_pool`."""
    owners, members, _, _ = slot_layout(base, slot)
    sl_list = slice_list()
    E = np.full((len(sl_list), N_CH, len(owners), len(members)), np.nan)
    for i, (w, d) in enumerate(sl_list):
        sl = slice(d * 24, (d + 1) * 24)
        ev = evs[w]
        c = make_context(base, ev, sl) if slot == "vav_zone" else None
        for a, o in enumerate(owners):
            for b, m in enumerate(members):
                E[i, :, a, b] = pair_errors(base, ev, slot, o, m, sl, c, mask_uninformative=False)
    return E


def slice_groups() -> np.ndarray:
    return np.array([w for w, _ in slice_list()])


CHANNEL_SETS = {"ch0": (0,), "ch1": (1,), "ch2": (2,), "all3": (0, 1, 2)}


def building_metrics(E: np.ndarray, truth: np.ndarray, cands: list, group: np.ndarray) -> dict:
    """Per-building ladder rows: per-channel AUROC/d', rank-1 (window-aggregated and fully pooled) per channel subset."""
    out = {"auroc": {}, "dprime": {}, "n_M": {}, "n_X": {}, "rank1_window": {}, "rank1_pooled": {}}
    for k in range(N_CH):
        ym, yx = class_rows(E, truth, cands, k)
        out["auroc"][k], out["dprime"][k] = auroc_x_above_m(ym, yx), dprime(ym, yx)
        out["n_M"][k], out["n_X"][k] = len(ym), len(yx)
    for name, chs in CHANNEL_SETS.items():
        out["rank1_window"][name] = rank1_accuracy(E, truth, cands, group, chs)
        out["rank1_pooled"][name] = rank1_accuracy(E, truth, cands, group, chs, pooled=True)
    return out


def boot_mean(vals: list, B: int = 500, seed: int = 0) -> dict:
    """mean over buildings (each counts equally) with a building-cluster bootstrap 95% interval; NaN buildings are dropped."""
    v = np.array([x for x in vals if x == x], float)
    if len(v) == 0:
        return dict(est=float("nan"), lo=float("nan"), hi=float("nan"), n=0)
    rng = np.random.default_rng(seed)
    bs = np.array([v[rng.integers(0, len(v), len(v))].mean() for _ in range(B)])
    return dict(est=float(v.mean()), lo=float(np.percentile(bs, 2.5)), hi=float(np.percentile(bs, 97.5)), n=len(v))
