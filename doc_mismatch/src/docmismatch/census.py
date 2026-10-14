"""Instrumentation census of Brick building models: for each connection type, how many buildings document (and record) the points that each evidence channel reads?

Metadata only -- no timeseries is read. A point counts as RECORDED when it links to a timeseries (`ref:hasExternalReference/ref:hasTimeseriesId`); DOCUMENTED means the graph lists it
at all. The channel needs are the SAME table the readiness report uses (`intake_report.CHANNEL_SIGNALS`), so a census cell means what a readiness cell means. Air-side connection
types only (`ahu_vav`, `vav_zone`, `coil_vav`, `coil_ahu`): the Mortar graphs contain no water loop, branch, valve or pump nodes at all (see `node_inventory`).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from .intake_report import CHANNEL_SIGNALS, OK_FRAC

BRICK_NS = "https://brickschema.org/schema/Brick#"
REF_NS = "https://brickschema.org/schema/Brick/ref#"
KIND_CLASSES = {"AHU": {"Air_Handler_Unit", "AHU", "RTU", "Rooftop_Unit"}, "VAV": {"VAV", "RVAV", "CAV"}, "Zone": {"HVACZone", "HVAC_Zone"},
                "Coil": {"Heating_Coil", "Cooling_Coil", "Coil"}}
# (equipment kind, signal) -> Brick point classes that provide it. Only classes that name the ROLE we need (supply / discharge / mixed / entering ...), never a guess from a generic class.
ROLE_CLASSES = {
    ("AHU", "flow"): {"Supply_Air_Flow_Sensor", "Discharge_Air_Flow_Sensor"}, ("AHU", "sat"): {"Supply_Air_Temperature_Sensor", "Discharge_Air_Temperature_Sensor"},
    ("AHU", "mat"): {"Mixed_Air_Temperature_Sensor"}, ("AHU", "htg"): {"Heating_Thermal_Power_Sensor"}, ("AHU", "clg"): {"Cooling_Thermal_Power_Sensor"},
    ("VAV", "flow"): {"Supply_Air_Flow_Sensor", "Discharge_Air_Flow_Sensor", "Air_Flow_Sensor"}, ("VAV", "t_dis"): {"Discharge_Air_Temperature_Sensor", "Supply_Air_Temperature_Sensor"},
    ("VAV", "t_in"): {"Entering_Air_Temperature_Sensor", "Inlet_Air_Temperature_Sensor"}, ("Zone", "temp"): {"Zone_Air_Temperature_Sensor"},
    ("Coil", "rate"): {"Heating_Thermal_Power_Sensor", "Cooling_Thermal_Power_Sensor", "Thermal_Power_Sensor"},
}
SLOT_ENDS = {"ahu_vav": ("AHU", "VAV"), "vav_zone": ("VAV", "Zone"), "coil_vav": ("VAV", "Coil"), "coil_ahu": ("AHU", "Coil")}
SLOTS = tuple(SLOT_ENDS)


@dataclass
class BrickCensus:
    building: str
    kinds: dict[str, str]                                   # node -> kind (AHU / VAV / Zone / Coil)
    points: dict[str, list[tuple[str, bool]]]               # node -> [(point class, recorded)]
    pairs: dict[str, list[tuple[str, str]]]                 # slot -> documented (owner, member)
    classes: Counter = field(default_factory=Counter)       # every node class in the graph (for the inventory)
    ts_ids: frozenset = frozenset()


def _short(x) -> str:
    return str(x).split("#")[-1].split("/")[-1]


def parse_census(ttl: str | Path, building: str | None = None) -> BrickCensus:
    from rdflib import RDF, Graph, Namespace
    B, R = Namespace(BRICK_NS), Namespace(REF_NS)
    g = Graph()
    g.parse(str(ttl), format="turtle")
    types: dict = {}
    for s, o in g.subject_objects(RDF.type):
        types.setdefault(s, []).append(_short(o))
    kinds = {}
    for s, ts in types.items():
        for kind, cls in KIND_CLASSES.items():
            if any(t in cls for t in ts):
                kinds[_short(s)] = kind
                break
    node = {_short(s): s for s in types}
    points, ids = {}, set()
    for name in kinds:
        for pt in g.objects(node[name], B.hasPoint):
            u = [str(x) for r in g.objects(pt, R.hasExternalReference) for x in g.objects(r, R.hasTimeseriesId)]
            ids.update(u)
            cls = next((t for t in types.get(pt, []) if t != "Point"), "?")
            points.setdefault(name, []).append((cls, bool(u)))
    pairs = {slot: [] for slot in SLOTS}
    for p in (B.feeds, B.hasPart, B.isPartOf):
        for s, o in g.subject_objects(p):
            a, b = _short(s), _short(o)
            ka, kb = kinds.get(a), kinds.get(b)
            if ka is None or kb is None:
                continue
            if p == B.feeds:
                for slot, (ko, km) in SLOT_ENDS.items():
                    if (ka, kb) == (ko, km) and slot in ("ahu_vav", "vav_zone"):
                        pairs[slot].append((a, b))
            elif p == B.hasPart:
                for slot in ("coil_vav", "coil_ahu"):
                    if (ka, kb) == SLOT_ENDS[slot]:
                        pairs[slot].append((a, b))
            elif p == B.isPartOf:
                for slot in ("coil_vav", "coil_ahu"):
                    if (kb, ka) == SLOT_ENDS[slot]:
                        pairs[slot].append((b, a))
    for slot in pairs:
        pairs[slot] = sorted(set(pairs[slot]))
    classes = Counter(t for ts in types.values() for t in ts if t not in ("Point", "Ontology"))
    return BrickCensus(building or Path(ttl).stem.replace("mortar__", ""), kinds, points, pairs, classes, frozenset(ids))


def has_role(bc: BrickCensus, node: str, kind: str, sig: str, recorded: bool) -> bool:
    """does `node` have a point providing (kind, sig)? A zone's temperature may also sit on a VAV that feeds it. `recorded`: the point must link to a timeseries."""
    classes = ROLE_CLASSES.get((kind, sig), set())
    hosts = [node]
    if kind == "Zone":
        hosts += [o for o, m in bc.pairs["vav_zone"] if m == node]
    return any(cls in classes and (ts or not recorded) for h in hosts for cls, ts in bc.points.get(h, []))


def channel_shares(bc: BrickCensus, slot: str, recorded: bool = True) -> dict:
    """{channel: fraction of the documented pairs of `slot` whose two ends both have every point the channel reads}, plus n_pairs."""
    pairs = bc.pairs[slot]
    out = {"n_pairs": len(pairs), "channels": {}}
    for k, needs in CHANNEL_SIGNALS[slot].items():
        ok = 0
        for o, m in pairs:
            ends = {"o": (o, bc.kinds[o]), "m": (m, bc.kinds[m])}
            if all(has_role(bc, ends[w][0], ends[w][1], "rate" if sig == "rate_s|rate" else sig, recorded) for w, sig in needs):
                ok += 1
        out["channels"][k] = ok / len(pairs) if pairs else float("nan")
    return out


def supports(shares: dict, k: int) -> bool:
    return bool(shares["n_pairs"]) and shares["channels"][k] >= OK_FRAC


def distinct(censuses: list[BrickCensus]) -> tuple[list[BrickCensus], list[tuple[str, str]]]:
    """drop buildings whose set of timeseries ids equals an earlier one's (Mortar lists bldg30 twice as `smc`); returns (kept, [(dropped, kept-as)])"""
    seen, keep, dup = {}, [], []
    for c in censuses:
        key = c.ts_ids if c.ts_ids else frozenset([c.building])
        if key in seen:
            dup.append((c.building, seen[key]))
        else:
            seen[key] = c.building
            keep.append(c)
    return keep, dup
