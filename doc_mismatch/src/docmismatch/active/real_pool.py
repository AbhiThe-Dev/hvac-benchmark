"""Reading pool from the real ORNL RTU-VAV data (LBNL FDD Data Sets, Figshare 22338265, CC BY 4.0).

Slice = one 4-hour block of one calendar day (6 per day, 14 days, 4 seasons). Context = block-mean outdoor-air temp
(degF), its within-block sd, and occupancy-mode fraction. Owners and members are the 10 rooms (box `o` vs the stream
named for room `m`); the true owner of stream m is box m (the dataset's own naming -- not an independent verification).
There is no injected noise: the values are the field data's own noise, gaps and flat streams.
"""

from __future__ import annotations

import pickle

import numpy as np

from .. import real_frp as R
from .pools import CACHE, Pool, SlotPool

SEASON_ID = {"fall": 0, "spring": 1, "summer": 2, "winter": 3}
REAL_SLOTS = ("vav_zone", "vav_sat", "vav_pwr")


def build_real_pool() -> Pool:
    W = R.load_windows()
    blocks = R.block_slices()
    rooms = R.ROOMS
    n = len(rooms)
    S = len(W) * len(blocks)
    ctx = np.zeros((S, 3))
    season = np.zeros(S, int)
    group = np.zeros(S, int)
    E = {s: np.full((S, 3, n, n), np.nan) for s in REAL_SLOTS}
    i = 0
    for d, w in enumerate(W):
        ser = w["series"]
        for sl in blocks:
            oat, occ = ser["RTU_OA_TEMP"][sl], ser["OCCU_MOD"][sl]
            ctx[i] = [np.nanmean(oat), np.nanstd(oat), np.nanmean(occ)]
            season[i], group[i] = SEASON_ID[w["season"]], d
            bd = R.make_bundle(ser, sl)
            for slot in REAL_SLOTS:
                for a, o in enumerate(rooms):
                    for b, m in enumerate(rooms):
                        E[slot][i, :, a, b] = R.pair_errors(bd, slot, o, m)
            i += 1
    pool = Pool("ornl_rtu#real", "real", ctx, season, group)
    for slot in REAL_SLOTS:
        pool.slots[slot] = SlotPool(slot, list(rooms), list(rooms), np.arange(n), E[slot], [("VAV",)] * n, np.ones(n))
    pool.days = [w["day"] for w in W]
    pool.day_series = [w["series"] for w in W]
    return pool


def load_or_build_real() -> Pool:
    f = CACHE / "pool_real.pkl"
    if f.exists():
        return pickle.loads(f.read_bytes())
    CACHE.mkdir(parents=True, exist_ok=True)
    p = build_real_pool()
    f.write_bytes(pickle.dumps(p))
    return p
