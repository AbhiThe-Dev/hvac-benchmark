"""Evidence with the DR telemetry layer + tracked distractor faults (hooked into `evidence.make_evidence(..., sensor=...)`).

sensor = dict(level="estimated"|"wide"|"legacy", profile_seed=int, distractors=[dict(type, seed, window)])
The profile (per-building sensor parameters) is fixed by (level, profile_seed); per-window randomness comes from the evidence seed.
The layer's own random per-tag distractors are disabled: distractors here are explicit, seeded and reported (`distractor_nodes`).
"""

from __future__ import annotations

import numpy as np

from ..data import Base
from ..evidence import FLOW_SIGNALS, TEMP_SIGNALS, window_truth
from . import sensor_layer as SL

_STATS = {}
_PROF = {}


def profile_for(level: str, profile_seed: int) -> SL.SensorProfile:
    key = (level, profile_seed)
    if key not in _PROF:
        if "s" not in _STATS:
            _STATS["s"] = SL.load_stats()
        p = SL.draw_profile(_STATS["s"], np.random.default_rng(profile_seed), level)
        p.distractors = []
        _PROF[key] = p
    return _PROF[key]


def _targets(base: Base, d: dict) -> list[str]:
    """tags hit by a distractor spec (deterministic given the building and the spec seed)"""
    r = np.random.default_rng(d["seed"])
    t = d["type"]
    if t == "flow_gain_error":
        pool = sorted(k for k in base.ev if k.split("|")[1] in FLOW_SIGNALS and k.split("-")[0] in ("VAV", "AHU"))
    elif t == "stuck_sensor":
        pool = sorted(k for k in base.ev if k.split("|")[1] in ("temp", "value", "t_dis", "sat"))
    else:
        pool = sorted(k for k in base.ev if k.split("|")[1] in TEMP_SIGNALS | {"value"} and not k.startswith("ENV"))
    return [pool[int(r.integers(len(pool)))]] if pool else []


def distractor_nodes(base: Base, specs: list[dict]) -> set[str]:
    return {tag.split("|")[0] for d in specs for tag in _targets(base, d)}


def apply_distractors(ev: dict, base: Base, specs: list[dict], window: int) -> dict:
    n = len(next(iter(ev.values())))
    for d in specs:
        if d.get("window") is not None and d["window"] != window:
            continue
        r = np.random.default_rng(d["seed"] + 7919 * window)
        for tag in _targets(base, d):
            if tag not in ev:
                continue
            y = ev[tag].copy()
            t = d["type"]
            if t == "stuck_sensor":
                i0 = int(r.integers(0, n // 2)); L = int(r.integers(48, 300))
                y[i0:i0 + L] = y[i0]
            elif t == "bias_step":
                i0 = int(r.integers(0, n)); y[i0:] += r.choice([-1.0, 1.0]) * r.uniform(1.0, 4.0)
            elif t == "spikes":
                k = max(1, int(n * r.uniform(0.005, 0.02))); idx = r.choice(n, k, replace=False)
                y[idx] += r.choice([-1.0, 1.0], k) * 5.0 * (y.std() + 0.1)
            elif t == "flow_gain_error":
                y *= r.uniform(0.75, 1.3)
            elif t == "dropout_burst":
                i0 = int(r.integers(0, n // 2)); L = int(r.integers(12, 72))
                y[i0:i0 + L] = y[max(i0 - 1, 0)]
            ev[tag] = y
    return ev


def make_evidence_dr(base: Base, window: int, seed: int, sensor: dict) -> dict:
    truth = window_truth(base, window)
    ev = SL.apply(truth, profile_for(sensor["level"], sensor["profile_seed"]), np.random.default_rng(seed))
    return apply_distractors(ev, base, sensor.get("distractors") or [], window)
