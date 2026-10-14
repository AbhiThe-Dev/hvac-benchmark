"""Latin-hypercube sampling with fixed seeds. numpy only (no scipy in this project)."""
from __future__ import annotations

import numpy as np

from .params import PARAMS, design_from_unit


def lhs_unit(n: int, d: int, rng: np.random.Generator) -> np.ndarray:
    """n x d Latin hypercube on [0,1): exactly one point per stratum in every dimension."""
    u = np.empty((n, d))
    for j in range(d):
        u[:, j] = (rng.permutation(n) + rng.random(n)) / n
    return u


def design_matrix(n: int, seed: int, overrides: dict | None = None) -> list[dict[str, float]]:
    """`overrides` maps a parameter name to a replacement (low, high); used only by stress tests (the frozen matrix passes none)."""
    rng = np.random.default_rng(np.random.SeedSequence(seed))
    u = lhs_unit(n, len(PARAMS), rng)
    out = []
    for row in u:
        d = design_from_unit(row)
        for name, (lo, hi) in (overrides or {}).items():
            spec = next(p for p in PARAMS if p.name == name)
            x = float(row[[p.name for p in PARAMS].index(name)])
            d[name] = (lo if x < 0.5 else hi) if spec.kind == "binary" else lo + x * (hi - lo)
        out.append(d)
    return out


def substream(seed: int, *keys: int) -> np.random.Generator:
    """Independent stream keyed by integers (e.g. sample index, cause index): results do not depend on loop order."""
    return np.random.default_rng(np.random.SeedSequence([seed, *keys]))
