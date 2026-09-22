"""Physical evidence: noisy BAS-like signals, and per-connection consistency errors.

`make_evidence` turns the *true* simulated series of a base topology into what a
BAS would log (sensor noise, per-sensor calibration offsets) for one 6-week
window. Nothing here depends on the documentation: clean and corrupted
documentation of the same building share identical evidence.

`slot_errors` scores every candidate (owner, member) pair of a connection slot
with three consistency errors (lower = more consistent with physics):
  channel 0: level match      - do the two ends agree on a shared quantity?
  channel 1: dynamics         - do their time series co-move?
  channel 2: conservation     - energy / flow balance or duty-cycle agreement
The set-level flow-closure statistics used for AHUs and loops live in
`closure_residual`.
"""

from __future__ import annotations

import numpy as np

from .data import HOURS_PER_WINDOW, Base, window_slice

CP_AIR = 1006.0
CP_WATER = 4180.0
EPS = 1e-9

TEMP_SIGNALS = {"sat", "mat", "t_in", "t_out", "t_dis", "temp", "t_sup", "t_ret", "t_air_out", "oat"}
FLOW_SIGNALS = {"flow"}
POWER_SIGNALS = {"rate", "rate_s", "kw", "reheat"}
SENSOR_NOISE_K = 0.30
SENSOR_OFFSET_K = 0.15


def window_truth(base: Base, window: int) -> dict[str, np.ndarray]:
    """window-sliced TRUE series plus the aggregate AHU htg/clg meters (sum of the AHU's true coils)."""
    sl = window_slice(window)
    truth = {k: v[sl].copy() for k, v in base.ev.items()}
    for ahu in base.ids("AHU"):
        for name, brick in (("htg", "Heating_Coil"), ("clg", "Cooling_Coil")):
            tot = np.zeros(HOURS_PER_WINDOW)
            for o, m in base.slot_edges.get("coil_ahu", []):
                if o == ahu and base.nodes[m]["brick_type"] == brick:
                    sig = "rate_s" if brick == "Cooling_Coil" and f"{m}|rate_s" in truth else "rate"
                    tot += truth[f"{m}|{sig}"]
            truth[f"{ahu}|{name}"] = tot
    return truth


def make_evidence(base: Base, window: int, seed: int, sensor: dict | None = None) -> dict[str, np.ndarray]:
    """window-sliced, noisy series keyed "NODE|signal", plus aggregate AHU htg/clg meters.
    sensor=None: the original hard-coded BAS noise (unchanged). sensor=dict(level, profile_seed, distractors): the data-grounded telemetry layer of `dr/`."""
    if sensor is not None:
        from .dr.evidence_dr import make_evidence_dr
        return make_evidence_dr(base, window, seed, sensor)
    rng = np.random.default_rng(seed)
    truth = window_truth(base, window)
    ev = {}
    for tag, x in truth.items():
        node, sig = tag.split("|")
        if sig in TEMP_SIGNALS:
            y = x + rng.normal(0, 0.25, x.shape)
        elif sig in FLOW_SIGNALS:
            y = x * rng.normal(1.0, 0.02, x.shape)
        elif sig in POWER_SIGNALS or sig in ("htg", "clg"):
            y = x * rng.normal(1.0, 0.03, x.shape) + rng.normal(0, 0.002 * (np.abs(x).max() + 1), x.shape)
        elif sig == "value":  # BAS sensor points
            y = x + rng.normal(0, SENSOR_NOISE_K, x.shape) + rng.normal(0, SENSOR_OFFSET_K)
        else:
            y = x
        ev[tag] = y
    return ev


# ---- channel validity (fix for "constant channel scored as if it carried signal") --------------
# A correlation / duty-cycle channel is only meaningful if every series feeding it varies by
# more than the measurement noise. E.g. a constant-volume terminal's flow is one value all year,
# so after noise its "flow" is pure noise and any correlation with it is meaningless.
import os

VARIATION_K = 2.0  # signal sd must exceed ~1.7x the noise sd (4.0 flagged legitimately-varying VAV flows as constant)
MASK_CHANNELS = os.environ.get("DM_MASKCH", "1") == "1"
NEEDS: dict[str, dict[int, list[tuple[str, str]]]] = {
    "ahu_vav": {1: [("m", "flow"), ("o", "flow")]},
    "vav_zone": {0: [("o", "flow"), ("m", "temp")], 1: [("o", "t_dis"), ("m", "temp")], 2: [("o", "flow"), ("o", "t_dis"), ("m", "temp")]},
    "loop_branch": {1: [("m", "flow"), ("o", "flow")]},
    "branch_coil": {1: [("o", "flow"), ("m", "rate")], 2: [("o", "flow"), ("m", "rate")]},
    "loop_pump": {0: [("m", "flow"), ("o", "flow")], 2: [("m", "kw"), ("o", "flow")]},
    "loop_source": {2: [("m", "rate"), ("o", "flow")]},
    # coil load prediction is flow*cp*dT: it varies with dT even when flow is constant, so only the coil's own rate must vary
    "coil_ahu": {1: [("m", "rate")], 2: [("m", "rate")]},
    "coil_vav": {1: [("m", "rate")], 2: [("m", "rate")]},
    "ahu_sat": {1: [("m", "value")]},
    "vav_dat": {1: [("m", "value")]},
}


def _noise_sd(sig: str, x: np.ndarray) -> float:
    if sig in TEMP_SIGNALS:
        return 0.25
    if sig in FLOW_SIGNALS:
        return 0.02 * abs(float(x.mean()))
    if sig in POWER_SIGNALS or sig in ("htg", "clg"):
        return 0.03 * abs(float(x.mean())) + 0.002 * (float(np.abs(x).max()) + 1.0)
    if sig == "value":
        return SENSOR_NOISE_K
    return 0.0


def informative(ev: dict, node: str, sig: str, sl: slice = slice(None)) -> bool:
    x = ev[f"{node}|{sig}"][sl]
    return bool(x.std() > VARIATION_K * _noise_sd(sig, x))


def _corr(a: np.ndarray, b: np.ndarray) -> float:
    a = a - a.mean()
    b = b - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d > EPS else 0.0


def _duty(x: np.ndarray) -> float:
    thr = 0.02 * np.abs(x).max() + EPS
    return float((np.abs(x) > thr).mean())


def _rel(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.abs(a - b).mean() / (np.abs(a).mean() + np.abs(b).mean() + EPS))


def _ahu_pred_sat(ev, ahu, sl):
    flow = np.maximum(ev[f"{ahu}|flow"][sl], 1e-3)
    return ev[f"{ahu}|mat"][sl] + (ev[f"{ahu}|htg"][sl] - ev[f"{ahu}|clg"][sl]) / (flow * CP_AIR)


def _vav_pred_dat(ev, vav, sl):
    flow = np.maximum(ev[f"{vav}|flow"][sl], 1e-3)
    reheat = ev.get(f"{vav}|reheat")
    heat = reheat[sl] if reheat is not None else 0.0
    return ev[f"{vav}|t_in"][sl] + heat / (flow * CP_AIR)


def _z(x: np.ndarray) -> np.ndarray:
    return (x - x.mean()) / (x.std() + 1e-9)


def make_context(base: Base, ev: dict[str, np.ndarray], sl: slice = slice(None)) -> dict:
    """Building-wide common-mode signals (fleet means of z-scored series) over `sl`.
    VAV<->zone evidence removes them: every zone follows the weather, so only the
    zone-specific residual says which box serves which zone."""
    vavs, zones = base.ids("VAV"), base.ids("Zone")
    return {
        "Fm": np.mean([_z(ev[f"{v}|flow"][sl]) for v in vavs], axis=0) if vavs else 0.0,
        "Dm": np.mean([_z(ev[f"{v}|t_dis"][sl]) for v in vavs], axis=0) if vavs else 0.0,
        "Tm": np.mean([_z(ev[f"{z}|temp"][sl]) for z in zones], axis=0) if zones else 0.0,
    }


def pair_errors(base: Base, ev: dict[str, np.ndarray], slot: str, o: str, m: str, sl: slice = slice(None), ctx: dict | None = None,
                mask_uninformative: bool | None = None) -> tuple[float, float, float]:
    """Three consistency errors; a channel whose inputs are constant-within-noise is returned as NaN (missing)."""
    e = _pair_errors(base, ev, slot, o, m, sl, ctx)
    if mask_uninformative is None:
        mask_uninformative = MASK_CHANNELS
    if not mask_uninformative:
        return e
    out = list(e)
    for ch, needs in NEEDS.get(slot, {}).items():
        if not all(informative(ev, (o if who == "o" else m), sig, sl) for who, sig in needs):
            out[ch] = float("nan")
    return tuple(out)


def _pair_errors(base: Base, ev: dict[str, np.ndarray], slot: str, o: str, m: str, sl: slice = slice(None), ctx: dict | None = None) -> tuple[float, float, float]:
    g = lambda n, s: ev[f"{n}|{s}"][sl]  # noqa: E731
    if slot == "ahu_vav":
        e0 = float(np.abs(g(m, "t_in") - g(o, "sat")).mean())
        e1 = 1.0 - _corr(g(m, "flow"), g(o, "flow"))
        e2 = float(np.maximum(0.0, g(m, "flow") - 1.05 * g(o, "flow")).mean() / (g(m, "flow").mean() + EPS))
    elif slot == "vav_zone":
        q = g(o, "flow") * CP_AIR * (g(o, "t_dis") - g(m, "temp"))
        dT = np.diff(g(m, "temp"), append=g(m, "temp")[-1])
        assert ctx is not None
        tres = _z(g(m, "temp")) - ctx["Tm"]
        e0 = 1.0 - _corr(_z(g(o, "flow")) - ctx["Fm"], tres)
        e1 = 1.0 - abs(_corr(_z(g(o, "t_dis")) - ctx["Dm"], tres))
        e2 = 1.0 - abs(_corr(q, dT))
    elif slot == "loop_branch":
        e0 = float(np.abs(g(m, "t_in") - g(o, "t_sup")).mean())
        e1 = 1.0 - _corr(g(m, "flow"), g(o, "flow"))
        e2 = float(np.maximum(0.0, g(m, "flow") - 1.05 * g(o, "flow")).mean() / (g(m, "flow").mean() + EPS))
    elif slot == "branch_coil":
        rate = g(m, "rate")
        qw = g(o, "flow") * CP_WATER * np.abs(g(o, "t_in") - g(o, "t_out"))
        e0 = _rel(qw, rate)
        e1 = 1.0 - _corr(g(o, "flow"), rate)
        e2 = abs(_duty(g(o, "flow")) - _duty(rate))
    elif slot == "loop_pump":
        e0 = 1.0 - _corr(g(m, "flow"), g(o, "flow"))
        e1 = float(np.abs(g(m, "flow") - g(o, "flow")).mean() / (g(o, "flow").mean() + EPS))
        e2 = 1.0 - _corr(g(m, "kw"), g(o, "flow"))
    elif slot == "loop_source":
        ql = g(o, "flow") * CP_WATER * np.abs(g(o, "t_sup") - g(o, "t_ret"))
        e0 = float(np.abs(g(m, "t_out") - g(o, "t_sup")).mean())
        e1 = _rel(np.abs(g(m, "rate")), ql)
        e2 = 1.0 - _corr(np.abs(g(m, "rate")), ql)
    elif slot == "coil_ahu":
        flow = g(o, "flow")
        dT = g(o, "sat") - g(o, "mat")
        heating = base.nodes[m]["brick_type"] == "Heating_Coil"
        x = np.maximum(0.0, flow * CP_AIR * (dT if heating else -dT))
        rate = g(m, "rate_s") if (not heating and f"{m}|rate_s" in ev) else g(m, "rate")
        e0 = _rel(rate, x)
        e1 = 1.0 - _corr(rate, x)
        e2 = abs(_duty(rate) - _duty(x))
    elif slot == "coil_vav":
        x = np.maximum(0.0, g(o, "flow") * CP_AIR * (g(o, "t_dis") - g(o, "t_in")))
        rate = g(m, "rate")
        e0 = _rel(rate, x)
        e1 = 1.0 - _corr(rate, x)
        e2 = abs(_duty(rate) - _duty(x))
    elif slot in ("ahu_sat", "vav_dat"):
        pred = _ahu_pred_sat(ev, o, sl) if slot == "ahu_sat" else _vav_pred_dat(ev, o, sl)
        s = g(m, "value")
        e0 = float(np.abs(s - pred).mean())
        e1 = 1.0 - _corr(s, pred)
        e2 = float(abs(s.mean() - pred.mean()))
    else:
        return (0.0, 0.0, 0.0)
    return (e0, e1, e2)


def closure_residual(ev, owner: str, members: list[str], sl: slice = slice(None), slot: str = "ahu_vav") -> float:
    """Set-level conservation error of an owner against its documented members.
    ahu_vav: AHU supply flow vs sum of VAV flows (exact mass balance).
    loop_branch: loop demand-side heat (flow*cp*|Tsup-Tret|) vs sum of branch heat.
    (Flow alone is confounded by the demand-side bypass; heat is not, because a
    bypass adds flow at zero delta-T.)"""
    if slot == "ahu_vav":
        f = ev[f"{owner}|flow"][sl]
        tot = np.zeros_like(f)
        for mm in members:
            tot = tot + ev[f"{mm}|flow"][sl]
    else:
        f = ev[f"{owner}|flow"][sl] * CP_WATER * np.abs(ev[f"{owner}|t_sup"][sl] - ev[f"{owner}|t_ret"][sl])
        tot = np.zeros_like(f)
        for mm in members:
            tot = tot + ev[f"{mm}|flow"][sl] * CP_WATER * np.abs(ev[f"{mm}|t_in"][sl] - ev[f"{mm}|t_out"][sl])
    return float(np.abs(f - tot).mean() / (f.mean() + EPS))


CLOSURE_SLOTS = ("ahu_vav", "loop_branch")
