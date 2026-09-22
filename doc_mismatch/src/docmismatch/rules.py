"""Documentation graphs, structural validity, and physical plausibility (Phase 7).

A documentation graph is `dict[slot, list[(owner, member)]]`. The true building
is `base.slot_edges`; corruptions edit only this documentation.
"""

from __future__ import annotations

import copy
from collections import Counter, defaultdict
from dataclasses import dataclass, field

import numpy as np

from .data import SLOTS, Base

Doc = dict[str, list[tuple[str, str]]]
Edit = tuple[str, str, str]  # (slot, owner, member)

# max number of members of one class an owner may have in a slot (None = unbounded)
MAX_PER_OWNER_CLASS: dict[str, int | None] = {
    "ahu_vav": None, "vav_zone": 1, "loop_branch": None, "branch_coil": 1, "loop_pump": 1,
    "loop_source": 1, "coil_ahu": 1, "coil_vav": 1, "fan_ahu": 1, "ahu_sat": 1, "vav_dat": 1,
}
# same-class slot ownership: which owner classes may own a member class
def true_doc(base: Base) -> Doc:
    return {s: list(e) for s, e in base.slot_edges.items()}


def apply_edits(doc: Doc, removed: list[Edit], added: list[Edit]) -> Doc:
    out = copy.deepcopy(doc)
    for slot, o, m in removed:
        out[slot].remove((o, m))
    for slot, o, m in added:
        out.setdefault(slot, []).append((o, m))
    return out


def structural_checks(base: Base, doc: Doc) -> dict[str, bool]:
    single_owner = no_orphan_member = no_orphan_owner = cardinality = no_dup = medium_ok = True
    for slot, truth in base.slot_edges.items():
        edges = doc.get(slot, [])
        members_true = {m for _, m in truth}
        owners_true = {o for o, _ in truth}
        if len(edges) != len(set(edges)):
            no_dup = False
        by_member = Counter(m for _, m in edges)
        if any(by_member[m] != 1 for m in members_true) or any(m not in members_true for m in by_member):
            single_owner = False if any(c > 1 for c in by_member.values()) else single_owner
            no_orphan_member = False if any(by_member[m] == 0 for m in members_true) else no_orphan_member
        by_owner = Counter(o for o, _ in edges)
        if any(by_owner[o] == 0 for o in owners_true):
            no_orphan_owner = False
        cap = MAX_PER_OWNER_CLASS[slot]
        if cap is not None:
            per = Counter((o, base.cls(m)) for o, m in edges)
            if any(c > cap for c in per.values()):
                cardinality = False
        for o, m in edges:
            mo, mm = base.nodes[o].get("medium"), base.nodes[m].get("medium")
            if mo and mm and mo != mm:
                medium_ok = False
    return {"single_owner": single_owner, "no_orphan_member": no_orphan_member, "no_orphan_owner": no_orphan_owner,
            "valid_cardinality": cardinality, "no_duplicate_edge": no_dup, "medium_consistent": medium_ok}


def graph_valid(checks: dict[str, bool]) -> bool:
    return all(checks.values())


# ----------------------------------------------------------------------------
# plausibility: would a reader of the paperwork find the *documented* connection believable?
# Uses only design-level facts (peak sizes / floor areas), not the time-series evidence.
# ----------------------------------------------------------------------------
def peak(base: Base, nid: str, sig: str) -> float:
    return float(np.abs(base.ev[f"{nid}|{sig}"]).max()) + 1e-9


def _ratio_ok(a: float, b: float, lim: float) -> bool:
    return max(a, b) / min(a, b) <= lim


def loop_peak_heat(base: Base, loop: str) -> float:
    q = np.abs(base.ev[f"{loop}|flow"] * 4180.0 * np.abs(base.ev[f"{loop}|t_sup"] - base.ev[f"{loop}|t_ret"]))
    return float(q.max()) + 1e-9


def sensor_range_ok(base: Base, host_a: str, host_b: str, sig_host: str, tol: float = 4.0) -> bool:
    return abs(float(base.ev[f"{host_a}|{sig_host}"].mean()) - float(base.ev[f"{host_b}|{sig_host}"].mean())) <= tol


def ahu_capacity_ok(base: Base, doc: Doc, ahu: str, lim: float = 1.6) -> bool:
    kids = [m for o, m in doc["ahu_vav"] if o == ahu]
    if not kids:
        return False
    return sum(peak(base, k, "flow") for k in kids) <= lim * peak(base, ahu, "flow")


def loop_capacity_ok(base: Base, doc: Doc, loop: str, lim: float = 1.6) -> bool:
    kids = [m for o, m in doc["loop_branch"] if o == loop]
    if not kids:
        return False
    qsum = sum(float(np.abs(base.ev[f"{k}|flow"] * 4180.0 * np.abs(base.ev[f"{k}|t_in"] - base.ev[f"{k}|t_out"])).max()) for k in kids)
    return qsum <= lim * loop_peak_heat(base, loop)


@dataclass
class Plausibility:
    same_class: bool = True
    same_medium: bool = True
    same_relation: bool = True
    same_direction: bool = True
    replacement_differs: bool = True
    capacity_ok: bool = True
    size_ok: bool = True

    def all(self) -> bool:
        return all(vars(self).values())
