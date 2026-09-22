"""Per-channel trust-weighted evidence (PREREGISTRATION_DR.md Addendum 8): a continuous generalisation of
`engine.exclude_k`'s binary in/out gate, driven directly by `measurement.real_channel_validity`'s honest,
cluster-robust accuracy estimate.

Why: `exclude_k` treats every channel as either fully trusted or not used at all. But Addendum 5a's own numbers
show a spectrum, not two buckets -- real `vav_zone` channel 1 is weak-but-real (point balanced accuracy 0.533),
channel 0 is barely-above-chance (0.516), channel 2 is confidently BELOW chance (0.307, actively backwards).
Dropping 0 and 2 entirely (Addendum 5's `exclude_struct`) throws away whatever little real signal channel 0 has.

Mechanism: `TrustWeightedModel` wraps a `ChannelModel` (same drop-in pattern as `dr.sysid.BiasAdaptedModel`) and
inflates its class-conditional standard deviations by `1/sqrt(weight)`. For a Gaussian, raising the likelihood to
a power `w` is equivalent (up to a y-independent constant) to evaluating it at variance `sigma^2 / w` -- the SAME
power-likelihood tempering `engine.py`'s global `beta` already performs, just made channel-specific instead of
one number for the whole slot. `weight=1` is a pure passthrough (bit-identical); `weight->0` drives a channel's
contribution to the posterior update AND to its own EIG toward zero without any special-casing in engine.py --
both `_Actions`/`observe()` (posterior) and `eig_all()` (selection) already read `sd_M`/`sd_X` purely from
`model.params(ctx)`, so nothing in engine.py needs to know a weighted model even exists.
"""

from __future__ import annotations

import numpy as np

from .measurement import ChannelValidity
from .model import ChannelModel

MIN_WEIGHT = 0.02   # below this, wrap-and-inflate is numerically pointless (sd inflated >7x); exclude instead


class TrustWeightedModel:
    """Wraps a fitted ChannelModel, inflating both class sds by 1/sqrt(weight) (weight in (0, 1]). Delegates
    every other attribute (fit, kappa, rho, omega, rho_s, ...) to the wrapped model, exactly like
    `dr.sysid.BiasAdaptedModel`, so it is a drop-in replacement in engine.run_episode."""

    def __init__(self, base: ChannelModel, weight: float):
        if not (0 < weight <= 1):
            raise ValueError(f"weight must be in (0, 1], got {weight}")
        self._base = base
        self.weight = float(weight)

    def __getattr__(self, name):
        return getattr(self._base, name)

    def params(self, ctx: np.ndarray):
        mM, sM, mX, sX, pinfo = self._base.params(ctx)
        scale = 1.0 / np.sqrt(self.weight)
        return [mM, sM * scale, mX, sX * scale, pinfo]


def trust_weight(validity: ChannelValidity, *, floor: float = 0.0) -> float:
    """Map a channel's honest real-data balanced accuracy to a trust weight in [0, 1]: chance (0.5) -> 0,
    perfect (1.0) -> 1, linear between; a channel confidently BELOW chance (like real vav_zone channel 2) also
    maps to 0 -- inverting evidence is a different, riskier mechanism this does not attempt. Uses the POINT
    estimate, not the conservative lower bound (`real_channel_validity`'s `validated` gate already plays the
    conservative role; this weight is a best estimate for continuous scaling, not a go/no-go decision)."""
    if not np.isfinite(validity.point_bal_acc):
        return floor
    return float(np.clip(2.0 * (validity.point_bal_acc - 0.5), floor, 1.0))


def apply_trust_weights(models: dict[int, ChannelModel], validity: dict[int, ChannelValidity], *,
                         min_weight: float = MIN_WEIGHT) -> dict[int, ChannelModel]:
    """For every channel with a validity estimate: wrap it at its trust weight, or drop it entirely if that
    weight is below `min_weight` (equivalent to `exclude_k`, and avoids numerically-pointless sd inflation).
    Channels with no validity estimate at all are passed through unchanged (nothing is known to discount)."""
    out = {}
    for k, m in models.items():
        v = validity.get(k)
        if v is None:
            out[k] = m
            continue
        w = trust_weight(v)
        if w < min_weight:
            continue
        out[k] = TrustWeightedModel(m, w)
    return out
