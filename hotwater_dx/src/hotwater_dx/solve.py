"""Steady-state solve of one plant in one operating state.

States are quasi-steady: `load` 0 = idle recirculation, 1 = peak draw; `pump_on` selects circulation or stagnation (then `t_off_h` hours have
passed since the pump stopped and pipes have cooled exponentially). No time stepping: transients are closed-form exponentials.

Plant block (the "split tie" layout): the loop return and the cold makeup mix into one stream at T_cm; part of it is heated and fed to the TMV hot port,
the rest goes straight to the TMV cold port. Mass and energy are consistent at every draw including zero:
    heat required = 500 * Qs * (Ts - T_cm)         (Btu/h, gpm, F)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from .params import FIXTURE_GPM
from .plant import (CP_PER_FT, GAL_PER_FT_DEADLEG, GAL_PER_FT_RISER, PEAK_H, STORE_USABLE, STRAINER_DP0, T_USABLE_MIN, Plant, thermal_cv)

Q_MIN = 0.02     # gpm: below this a flow is treated as zero
FLOW_FLOOR = 0.005


@dataclass
class Solution:
    load: float
    pump_on: bool
    t_off_h: float
    converged: bool = True
    iters: int = 0
    energy_residual: float = 0.0     # relative enthalpy imbalance of the loop (0 when not applicable)
    flow_residual: float = 0.0       # relative hydraulic imbalance (parallel-path heads, pump head)
    Qd: float = 0.0
    Qp: float = 0.0                  # sum of riser branch flows (recirculation)
    Qs: float = 0.0
    head: float = 0.0                # pump head, ft
    q: list[float] = field(default_factory=list)
    c: list[float] = field(default_factory=list)         # crossover cold inflow per riser, gpm
    dp_valve: list[float] = field(default_factory=list)  # psi across each balancing valve
    Ts: float = 0.0                  # TMV outlet
    T_H_out: float = 0.0             # actual heater outlet
    T_tank_top: float = 0.0
    T_hot_in: float = 0.0
    T_cm: float = 0.0
    margin: float = 0.0
    tmv_regime: str = ""
    T_E: list[float] = field(default_factory=list)       # temperature at the top of each supply riser
    T_ret_i: list[float] = field(default_factory=list)   # return temperature of each riser as read at the riser base
    T_ret: float = 0.0               # principal return at the plant
    amps_ratio: float = 0.0
    head_ratio: float = 0.0
    p_static: float = 0.0
    p_dynamic: float = 0.0
    strainer_dp: float = 0.0
    t_hot_s: list[float] = field(default_factory=list)   # time-to-hot at the fixture at the top of each riser, s
    T_fix: list[float] = field(default_factory=list)     # hot temperature delivered at each riser-top fixture (cold leaking into the valve lowers it)
    pump_cmd_mismatch: bool = False


# ------------------------------------------------------------------------------------------------ hydraulics
def _riser_cv(P: Plant, i: int, t_ret_i: float) -> float:
    cv = thermal_cv(t_ret_i, P.t_vset) if P.thermal else P.cv[i]
    return max(cv * P.cv_mult[i], 1e-6)


def _riser_k(P: Plant, i: int, t_ret_i: float) -> float:
    cv = _riser_cv(P, i, t_ret_i)
    return P.k_pipe[i] + 2.31 / (cv * cv)


def hydraulics(P: Plant, Qd: float, t_ret_i: list[float]) -> tuple[list[float], float, float]:
    """Flow split and pump operating point in closed form. Returns (riser flows, pump head ft, total recirculation flow gpm).

    Parallel risers share one head h_b: q_i = sqrt(h_b / K_i). The pump curve H(Q) = H0 - b Q^2 meets the system curve
    K_sm (Q + Qd)^2 + K_rm Q^2 + h_b, with h_b = (Q / S)^2 and S = sum 1/sqrt(K_i): a quadratic in Q.
    """
    if P.pump_head_mult <= 0.0 or P.pump_speed <= 0.0:
        return [0.0] * P.n, 0.0, 0.0
    ks = [_riser_k(P, i, t_ret_i[i]) for i in range(P.n)]
    S = sum(1.0 / math.sqrt(k) for k in ks)
    qd_tot = P.design_total
    Hd = P.h_design * P.pump_oversize * P.pump_head_mult
    H0 = 1.25 * Hd * P.pump_speed ** 2        # shut-off head (affinity law: head ~ speed^2)
    b = 0.25 * Hd / (qd_tot * qd_tot)         # curve passes through (Q_d, Hd) at full speed
    A = b + P.k_rm + P.k_sm + 1.0 / (S * S)
    B = 2.0 * P.k_sm * Qd
    C = P.k_sm * Qd * Qd - H0
    disc = B * B - 4.0 * A * C
    if disc <= 0.0 or H0 <= 0.0:
        return [0.0] * P.n, 0.0, 0.0
    Q = max((-B + math.sqrt(disc)) / (2.0 * A), 0.0)
    h_b = (Q / S) ** 2
    q = [math.sqrt(h_b / k) for k in ks]
    return q, H0 - b * Q * Q, Q


# ------------------------------------------------------------------------------------------------ plant block
def _plant_block(P: Plant, Qr: float, Qd: float, sum_c: float, T_ret: float, load: float):
    """TMV, heater and mixing at the plant. Returns (Qs, Ts, T_H_out, T_hot_in, T_cm, margin, regime, T_tank_top)."""
    M = Qd - sum_c
    Qm = max(M, 0.0)
    Qx = max(-M, 0.0)                      # excess cold inflow at fixtures is relieved before the heater
    Qr_eff = max(Qr - Qx, 0.0)
    Qs = max(Qr_eff + Qm, 1e-6)
    T_cm = (Qr_eff * T_ret + Qm * P.t_cold) / Qs
    th_pre = P.t_set_heater - 0.5 * P.deadband             # tank-top water temperature
    th_eff = (1.0 - P.dip_frac) * th_pre + P.dip_frac * T_cm
    t_set_eff = P.t_set_tmv + P.tmv_drift
    store_rel = P.storage_gal * 8.33 * STORE_USABLE * max(th_pre - T_USABLE_MIN, 0.0) / PEAK_H if load > 0 else 0.0
    avail = P.heater_cap * P.cap_eff + store_rel
    d_th = max(th_eff - T_cm, 1e-6)
    f_h = max((t_set_eff - T_cm) / d_th, 0.0)
    f_port = P.tmv_hot_frac
    f_heat = avail / (500.0 * Qs * d_th)
    f_lim = min(1.0, f_port, f_heat)
    in_control = f_h <= f_lim + 1e-9
    f_ach = min(f_h, f_lim)
    Ts = T_cm + f_ach * d_th
    margin = th_eff - t_set_eff
    if P.tmv_fixed_mix >= 0.0:
        Ts = T_cm + P.tmv_fixed_mix * d_th                             # unregulated valve (Addendum 10 mode)
    elif in_control and margin < P.tmv_margin_min:
        Ts -= P.tmv_sag_gain * (P.tmv_margin_min - max(margin, 0.0))   # SOURCE POWERS: outlet low when hot supply is below the minimum margin
    if P.tmv_min_flow > 0.0 and Qs < P.tmv_min_flow:
        Ts -= P.tmv_lowflow_droop * (1.0 - Qs / P.tmv_min_flow)         # below the valve's minimum flow (Addendum 10 mode)
    Ts += P.tmv_p_shift
    Ts = min(max(Ts, T_cm), max(th_eff, T_cm))
    if f_heat < min(1.0, f_port) and f_heat <= f_h:
        T_H_out = min(T_cm + avail / (500.0 * max(min(1.0, f_port) * Qs, 1e-6)), th_eff)
        regime = "heat_limited"
    else:
        T_H_out = th_eff
        regime = "in_control" if in_control and margin >= P.tmv_margin_min else ("margin_lost" if in_control else "hot_port_limited")
    return Qs, Ts, T_H_out, th_eff, T_cm, margin, regime, th_pre


def _tau(P: Plant, ins: float) -> float:
    """Stagnation cool-down time constant, hours: heat capacity per ft over loss per ft (PHYSICS)."""
    return CP_PER_FT / max(P.u_eff * ins, 1e-9)


# ------------------------------------------------------------------------------------------------ main solve
def solve(P: Plant, load: float, pump_on: bool = True, t_off_h: float = 0.5) -> Solution:
    n = P.n
    Qd = P.peak_draw * load
    d_i = [Qd * s for s in P.d_share]
    sol = Solution(load=load, pump_on=pump_on, t_off_h=t_off_h, Qd=Qd)
    sol.p_static = P.p_cold
    sol.p_dynamic = P.p_cold - P.p_drop_per_gpm * Qd
    t_set_eff = P.t_set_tmv + P.tmv_drift
    psi = P.psi_check
    UA_s = [P.u_eff * P.ins_mult[i] * P.L[i] for i in range(n)]    # one-way (supply or return) riser
    UA_r = UA_s
    UA_ms = P.u_eff * P.main_ins_mult * P.L_main
    UA_mr = UA_ms
    running = pump_on and P.pump_head_mult > 0 and P.pump_speed > 0

    if running:
        T_ret = t_set_eff - P.dT_design
        T_ret_i = [T_ret] * n
        converged, it = False, 0
        for it in range(1, 201):
            q, head, Qp = hydraulics(P, Qd, T_ret_i)
            qe = [q[i] * (1.0 - psi[i]) for i in range(n)]
            dp_x = P.p_hot_deficit * (1.0 + 0.04 * Qd)
            c = [P.g_x[i] * math.sqrt(max(dp_x, 0.0)) for i in range(n)]
            sum_c, sum_qe = sum(c), sum(qe)
            Qr = sum_qe + sum_c
            Qs, Ts, T_H_out, T_hot_in, T_cm, margin, regime, th_pre = _plant_block(P, Qr, Qd, sum_c, T_ret, load)
            Qs_loop = sum_qe + Qd
            T_hdr = P.t_amb + (Ts - P.t_amb) * math.exp(-UA_ms / (500.0 * max(Qs_loop, FLOW_FLOOR)))
            T_E, T_new_i, loss = [], [], 500.0 * Qs_loop * (Ts - T_hdr)
            r_tot, rt_sum = 0.0, 0.0
            for i in range(n):
                s_i = qe[i] + d_i[i]
                te = P.t_amb + (T_hdr - P.t_amb) * math.exp(-UA_s[i] / (500.0 * max(s_i, FLOW_FLOOR)))
                loss += 500.0 * s_i * (T_hdr - te)
                T_E.append(te)
                r_i = qe[i] + c[i]
                t_ri = (qe[i] * te + c[i] * P.t_cold) / r_i if r_i > 1e-9 else te
                tret = P.t_amb + (t_ri - P.t_amb) * math.exp(-UA_r[i] / (500.0 * max(r_i, FLOW_FLOOR)))
                loss += 500.0 * r_i * (t_ri - tret)
                if psi[i] > 0:
                    tret = psi[i] * T_ret + (1.0 - psi[i]) * tret   # a stuck-open check valve: the riser base reads return-header water
                T_new_i.append(tret)
                r_tot += r_i
                rt_sum += r_i * tret
            t_mix = rt_sum / r_tot if r_tot > 1e-9 else T_ret
            T_ret_new = P.t_amb + (t_mix - P.t_amb) * math.exp(-UA_mr / (500.0 * max(r_tot, FLOW_FLOOR)))
            loss += 500.0 * r_tot * (t_mix - T_ret_new)
            err = abs(T_ret_new - T_ret)
            T_ret_prev = T_ret
            w = 0.25 if P.thermal else 0.5     # thermal balancing valves feed back on temperature: damp harder
            T_ret = (1 - w) * T_ret + w * T_ret_new
            T_ret_i = [(1 - w) * a + w * b for a, b in zip(T_ret_i, T_new_i)]
            if err < 0.005 and it > 2:
                converged = True
                break
        # residual diagnostics at the converged state (use the unmixed return so the stuck-check masking does not count as an energy error)
        in_flux = 500.0 * Qs_loop * Ts + 500.0 * sum_c * P.t_cold
        out_flux = loss + 500.0 * sum(d_i[i] * T_E[i] for i in range(n)) + 500.0 * r_tot * T_ret_new
        sol.energy_residual = abs(in_flux - out_flux) / max(in_flux, 1.0) if not any(x > 0 for x in psi) else 0.0
        ks = [_riser_k(P, i, T_ret_i[i]) for i in range(n)]
        hb = [ks[i] * q[i] ** 2 for i in range(n)]
        hmean = sum(hb) / n if n else 0.0
        sol.flow_residual = (max(abs(x - hmean) for x in hb) / hmean) if hmean > 1e-9 else 0.0
        sol.q, sol.c, sol.Qp, sol.Qs, sol.head = q, c, Qp, Qs_loop, head
        sol.Ts, sol.T_H_out, sol.T_hot_in, sol.T_cm, sol.margin, sol.tmv_regime, sol.T_tank_top = Ts, T_H_out, T_hot_in, T_cm, margin, regime, th_pre
        sol.T_E, sol.T_ret_i, sol.T_ret = T_E, T_ret_i, T_ret
        sol.dp_valve = [(q[i] / _riser_cv(P, i, T_ret_i[i])) ** 2 for i in range(n)]
        sol.head_ratio = P.pump_head_mult * P.pump_speed ** 2
        sol.amps_ratio = P.amps_mult * P.pump_speed ** 3 * (0.5 + 0.5 * (Qp / P.design_total) * (head / max(P.h_design, 1e-9)))
        sol.converged, sol.iters = converged, it
    else:
        # stagnation (pump off or dead), with draws at peak: no recirculation
        Qs, Ts, T_H_out, T_hot_in, T_cm, margin, regime, th_pre = _plant_block(P, 0.0, Qd, 0.0, P.t_cold, load)
        Ts_stag = Ts if Qd > Q_MIN else min(t_set_eff, max(T_hot_in, P.t_cold))
        T_hdr = P.t_amb + (Ts - P.t_amb) * math.exp(-UA_ms / (500.0 * max(Qs, FLOW_FLOOR)))
        T_E, T_ret_i = [], []
        for i in range(n):
            if d_i[i] > Q_MIN:
                te = P.t_amb + (T_hdr - P.t_amb) * math.exp(-UA_s[i] / (500.0 * d_i[i]))
            else:
                te = P.t_amb + (Ts_stag - P.t_amb) * math.exp(-t_off_h / _tau(P, P.ins_mult[i]))
            T_E.append(te)
            T_ret_i.append(P.t_amb + (Ts_stag - P.t_amb) * math.exp(-t_off_h / _tau(P, P.ins_mult[i])))
        sol.q, sol.c, sol.Qs = [0.0] * n, [0.0] * n, Qd
        sol.Ts, sol.T_H_out, sol.T_hot_in, sol.T_cm, sol.margin, sol.tmv_regime, sol.T_tank_top = Ts, T_H_out, T_hot_in, T_cm, margin, regime, th_pre
        sol.T_E, sol.T_ret_i = T_E, T_ret_i
        sol.T_ret = P.t_amb + (Ts_stag - P.t_amb) * math.exp(-t_off_h / _tau(P, P.main_ins_mult))
        sol.dp_valve = [0.0] * n
        sol.head_ratio = P.pump_head_mult * P.pump_speed ** 2
        sol.converged = True

    sol.strainer_dp = STRAINER_DP0 * P.strainer_mult * (max(sol.Qs, 0.0) / max(P.peak_draw, 1e-6)) ** 2
    sol.pump_cmd_mismatch = P.control_state != "normal"
    sol.T_fix = [sol.T_E[i] - (sol.c[i] / FIXTURE_GPM) * (sol.T_E[i] - P.t_cold) for i in range(n)]
    # time-to-hot at the fixture at the top of each riser: ~2x the cold volume must flow (SOURCE KLEIN); the riser counts if it is not hot
    sol.t_hot_s = []
    for i in range(n):
        v_cold = P.deadleg_ft * GAL_PER_FT_DEADLEG
        if sol.T_E[i] < 105.0:
            v_cold += P.L[i] * GAL_PER_FT_RISER
        sol.t_hot_s.append(60.0 * 2.0 * v_cold / (FIXTURE_GPM * max(P.fixture_mult[i], 0.05)))
    return sol


def spot(P: Plant, load: float, rng: np.random.Generator) -> Solution:
    """What a technician sees when they happen to arrive: the pump is running with probability `duty`, else it has been off for a while."""
    run_p = P.duty if (P.pump_head_mult > 0 and P.pump_speed > 0) else 0.0
    if rng.random() < run_p:
        return solve(P, load, True)
    lo, hi = P.off_range
    return solve(P, load, False, float(rng.uniform(lo, hi)))


def reference_states(P: Plant) -> tuple[Solution, Solution]:
    """Representative idle and peak solutions for the complaint gate: pump on if it can run and mostly should, else off at the middle of its off range."""
    on = P.pump_head_mult > 0 and P.pump_speed > 0 and P.control_state in ("normal", "vfd_hand")
    t_off = 0.5 * sum(P.off_range)
    return solve(P, 0.0, on, t_off), solve(P, 1.0, on, t_off)


def has_complaint(P: Plant) -> bool:
    """Does this plant produce the symptom family (lukewarm / slow / uneven)? Same thresholds for every cause (frozen in PREREGISTRATION.md)."""
    idle, peak = reference_states(P)
    t_low = P.t_set_tmv - 12.0
    if max(idle.t_hot_s) > 30.0:
        return True
    if min(idle.T_fix) < t_low or peak.Ts < t_low:
        return True
    return max(idle.T_fix) - min(idle.T_fix) > 8.0 and min(idle.T_fix) < P.t_set_tmv - 6.0
