"""OpenStudio builder for domain-randomized VAV buildings (extends `build_ext` without editing it).

Reuses `build_ext._build_envelope` / `_add_design_days` / `_plant` and adds the DR controls listed in PREREGISTRATION_DR.md:
SAT strategy (constant / OA reset / warmest-zone / time-of-day), static-pressure reset (emulated through the fan power curve: fan power only), economizer type + limit,
occupancy-scheduled minimum OA, boiler / chiller / fan efficiencies, electric / hydronic / mixed VAV reheat, weather transform (EPW copy).
The building is always physically correct; only documentation is corrupted later.
"""

from __future__ import annotations

import random
from pathlib import Path

import openstudio
from openstudio import model as osm

from .. import build_ext as BX
from .. import physical
from ..build_models import _const, _load_base
from .spec import ECON_OS

REPO = Path(__file__).resolve().parents[4]
DR_ROOT = REPO / "results" / "docmismatch_dr"
WX_DIR = DR_ROOT / "weather"

# climates not in build_ext.CLIMATE_FILES
BX.CLIMATE_FILES.setdefault("chicago_tmy3", (BX.EP_W / "USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw", BX.EP_W / "USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.ddy"))
BX.CLIMATE_FILES.setdefault("oakland", (BX.OS_W / "OAKLAND_724930_CZ2010.epw", BX.OS_W / "OAKLAND_724930_CZ2010.DDY"))
BX.CLIMATE_FILES.setdefault("los_angeles", (BX.OS_W / "LOS-ANGELES-INTL_722950_CZ2010.epw", BX.OS_W / "LOS-ANGELES-INTL_722950_CZ2010.DDY"))

# ASHRAE 90.1 VAV fan curves: (c1..c5) fixed-pressure vs static-pressure-reset (VSD, optimised)
FAN_FIXED = (0.0013, 0.1470, 0.9506, -0.0998, 0.0)
FAN_RESET = (0.040759894, 0.08804497, -0.07292612, 0.94373, 0.0)


def transform_epw(src: Path, dst: Path, temp_offset: float, solar_scale: float) -> Path:
    """Copy of an EPW with dry-bulb and dew-point shifted by `temp_offset` K and global/direct/diffuse solar scaled. Date/time columns untouched."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    lines = src.read_text(errors="replace").splitlines()
    out = []
    for i, ln in enumerate(lines):
        if i < 8:
            out.append(ln)
            continue
        f = ln.split(",")
        try:
            f[6] = f"{float(f[6]) + temp_offset:.1f}"
            f[7] = f"{float(f[7]) + temp_offset:.1f}"
            for k in (13, 14, 15):
                f[k] = f"{max(0.0, float(f[k]) * solar_scale):.0f}"
        except (ValueError, IndexError):
            pass
        out.append(",".join(f))
    dst.write_text("\n".join(out) + "\n")
    return dst


def _min_oa_sched(m, spec: dict):
    """1.0 while occupied, `night_oa` outside (scales the controller's minimum OA flow); None when night_oa == 1 (always full minimum)."""
    if spec["night_oa"] >= 0.999:
        return None
    o = spec["occ"]
    return BX._profile_sched(m, "min OA sched", o["start"], o["end"], spec["night_oa"], spec["night_oa"], peak=1.0)


def _tune_plant(pl, kind: str, spec: dict):
    for c in pl.supplyComponents():
        if kind == "hw" and c.to_BoilerHotWater().is_initialized():
            c.to_BoilerHotWater().get().setNominalThermalEfficiency(spec["boiler_eff"])
        if kind == "chw" and c.to_ChillerElectricEIR().is_initialized():
            c.to_ChillerElectricEIR().get().setReferenceCOP(spec["chiller_cop"])


def build_dr_model(spec: dict) -> osm.Model:
    rng = random.Random(spec["geometry_seed"])
    m = _load_base()
    zones = BX._build_envelope(m, spec, rng)
    BX._add_design_days(m, spec["climate"])
    sc = m.getSimulationControl()
    sc.setDoZoneSizingCalculation(True)
    sc.setDoSystemSizingCalculation(True)
    sc.setDoPlantSizingCalculation(True)
    on = m.alwaysOnDiscreteSchedule()
    hw = [BX._plant(m, "hw", i + 1, spec["hw_t"][i], spec["hw_dt"][i]) for i in range(spec["n_hw"])]
    chw = [BX._plant(m, "chw", i + 1, spec["chw_t"][i], spec["chw_dt"][i]) for i in range(spec["n_chw"])]
    for p in hw:
        _tune_plant(p, "hw", spec)
    for p in chw:
        _tune_plant(p, "chw", spec)
    assign = BX.ahu_assignment(spec)
    vrng = random.Random(spec["geometry_seed"] + 1)
    min_oa = _min_oa_sched(m, spec)
    for a in range(spec["n_ahu"]):
        sat_c = spec["ahu_sat"][a]
        al = osm.AirLoopHVAC(m)
        al.setName(f"AHU {a + 1}")
        ss = al.sizingSystem()
        ss.setCentralCoolingDesignSupplyAirTemperature(sat_c)
        ss.setCentralHeatingDesignSupplyAirTemperature(sat_c)
        ss.setTypeofLoadtoSizeOn("Sensible")
        ss.setAllOutdoorAirinCooling(True)
        ss.setAllOutdoorAirinHeating(True)
        ss.setSizingOption("NonCoincident")
        ss.setPreheatDesignTemperature(7.0)
        ctrl = osm.ControllerOutdoorAir(m)
        et = spec["econ_type"][a]
        ctrl.setEconomizerControlType(ECON_OS[et])
        if et == "fixed_db":
            ctrl.setEconomizerMaximumLimitDryBulbTemperature(spec["econ_limit_db"][a])
        elif et == "fixed_enth":
            ctrl.setEconomizerMaximumLimitEnthalpy(spec["econ_limit_enth"][a])
        if min_oa is not None:
            ctrl.setMinimumOutdoorAirSchedule(min_oa)
        oas = osm.AirLoopHVACOutdoorAirSystem(m, ctrl)
        oas.setName(f"AHU {a + 1} OA System")
        oas.addToNode(al.supplyInletNode())
        fan = osm.FanVariableVolume(m, on)
        fan.setName(f"AHU {a + 1} Fan")
        fan.setPressureRise(spec["fan_dp"][a])
        fan.setFanTotalEfficiency(spec["fan_eff"])
        cf = FAN_RESET if spec["sp_reset"][a] else FAN_FIXED
        for k, v in enumerate(cf, 1):
            getattr(fan, f"setFanPowerCoefficient{k}")(v)
        fan.addToNode(al.supplyOutletNode())
        heat = osm.CoilHeatingWater(m, on)
        heat.setName(f"AHU {a + 1} Heating Coil")
        hw[spec["ahu_hw"][a]].addDemandBranchForComponent(heat)
        heat.addToNode(al.supplyOutletNode())
        cool = osm.CoilCoolingWater(m, on)
        cool.setName(f"AHU {a + 1} Cooling Coil")
        chw[spec["ahu_chw"][a]].addDemandBranchForComponent(cool)
        cool.addToNode(al.supplyOutletNode())
        strat = spec["sat_strategy"][a]
        rs = spec["sat_reset"][a]
        nodes = [heat.airOutletModelObject().get().to_Node().get(), cool.airOutletModelObject().get().to_Node().get(), al.supplyOutletNode()]
        for k, node in enumerate(nodes):
            if strat == "constant":
                sp = osm.SetpointManagerScheduled(m, _const(m, sat_c, f"AHU {a + 1} SAT sp {k}"))
            elif strat == "oa_reset":
                sp = osm.SetpointManagerOutdoorAirReset(m)
                sp.setSetpointatOutdoorHighTemperature(sat_c)
                sp.setOutdoorHighTemperature(rs["oa_high"])
                sp.setSetpointatOutdoorLowTemperature(sat_c + rs["span"])
                sp.setOutdoorLowTemperature(rs["oa_low"])
            elif strat == "tod_reset":  # time-of-day: SAT is `span` K warmer outside occupied hours
                sp = osm.SetpointManagerScheduled(m, BX._setpoint_sched(m, f"AHU {a + 1} SAT tod {k}", spec["occ"]["start"], spec["occ"]["end"], sat_c, sat_c + rs["span"]))
            else:  # warmest-zone reset
                sp = osm.SetpointManagerWarmest(m)
                sp.setMinimumSetpointTemperature(sat_c)
                sp.setMaximumSetpointTemperature(sat_c + rs["span"])
            sp.addToNode(node)
        osm.SetpointManagerMixedAir(m).addToNode(oas.mixedAirModelObject().get().to_Node().get())
        for k, z in enumerate(zones):
            if assign[k] != a:
                continue
            z.sizingZone().setZoneCoolingDesignSupplyAirTemperature(sat_c)
            electric = spec["reheat"] == "electric" or (spec["reheat"] == "mixed" and spec["electric_zones"][k])
            if electric:
                rc = osm.CoilHeatingElectric(m, on)
                rc.setName(f"VAV {z.name().get()} Reheat Coil")
            else:
                rc = osm.CoilHeatingWater(m, on)
                rc.setName(f"VAV {z.name().get()} Reheat Coil")
                hw[spec["ahu_hw"][a]].addDemandBranchForComponent(rc)
            term = osm.AirTerminalSingleDuctVAVReheat(m, on, rc)
            term.setName(f"VAV {z.name().get()}")
            term.setZoneMinimumAirFlowInputMethod("Constant")
            term.setConstantMinimumAirFlowFraction(max(0.1, min(0.6, spec["min_flow_frac"] + vrng.uniform(-0.05, 0.05))))
            al.addBranchForZone(z, term)
    return m


def register(spec: dict) -> str:
    """Register one DR spec in physical.TOPOLOGIES with its (transformed) weather file. Returns the climate key used."""
    w = spec["weather"]
    src = BX.CLIMATE_FILES[w["climate"]][0]
    key = f"{spec['id']}_wx"
    if w["temp_offset"] == 0.0 and w["solar_scale"] == 1.0:
        physical.CLIMATES[key] = src
    else:
        physical.CLIMATES[key] = transform_epw(src, WX_DIR / f"{spec['id']}.epw", w["temp_offset"], w["solar_scale"])
    physical.TOPOLOGIES[spec["id"]] = ("ext", spec["id"], key)
    physical.EXT_BUILDERS[spec["id"]] = (lambda s=spec: build_dr_model(s))
    return key
