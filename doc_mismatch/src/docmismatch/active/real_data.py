"""Real-data pools with a pre-registered dev / SEALED split (see doc_mismatch/PREREGISTRATION.md).

Source: LBNL FDD Data Sets RTU (Figshare 22338265, CC BY 4.0), ORNL FRP research building, 10 VAV rooms.
  baseline : ERTU_{Fall_2020,Spring_2021,Summer_2021,Winter_2022}.csv  (14 days)         -> DEV
  Inc_Eco  : Inc_Eco_SP_{-4,-2,2,4}_<season>.csv        (16 days, 1 day each)            -> DEV
  OA_damper: OA_damper_stuck_{005,010,050,100}_<season>.csv (16 days)                     -> SEALED
  SA_bias  : SA_temp_bias_{-4,-2,2,4}_<season>.csv      (16 days)                        -> SEALED
The split was fixed BEFORE any modelling on the fault days; the fault days had never been loaded by any earlier analysis.
The 14 baseline days were used across ~15 earlier variant comparisons and are therefore DEV only.
Every load of the sealed pool is appended to results/docmismatch/active/sealed_access.log (audit trail).
Slices are 4-hour blocks (6/day); evidence = real_frp.pair_errors; context = (block-mean OAT, its sd, occupancy fraction).
"""

from __future__ import annotations

import datetime
import hashlib
import pickle
import sys
from pathlib import Path

import numpy as np

from .. import real_frp as R
from .pools import CACHE, Pool, SlotPool
from .real_pool import REAL_SLOTS, SEASON_ID

FAULT_DIR = R.DATA.parent / "rtu_faults"
SEASON_FILE = {"Fall_2020": "fall", "Spring_2021": "spring", "Summer_2021": "summer", "Winter_2022": "winter"}
DEV_FAMILIES = ("baseline", "Inc_Eco")
SEALED_FAMILIES = ("OA_damper", "SA_bias")
LEDGER = CACHE / "sealed_access.log"


def _family(fname: str) -> str:
    if fname.startswith("Inc_Eco"):
        return "Inc_Eco"
    if fname.startswith("OA_damper"):
        return "OA_damper"
    if fname.startswith("SA_temp_bias"):
        return "SA_bias"
    return "baseline"


def _sources():
    out = []
    for fn, sn in R.SEASONS.items():
        out.append((R.DATA / fn, sn, "baseline", fn[:-4]))
    for f in sorted(FAULT_DIR.glob("*.csv")):
        season = SEASON_FILE["_".join(f.stem.split("_")[-2:])]
        out.append((f, season, _family(f.name), f.stem))
    return out


def _build(families) -> Pool:
    days, series, meta = [], [], []
    for path, season, fam, scen in _sources():
        if fam not in families:
            continue
        for w in R.load_windows([(path, season)]):
            days.append(w["day"]); series.append(w["series"]); meta.append(dict(day=w["day"], season=season, family=fam, scenario=scen))
    blocks, rooms = R.block_slices(), R.ROOMS
    n, S = len(rooms), len(days) * len(R.block_slices())
    ctx = np.zeros((S, 3)); season = np.zeros(S, int); group = np.zeros(S, int)
    E = {s: np.full((S, 3, n, n), np.nan) for s in REAL_SLOTS}
    i = 0
    for d, ser in enumerate(series):
        for sl in blocks:
            oat, occ = ser["RTU_OA_TEMP"][sl], ser["OCCU_MOD"][sl]
            ctx[i] = [np.nanmean(oat), np.nanstd(oat), np.nanmean(occ)]
            season[i], group[i] = SEASON_ID[meta[d]["season"]], d
            bd = R.make_bundle(ser, sl)
            for slot in REAL_SLOTS:
                for a, o in enumerate(rooms):
                    for b, m in enumerate(rooms):
                        E[slot][i, :, a, b] = R.pair_errors(bd, slot, o, m)
            i += 1
    pool = Pool("ornl_rtu#real", "real", ctx, season, group)
    for slot in REAL_SLOTS:
        pool.slots[slot] = SlotPool(slot, list(rooms), list(rooms), np.arange(n), E[slot], [("VAV",)] * n, np.ones(n))
    pool.days, pool.day_series, pool.day_meta = days, series, meta
    return pool


def load_real_dev(rebuild: bool = False) -> Pool:
    """DEV pool: 14 baseline + 16 Inc_Eco days. All design, training, calibration and variant selection happens here (nested by season)."""
    f = CACHE / "pool_real_dev.pkl"
    if f.exists() and not rebuild:
        return pickle.loads(f.read_bytes())
    CACHE.mkdir(parents=True, exist_ok=True)
    p = _build(DEV_FAMILIES)
    f.write_bytes(pickle.dumps(p))
    return p


def load_real_sealed(reason: str) -> Pool:
    """SEALED pool: 32 OA_damper + SA_bias days. Load ONLY for the pre-registered final evaluation; every call is logged."""
    CACHE.mkdir(parents=True, exist_ok=True)
    with open(LEDGER, "a") as fh:
        fh.write(f"{datetime.datetime.now(datetime.timezone.utc).isoformat()}\t{Path(sys.argv[0]).name}\t{reason}\n")
    f = CACHE / "pool_real_sealed.pkl"
    if f.exists():
        return pickle.loads(f.read_bytes())
    p = _build(SEALED_FAMILIES)
    f.write_bytes(pickle.dumps(p))
    return p


def real_episodes(pool: Pool, n_wrong: int = 30, n_right: int = 10, seed: int = 2026):
    """Pre-registered episode set: per (day, slot) n_wrong random ordered swaps (documented owner a, member b, a != b) and n_right correct edges.
    Seeds depend only on (day, slot) so every variant/policy sees identical episodes. `obs` = day-level observability of the swap (real_frp.observability)."""
    from .engine import Episode
    eps = []
    for d, day in enumerate(pool.days):
        ser, season = pool.day_series[d], pool.day_meta[d]["season"]
        for slot in REAL_SLOTS:
            h = int(hashlib.sha1(f"{seed}|{day}|{slot}|{pool.day_meta[d]['scenario']}".encode()).hexdigest()[:8], 16)
            rng = np.random.default_rng(h)
            pairs = [(a, b) for a in range(10) for b in range(10) if a != b]
            wrong = [pairs[i] for i in rng.choice(len(pairs), n_wrong, replace=False)]
            for a, b in wrong:
                e = Episode(pool, slot, b, a, b, True, f"real|{day}|{pool.day_meta[d]['scenario']}|{slot}|{a}>{b}|wrong", f"{day}|{slot}",
                            {"obs": R.observability(ser, R.Event(slot, min(a, b), max(a, b))), "family": R.FAMILY[slot], "day": d,
                             "season": season, "scenario": pool.day_meta[d]["family"]})
                eps.append(e)
            for b in rng.choice(10, n_right, replace=False):
                b = int(b)
                eps.append(Episode(pool, slot, b, b, b, False, f"real|{day}|{pool.day_meta[d]['scenario']}|{slot}|{b}|right", f"{day}|{slot}",
                                   {"obs": "n/a", "family": "clean", "day": d, "season": season, "scenario": pool.day_meta[d]["family"]}))
    return eps
