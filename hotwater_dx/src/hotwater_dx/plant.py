"""The concrete plant: one storage heater + master TMV + recirculation pump + 4 risers with balancing valves.

`build_plant` also *commissions* the plant: balancing valves are set so each riser gets its design flow (with a residual setting error) and the pump
is sized to the balanced design head. "Healthy" therefore means a commissioned, balanced system; faults are applied afterwards (causes.py) and never
re-commission, because re-commissioning would hide the fault.

Units: F, gpm, ft, psi, Btu/h. Head (ft) = 2.31 * psi. Quadratic hydraulics: head = K * q^2 per path (pipe friction linearised at the design flow).
"""
from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field

import numpy as np

from .params import (CV_THERMAL_MAX, CV_THERMAL_MIN, MAIN_FT, N_RISERS, Q_FLOOR_PER_RISER, RISER_BASE_FT, RISER_REL_LEN, VALVE_DROP_PSI)

HAZEN_C = 140.0
FITTING_FACTOR = 1.4          # SOURCE BOCK: fittings add 30-50% to pipe friction
CP_PER_FT = 0.30              # Btu/ft/F: water + copper in 3/4 to 1 in pipe (PHYSICS); used for stagnation cool-down
STORE_USABLE = 0.7            # usable fraction of storage during a peak (ANALYST)
PEAK_H = 0.5                  # h: storage is released over a half-hour peak (ANALYST)
T_USABLE_MIN = 100.0          # F: stored water below this is not usable (ANALYST)
GAL_PER_FT_DEADLEG = 0.025    # 3/4 in copper (PHYSICS)
GAL_PER_FT_RISER = 0.043      # 1 in copper (PHYSICS)
P_DROP_PER_GPM = 0.4          # psi of cold-side dynamic pressure lost per gpm of draw (ANALYST)
STRAINER_DP0 = 0.5            # psi across the TMV strainer at peak flow when clean (ANALYST)


def _hw_coef(d_in: float) -> float:
    """Head loss in ft per ft of pipe at 1 gpm for q**1.85 (Hazen-Williams), including fittings."""
    return FITTING_FACTOR * 2.31 * 4.52 / (HAZEN_C ** 1.85 * d_in ** 4.87)


@dataclass
class Plant:
    # environment
    t_amb: float
    t_cold: float
    p_cold: float
    p_hot_deficit: float
    # heater
    t_set_heater: float          # actual thermostat set point
    t_set_display: float         # what the controller shows
    deadband: float
    heater_cap: float
    cap_eff: float
    storage_gal: float
    dip_frac: float
    peak_draw: float             # gpm at the peak state
    # TMV
    t_set_tmv: float
    tmv_drift: float
    tmv_margin_min: float
    tmv_sag_gain: float
    tmv_hot_frac: float          # share of the loop flow the hot port can pass (1.0 = unrestricted)
    strainer_mult: float
    tmv_p_shift: float
    # geometry (per riser)
    L: list[float]
    ins_mult: list[float]
    L_main: float
    main_ins_mult: float
    u_eff: float                 # Btu/h/ft/F including the field multiplier
    deadleg_ft: float
    fixture_mult: list[float]    # restrictor / cartridge multiplier on the fixture flow at each riser top
    # hydraulics
    q_design: list[float]
    k_pipe: list[float]
    cv: list[float]              # manual valve Cv as commissioned
    cv_mult: list[float]         # fault multipliers on each riser's valve path
    thermal: bool
    t_vset: float
    k_sm: float
    k_rm: float
    h_design: float
    pump_oversize: float
    pump_head_mult: float = 1.0
    pump_speed: float = 1.0
    amps_mult: float = 1.0
    duty: float = 0.6
    t_off_max_h: float = 1.2
    off_range: tuple[float, float] = (0.1, 1.2)
    control_state: str = "normal"     # normal | timer_off | reversed | vfd_hand
    # leaks / bypass
    g_x: list[float] = field(default_factory=lambda: [0.0] * N_RISERS)
    psi_check: list[float] = field(default_factory=lambda: [0.0] * N_RISERS)
    d_share: list[float] = field(default_factory=lambda: [0.25] * N_RISERS)
    p_drop_per_gpm: float = P_DROP_PER_GPM
    # judging thresholds / design values carried with the plant
    dT_design: float = 7.5
    t_min_circ: float = 122.0
    # mixing-valve modes from the manufacturer-document study (Addendum 10); the neutral defaults change nothing
    tmv_min_flow: float = 0.0          # gpm below which the valve cannot hold its set point (0 = no such limit)
    tmv_lowflow_droop: float = 0.0     # F the outlet sags at zero flow when the valve runs below its minimum flow
    tmv_fixed_mix: float = -1.0        # >= 0: unregulated valve, hot fraction stuck at this value (failed thermal element, reversed supplies); -1 = regulated

    def copy(self) -> "Plant":
        return copy.deepcopy(self)

    @property
    def n(self) -> int:
        return len(self.L)

    @property
    def design_total(self) -> float:
        return float(sum(self.q_design))


def build_plant(d: dict[str, float], rng: np.random.Generator) -> Plant:
    """Commission a healthy plant from a parameter draw `d`. `rng` supplies the valve-setting errors and TMV drift (healthy variation)."""
    n = N_RISERS
    L = [RISER_BASE_FT * r * d["len_scale"] for r in RISER_REL_LEN]
    Lm = MAIN_FT * d["len_scale"]
    u = d["u_ins"] * d["ua_mult"]
    ts = d["t_set_tmv"]
    tr_design = ts - d["dT_design"]
    t_mean = 0.5 * (ts + tr_design) - d["t_amb"]
    loss_r = [u * 2 * Li * t_mean for Li in L]                 # supply + return of each riser
    loss_m = u * 2 * Lm * t_mean
    q_loss = sum(loss_r) + loss_m
    q_total = q_loss / (500.0 * d["dT_design"])                # SOURCE CALEFFI: Btu/h = 500 * gpm * dT
    share = [x / sum(loss_r) for x in loss_r]
    q_d = [max(Q_FLOOR_PER_RISER, s * q_total) for s in share]
    qd_sum = sum(q_d)
    k_pipe = []
    for Li, qi in zip(L, q_d):
        k_pipe.append((_hw_coef(1.0) + _hw_coef(0.75)) * Li * qi ** -0.15)
    k_sm = _hw_coef(2.0) * Lm * qd_sum ** -0.15
    k_rm = _hw_coef(1.5) * Lm * qd_sum ** -0.15
    h_b = 2.31 * VALVE_DROP_PSI
    cv = []
    for kp, qi in zip(k_pipe, q_d):
        drop_psi = max((h_b - kp * qi ** 2) / 2.31, 0.2)
        cv.append(qi / math.sqrt(drop_psi))
    err = np.clip(rng.standard_normal(n), -2, 2) * d["balance_err"]
    cv = [c * (1.0 + e) for c, e in zip(cv, err)]
    h_design = h_b + (k_sm + k_rm) * qd_sum ** 2
    # a commissioned plant respects the TMV's minimum hot-supply margin (SOURCE POWERS) as far as a 150 F heater allows
    t_heater = min(max(d["t_set_heater"], ts + d["tmv_margin_min"] + 2.0 + 0.5 * d["deadband"]), 150.0)
    # heater / peak sizing: the healthy plant can heat `peak_draw` with margin (peak_frac < 1)
    store_rel = d["storage_gal"] * 8.33 * STORE_USABLE * max(t_heater - T_USABLE_MIN, 0.0) / PEAK_H
    p_nom = d["heater_cap"] + store_rel
    peak_draw = d["peak_frac"] * p_nom / (500.0 * max(ts - d["t_cold"], 1.0))
    far = d["far_share"]
    shares = [(1 - far) / (n - 1)] * (n - 1) + [far]
    drift = float(np.clip(rng.standard_normal(), -1.5, 1.5)) / 1.5 * d["tmv_tol"] * 0.5   # healthy TMV sits within half its tolerance
    # the aquastat restarts the pump when the return has cooled ~12 F, which bounds a healthy off-phase (stagnation cool-down, PHYSICS)
    tau_h = CP_PER_FT / max(u, 1e-9)
    t_off_hi = min(d["t_off_max_h"], tau_h * math.log(max(ts - d["t_amb"], 2.0) / max(ts - 12.0 - d["t_amb"], 1.0)))
    return Plant(
        t_amb=d["t_amb"], t_cold=d["t_cold"], p_cold=d["p_cold"], p_hot_deficit=d["p_hot_deficit"],
        t_set_heater=t_heater, t_set_display=t_heater, deadband=d["deadband"], heater_cap=d["heater_cap"],
        cap_eff=1.0, storage_gal=d["storage_gal"], dip_frac=0.0, peak_draw=peak_draw,
        t_set_tmv=ts, tmv_drift=drift, tmv_margin_min=d["tmv_margin_min"], tmv_sag_gain=d["tmv_sag_gain"], tmv_hot_frac=1.0,
        strainer_mult=1.0, tmv_p_shift=0.0,
        L=L, ins_mult=[1.0] * n, L_main=Lm, main_ins_mult=1.0, u_eff=u, deadleg_ft=d["deadleg_ft"], fixture_mult=[1.0] * n,
        q_design=q_d, k_pipe=k_pipe, cv=cv, cv_mult=[1.0] * n, thermal=bool(d["valve_thermal"] >= 0.5), t_vset=tr_design - 2.0,
        k_sm=k_sm, k_rm=k_rm, h_design=h_design, pump_oversize=d["pump_oversize"],
        duty=d["duty"], t_off_max_h=d["t_off_max_h"], off_range=(0.05, t_off_hi),
        d_share=shares, dT_design=d["dT_design"], t_min_circ=d["t_min_circ"],
    )


def thermal_cv(t_ret: float, t_vset: float, band: float = 10.0) -> float:
    """Thermal balancing valve: opens when its return is below the valve set point, throttles toward the minimum Cv as it warms (CALEFFI 1164: 0.35-2.1)."""
    x = min(max((t_vset - t_ret) / band, 0.0), 1.0)
    return CV_THERMAL_MIN + (CV_THERMAL_MAX - CV_THERMAL_MIN) * x
