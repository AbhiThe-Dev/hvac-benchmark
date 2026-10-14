"""Plant parameters and their ranges. A parameter is a *range*, not a constant: the matrix is computed over draws of all of them.

Known source conflicts are encoded as parameters (t_min_circ 120 vs 124 F, dT_design 5 vs 10 F), not resolved by choosing one.
Every range carries a provenance tag; almost all geometry, valve and demand ranges are ANALYST (see provenance.py).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .provenance import PROV
from .sources import SOURCES


@dataclass(frozen=True)
class ParamSpec:
    name: str
    nominal: float
    low: float
    high: float
    unit: str
    prov: str
    source: str = ""       # key(s) in SOURCES, space separated, for SOURCE/PHYSICS
    note: str = ""
    kind: str = "uniform"  # uniform | binary (value is low if u < 0.5 else high)


PARAMS: tuple[ParamSpec, ...] = (
    # environment
    ParamSpec("t_amb", 70, 60, 75, "F", "ANALYST", note="ambient around distribution piping; BED15 lab 20 C, PGE24 rig 70 F"),
    ParamSpec("t_cold", 55, 45, 68, "F", "ANALYST", note="incoming cold water"),
    ParamSpec("p_cold", 60, 45, 80, "psi", "ANALYST", note="static cold-side pressure"),
    ParamSpec("p_hot_deficit", 2.5, 0.5, 6.0, "psi", "ANALYST", note="how far hot-side pressure sits below cold at the fixtures; drives crossover when a fixture leaks"),
    # heater / storage
    ParamSpec("t_set_heater", 145, 140, 150, "F", "SOURCE", "CDC VHA1061", "storage at least 140 F; commissioned plants are raised if needed to respect the TMV minimum margin (plant.py)"),
    ParamSpec("deadband", 3.0, 2.0, 6.0, "F", "ANALYST", note="thermostat deadband; outlet sits half a band below setpoint on average"),
    ParamSpec("heater_cap", 400_000, 250_000, 700_000, "Btu/h", "ANALYST", note="rated input x efficiency; central plant for ~40-100 apartments"),
    ParamSpec("storage_gal", 300, 120, 600, "gal", "ANALYST"),
    ParamSpec("peak_frac", 0.70, 0.50, 0.85, "-", "ANALYST", note="peak draw as a fraction of what the healthy plant can heat; <1 means the healthy plant is not capacity-limited"),
    # mixing valve
    ParamSpec("t_set_tmv", 125, 120, 130, "F", "ANALYST", note="master TMV / loop supply set point; spans 120 F scald-driven plants to 130 F plants that follow the 120-124 F return floor"),
    ParamSpec("tmv_margin_min", 20.0, 15.0, 25.0, "F", "SOURCE", "POWERS", "hot supply must be at least 15 (1430) to 25 (Hi/Lo) F above set"),
    ParamSpec("tmv_sag_gain", 0.5, 0.2, 0.8, "-", "PLACEHOLDER", note="how much the outlet sags per F of lost margin; shape is an assumption"),
    ParamSpec("tmv_tol", 3.0, 1.0, 5.0, "F", "SOURCE", "WATTS_ASSE", "ASSE 1017 outlet tolerance +-3 to +-7 F by size; healthy valves drift within +-tol"),
    # distribution geometry and thermal
    ParamSpec("len_scale", 1.0, 0.7, 1.5, "-", "ANALYST", note="scales all pipe lengths"),
    ParamSpec("u_ins", 0.12, 0.08, 0.20, "Btu/h/ft/F", "PHYSICS", note="3/4 in copper, ~1 in fiberglass, hand-computed ~0.12"),
    ParamSpec("ua_mult", 1.35, 1.0, 1.9, "-", "SOURCE", "ETCC BPA22", "field loss / ideal 1.1-2.3; Seattle 1.35 and 1.95"),
    ParamSpec("dT_design", 7.5, 5.0, 10.0, "F", "SOURCE", "CALEFFI", "design loop dT is quoted as 5 or 10 F; both used"),
    ParamSpec("t_min_circ", 122, 120, 124, "F", "SOURCE", "CDC VHA1061", "circulating floor 120 (CDC) vs 124 (VA)", kind="binary"),
    # hydraulics / balancing
    ParamSpec("valve_thermal", 0, 0, 1, "-", "ANALYST", "CALEFFI", "0 = manual fixed-orifice balancing valves, 1 = thermal balancing valves", kind="binary"),
    ParamSpec("balance_err", 0.2, 0.1, 0.3, "-", "ANALYST", note="commissioning residual: relative error on each manual valve Cv"),
    ParamSpec("pump_oversize", 1.25, 1.0, 1.8, "-", "ANALYST", note="pump head at design flow relative to the balanced design head"),
    ParamSpec("duty", 0.6, 0.25, 1.0, "-", "ANALYST", note="share of time the aquastat/timer lets a healthy pump run"),
    ParamSpec("t_off_max_h", 1.2, 0.5, 2.0, "h", "ANALYST", note="longest healthy off-phase before the aquastat restarts the pump"),
    # fixtures / draws
    ParamSpec("deadleg_ft", 8, 4, 12, "ft", "ANALYST", note="uncirculated 3/4 in branch to the far fixture"),
    ParamSpec("far_share", 0.5, 0.25, 0.8, "-", "ANALYST", note="share of the peak draw taken on the farthest riser"),
)

BY_NAME = {p.name: p for p in PARAMS}
NAMES = tuple(p.name for p in PARAMS)

# structural constants (not sampled): see PREREGISTRATION.md section 1
N_RISERS = 4
RISER_REL_LEN = (1.0, 1.6, 2.3, 3.2)   # riser lengths relative to the nearest one (ANALYST)
RISER_BASE_FT = 40.0                   # one-way length of the nearest riser (ANALYST)
MAIN_FT = 80.0                         # each of supply and return main (ANALYST)
FIXTURE_GPM = 1.5                      # far-fixture draw used by the time-to-hot test (PNNL21 table rows)
Q_FLOOR_PER_RISER = 0.25               # SOURCE PGE24: satisfactory distribution above 0.25 gpm/riser
VALVE_DROP_PSI = 1.5                   # commissioned drop across each balancing valve at design flow (ANALYST)
CV_THERMAL_MIN, CV_THERMAL_MAX = 0.35, 2.1  # SOURCE CALEFFI
CONFLICTS = {
    "t_min_circ": "circulating return floor: 120 F (CDC, ASHRAE G12 addendum b) vs 124 F (VHA 1061)",
    "dT_design": "design loop dT: 5 F vs 10 F",
}


def validate() -> list[str]:
    problems = []
    if len(set(NAMES)) != len(NAMES):
        problems.append("duplicate parameter names")
    for p in PARAMS:
        if p.prov not in PROV:
            problems.append(f"{p.name}: unknown provenance {p.prov}")
        if not (p.low <= p.nominal <= p.high):
            problems.append(f"{p.name}: nominal outside [low, high]")
        if p.prov in ("SOURCE", "PHYSICS") and p.prov == "SOURCE" and not p.source:
            problems.append(f"{p.name}: SOURCE provenance needs source keys")
        for key in p.source.split():
            if key not in SOURCES:
                problems.append(f"{p.name}: unknown source key {key}")
    return problems


assert not validate(), validate()


def design_from_unit(u: np.ndarray) -> dict[str, float]:
    """Map a unit-cube vector (len == len(PARAMS)) to a parameter dict."""
    out = {}
    for x, p in zip(u, PARAMS):
        out[p.name] = (p.low if x < 0.5 else p.high) if p.kind == "binary" else p.low + float(x) * (p.high - p.low)
    return out


def nominal_design() -> dict[str, float]:
    return {p.name: float(p.nominal) for p in PARAMS}
