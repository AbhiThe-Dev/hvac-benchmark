"""What a missing signal costs, and whether a recorded signal or a technician's reading can replace it (PREREGISTRATION_DR.md Addendum 18). Model-free: nothing is fitted.

Part A ranks single signals by how much the best possible channel combination loses when the signal is missing. Part B asks, for `ahu_vav`, whether box discharge temperature
(unfiltered, or restricted to hours the box's own airflow says the reheat is off) or a few technician readings of the box inlet temperature reproduce the ch0 identification
that the (rarely recorded) inlet temperature gives. Everything reuses `diagnosability.rank1_accuracy` and the simulator's evidence unchanged.
"""

from __future__ import annotations

import itertools
import re
import warnings
from dataclasses import dataclass, field

import numpy as np

from ..active.pools import DAYS_PER_WINDOW_PICK
from ..data import N_WINDOWS, SLOTS, window_slice
from ..evidence import EPS
from ..intake_report import CHANNEL_SIGNALS
from . import diagnosability as D

# ---------------------------------------------------------------------------------------------- frozen constants (Addendum 18)
OFFSETS = (0.0, 0.25, 0.5, 1.0, 2.0)          # per-box constant offset sd, kelvin
N_DRAWS = 20
BASE_SEED = 18
BAR, TOL, MIN_HOURS = 0.80, 0.10, 6
USABLE_S = 0.5
DAY_HOURS = tuple(range(8, 18))              # daytime hours of a slice from which spot readings are drawn
SPOT_M = (1, 3, 6)
LOGGER_M = 24
VERDICT_GROUPS = ("g0", "g2")                # winter, summer (windows 0-1 and 4-5)
GROUPS = {"g0": (0, 1), "g1": (2, 3), "g2": (4, 5), "g3": (6, 7), "all": tuple(range(N_WINDOWS))}
CRITICAL_V, MINOR_V = 0.15, 0.05
N_PERM, NULL_TOL = 200, 0.05
DUTY = 0.02
SUBSETS = [c for r in (1, 2, 3) for c in itertools.combinations(range(3), r)]
SUBSET_INDEX = {s: i for i, s in enumerate(SUBSETS)}
TRENDED = ("V0", "V1", "V2", "V3", "V4")
SPOTS = tuple(f"S{m}" for m in SPOT_M) + (f"S{LOGGER_M}",)
VARIANTS = TRENDED + SPOTS
VARIANT_NAMES = {"V0": "inlet_trend", "V1": "dis_reheat_off_oracle", "V2": "dis_flow_top50", "V3": "dis_flow_top25", "V4": "dis_all",
                 "S1": "spot_1", "S3": "spot_3", "S6": "spot_6", "S24": "day_logger"}


# ---------------------------------------------------------------------------------------------- Part A: signal-removal ceilings
def signal_catalogue(slot: str) -> list[tuple[str, str]]:
    seen: list[tuple[str, str]] = []
    for k in sorted(CHANNEL_SIGNALS[slot]):
        for s in CHANNEL_SIGNALS[slot][k]:
            if s not in seen:
                seen.append(s)
    return seen


def remaining_channels(slot: str, signal: tuple[str, str]) -> tuple[int, ...]:
    """the channels that do not read `signal`"""
    return tuple(k for k in sorted(CHANNEL_SIGNALS[slot]) if signal not in CHANNEL_SIGNALS[slot][k])


def subset_ceiling(means: np.ndarray, channels: tuple[int, ...]) -> float:
    """CEILING(S): the best (building-mean) rank-1 over the non-empty subsets of `channels`; `means` is indexed as SUBSETS; NaN if no subset has a value."""
    vals = [means[SUBSET_INDEX[s]] for r in range(1, len(channels) + 1) for s in itertools.combinations(channels, r) if np.isfinite(means[SUBSET_INDEX[s]])]
    return float(max(vals)) if vals else float("nan")


def building_subset_acc(E: np.ndarray, truth: np.ndarray, cands: list, group: np.ndarray) -> np.ndarray:
    """window-aggregated rank-1 of every non-empty channel subset (SUBSETS order); NaN if the building has no scored unit"""
    return np.array([D.rank1_accuracy(E, truth, cands, group, chs)["acc"] for chs in SUBSETS])


def _colmeans(A: np.ndarray) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return np.nanmean(A, axis=0)


def label_value(value: float | None, no_channel: bool) -> str:
    if no_channel or (value is not None and value >= CRITICAL_V):
        return "CRITICAL"
    if value is None or not np.isfinite(value):
        return "UNDEFINED"
    return "MINOR" if value < MINOR_V else "MODERATE"


def part_a_rows(slot: str, A: np.ndarray, n_boot: int = 500, seed: int = 0) -> dict:
    """A: (buildings, 7) subset accuracies. One row per catalogue signal: remaining channels, CEILING(remaining), VALUE = CEILING(all 3) - CEILING(remaining) with a
    building-cluster bootstrap 95% interval (the maximum is recomputed inside every resample), and the frozen label."""
    means = _colmeans(A)
    ceil_all = subset_ceiling(means, (0, 1, 2))
    rng = np.random.default_rng(seed)
    boots = [_colmeans(A[rng.integers(0, len(A), len(A))]) for _ in range(n_boot)]
    rows = []
    for sig in signal_catalogue(slot):
        rem = remaining_channels(slot, sig)
        if not rem:
            rows.append(dict(signal=sig, remaining=rem, ceiling=None, value=None, lo=None, hi=None, label=label_value(None, True), no_channel=True))
            continue
        vals = np.array([subset_ceiling(b, (0, 1, 2)) - subset_ceiling(b, rem) for b in boots])
        value = ceil_all - subset_ceiling(means, rem)
        rows.append(dict(signal=sig, remaining=rem, ceiling=subset_ceiling(means, rem), value=value, lo=float(np.nanpercentile(vals, 2.5)),
                         hi=float(np.nanpercentile(vals, 97.5)), label=label_value(value, False), no_channel=False))
    return dict(slot=slot, ceiling_all=ceil_all, subset_means=means, rows=rows, n_buildings=int(np.isfinite(A).any(axis=1).sum()))


_MEAS_ROW = re.compile(r"^\|\s*(\w+)\s*\|\s*(\w+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*$")


def parse_census_measurements(md: str) -> dict[tuple[str, str], dict]:
    """{(equipment kind, signal): dict(rec_any, rec_80, doc_any, doc_80)} from the 'Which measurements exist' table of `mortar_census.md` (buildings)."""
    out = {}
    section = md.split("## Which measurements exist", 1)[-1].split("\n## ", 1)[0]
    for line in section.splitlines():
        m = _MEAS_ROW.match(line)
        if m:
            out[(m.group(1), m.group(2))] = dict(zip(("rec_any", "rec_80", "doc_any", "doc_80"), map(int, m.groups()[2:])))
    return out


def census_availability(slot: str, signal: tuple[str, str], census: dict) -> str:
    who, sig = signal
    kind = SLOTS[slot]["owner" if who == "o" else "member"][0]
    sig = "rate" if sig == "rate_s|rate" else sig
    row = census.get((kind, sig))
    if row is None:
        return "no such node in any Mortar graph" if kind not in {k for k, _ in census} else "not in the census table"
    return f"recorded in {row['rec_any']} buildings ({row['rec_80']} at >= 80%); documented in {row['doc_any']}"


# ---------------------------------------------------------------------------------------------- Part B: building data
@dataclass
class ABuilding:
    """One simulated building's `ahu_vav` data, per window: box series (M, H), handler series (O, H). `legacy` = noisy (Addendum 11's seeds); `*_truth` and `reheat` = noise-free."""
    tid: str
    owners: list
    members: list
    truth: np.ndarray
    cands: list
    t_in: list
    t_dis: list
    flow: list
    sat: list
    reheat: list | None = None                 # noise-free, or None (the building has no reheat series)
    t_in_truth: list = field(default_factory=list)
    t_dis_truth: list = field(default_factory=list)
    oat_window_mean: np.ndarray | None = None


def from_base(tid: str) -> ABuilding:
    from ..data import load_base
    base = load_base(tid)
    owners, members, truth, cands = D.slot_layout(base, "ahu_vav")
    leg, tru = D.level_evidence(base, "legacy", 0), D.level_evidence(base, "truth")
    st = lambda evs, sig: [np.array([evs[w][f"{m}|{sig}"] for m in members]) for w in range(N_WINDOWS)]  # noqa: E731
    has_reheat = all(f"{m}|reheat" in tru[0] for m in members)
    oat = base.ev.get("ENV|oat")
    return ABuilding(tid, owners, members, truth, cands, st(leg, "t_in"), st(leg, "t_dis"), st(leg, "flow"),
                     [np.array([leg[w][f"{o}|sat"] for o in owners]) for w in range(N_WINDOWS)],
                     st(tru, "reheat") if has_reheat else None, st(tru, "t_in"), st(tru, "t_dis"),
                     np.array([oat[window_slice(w)].mean() for w in range(N_WINDOWS)]) if oat is not None else None)


# ---------------------------------------------------------------------------------------------- Part B: hour selection, readings, error matrices
def selected_hours(variant: str, flow: np.ndarray, reheat_truth: np.ndarray | None) -> np.ndarray:
    """(M, H) boolean hour mask of a trended variant. Reads ONLY the box's own flow (V2, V3) or the noise-free reheat (V1, the oracle): never a temperature, never a candidate's series."""
    if variant in ("V0", "V4"):
        return np.ones(flow.shape, bool)
    if variant == "V1":
        if reheat_truth is None:
            raise ValueError("V1 needs a reheat series")
        return np.abs(reheat_truth) <= DUTY * np.abs(reheat_truth).max(axis=1, keepdims=True) + EPS
    if variant == "V2":
        return flow >= np.median(flow, axis=1, keepdims=True)
    if variant == "V3":
        return flow >= np.percentile(flow, 75, axis=1, keepdims=True)
    raise ValueError(variant)


def trended_E(b: ABuilding, variant: str, off: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """E[s, 0, o, m] over the 48 standard day-slices (channel 0 only): mean over the selected hours of |x_m + off_m - sat_o|; NaN when fewer than MIN_HOURS of the slice's 24 hours are
    selected. Returns (E, window of each slice). V0 (x = t_in, all hours) equals `evidence.pair_errors` channel 0."""
    src = b.t_in if variant == "V0" else b.t_dis
    n_o, n_m = len(b.owners), len(b.members)
    E = np.full((N_WINDOWS * len(DAYS_PER_WINDOW_PICK), 3, n_o, n_m), np.nan)
    for w in range(N_WINDOWS):
        mask = selected_hours(variant, b.flow[w], b.reheat[w] if b.reheat is not None else None)
        x = src[w] + off[:, None]
        for j, d in enumerate(DAYS_PER_WINDOW_PICK):
            sl = slice(d * 24, (d + 1) * 24)
            mk = mask[:, sl]
            n = mk.sum(axis=1)
            err = np.abs(x[None, :, sl] - b.sat[w][:, None, sl])
            e = np.where(mk[None], err, 0.0).sum(axis=2) / np.maximum(n, 1)[None]
            e[:, n < MIN_HOURS] = np.nan
            E[w * len(DAYS_PER_WINDOW_PICK) + j, 0] = e
    return E, np.repeat(np.arange(N_WINDOWS), len(DAYS_PER_WINDOW_PICK))


def spot_E(b: ABuilding, n_reads: int, off: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """One technician visit per (box, window): a day drawn uniformly from the window's six standard day-slices and `n_reads` distinct daytime hours of it (all 24 hours for the
    logger); E[w, 0, o, m] = mean |t_in reading + off_m - sat_o| at those hours. One slice per window."""
    n_o, n_m = len(b.owners), len(b.members)
    E = np.full((N_WINDOWS, 3, n_o, n_m), np.nan)
    for w in range(N_WINDOWS):
        for j in range(n_m):
            d = int(rng.choice(DAYS_PER_WINDOW_PICK))
            hrs = np.arange(24) if n_reads >= 24 else np.sort(rng.choice(DAY_HOURS, n_reads, replace=False))
            idx = d * 24 + hrs
            x = b.t_in[w][j, idx] + off[j]
            E[w, 0, :, j] = np.abs(x[None] - b.sat[w][:, idx]).mean(axis=1)
    return E, np.arange(N_WINDOWS)


def score_groups(E: np.ndarray, win: np.ndarray, truth: np.ndarray, cands: list) -> dict:
    """`diagnosability.rank1_accuracy` (channel 0, per window) restricted to each season group"""
    out = {}
    for name, wins in GROUPS.items():
        idx = np.flatnonzero(np.isin(win, wins))
        out[name] = D.rank1_accuracy(E[idx], truth, cands, win[idx], (0,))
    return out


def _avg(draws: list[dict]) -> dict:
    keys = ("acc", "chance", "n_units", "n_skipped")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return {k: float(np.nanmean([d[k] for d in draws])) for k in keys}


def run_variant(b: ABuilding, variant: str, bi: int, vi: int, offsets=OFFSETS, n_draws: int = N_DRAWS) -> dict:
    """{offset: {group: dict(acc, chance, n_units, n_skipped)}} for one building; averaged over the draws (trended variants at offset 0 are deterministic: one draw)."""
    res = {}
    n_m = len(b.members)
    for si, s in enumerate(offsets):
        rng = np.random.default_rng([BASE_SEED, bi, vi, si])
        draws = 1 if (variant in TRENDED and s == 0.0) else n_draws
        per = []
        for _ in range(draws):
            off = rng.normal(0.0, s, n_m) if s > 0 else np.zeros(n_m)
            E, win = trended_E(b, variant, off) if variant in TRENDED else spot_E(b, int(variant[1:]), off, rng)
            per.append(score_groups(E, win, b.truth, b.cands))
        res[s] = {g: _avg([p[g] for p in per]) for g in GROUPS}
    return res


# ---------------------------------------------------------------------------------------------- Part B: reading rules
def works(v: float, v0: float) -> bool:
    return bool(np.isfinite(v) and np.isfinite(v0) and v >= BAR and v >= v0 - TOL)


def evaluate_variant(pooled: dict, pooled_v0: dict, gate_ok: bool = True, offsets=OFFSETS) -> dict:
    """Addendum 18's frozen rule. `pooled[(s, g)]` and `pooled_v0[(s, g)]` are building-mean rank-1 values over the SAME buildings. A verdict season whose V0 is below BAR at that
    offset is baseline-limited (counts neither way); WORKS at an offset needs at least one non-limited verdict season and success in every one of them. s* = the largest offset at which the
    variant works at it and at every smaller one."""
    works_at, limited = {}, {}
    for s in offsets:
        lim = {g: not (np.isfinite(pooled_v0[(s, g)]) and pooled_v0[(s, g)] >= BAR) for g in VERDICT_GROUPS}
        live = [g for g in VERDICT_GROUPS if not lim[g]]
        limited[s] = lim
        works_at[s] = bool(live) and all(works(pooled[(s, g)], pooled_v0[(s, g)]) for g in live)
    s_star = None
    for s in sorted(offsets):
        if not works_at[s]:
            break
        s_star = s
    if not gate_ok or all(limited[min(offsets)].values()):
        verdict = "NO VERDICT"
    elif s_star is None:
        verdict = "FAILS"
    else:
        verdict = "USABLE" if s_star >= USABLE_S else "FRAGILE"
    return dict(verdict=verdict, s_star=s_star, works_at=works_at, limited=limited)


def smallest_m(pooled_by_m: dict, pooled_v0: dict, s: float) -> int | None:
    """smallest number of readings whose spot variant WORKS at offset s under the same rule (None if none does); `pooled_by_m` = {m: pooled dict}"""
    for m in sorted(pooled_by_m):
        if evaluate_variant(pooled_by_m[m], pooled_v0, offsets=(s,))["works_at"][s]:
            return m
    return None


# ---------------------------------------------------------------------------------------------- Part B: gates and checks
def unit_weights(E: np.ndarray, cands: list, group: np.ndarray, channel: int = 0) -> list[tuple[int, list, np.ndarray]]:
    """Every scored (group, member) unit of `diagnosability.rank1_accuracy` for one channel, as (member, candidates, tie weights over the candidates); the permutation null
    re-scores these with a shuffled truth without recomputing the errors."""
    from ..active.model import tf
    units = []
    for g in np.unique(group):
        idx = np.where(group == g)[0]
        for m, cs in enumerate(cands):
            if len(cs) < 2:
                continue
            y = np.array([np.nanmean(tf(E[idx, channel, o, m])) if np.isfinite(E[idx, channel, o, m]).any() else np.nan for o in cs])
            if not np.isfinite(y).all():
                continue
            sd = y.std()
            z = (y - y.mean()) / sd if sd > 1e-12 else np.zeros_like(y)
            tied = np.isclose(z, z.min(), atol=1e-9)
            units.append((m, cs, tied / tied.sum()))
    return units


def acc_from_units(units: list, truth: np.ndarray) -> tuple[float, float]:
    """(accuracy, chance) over the units whose `truth[m]` is among the candidates"""
    hit, chance = [], []
    for m, cs, w in units:
        if truth[m] in cs:
            hit.append(w[cs.index(truth[m])])
            chance.append(1.0 / len(cs))
    return (float(np.mean(hit)), float(np.mean(chance))) if hit else (float("nan"), float("nan"))


def null_control(units: list, truth: np.ndarray, n_perm: int = N_PERM, seed: int = 0) -> dict:
    """mean accuracy when the true owners are shuffled among the boxes (each handler keeps its number of boxes): should sit at chance"""
    rng = np.random.default_rng(seed)
    accs, chances = [], []
    for _ in range(n_perm):
        a, c = acc_from_units(units, truth[rng.permutation(len(truth))])
        if np.isfinite(a):
            accs.append(a)
            chances.append(c)
    return dict(acc=float(np.mean(accs)) if accs else float("nan"), chance=float(np.mean(chances)) if chances else float("nan"), n_perm=len(accs))


def oracle_identity_gap(b: ABuilding) -> float | None:
    """C2: the largest |t_dis - t_in| (noise-free) over the hours the reheat is off; None when the building has no reheat series"""
    if b.reheat is None:
        return None
    gaps = []
    for w in range(N_WINDOWS):
        off = selected_hours("V1", b.flow[w], b.reheat[w])
        gaps.append(np.abs(b.t_dis_truth[w] - b.t_in_truth[w])[off].max() if off.any() else 0.0)
    return float(max(gaps))


def selection_shares(b: ABuilding, variant: str) -> dict:
    """C3: per season group, the share of hours selected and the share of (box, slice) readings valid, averaged over boxes and slices"""
    hours = {g: [] for g in GROUPS}
    valid = {g: [] for g in GROUPS}
    for w in range(N_WINDOWS):
        mask = selected_hours(variant, b.flow[w], b.reheat[w] if b.reheat is not None else None)
        per_slice = np.stack([mask[:, d * 24:(d + 1) * 24].sum(axis=1) for d in DAYS_PER_WINDOW_PICK])      # (slices, M)
        for g, wins in GROUPS.items():
            if w in wins:
                hours[g].append(per_slice.mean() / 24.0)
                valid[g].append((per_slice >= MIN_HOURS).mean())
    return {g: dict(hours=float(np.mean(hours[g])), valid=float(np.mean(valid[g]))) for g in GROUPS}


def season_check(b: ABuilding) -> bool | None:
    """C4: the winter windows (0-1) are colder than the summer windows (4-5) by the building's own outdoor-air series"""
    if b.oat_window_mean is None:
        return None
    return bool(b.oat_window_mean[[0, 1]].mean() < b.oat_window_mean[[4, 5]].mean())
