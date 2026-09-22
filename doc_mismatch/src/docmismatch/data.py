"""Numpy-only loading of a simulated base topology (physical truth + evidence)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

BASE_DIR = Path(__file__).resolve().parents[3] / "results" / "docmismatch" / "base"
DR_BASE_DIR = Path(__file__).resolve().parents[3] / "results" / "docmismatch_dr" / "base"   # domain-randomized buildings (dr/), looked up when tid is not in BASE_DIR
HOURS_PER_WINDOW = 1008  # 6 weeks; 8 disjoint windows per weather year
N_WINDOWS = 8

# Relation slots. `owner` is the host/parent side; `edge_owner_first` says whether
# the stored (src, dst) tuple is (owner, member) or (member, owner).
SLOTS: dict[str, dict] = {
    "ahu_vav": dict(rel="feeds", owner=("AHU",), member=("VAV",), owner_first=True),
    "vav_zone": dict(rel="feeds", owner=("VAV",), member=("Zone",), owner_first=True),
    "loop_branch": dict(rel="feeds", owner=("HWL", "CHWL"), member=("Branch",), owner_first=True),
    "branch_coil": dict(rel="feeds", owner=("Branch",), member=("Coil",), owner_first=True),
    "loop_pump": dict(rel="hasPart", owner=("HWL", "CHWL"), member=("Pump",), owner_first=True),
    "loop_source": dict(rel="hasPart", owner=("HWL", "CHWL"), member=("Boiler", "Chiller"), owner_first=True),
    "coil_ahu": dict(rel="hasPart", owner=("AHU",), member=("Coil",), owner_first=False),
    "coil_vav": dict(rel="hasPart", owner=("VAV",), member=("Coil",), owner_first=False),
    "fan_ahu": dict(rel="hasPart", owner=("AHU",), member=("Fan",), owner_first=False),
    "ahu_sat": dict(rel="hasPoint", owner=("AHU",), member=("SAT",), owner_first=True),
    "vav_dat": dict(rel="hasPoint", owner=("VAV",), member=("DAT",), owner_first=True),
}
SLOT_NAMES = tuple(SLOTS)
# slots whose physics we can test against time series
EVIDENCE_SLOTS = tuple(s for s in SLOTS if s not in ("fan_ahu",))


@dataclass
class Base:
    tid: str
    nodes: dict[str, dict]
    edges: list[tuple[str, str, str]]  # (src, dst, rel)
    ev: dict[str, np.ndarray]  # "NODE|signal" -> (8760,) true series
    run: dict = field(default_factory=dict)
    slot_edges: dict[str, list[tuple[str, str]]] = field(default_factory=dict)  # slot -> [(owner, member)]

    def kind(self, nid):
        return self.nodes[nid]["kind"]

    def cls(self, nid):
        n = self.nodes[nid]
        return (n["kind"], n["brick_type"], n.get("medium"))

    def ids(self, *kinds):
        return sorted(i for i, n in self.nodes.items() if n["kind"] in kinds)

    def slot_of(self, src, dst, rel):
        for name, s in SLOTS.items():
            if s["rel"] != rel:
                continue
            o, m = (src, dst) if s["owner_first"] else (dst, src)
            if self.kind(o) in s["owner"] and self.kind(m) in s["member"]:
                return name, o, m
        return None, None, None


def load_base(tid: str, root: Path = BASE_DIR) -> Base:
    d = root / tid
    if not d.exists() and root == BASE_DIR and (DR_BASE_DIR / tid).exists():
        d = DR_BASE_DIR / tid
    g = json.loads((d / "graph.json").read_text())
    z = np.load(d / "evidence.npz")
    nodes = {n["id"]: n for n in g["nodes"]}
    edges = [(e["src"], e["dst"], e["rel"]) for e in g["edges"]]
    ev = {k.replace("__", "|"): z[k] for k in z.files}
    b = Base(tid, nodes, edges, ev, json.loads((d / "run.json").read_text()))
    for s, t, r in edges:
        name, o, m = b.slot_of(s, t, r)
        if name is None:
            raise ValueError(f"{tid}: edge {s}-{r}->{t} fits no slot")
        b.slot_edges.setdefault(name, []).append((o, m))
    return b


def window_slice(w: int) -> slice:
    return slice(w * HOURS_PER_WINDOW, (w + 1) * HOURS_PER_WINDOW)
