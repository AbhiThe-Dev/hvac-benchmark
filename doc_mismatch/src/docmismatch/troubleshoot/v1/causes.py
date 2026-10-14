"""The cause tree for a VAV-zone complaint ("the room is not getting the right airflow or temperature"), working model v1.

A cause is a tuple whose first element is its id, like v0's: `("wrong", j)` (the documented box is wrong; the real one is candidate j), `("unlisted",)`, and one leaf id per
hardware / configuration cause below, e.g. `("actuator_fail",)`. The causes are treated as mutually exclusive (one first-order cause per call-out), as in v0.

STRUCTURE comes from two guides (SOURCES): the branches and their members follow the failure lists in ControlsHub sections 3.1, 4.1, 5.1, 6.1, 7.1 and 8 and the PNNL maintenance checklist.
NUMBERS (`share` = the cause's share of its lump's prior mass) are PLACEHOLDERS. Neither guide gives failure frequencies.

Each leaf belongs to one of v0's two "documented box is right" lumps, so v1 is a refinement of v0's prior: with the defaults, the leaves of `doc_acts_fail` add up to v0's
P(acts-fail) and the leaves of `doc_other` to the rest, and collapsing the leaves gives v0's prior back (tested). `lump` also says how v0's four checks treat the leaf.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .. import model as M

SOURCES = {
    "PNNL": ("PNNL, Variable Air Volume (VAV) Systems: Operations & Maintenance Guide (O&M Best Practices), maintenance checklist and performance monitoring",
             "https://www.pnnl.gov/projects/om-best-practices/variable-air-volume-systems"),
    "CH": ("ControlsHub, VAV Box Airflow Problems: Complete Troubleshooting Guide (a vendor blog: its numbers are its own, not independently verified here)",
           "https://controlshub.tech/en/blog/66-vav-box-airflow-problems/"),
    "PNNL_RTU": ("PNNL-23790, Rooftop Unit Embedded Diagnostics: Automated Fault Detection and Diagnostics (AFDD) Development, Field Testing and Validation "
                 "(AFDD1: is the outdoor-air damper modulating; AFDD3: does the RTU economize when it should, from mixed/outdoor/return-air temperatures and the damper command)",
                 "https://www.pnnl.gov/main/publications/external/technical_reports/PNNL-23790.pdf"),
    "T24": ("California Title 24, Part 6, Section 120.2(i) and JA6.3: mandatory economizer fault detection and diagnostics on new commercial unitary AC/HP systems above 4.5 tons, "
            "naming 'not economizing when it should' and 'damper not modulating' among the faults it must detect",
            "http://title24stakeholders.com/economizer-fault-detection-diagnostics-fdd-requirements/"),
    "CEC_ECON": ("California Energy Commission / Western Cooling Efficiency Center case study, citing New Buildings Institute (2003): 64% of surveyed economizers have some fault; "
                 "economizer damper failure ~75% probability within a 15-year equipment life, 24% efficiency penalty, only 25% probability of being caught without automated tools (75% with)",
                 "https://wcec.ucdavis.edu/wp-content/uploads/2013/07/Case-Study_FaultDetectionDiagnostics_PRINT.pdf"),
    "LBNL_FDD": ("LBNL Fault Detection and Diagnostics Data Sets: Roof Top Unit (Granderson, Lin, Chen, Casillas, LBNL; Im, Jung, ORNL; Benne, Ling, NREL; Gorthala, UConn, 2022); the "
                 "Experimental RTU set (ORNL's Flexible Research Platform, ground-truth-labeled) used here: a `bas_economizer`-style rule (occupied-hours OA damper command vs. "
                 "OA/RA temperatures, plus an empirical enable-crossover check) measured against real 'OA damper stuck' (5/10/50/100%) and 'incorrect economizer setpoint' "
                 "(+-2/4C) fault-days, 1-minute resolution, 4 seasons. Recommended by Gabe Fierro; PREREGISTRATION_DR.md, Addendum 37 follow-up, 2026-09-29",
                 "https://faultdetection.lbl.gov/data/, DOI 10.25984/1881324"),
}
SOURCES_READ = "2026-09-25"
SOURCES_READ_ECON = "2026-09-28"   # PREREGISTRATION_DR.md Addendum 37
SOURCES_READ_ECON_AFDD = "2026-09-29"   # PREREGISTRATION_DR.md Addendum 37 follow-up (real-data detection-rate calibration)

ACTS_FAIL, OTHER = "doc_acts_fail", "doc_other"        # v0's two 'documented box is right' lumps


@dataclass(frozen=True)
class CauseSpec:
    id: str
    group: str                  # branch of the tree
    lump: str                   # ACTS_FAIL (the box does not act when commanded) | OTHER
    share: float                # share of the lump's prior mass (PLACEHOLDER)
    label: str
    detail: str
    needs: str | None = None    # box feature the cause requires: "reheat" | "pressure_independent"
    refs: tuple[str, ...] = ()

    @property
    def cause(self) -> tuple:
        return (self.id,)


GROUPS = {
    "documentation": "the drawings' claim about which box serves the room is wrong (this is what v0 handles)",
    "box_mechanical": "the box's actuator, damper or linkage",
    "power_and_signal": "24 VAC power or the control signal to the actuator",
    "controls": "the VAV controller: communications, and how it is set up",
    "sensing": "the airflow (pressure) sensor",
    "zone_inputs": "what the controller is told about the room: sensor, setpoint, schedule",
    "upstream": "the air handler, its duct pressure and its economizer or discharge-air control feeding the box",
    "reheat": "heating at the box",
    "distribution": "the duct and diffuser between the box and the room",
    "capacity": "the box or room being asked for more than it can deliver",
    "other": "anything not listed",
}

CAUSES: tuple[CauseSpec, ...] = (
    CauseSpec("actuator_fail", "box_mechanical", ACTS_FAIL, 0.30, "Actuator failed or out of torque",
              "gear stripped, motor burned out, or a fail-safe driving the damper the wrong way", refs=("CH 3.1", "CH 5.1", "CH 13 Q2")),
    CauseSpec("damper_mech", "box_mechanical", ACTS_FAIL, 0.30, "Damper or linkage stuck or slipping",
              "blade stuck (corrosion, debris, ice), linkage disconnected or slipping, travel limited by a stop or a misaligned coupling, poor seals", refs=("CH 3.1", "CH 4.1", "PNNL damper, linkage")),
    CauseSpec("no_power", "power_and_signal", ACTS_FAIL, 0.15, "Actuator has no 24 VAC",
              "blown fuse, tripped breaker or failed transformer", refs=("CH 3.1", "CH 3.2 step 4")),
    CauseSpec("signal_fault", "power_and_signal", ACTS_FAIL, 0.10, "Control signal broken, shorted, inverted or the wrong range",
              "no command reaches the actuator, or it acts the wrong way (0-10 V against 2-10 V)", refs=("CH 3.1", "CH 5.1", "CH 13 Q2", "PNNL controls")),
    CauseSpec("controller_comms", "controls", ACTS_FAIL, 0.15, "VAV controller offline or faulted",
              "offline, rebooting, in a fault state or alarming, so commands do not get through", refs=("CH 3.1", "CH 3.2 step 2")),
    CauseSpec("controller_config", "controls", OTHER, 0.14, "Controller set up wrongly",
              "K-factor not the nameplate's, maximum airflow setpoint off the design value, minimum setpoint wrong, occupied and unoccupied swapped, poor loop tuning (hunting)",
              refs=("CH 4.1", "CH 5.1", "CH 6", "CH 7", "CH 9.2")),
    CauseSpec("flow_sensor", "sensing", OTHER, 0.12, "Flow sensor reads wrong",
              "clogged ports, kinked, loose or swapped (high/low) tubes, transducer offset or drift", needs="pressure_independent", refs=("CH 4.1", "CH 7.1", "PNNL airflow sensor")),
    CauseSpec("zone_sensor_setpoint", "zone_inputs", OTHER, 0.22, "Zone sensor, setpoint or schedule",
              "sensor out of calibration, setpoint or occupancy schedule or mode wrong, an occupant override", refs=("PNNL zone sensor", "PNNL performance monitoring", "CH 9.2")),
    CauseSpec("ahu_fan_off", "upstream", OTHER, 0.05, "Air handler fan off or tripped",
              "supply fan stopped, VFD tripped", refs=("CH 3.1", "CH 3.2 step 1", "CH 10")),
    CauseSpec("low_static", "upstream", OTHER, 0.12, "Duct pressure too low upstream",
              "static setpoint too low, degraded fan or belt, dirty filters, an upstream leak or blockage, many boxes calling for maximum", refs=("CH 4.1", "CH 8")),
    CauseSpec("reheat_fail", "reheat", OTHER, 0.10, "Reheat not working",
              "valve stuck or leaking, coil fouled, electric element or connections damaged, no hot water", needs="reheat", refs=("PNNL hydronic reheat", "PNNL electric reheat")),
    CauseSpec("duct_diffuser", "distribution", OTHER, 0.10, "Duct or diffuser problem between the box and the room",
              "leaks or bypass, crushed or disconnected flex duct, diffuser or balancing damper blocked or closed", refs=("CH 5.1", "PNNL duct connections")),
    CauseSpec("capacity_design", "capacity", OTHER, 0.08, "Box or room capacity problem",
              "box undersized for the room's current use, design airflow not enough, many boxes at maximum together", refs=("CH 4.1", "CH 9")),
    CauseSpec("other", "other", OTHER, 0.07, "Something else", "the residual: nothing above explains it"),
)
BY_ID = {c.id: c for c in CAUSES}
LUMPS = (OTHER, ACTS_FAIL)          # v0's order
assert len(BY_ID) == len(CAUSES) and abs(sum(c.share for c in CAUSES if c.lump == OTHER) - 1) < 1e-9 and abs(sum(c.share for c in CAUSES if c.lump == ACTS_FAIL) - 1) < 1e-9
DEFAULT_SHARES = {c.id: c.share for c in CAUSES}

# ---------------------------------------------------------------------------------------------- Addendum 37 (PREREGISTRATION_DR.md): an upstream cause NOT enrolled above.
# `share=0.0` here is a placeholder never read by default: any caller wanting this cause supplies its own share via `make_prior_v1(shares=..., extra_causes=(ECON_FAULT,))`, which
# relies on `make_prior_v1`'s own normalisation to fold it into the 'upstream' group correctly. Deliberately NOT a member of `CAUSES` / `DEFAULT_SHARES` / `BY_ID`: adding it there would
# perturb the prior of every existing session, however slightly, through `M.PRIOR_FLOOR`. `ALL_BY_ID` below is a superset that ALSO resolves it, with no effect on any existing lookup.
ECON_FAULT = CauseSpec(
    "econ_fault", "upstream", OTHER, 0.0, "Economizer not delivering free cooling when it should",
    "the outdoor-air economizer does not bring in as much free cooling as conditions allow when there is a call for cooling: a stuck-near-minimum or non-modulating damper, an "
    "actuator or linkage failure, or a wrong changeover or discharge-air setpoint, lumped as one cause the way 'low_static' already lumps several distinct mechanisms. Usually hidden "
    "because the compressor 'picks up the slack'; only in extreme cases (high load, hot weather) does it produce an actual comfort complaint (PNNL_RTU) -- not modelled here: outdoor "
    "temperature, load or time of day.",
    refs=("PNNL_RTU", "T24", "CEC_ECON"))
EXTRA_CAUSES: tuple[CauseSpec, ...] = (ECON_FAULT,)
ALL_BY_ID = {**BY_ID, **{c.id: c for c in EXTRA_CAUSES}}      # a strict superset of BY_ID: every existing lookup is unaffected; extras also resolve

# Symptom answers -> prior multipliers (PLACEHOLDERS). "airflow" is v0's question (is air coming out of the diffuser?): "no" multiplies, "yes" divides by `Settings.no_airflow_multiplier`
# the causes where the box delivers no air at all; v0 applied that to its acts-fail lump only, v1 adds the air handler being off.
AIRFLOW_SET = tuple(c.id for c in CAUSES if c.lump == ACTS_FAIL) + ("ahu_fan_off",)
FEEL_MULT = {"too_cold": {"reheat_fail": 3.0}, "too_hot": {"capacity_design": 2.0}}
SYMPTOM_VALUES = {"airflow": ("yes", "no", "unsure"), "feel": ("too_hot", "too_cold", "unsure")}


def v0_tag(cause: tuple) -> tuple:
    """The v0 cause a v1 cause collapses to: wrong / unlisted stay, the leaves become their lump, a lump stays."""
    c = cause[0]
    if c in ("wrong", "unlisted", ACTS_FAIL, OTHER):
        return cause
    return (ALL_BY_ID[c].lump,)


def leaf_causes(reheat: bool | None = True, pressure_independent: bool = True, extra: tuple[CauseSpec, ...] = ()) -> list[CauseSpec]:
    """The leaves that can exist for this box. `reheat=False` removes reheat_fail; `pressure_independent=False` removes flow_sensor; `None` (unknown) keeps them.
    `extra` (Addendum 37): additional leaves not in `CAUSES`, e.g. `(ECON_FAULT,)`; empty by default, so every existing caller is unaffected."""
    return [c for c in CAUSES if not (c.needs == "reheat" and reheat is False) and not (c.needs == "pressure_independent" and not pressure_independent)] + list(extra)


def make_prior_v1(candidates: list[str], doc: str, settings: M.Settings, *, docs: bool = True, airflow: str | None = None, feel: str | None = None,
                  weights: dict | None = None, shares: dict | None = None, reheat: bool | None = True, pressure_independent: bool = True,
                  extra_causes: tuple[CauseSpec, ...] = ()) -> tuple[list[tuple], np.ndarray]:
    """(causes, prior). `docs=False` (no equipment list or claims: tier T0) leaves out the documentation causes, and the hardware causes keep their relative odds.
    The lump masses are v0's: P(acts-fail) = `settings.p_acts_fail`, the rest of what is not `p_wrong`, and the leaves split their lump by `shares`
    (removing a leaf hands its share to its lump-mates, so a lump's mass never changes). Symptom multipliers apply to leaves before normalising, as in v0.
    `extra_causes` (Addendum 37): leaves beyond `CAUSES`, e.g. `(ECON_FAULT,)`; `shares` must then also give each of their shares (it is used as given, not defaulted). Empty by
    default, so this is a byte-for-byte no-op for every existing caller."""
    shares = shares or DEFAULT_SHARES
    lump_mass = {ACTS_FAIL: settings.p_acts_fail, OTHER: 1.0 - settings.p_wrong - settings.p_acts_fail}
    leaves = leaf_causes(reheat, pressure_independent, extra=extra_causes)
    missing = [c.id for c in extra_causes if c.id not in shares]
    if missing:
        raise ValueError(f"extra_causes {missing} have no entry in shares")
    total = {lump: sum(shares[c.id] for c in leaves if c.lump == lump) for lump in LUMPS}
    mult = {c.id: 1.0 for c in leaves}
    if airflow in ("yes", "no"):
        m = settings.no_airflow_multiplier if airflow == "no" else 1.0 / settings.no_airflow_multiplier
        for cid in AIRFLOW_SET:
            if cid in mult:
                mult[cid] *= m
    for cid, m in FEEL_MULT.get(feel, {}).items():
        if cid in mult:
            mult[cid] *= m
    causes = [c.cause for c in leaves]
    raw = [lump_mass[c.lump] * shares[c.id] / total[c.lump] * mult[c.id] if total[c.lump] > 0 else 0.0 for c in leaves]
    if docs:
        wrong = [c for c in candidates if c != doc]
        w = np.array([(weights or {}).get(c, 1.0) for c in wrong], float)
        p_unlisted = settings.p_wrong * settings.unlisted_share if wrong else settings.p_wrong
        listed = (settings.p_wrong - p_unlisted) * (w / w.sum() if len(w) else w)
        causes += [("wrong", c) for c in wrong] + [("unlisted",)]
        raw += list(listed) + [p_unlisted]
    p = np.maximum(np.array(raw, float), M.PRIOR_FLOOR)
    return causes, p / p.sum()


def cause_text(cause: tuple) -> str:
    if cause[0] in ALL_BY_ID:
        return ALL_BY_ID[cause[0]].label
    return {"wrong": "Documented box is wrong", "unlisted": "Fed by something not on the list", ACTS_FAIL: "Box does not act when commanded", OTHER: "Box acts; cause elsewhere"}[cause[0]]
