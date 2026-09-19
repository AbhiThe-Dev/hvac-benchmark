"""Simulated direct relationship queries with configurable false-positive /
false-negative rates.

These are abstract relationship tests ("does edge (s, t) exist"), not
calibrated actuator-response or downstream-reachability simulations. Noise
is coupled by topology, edge, and repeat number: the underlying random draw
for "the k-th test of edge (s, t) in topology T under seed R" is generated
once from a stable hash of those exact keys, independent of which policy or
noise level is asking, so different policies observe *the same* raw draw
for a given (topology, edge, repeat, seed) and different noise levels are
reproducible replays of that draw, not fresh randomness.
"""

from __future__ import annotations

import hashlib
import struct

import numpy as np


def _stable_seed(*parts: object) -> int:
    payload = "|".join(str(p) for p in parts).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return struct.unpack("<Q", digest[:8])[0] % (2**32 - 1)


def noise_draw(building_id: str, source: str, target: str, repeat_index: int, seed: int) -> float:
    """A single, reproducible U(0,1) draw keyed on (topology, edge, repeat,
    seed) -- the same draw is reused across policies and noise levels."""
    rng = np.random.RandomState(_stable_seed(building_id, source, target, repeat_index, seed))
    return float(rng.random())


def observe(true_value: bool, fp_rate: float, fn_rate: float, draw: float) -> bool:
    """Deterministic function of the coupled draw and the ground truth: a
    true edge is (falsely) reported absent if draw < fn_rate; a false edge
    is (falsely) reported present if draw < fp_rate."""
    if true_value:
        return not (draw < fn_rate)
    return draw < fp_rate
