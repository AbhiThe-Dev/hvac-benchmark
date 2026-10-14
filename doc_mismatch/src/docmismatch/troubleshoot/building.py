"""What the technician (or a control-system export) supplies about the building: an equipment list with types and rough area, and the drawings' claims.
That is all the working model needs from a building: no connections beyond the claims, no trends. The claims may be wrong or out of date; they are the thing checked.

JSON format (see examples/troubleshoot_example/building.json):
  {"name": "...",
   "equipment": [{"id": "VAV-2-04", "kind": "VAV", "area": "Floor 2 West", "tag": "2-04"}, ...],       # kinds used: Zone, VAV, AHU; `area` and `tag` optional
   "claims": {"vav_zone": {"Room-204": "VAV-2-04"}, "ahu_vav": {"VAV-2-04": "AHU-1"}}}                 # slot -> {member: documented owner}
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

from .model import SLOT_MEMBER_KIND, SLOT_OWNER_KIND, Settings


@dataclass(frozen=True)
class Equipment:
    id: str
    kind: str
    area: str | None = None
    tag: str | None = None

    @property
    def label(self) -> str:
        return self.tag or self.id


@dataclass
class Building:
    name: str
    equipment: dict[str, Equipment]
    claims: dict[str, dict[str, str]] = field(default_factory=dict)

    def label(self, eid: str) -> str:
        return self.equipment[eid].label if eid in self.equipment else eid

    def members(self, slot: str) -> list[str]:
        return sorted(self.claims.get(slot, {}))


def load_building(path: str | Path) -> Building:
    d = json.loads(Path(path).read_text())
    eq = {}
    for e in d["equipment"]:
        if e["id"] in eq:
            raise ValueError(f"duplicate equipment id {e['id']!r}")
        eq[e["id"]] = Equipment(e["id"], e["kind"], e.get("area"), e.get("tag"))
    b = Building(d.get("name", "building"), eq, d.get("claims", {}))
    for slot, m in b.claims.items():
        for member, owner in m.items():
            if member not in eq or owner not in eq:
                raise ValueError(f"claim {slot}: {member!r} -> {owner!r} names equipment that is not in the equipment list")
    return b


def natural_key(s: str) -> tuple:
    """Sort key in which digit runs compare as integers and other runs case-insensitively ('V2' < 'V10')."""
    return tuple((0, int(t), "") if t.isdigit() else (1, 0, t.upper()) for t in re.findall(r"\d+|\D+", s))


def id_ranks(b: Building, kind: str) -> dict[str, int]:
    """Rank of each piece of equipment of `kind` in natural id order (ties: the plain identifier)."""
    ids = sorted((e.id for e in b.equipment.values() if e.kind == kind), key=lambda i: (natural_key(i), i))
    return {i: r for r, i in enumerate(ids)}


def id_weight(rank_doc: int, rank_other: int, decay: float) -> float:
    """Nearness weight of a candidate `|rank difference|` places from the documented one in id order."""
    return math.exp(-abs(rank_other - rank_doc) / decay)


def candidates_for(b: Building, slot: str, doc: str, max_candidates: int = 8, settings: Settings | None = None) -> tuple[list[str], dict[str, float]]:
    """The documented owner first, then every other piece of equipment of the owner kind (same area first, capped at `max_candidates`), with a nearness weight: 1 inside the
    documented owner's area, `settings.other_area_weight` outside it (all 1 when areas are unknown). With `settings.nearness == "id"`: the owners nearest to the documented one in natural
    id order instead, weighted exp(-rank distance / `settings.id_decay`)."""
    s = settings or Settings()
    kind = SLOT_OWNER_KIND[slot]
    if s.nearness == "id":
        rk = id_ranks(b, kind)
        nearest = sorted((i for i in rk if i != doc), key=lambda i: (abs(rk[i] - rk[doc]), rk[i]))
        cands = ([doc] + nearest)[:max_candidates]
        return cands, {c: id_weight(rk[doc], rk[c], s.id_decay) for c in cands}
    owners = [e for e in b.equipment.values() if e.kind == kind]
    area = b.equipment[doc].area
    same = [e.id for e in owners if e.id != doc and (area is None or e.area == area)]
    other = [e.id for e in owners if e.id != doc and area is not None and e.area != area]
    cands = ([doc] + same + other)[:max_candidates]
    weights = {c: (1.0 if (area is None or b.equipment[c].area == area) else s.other_area_weight) for c in cands}
    return cands, weights


@dataclass
class Case:
    """One complaint: what the drawings claim and who could feed it."""
    building: Building
    slot: str
    member: str
    doc: str
    candidates: list[str]
    weights: dict[str, float]
    settings: Settings
    airflow: str | None = None
    entries0: int = 1                           # entries made to set the case up (the location, plus each symptom answer)

    @property
    def member_name(self) -> str:
        return self.building.label(self.member)


def make_case(b: Building, member: str, slot: str = "vav_zone", settings: Settings | None = None, airflow: str | None = None,
              max_candidates: int = 8) -> Case:
    s = settings or Settings()
    if slot not in SLOT_OWNER_KIND:
        raise ValueError(f"unsupported slot {slot!r}; choose from {sorted(SLOT_OWNER_KIND)}")
    claims = b.claims.get(slot, {})
    if member not in claims:
        raise ValueError(f"no documented {slot} claim for {member!r}; choose from {sorted(claims)}")
    if b.equipment[member].kind != SLOT_MEMBER_KIND[slot]:
        raise ValueError(f"{member!r} is a {b.equipment[member].kind}, not a {SLOT_MEMBER_KIND[slot]}")
    if airflow not in (None, "yes", "no", "unsure"):
        raise ValueError("airflow must be 'yes', 'no', 'unsure' or None")
    doc = claims[member]
    cands, w = candidates_for(b, slot, doc, max_candidates, s)
    return Case(b, slot, member, doc, cands, w, s, airflow, 1 + (airflow is not None))
