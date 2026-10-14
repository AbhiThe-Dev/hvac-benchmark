"""The check catalogue, working model v1: what each check tests, how each cause makes its reading come out, how long it takes, and what data it needs.

RESPONSE MODEL. For each check and each cause, `p_pos` is the probability that the check comes back POSITIVE:
  reading checks (`kind = "reading"`): positive = the reading is ABNORMAL (the question is phrased 'is it wrong?', so yes = abnormal). A cause the check 'sees' has a high number
    (`detects`); every other cause, including 'the documented box is wrong', gets the check's false-alarm rate `bg`.
  the four v0 checks (`kind` act_observe / trace / acts): positive = yes, exactly as in v0: v0's hit and false-alarm rates on v0's truth rule for the cause's lump, except where a
    refined cause behaves differently from its lump (`overrides`, on the documented box only; e.g. with the air handler off no box override can make the room respond).
Every response number is a PLACEHOLDER (`source`), except the `override_room` rates, which v0 took from a simulation (PREREGISTRATION_DR.md Addendum 16). What IS cited is the
procedure (`refs`: which guide describes it) and the expected value or tolerance of a numeric reading where a guide gives one (`ReadingSpec.source`). Minutes are PLACEHOLDERS.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Callable

import numpy as np

from .. import model as M
from .causes import v0_tag
from .data import Need

LV = dict(strong=0.92, good=0.75, partial=0.50, weak=0.20)       # PLACEHOLDER: chance of an abnormal reading when the check sees the cause
BG = 0.05                                                         # PLACEHOLDER default false-alarm rate


def lv(**kw) -> dict:
    """{cause id: P(abnormal)} from level names ('strong', 'good', 'partial', 'weak') or plain probabilities."""
    return {k: (LV[v] if isinstance(v, str) else float(v)) for k, v in kw.items()}


# ---------------------------------------------------------------------------------------------- numeric readings
def static_min_inwc(attrs: dict) -> float:
    """Minimum recommended inlet static pressure by inlet diameter (ControlsHub 8.3: 4-6 in 0.25, 8-10 in 0.30, 12-14 in 0.35, 16 in and up 0.40-0.50; 0.40 used). Unknown size: 0.25."""
    d = attrs.get("inlet_diameter_in")
    return 0.25 if d is None else 0.25 if d <= 6 else 0.30 if d <= 10 else 0.35 if d <= 14 else 0.40


@dataclass(frozen=True)
class ReadingSpec:
    """How a numeric reading is judged. NORMAL if it is within `tol` (absolute) or `rel_tol` (fraction of the expected value) of the expected value, or, for a threshold check, at
    or above `low` / at or below `high`. The expected value is, in order: the one the technician supplies, the documented attribute `expected_attr` (tier T2 and up), `expected`."""
    quantity: str
    unit: str
    expected: float | None = None
    tol: float | None = None
    rel_tol: float | None = None
    low: float | None = None
    high: float | None = None
    expected_attr: str | None = None
    low_fn: Callable[[dict], float] | None = None
    source: str = "PLACEHOLDER"

    def band(self, attrs: dict, expected: float | None = None) -> tuple[float, float] | None:
        """(lowest normal value, highest normal value), or None when there is nothing to compare with (the technician then answers normal / abnormal themselves)."""
        e = expected if expected is not None else attrs.get(self.expected_attr) if self.expected_attr else None
        e = self.expected if e is None else e
        if e is not None and (self.tol is not None or self.rel_tol is not None):
            t = self.tol if self.tol is not None else self.rel_tol * abs(e)
            return e - t, e + t
        low = self.low_fn(attrs) if self.low_fn is not None else self.low
        if low is not None or self.high is not None:
            return (-np.inf if low is None else low), (np.inf if self.high is None else self.high)
        return None

    def classify(self, value: float, attrs: dict, expected: float | None = None) -> str:
        b = self.band(attrs, expected)
        if b is None:
            raise ValueError(f"nothing to compare a {self.quantity} reading with: give the expected value, or answer normal / abnormal")
        return "normal" if b[0] <= value <= b[1] else "abnormal"

    def describe(self, attrs: dict, expected: float | None = None) -> str:
        b = self.band(attrs, expected)
        if b is None:
            return f"{self.quantity} ({self.unit}); no expected value on file"
        lo, hi = b
        rng = f"at least {lo:g}" if hi == np.inf else f"at most {hi:g}" if lo == -np.inf else f"{lo:g} to {hi:g}"
        return f"{self.quantity}: normal is {rng} {self.unit}".rstrip()


# ---------------------------------------------------------------------------------------------- checks
@dataclass(frozen=True)
class CheckV1:
    name: str
    family: str                        # "v0 check" | "control system" | "at the box" | "at the air handler" | "in the room"
    text: str                          # {box} = 'box 2-04' (or 'the box serving <room>'), {t} = the target, {m} = the room, {ahu} = the air handler
    kind: str                          # "reading" | "act_observe" | "trace" | "acts"
    place: str                         # where the technician is while doing it: "box" | "room" | "ahu" | "bas" | "target" (v0 kinds: the box they act on)
    subject: str                       # whose attributes / point names apply: "box" | "ahu" | "zone"
    access_min: float
    do_min: float
    wait_min: float
    needs: tuple = ()                  # Need(item, fallback_min)
    feature: str | None = None         # "reheat" | "pressure_independent": not offered on a box without it
    detects: dict = field(default_factory=dict)      # reading checks: cause id -> P(abnormal)
    bg: float = BG                     # reading checks: P(abnormal) under every other cause
    reading: ReadingSpec | None = None
    v0: M.CheckType | None = None      # the four v0 checks: v0's own object (hit rate, false-alarm rate)
    overrides: dict = field(default_factory=dict)    # v0 checks on the documented box: cause id -> P(yes) where a refined cause differs from its lump
    doc_only: bool = False
    point: str | None = None           # control-system reads: the key of the point in a point map (Building1.points)
    source: str = "PLACEHOLDER"        # of the response numbers
    minutes_source: str = "PLACEHOLDER"
    refs: tuple = ()                   # where the procedure is described
    note: str = ""

    @property
    def is_reading(self) -> bool:
        return self.kind == "reading"

    @property
    def words(self) -> tuple[str, str]:
        """(positive answer, negative answer) in this check's own vocabulary."""
        return ("abnormal", "normal") if self.is_reading else ("yes", "no")

    def minutes(self, at: str | None, place: str, extra: float = 0.0) -> float:
        """Getting there (0 when the technician is already at `place`) + doing it + waiting + `extra` (the fallback cost of missing data)."""
        return (0.0 if at == place else self.access_min) + self.do_min + self.wait_min + extra

    def describe(self, box: str, target: str, member: str, ahu: str) -> str:
        return self.text.format(box=box, t=target, m=member, ahu=ahu)


def p_pos(check: CheckV1, cause: tuple, target: str, doc: str) -> float:
    """P(this check comes back positive | this cause), before clipping."""
    cid = cause[0]
    if check.is_reading:
        return check.detects.get(cid, check.bg)
    if target == doc and cid in check.overrides:
        return check.overrides[cid]
    return check.v0.tpr if M.truth("vav_zone", check.kind, target, v0_tag(cause), doc) else check.v0.fpr


def p_pos_row(check: CheckV1, causes: list[tuple], target: str, doc: str) -> np.ndarray:
    return np.clip(np.array([p_pos(check, c, target, doc) for c in causes], float), M.RATE_FLOOR, 1.0 - M.RATE_FLOOR)


def _v0(name: str, overrides: dict | None = None, source: str | None = None, refs: tuple = ()) -> CheckV1:
    ck = next(c for c in M.MENUS["vav_zone"] if c.name == name)
    return CheckV1(ck.name, "v0 check", ck.text.replace("box {t}", "{box}"), ck.kind, "target", "box", ck.access_min, ck.do_min, ck.wait_min, v0=ck, overrides=overrides or {},
                   doc_only=ck.doc_only, source=source or ck.source, refs=refs)


BAS = (Need("bas_access", None), Need("point_map", 8.0))         # a control-system read: 2 minutes with a point map, 10 without, not at all without access
BAS_AHU = BAS + (Need("claims", 4.0),)                            # ... and 4 more to find which air handler serves the box when the claims are not on file

CATALOGUE: tuple[CheckV1, ...] = (
    # ---- the four v0 checks (text, minutes and rates are v0's) ------------------------------------------------------------------------------------------------------------
    _v0("override_room", dict(ahu_fan_off=0.03, low_static=0.35, duct_diffuser=0.15, capacity_design=0.50, controller_config=0.60, flow_sensor=0.85, other=0.60),
        "rates: v0's (override_room hit and false-alarm rates measured in simulation, Addendum 16); the refined causes' rows PLACEHOLDER", refs=("v0",)),
    _v0("override_diffuser", dict(ahu_fan_off=0.10, low_static=0.40, duct_diffuser=0.20, capacity_design=0.75, controller_config=0.65, flow_sensor=0.85, other=0.60), refs=("v0",)),
    _v0("duct_trace", refs=("v0",)),
    _v0("confirm_acts", refs=("v0", "CH 3.2 step 3")),
    # ---- control system (place 'bas': a laptop or workstation; needs access, a point map makes it quick) -------------------------------------------------------------------
    CheckV1("bas_ahu_fan", "control system", "In the control system, read the supply fan status, speed and alarms of {ahu}: is the fan off, tripped or in alarm?",
            "reading", "bas", "ahu", 0, 2, 0, BAS_AHU, detects=lv(ahu_fan_off="strong", low_static="weak"), bg=0.03, refs=("CH 3.2 step 1", "CH 10"), point="fan_status"),
    CheckV1("bas_static", "control system", "In the control system, read the duct static pressure of {ahu} against its setpoint: is it low?",
            "reading", "bas", "ahu", 0, 2, 0, BAS_AHU, detects=lv(ahu_fan_off="strong", low_static="strong"), bg=0.03,
            reading=ReadingSpec("duct static pressure", "in. w.c.", expected_attr="static_setpoint_inwc", rel_tol=0.20, source="PLACEHOLDER tolerance; the setpoint is documented (T2)"), refs=("CH 4.2 step 4", "CH 8"), point="static_pressure"),
    CheckV1("bas_controller", "control system", "In the control system, read the controller status and alarms of {box}: is it offline, in a fault state or alarming?",
            "reading", "bas", "box", 0, 2, 0, BAS, detects=lv(controller_comms="strong", no_power=0.35, actuator_fail="weak", signal_fault=0.15), bg=0.04, refs=("CH 3.2 step 2",), point="status"),
    CheckV1("bas_airflow", "control system", "In the control system, read the airflow setpoint and measured airflow of {box}: does the measurement miss the setpoint by more than about 10%?",
            "reading", "bas", "box", 0, 2, 0, BAS,
            detects=lv(ahu_fan_off="strong", low_static="good", actuator_fail="good", damper_mech="good", no_power="good", signal_fault="good", controller_comms="partial",
                       flow_sensor="partial", controller_config="partial", capacity_design="partial"), bg=0.05,
            reading=ReadingSpec("measured airflow", "cfm", rel_tol=0.10, source="cited (ControlsHub 13 Q5, which cites ASHRAE Guideline 36: within 10% above 20% of maximum; not checked against the Guideline); the expected value is the setpoint the technician reads"),
            refs=("CH 4.2 step 1", "CH 10"), point="airflow"),
    CheckV1("bas_damper", "control system", "In the control system, read the damper position of {box} against its command: is it pinned at 100% while airflow is low, or not following its command?",
            "reading", "bas", "box", 0, 2, 0, BAS,
            detects=lv(damper_mech="good", actuator_fail="good", no_power="partial", signal_fault="partial", low_static="partial", ahu_fan_off="partial", capacity_design="partial",
                       controller_comms="weak", flow_sensor="weak", controller_config="weak"), bg=0.05, refs=("CH 4.2 step 1", "PNNL performance monitoring"), point="damper"),
    CheckV1("bas_zone", "control system", "In the control system, read the temperature, setpoint, occupancy schedule and mode of {m}: is the setpoint, schedule or mode wrong for this room?",
            "reading", "bas", "zone", 0, 2, 0, BAS, detects=lv(zone_sensor_setpoint="good"), bg=0.05, refs=("PNNL performance monitoring", "CH 9.2"), point="temperature"),
    CheckV1("bas_reheat", "control system", "In the control system, read the reheat command and valve or stage position of {box}: is heat called for but the valve or stage not responding?",
            "reading", "bas", "box", 0, 2, 0, BAS, feature="reheat", detects=lv(reheat_fail="good", zone_sensor_setpoint="weak"), bg=0.05, refs=("PNNL performance monitoring",), point="reheat"),
    CheckV1("bas_hunting", "control system", "In the control system, watch the damper and airflow of {box} for about 5 minutes: do they keep swinging up and down?",
            "reading", "bas", "box", 0, 2, 5, BAS, detects=lv(controller_config="partial", flow_sensor="partial", damper_mech="weak", low_static="weak"), bg=0.04, refs=("CH 6",),
            note="a live look, not a trend analysis", point="airflow"),
    # ---- at the box ---------------------------------------------------------------------------------------------------------------------------------------------------------
    CheckV1("power_24vac", "at the box", "At {box}, measure the voltage at the actuator terminals: is it missing or outside 22 to 26 VAC?",
            "reading", "box", "box", 6, 4, 0, detects=lv(no_power="strong", controller_comms="weak"), bg=0.03,
            reading=ReadingSpec("AC voltage at the actuator", "V", expected=24.0, tol=2.0, source="cited (ControlsHub 3.2 step 4: 22-26 VAC)"), refs=("CH 3.2 step 4",)),
    CheckV1("control_signal", "at the box", "With {box} commanded open, measure the control signal at its actuator input: is it missing (under about 2 V on a 0-10 V actuator)?",
            "reading", "box", "box", 6, 4, 2, detects=lv(signal_fault="strong", controller_comms="partial", controller_config="weak"), bg=0.04,
            reading=ReadingSpec("DC control signal with an open command", "V", low=2.0, source="cited (ControlsHub 3.2 step 5: above 2 V for an open command on a 0-10 V actuator)"), refs=("CH 3.2 step 5",)),
    CheckV1("manual_damper_test", "at the box", "At {box}, disconnect the actuator and turn the damper shaft by hand: is the damper stuck or binding?",
            "reading", "box", "box", 6, 8, 0, detects=lv(damper_mech="strong"), bg=0.05, refs=("CH 3.2 step 6",),
            note="separates a dead actuator (shaft turns freely) from a mechanical fault (stuck)"),
    CheckV1("damper_linkage", "at the box", "At {box}, inspect the damper linkage, seals and stops: is the linkage loose or slipping, or the damper not reaching fully open or fully closed?",
            "reading", "box", "box", 6, 10, 0, detects=lv(damper_mech="good", actuator_fail="weak", controller_config="weak"), bg=0.04, refs=("PNNL damper", "PNNL damper linkage", "CH 4.1")),
    CheckV1("controller_leds", "at the box", "At {box}, look at the controller status lights and event log: is it dead, showing a fault, or off the network?",
            "reading", "box", "box", 6, 3, 0, detects=lv(controller_comms="good", no_power=0.35, signal_fault=0.15), bg=0.04, refs=("CH 3.3",),
            note="the walk-there version of the control-system controller status read"),
    CheckV1("sensing_ports", "at the box", "At {box}, inspect the flow-sensing ports and tubing: are ports clogged, or tubes kinked, loose or swapped (high and low)?",
            "reading", "box", "box", 6, 10, 0, feature="pressure_independent", detects=lv(flow_sensor="good"), bg=0.04, refs=("CH 4.3", "PNNL airflow sensor"),
            note="does not see transducer drift"),
    CheckV1("flow_vs_gauge", "at the box", "At {box}, compare the controller's pressure reading with a gauge on its flow taps: do they disagree by more than about 10%?",
            "reading", "box", "box", 6, 8, 0, BAS + (Need("instrument", None),), feature="pressure_independent", detects=lv(flow_sensor="strong"), bg=0.04,
            reading=ReadingSpec("controller differential pressure", "in. w.c.", rel_tol=0.10, source="PLACEHOLDER tolerance (ControlsHub 4.2 step 2 gives none); the expected value is the gauge's reading"),
            refs=("CH 4.2 step 2",)),
    CheckV1("k_factor", "at the box", "Compare the K-factor programmed in the controller of {box} with the value on its nameplate or submittal: do they differ?",
            "reading", "box", "box", 6, 4, 0, (Need("bas_access", None), Need("point_map", 4.0), Need("attr:k_factor", 4.0)), feature="pressure_independent",
            detects=lv(controller_config="partial"), bg=0.03,
            reading=ReadingSpec("K-factor", "", expected_attr="k_factor", rel_tol=0.01, source="PLACEHOLDER tolerance (ControlsHub 7.2: a mismatch is corrected); the expected value is the documented or nameplate one"),
            refs=("CH 4.2 step 5", "CH 7.2"), note="the nameplate is read at the box when no K-factor is on file (+4)"),
    CheckV1("max_airflow", "at the box", "Compare the maximum airflow setpoint in the controller of {box} with its design airflow: is it different?",
            "reading", "box", "box", 0, 4, 0, (Need("bas_access", None), Need("point_map", 4.0), Need("attr:design_airflow_cfm", 8.0)),
            detects=lv(controller_config="partial"), bg=0.03,
            reading=ReadingSpec("maximum airflow setpoint", "cfm", expected_attr="design_airflow_cfm", rel_tol=0.10, source="PLACEHOLDER tolerance; ControlsHub 4.2 step 6 and 13 Q7: the maximum should equal the design value"),
            refs=("CH 4.2 step 6", "CH 13 Q7"), note="finding the design airflow in the schedule or submittal when it is not on file costs +8"),
    CheckV1("static_at_box", "at the box", "At {box}, measure the static pressure at the inlet: is it below the minimum for its size (about 0.25 to 0.5 in. w.c.)?",
            "reading", "box", "box", 6, 6, 0, (Need("instrument", None), Need("attr:inlet_diameter_in", 2.0)), detects=lv(low_static="strong", ahu_fan_off="strong"), bg=0.04,
            reading=ReadingSpec("inlet static pressure", "in. w.c.", low_fn=static_min_inwc, source="cited (ControlsHub 8.3, minimum inlet static by box size)"), refs=("CH 4.2 step 4", "CH 8.3")),
    CheckV1("reheat_coil", "at the box", "At {box}, inspect the reheat coil and valve (or electric element and connections): is the valve stuck or leaking, the coil fouled, or a connection damaged?",
            "reading", "box", "box", 6, 10, 0, feature="reheat", detects=lv(reheat_fail="good"), bg=0.04, refs=("PNNL hydronic reheat", "PNNL electric reheat")),
    # ---- at the air handler ---------------------------------------------------------------------------------------------------------------------------------------------------
    CheckV1("ahu_visit", "at the air handler", "Go to {ahu}: is the supply fan stopped, tripped or in fault?",
            "reading", "ahu", "ahu", 15, 4, 0, (Need("claims", 10.0),), detects=lv(ahu_fan_off="strong", low_static=0.10), bg=0.04, refs=("CH 3.2 step 1", "CH 8"),
            note="the walk-there version of the control-system fan read; +10 to work out which handler serves the box when the claims are not on file"),
    CheckV1("ahu_gauge", "at the air handler", "At {ahu}, read the duct static pressure gauge against its setpoint: is it low?",
            "reading", "ahu", "ahu", 15, 2, 0, (Need("claims", 10.0),), detects=lv(ahu_fan_off="strong", low_static="strong"), bg=0.04,
            reading=ReadingSpec("duct static pressure", "in. w.c.", expected_attr="static_setpoint_inwc", rel_tol=0.20, source="PLACEHOLDER tolerance; the setpoint is documented (T2)"),
            refs=("CH 4.2 step 4", "CH 8"), note="the walk-there version of the control-system static pressure read"),
    # ---- in the room ----------------------------------------------------------------------------------------------------------------------------------------------------------
    CheckV1("flow_hood", "in the room", "Measure airflow at the diffuser in {m} with a flow hood: is it well off what {box} should be delivering right now?",
            "reading", "room", "zone", 5, 8, 0, (Need("instrument", None),),
            detects=lv(ahu_fan_off="strong", low_static="good", actuator_fail="good", damper_mech="good", no_power="good", signal_fault="good", controller_comms="partial", flow_sensor="good",
                       controller_config="good", duct_diffuser="good", capacity_design="partial", other="weak"), bg=0.05,
            reading=ReadingSpec("airflow at the diffuser", "cfm", rel_tol=0.10, source="cited (ControlsHub 13 Q5, secondary); the expected value is the box's current setpoint or design airflow, supplied by the technician"),
            refs=("CH 5.2 step 1",)),
    CheckV1("diffuser_duct", "in the room", "Look at the diffuser in {m} and the duct behind it: is the diffuser blocked or closed, or the duct crushed, disconnected or leaking?",
            "reading", "room", "zone", 8, 10, 0, detects=lv(duct_diffuser=0.85), bg=0.04, refs=("CH 5.1", "PNNL duct connections")),
    CheckV1("thermostat", "in the room", "In {m}, compare the thermostat or zone sensor with a reference thermometer and check its setpoint and mode: is it off, or the setpoint or mode wrong?",
            "reading", "room", "zone", 5, 6, 0, detects=lv(zone_sensor_setpoint="strong"), bg=0.05, refs=("PNNL zone sensor",)),
    CheckV1("ask_occupant", "in the room", "Ask the occupant: does it happen only at certain times, has anyone changed the thermostat, is a diffuser blocked? Do the answers point to one of those?",
            "reading", "room", "zone", 3, 3, 0, (Need("occupant", None),), detects=lv(zone_sensor_setpoint=0.55, duct_diffuser=0.35, capacity_design=0.35, controller_config="weak"), bg=0.12,
            refs=("PNNL performance monitoring",), note="cheap and unreliable: a high false-alarm rate"),
    CheckV1("design_load", "in the room", "Compare the current use of {m} (people, equipment, area) with the design airflow of {box}: is the room now asking for more than the box can deliver?",
            "reading", "room", "box", 0, 6, 0, (Need("attr:design_airflow_cfm", None),), detects=lv(capacity_design="good"), bg=0.04, refs=("CH 4.1", "CH 9"),
            note="cannot be offered without design values on file"),
)
# ---------------------------------------------------------------------------------------------- Addendum 37 (PREREGISTRATION_DR.md): checks for `causes.ECON_FAULT`, NOT enrolled in
# `CATALOGUE` above (a case that wants them is built with `checks=CATALOGUE + ECON_CHECKS`, already supported by `make_case_v1`'s existing `checks=` parameter).
BAS_ECONOMIZER = CheckV1(
    "bas_economizer", "control system", "In the control system, compare the outdoor-air damper command of {ahu} against the outdoor, return and mixed-air temperatures and its trend "
    "for the day: is it stuck (near its minimum, or anywhere else), or opening/closing at the wrong outdoor temperature?",
    "reading", "bas", "ahu", 0, 2, 0, BAS_AHU, detects=lv(econ_fault=0.69, low_static="weak"), bg=0.03, refs=("PNNL_RTU", "T24", "LBNL_FDD"), point="economizer_position",
    note="the AFDD1/AFDD3 comparison (damper command vs. outdoor/return/mixed-air temperatures), read as one BAS trend page, not a single instant. 0.69 is measured "
         "(LBNL_FDD, 2026-09-29): a stuck damper in EITHER direction and a wrong enable temperature in EITHER direction were each ~88-100% detectable on the day the dataset "
         "actually tested them, but that number assumes the weather that day happened to test the fault; averaged over all four failure signatures INCLUDING the days a fault "
         "(especially a wrong setpoint) simply wasn't cold enough to reveal itself at all, the honest single-visit rate drops to about 69% -- lower than the 0.92 this replaced, "
         "not higher, because most of the real detectability loss is weather, not the check's own sensitivity. Small sample (32 fault-days, one lab building); see PREREGISTRATION_DR.md "
         "Addendum 37's follow-up for the full breakdown by failure type.")
AHU_ECONOMIZER_TEST = CheckV1(
    "ahu_economizer_test", "at the air handler", "At {ahu}, override the outdoor-air damper open and watch it respond: is it stuck near its minimum, or slow or failing to modulate?",
    "reading", "ahu", "ahu", 15, 5, 0, (Need("claims", 10.0),), detects=lv(econ_fault="strong"), bg=0.04, refs=("PNNL_RTU",),
    note="the walk-there version of bas_economizer: a manual override and watch, standing in for the video's water-valve-override verification")
ECON_CHECKS: tuple[CheckV1, ...] = (BAS_ECONOMIZER, AHU_ECONOMIZER_TEST)

BY_NAME = {c.name: c for c in CATALOGUE}
V0_NAMES = ("override_room", "override_diffuser", "duct_trace", "confirm_acts")
assert len(BY_NAME) == len(CATALOGUE)


def v0_menu() -> tuple[CheckV1, ...]:
    """The four v0 checks only (the menu of the v0-equivalent tree)."""
    return tuple(BY_NAME[n] for n in V0_NAMES)


def _toward_half(p: float, a: float) -> float:
    return 0.5 + (p - 0.5) * (1.0 - a)


def degrade(check: CheckV1, a: float) -> CheckV1:
    """The check as it would behave if its readings were less reliable than the tool assumes: every probability moves a fraction `a` of the way toward 0.5 (0 = as assumed,
    1 = the check tells nothing). Hit rates fall and false-alarm rates rise together. Used only to make a simulated world worse than the tool's model of it."""
    if not 0.0 <= a <= 1.0:
        raise ValueError("a must be in [0, 1]")
    if a == 0.0:
        return check                                    # exactly the check, not a float-rounded copy: 'as assumed' must equal the tool's own model
    f = lambda p: _toward_half(p, a)  # noqa: E731
    if check.is_reading:
        return replace(check, detects={k: f(v) for k, v in check.detects.items()}, bg=f(check.bg))
    return replace(check, v0=replace(check.v0, tpr=f(check.v0.tpr), fpr=f(check.v0.fpr)), overrides={k: f(v) for k, v in check.overrides.items()})


def degrade_all(checks: tuple[CheckV1, ...], a: float) -> tuple[CheckV1, ...]:
    return tuple(degrade(c, a) for c in checks)


def validate(checks: tuple[CheckV1, ...] = CATALOGUE) -> list[str]:
    """Problems with a catalogue (empty when it is sound): probabilities outside (0, 1), unknown places, unknown causes, a v0 check without its v0 object."""
    from .causes import ALL_BY_ID as BY_ID
    bad = []
    for c in checks:
        if c.kind not in ("reading", "act_observe", "trace", "acts"):
            bad.append(f"{c.name}: kind {c.kind!r}")
        if c.place not in ("box", "room", "ahu", "bas", "target") or c.subject not in ("box", "ahu", "zone"):
            bad.append(f"{c.name}: place {c.place!r} / subject {c.subject!r}")
        if min(c.access_min, c.do_min, c.wait_min) < 0:
            bad.append(f"{c.name}: negative minutes")
        if c.do_min + c.wait_min <= 0:
            bad.append(f"{c.name}: takes no time (the per-minute rules divide by the minutes)")
        if c.is_reading:
            if c.v0 is not None or c.overrides:
                bad.append(f"{c.name}: a reading check with v0 fields")
            probs = list(c.detects.values()) + [c.bg]
            bad += [f"{c.name}: detects names unknown cause {k!r}" for k in c.detects if k not in BY_ID]
        else:
            if c.v0 is None:
                bad.append(f"{c.name}: a v0 kind without a v0 object")
            probs = [c.v0.tpr, c.v0.fpr] + list(c.overrides.values()) if c.v0 else []
            bad += [f"{c.name}: overrides name unknown cause {k!r}" for k in c.overrides if k not in BY_ID]
        if any(not 0.0 < p < 1.0 for p in probs):
            bad.append(f"{c.name}: a probability outside (0, 1)")
    return bad
