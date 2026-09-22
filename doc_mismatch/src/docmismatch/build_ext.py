"""Parametric multi-AHU VAV-reheat buildings for the simulation expansion (dev_E..dev_H, seal_S1..seal_S4).

Unlike `build_models.py` (which reuses the fixed 10-zone baseline_sys07 envelope), this module also builds the
ENVELOPE from a spec: a `floors x nx x ny` grid of equal rectangular zones, so the number of VAV boxes can be
6..16, with per-zone load scaling, occupancy schedules, setpoints with setback, window ratio, infiltration and
geometry varying by spec. Constructions / space-type schedules come from the same vendored baseline_sys07 model
(ASHRAE 189.1 climate-zone 4-5 construction set is reused in every climate -- it is NOT climate-adapted).

The building is always correct; only documentation is corrupted later (corruptions.py).
Registration into `physical.TOPOLOGIES` is explicit (`register_from_spec`), so importing this module changes nothing.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import openstudio
from openstudio import model as osm

from .build_models import _const, _load_base
from . import physical

PP = Path(__file__).resolve().parents[3] / "physics_pipeline" / "vendor"
EP_W = PP / "EnergyPlus-25.2.0-cf7368216c-Darwin-macOS13-arm64" / "WeatherData"
OS_W = PP / "OpenStudio-resources" / "WeatherData"

# climate key -> (epw, ddy). All vendored in the repo; nothing is downloaded.
CLIMATE_FILES: dict[str, tuple[Path, Path]] = {
    "sterling_va": (EP_W / "USA_VA_Sterling-Washington.Dulles.Intl.AP.724030_TMY3.epw", EP_W / "USA_VA_Sterling-Washington.Dulles.Intl.AP.724030_TMY3.ddy"),
    "sanfrancisco": (EP_W / "USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw", EP_W / "USA_CA_San.Francisco.Intl.AP.724940_TMY3.ddy"),
    "golden": (EP_W / "USA_CO_Golden-NREL.724666_TMY3.epw", EP_W / "USA_CO_Golden-NREL.724666_TMY3.ddy"),
    "tampa": (EP_W / "USA_FL_Tampa.Intl.AP.722110_TMY3.epw", EP_W / "USA_FL_Tampa.Intl.AP.722110_TMY3.ddy"),
    "chicago_amy2012": (OS_W / "USA_IL_Chicago-OHare.Intl.AP.725300_AMY_2012_NonLeapYear.epw", OS_W / "USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.ddy"),
    "chicago_amy2013": (OS_W / "USA_IL_Chicago-OHare.Intl.AP.725300_AMY_2013.epw", OS_W / "USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.ddy"),
    "sacramento": (OS_W / "SACRAMENTO-EXECUTIVE_724830_CZ2010.epw", OS_W / "SACRAMENTO-EXECUTIVE_724830_CZ2010.DDY"),
    "palm_springs": (OS_W / "PALM-SPRINGS-INTL_722868_CZ2010.epw", OS_W / "PALM-SPRINGS-INTL_722868_CZ2010.DDY"),
    "arcata": (OS_W / "ARCATA_725945_CZ2010.epw", OS_W / "ARCATA_725945_CZ2010.DDY"),
    "blue_canyon": (OS_W / "BLUE-CANYON_725845_CZ2010.epw", OS_W / "BLUE-CANYON_725845_CZ2010.DDY"),
}


def _t(h: float):
    q = round(h * 6) / 6.0  # snap to the 10-minute timestep
    return openstudio.Time(0, int(q), int(round((q - int(q)) * 60)), 0)


def _profile_sched(m, name: str, start: float, end: float, low: float, weekend: float, peak: float = 1.0):
    """Weekday: `low` outside [start, end), `peak` inside with a 1 h ramp at both ends and a lunch dip; weekends constant `weekend`."""
    s = osm.ScheduleRuleset(m)
    s.setName(name)
    d = s.defaultDaySchedule()
    ramp_hi = (low + peak) / 2
    pts = [(start - 1, low), (start, ramp_hi), (12, peak), (13, 0.85 * peak), (end - 1, peak), (end, ramp_hi), (24, low)]
    for h, v in pts:
        d.addValue(_t(h), float(v))
    r = osm.ScheduleRule(s)
    r.setApplySaturday(True)
    r.setApplySunday(True)
    r.daySchedule().addValue(_t(24), float(weekend))
    return s


def _setpoint_sched(m, name: str, start: float, end: float, occ: float, unocc: float):
    s = osm.ScheduleRuleset(m)
    s.setName(name)
    d = s.defaultDaySchedule()
    for h, v in ((start - 1, unocc), (end + 1, occ), (24, unocc)):
        d.addValue(_t(h), float(v))
    r = osm.ScheduleRule(s)
    r.setApplySaturday(True)
    r.setApplySunday(True)
    r.daySchedule().addValue(_t(24), float(unocc))
    return s


def zone_grid(spec: dict) -> list[tuple[int, int, int]]:
    """Scan order of zones: (floor, row, col)."""
    return [(f, j, i) for f in range(spec["floors"]) for j in range(spec["ny"]) for i in range(spec["nx"])]


def ahu_assignment(spec: dict) -> list[int]:
    """AHU index of each zone (indexed like zone_grid). `block`: consecutive in scan order; `stripe`: by column, then floor/row."""
    grid = zone_grid(spec)
    order = list(range(len(grid))) if spec["group_mode"] == "block" else sorted(range(len(grid)), key=lambda k: (grid[k][2], grid[k][0], grid[k][1]))
    out = [-1] * len(grid)
    pos = 0
    for a, sz in enumerate(spec["group_sizes"]):
        for k in order[pos:pos + sz]:
            out[k] = a
        pos += sz
    assert pos == len(grid) and min(out) >= 0
    return out


def _build_envelope(m, spec: dict, rng: random.Random):
    for s in list(m.getSpaces()):
        s.remove()
    for z in list(m.getThermalZones()):
        z.remove()
    for st in list(m.getBuildingStorys()):
        st.remove()
    m.getBuilding().setNorthAxis(float(spec["north_axis"]))
    w, dpt, h = spec["tile_w"], spec["tile_d"], spec["floor_h"]
    o = spec["occ"]
    sp = spec["setpoints"]
    scheds: dict = {}

    def sched(kind: str, shift: int):
        key = (kind, shift)
        if key not in scheds:
            a, b = o["start"] + shift, o["end"] + shift
            if kind == "people":
                scheds[key] = _profile_sched(m, f"people s{shift}", a, b, o["night_frac"], o["weekend_frac"])
            elif kind == "lights":
                scheds[key] = _profile_sched(m, f"lights s{shift}", a, b, min(1.0, o["night_frac"] + 0.05), min(1.0, o["weekend_frac"] + 0.05))
            elif kind == "equip":
                scheds[key] = _profile_sched(m, f"equip s{shift}", a, b, min(1.0, o["night_frac"] + 0.25), min(1.0, o["weekend_frac"] + 0.25))
            elif kind == "heat":
                scheds[key] = _setpoint_sched(m, f"heat sp s{shift}", a, b, sp["heat"], sp["heat_setback"])
            else:
                scheds[key] = _setpoint_sched(m, f"cool sp s{shift}", a, b, sp["cool"], sp["cool_setback"])
        return scheds[key]

    activity = m.getScheduleByName("Baseline Model People Activity Schedule").get()
    stories = [osm.BuildingStory(m) for _ in range(spec["floors"])]
    for i, st in enumerate(stories):
        st.setName(f"Story {i + 1}")
    spaces, zones = [], []
    for k, (f, j, i) in enumerate(zone_grid(spec)):
        x0, y0 = i * w, j * dpt
        # floor print must be clockwise seen from above (outward normal down)
        pts = [openstudio.Point3d(x0, y0, 0), openstudio.Point3d(x0, y0 + dpt, 0), openstudio.Point3d(x0 + w, y0 + dpt, 0), openstudio.Point3d(x0 + w, y0, 0)]
        sp_ = osm.Space.fromFloorPrint(pts, h, m).get()
        sp_.setName(f"Story {f + 1} Tile r{j}c{i} Space")
        sp_.setZOrigin(f * h)
        sp_.setBuildingStory(stories[f])
        z = osm.ThermalZone(m)
        z.setName(f"Thermal Zone {k + 1}")
        sp_.setThermalZone(z)
        spaces.append(sp_)
        zones.append(z)
        area = sp_.floorArea()
        scale = rng.lognormvariate(0.0, spec["zone_load_sigma"])
        shift = rng.choice(spec["zone_shifts"])
        ld = osm.LightsDefinition(m)
        ld.setName(f"lights def {k + 1}")
        ld.setWattsperSpaceFloorArea(spec["lights_wm2"] * scale)
        l = osm.Lights(ld)
        l.setSpace(sp_)
        l.setSchedule(sched("lights", shift))
        ed = osm.ElectricEquipmentDefinition(m)
        ed.setName(f"equip def {k + 1}")
        ed.setWattsperSpaceFloorArea(spec["equip_wm2"] * scale)
        e = osm.ElectricEquipment(ed)
        e.setSpace(sp_)
        e.setSchedule(sched("equip", shift))
        pd = osm.PeopleDefinition(m)
        pd.setName(f"people def {k + 1}")
        pd.setPeopleperSpaceFloorArea(spec["people_m2"] * scale)
        p = osm.People(pd)
        p.setSpace(sp_)
        p.setNumberofPeopleSchedule(sched("people", shift))
        p.setActivityLevelSchedule(activity)
        oa = osm.DesignSpecificationOutdoorAir(m)
        oa.setName(f"OA spec {k + 1}")
        oa.setOutdoorAirMethod("Sum")
        oa.setOutdoorAirFlowperPerson(0.00944)
        oa.setOutdoorAirFlowperFloorArea(spec["oa_per_area"])
        sp_.setDesignSpecificationOutdoorAir(oa)
        inf = osm.SpaceInfiltrationDesignFlowRate(m)
        inf.setName(f"infiltration {k + 1}")
        inf.setFlowperExteriorSurfaceArea(spec["infiltration"])
        inf.setSpace(sp_)
        th = osm.ThermostatSetpointDualSetpoint(m)
        th.setName(f"thermostat {k + 1}")
        th.setHeatingSetpointTemperatureSchedule(sched("heat", shift))
        th.setCoolingSetpointTemperatureSchedule(sched("cool", shift))
        z.setThermostatSetpointDualSetpoint(th)
    osm.matchSurfaces(osm.SpaceVector(spaces))
    for s in spaces:
        for sf in s.surfaces():
            if sf.surfaceType() == "Floor" and sf.outsideBoundaryCondition() != "Surface":
                sf.setOutsideBoundaryCondition("Ground")
            if sf.surfaceType() == "Wall" and sf.outsideBoundaryCondition() == "Outdoors":
                sf.setWindowToWallRatio(spec["wwr"])
    sp = m.getSizingParameters()
    sp.setHeatingSizingFactor(spec["heat_sizing_factor"])
    sp.setCoolingSizingFactor(spec["cool_sizing_factor"])
    return zones


def _ddy_objects(ddy: Path) -> list[str]:
    """Annual heating/cooling SizingPeriod:DesignDay objects of a DDY file, parsed as text (some CZ2010 files contain
    monthly design days that fail the IDD range check, so the file cannot be loaded whole)."""
    txt = "\n".join(l.split("!")[0] for l in ddy.read_text(errors="replace").splitlines())
    keep = []
    for obj in txt.split(";"):
        o = obj.strip()
        if not o.startswith("SizingPeriod:DesignDay"):
            continue
        name = o.split(",")[1]
        if "Ann Htg 99.6% Condns DB" in name or ("Ann Clg" in name and any(k in name for k in ("DB=>MCWB", "DB=>MWB", "WB=>MDB"))):
            keep.append(o + ";")
    return keep


def _add_design_days(m, climate: str):
    import tempfile
    epw, ddy = CLIMATE_FILES[climate]
    objs = _ddy_objects(ddy)
    if not objs:
        raise RuntimeError(f"no annual design days found in {ddy}")
    for d in list(m.getDesignDays()):
        d.remove()
    with tempfile.NamedTemporaryFile("w", suffix=".idf", delete=False) as f:
        f.write("Version,25.2;\n" + "\n".join(objs) + "\n")
    dm = openstudio.energyplus.ReverseTranslator().loadModel(openstudio.path(f.name)).get()
    Path(f.name).unlink()
    for d in dm.getDesignDays():
        d.clone(m)
    osm.WeatherFile.setWeatherFile(m, openstudio.EpwFile(openstudio.path(str(epw))))
    return len(objs)


def _plant(m, kind: str, idx: int, t_sup: float, dt: float):
    pl = osm.PlantLoop(m)
    pl.setName(("Hot" if kind == "hw" else "Chilled") + f" Water Loop {idx}")
    sp = pl.sizingPlant()
    sp.setLoopType("Heating" if kind == "hw" else "Cooling")
    sp.setDesignLoopExitTemperature(t_sup)
    sp.setLoopDesignTemperatureDifference(dt)
    pump = osm.PumpVariableSpeed(m)
    pump.setName(f"{kind.upper()} Pump {idx}")
    pump.addToNode(pl.supplyInletNode())
    if kind == "hw":
        src = osm.BoilerHotWater(m)
        src.setName(f"HW Boiler {idx}")
    else:
        src = osm.ChillerElectricEIR(m)
        src.setName(f"CHW Chiller {idx}")
        src.setCondenserType("AirCooled")
    pl.addSupplyBranchForComponent(src)
    pl.addSupplyBranchForComponent(osm.PipeAdiabatic(m))
    osm.PipeAdiabatic(m).addToNode(pl.supplyOutletNode())
    osm.SetpointManagerScheduled(m, _const(m, t_sup, f"{kind}{idx} temp sp")).addToNode(pl.supplyOutletNode())
    pl.addDemandBranchForComponent(osm.PipeAdiabatic(m))
    return pl


def build_ext_model(spec: dict) -> osm.Model:
    rng = random.Random(spec["geometry_seed"])
    m = _load_base()
    zones = _build_envelope(m, spec, rng)
    _add_design_days(m, spec["climate"])
    sc = m.getSimulationControl()
    sc.setDoZoneSizingCalculation(True)
    sc.setDoSystemSizingCalculation(True)
    sc.setDoPlantSizingCalculation(True)
    on = m.alwaysOnDiscreteSchedule()
    hw = [_plant(m, "hw", i + 1, spec["hw_t"][i], spec["hw_dt"][i]) for i in range(spec["n_hw"])]
    chw = [_plant(m, "chw", i + 1, spec["chw_t"][i], spec["chw_dt"][i]) for i in range(spec["n_chw"])]
    assign = ahu_assignment(spec)
    vrng = random.Random(spec["geometry_seed"] + 1)
    for a in range(spec["n_ahu"]):
        sat_c = spec["ahu_sat"][a]
        al = osm.AirLoopHVAC(m)
        al.setName(f"AHU {a + 1}")
        ss = al.sizingSystem()
        ss.setCentralCoolingDesignSupplyAirTemperature(sat_c)
        ss.setCentralHeatingDesignSupplyAirTemperature(sat_c)
        # mirror baseline_sys07's AHU sizing (ventilation-only sizing made an earlier draft ~40x undersized)
        ss.setTypeofLoadtoSizeOn("Sensible")
        ss.setAllOutdoorAirinCooling(True)
        ss.setAllOutdoorAirinHeating(True)
        ss.setSizingOption("NonCoincident")
        ss.setPreheatDesignTemperature(7.0)
        ctrl = osm.ControllerOutdoorAir(m)
        ctrl.setEconomizerControlType("FixedDryBulb" if spec["economizer"][a] else "NoEconomizer")
        oa = osm.AirLoopHVACOutdoorAirSystem(m, ctrl)
        oa.setName(f"AHU {a + 1} OA System")
        oa.addToNode(al.supplyInletNode())
        fan = osm.FanVariableVolume(m, on)
        fan.setName(f"AHU {a + 1} Fan")
        fan.setPressureRise(spec["fan_dp"][a])
        fan.setFanTotalEfficiency(0.6045)
        fan.addToNode(al.supplyOutletNode())
        heat = osm.CoilHeatingWater(m, on)
        heat.setName(f"AHU {a + 1} Heating Coil")
        hw[spec["ahu_hw"][a]].addDemandBranchForComponent(heat)
        heat.addToNode(al.supplyOutletNode())
        cool = osm.CoilCoolingWater(m, on)
        cool.setName(f"AHU {a + 1} Cooling Coil")
        chw[spec["ahu_chw"][a]].addDemandBranchForComponent(cool)
        cool.addToNode(al.supplyOutletNode())
        sat = _const(m, sat_c, f"AHU {a + 1} SAT sp")
        for comp in (heat, cool):
            osm.SetpointManagerScheduled(m, sat).addToNode(comp.airOutletModelObject().get().to_Node().get())
        osm.SetpointManagerScheduled(m, sat).addToNode(al.supplyOutletNode())
        osm.SetpointManagerMixedAir(m).addToNode(oa.mixedAirModelObject().get().to_Node().get())
        for k, z in enumerate(zones):
            if assign[k] != a:
                continue
            z.sizingZone().setZoneCoolingDesignSupplyAirTemperature(sat_c)
            rc = osm.CoilHeatingWater(m, on)
            rc.setName(f"VAV {z.name().get()} Reheat Coil")
            hw[spec["ahu_hw"][a]].addDemandBranchForComponent(rc)
            term = osm.AirTerminalSingleDuctVAVReheat(m, on, rc)
            term.setName(f"VAV {z.name().get()}")
            term.setZoneMinimumAirFlowInputMethod("Constant")
            term.setConstantMinimumAirFlowFraction(max(0.1, min(0.6, spec["min_flow_frac"] + vrng.uniform(-0.05, 0.05))))
            al.addBranchForZone(z, term)
    return m


# ------------------------------------------------------------------ registration into physical.py
def load_spec(path: Path) -> dict:
    return json.loads(Path(path).read_text())


def register_from_spec(spec_path: Path, only: list[str] | None = None) -> list[str]:
    """Adds spec topologies to physical.TOPOLOGIES / CLIMATES / EXT_BUILDERS (idempotent). Returns the registered ids."""
    spec = load_spec(spec_path)
    ids = []
    for t in spec["topologies"]:
        tid = t["id"]
        if only and tid not in only:
            continue
        physical.CLIMATES[t["climate"]] = CLIMATE_FILES[t["climate"]][0]
        physical.TOPOLOGIES[tid] = ("ext", tid, t["climate"])
        physical.EXT_BUILDERS[tid] = (lambda t=t: build_ext_model(t))
        ids.append(tid)
    return ids
