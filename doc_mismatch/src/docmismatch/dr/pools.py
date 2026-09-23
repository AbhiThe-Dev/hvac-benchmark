"""Reading pools for DR-study buildings (existing A-H and DR buildings) under an explicit telemetry setting.

Same construction as `active.pools.build_sim_pool` (48 day-slices = 8 windows x 6 days, three pair-consistency channels per candidate pair, operating context per slice),
except that evidence comes from `make_evidence(..., sensor=...)`. sensor=None reproduces the legacy pools exactly.
"""

from __future__ import annotations

import hashlib
import json
import pickle
from pathlib import Path

import numpy as np

from ..active.pools import CTX_NAMES, DAYS_PER_WINDOW_PICK, EVIDENCE_SLOTS, SEASON_OF_WINDOW, Pool, SlotPool, _slice_context
from ..data import SLOTS, load_base
from ..evidence import closure_channel, make_context, make_evidence, pair_errors
DR_ROOT = Path(__file__).resolve().parents[4] / "results" / "docmismatch_dr"   # (same as build.DR_ROOT; kept here so pools need no openstudio)

POOL_DIR = DR_ROOT / "pools"
DR_DIR = Path(__file__).resolve().parents[4] / "results" / "docmismatch" / "dr"


def _h(s: str) -> int:
    return int(hashlib.sha1(s.encode()).hexdigest()[:8], 16)


def building_spec(tid: str) -> dict | None:
    f = DR_ROOT / "base" / tid / "spec.json"
    return json.loads(f.read_text()) if f.exists() else None


def sensor_setting(tid: str, telemetry: str) -> dict | None:
    """telemetry: 'legacy' (None = the original code path) | 'estimated' | 'wide' | 'wide_distractors' (explicit, seeded, tracked distractors) | 'spec' (what the building's own spec says)."""
    spec = building_spec(tid)
    if telemetry == "legacy":
        return None
    if telemetry == "spec":
        if spec is None:
            return None
        return dict(level=spec["sensor_level"], profile_seed=spec["profile_seed"], distractors=spec["distractors"]) if spec["sensor_level"] != "legacy" else None
    seed = _h(f"telemetry|{telemetry}|{tid}") % 10**6
    d = []
    if telemetry == "wide_distractors":
        d = [dict(type=t, seed=_h(f"dist|{tid}|{k}") % 10**6, window=None if k == 0 else _h(f"dw|{tid}|{k}") % 8)
             for k, t in enumerate(("stuck_sensor", "bias_step", "flow_gain_error"))]
    level = {"estimated": "estimated", "wide": "wide", "wide_distractors": "wide"}[telemetry]
    return dict(level=level, profile_seed=seed, distractors=d)


def build_pool(tid: str, rep: int, sensor: dict | None) -> Pool:
    base = load_base(tid)
    fl = [base.ev[f"{a}|flow"] / (np.abs(base.ev[f"{a}|flow"]).max() + 1e-9) for a in base.ids("AHU")]
    load = np.mean(fl, axis=0)
    slices = [(w, d) for w in range(8) for d in DAYS_PER_WINDOW_PICK]
    ctx = np.zeros((len(slices), len(CTX_NAMES)))
    season = np.zeros(len(slices), dtype=int)
    group = np.zeros(len(slices), dtype=int)
    for i, (w, d) in enumerate(slices):
        a = w * 1008 + d * 24
        ctx[i] = _slice_context(base, slice(a, a + 24), load)
        season[i], group[i] = SEASON_OF_WINDOW[w], w
    pool = Pool(f"{tid}#r{rep}", "sim", ctx, season, group)
    evs = {w: make_evidence(base, w, seed=9000 + 97 * rep + w, sensor=sensor) for w in range(8)}
    for slot in EVIDENCE_SLOTS:
        if slot not in base.slot_edges:
            continue
        spec = SLOTS[slot]
        owners = base.ids(*spec["owner"])
        members = sorted({m for _, m in base.slot_edges[slot]})
        oi = {o: i for i, o in enumerate(owners)}
        truth = np.full(len(members), -1)
        for o, m in base.slot_edges[slot]:
            truth[members.index(m)] = oi[o]
        E = np.full((len(slices), 4, len(owners), len(members)), np.nan)
        for i, (w, d) in enumerate(slices):
            sl = slice(d * 24, (d + 1) * 24)
            ev = evs[w]
            c = make_context(base, ev, sl) if slot == "vav_zone" else None
            for a, o in enumerate(owners):
                for b, m in enumerate(members):
                    E[i, :3, a, b] = pair_errors(base, ev, slot, o, m, sl, c)
                    E[i, 3, a, b] = closure_channel(base, ev, slot, o, m, sl)
        size = np.array([float(np.abs(base.ev[f"{o}|flow"]).max()) + 1e-9 for o in owners])
        pool.slots[slot] = SlotPool(slot, owners, members, truth, E, [base.cls(o) for o in owners], size)
    if sensor and sensor.get("distractors"):
        from .evidence_dr import distractor_nodes
        pool.distractor_nodes = distractor_nodes(base, sensor["distractors"])
    else:
        pool.distractor_nodes = set()
    return pool


_MEM: dict = {}


def load_pool(tid: str, rep: int, telemetry: str) -> Pool:
    key = (tid, rep, telemetry)
    if key in _MEM:
        return _MEM[key]
    POOL_DIR.mkdir(parents=True, exist_ok=True)
    f = POOL_DIR / f"{tid}__{telemetry}__r{rep}.pkl"
    if f.exists():
        p = pickle.loads(f.read_bytes())
    else:
        p = build_pool(tid, rep, sensor_setting(tid, telemetry))
        f.write_bytes(pickle.dumps(p))
    _MEM[key] = p
    return p
