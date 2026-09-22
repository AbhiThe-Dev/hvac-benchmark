"""Documentation-only corruption events (never touches the physical model).

Hard families (wrong-but-believable paperwork) are proposed exhaustively per
topology, then every proposal must pass structural validity and plausibility
(rules.py). Easy corruptions are deliberately implausible sanity checks.
"""

from __future__ import annotations

import hashlib
import itertools
from dataclasses import dataclass, field

from .data import Base
from .rules import (Doc, Edit, Plausibility, ahu_capacity_ok, apply_edits, graph_valid, loop_capacity_ok, loop_peak_heat,
                    peak, sensor_range_ok, structural_checks, true_doc, _ratio_ok)

HARD_FAMILIES = ("wrong_ahu_mapping", "vav_zone_swap", "plant_loop_mapping", "sensor_mapping", "same_medium_branch", "parallel_peer_swap")
EASY_TYPES = ("cross_medium_loop", "missing_link", "dual_parent")


@dataclass
class Event:
    topology: str
    family: str
    subtype: str
    difficulty: str  # hard | easy
    removed: list[Edit]
    added: list[Edit]
    checks: dict = field(default_factory=dict)
    plaus: Plausibility = field(default_factory=Plausibility)
    plausibility_confounded: bool = False

    @property
    def key(self) -> str:
        return f"{self.topology}|{self.family}|{self.subtype}|{sorted(self.removed)}|{sorted(self.added)}"

    @property
    def event_id(self) -> str:
        return "ev_" + hashlib.sha1(self.key.encode()).hexdigest()[:10]

    def members(self) -> list[str]:
        return sorted({m for _, _, m in self.removed + self.added})

    def owners(self) -> list[str]:
        return sorted({o for _, o, _ in self.removed + self.added})


def _pair_swap_edits(slot: str, a: tuple[str, str], b: tuple[str, str]) -> tuple[list[Edit], list[Edit]]:
    (o1, m1), (o2, m2) = a, b
    return [(slot, o1, m1), (slot, o2, m2)], [(slot, o1, m2), (slot, o2, m1)]


def _finish(base: Base, doc: Doc, ev: Event, plaus: Plausibility) -> Event | None:
    new = apply_edits(doc, ev.removed, ev.added)
    ev.checks = structural_checks(base, new)
    ev.checks["graph_valid"] = graph_valid(ev.checks)
    ev.plaus = plaus
    # replacement != true endpoint: every added edge must be a genuinely new edge
    truth = {(s, o, m) for s, es in doc.items() for o, m in es}
    if any(e in truth for e in ev.added):
        plaus.replacement_differs = False
    return ev


def propose_hard(base: Base) -> list[Event]:
    doc = true_doc(base)
    out: list[Event] = []
    T = base.tid

    def add(fam, sub, removed, added, plaus):
        e = Event(T, fam, sub, "hard", removed, added)
        e = _finish(base, doc, e, plaus)
        out.append(e)

    # ---- 1. wrong AHU: retarget a VAV to a different, capacity-compatible AHU
    ahus = base.ids("AHU")
    own_of = {m: o for o, m in doc["ahu_vav"]}
    kids = lambda a: [m for o, m in doc["ahu_vav"] if o == a]  # noqa: E731
    for v, a in own_of.items():
        for a2 in ahus:
            if a2 == a or base.cls(a2) != base.cls(a):
                continue
            if len(kids(a)) > 1:
                removed, added = [("ahu_vav", a, v)], [("ahu_vav", a2, v)]
                sub = "retarget"
                p = Plausibility(same_class=base.cls(a) == base.cls(a2))
                new = apply_edits(doc, removed, added)
                p.capacity_ok = ahu_capacity_ok(base, new, a2)
                add("wrong_ahu_mapping", sub, removed, added, p)
            else:  # single-terminal AHUs: retargeting would orphan `a`, so swap terminals
                for v2 in kids(a2):
                    if (a, v) < (a2, v2):
                        removed, added = _pair_swap_edits("ahu_vav", (a, v), (a2, v2))
                        new = apply_edits(doc, removed, added)
                        p = Plausibility(capacity_ok=ahu_capacity_ok(base, new, a) and ahu_capacity_ok(base, new, a2, 1.6))
                        add("wrong_ahu_mapping", "swap", removed, added, p)
    # ---- 2. VAV <-> zone swap between size-compatible boxes
    vz = doc["vav_zone"]
    for (v1, z1), (v2, z2) in itertools.combinations(vz, 2):
        removed, added = _pair_swap_edits("vav_zone", (v1, z1), (v2, z2))
        p = Plausibility(same_class=base.cls(v1) == base.cls(v2) and base.cls(z1) == base.cls(z2))
        p.size_ok = (_ratio_ok(peak(base, v1, "flow"), peak(base, v2, "flow"), 1.5)
                     and _ratio_ok(base.nodes[z1]["floor_area_m2"], base.nodes[z2]["floor_area_m2"], 1.5))
        add("vav_zone_swap", "swap", removed, added, p)
    # ---- 3. wrong compatible plant loop for a coil's branch
    loops = base.ids("HWL", "CHWL")
    lown = {m: o for o, m in doc.get("loop_branch", [])}
    lkids = lambda l: [m for o, m in doc.get("loop_branch", []) if o == l]  # noqa: E731
    for b, l in lown.items():
        for l2 in loops:
            if l2 == l or base.nodes[l2]["medium"] != base.nodes[l]["medium"]:
                continue
            if len(lkids(l)) > 1:
                removed, added = [("loop_branch", l, b)], [("loop_branch", l2, b)]
                new = apply_edits(doc, removed, added)
                add("plant_loop_mapping", "retarget", removed, added, Plausibility(capacity_ok=loop_capacity_ok(base, new, l2)))
            else:
                for b2 in lkids(l2):
                    if (l, b) < (l2, b2):
                        removed, added = _pair_swap_edits("loop_branch", (l, b), (l2, b2))
                        new = apply_edits(doc, removed, added)
                        add("plant_loop_mapping", "swap", removed, added,
                            Plausibility(capacity_ok=loop_capacity_ok(base, new, l) and loop_capacity_ok(base, new, l2)))
    # ---- 4. BAS point mapping: swap same-type sensors between two same-class hosts
    for slot, sig in (("ahu_sat", "sat"), ("vav_dat", "t_dis")):
        for (o1, s1), (o2, s2) in itertools.combinations(doc.get(slot, []), 2):
            removed, added = _pair_swap_edits(slot, (o1, s1), (o2, s2))
            p = Plausibility(same_class=base.cls(o1) == base.cls(o2) and base.cls(s1) == base.cls(s2))
            p.size_ok = sensor_range_ok(base, o1, o2, sig)
            add("sensor_mapping", slot, removed, added, p)
    # ---- 5. coil <-> branch swap within the same medium (parallel branches)
    for (b1, c1), (b2, c2) in itertools.combinations(doc.get("branch_coil", []), 2):
        if base.nodes[b1]["medium"] != base.nodes[b2]["medium"]:
            continue
        removed, added = _pair_swap_edits("branch_coil", (b1, c1), (b2, c2))
        p = Plausibility(same_class=base.cls(c1) == base.cls(c2))
        p.size_ok = _ratio_ok(peak(base, c1, "rate"), peak(base, c2, "rate"), 1.5)
        add("same_medium_branch", "branch_coil", removed, added, p)
    # ---- 6. peer-equipment swap: pump / source between same-medium loops, coils between AHUs / VAVs
    for slot in ("loop_pump", "loop_source"):
        for (o1, m1), (o2, m2) in itertools.combinations(doc.get(slot, []), 2):
            if base.nodes[o1]["medium"] != base.nodes[o2]["medium"]:
                continue
            removed, added = _pair_swap_edits(slot, (o1, m1), (o2, m2))
            p = Plausibility(same_class=base.cls(m1) == base.cls(m2))
            if slot == "loop_source":
                p.size_ok = _ratio_ok(loop_peak_heat(base, o1), loop_peak_heat(base, o2), 1.5) and _ratio_ok(peak(base, m1, "rate"), peak(base, m2, "rate"), 1.5)
            else:
                p.size_ok = _ratio_ok(peak(base, m1, "flow"), peak(base, m2, "flow"), 1.5)
            add("parallel_peer_swap", slot, removed, added, p)
    for slot in ("coil_ahu", "coil_vav"):
        for (o1, m1), (o2, m2) in itertools.combinations(doc.get(slot, []), 2):
            if o1 == o2 or base.cls(m1) != base.cls(m2):
                continue
            removed, added = _pair_swap_edits(slot, (o1, m1), (o2, m2))
            p = Plausibility(same_class=True)
            sig = "rate"
            p.size_ok = _ratio_ok(peak(base, m1, sig), peak(base, m2, sig), 1.5)
            add("parallel_peer_swap", slot, removed, added, p)
    return out


def propose_easy(base: Base) -> list[Event]:
    """Deliberately implausible corruptions. Marked plausibility_confounded."""
    doc = true_doc(base)
    out = []
    T = base.tid
    loops = base.ids("HWL", "CHWL")

    def add(sub, removed, added, plaus=None):
        e = Event(T, "easy_" + sub, sub, "easy", removed, added, plausibility_confounded=True)
        e = _finish(base, doc, e, plaus or Plausibility())
        out.append(e)

    # cross-medium: hot-water coil branch documented on a chilled-water loop (and vice versa); boiler in a CHW loop
    for b, l in [(m, o) for o, m in doc.get("loop_branch", [])]:
        for l2 in loops:
            if base.nodes[l2]["medium"] != base.nodes[l]["medium"]:
                p = Plausibility(same_medium=False)
                add("cross_medium_loop", [("loop_branch", l, b)], [("loop_branch", l2, b)], p)
    for slot in ("loop_source",):
        for o, m in doc.get(slot, []):
            for l2 in loops:
                if base.nodes[l2]["medium"] != base.nodes[o]["medium"]:
                    add("cross_medium_loop", [(slot, o, m)], [(slot, l2, m)], Plausibility(same_medium=False))
    # a required connection is simply missing from the paperwork
    for slot in ("ahu_vav", "vav_zone", "loop_branch", "branch_coil", "coil_ahu", "ahu_sat", "vav_dat", "loop_pump", "loop_source"):
        for o, m in doc.get(slot, []):
            add("missing_link", [(slot, o, m)], [])
    # a VAV listed under two AHUs / a zone under two VAVs (mutually exclusive parents)
    for slot in ("ahu_vav", "vav_zone"):
        owners = sorted({o for o, _ in doc[slot]})
        for o, m in doc[slot]:
            for o2 in owners:
                if o2 != o and (o2, m) not in doc[slot]:
                    add("dual_parent", [], [(slot, o2, m)])
    return out


def is_hard_ok(e: Event) -> bool:
    return e.checks.get("graph_valid", False) and e.plaus.all()
