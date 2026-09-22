"""Programmatic, physically valid multi-AHU VAV-reheat OpenStudio models.

Vendored `multiple_airloops.osm` / `multiple_loops_w_plenums.osm` were
inspected and rejected: both AHUs serve the *same* 10 zones (20 terminals on
10 zones), so "which AHU serves this VAV" has no clean ground truth. Instead
we keep the envelope, schedules and loads of NREL/OpenStudio-resources
`baseline_sys07.osm`, strip its HVAC, and rebuild the HVAC from a zone-group
spec: each AHU serves a disjoint zone group, every VAV has its own hydronic
reheat coil on a demand branch of a hot-water loop, every AHU has a hot-water
heating coil and a chilled-water cooling coil, and each loop has its own
pump and boiler / air-cooled chiller.

The buildings are correct. Documentation faults are applied later, on paper
only (see corruptions.py); nothing here is ever "rewired".
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import openstudio
from openstudio import model as osm

RESOURCES = Path(__file__).resolve().parents[3] / "physics_pipeline" / "vendor" / "OpenStudio-resources" / "model" / "simulationtests"


@dataclass(frozen=True)
class SystemSpec:
    """ahu_zone_groups: zone-name substrings per AHU. ahu_hw / ahu_chw: which
    loop index each AHU's coils (heating coil + its VAV reheat coils, cooling
    coil) sit on."""

    topology_id: str
    ahu_zone_groups: tuple[tuple[str, ...], ...]
    ahu_hw: tuple[int, ...]
    ahu_chw: tuple[int, ...]
    n_hw: int
    n_chw: int


def _load_base() -> osm.Model:
    tr = openstudio.osversion.VersionTranslator()
    m = tr.loadModel(openstudio.path(str(RESOURCES / "baseline_sys07.osm"))).get()
    for al in m.getAirLoopHVACs():
        al.remove()
    for pl in m.getPlantLoops():
        pl.remove()
    for z in m.getThermalZones():
        for e in z.equipment():
            e.remove()
    return m


def _const(m, value, name):
    s = osm.ScheduleConstant(m)
    s.setValue(value)
    s.setName(name)
    return s


def _plant_common(m, pl, kind: str, idx: int):
    sp = pl.sizingPlant()
    if kind == "hw":
        sp.setLoopType("Heating")
        sp.setDesignLoopExitTemperature(82.0)
        sp.setLoopDesignTemperatureDifference(11.0)
        setpoint = 82.0
    else:
        sp.setLoopType("Cooling")
        sp.setDesignLoopExitTemperature(7.0)
        sp.setLoopDesignTemperatureDifference(6.0)
        setpoint = 7.0
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
    bypass = osm.PipeAdiabatic(m)
    pl.addSupplyBranchForComponent(bypass)
    osm.PipeAdiabatic(m).addToNode(pl.supplyOutletNode())
    sm = osm.SetpointManagerScheduled(m, _const(m, setpoint, f"{kind}{idx} temp sp"))
    sm.addToNode(pl.supplyOutletNode())
    pl.addDemandBranchForComponent(osm.PipeAdiabatic(m))
    return pump, src


def build_vav_model(spec: SystemSpec) -> osm.Model:
    m = _load_base()
    on = m.alwaysOnDiscreteSchedule()
    hw, chw = [], []
    for i in range(spec.n_hw):
        pl = osm.PlantLoop(m)
        pl.setName(f"Hot Water Loop {i + 1}")
        _plant_common(m, pl, "hw", i + 1)
        hw.append(pl)
    for i in range(spec.n_chw):
        pl = osm.PlantLoop(m)
        pl.setName(f"Chilled Water Loop {i + 1}")
        _plant_common(m, pl, "chw", i + 1)
        chw.append(pl)

    zones = list(m.getThermalZones())
    claimed: set[str] = set()
    for a, group in enumerate(spec.ahu_zone_groups):
        al = osm.AirLoopHVAC(m)
        al.setName(f"AHU {a + 1}")
        ss = al.sizingSystem()
        ss.setCentralCoolingDesignSupplyAirTemperature(12.8)
        ss.setCentralHeatingDesignSupplyAirTemperature(12.8)
        # mirror baseline_sys07's AHU sizing exactly (an earlier draft sized on
        # ventilation load only -> ~40x undersized fans and zones at 0..40 C)
        ss.setTypeofLoadtoSizeOn("Sensible")
        ss.setAllOutdoorAirinCooling(True)
        ss.setAllOutdoorAirinHeating(True)
        ss.setSizingOption("NonCoincident")
        ss.setPreheatDesignTemperature(7.0)

        oa = osm.AirLoopHVACOutdoorAirSystem(m, osm.ControllerOutdoorAir(m))
        oa.setName(f"AHU {a + 1} OA System")
        oa.addToNode(al.supplyInletNode())
        fan = osm.FanVariableVolume(m, on)
        fan.setName(f"AHU {a + 1} Fan")
        fan.setPressureRise(500.0)
        fan.setFanTotalEfficiency(0.6045)
        fan.addToNode(al.supplyOutletNode())
        heat = osm.CoilHeatingWater(m, on)
        heat.setName(f"AHU {a + 1} Heating Coil")
        hw[spec.ahu_hw[a]].addDemandBranchForComponent(heat)
        heat.addToNode(al.supplyOutletNode())
        cool = osm.CoilCoolingWater(m, on)
        cool.setName(f"AHU {a + 1} Cooling Coil")
        chw[spec.ahu_chw[a]].addDemandBranchForComponent(cool)
        cool.addToNode(al.supplyOutletNode())
        # Distinct constant SAT setpoints per AHU (realistic: AHUs are commissioned
        # independently). Without this the built AHUs would be byte-identical in SAT
        # and every SAT-sensor swap would be unobservable by construction.
        sat = _const(m, SAT_SETPOINTS[a % len(SAT_SETPOINTS)], f"AHU {a + 1} SAT sp")
        for comp in (heat, cool):
            n = comp.airOutletModelObject().get().to_Node().get()
            osm.SetpointManagerScheduled(m, sat).addToNode(n)
        osm.SetpointManagerScheduled(m, sat).addToNode(al.supplyOutletNode())
        oa_ctrl = oa.getControllerOutdoorAir()
        mixed = oa.mixedAirModelObject().get().to_Node().get()
        osm.SetpointManagerMixedAir(m).addToNode(mixed)

        for z in zones:
            name = z.name().get()
            space_name = z.spaces()[0].name().get()  # zone names are "Thermal Zone N"; geometry is in the space name
            if name in claimed or not any(g in space_name for g in group):
                continue
            claimed.add(name)
            rc = osm.CoilHeatingWater(m, on)
            rc.setName(f"VAV {name} Reheat Coil")
            hw[spec.ahu_hw[a]].addDemandBranchForComponent(rc)
            term = osm.AirTerminalSingleDuctVAVReheat(m, on, rc)
            term.setName(f"VAV {name}")
            term.setZoneMinimumAirFlowInputMethod("Constant")
            term.setConstantMinimumAirFlowFraction(0.3)
            al.addBranchForZone(z, term)
    unclaimed = [z.name().get() for z in zones if z.name().get() not in claimed]
    if unclaimed:
        raise ValueError(f"zones without an AHU: {unclaimed}")
    return m


SAT_SETPOINTS = (12.2, 13.3, 12.8)

# Zone-name groups (sys07 envelope: 2 stories x {N,S,E,W perimeter, core}).
S1 = ("Story 1",)
S2 = ("Story 2",)
SPECS: dict[str, SystemSpec] = {
    # C: two AHUs by floor, each with its own HW and CHW loop.
    "vav_2ahu_2loops": SystemSpec("vav_2ahu_2loops", (S1, S2), (0, 1), (0, 1), 2, 2),
    # D: three AHUs (floor-1 perimeter+core split N/S+core vs E/W?) with shared HW loop pairs:
    #    AHU1 = N+S perimeters (both floors), AHU2 = E+W perimeters, AHU3 = cores.
    "vav_3ahu_2loops": SystemSpec(
        "vav_3ahu_2loops",
        (("North Perimeter", "South Perimeter"), ("East Perimeter", "West Perimeter"), ("Core",)),
        (0, 1, 0),
        (0, 1, 0),
        2,
        2,
    ),
}
