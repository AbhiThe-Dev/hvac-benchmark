"""The cause library: 17 causes, each a pure change to a commissioned `Plant`.

Consolidated from the 25 rows of research_notes/Hot water recirculation diagnostic inputs/cause_taxonomy.md (the consolidation map is CONSOLIDATION,
and what was dropped and why is DROPPED). Severity `sev` runs from 0 (neutral: `apply` returns an identical plant) up to 1 (the worst modelled);
each cause draws its severity from `sev_range`, so a sampled fault is never trivially small. Mode and location are drawn too.

Every effect size is ANALYST/PLACEHOLDER (the notes found no published severity distributions); mechanisms are from the cited sources.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .plant import Plant
from .provenance import PROV
from .sources import SOURCES


@dataclass(frozen=True)
class CauseSpec:
    id: str
    group: str                      # A plant, B mixing valve, C recirculation hydraulics, D crossover/pressure, E fixture, G controls
    label: str
    detail: str
    taxonomy_rows: tuple[int, ...]
    modes: tuple[str, ...]
    sev_range: tuple[float, float]
    draw_extra: Callable[[np.random.Generator, Plant, str], dict]   # extra draws (riser index, ...)
    apply_fn: Callable[[Plant, str, float, dict], None]              # mutates a copy
    refs: tuple[str, ...] = ()
    source: str = "PLACEHOLDER"      # provenance of the effect sizes
    requires_dynamics: bool = False  # the real fault has time-dependent behaviour the steady model cannot show

    def draw(self, rng: np.random.Generator, P: Plant) -> dict:
        mode = self.modes[int(rng.integers(len(self.modes)))]
        sev = float(rng.uniform(*self.sev_range))
        return {"mode": mode, "sev": sev, **self.draw_extra(rng, P, mode)}

    def apply(self, P: Plant, draw: dict) -> Plant:
        Q = P.copy()
        if draw["sev"] > 0.0:             # severity 0 is neutral by definition: an identical plant
            self.apply_fn(Q, draw["mode"], draw["sev"], draw)
        return Q


def _none(rng, P, mode):
    return {}


def _riser(rng, P, mode, weights=None):
    n = P.n
    p = np.asarray(weights if weights is not None else [1.0] * n, dtype=float)
    return {"riser": int(rng.choice(n, p=p / p.sum()))}


def _risers_many(rng, P, mode):
    k = int(rng.integers(1, 4))
    return {"risers": [int(x) for x in rng.choice(P.n, size=k, replace=False)]}


# --------------------------------------------------------------------------------------------- apply functions
def _setpoint_low(Q, mode, sev, d):
    Q.t_set_heater -= 30.0 * sev
    Q.t_set_display = Q.t_set_heater          # the controller truthfully shows the (wrong) set point


def _output_loss(Q, mode, sev, d):
    Q.cap_eff = 1.0 - 0.8 * sev


def _sensor_offset(Q, mode, sev, d):
    Q.t_set_heater = Q.t_set_display - 25.0 * sev   # the controller believes the display set point; the water is colder


def _dip_tube(Q, mode, sev, d):
    Q.dip_frac = 0.6 * sev


def _demand(Q, mode, sev, d):
    Q.peak_draw *= 1.0 + 1.2 * sev
    Q.storage_gal *= 1.0 - 0.7 * sev


def _tmv_wrong(Q, mode, sev, d):
    if mode == "low":
        Q.tmv_drift -= 20.0 * sev
    else:                                    # "raised": set point pushed toward the heater temperature, margin lost
        Q.t_set_tmv += 15.0 * sev


def _tmv_starved(Q, mode, sev, d):
    Q.tmv_hot_frac = 1.0 - 0.85 * sev
    Q.strainer_mult = 1.0 + 9.0 * sev


def _pump_failed(Q, mode, sev, d):
    if mode == "dead":
        Q.pump_head_mult, Q.amps_mult = 0.0, 0.0
        Q.off_range = (2.0, 24.0)             # a dead pump has been off for hours
    elif mode == "air":
        Q.pump_head_mult = 1.0 - 0.93 * sev
        Q.amps_mult = 1.0 - 0.55 * sev
    else:                                     # wrong rotation
        Q.pump_head_mult = 1.0 - 0.75 * sev
        Q.amps_mult = 1.0 - 0.35 * sev


def _pump_control(Q, mode, sev, d):
    if mode == "timer_off":
        Q.control_state, Q.duty, Q.off_range = "timer_off", 0.05, (1.0, 10.0)
    elif mode == "reversed":
        Q.control_state, Q.duty, Q.off_range = "reversed", 0.03, (2.0, 24.0)
    else:                                     # "vfd_hand": drive stuck in hand at high speed, runs continuously
        Q.control_state, Q.duty, Q.pump_speed = "vfd_hand", 1.0, 1.0 + 0.35 * sev


def _pump_under(Q, mode, sev, d):
    Q.pump_head_mult = 1.0 - 0.65 * sev


def _check_valve(Q, mode, sev, d):
    for j in d["risers"]:
        Q.psi_check[j] = 0.95 * sev


def _balancing(Q, mode, sev, d):
    j = d["riser"]
    Q.cv_mult[j] = 1.0 - 0.95 * sev


def _isolation(Q, mode, sev, d):
    if mode == "riser":
        Q.cv_mult[d["riser"]] = max(1.0 - sev, 0.002)
    else:                                     # main isolation valve partly closed
        Q.k_rm *= 1.0 + 400.0 * sev


def _fixture_local(Q, mode, sev, d):
    j = d["riser"]
    if mode == "deadleg":
        Q.deadleg_ft += 40.0 * sev
    else:
        Q.fixture_mult[j] = 1.0 - 0.8 * sev


def _insulation(Q, mode, sev, d):
    if mode == "all":
        Q.u_eff *= 1.0 + 1.0 * sev
    elif mode == "one_riser":
        Q.ins_mult[d["riser"]] = 1.0 + 3.5 * sev
    else:
        Q.main_ins_mult = 1.0 + 3.5 * sev


def _crossover(Q, mode, sev, d):
    for j in d["risers"]:
        Q.g_x[j] = 0.02 + 0.13 * sev
    Q.p_hot_deficit *= 1.0 + 0.5 * sev


def _cold_pressure(Q, mode, sev, d):
    Q.p_cold *= 1.0 - 0.5 * sev
    Q.p_drop_per_gpm *= 1.0 + 3.0 * sev
    Q.tmv_p_shift = d.get("sign", 1.0) * 6.0 * sev


def _draw_sign(rng, P, mode):
    return {"sign": float(rng.choice([-1.0, 1.0]))}


def _draw_risers_far(rng, P, mode):
    return _risers_many(rng, P, mode)


def _riser_far_biased(rng, P, mode):
    return _riser(rng, P, mode, weights=[1, 1, 1.5, 2])


def _riser_any(rng, P, mode):
    return _riser(rng, P, mode)


def _check_valve_draw(rng, P, mode):
    k = int(rng.integers(1, 3))
    return {"risers": [int(x) for x in rng.choice(P.n, size=k, replace=False)]}


CAUSES: tuple[CauseSpec, ...] = (
    CauseSpec("heater_setpoint_low", "A", "Heater set point too low (including Legionella-motivated lowering or an energy setback)",
              "Thermostat set 10-30 F below normal; the controller truthfully shows the low value", (1, 23), ("low",), (0.35, 1.0), _none, _setpoint_low, ("CDC", "VHA1061")),
    CauseSpec("heater_output_loss", "A", "Heater output loss (element or burner failure, HX scale, lockout)",
              "Delivered capacity 20-100% lower; matters most when load is high", (2,), ("element", "burner", "scale"), (0.2, 1.0), _none, _output_loss, ("BED15",)),
    CauseSpec("plant_sensor_offset", "A", "Plant sensor / aquastat fault (controller believes it is at set point, water is colder)",
              "Actual heater set point 8-25 F below the displayed one", (3,), ("sensor",), (0.3, 1.0), _none, _sensor_offset, ()),
    CauseSpec("dip_tube_short_circuit", "A", "Dip-tube failure / stratification short-circuit",
              "A share of the cold inlet bypasses to the outlet", (4,), ("dip_tube",), (0.25, 1.0), _none, _dip_tube, ("HILLER",)),
    CauseSpec("demand_exceeds_capacity", "A", "Demand exceeds capacity / storage undersized",
              "Peak draw 30-120% higher and storage 25-70% smaller than the plant was sized for", (5,), ("demand",), (0.25, 1.0), _none, _demand, ()),
    CauseSpec("tmv_setpoint_wrong", "B", "Mixing valve set too low, drifted, or hot-supply margin lost",
              "Low: valve outlet 5-20 F under its set point. Raised: set point pushed toward the heater temperature so the 15-25 F margin is lost",
              (6, 8, 23), ("low", "margin_lost"), (0.25, 1.0), _none, _tmv_wrong, ("POWERS",)),
    CauseSpec("tmv_starved_fouled", "B", "Mixing valve fouled: liming on checkstops, clogged strainer (hot port starved)",
              "Hot port passes 15-70% of the loop flow; strainer drop up to ~10x", (7,), ("liming", "strainer"), (0.3, 1.0), _none, _tmv_starved, ("POWERS",)),
    CauseSpec("pump_failed", "C", "Recirculation pump failed, air-bound, or running the wrong way",
              "Dead (no flow), air-bound (head ~5-30%), wrong rotation (head ~25-50%)", (9,), ("dead", "air", "wrong_rotation"), (0.6, 1.0), _none, _pump_failed, ("BED15", "HABITAT")),
    CauseSpec("pump_control_fault", "C", "Pump control fault: timer or schedule off, aquastat reversed, drive stuck in hand",
              "Pump commanded off most of the time (or run flat out); the cause is in the controls, not the pump", (10, 22), ("timer_off", "reversed", "vfd_hand"), (0.5, 1.0), _none, _pump_control, ("HABITAT",)),
    CauseSpec("pump_undersized", "C", "Pump under-sized or worn (low head)",
              "Head 35-65% lower than needed", (11,), ("undersized",), (0.35, 1.0), _none, _pump_under, ("BOCK",)),
    CauseSpec("check_valve_failure", "C", "Return check valve stuck open / missing / reversed on one or two risers",
              "Riser base reads return-header water; the riser top is starved", (12,), ("stuck_open",), (0.2, 1.0), _check_valve_draw, _check_valve, ("COOP",)),
    CauseSpec("balancing_valve_misset", "C", "Balancing valve closed, mis-set or scaled on one riser",
              "Valve Cv 5-60% of commissioned; the riser is starved while others over-flow", (13,), ("closed", "scaled"), (0.4, 1.0), _riser_far_biased, _balancing, ("PGE24", "BOCK")),
    CauseSpec("isolation_valve_closed", "C", "Isolation valve closed (a riser) or partly closed (the main)",
              "Riser path essentially shut, or return main restricted so total flow collapses", (14,), ("riser", "main"), (0.5, 1.0), _riser_any, _isolation, ()),
    CauseSpec("fixture_branch_local", "E", "Fixture-level problem: long dead leg, restrictor, worn cartridge or stop on one riser's fixture",
              "Only the fixture at the top of one riser is slow or weak; the loop itself is healthy", (15, 21), ("deadleg", "restrictor"), (0.4, 1.0), _riser_any, _fixture_local, ("KLEIN", "PNNL21")),
    CauseSpec("insulation_loss", "C", "Insulation loss: wet, missing, or gaps on all piping, one riser, or the main",
              "Heat loss 1.35-2x higher everywhere, or 2-4.5x on one riser or the main", (16,), ("all", "one_riser", "main"), (0.35, 1.0), _riser_any, _insulation, ("ETCC", "BPA22")),
    CauseSpec("crossover", "D", "Hot/cold crossover through worn fixture cartridges or failed check stops",
              "Cold water enters the hot loop at one to three risers; the return cools and the heater load rises", (18,), ("cartridge",), (0.2, 1.0), _risers_many, _crossover, ("AYALA16", "COOP"), requires_dynamics=False),
    CauseSpec("cold_pressure_problem", "D", "Low or unstable cold-side pressure / PRV problem",
              "Static pressure 15-50% low, larger dynamic drop under draw, and a TMV outlet shift of unknown sign", (19,), ("pressure",), (0.3, 1.0), _draw_sign, _cold_pressure, ("POWERS",), requires_dynamics=True),
)

BY_ID = {c.id: c for c in CAUSES}
IDS = tuple(c.id for c in CAUSES)
NORMAL = "normal"

# which taxonomy rows (cause_taxonomy.md matrix) each cause covers; rows 17 (erosion), 20, 24, 25 are DROPPED
CONSOLIDATION = {c.id: c.taxonomy_rows for c in CAUSES}
DROPPED = {
    17: "flow velocity / erosion-corrosion / pinhole leaks: slow degradation with no steady 'not hot' signature in v0",
    20: "closed-system thermal expansion / expansion tank: no hot-water-temperature signature (pressure/relief symptoms)",
    24: "heat-pump water heater defrost / lockout / swing-tank misconfiguration: a different plant archetype (A5), not modelled",
    25: "solar / preheat bypass or staging: a different plant archetype (A6), not modelled",
}

# Pairs where the research notes report an interaction (multi-fault support). kind: MASKS / CONFOUNDS / COMPOUNDS / CAUSES / CHAINED / CONFOUNDED_CHANGE
INTERACTIONS: tuple[dict, ...] = (
    dict(a="crossover", b="pump_control_fault", kind="CAUSES", note="crossover cools the return, staff bypass the aquastat or raise set points", src="AYALA16"),
    dict(a="crossover", b="balancing_valve_misset", kind="CONFOUNDS", note="imbalance and crossover look alike", src="COOP"),
    dict(a="crossover", b="check_valve_failure", kind="CONFOUNDS", note="both let cold or return water into the wrong place", src="COOP"),
    dict(a="heater_setpoint_low", b="tmv_setpoint_wrong", kind="CHAINED", note="a lower heater set point eats the hot-supply margin the TMV needs", src="POWERS"),
    dict(a="heater_output_loss", b="tmv_setpoint_wrong", kind="CHAINED", note="lost capacity drops the hot supply toward the TMV set point", src="POWERS"),
    dict(a="pump_failed", b="pump_control_fault", kind="CONFOUNDS", note="a pump that never starts: the pump or its controls? (Brooklyn case)", src="HABITAT"),
    dict(a="balancing_valve_misset", b="isolation_valve_closed", kind="CONFOUNDS", note="one starved riser either way", src="BOCK"),
    dict(a="dip_tube_short_circuit", b="heater_output_loss", kind="CONFOUNDS", note="both lower the hot supply", src=""),
    dict(a="tmv_starved_fouled", b="cold_pressure_problem", kind="CONFOUNDS", note="both give an unstable or low TMV outlet", src="POWERS"),
    dict(a="tmv_setpoint_wrong", b="pump_control_fault", kind="CONFOUNDED_CHANGE", note="a new TMV plus a new aquastat: two changes, one complaint", src="HABITAT"),
    dict(a="fixture_branch_local", b="crossover", kind="CONFOUNDS", note="a worn cartridge is both a local and a crossover fault", src="AYALA16"),
)


def validate() -> list[str]:
    problems = []
    ids = [c.id for c in CAUSES]
    if len(set(ids)) != len(ids):
        problems.append("duplicate cause ids")
    for c in CAUSES:
        if c.source != "PLACEHOLDER" and c.source not in PROV:
            problems.append(f"{c.id}: bad source tag {c.source}")
        if not c.modes:
            problems.append(f"{c.id}: no modes")
        lo, hi = c.sev_range
        if not (0.0 < lo < hi <= 1.0):
            problems.append(f"{c.id}: bad sev_range {c.sev_range}")
        for r in c.refs:
            if r not in SOURCES:
                problems.append(f"{c.id}: unknown ref {r}")
    for it in INTERACTIONS:
        for k in ("a", "b"):
            if it[k] not in BY_ID:
                problems.append(f"interaction names unknown cause {it[k]}")
        if it["src"] and it["src"] not in SOURCES:
            problems.append(f"interaction unknown source {it['src']}")
    covered = {r for c in CAUSES for r in c.taxonomy_rows} | set(DROPPED)
    missing = [r for r in range(1, 26) if r not in covered]
    if missing:
        problems.append(f"taxonomy rows unaccounted for: {missing}")
    return problems


assert not validate(), validate()
