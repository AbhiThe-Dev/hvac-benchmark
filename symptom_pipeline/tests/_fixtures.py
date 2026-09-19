"""Hand-built fixtures mirroring `tests/test_troubleshooting_runner.py` at
the benchmark repo root exactly (that file lives inside `hvac_benchmark`'s
own test suite, not its installed package, so it cannot be imported here --
duplicated deliberately, not reinvented, and kept in lockstep by
`test_oracle_parity.py::test_fixture_matches_upstream_shape`).
"""

from __future__ import annotations

import networkx as nx
from hvac_benchmark.experiment.blueprint import Blueprint, CorruptionEvent
from hvac_benchmark.graph.networkx_build import TopologyGraph


def make_tg() -> TopologyGraph:
    g = nx.MultiDiGraph()
    g.add_node("AHU", brick_type="AHU", brick_types=["AHU"], location=None)
    edges = {"feeds": set(), "hasPoint": set(), "hasPart": set()}
    for i in range(2):
        vav, zone = f"VAV_{i}", f"Zone_{i}"
        g.add_node(vav, brick_type="VAV", brick_types=["VAV"], location=None)
        g.add_node(zone, brick_type="HVAC_Zone", brick_types=["HVAC_Zone"], location=None)
        g.add_edge("AHU", vav, relation="feeds")
        g.add_edge(vav, zone, relation="feeds")
        edges["feeds"].add(("AHU", vav))
        edges["feeds"].add((vav, zone))
    return TopologyGraph("troubleshooting_test", "test", g, edges)


def forced_removal_blueprint(tg: TopologyGraph) -> Blueprint:
    true_edges = set(tg.edges_by_relation["feeds"])
    removed = ("VAV_0", "Zone_0")
    assert removed in true_edges
    claimed = frozenset(true_edges - {removed})
    event = CorruptionEvent("removal", (removed,), "Zone_0")
    return Blueprint(
        building_id=tg.building_id, severity=1, corruption_seed=0, claimed_edges=claimed, events=(event,)
    )


def forced_fabrication_blueprint(tg: TopologyGraph) -> Blueprint:
    true_edges = set(tg.edges_by_relation["feeds"])
    fabricated = ("AHU", "Zone_1")
    claimed = frozenset(true_edges | {fabricated})
    event = CorruptionEvent("fabrication", (fabricated,), "Zone_1")
    return Blueprint(
        building_id=tg.building_id, severity=1, corruption_seed=1, claimed_edges=claimed, events=(event,)
    )
