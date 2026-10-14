"""Model-free passive `vav_zone` identifiability on real buildings (PREREGISTRATION_DR.md Addendum 17). Nothing is fitted.

Pieces: the truth audit (point labels), the analysis set, the score matrix behind `diagnosability.rank1_accuracy` (so a permutation null can be run on it), the permutation
p-value, top-k accuracy, the coupling-injection sensitivity control, and the frozen reading rules.
"""

from __future__ import annotations

import csv
import re
import warnings
from dataclasses import replace
from pathlib import Path

import numpy as np

from ..active.model import tf
from ..intake import FieldBuilding
from ..intake_report import _series_status

# box token in a point label: `<bldg>.ZONE.<AHU>.<room>.<point>` (pattern A) or `<a>-<b>-<c>_<point>` (pattern B; alphanumeric ids such as 2-4-17A)
LABEL_A = re.compile(r"^[^.]+\.ZONE\.[^.]+\.([^.]+)\.")
LABEL_B = re.compile(r"^([0-9A-Za-z]+-[0-9A-Za-z]+-[0-9A-Za-z]+)_")
ALPHAS = (0.1, 0.25, 0.5, 1.0)
GATE_ALPHA, GATE_ACC = 1.0, 0.80
N_PERM, PERM_SEED = 10_000, 0
IDENTIFIES_ACC, IDENTIFIES_P, CHANCE_P = 0.50, 0.01, 0.05
MIN_PAIRS = 8


# ---------------------------------------------------------------------------------------------- truth audit and analysis set
def label_token(label: str) -> str | None:
    for rx in (LABEL_A, LABEL_B):
        m = rx.match(label or "")
        if m:
            return m.group(1)
    return None


def read_labels(points_csv: str | Path) -> dict[tuple[str, str], str]:
    """{(equipment_id, signal): label} from an intake `points.csv` that carries a `label` column (written by the Mortar converter)."""
    with open(points_csv, newline="", encoding="utf-8-sig") as fh:
        return {(r["equipment_id"], r["signal"]): r.get("label", "") for r in csv.DictReader(fh)}


def audit_claim(vav: str, zone: str, labels: dict, need: tuple = ("flow", "t_dis")) -> bool:
    """A claim passes when the labels of the VAV's `need` points and of the zone temperature all carry the same box token (Addendum 17: flow, discharge temperature, zone
    temperature; the secondary buildings, which have no discharge temperature, are audited on the points they have)."""
    toks = [label_token(labels.get(k, "")) for k in [(vav, s) for s in need] + [(zone, "temp")]]
    return all(t is not None for t in toks) and len(set(toks)) == 1


def analysis_set(fb: FieldBuilding, labels: dict, need: tuple = ("flow", "t_dis")) -> dict:
    """The documented (VAV, zone) pairs that pass the label audit and whose VAV `need` series and zone temperature are all usable (`intake_report._series_status == "ok"`).
    Returns dict(pairs=[(vav, zone)], failed_audit=[(vav, zone)], failed_series={(vav, zone): reason})."""
    pairs, bad_audit, bad_series = [], [], {}
    for c in fb.claims:
        if c.slot != "vav_zone":
            continue
        if not audit_claim(c.owner, c.member, labels, need):
            bad_audit.append((c.owner, c.member))
            continue
        why = []
        for eq, sig in [(c.owner, s) for s in need] + [(c.member, "temp")]:
            st = _series_status(fb, eq, sig)
            if st != "ok":
                why.append(f"{eq}|{sig} {st}")
        if why:
            bad_series[(c.owner, c.member)] = "; ".join(why)
        else:
            pairs.append((c.owner, c.member))
    return dict(pairs=pairs, failed_audit=bad_audit, failed_series=bad_series)


def restrict(E: np.ndarray, owners: list, members: list, pairs: list) -> tuple[np.ndarray, np.ndarray, list]:
    """E and truth restricted to the analysis set: candidates = the set's VAVs, members = its zones. Returns (E[:, :3, n, n], truth (n,), cands)."""
    oi, mi = {o: i for i, o in enumerate(owners)}, {m: i for i, m in enumerate(members)}
    vavs = [v for v, _ in pairs]
    zones = [z for _, z in pairs]
    sub = E[:, :3][:, :, [oi[v] for v in vavs]][:, :, :, [mi[z] for z in zones]]
    truth = np.arange(len(pairs))                                  # member j's true owner is VAV j (same order)
    cands = [list(range(len(pairs))) for _ in pairs]
    return sub, truth, cands


# ---------------------------------------------------------------------------------------------- scores, rank-1, permutation null
def score_matrix(E: np.ndarray, channels: tuple = (0, 1, 2), idx: np.ndarray | None = None) -> np.ndarray:
    """S[m, o]: for member m, each channel's mean tf(e) over the slices `idx`, standardised across the candidates, averaged over the channels for which every candidate has a
    finite value (lowest = best). Identical to what `diagnosability.rank1_accuracy` computes per unit; NaN row = the unit has no usable channel (skipped)."""
    idx = np.arange(E.shape[0]) if idx is None else idx
    n_o, n_m = E.shape[2], E.shape[3]
    Z = np.full((len(channels), n_o, n_m), np.nan)
    for ci, k in enumerate(channels):
        T = tf(E[idx, k])                                          # (S, O, M), NaN = no reading
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)        # a candidate with no finite reading at all gives NaN, as in rank1_accuracy
            Y = np.nanmean(T, axis=0)                              # (O, M)
        for m in range(n_m):
            y = Y[:, m]
            if np.isfinite(y).all():
                sd = y.std()
                Z[ci, :, m] = (y - y.mean()) / sd if sd > 1e-12 else 0.0
    ok = np.isfinite(Z).all(axis=1)                                # (channel, member)
    S = np.full((n_m, n_o), np.nan)
    for m in range(n_m):
        if ok[:, m].any():
            S[m] = Z[ok[:, m], :, m].mean(axis=0)
    return S


def tie_weights(S: np.ndarray) -> np.ndarray:
    """W[m, o] = 1/#tied if candidate o ties for the lowest score of member m, else 0 (NaN rows: all 0)."""
    W = np.zeros_like(S)
    for m in range(S.shape[0]):
        if np.isfinite(S[m]).all():
            t = np.isclose(S[m], S[m].min(), atol=1e-9)
            W[m] = t / t.sum()
    return W


def rank1_from_scores(S: np.ndarray, truth: np.ndarray) -> dict:
    used = np.isfinite(S).all(axis=1)
    W = tie_weights(S)
    acc = float(np.mean([W[m, truth[m]] for m in np.flatnonzero(used)])) if used.any() else float("nan")
    return dict(acc=acc, chance=1.0 / S.shape[1] if S.shape[1] else float("nan"), n_units=int(used.sum()), n_skipped=int((~used).sum()))


def perm_pvalue(S: np.ndarray, truth: np.ndarray, n_perm: int = N_PERM, seed: int = PERM_SEED) -> dict:
    """Permutation test on the same scores: `truth` is replaced by random one-to-one re-assignments of the candidates to the members; p = (1 + #{acc_perm >= acc}) / (n_perm + 1)."""
    used = np.flatnonzero(np.isfinite(S).all(axis=1))
    W = tie_weights(S)
    obs = float(np.mean([W[m, truth[m]] for m in used])) if len(used) else float("nan")
    rng = np.random.default_rng(seed)
    n_o = S.shape[1]
    ge = 0
    null = np.empty(n_perm)
    for i in range(n_perm):
        perm = rng.permutation(n_o)
        null[i] = W[used, perm[used]].mean()
        ge += null[i] >= obs - 1e-12
    return dict(acc=obs, p=(1 + ge) / (n_perm + 1), null_mean=float(null.mean()), null_p95=float(np.percentile(null, 95)))


def top_k_accuracy(S: np.ndarray, truth: np.ndarray, k: int = 3) -> float:
    """Fraction of members whose true candidate is among the k lowest scores (a tie straddling the boundary earns fractional credit)."""
    credit = []
    for m in range(S.shape[0]):
        if not np.isfinite(S[m]).all():
            continue
        s = S[m, truth[m]]
        lower = int((S[m] < s - 1e-9).sum())
        tied = int(np.isclose(S[m], s, atol=1e-9).sum())
        credit.append(float(np.clip((k - lower) / tied, 0.0, 1.0)))
    return float(np.mean(credit)) if credit else float("nan")


# ---------------------------------------------------------------------------------------------- sensitivity control and reading rules
def _z(x: np.ndarray) -> np.ndarray:
    sd = np.nanstd(x)
    return (x - np.nanmean(x)) / sd if sd > 1e-12 else np.zeros_like(x)


def inject_coupling(fb: FieldBuilding, pairs: list, alpha: float) -> FieldBuilding:
    """Copy of `fb` in which each analysed zone's hourly temperature gets `alpha * sd(temp) * (z(flow_v) + z(t_dis_v)) / sqrt(2)` added, z = standardised hourly series of its own
    box over the whole export. In memory only: the export files and the original `fb` are untouched. alpha = 0 returns the data unchanged."""
    ev = dict(fb.ev)
    if alpha:
        for v, z in pairs:
            t = fb.ev[f"{z}|temp"]
            ev[f"{z}|temp"] = t + alpha * np.nanstd(t) * (_z(fb.ev[f"{v}|flow"]) + _z(fb.ev[f"{v}|t_dis"])) / np.sqrt(2.0)
    return replace(fb, ev=ev)


def detected(acc: float, p: float) -> bool:
    return bool(acc >= IDENTIFIES_ACC and p < IDENTIFIES_P)


def min_detectable(results_by_alpha: dict) -> float | None:
    """smallest alpha on the grid at which the primary statistic reaches the IDENTIFIES bar (acc >= 0.50 and p < 0.01), else None"""
    for a in sorted(results_by_alpha):
        r = results_by_alpha[a]
        if detected(r["acc"], r["p"]):
            return a
    return None


def verdict(primary: dict, gates: dict) -> str:
    """Addendum 17's frozen reading rules. `primary` = {building: dict(acc, p)}, `gates` = {name: bool}; a failed gate means no verdict."""
    failed = [g for g, ok in gates.items() if not ok]
    if failed:
        return "NO VERDICT (gate failed: " + ", ".join(failed) + ")"
    if all(detected(r["acc"], r["p"]) for r in primary.values()):
        return "PASSIVE vav_zone IDENTIFIES ON REAL DATA"
    if all(r["p"] >= CHANCE_P for r in primary.values()):
        return "AT CHANCE -- ADDENDUM 11 HOLDS ON REAL DATA"
    return "BUILDING-DEPENDENT OR WEAK"
