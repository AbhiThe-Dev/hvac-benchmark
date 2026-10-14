"""Graded numeric readings: use how far off a reading is, not just which side of its tolerance it falls on. EXPLORATORY and OFF by default (`make_case_v1(..., graded=True)`).

No new rate is introduced. For a reading check with a two-sided tolerance let z = |reading - expected| / tolerance (z <= 1 is 'normal'). The catalogue's own numbers fix the shape:
  - the noise is a half-normal with scale s0 such that P(z > 1) = bg (the chance of 'abnormal' when the check does not see the cause);
  - a cause the check sees at rate p shifts that same noise by m so that P(z > 1) = p (when p <= bg, the same zero-mean shape is narrowed instead: the check fires LESS under that cause).
A reading is scored by its density under each cause. Integrating the density over z > 1 returns the catalogue's rate, so the graded model agrees with the yes/no one on the yes/no question.

The assumption that is not measured: the readings are (folded) Gaussian around the expected value. Direction (above or below the expected value) is not used.
"""

from __future__ import annotations

from functools import lru_cache
from statistics import NormalDist

import numpy as np

from .. import model as M

_N = NormalDist()


def noise_scale(p_null: float) -> float:
    """The scale s such that P(|N(0, s)| > 1) = p_null."""
    p = min(max(p_null, M.RATE_FLOOR), 1.0 - M.RATE_FLOOR)
    return 1.0 / _N.inv_cdf(1.0 - p / 2.0)


def tail(m: float, s: float) -> float:
    """P(|N(m, s)| > 1)."""
    return 1.0 - _N.cdf((1.0 - m) / s) + _N.cdf((-1.0 - m) / s)


@lru_cache(maxsize=4096)
def row_shape(p: float, bg: float) -> tuple[float, float]:
    """(shift m, scale s) of the reading's distribution under a cause the check fires on with rate `p`, given the null rate `bg`."""
    p = min(max(p, M.RATE_FLOOR), 1.0 - M.RATE_FLOOR)
    s0 = noise_scale(bg)
    if p <= bg:
        return 0.0, noise_scale(p)
    lo, hi = 0.0, 1.0
    while tail(hi, s0) < p:
        hi *= 2.0
        if hi > 1e6:
            break
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if tail(mid, s0) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi), s0


def log_density(z: float, m: float, s: float) -> float:
    """log of the density of z >= 0 under |N(m, s)|."""
    a = -0.5 * ((z - m) / s) ** 2
    b = -0.5 * ((z + m) / s) ** 2
    return float(np.logaddexp(a, b) - np.log(s) - 0.5 * np.log(2.0 * np.pi))


def likelihood(z: float, p_row: np.ndarray, bg: float) -> np.ndarray:
    """Density of the reading z under each cause (up to one common factor); `p_row` is the check's P(abnormal | cause) row, as the yes/no update uses it."""
    bg = min(max(bg, M.RATE_FLOOR), 1.0 - M.RATE_FLOOR)
    ll = np.array([log_density(z, *row_shape(float(p), bg)) for p in p_row])
    return np.exp(ll - ll.max())


def update(post: np.ndarray, z: float, p_row: np.ndarray, bg: float) -> np.ndarray:
    p = post * likelihood(z, p_row, bg)
    s = p.sum()
    return p / s if s > 0 else post


def z_of(value: float, band: tuple[float, float] | None) -> float | None:
    """z for a reading against a two-sided band (lowest normal, highest normal); None for a one-sided or missing band."""
    if band is None or not np.isfinite(band[0]) or not np.isfinite(band[1]):
        return None
    t = 0.5 * (band[1] - band[0])
    return None if t <= 0 else abs(value - 0.5 * (band[0] + band[1])) / t
