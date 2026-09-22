"""Real-data variant of the evidence-vs-structure test on LBNL's ORNL FRP RTU-VAV dataset
(LBNL FDD Data Sets RTU, `ORNL_RTU/ERTU_*.csv`, real fault-free operation of a research
facility: one RTU, 10 electric-reheat VAV boxes serving rooms 102-106 / 202-206; 1-minute data, degF).

What real data changes relative to the simulated checks (docmismatch.evidence):
  * NO per-box airflow, no coil water-side data: the mass/heat-balance identities are unavailable.
    Only three coupled quantities exist per box: reheat power P, discharge-air temperature (SAT),
    and room temperature T. Evidence is therefore *coupling* (does this power/SAT stream co-move with
    that other stream), not conservation.
  * Data has gaps (fan-off overnight leaves RTU/VAV supply temperature NaN; files hold non-contiguous
    days). Everything is NaN-aware, pairwise-complete, with a minimum-sample rule; a channel without
    enough valid overlapping samples or with a flat stream is MISSING (NaN), never scored.
  * Units are degF and W; all statistics used are unit-free (correlations, duty cycles, ranks).
  * "Ground truth" mapping = the dataset's own point naming (VAV_RM_SAT_103 is VAV 103). That is a
    well-instrumented lab facility, but it is not an independent field verification of the mapping.
"""

from __future__ import annotations

import csv
import itertools
from dataclasses import dataclass
from pathlib import Path

import numpy as np

DATA = Path(__file__).resolve().parents[3] / "data_cache" / "timeseries" / "rtu_exp"
ROOMS = ["102", "103", "104", "105", "106", "202", "203", "204", "205", "206"]
SEASONS = {"ERTU_Fall_2020.csv": "fall", "ERTU_Spring_2021.csv": "spring", "ERTU_Summer_2021.csv": "summer", "ERTU_Winter_2022.csv": "winter"}
BIN = 5            # minutes per bin after resampling (1-min data are noisy; 5-min means)
N_BLOCKS = 6       # audit blocks per day window (4 h each)
MIN_VALID = 24     # minimum pairwise-valid bins (2 h) for any statistic
LAG = 1            # bins for the lagged-response channel


def load_windows(files: list | None = None) -> list[dict]:
    """One window per calendar day: dict(day, season, series{name: (n_bins,) float, NaN = missing}).
    `files` = optional list of (path, season); default = the four baseline ERTU files (behaviour unchanged)."""
    wins = []
    for fpath, season in (files if files is not None else [(DATA / f, sn) for f, sn in SEASONS.items()]):
        with open(fpath) as fh:
            r = csv.reader(fh)
            hdr = next(r)
            rows = list(r)
        t = np.array([x[0] for x in rows], dtype="datetime64[s]")
        X = np.array([[float(v) if v != "" else np.nan for v in x[1:]] for x in rows])
        names = hdr[1:]
        days = t.astype("datetime64[D]")
        for d in np.unique(days):
            m = days == d
            tm = t[m]
            minute = ((tm - tm.astype("datetime64[D]")).astype("timedelta64[m]").astype(int)) // BIN
            nb = 1440 // BIN
            ser = {}
            for j, n in enumerate(names):
                col = X[m, j]
                out = np.full(nb, np.nan)
                for b in range(nb):
                    v = col[minute == b]
                    v = v[~np.isnan(v)]
                    if len(v):
                        out[b] = v.mean()
                ser[n] = out
            if np.isfinite(ser["TERM_RM_TEMP_102"]).mean() < 0.9:
                continue  # partial day
            wins.append({"day": str(d), "season": season, "series": ser})
    return wins


# ------------------------------------------------------------------ NaN-aware statistics
def _valid(*xs):
    m = np.ones(len(xs[0]), dtype=bool)
    for x in xs:
        m &= np.isfinite(x)
    return m


def pcorr(a, b) -> float:
    m = _valid(a, b)
    if m.sum() < MIN_VALID:
        return np.nan
    a, b = a[m] - a[m].mean(), b[m] - b[m].mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d > 1e-12 else np.nan


def prank(a, b) -> float:
    m = _valid(a, b)
    if m.sum() < MIN_VALID:
        return np.nan
    ra = np.argsort(np.argsort(a[m])).astype(float)
    rb = np.argsort(np.argsort(b[m])).astype(float)
    return pcorr(ra, rb)


def pduty(a, b, ta, tb) -> float:
    m = _valid(a, b)
    if m.sum() < MIN_VALID:
        return np.nan
    return float(abs((a[m] > ta).mean() - (b[m] > tb).mean()))


def _z(x):
    m = np.isfinite(x)
    if m.sum() < MIN_VALID or np.nanstd(x) < 1e-9:
        return np.full_like(x, np.nan)
    return (x - np.nanmean(x)) / np.nanstd(x)


def informative(x, min_range: float) -> bool:
    m = np.isfinite(x)
    return bool(m.sum() >= MIN_VALID and (np.nanmax(x) - np.nanmin(x)) >= min_range)


P_RANGE_W = 50.0   # a reheat stream that never rises 50 W above its floor carries no coupling information
T_RANGE_F = 1.0


@dataclass
class Bundle:
    """Per-room streams for a slice of one day."""
    P: dict; L: dict; T: dict; H: dict
    Pm: np.ndarray; Lm: np.ndarray; Tm: np.ndarray


def make_bundle(ser: dict, sl: slice = slice(None)) -> Bundle:
    sa = ser["RTU_SA_TEMP"][sl]
    P = {r: ser[f"VAV_RM_WATT_{r}"][sl] for r in ROOMS}
    L = {r: ser[f"VAV_RM_SAT_{r}"][sl] - sa for r in ROOMS}       # discharge lift over RTU supply temp (NaN when fan off)
    T = {r: ser[f"TERM_RM_TEMP_{r}"][sl] for r in ROOMS}
    H = {r: ser[f"TERM_RM_HUMD_{r}"][sl] for r in ROOMS}
    fm = lambda D: np.nanmean(np.vstack([_z(D[r]) for r in ROOMS]), axis=0) if any(np.isfinite(_z(D[r])).any() for r in ROOMS) else np.full(len(P[ROOMS[0]]), np.nan)  # noqa: E731
    with np.errstate(all="ignore"):
        return Bundle(P, L, T, H, fm(P), fm(L), fm(T))


SLOTS = {
    "vav_zone": dict(rel="feeds", owner="VAV", member="Zone"),
    "vav_sat": dict(rel="hasPoint", owner="VAV", member="SAT"),
    "vav_pwr": dict(rel="hasPoint", owner="VAV", member="PWR"),
    "zone_temp": dict(rel="hasPoint", owner="Zone", member="TEMP"),
}
FAMILY = {"vav_zone": "VAV-zone swap", "vav_sat": "VAV supply-temp point swap", "vav_pwr": "VAV power point swap", "zone_temp": "Room-temp point swap"}


def pair_errors(bd: Bundle, slot: str, o: str, m: str) -> tuple:
    """(e0, e1, e2), lower = more consistent; NaN = channel missing. `o` = documented owner room id, `m` = documented member's room id
    (the room a stream is named for). Owner-side signals are always those of the physically true box `o`."""
    if slot == "vav_sat":        # documented: SAT stream named `m` is the discharge temp of box `o`;  evidence: box o's reheat power vs that stream's lift
        a, b = bd.L[m], bd.P[o]
        ok = informative(a, 2.0) and informative(b, P_RANGE_W)
        return (1 - pcorr(a, b), 1 - prank(a, b), pduty(a, b, 2.0, 50.0)) if ok else (np.nan,) * 3
    if slot == "vav_pwr":        # documented: power stream `m` is box `o`'s reheat power; evidence: box o's SAT lift vs that stream
        a, b = bd.L[o], bd.P[m]
        ok = informative(a, 2.0) and informative(b, P_RANGE_W)
        return (1 - pcorr(a, b), 1 - prank(a, b), pduty(a, b, 2.0, 50.0)) if ok else (np.nan,) * 3
    # vav_zone / zone_temp: box o's heating activity vs room m's temperature (fleet common mode removed)
    p, l, t = bd.P[o], bd.L[o], bd.T[m]
    if not informative(t, T_RANGE_F):
        return (np.nan,) * 3
    zt = _z(t) - bd.Tm
    # sign-agnostic: the sign of the residual power/lift-vs-temperature relation flipped between seasons in exploration (design=Fall)
    e0 = 1 - abs(pcorr(_z(p) - bd.Pm, zt)) if informative(p, P_RANGE_W) else np.nan
    e1 = 1 - abs(pcorr(_z(l) - bd.Lm, zt)) if informative(l, 2.0) else np.nan
    dT = np.r_[t[LAG:] - t[:-LAG], np.full(LAG, np.nan)]
    e2 = 1 - pcorr(p, dT) if informative(p, P_RANGE_W) else np.nan                 # heating power should precede a temperature rise
    return (e0, e1, e2)


def slot_matrix(bd: Bundle, slot: str) -> np.ndarray:
    """E[k, i, j]: channel k error for owner room ROOMS[i] with member named for ROOMS[j]."""
    E = np.full((3, len(ROOMS), len(ROOMS)), np.nan)
    for i, o in enumerate(ROOMS):
        for j, m in enumerate(ROOMS):
            E[:, i, j] = pair_errors(bd, slot, o, m)
    return E


# ------------------------------------------------------------------ scoring rule (untrained)
EPS = 1e-9


def _margin(e, alts):
    alts = alts[np.isfinite(alts)]
    if not np.isfinite(e) or len(alts) == 0:
        return 0.0
    m = alts.min()
    return float((e - m) / (abs(e) + abs(m) + EPS))


def edge_score_matrix(E: np.ndarray) -> np.ndarray:
    """S[i, j]: suspicion of documenting stream/room j under owner i = mean over VALID channels of
    max(parent-side margin, child-side margin). Untrained, parameter-free; same rule as `sim_rule_scores`."""
    n = E.shape[1]
    S = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            vals = []
            for k in range(3):
                e = E[k, i, j]
                if not np.isfinite(e):
                    continue
                mp = _margin(e, np.delete(E[k, :, j], i))
                mc = _margin(e, np.delete(E[k, i, :], j))
                vals.append(max(mp, mc))
            S[i, j] = float(np.mean(vals)) if vals else 0.0
    return S


@dataclass
class Event:
    slot: str
    a: int
    b: int  # room indices swapped

    @property
    def same_floor(self) -> bool:
        return ROOMS[self.a][0] == ROOMS[self.b][0]

    @property
    def id(self) -> str:
        return f"{self.slot}|{ROOMS[self.a]}|{ROOMS[self.b]}"


def all_events() -> list[Event]:
    return [Event(s, i, j) for s in SLOTS for i, j in itertools.combinations(range(len(ROOMS)), 2)]


def doc_score(S: dict, ev: Event | None) -> float:
    """max edge suspicion over the documentation; the event swaps two members of one slot."""
    best = -1.0
    for slot, M in S.items():
        n = M.shape[0]
        for i in range(n):
            j = i
            if ev is not None and ev.slot == slot and i in (ev.a, ev.b):
                j = ev.b if i == ev.a else ev.a
            best = max(best, M[i, j])
    return best


def block_slices(n_bins: int = 1440 // BIN):
    step = n_bins // N_BLOCKS
    return [slice(k * step, (k + 1) * step) for k in range(N_BLOCKS)]


def observability(ser: dict, ev: Event) -> str:
    """Same rule as docmismatch.observability: some channel separates true from documented owner in >=5/6 blocks with mean relative gap >=0.2."""
    gaps = {(w, k): [] for w in range(2) for k in range(3)}
    for sl in block_slices():
        bd = make_bundle(ser, sl)
        for w, (i, j) in enumerate(((ev.a, ev.b), (ev.b, ev.a))):
            # member named for room j is documented under owner i; the truth is owner j
            et = pair_errors(bd, ev.slot, ROOMS[j], ROOMS[j])
            ed = pair_errors(bd, ev.slot, ROOMS[i], ROOMS[j])
            for k in range(3):
                g = 0.0 if (not np.isfinite(et[k]) or not np.isfinite(ed[k])) else (ed[k] - et[k]) / (abs(ed[k]) + abs(et[k]) + EPS)
                gaps[(w, k)].append(g)
    status = "unobservable"
    for g in gaps.values():
        g = np.array(g)
        wins, mean = int((g > 0).sum()), float(g.mean())
        if wins >= 5 and mean >= 0.2:
            return "observable"
        if wins > 3 and mean >= 0.08:
            status = "ambiguous"
    return status
