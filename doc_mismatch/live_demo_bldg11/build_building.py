"""Brick model of Mortar bldg11 -> the troubleshooting tool's building file, for the AHUs a demo visit touches.

A SUBSET of a real building: the named air handlers, every box they feed, the room each box feeds, and the control-system points the Brick file actually records for them. Nothing is invented
here: a point is on the map only if the Brick graph lists it AND links it to a timeseries (the same "recorded" rule as the census). Points the Brick file does not list are absent, so a check
that needs one is not offered at the cheap price (the engine charges its fallback minutes instead).

What the Brick file does NOT carry (so this map does not either): reheat type, design airflow, K-factor, static setpoint (no attributes: the T3-noattr profile), any location, any airflow
SETPOINT point, any fan status, any controller status.

The output goes to data_cache/ (git-ignored): the Mortar licence rests on an email, so the layout is generated on the fly and never committed.

  .venv/bin/python doc_mismatch/live_demo_bldg11/build_building.py            # writes data_cache/demo_bldg11/building_v2.json (+ coverage.json)
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from docmismatch.troubleshoot.building import natural_key  # noqa: E402

REPO = ROOT.parent
TTL = REPO / "data_cache" / "mortar__bldg11.ttl"
OUT = REPO / "data_cache" / "demo_bldg11"
BRICK_NS = "https://brickschema.org/schema/Brick#"
REF_NS = "https://brickschema.org/schema/Brick/ref#"
DEFAULT_AHUS = ("AHU06", "AHU05")

# Brick point (by its own name suffix) -> the engine's point key, per kind of equipment. Checked by hand against the graph on 2026-10-11 (see coverage.json for the counts).
BOX_POINTS = {"Zone_Supply_Air_Flow": "airflow", "Zone_Reheat_Valve_Command": "reheat"}
DAMPER_POINTS = {"Zone_Air_Damper_Command": "damper"}               # on the box's Damper sub-node (isPartOf the box), not on the box itself
ZONE_TEMP = "Zone_Air_Temp"                                         # sits on the box in bldg11; the engine looks for it on the room
AHU_POINTS = {"Supply_Air_Pressure": "static_pressure"}


def _short(x) -> str:
    return str(x).split("#")[-1].split("/")[-1]


def build_subset(ttl: Path = TTL, ahus: tuple | None = DEFAULT_AHUS) -> tuple[dict, dict]:
    """(building json, coverage report) for the given air handlers of the Brick file (`ahus=None`: every air handler that feeds a box)."""
    from rdflib import RDF, Graph, Namespace
    B, R = Namespace(BRICK_NS), Namespace(REF_NS)
    g = Graph()
    g.parse(str(ttl), format="turtle")
    by_name = {}
    for s in set(g.subjects(RDF.type, None)):
        by_name.setdefault(_short(s), s)
    if ahus is None:
        ahus = tuple(sorted((_short(a) for a in g.subjects(RDF.type, B.Air_Handler_Unit) if any(True for _ in g.objects(a, B.feeds))), key=lambda s: (natural_key(s), s)))

    def recorded_points(node) -> dict[str, str]:
        """{point name suffix: full point name} for the node's points that link to a timeseries."""
        out = {}
        for p in g.objects(node, B.hasPoint):
            if any(True for r in g.objects(p, R.hasExternalReference) for _ in g.objects(r, R.hasTimeseriesId)):
                full = _short(p)
                out[full.split(".")[-1]] = full
        return out

    equipment, claims_vz, claims_av, points = [], {}, {}, {}
    cover = {}
    for ahu_id in ahus:
        a = by_name[ahu_id]
        equipment.append({"id": ahu_id, "kind": "AHU", "area": ahu_id})
        ap = recorded_points(a)
        pts = {key: ap[name] for name, key in AHU_POINTS.items() if name in ap}
        if pts:
            points[ahu_id] = pts
        boxes = sorted((_short(o) for o in g.objects(a, B.feeds)), key=lambda s: (natural_key(s), s))
        n_pts, n_rooms = Counter(), 0
        for bid in boxes:
            v = by_name[bid]
            equipment.append({"id": bid, "kind": "VAV", "area": ahu_id})
            claims_av[bid] = ahu_id
            vp = recorded_points(v)
            bpts = {key: vp[name] for name, key in BOX_POINTS.items() if name in vp}
            for d in g.subjects(B.isPartOf, v):
                dp = recorded_points(d)
                bpts.update({key: dp[name] for name, key in DAMPER_POINTS.items() if name in dp})
            if bpts:
                points[bid] = bpts
            for key in bpts:
                n_pts[key] += 1
            for z in sorted((_short(o) for o in g.objects(v, B.feeds)), key=lambda s: (natural_key(s), s)):
                if z in claims_vz:                                    # a room fed by two boxes is claimed by the first in id order (as in troubleshoot/realmaps.py)
                    continue
                equipment.append({"id": z, "kind": "Zone", "area": ahu_id})
                claims_vz[z] = bid
                n_rooms += 1
                if ZONE_TEMP in vp:
                    points[z] = {"temperature": vp[ZONE_TEMP]}
                    n_pts["temperature"] += 1
        full = [b for b in boxes if {"airflow", "damper", "reheat"} <= set(points.get(b, {}))]
        cover[ahu_id] = dict(boxes=len(boxes), rooms=n_rooms, ahu_points=sorted(pts), box_points={k: n_pts[k] for k in ("airflow", "damper", "reheat", "temperature")},
                             boxes_with_airflow_damper_reheat=len(full))
    building = {"name": f"Mortar {Path(ttl).stem.replace('mortar__', '')} (subset: " + ", ".join(ahus) + "; real layout and recorded points, scripted scenario)",
                "equipment": equipment, "claims": {"vav_zone": claims_vz, "ahu_vav": claims_av}, "control_system": {"points": points}}
    return building, cover


def checks_absent_from_map(building: dict, catalogue) -> set:
    """Names of the catalogue's control-system checks whose point exists nowhere in the building's point map (so the real map cannot support them; the engine's own availability rule only asks whether
    a piece of equipment has ANY point). For bldg11 this is bas_ahu_fan (no fan status) and bas_controller (no controller status)."""
    keys = {k for p in building["control_system"]["points"].values() for k in p}
    return {c.name for c in catalogue if c.point is not None and c.point not in keys}


def ensure_building(name: str, ahus: tuple | None = None) -> Path:
    """Write (once) data_cache/demo_<name>/building_v2.json for every air handler of Mortar building `name` and return its path (git-ignored; see the module docstring on the licence)."""
    d = REPO / "data_cache" / f"demo_{name}"
    p = d / "building_v2.json"
    if not p.exists():
        b, cover = build_subset(REPO / "data_cache" / f"mortar__{name}.ttl", ahus)
        d.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(b))
        (d / "coverage.json").write_text(json.dumps(cover, indent=1))
    return p


def main() -> None:
    if not TTL.exists():
        raise SystemExit(f"{TTL} not found: the Mortar Brick files are downloaded by the project's data step and are not part of the repository")
    b, cover = build_subset()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "building_v2.json").write_text(json.dumps(b))
    (OUT / "coverage.json").write_text(json.dumps(cover, indent=1))
    print(json.dumps(cover, indent=1))
    print("wrote", OUT / "building_v2.json")


if __name__ == "__main__":
    main()
