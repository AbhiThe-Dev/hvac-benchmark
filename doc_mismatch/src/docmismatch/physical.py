"""OpenStudio side of the pipeline (needs `openstudio`; run it from
physics_pipeline/.venv). For one base topology it

  1. builds/loads a *valid* OpenStudio model (never rewired, never corrupted),
  2. extracts the physical connection graph straight from the model API,
  3. runs EnergyPlus for a full year (hourly), and
  4. exports per-component time series ("physical evidence") to plain npz/json
     so everything downstream is numpy-only.

Output per topology: <out>/<topology_id>/{graph.json, evidence.npz, run.json}.
"""

from __future__ import annotations

import json
import random
import sqlite3
import subprocess
import time
from pathlib import Path

import numpy as np
import openstudio
from openstudio import model as osm

from .build_models import RESOURCES, SPECS, build_vav_model

PP_ROOT = Path(__file__).resolve().parents[3] / "physics_pipeline" / "vendor"
EPLUS = PP_ROOT / "EnergyPlus-25.2.0-cf7368216c-Darwin-macOS13-arm64"
WEATHER_DIR = EPLUS / "WeatherData"
CLIMATES = {
    "chicago": WEATHER_DIR / "USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw",
    "golden": WEATHER_DIR / "USA_CO_Golden-NREL.724666_TMY3.epw",
    "tampa": WEATHER_DIR / "USA_FL_Tampa.Intl.AP.722110_TMY3.epw",
    "sanfrancisco": WEATHER_DIR / "USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw",
}

# topology_id -> (source, climate). "file" = vendored NREL/OpenStudio-resources model as-is.
TOPOLOGIES: dict[str, tuple[str, str, str]] = {
    "sys07_vav_reheat": ("file", "baseline_sys07", "chicago"),
    "sys03_psz_ac": ("file", "baseline_sys03", "chicago"),
    "vav_2ahu_2loops": ("built", "vav_2ahu_2loops", "chicago"),
    "vav_3ahu_2loops": ("built", "vav_3ahu_2loops", "golden"),
}

# spec-built topologies (build_ext.register_from_spec fills this): topology_id -> zero-arg model builder
EXT_BUILDERS: dict = {}

OUTPUT_VARIABLES = (
    "System Node Temperature",
    "System Node Mass Flow Rate",
    "Zone Mean Air Temperature",
    "Fan Electricity Rate",
    "Heating Coil Heating Rate",
    "Cooling Coil Total Cooling Rate",
    "Cooling Coil Sensible Cooling Rate",
    "Boiler Heating Rate",
    "Boiler Outlet Temperature",
    "Chiller Evaporator Cooling Rate",
    "Chiller Evaporator Outlet Temperature",
    "Pump Mass Flow Rate",
    "Pump Electricity Rate",
    "Site Outdoor Air Drybulb Temperature",
)


def load_model(topology_id: str) -> osm.Model:
    kind, ref, _ = TOPOLOGIES[topology_id]
    if kind == "ext":
        return EXT_BUILDERS[ref]()
    if kind == "built":
        return build_vav_model(SPECS[ref])
    tr = openstudio.osversion.VersionTranslator()
    return tr.loadModel(openstudio.path(str(RESOURCES / f"{ref}.osm"))).get()


def _n(obj) -> str:
    return obj.name().get()


def _node(opt) -> "osm.Node":
    # `.get()` on an empty optional segfaults the bindings instead of raising: always guard.
    if not opt.is_initialized():
        raise LookupError("expected a connected model object, found none")
    n = opt.get().to_Node()
    if not n.is_initialized():
        raise LookupError("connected object is not a Node")
    return n.get()


def _node_or_none(opt):
    try:
        return _node(opt)
    except LookupError:
        return None


class _Ids:
    """Stable, shuffled per-kind numbering so an id's number leaks nothing about
    physical position (VAV-1 is not 'the first VAV on AHU-1')."""

    def __init__(self, seed: int):
        self.rng = random.Random(seed)
        self.pool: dict[str, list[int]] = {}
        self.n: dict[str, int] = {}

    def reserve(self, kind: str, count: int):
        nums = list(range(1, count + 1))
        self.rng.shuffle(nums)
        self.pool[kind] = nums

    def new(self, kind: str) -> str:
        return f"{kind}-{self.pool[kind].pop()}"


def extract_graph(m: osm.Model, topology_id: str) -> dict:
    """Physical truth. `series` maps signal name -> ['node'|'var', key, variable]."""
    ids = _Ids(seed=abs(hash(topology_id)) % 10**6 if False else sum(map(ord, topology_id)))
    als = sorted(m.getAirLoopHVACs(), key=_n)
    zones = sorted(m.getThermalZones(), key=_n)
    pls = sorted(m.getPlantLoops(), key=_n)

    def is_loop(pl, hot):
        sup = [c.iddObjectType().valueName() for c in pl.supplyComponents()]
        return any(("Boiler" in s) if hot else ("Chiller" in s) for s in sup)

    hw_loops = [p for p in pls if is_loop(p, True)]
    chw_loops = [p for p in pls if is_loop(p, False)]
    n_terms = sum(1 for al in als for c in al.demandComponents() if "AirTerminal" in c.iddObjectType().valueName())
    n_coils = sum(1 for p in hw_loops + chw_loops for c in p.demandComponents() if "Coil" in c.iddObjectType().valueName())
    # electric VAV reheat coils sit inside the terminal (not on a plant demand side): reserve ids for them too (0 for all-hydronic buildings, so their numbering is unchanged)
    n_elec = sum(1 for al in als for c in al.demandComponents() if c.iddObjectType().valueName() == "OS_AirTerminal_SingleDuct_VAV_Reheat"
                 and "Electric" in c.to_AirTerminalSingleDuctVAVReheat().get().reheatCoil().iddObjectType().valueName())
    for kind, cnt in (
        ("AHU", len(als)), ("VAV", n_terms), ("Zone", len(zones)), ("HWL", len(hw_loops)), ("CHWL", len(chw_loops)),
        ("Coil", n_coils + n_elec + len(als) * 2 + 5), ("Fan", len(als)), ("Pump", len(pls)), ("Boiler", len(hw_loops)),
        ("Chiller", len(chw_loops)), ("Branch", n_coils), ("SAT", len(als)), ("DAT", n_terms),
    ):
        ids.reserve(kind, max(cnt, 1))

    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    handle_id: dict[str, str] = {}

    def add(kind, brick, obj, series=None, **extra):
        nid = ids.new(kind)
        handle_id[str(obj.handle())] = nid
        nodes[nid] = {"id": nid, "kind": kind, "brick_type": brick, "os_name": _n(obj), "series": series or {}, **extra}
        return nid

    def edge(s, t, rel):
        edges.append({"src": s, "dst": t, "rel": rel})

    def node_series(n):
        return ["node", _n(n).upper()]

    # zones
    zone_id = {}
    for z in zones:
        zone_id[str(z.handle())] = add("Zone", "HVAC_Zone", z, {"temp": ["var", _n(z).upper(), "Zone Mean Air Temperature"]},
                                         story=z.spaces()[0].buildingStory().get().name().get() if z.spaces() and z.spaces()[0].buildingStory().is_initialized() else None,
                                         floor_area_m2=round(z.spaces()[0].floorArea(), 1) if z.spaces() else None)

    # plant loops
    loop_id, coil_branch, coil_loop = {}, {}, {}
    for pls_list, hot in ((hw_loops, True), (chw_loops, False)):
        for pl in pls_list:
            medium = "hot_water" if hot else "chilled_water"
            lid = add("HWL" if hot else "CHWL", "Hot_Water_Loop" if hot else "Chilled_Water_Loop", pl,
                      {"t_sup": node_series(pl.supplyOutletNode()) + ["System Node Temperature"],
                       "t_ret": node_series(pl.supplyInletNode()) + ["System Node Temperature"],
                       # demand-side inlet flow = sum of coil-branch flows + demand bypass (the pump also carries the supply bypass)
                       "flow": node_series(pl.demandInletNode()) + ["System Node Mass Flow Rate"]},
                      medium=medium)
            loop_id[str(pl.handle())] = lid
            pump = [c for c in pl.supplyComponents() if "Pump" in c.iddObjectType().valueName()][0]
            pump_id = add("Pump", "Hot_Water_Pump" if hot else "Chilled_Water_Pump", pump,
                          {"flow": ["var", _n(pump).upper(), "Pump Mass Flow Rate"], "kw": ["var", _n(pump).upper(), "Pump Electricity Rate"]},
                          medium=medium)
            edge(lid, pump_id, "hasPart")
            srcs = [c for c in pl.supplyComponents() if ("Boiler" in c.iddObjectType().valueName() or "Chiller" in c.iddObjectType().valueName())]
            for s in srcs:
                if hot:
                    sid = add("Boiler", "Boiler", s, {"rate": ["var", _n(s).upper(), "Boiler Heating Rate"], "t_out": ["var", _n(s).upper(), "Boiler Outlet Temperature"]}, medium=medium)
                else:
                    sid = add("Chiller", "Chiller", s, {"rate": ["var", _n(s).upper(), "Chiller Evaporator Cooling Rate"], "t_out": ["var", _n(s).upper(), "Chiller Evaporator Outlet Temperature"]}, medium=medium)
                edge(lid, sid, "hasPart")
            coils = [c for c in pl.demandComponents() if "Coil" in c.iddObjectType().valueName()]
            for c in coils:
                bid = ids.new("Branch")
                nodes[bid] = {"id": bid, "kind": "Branch", "brick_type": "Hot_Water_Valve" if hot else "Chilled_Water_Valve",
                              "os_name": f"branch of {_n(c)}", "series": {}, "medium": medium}
                edge(lid, bid, "feeds")
                coil_branch[str(c.handle())] = bid
                coil_loop[str(c.handle())] = lid

    def water_series(c, hot):
        cc = c.to_CoilHeatingWater().get() if hot else c.to_CoilCoolingWater().get()
        return _node(cc.waterInletModelObject()), _node(cc.waterOutletModelObject()), _node_or_none(cc.airOutletModelObject())

    def add_coil(c, parent_id):
        t = c.iddObjectType().valueName()
        heating = "Heating" in t
        brick = "Heating_Coil" if heating else "Cooling_Coil"
        var = "Heating Coil Heating Rate" if heating else "Cooling Coil Total Cooling Rate"
        ser = {"rate": ["var", _n(c).upper(), var]}
        if not heating:
            ser["rate_s"] = ["var", _n(c).upper(), "Cooling Coil Sensible Cooling Rate"]
        medium = None
        if t.endswith("Coil_Heating_Water") or t.endswith("Coil_Cooling_Water"):
            win, wout, aout = water_series(c, heating)
            if aout is not None:  # a VAV's embedded reheat coil has no air-outlet node of its own
                ser["t_air_out"] = node_series(aout) + ["System Node Temperature"]
            medium = "hot_water" if heating else "chilled_water"
            bid = coil_branch[str(c.handle())]
            nodes[bid]["series"] = {"flow": node_series(win) + ["System Node Mass Flow Rate"], "t_in": node_series(win) + ["System Node Temperature"],
                                    "t_out": node_series(wout) + ["System Node Temperature"]}
        cid = add("Coil", brick, c, ser, coil_type=t.replace("OS_", ""), **({"medium": medium} if medium else {}))
        edge(cid, parent_id, "hasPart")
        if medium:
            edge(coil_branch[str(c.handle())], cid, "feeds")
        return cid

    # air loops
    term_id = {}
    for al in als:
        aid = add("AHU", "AHU", al, {
            "flow": node_series(al.supplyOutletNode()) + ["System Node Mass Flow Rate"],
            "sat": node_series(al.supplyOutletNode()) + ["System Node Temperature"],
            "mat": node_series(al.mixedAirNode().get()) + ["System Node Temperature"] if al.mixedAirNode().is_initialized() else node_series(al.supplyInletNode()) + ["System Node Temperature"],
        })
        for c in al.supplyComponents():
            t = c.iddObjectType().valueName()
            if "Coil" in t:
                add_coil(c, aid)
            elif "Fan" in t:
                fid = add("Fan", "Fan", c, {"kw": ["var", _n(c).upper(), "Fan Electricity Rate"]})
                edge(fid, aid, "hasPart")
        sid = add("SAT", "Supply_Air_Temperature_Sensor", al, {"value": node_series(al.supplyOutletNode()) + ["System Node Temperature"]}, host=aid)
        edge(aid, sid, "hasPoint")
        dem = al.demandComponents()
        for i, c in enumerate(dem):
            t = c.iddObjectType().valueName()
            if "AirTerminal" not in t:
                continue
            sc = c.to_StraightComponent().get()
            nin, nout = _node(sc.inletModelObject()), _node(sc.outletModelObject())
            brick = "VAV" if "VAV" in t or "PIU" in t else "Terminal_Unit"
            vid = add("VAV", brick, c, {"flow": node_series(nin) + ["System Node Mass Flow Rate"], "t_in": node_series(nin) + ["System Node Temperature"],
                                         "t_dis": node_series(nout) + ["System Node Temperature"]}, terminal_type=t.replace("OS_", ""))
            edge(aid, vid, "feeds")
            j = i + 1
            while j < len(dem) and dem[j].iddObjectType().valueName() != "OS_ThermalZone":
                j += 1
            z = dem[j].to_ThermalZone().get()
            edge(vid, zone_id[str(z.handle())], "feeds")
            term_id[str(c.handle())] = vid
            if t == "OS_AirTerminal_SingleDuct_VAV_Reheat":
                rc = c.to_AirTerminalSingleDuctVAVReheat().get().reheatCoil()
                cid = add_coil(rc, vid)
                nodes[vid]["series"]["reheat"] = nodes[cid]["series"]["rate"]
            dsid = add("DAT", "Discharge_Air_Temperature_Sensor", c, {"value": node_series(nout) + ["System Node Temperature"]}, host=vid)
            edge(vid, dsid, "hasPoint")
    nodes["ENV"] = {"id": "ENV", "kind": "Weather", "brick_type": "Weather_Station", "os_name": "outdoor", "series": {"oat": ["var", "ENVIRONMENT", "Site Outdoor Air Drybulb Temperature"]}}
    return {"topology_id": topology_id, "nodes": list(nodes.values()), "edges": edges}


def run_energyplus(m: osm.Model, out: Path, climate: str) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    rp = m.getRunPeriod()
    rp.setBeginMonth(1); rp.setBeginDayOfMonth(1); rp.setEndMonth(12); rp.setEndDayOfMonth(31)
    for v in OUTPUT_VARIABLES:
        ov = osm.OutputVariable(v, m)
        ov.setReportingFrequency("Hourly")
    ft = openstudio.energyplus.ForwardTranslator()
    ws = ft.translateModel(m)
    idf = out / "in.idf"
    ws.save(openstudio.path(str(idf)), True)
    t0 = time.time()
    r = subprocess.run([str(EPLUS / "energyplus"), "-w", str(CLIMATES[climate]), "-d", str(out), "-i", str(EPLUS / "Energy+.idd"), str(idf)],
                       capture_output=True, text=True, timeout=1800)
    err = (out / "eplusout.err").read_text(errors="replace") if (out / "eplusout.err").exists() else ""
    severe = sum(1 for l in err.splitlines() if "** Severe" in l)
    fatal = sum(1 for l in err.splitlines() if "** Fatal" in l)
    return {"returncode": r.returncode, "severe": severe, "fatal": fatal, "seconds": round(time.time() - t0, 1), "climate": climate,
            "ok": r.returncode == 0 and severe == 0 and fatal == 0 and (out / "eplusout.sql").exists()}


def read_series(sql_path: Path, wanted: dict[tuple[str, str], str]) -> dict[str, np.ndarray]:
    """wanted: (KEY, Variable Name) -> out-key. Returns hourly arrays."""
    con = sqlite3.connect(str(sql_path))
    env = con.execute("select EnvironmentPeriodIndex from EnvironmentPeriods where EnvironmentName like 'RUN PERIOD%'").fetchone()[0]
    d = {}
    for idx, key, name, freq in con.execute("select ReportDataDictionaryIndex, KeyValue, Name, ReportingFrequency from ReportDataDictionary"):
        if freq == "Hourly" and (key.upper(), name) in wanted:
            d[idx] = wanted[(key.upper(), name)]
    out = {}
    for idx, tag in d.items():
        rows = con.execute(
            "select rd.Value from ReportData rd join Time t on rd.TimeIndex = t.TimeIndex "
            "where rd.ReportDataDictionaryIndex=? and t.EnvironmentPeriodIndex=? order by rd.TimeIndex", (idx, env)).fetchall()  # weather year only: no design days
        out[tag] = np.array([r[0] for r in rows], dtype=np.float64)
    con.close()
    return out


def simulate_topology(topology_id: str, out_root: Path) -> dict:
    out = out_root / topology_id
    m = load_model(topology_id)
    graph = extract_graph(m, topology_id)
    run = run_energyplus(m, out, TOPOLOGIES[topology_id][2])
    if not run["ok"]:
        raise RuntimeError(f"{topology_id}: EnergyPlus did not run cleanly: {run}")
    wanted, tagmap = {}, {}
    for n in graph["nodes"]:
        for sig, spec in n["series"].items():
            if spec[0] == "node":
                key, var = spec[1], spec[2]
            else:
                key, var = spec[1], spec[2]
            wanted[(key, var)] = f"{n['id']}|{sig}"
    # a (key,var) pair can be shared by several nodes (e.g. a sensor and its host): map to a list
    multi: dict[tuple[str, str], list[str]] = {}
    for n in graph["nodes"]:
        for sig, spec in n["series"].items():
            multi.setdefault((spec[1], spec[2]), []).append(f"{n['id']}|{sig}")
    raw = read_series(out / "eplusout.sql", {k: "|".join(v) for k, v in multi.items()})
    arrays = {}
    for joined, arr in raw.items():
        for tag in joined.split("|", 0) if False else [t for t in _split_tags(joined)]:
            arrays[tag] = arr
    missing = [t for tags in multi.values() for t in tags if t not in arrays]
    if missing:
        raise RuntimeError(f"{topology_id}: series missing from SQL: {missing[:8]} (+{len(missing) - 8 if len(missing) > 8 else 0})")
    np.savez_compressed(out / "evidence.npz", **{k.replace("|", "__"): v for k, v in arrays.items()})
    (out / "graph.json").write_text(json.dumps(graph, indent=1))
    run["n_hours"] = int(len(next(iter(arrays.values()))))
    run["n_series"] = len(arrays)
    (out / "run.json").write_text(json.dumps(run, indent=1))
    return run


def _split_tags(joined: str) -> list[str]:
    # tags look like "NODE-3|signal"; several tags joined with '|' -> ["NODE-3","signal","NODE-4","signal"]
    parts = joined.split("|")
    return [f"{parts[i]}|{parts[i + 1]}" for i in range(0, len(parts), 2)]
