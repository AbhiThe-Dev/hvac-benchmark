"""Real building layouts for the troubleshooting study (PREREGISTRATION_DR.md Addendum 20). A Brick model gives the documented equipment and the documented claims (zone -> box, box ->
air handler); it carries no location at all, so the only "area" it can supply is the air handler a box hangs on, which stands in for "nearby". Metadata only: no timeseries is read."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from ..census import parse_census
from . import model as M
from .building import Building, Equipment, make_case

MIN_ROOMS = 12
REGIME_CAPS = {"R_narrow": 8, "R_wide": 40}          # candidate-list caps (Addendum 20)
FROZEN_BUILDINGS = ("bldg2", "bldg4", "bldg5", "bldg6", "bldg8", "bldg9", "bldg10", "bldg11", "bldg12", "bldg13", "bldg15", "bldg18", "bldg20", "bldg27", "bldg28", "bldg30", "bldg32",
                    "bldg34", "bldg36", "bldg37", "bldg39", "bldg40", "bldg42", "bldg43", "bldg44")


@dataclass(frozen=True)
class LayoutMeta:
    name: str
    rooms: int
    boxes: int
    handlers: int
    boxes_without_handler: int
    rooms_with_several_boxes: int


def building_number(name: str) -> int:
    return int(re.sub(r"\D", "", name) or 0)


def layout_from_census(bc) -> tuple[Building, LayoutMeta]:
    """Build the layout from a parsed `census.BrickCensus`. A box's area is its documented air handler (the lowest identifier if several; None if it has none); a zone takes its box's
    area; a zone documented under several boxes is claimed by the first in identifier order (none of the 28 Mortar buildings has one)."""
    zone_boxes, handler_of = defaultdict(list), defaultdict(list)
    for v, z in bc.pairs["vav_zone"]:
        zone_boxes[z].append(v)
    for a, v in bc.pairs["ahu_vav"]:
        handler_of[v].append(a)
    boxes = sorted({v for vs in zone_boxes.values() for v in vs})
    area = {v: (sorted(handler_of[v])[0] if handler_of.get(v) else None) for v in boxes}
    equipment = {v: Equipment(v, "VAV", area[v]) for v in boxes}
    claims_vz, several = {}, 0
    for z in sorted(zone_boxes):
        vs = sorted(zone_boxes[z])
        several += len(vs) > 1
        equipment[z] = Equipment(z, "Zone", area[vs[0]])
        claims_vz[z] = vs[0]
    handlers = sorted({a for v in boxes for a in handler_of.get(v, [])})
    for a in handlers:
        equipment[a] = Equipment(a, "AHU", None)
    claims_av = {v: sorted(handler_of[v])[0] for v in boxes if handler_of.get(v)}
    meta = LayoutMeta(bc.building, len(claims_vz), len(boxes), len(handlers), sum(1 for v in boxes if not handler_of.get(v)), several)
    return Building(bc.building, equipment, {"vav_zone": claims_vz, "ahu_vav": claims_av}), meta


def load_layout(ttl: str | Path, name: str | None = None) -> tuple[Building, LayoutMeta]:
    return layout_from_census(parse_census(ttl, name))


def eligible(data_dir: str | Path, min_rooms: int = MIN_ROOMS) -> list[str]:
    """Mortar buildings with at least `min_rooms` documented rooms, in numeric order of the building number."""
    data_dir = Path(data_dir)
    names = sorted((p.name[len("mortar__"):-len(".ttl")] for p in data_dir.glob("mortar__bldg*.ttl")), key=building_number)
    return [n for n in names if load_layout(data_dir / f"mortar__{n}.ttl", n)[1].rooms >= min_rooms]


def layout_problems(name: str, layout: Building, bc, regimes: dict = REGIME_CAPS) -> list[str]:
    """G6: the layout has as many rooms and distinct boxes as the parsed documentation, every room has exactly one claim whose box exists, and every candidate list starts with the
    documented box, has no duplicates and has length min(cap, boxes)."""
    bad = []
    zones = {z for _, z in bc.pairs["vav_zone"]}
    boxes = {v for v, _ in bc.pairs["vav_zone"]}
    claims = layout.claims["vav_zone"]
    if set(claims) != zones:
        bad.append(f"{name}: rooms differ from the documented zones ({len(claims)} vs {len(zones)})")
    if {b for b in claims.values()} - boxes or any(b not in layout.equipment or layout.equipment[b].kind != "VAV" for b in claims.values()):
        bad.append(f"{name}: a claim names a box that is not documented or not in the equipment list")
    if sum(1 for e in layout.equipment.values() if e.kind == "VAV") != len(boxes):
        bad.append(f"{name}: box count differs from the documentation")
    if bad:
        return bad                                                                           # the candidate lists cannot be built from a broken layout
    for reg, cap in regimes.items():
        for room in sorted(claims):
            try:
                c = make_case(layout, room, "vav_zone", M.Settings(), max_candidates=cap)
                wrong = c.candidates[0] != claims[room] or len(set(c.candidates)) != len(c.candidates) or len(c.candidates) != min(cap, len(boxes))
            except (KeyError, ValueError):
                wrong = True
            if wrong:
                bad.append(f"{name}/{reg}/{room}: candidate list wrong")
                break
    return bad
