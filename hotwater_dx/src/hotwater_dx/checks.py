"""The check library: 23 checks (20 physical/readout checks + 3 zero-cost questions), each with a measured feature, a tool error model, a location,
a time estimate and a safety class.

Time and safety are ANALYST estimates (`minutes_source`): practitioners rarely publish durations (research_notes/.../check_catalogue.md section 4).
`location` is kept so a later engine can charge travel time: MR mechanical room, RS riser, FX fixture, BAS remote, INT interview/question.
A check with `physics_readable=False` is decided by elicitation, not by this model (cells for `relevant` causes are NEEDS-ELICITATION by rule).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from . import measurement as M
from .plant import Plant
from .solve import Solution, solve


# ------------------------------------------------------------------------------------------------ per-plant cache
class Ctx:
    """Solutions of one plant, computed once, from which noisy spot readings are drawn."""

    def __init__(self, P: Plant):
        self.P = P
        self.runnable = P.pump_head_mult > 0 and P.pump_speed > 0
        lo, hi = P.off_range
        self.grid = [lo + (hi - lo) * x for x in (0.0, 0.25, 0.5, 0.75, 1.0)]
        self.idle_on = solve(P, 0.0, True) if self.runnable else None
        self.peak_on = solve(P, 1.0, True) if self.runnable else None
        self.idle_off = [solve(P, 0.0, False, t) for t in self.grid]
        self.peak_off = solve(P, 1.0, False, 0.5 * (lo + hi))

    def idle(self, rng: np.random.Generator) -> Solution:
        if self.runnable and rng.random() < self.P.duty:
            return self.idle_on
        return self.idle_off[int(rng.integers(len(self.idle_off)))]

    def peak(self, rng: np.random.Generator) -> Solution:
        if self.runnable and rng.random() < self.P.duty:
            return self.peak_on
        return self.peak_off

    def idle_running(self) -> Solution:
        """A state with the pump on if it can run (for checks that need flow), else the off state."""
        return self.idle_on if self.runnable else self.idle_off[len(self.idle_off) // 2]

    def logged_frac_below(self, floor: float) -> float:
        """Fraction of a 72 h log with the principal return below `floor`: on-phase share = duty, off-phases cool through the grid."""
        d = self.P.duty if self.runnable else 0.0
        on = 1.0 if (self.idle_on is not None and self.idle_on.T_ret < floor) else 0.0
        off = float(np.mean([s.T_ret < floor for s in self.idle_off]))
        return d * on + (1.0 - d) * off


@dataclass(frozen=True)
class CheckSpec:
    id: str
    name: str
    feature: str
    unit: str
    location: str
    tool: str
    sigma_min: float                      # resolution floor used when standardising an effect
    do_min: float                         # analyst estimate, minutes on the spot (excluding travel)
    n_points: int
    safety: str
    remote: str                           # yes | partial | no
    read: Callable[[Ctx, np.random.Generator, str], float] | None
    applies: Callable[[Plant], bool] = lambda P: True
    physics_readable: bool = True
    relevant: tuple[str, ...] = ()        # for non-physics checks: the causes the check is declared relevant to
    tools_alt: tuple[str, ...] = ()       # alternative tools to test fragility
    refs: tuple[str, ...] = ()
    minutes_source: str = "ANALYST"
    note: str = ""
    binary: bool = False                  # 0/1 reading with a misread rate: needs more repeats for a stable standardised effect


def _T(x, tool, P, rng):
    return M.temp(x, tool, P.t_amb, rng)


# ------------------------------------------------------------------------------------------------ readers
def r_heater_outlet(c: Ctx, rng, tool):
    return _T(c.idle(rng).T_H_out, tool, c.P, rng)


def r_tank_vs_outlet(c: Ctx, rng, tool):
    s = c.idle(rng)
    a, b = M.temp_pair(s.T_tank_top, s.T_H_out, tool, c.P.t_amb, rng)
    return a - b


def r_tmv_out_vs_set(c: Ctx, rng, tool):
    s = c.peak(rng)
    return _T(s.Ts, tool, c.P, rng) - c.P.t_set_tmv


def r_return_plant(c: Ctx, rng, tool):
    return _T(c.idle(rng).T_ret, tool, c.P, rng)


def r_riser_min_return(c: Ctx, rng, tool):
    s = c.idle(rng)
    return min(_T(t, tool, c.P, rng) for t in s.T_ret_i)


def r_loop_dT(c: Ctx, rng, tool):
    s = c.idle(rng)
    a, b = M.temp_pair(s.Ts, s.T_ret, tool, c.P.t_amb, rng)
    return a - b


def r_pump_amps(c: Ctx, rng, tool):
    """The technician forces the pump on (hand switch) before reading amps, so a pump that is merely in its off-cycle or commanded off still reads normal."""
    return M.amps(c.idle_running().amps_ratio, rng)


def r_pump_head(c: Ctx, rng, tool):
    return M.amps(c.idle_running().head_ratio, rng) if c.runnable else rng.normal(0.0, 0.05)


def r_controls_readout(c: Ctx, rng, tool):
    return M.flip(1.0 if c.P.control_state != "normal" else 0.0, rng, 0.05)


def r_display_vs_reference(c: Ctx, rng, tool):
    return (c.P.t_set_display - c.P.t_set_heater) + rng.normal(0.0, 0.7)


def r_thermal_wells(c: Ctx, rng, tool):
    s = c.idle(rng)
    return min(_T(t, tool, c.P, rng) for t in s.T_ret_i) - c.P.t_vset


def r_balancing_flow(c: Ctx, rng, tool):
    s = c.idle_running()
    ratios = [q / qd for q, qd in zip(s.q, c.P.q_design)]
    return min(ratios) * (1.0 + rng.normal(0.0, 0.10)) if c.runnable else rng.normal(0.0, 0.03)


def r_strainer_dp(c: Ctx, rng, tool):
    return M.gauge(c.peak(rng).strainer_dp, rng, 0.25)


def r_plant_pressure(c: Ctx, rng, tool):
    return M.gauge(c.peak(rng).p_dynamic, rng, 1.0)


def r_time_to_hot(c: Ctx, rng, tool):
    return M.stopwatch(max(c.idle(rng).t_hot_s), rng)


def r_crossover_isolation(c: Ctx, rng, tool):
    return sum(c.idle_running().c) + rng.normal(0.0, 0.04)


def r_eatherton(c: Ctx, rng, tool):
    return max(c.idle_running().c) + rng.normal(0.0, 0.05)


def r_return_logger(c: Ctx, rng, tool):
    return c.logged_frac_below(c.P.t_min_circ) + rng.normal(0.0, 0.03)


def r_q_scope(c: Ctx, rng, tool):
    s = c.idle(rng)
    n = sum(1 for t in s.T_fix if t < c.P.t_set_tmv - 8.0)
    if rng.random() < 0.15:                                   # tenants over- or under-report which floors are affected
        n = max(0, min(c.P.n, n + int(rng.choice([-1, 1]))))
    return float(n)


def r_q_peak_only(c: Ctx, rng, tool):
    return (c.idle(rng).Ts - c.peak(rng).Ts) + rng.normal(0.0, 1.5)


def r_q_warm_cold(c: Ctx, rng, tool):
    return sum(c.idle_running().c) + rng.normal(0.0, 0.05)


_thermal = lambda P: P.thermal
_fixed = lambda P: not P.thermal

CHECKS: tuple[CheckSpec, ...] = (
    CheckSpec("K01", "Heater outlet temperature", "heater outlet T", "F", "MR", "clamp", 0.5, 10, 1, "scald", "partial", r_heater_outlet, tools_alt=("ir",), refs=("VHA1061",)),
    CheckSpec("K02", "Tank-top thermowell vs outlet pipe", "T_top - T_outlet", "F", "MR", "probe", 0.5, 15, 2, "scald", "partial", r_tank_vs_outlet, refs=("HILLER",)),
    CheckSpec("K03", "TMV outlet vs its set point (at peak)", "T_out - T_set", "F", "MR", "clamp", 0.5, 10, 1, "scald", "partial", r_tmv_out_vs_set, tools_alt=("ir",), refs=("POWERS", "WATTS_ASSE")),
    CheckSpec("K04", "TMV cold-supply isolation (thermal shutdown) test", "outlet flow after cold isolated", "-", "MR", "observe", 1.0, 20, 1, "isolation_lockout", "no", None, physics_readable=False,
              relevant=("tmv_starved_fouled", "tmv_setpoint_wrong"), note="needs a valve-internals model (thermal element, piston scale) that v0 does not have"),
    CheckSpec("K05", "Principal return temperature (spot)", "return T", "F", "MR", "clamp", 0.5, 5, 1, "hot_surface", "partial", r_return_plant, tools_alt=("ir", "bas"), refs=("BED15", "VHA1061")),
    CheckSpec("K06", "Coolest riser-base return temperature (riser walk)", "min riser return T", "F", "RS", "clamp", 0.5, 20, 4, "hot_surface", "no", r_riser_min_return, tools_alt=("ir",), refs=("BED15",)),
    CheckSpec("K07", "Loop dT (TMV outlet minus principal return)", "Ts - T_ret", "F", "MR", "clamp", 0.5, 10, 2, "hot_surface", "partial", r_loop_dT, refs=("CALEFFI",)),
    CheckSpec("K08", "Pump amps vs nameplate / rotation", "I / I_expected", "-", "MR", "amps", 0.03, 10, 1, "electrical", "partial", r_pump_amps),
    CheckSpec("K09", "Pump head vs curve", "head / curve", "-", "MR", "gauge", 0.05, 20, 2, "pressure", "no", r_pump_head),
    CheckSpec("K10", "Pump controls read-out (command / schedule / aquastat polarity)", "command differs from expected", "0/1", "MR", "readout", 0.1, 5, 1, "electrical", "yes", r_controls_readout, refs=("HABITAT",), binary=True),
    CheckSpec("K11", "Heater controller display vs reference thermometer", "display - actual set", "F", "MR", "probe", 0.7, 10, 1, "scald", "no", r_display_vs_reference),
    CheckSpec("K12", "Thermal balancing valve wells vs valve set point", "T_valve - T_set", "F", "RS", "probe", 0.5, 8, 4, "hot_surface", "partial", r_thermal_wells, applies=_thermal, refs=("CALEFFI",)),
    CheckSpec("K13", "Per-riser flow from balancing-valve dP (fixed orifice)", "min q / q_design", "-", "RS", "gauge", 0.10, 8, 4, "pressure", "no", r_balancing_flow, applies=_fixed, refs=("PGE24",)),
    CheckSpec("K14", "Strainer / TMV pressure drop at peak", "dP", "psi", "MR", "gauge", 0.25, 10, 2, "pressure", "partial", r_strainer_dp, refs=("POWERS",)),
    CheckSpec("K15", "Plant dynamic pressure at peak", "P_dynamic", "psi", "MR", "gauge", 1.0, 10, 1, "pressure", "partial", r_plant_pressure),
    CheckSpec("K16", "Time to hot at the complaint fixture", "seconds to +10 F", "s", "FX", "stopwatch", 4.0, 5, 1, "scald", "no", r_time_to_hot, refs=("PNNL21", "KLEIN")),
    CheckSpec("K17", "Cold-feed-isolated crossover test (pressure rebuild / flow continues)", "cold inflow", "gpm", "MR", "observe", 0.05, 20, 1, "isolation_lockout", "no", r_crossover_isolation, refs=("AYALA16",)),
    CheckSpec("K18", "Eatherton test (valve body cools when a nearby hot tap opens)", "max fixture cold inflow", "gpm", "FX", "hand", 0.06, 15, 1, "hot_surface", "no", r_eatherton, refs=("AYALA16",)),
    CheckSpec("K19", "Return-temperature log, 72 h", "fraction of time return < floor", "-", "MR", "logger", 0.05, 60, 1, "none", "yes", r_return_logger, refs=("BED15",)),
    CheckSpec("K20", "History interview: what changed recently, when did it start", "recent change reported", "0/1", "INT", "human", 1.0, 5, 1, "none", "n/a", None, physics_readable=False,
              relevant=("heater_setpoint_low", "tmv_setpoint_wrong", "pump_control_fault", "balancing_valve_misset", "isolation_valve_closed", "check_valve_failure", "pump_failed", "plant_sensor_offset"),
              refs=("HABITAT",), note="'what changed' is the strongest published discriminator but it is a human fact, not a physical quantity"),
    CheckSpec("Q1", "Question: which floors / risers are affected", "number of risers complaining", "count", "INT", "tenant", 0.5, 1, 1, "none", "n/a", r_q_scope),
    CheckSpec("Q2", "Question: worse at peak only?", "idle outlet T - peak outlet T", "F", "INT", "tenant", 1.5, 1, 1, "none", "n/a", r_q_peak_only),
    CheckSpec("Q3", "Question: warm water from cold taps?", "cold inflow", "gpm", "INT", "tenant", 0.06, 1, 1, "none", "n/a", r_q_warm_cold, refs=("AYALA16",)),
)

BY_ID = {c.id: c for c in CHECKS}
IDS = tuple(c.id for c in CHECKS)
SAFETY = ("none", "hot_surface", "scald", "pressure", "electrical", "isolation_lockout")
LOCATIONS = ("MR", "RS", "FX", "BAS", "INT")


def validate() -> list[str]:
    from .causes import IDS as CAUSE_IDS
    from .sources import SOURCES
    problems = []
    ids = [c.id for c in CHECKS]
    if len(set(ids)) != len(ids):
        problems.append("duplicate check ids")
    for c in CHECKS:
        if c.safety not in SAFETY:
            problems.append(f"{c.id}: unknown safety class {c.safety}")
        if c.location not in LOCATIONS:
            problems.append(f"{c.id}: unknown location {c.location}")
        if c.physics_readable and c.read is None:
            problems.append(f"{c.id}: physics-readable check needs a reader")
        if not c.physics_readable and not c.relevant:
            problems.append(f"{c.id}: non-physics check must declare relevant causes")
        for r in c.relevant:
            if r not in CAUSE_IDS:
                problems.append(f"{c.id}: unknown relevant cause {r}")
        for r in c.refs:
            if r not in SOURCES:
                problems.append(f"{c.id}: unknown ref {r}")
        if c.sigma_min <= 0:
            problems.append(f"{c.id}: sigma_min must be positive")
    return problems


assert not validate(), validate()
