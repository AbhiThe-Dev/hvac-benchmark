"""Data-grounded sensor / telemetry corruption layer for simulated HVAC evidence (numpy only).

`draw_profile(stats, rng, level)` draws ONE building's sensor/telemetry parameters (a `SensorProfile`);
`apply(truth, profile, rng)` turns hourly truth series (keys "NODE|signal", signals as in docmismatch.evidence) into what a BAS export would log.

Levels
  legacy    : EXACTLY the noise hard-coded in docmismatch.evidence.make_evidence (temp sd 0.25 K, flow x N(1,0.02), power x N(1,0.03)+N(0,0.002*(max|x|+1)),
              BAS 'value' points sd 0.30 K + per-sensor static offset sd 0.15 K); no quantisation / dropout / stale / drift / jitter.
  estimated : parameters ESTIMATED from the real ORNL FRP DEV files (results/docmismatch/dr/sensor_stats.json; scripts/23_sensor_stats.py), one draw of each
              parameter within its bootstrap CI per building.  Notes: the lab logger is far cleaner than the legacy assumption (temperature white noise ~0.02 K,
              quantum 0.0056 K, no stale runs, ~no dropouts) so this level is EASIER than legacy on noise; what it adds is per-sensor offsets/drift proxies.
  wide      : estimated x lognormal(sd 0.5) inflation factors, sub-hour variability switched on (proxy), 2-3x missingness/stale/drift rates floored by ASSUMED
              field priors, coarse quantisation, jitter/lag and optional distractor faults, for robustness training.

Every parameter not identified by the data is listed in `SensorProfile.assumed` (and flagged assumed=True in sensor_stats.json).
Parameters that are only PROXIES (offset sd, drift, sub-hour variability) are listed in `SensorProfile.proxy`.
Units: temperature-like classes ("temp", "value") additive in K; "flow"/"power" multiplicative (relative) so they are unit-free.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ..evidence import FLOW_SIGNALS, POWER_SIGNALS, TEMP_SIGNALS

STATS_PATH = Path(__file__).resolve().parents[4] / "results" / "docmismatch" / "dr" / "sensor_stats.json"
CLASSES = ("temp", "value", "flow", "power")
LEVELS = ("legacy", "estimated", "wide")


def load_stats(path: Path | str | None = None) -> dict:
    return json.load(open(path or STATS_PATH))


def signal_class(sig: str) -> str | None:
    if sig in TEMP_SIGNALS:
        return "temp"
    if sig in FLOW_SIGNALS:
        return "flow"
    if sig in POWER_SIGNALS or sig in ("htg", "clg"):
        return "power"
    if sig == "value":
        return "value"
    return None


def _z4() -> dict:
    return {c: 0.0 for c in CLASSES}


@dataclass
class SensorProfile:
    level: str = "legacy"
    # white measurement noise: K (temp, value) or relative (flow, power)
    noise_sd: dict = field(default_factory=_z4)
    power_abs_frac: float = 0.0            # additive power floor sd as a fraction of (max|x|+1)
    subhour_sd: dict = field(default_factory=_z4)   # extra sample-to-sample variability of instantaneous vs hourly-line truth (proxy)
    sensor_noise_sdlog: float = 0.0        # per-sensor lognormal multiplier on noise (sensor heterogeneity)
    quant: dict = field(default_factory=_z4)        # step: K for temp/value, fraction of series max|truth| for flow/power (0 = none)
    offset_sd: dict = field(default_factory=_z4)    # per-(window, sensor) static additive offset sd, K (temp, value)
    gain_sd: dict = field(default_factory=_z4)      # per-(window, sensor) static relative gain error sd (flow, power)
    drift_lin_sd: dict = field(default_factory=_z4)  # linear drift: sd of the total drift accumulated over 90 days (K or relative)
    drift_rw_sd: dict = field(default_factory=_z4)   # random-walk drift: sd of the walk after 90 days
    dropout_frac: float = 0.0              # fraction of samples NaN (random dropouts)
    dropout_run_mean_h: float = 1.0        # geometric mean run length, hours
    stale_frac: float = 0.0                # fraction of samples inside stale (repeat-previous) runs
    stale_run_mean_h: float = 6.0
    jitter_min: float = 0.0                # sd of per-sample timestamp error, minutes
    lag_min: float = 0.0                   # per-sensor constant lag ~ U(-lag_min, +lag_min) minutes
    distractors: list = field(default_factory=list)  # [{"kind": "step"|"stuck"|"spike", "prob": per-sensor prob, "mag_K"/"mag_rel", "len_h"}]
    assumed: tuple = ()                    # parameters NOT identified by data (priors)
    proxy: tuple = ()                      # parameters only supported by a proxy in the data
    docs: dict = field(default_factory=dict)


# ------------------------------------------------------------------------------------------------ profile drawing
def legacy_profile() -> SensorProfile:
    return SensorProfile(
        level="legacy",
        noise_sd={"temp": 0.25, "value": 0.30, "flow": 0.02, "power": 0.03},
        power_abs_frac=0.002,
        offset_sd={"temp": 0.0, "value": 0.15, "flow": 0.0, "power": 0.0},
        docs={"all": "hard-coded values of docmismatch.evidence.make_evidence; no data grounding"},
    )


def _ci_draw(e: dict, rng: np.random.Generator) -> float:
    """one draw within the bootstrap CI (normal with sd=(hi-lo)/3.92, clipped to the CI); point estimate if no CI"""
    est, ci = e["est"], e.get("ci95")
    if not ci or ci[0] is None or ci[1] is None or ci[1] <= ci[0]:
        return float(est)
    return float(np.clip(rng.normal(est, (ci[1] - ci[0]) / 3.92), ci[0], ci[1]))


def _loguni(lo: float, hi: float, rng) -> float:
    lo = max(lo, 1e-9)
    return float(np.exp(rng.uniform(np.log(lo), np.log(hi))))


def draw_profile(stats: dict, rng: np.random.Generator, level: str = "estimated") -> SensorProfile:
    if level not in LEVELS:
        raise ValueError(level)
    if level == "legacy":
        return legacy_profile()
    P = stats["profile_inputs"]
    wide = level == "wide"
    infl = (lambda: float(np.exp(rng.normal(0.0, 0.5)))) if wide else (lambda: 1.0)
    rate_k = (lambda: float(rng.uniform(2.0, 3.0))) if wide else (lambda: 1.0)
    pr = SensorProfile(level=level)
    for c in CLASSES:
        pr.noise_sd[c] = _ci_draw(P["noise_sd"][c], rng) * infl()
        pr.quant[c] = _ci_draw(P["quant"][c], rng)
        if wide:  # assumed prior: coarse BAS point resolution (0.1 K-ish / 1% of range) as the upper end
            pr.quant[c] = _loguni(pr.quant[c], 0.1 if c in ("temp", "value") else 0.01, rng)
    pr.power_abs_frac = _ci_draw(P["power_abs_frac"], rng) * infl()
    pr.sensor_noise_sdlog = float(stats["noise_heterogeneity"]["room_temp"]["sd_log"])
    if wide:
        pr.sensor_noise_sdlog *= 1.5
        for c in CLASSES:  # sub-hour variability (proxy): instantaneous hourly samples vs the hourly line
            pr.subhour_sd[c] = _ci_draw(P["subhour_sd"][c], rng) * infl()
    # static offsets (proxy): temp uses the cleaner VAV-SAT proxy (transfer, assumed); the room-temp spread is only used at the wide level as an upper bound
    ov, ot = P["offset_sd_K"]["value"], P["offset_sd_K"]["temp"]
    pr.offset_sd["value"] = _ci_draw(ov, rng) * infl()
    pr.offset_sd["temp"] = (_ci_draw(ot, rng) if wide else _ci_draw(ov, rng)) * infl()
    if wide:  # gain errors on flow/power: not estimable, assumed prior
        pr.gain_sd["flow"], pr.gain_sd["power"] = _loguni(0.005, 0.03, rng), _loguni(0.005, 0.03, rng)
    # drift (proxy + assumed): per 90 days
    dr, dl, du = P["drift_K_per_90d"]["random_walk_sd"], P["drift_K_per_90d"]["linear_sd"], P["drift_K_per_90d"]["room_upper"]
    base_rw = _ci_draw(dr, rng) if not wide else _loguni(dr["est"], du["est"], rng)
    for c in ("temp", "value"):
        pr.drift_rw_sd[c] = base_rw * infl() * (rate_k() if wide else 1.0)
        pr.drift_lin_sd[c] = base_rw * 0.5 * infl() * (rate_k() if wide else 1.0)
    if wide:
        for c in ("flow", "power"):
            pr.drift_rw_sd[c], pr.drift_lin_sd[c] = _loguni(0.002, 0.02, rng), _loguni(0.002, 0.02, rng)
    # missingness / stale: data give ~0; wide adds assumed field priors
    d = P["dropout"]
    pr.dropout_frac = _ci_draw(d["frac"], rng)
    pr.dropout_run_mean_h = 1.0
    st = P["stale"]
    pr.stale_frac = _ci_draw(st["frac"], rng)
    pr.stale_run_mean_h = float(np.mean(st["field_prior_run_mean_h"]["est"]))
    if wide:
        lo, hi = d["field_prior_frac"]["est"]
        pr.dropout_frac = max(pr.dropout_frac * rate_k(), _loguni(lo, hi, rng))
        pr.dropout_run_mean_h = _loguni(*d["field_prior_run_mean_h"]["est"], rng)
        lo, hi = st["field_prior_frac"]["est"]
        pr.stale_frac = max(pr.stale_frac * rate_k(), float(rng.uniform(lo, hi)))
        pr.stale_run_mean_h = _loguni(*st["field_prior_run_mean_h"]["est"], rng)
        jm, lm = P["timestamp"]["jitter_min"]["est"], P["timestamp"]["lag_min"]["est"]
        pr.jitter_min, pr.lag_min = float(rng.uniform(*jm)), float(rng.uniform(*lm))
        pr.distractors = [{"kind": "step", "prob": 0.03, "mag_K": 0.5, "mag_rel": 0.05}, {"kind": "stuck", "prob": 0.02, "len_h": 24.0}, {"kind": "spike", "prob": 0.02, "mag_K": 3.0, "mag_rel": 0.3}]
    pr.assumed = ("gain_sd", "drift_lin_sd", "drift_rw_sd", "offset_sd[temp] (transfer of VAV-SAT proxy)", "flow noise transferred from RTU_SA_FLOW to all flow sensors")
    pr.proxy = ("offset_sd", "drift_rw_sd", "subhour_sd", "noise_sd[value] (upper bound)")
    if wide:
        pr.assumed += ("dropout_frac/run (field prior)", "stale_frac/run (field prior)", "jitter_min", "lag_min", "quant (coarse prior)", "distractors")
    else:
        pr.assumed += ("jitter_min=0 / lag_min=0 (unobservable, exact-minute stamps)",)
    pr.docs = {k: v for k, v in {
        "noise_sd": "estimated: trimmed-RMS of 2nd differences, 1-min data; temp is quantisation-limited",
        "offset_sd": "PROXY: sd across co-located sensors (VAV SAT vs box median, unheated); room spread is an upper bound",
        "drift": "PROXY+ASSUMED: rms offset change between season files scaled by sqrt(gap/90 d)",
        "dropout/stale": "estimated (~0 in this lab logger); wide floors them with ASSUMED field priors",
        "quant": "estimated: 0.01 degF, 2.77 W, 1 cfm",
    }.items()}
    return pr


# ------------------------------------------------------------------------------------------------ apply
def _runs_mask(n: int, frac: float, mean_len: float, rng: np.random.Generator) -> np.ndarray:
    """boolean mask with ~frac of samples in runs of geometric length (mean `mean_len` samples, >=1)"""
    m = np.zeros(n, bool)
    if frac <= 0 or n == 0:
        return m
    mean_len = max(float(mean_len), 1.0)
    p_start = min(frac / mean_len, 1.0)
    starts = np.flatnonzero(rng.random(n) < p_start)
    if len(starts):
        lens = rng.geometric(1.0 / mean_len, len(starts))
        for s, L in zip(starts, lens):
            m[s:s + L] = True
    return m


def _locf(y: np.ndarray, bad: np.ndarray) -> np.ndarray:
    """last-observation-carried-forward; leading bad samples take the first valid value"""
    if not bad.any():
        return y
    if bad.all():
        return np.where(bad, 0.0, y)
    idx = np.where(~bad, np.arange(len(y)), 0)
    np.maximum.accumulate(idx, out=idx)
    y = y[idx]
    first = np.flatnonzero(~bad)[0]
    y[:first] = y[first]
    return y


def apply_with_flags(truth: dict, profile: SensorProfile, rng: np.random.Generator, step_hours: float = 1.0, nan_out: bool = False):
    """returns (out, flags); flags[tag] = dict(dropout=bool mask, stale=bool mask, distractor=bool mask, offset=float, lag_h=float).
    With nan_out=False dropouts are filled by LOCF (so `out` is finite) but flags['dropout'] still marks them."""
    p = profile
    out, flags = {}, {}
    for tag, x0 in truth.items():
        sig = tag.split("|")[-1]
        cls = signal_class(sig)
        x0 = np.asarray(x0, float)
        n = len(x0)
        if cls is None:
            out[tag] = x0.copy()
            flags[tag] = dict(dropout=np.zeros(n, bool), stale=np.zeros(n, bool), distractor=np.zeros(n, bool), offset=0.0, lag_h=0.0)
            continue
        t = np.arange(n) * step_hours
        x = x0
        lag_h = 0.0
        if p.lag_min > 0 or p.jitter_min > 0:  # sub-hour timing: interpolate the hourly truth at shifted times
            lag_h = rng.uniform(-p.lag_min, p.lag_min) / 60.0 if p.lag_min > 0 else 0.0
            sh = lag_h + (rng.normal(0.0, p.jitter_min / 60.0, n) if p.jitter_min > 0 else 0.0)
            x = np.interp(t + sh, t, x0)
        mult = float(np.exp(rng.normal(0.0, p.sensor_noise_sdlog))) if p.sensor_noise_sdlog > 0 else 1.0
        sd, sub = p.noise_sd[cls] * mult, p.subhour_sd[cls]
        tot = float(np.hypot(sd, sub))
        off = 0.0
        if cls in ("temp", "value"):
            y = x + rng.normal(0.0, tot, n) if tot > 0 else x.copy()
            if p.offset_sd[cls] > 0:
                off = float(rng.normal(0.0, p.offset_sd[cls]))
                y = y + off
            if p.drift_lin_sd[cls] > 0 or p.drift_rw_sd[cls] > 0:
                days = t / 24.0
                d = rng.normal(0.0, p.drift_lin_sd[cls]) * days / 90.0
                if p.drift_rw_sd[cls] > 0:
                    step = p.drift_rw_sd[cls] * np.sqrt(step_hours / (90.0 * 24.0))
                    d = d + np.cumsum(rng.normal(0.0, step, n))
                y = y + d
        else:
            y = x * (1.0 + rng.normal(0.0, tot, n)) if tot > 0 else x.copy()
            if cls == "power" and p.power_abs_frac > 0:
                y = y + rng.normal(0.0, p.power_abs_frac * (np.abs(x0).max() + 1.0), n)
            if p.gain_sd[cls] > 0:
                off = float(rng.normal(0.0, p.gain_sd[cls]))
                y = y * (1.0 + off)
            if p.drift_lin_sd[cls] > 0 or p.drift_rw_sd[cls] > 0:
                days = t / 24.0
                d = rng.normal(0.0, p.drift_lin_sd[cls]) * days / 90.0
                if p.drift_rw_sd[cls] > 0:
                    d = d + np.cumsum(rng.normal(0.0, p.drift_rw_sd[cls] * np.sqrt(step_hours / (90.0 * 24.0)), n))
                y = y * (1.0 + d)
        # distractor faults (assumed, wide only)
        dist = np.zeros(n, bool)
        for dspec in p.distractors:
            if n and rng.random() < dspec["prob"]:
                i0 = int(rng.integers(0, n))
                if dspec["kind"] == "step":
                    mag = dspec.get("mag_K", 0.5) if cls in ("temp", "value") else dspec.get("mag_rel", 0.05)
                    s = rng.choice([-1.0, 1.0]) * mag
                    y = y + s * (np.arange(n) >= i0) if cls in ("temp", "value") else y * (1.0 + s * (np.arange(n) >= i0))
                    dist[i0:] = True
                elif dspec["kind"] == "stuck":
                    L = max(int(round(dspec.get("len_h", 24.0) / step_hours)), 2)
                    y[i0:i0 + L] = y[i0]
                    dist[i0:i0 + L] = True
                elif dspec["kind"] == "spike":
                    mag = dspec.get("mag_K", 3.0) if cls in ("temp", "value") else dspec.get("mag_rel", 0.3)
                    y[i0] = y[i0] + rng.choice([-1.0, 1.0]) * mag if cls in ("temp", "value") else y[i0] * (1.0 + rng.choice([-1.0, 1.0]) * mag)
                    dist[i0] = True
        # quantisation
        q = p.quant[cls]
        if q > 0:
            step = q if cls in ("temp", "value") else q * (np.abs(x0).max() + 1e-12)
            if step > 0:
                y = np.round(y / step) * step
        # stale runs: repeat the previous output value
        stale = _runs_mask(n, p.stale_frac, p.stale_run_mean_h / step_hours, rng)
        if stale.any():
            stale[0] = False
            for s in np.flatnonzero(stale & ~np.r_[False, stale[:-1]]):  # run starts
                e = s
                while e < n and stale[e]:
                    e += 1
                y[s:e] = y[s - 1]
        # random dropouts
        drop = _runs_mask(n, p.dropout_frac, p.dropout_run_mean_h / step_hours, rng)
        if nan_out:
            y = np.where(drop, np.nan, y)
        else:
            y = _locf(y, drop)
        out[tag] = y
        flags[tag] = dict(dropout=drop, stale=stale, distractor=dist, offset=off, lag_h=lag_h)
    return out, flags


def apply(truth: dict, profile: SensorProfile, rng: np.random.Generator, step_hours: float = 1.0, nan_out: bool = False) -> dict:
    return apply_with_flags(truth, profile, rng, step_hours, nan_out)[0]
