"""Bridge to hvac_benchmark's Brick graphs: ground "does this channel need extra instrumentation" in what a
building's OWN documentation says it already has, instead of doc_mismatch's simulation-derived assumption table.

Why this exists (PREREGISTRATION_DR.md Addendum 5): `measurement.py`'s `requires_instrument`/`describe_requirement`
originally answered from a fixed, simulation-wide table (`evidence.NEEDS` / `engine._BAS_ONLY`) -- true on average,
but not building-specific. hvac_benchmark already parses every building's Brick documentation (`hasPoint` edges
typed by Brick sensor class) for its OWN purpose (the pretrained graph encoder); this module reuses that, so the
same question can be answered PER BUILDING, including for the 44 real MORTAR buildings that have Brick metadata
but no timeseries at all -- buildings doc_mismatch's own evidence engine can never otherwise touch.

Ground-truth cross-check done while building this (not hardcoded, discovered by querying the actual cached Brick
file): the ORNL `rtu_exp` building's VAV boxes are documented with exactly a `Supply_Air_Temperature_Sensor` and
an `Electrical_Power_Sensor` per box -- NO flow point -- independently reproducing this session's earlier,
purely statistical finding (Addendum 1/4: real `vav_zone` channels 0/2, which need airflow, carry no real
signal). That file also uses the non-canonical class name `Electrical_Power_Sensor` (Brick 1.3.0's own name is
`Electric_Power_Sensor`), which the reference ontology cannot place in the subclass hierarchy -- see
`equipment_has_signal`'s three-way return for how that is handled honestly rather than guessed.
"""

from __future__ import annotations

import os
from pathlib import Path

from hvac_benchmark.data.cache import FileCache
from hvac_benchmark.data.ontology import BrickOntology
from hvac_benchmark.graph.networkx_build import TopologyGraph, build_topology_graph
from hvac_benchmark.pretrain.data import _merged_topologies

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CACHE_DIR = REPO_ROOT / "data_cache"

# doc_mismatch signal tag (evidence.NEEDS) -> Brick sensor umbrella class. None = not a distinct sensor-class
# requirement (e.g. "temp"/"t_dis"/"value" are ordinary BAS trend points already assumed present, matching
# measurement.py's INSTRUMENT_DEVICE, which only names devices for flow/rate/kw).
SIGNAL_BRICK_CLASS: dict[str, str | None] = {
    "flow": "Flow_Sensor",
    "rate": "Flow_Sensor",     # coil/loop "rate" signals are flow-derived; best available umbrella, noted as approximate
    "kw": "Power_Sensor",
    "t_dis": None,   # standard BAS temperature point; measurement.py never recommends instrumenting these, so
    "temp": None,    # they are out of scope here too (and member/zone nodes are typically rec: namespace, not
    "value": None,   # captured by TopologyGraph.node_type at all -- see networkx_build.py)
}

# For a point whose Brick class the reference ontology cannot place (a non-canonical name in the source file,
# e.g. real rtu_exp's "Electrical_Power_Sensor" vs Brick 1.3.0's own "Electric_Power_Sensor"): a plain keyword in
# its OWN local name is the only signal available about which target class it might satisfy. This only ever
# downgrades a confident False to an undetermined None (never upgrades an unknown class to True) -- it is a
# textual hint used to decide where to stay honestly uncertain, never a claimed subclass equivalence.
_CLASS_KEYWORD = {"Flow_Sensor": "flow", "Power_Sensor": "power"}


def load_real_topologies(cache_dir: str | Path = DEFAULT_CACHE_DIR) -> tuple[dict[str, TopologyGraph], BrickOntology]:
    """{building_id: TopologyGraph} for every REAL building in the on-disk cache (44 MORTAR + ORNL `rtu_exp`;
    never the network, never the simulated LBNL testbeds). Cross-referenced against `config_type == "experimental"`
    by `building_grouping.py`'s own provenance table, not re-derived here."""
    cache = FileCache(cache_dir)
    ontology = BrickOntology.load(cache)
    merged = _merged_topologies(cache, ontology, include_simulated=False, exclude_ids=frozenset())
    out = {m.building_id: build_topology_graph(m.building_id, m.config_type, m.graph) for m in merged}
    return out, ontology


def class_nodes(tg: TopologyGraph, ontology: BrickOntology, brick_class: str) -> list[str]:
    """Every node of `tg` whose Brick type is-a `brick_class` (e.g. all VAV boxes)."""
    return [n for n in tg.nodes() if tg.node_type(n) and ontology.is_a(tg.node_type(n), brick_class)]


def equipment_has_signal(tg: TopologyGraph, ontology: BrickOntology, equipment_node: str, sig: str) -> bool | None:
    """True: a hasPoint'd point is-a the Brick class this signal needs. False: every hasPoint'd point's class is
    KNOWN to the reference ontology and none matches (confidently absent). None: `sig` has no distinct
    sensor-class requirement, OR a point exists whose Brick class the reference ontology cannot place (a
    non-canonical name in the source file) so subclass membership cannot be determined -- never guessed."""
    cls = SIGNAL_BRICK_CLASS.get(sig)
    if cls is None:
        return True
    known = ontology.known_classes()
    pts = [t for (s, o) in tg.edges_by_relation.get("hasPoint", ()) if s == equipment_node for t in [tg.node_type(o)] if t]
    if any(p in known and ontology.is_a(p, cls) for p in pts):
        return True
    kw = _CLASS_KEYWORD.get(cls)
    if kw and any(p not in known and kw in p.lower() for p in pts):
        return None
    return False


def structural_requirement_met(tg: TopologyGraph, ontology: BrickOntology, owner_node: str | None, member_node: str | None,
                                slot: str, k: int) -> bool | None:
    """Does this building's OWN Brick documentation already carry every signal channel `k` of `slot` needs
    (per `evidence.NEEDS`)? True/False/None (undetermined: nothing catalogued for this channel, or an
    involved node's required point exists under a class the reference ontology can't place)."""
    from .measurement import channel_requirement
    req = channel_requirement(slot, k)
    if not req:
        return None
    node_of = {"o": owner_node, "m": member_node}
    results = []
    for who, sig in req:
        if SIGNAL_BRICK_CLASS.get(sig) is None:
            results.append(True)   # no distinct sensor-class requirement -- never needs a node lookup
            continue
        node = node_of.get(who)
        results.append(None if node is None else equipment_has_signal(tg, ontology, node, sig))
    if any(r is False for r in results):
        return False
    if any(r is None for r in results):
        return None
    return True
