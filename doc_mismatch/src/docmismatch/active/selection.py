"""Named selection/model variants for the sequential-verification runs (scripts 12 and 14 read DM_SEL).

Every option defaults to the original behaviour; a variant only switches options on, so the default runs (and their pickles) are unchanged.

  info     : informativeness model = ridge-logistic on ALL context columns (+ squares of outdoor temp and load) instead of a regression on the
             mean-shift features (which, in the OAT-only model, sees only outdoor temperature); plus ONLINE learning of the slice-level
             informativeness: whether a stream is flat / off in a slice is shared by the readings taken in it, so once one reading in a slice
             came back empty the others are predicted empty too (beta-binomial prior strength kappa = (1-ICC)/ICC estimated from the training pools).
  sp       : shared pair effect. The three channels of one candidate pair are computed from the same two streams, so a pair's random effect is
             largely common to its channels (real ORNL: cross-channel correlation 0.5-0.9). Original model: independent per-channel effects,
             so reading one pair on a second channel counted as a fresh independent look. New: one shared factor with correlation rho
             (estimated from training cells), integrated out exactly in the belief and used in the EIG's predictive.
  clip     : evaluate the context regressions at the training-range-clamped context (no linear extrapolation in outdoor temperature).
  info_sp  : info + sp                     (the headline "sel" variant)
  sel      : info + sp
"""
from __future__ import annotations

VARIANTS = {
    "": dict(fitkw={}, runkw={}, extra=()),
    "info": dict(fitkw=dict(info_mode="info", online_info=True), runkw=dict(online_info=True), extra=()),
    "sp": dict(fitkw=dict(shared_pair=True), runkw=dict(shared_pair=True), extra=()),
    "clip": dict(fitkw=dict(clip_ctx=True), runkw={}, extra=()),
    "info_sp": dict(fitkw=dict(info_mode="info", online_info=True, shared_pair=True), runkw=dict(online_info=True, shared_pair=True), extra=("random_info",)),
    "info_sp_clip": dict(fitkw=dict(info_mode="info", online_info=True, shared_pair=True, clip_ctx=True), runkw=dict(online_info=True, shared_pair=True), extra=("random_info",)),
}
VARIANTS["sel"] = VARIANTS["info_sp"]
# sel + slice-member effect (common offset shared by all candidates' readings of one member in one slice; joint-Gaussian exact belief). Added in the readiness work.
VARIANTS["sel_slice"] = dict(fitkw=dict(info_mode="info", online_info=True, shared_pair=True, slice_effect=True),
                             runkw=dict(online_info=True, shared_pair=True, slice_effect=True), extra=("random_info",))


def get(name: str) -> dict:
    return VARIANTS[name]
