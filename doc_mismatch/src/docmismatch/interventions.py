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

from .physical import CLIMATES, EPLUS, OUTPUT_VARIABLES, TOPOLOGIES, _n, _split_tags, extract_graph, load_model, read_series

SP_VAR = "Zone Thermostat Cooling Setpoint Temperature"


def random_codes(n_zones: int, n_blocks: int, seed: int) -> np.ndarray:
    """(n_zones, n_blocks) independent +-1 codes."""
    return np.random.default_rng(seed).choice([-1, 1], size=(n_zones, n_blocks)).astype(int)


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
                 base_cool: float = 24.0, base_heat: float = 20.0, seed: int = 0, dither: bool = True, shift_heat: bool = True) -> dict:
    """One EnergyPlus campaign. dither=False runs the SAME building/period with every zone held at base_cool (the passive baseline)."""
    out = out_root / topology_id
    out.mkdir(parents=True, exist_ok=True)
    m = load_model(topology_id)
    graph = extract_graph(m, topology_id)
    zone_nodes = {n["os_name"]: n["id"] for n in graph["nodes"] if n["kind"] == "Zone"}
    names = sorted(zone_nodes)
    n_blocks = n_days * 24 // block_h
    code_arr = random_codes(len(names), n_blocks, seed) if dither else np.zeros((len(names), n_blocks), dtype=int)
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
        seed=seed, dither=dither, shift_heat=shift_heat, zone_nodes={nm: zone_nodes[nm] for nm in names}, codes={zone_nodes[nm]: codes[nm].tolist() for nm in names})))
    return run


def _n_upper(name: str) -> str:
    return name.upper()
