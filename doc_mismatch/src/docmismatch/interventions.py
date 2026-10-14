"""Deliberate-perturbation campaigns (PREREGISTRATION_DR.md Addendum 13). Needs `openstudio`: run it from physics_pipeline/.venv.

Passive BAS data cannot say which VAV box serves which zone (Addendum 11): under closed-loop control the zone temperature is regulated, so the
actuator (box flow) carries the link and it is confounded by weather/schedule common mode. The remedy tested here is external excitation of the
control REFERENCE: every zone's cooling setpoint follows its own pseudo-random +-half_span pattern (a BAS setpoint schedule; no hardware), and the
serving box's flow -- the manipulated variable -- should follow that zone's pattern and no other zone's.

For one base topology this builds the model (never rewired), gives every zone its own cooling-setpoint schedule, runs a short EnergyPlus period
(hourly) and writes <out>/<topology_id>/{graph.json, evidence.npz, run.json, campaign.json} in the same layout as `physical.simulate_topology`
(so `data.load_base(tid, root)` reads it), plus a per-zone `sp_cool` series proving the pattern reached the simulation.
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import numpy as np
import openstudio
from openstudio import model as osm

from .dr.override_eval import START_HOURS, STEPS_PER_HOUR, plan_override_tests  # noqa: F401
from .dr.perturbation import make_codes
from .physical import CLIMATES, EPLUS, OUTPUT_VARIABLES, TOPOLOGIES, _n, _split_tags, extract_graph, load_model, read_series

SP_VAR = "Zone Thermostat Cooling Setpoint Temperature"


def random_codes(n_zones: int, n_blocks: int, seed: int, dropout: float = 0.0) -> np.ndarray:
    """(n_zones, n_blocks) independent +-1 codes (with optional override dropout, see `dr.perturbation.make_codes`; dropout = 0 is bit-identical to the original)."""
    return make_codes(n_zones, n_blocks, seed, dropout)


def _day_rule(sched: osm.ScheduleRuleset, month: int, day: int, values: np.ndarray) -> None:
    rule = osm.ScheduleRule(sched)
    for setter in ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"):
        getattr(rule, f"setApply{setter}")(True)
    d = openstudio.Date(openstudio.MonthOfYear(month), day)
    rule.setStartDate(d)
    rule.setEndDate(d)
    ds = rule.daySchedule()
    ds.clearValues()
    for h in range(24):
        ds.addValue(openstudio.Time(0, h + 1, 0, 0), float(values[h]))


def apply_setpoint_dither(m: osm.Model, codes: dict[str, np.ndarray], *, month: int, pre_days: int, n_days: int, block_h: int,
                          base_cool: float, base_heat: float, half_span: float, shift_heat: bool = True) -> None:
    """Replace every thermal zone's thermostat with a clone whose cooling setpoint is base_cool + half_span * code(t) during the campaign
    (constant base_cool during the `pre_days` warm-up/passive days). With `shift_heat` the heating setpoint gets the SAME offset (a thermostat-shift campaign that
    excites a zone whether it is in cooling or heating); otherwise it is the constant base_heat. `codes[zone_name]` has one +-1 entry per block."""
    heat_const = osm.ScheduleRuleset(m, base_heat)
    # A dual-setpoint thermostat object can be shared by several zones, and re-assigning one zone's thermostat can remove the shared original
    # from the others: clone one private thermostat per zone FIRST, only then assign.
    zones = list(m.getThermalZones())
    clones = {}
    for z in zones:
        old = z.thermostatSetpointDualSetpoint()
        if not old.is_initialized():
            raise RuntimeError(f"zone {_n(z)} has no dual-setpoint thermostat")
        old = old.get()
        tl = old.coolingSetpointTemperatureSchedule().get().scheduleTypeLimits() if old.coolingSetpointTemperatureSchedule().is_initialized() else None
        clones[_n(z)] = (old.clone(m).to_ThermostatSetpointDualSetpoint().get(), tl)
    for z in zones:
        name = _n(z)
        new, tl = clones[name]
        cool = osm.ScheduleRuleset(m, base_cool)
        heat = osm.ScheduleRuleset(m, base_heat) if shift_heat else heat_const
        if tl is not None and tl.is_initialized():
            cool.setScheduleTypeLimits(tl.get())
            heat.setScheduleTypeLimits(tl.get())
        c = codes[name]
        for d in range(n_days):
            hours = np.arange(24) + d * 24
            off = half_span * c[np.minimum(hours // block_h, len(c) - 1)]
            _day_rule(cool, month, 1 + pre_days + d, base_cool + off)
            if shift_heat:
                _day_rule(heat, month, 1 + pre_days + d, base_heat + off)
        new.setCoolingSetpointTemperatureSchedule(cool)
        new.setHeatingSetpointTemperatureSchedule(heat)
        z.setThermostatSetpointDualSetpoint(new)


def run_campaign(topology_id: str, out_root: Path, *, month: int = 7, pre_days: int = 2, n_days: int = 12, block_h: int = 2, half_span: float = 1.5,
                 base_cool: float = 24.0, base_heat: float = 20.0, seed: int = 0, dither: bool = True, shift_heat: bool = True, dropout: float = 0.0) -> dict:
    """One EnergyPlus campaign. dither=False runs the SAME building/period with every zone held at base_cool (the passive baseline)."""
    out = out_root / topology_id
    out.mkdir(parents=True, exist_ok=True)
    m = load_model(topology_id)
    graph = extract_graph(m, topology_id)
    zone_nodes = {n["os_name"]: n["id"] for n in graph["nodes"] if n["kind"] == "Zone"}
    names = sorted(zone_nodes)
    n_blocks = n_days * 24 // block_h
    code_arr = random_codes(len(names), n_blocks, seed, dropout) if dither else np.zeros((len(names), n_blocks), dtype=int)
    codes = {nm: code_arr[i] for i, nm in enumerate(names)}
    apply_setpoint_dither(m, codes, month=month, pre_days=pre_days, n_days=n_days, block_h=block_h, base_cool=base_cool, base_heat=base_heat, half_span=half_span, shift_heat=shift_heat)

    rp = m.getRunPeriod()
    rp.setBeginMonth(month); rp.setBeginDayOfMonth(1); rp.setEndMonth(month); rp.setEndDayOfMonth(pre_days + n_days)
    for v in (*OUTPUT_VARIABLES, SP_VAR):
        osm.OutputVariable(v, m).setReportingFrequency("Hourly")
    ws = openstudio.energyplus.ForwardTranslator().translateModel(m)
    idf = out / "in.idf"
    ws.save(openstudio.path(str(idf)), True)
    t0 = time.time()
    r = subprocess.run([str(EPLUS / "energyplus"), "-w", str(CLIMATES[TOPOLOGIES[topology_id][2]]), "-d", str(out), "-i", str(EPLUS / "Energy+.idd"), str(idf)],
                       capture_output=True, text=True, timeout=1800)
    err = (out / "eplusout.err").read_text(errors="replace") if (out / "eplusout.err").exists() else ""
    severe, fatal = sum("** Severe" in l for l in err.splitlines()), sum("** Fatal" in l for l in err.splitlines())
    run = dict(returncode=r.returncode, severe=severe, fatal=fatal, seconds=round(time.time() - t0, 1), climate=TOPOLOGIES[topology_id][2],
               ok=r.returncode == 0 and severe == 0 and fatal == 0 and (out / "eplusout.sql").exists())
    if not run["ok"]:
        raise RuntimeError(f"{topology_id}: EnergyPlus did not run cleanly: {run}")

    for n in graph["nodes"]:
        if n["kind"] == "Zone":
            n["series"]["sp_cool"] = ["var", _n_upper(n["os_name"]), SP_VAR]
    multi: dict[tuple[str, str], list[str]] = {}
    for n in graph["nodes"]:
        for sig, spec in n["series"].items():
            multi.setdefault((spec[1], spec[2]), []).append(f"{n['id']}|{sig}")
    raw = read_series(out / "eplusout.sql", {k: "|".join(v) for k, v in multi.items()})
    arrays = {tag: arr for joined, arr in raw.items() for tag in _split_tags(joined)}
    missing = [t for tags in multi.values() for t in tags if t not in arrays]
    if missing:
        raise RuntimeError(f"{topology_id}: series missing from SQL: {missing[:8]}")
    np.savez_compressed(out / "evidence.npz", **{k.replace("|", "__"): v for k, v in arrays.items()})
    (out / "graph.json").write_text(json.dumps(graph, indent=1))
    run.update(n_hours=int(len(next(iter(arrays.values())))), n_series=len(arrays))
    (out / "run.json").write_text(json.dumps(run, indent=1))
    (out / "campaign.json").write_text(json.dumps(dict(
        topology_id=topology_id, month=month, pre_days=pre_days, n_days=n_days, block_h=block_h, half_span=half_span, base_cool=base_cool, base_heat=base_heat,
        seed=seed, dither=dither, shift_heat=shift_heat, dropout=dropout, zone_nodes={nm: zone_nodes[nm] for nm in names}, codes={zone_nodes[nm]: codes[nm].tolist() for nm in names})))
    return run


def _n_upper(name: str) -> str:
    return name.upper()


# ---------------------------------------------------------------------------------------------- technician-style single-box overrides (Addendum 16)
def apply_box_overrides(m: osm.Model, plan: list[dict], terminal_of: dict[str, str], *, month: int, kind: str) -> None:
    """For every planned test, force the box to full airflow for its window (the terminal's minimum-air-flow fraction becomes a schedule that is the
    box's own constant fraction except 1.0 during the window). kind == "close" instead shuts the damper (zero airflow) for the window; kind == "full_cool" additionally switches the box's hot-water reheat coil OFF during the window
    (the coil's availability schedule), so the zone is driven to maximum cooling in every season; kind == "flow_only" leaves the reheat untouched."""
    if kind not in ("full_cool", "flow_only", "close"):
        raise ValueError(kind)
    terms = {_n(t): t for t in m.getAirTerminalSingleDuctVAVReheats()}
    frac = osm.ScheduleTypeLimits(m)
    frac.setName("override fraction"); frac.setLowerLimitValue(0.0); frac.setUpperLimitValue(1.0); frac.setNumericType("Continuous"); frac.setUnitType("Dimensionless")
    onoff = osm.ScheduleTypeLimits(m)
    onoff.setName("override on-off"); onoff.setLowerLimitValue(0.0); onoff.setUpperLimitValue(1.0); onoff.setNumericType("Discrete"); onoff.setUnitType("Availability")
    for tst in plan:
        t = terms[terminal_of[tst["vav"]]]
        if kind == "close":   # damper commanded shut: the terminal's availability schedule is 0 during the window (zero airflow, the zone is left to warm)
            h0, h1 = tst["start_hour"], tst["start_hour"] + tst["hours"]
            on = osm.ScheduleRuleset(m, 1.0)
            on.setScheduleTypeLimits(onoff)
            v0 = np.ones(24)
            v0[h0:h1] = 0.0
            _day_rule(on, month, 1 + tst["day"], v0)
            t.setAvailabilitySchedule(on)
            continue
        base = t.constantMinimumAirFlowFraction()
        if not base.is_initialized():
            raise RuntimeError(f"{_n(t)}: minimum air flow is not a constant fraction; cannot build the override schedule")
        h0, h1 = tst["start_hour"], tst["start_hour"] + tst["hours"]
        sched = osm.ScheduleRuleset(m, float(base.get()))
        sched.setScheduleTypeLimits(frac)
        vals = np.full(24, float(base.get()))
        vals[h0:h1] = 1.0
        _day_rule(sched, month, 1 + tst["day"], vals)
        t.setZoneMinimumAirFlowInputMethod("Scheduled")
        t.setMinimumAirFlowFractionSchedule(sched)
        if kind == "full_cool":
            coil = t.reheatCoil().to_CoilHeatingWater()
            if not coil.is_initialized():
                raise RuntimeError(f"{_n(t)}: reheat coil is not a hot-water coil")
            on = osm.ScheduleRuleset(m, 1.0)
            on.setScheduleTypeLimits(onoff)
            v2 = np.ones(24)
            v2[h0:h1] = 0.0
            _day_rule(on, month, 1 + tst["day"], v2)
            coil.get().setAvailabilitySchedule(on)


def _read_zone_timestep(sql_path: Path, wanted: dict[str, str]) -> dict[str, np.ndarray]:
    """{out-key: series} for zone variables reported at the zone timestep; wanted = {ZONE OS NAME UPPER: out-key}"""
    import sqlite3
    con = sqlite3.connect(str(sql_path))
    env = con.execute("select EnvironmentPeriodIndex from EnvironmentPeriods where EnvironmentName like 'RUN PERIOD%'").fetchone()[0]
    out = {}
    for idx, key, name, freq in con.execute("select ReportDataDictionaryIndex, KeyValue, Name, ReportingFrequency from ReportDataDictionary"):
        if freq == "Zone Timestep" and name == "Zone Mean Air Temperature" and key.upper() in wanted:
            rows = con.execute("select rd.Value from ReportData rd join Time t on rd.TimeIndex = t.TimeIndex "
                               "where rd.ReportDataDictionaryIndex=? and t.EnvironmentPeriodIndex=? order by rd.TimeIndex", (idx, env)).fetchall()
            out[wanted[key.upper()]] = np.array([r[0] for r in rows], dtype=np.float64)
    con.close()
    return out


def run_override_tests(topology_id: str, out_root: Path, *, month: int, seed: int, kind: str = "full_cool", pre_days: int = 2, hours: int = 2) -> dict:
    """One EnergyPlus run holding a technician-style override test of EVERY box, one box per day (after `pre_days` undisturbed days), in a seeded order and at a seeded
    clock hour. Writes <out>/<topology_id>/{graph.json, evidence.npz, run.json, tests.json}; the evidence adds `<zone id>|temp10` (zone temperature every 10 minutes)."""
    out = out_root / topology_id
    out.mkdir(parents=True, exist_ok=True)
    m = load_model(topology_id)
    graph = extract_graph(m, topology_id)
    vavs = sorted(n["id"] for n in graph["nodes"] if n["kind"] == "VAV")
    terminal_of = {n["id"]: n["os_name"] for n in graph["nodes"] if n["kind"] == "VAV"}
    plan = plan_override_tests(vavs, seed, pre_days, hours)
    apply_box_overrides(m, plan, terminal_of, month=month, kind=kind)
    n_days = pre_days + len(plan)

    rp = m.getRunPeriod()
    rp.setBeginMonth(month); rp.setBeginDayOfMonth(1); rp.setEndMonth(month); rp.setEndDayOfMonth(n_days)
    for v in OUTPUT_VARIABLES:
        osm.OutputVariable(v, m).setReportingFrequency("Hourly")
    osm.OutputVariable("Zone Mean Air Temperature", m).setReportingFrequency("Timestep")
    ws = openstudio.energyplus.ForwardTranslator().translateModel(m)
    idf = out / "in.idf"
    ws.save(openstudio.path(str(idf)), True)
    t0 = time.time()
    r = subprocess.run([str(EPLUS / "energyplus"), "-w", str(CLIMATES[TOPOLOGIES[topology_id][2]]), "-d", str(out), "-i", str(EPLUS / "Energy+.idd"), str(idf)],
                       capture_output=True, text=True, timeout=1800)
    err = (out / "eplusout.err").read_text(errors="replace") if (out / "eplusout.err").exists() else ""
    severe, fatal = sum("** Severe" in l for l in err.splitlines()), sum("** Fatal" in l for l in err.splitlines())
    run = dict(returncode=r.returncode, severe=severe, fatal=fatal, seconds=round(time.time() - t0, 1), climate=TOPOLOGIES[topology_id][2],
               ok=r.returncode == 0 and severe == 0 and fatal == 0 and (out / "eplusout.sql").exists())
    if not run["ok"]:
        raise RuntimeError(f"{topology_id}: EnergyPlus did not run cleanly: {run}")

    multi: dict[tuple[str, str], list[str]] = {}
    for n in graph["nodes"]:
        for sig, spec in n["series"].items():
            multi.setdefault((spec[1], spec[2]), []).append(f"{n['id']}|{sig}")
    raw = read_series(out / "eplusout.sql", {k: "|".join(v) for k, v in multi.items()})
    arrays = {tag: arr for joined, arr in raw.items() for tag in _split_tags(joined)}
    zone_key = {n["os_name"].upper(): f"{n['id']}|temp10" for n in graph["nodes"] if n["kind"] == "Zone"}
    arrays.update(_read_zone_timestep(out / "eplusout.sql", zone_key))
    missing = [t for tags in multi.values() for t in tags if t not in arrays] + [t for t in zone_key.values() if t not in arrays]
    if missing:
        raise RuntimeError(f"{topology_id}: series missing from SQL: {missing[:8]}")
    np.savez_compressed(out / "evidence.npz", **{k.replace("|", "__"): v for k, v in arrays.items()})
    (out / "graph.json").write_text(json.dumps(graph, indent=1))
    run.update(n_hours=n_days * 24, n_series=len(arrays), n_steps=int(len(next(v for k, v in arrays.items() if k.endswith("|temp10")))))
    (out / "run.json").write_text(json.dumps(run, indent=1))
    (out / "tests.json").write_text(json.dumps(dict(topology_id=topology_id, month=month, seed=seed, kind=kind, pre_days=pre_days, hours=hours, plan=plan)))
    return run
