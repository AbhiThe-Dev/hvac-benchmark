"""Candidate generation: subclass-based compatibility, location exclusion
(only applied when supported by metadata), and coverage reporting."""

from __future__ import annotations

import networkx as nx

from hvac_benchmark.experiment.candidates import (
    candidate_coverage,
    generate_feeds_candidates,
    generate_haspart_candidates,
    generate_haspoint_candidates,
)
from hvac_benchmark.graph.networkx_build import TopologyGraph


def make_tg(building_id: str, node_specs: dict[str, tuple[str, str | None]]) -> TopologyGraph:
    g = nx.MultiDiGraph()
    for node, (brick_type, location) in node_specs.items():
        g.add_node(node, brick_type=brick_type, brick_types=[brick_type] if brick_type else [], location=location)
    return TopologyGraph(building_id=building_id, config_type="test", nx_graph=g, edges_by_relation={
        "feeds": set(), "hasPoint": set(), "hasPart": set()
    })


def test_ahu_to_terminal_and_terminal_to_zone_candidates(ontology):
    tg = make_tg("t1", {
        "ahu": ("AHU", None),
        "vav1": ("VAV", None),
        "vav2": ("VAV", None),
        "zone1": ("HVAC_Zone", None),
        "zone2": ("HVAC_Zone", None),
    })
    cands = generate_feeds_candidates(tg, ontology)
    pairs = {(c.source, c.target) for c in cands}
    assert ("ahu", "vav1") in pairs
    assert ("ahu", "vav2") in pairs
    assert ("vav1", "zone1") in pairs
    assert ("vav2", "zone2") in pairs
    # AHU -> Location tier also fires (single-duct systems feed zones directly)
    assert ("ahu", "zone1") in pairs
    # never candidates in the wrong direction
    assert ("zone1", "ahu") not in pairs
    assert ("vav1", "ahu") not in pairs


def test_location_metadata_excludes_cross_location_pairs(ontology):
    tg = make_tg("t2", {
        "vav_a": ("VAV", "loc_A"),
        "zone_a": ("HVAC_Zone", "loc_A"),
        "zone_b": ("HVAC_Zone", "loc_B"),
    })
    cands = generate_feeds_candidates(tg, ontology)
    pairs = {(c.source, c.target) for c in cands}
    assert ("vav_a", "zone_a") in pairs
    assert ("vav_a", "zone_b") not in pairs  # excluded: locations disagree


def test_missing_location_never_excludes(ontology):
    """Absent location metadata must never be treated as a mismatch."""
    tg = make_tg("t3", {
        "vav_a": ("VAV", None),
        "zone_a": ("HVAC_Zone", "loc_A"),
        "zone_b": ("HVAC_Zone", None),
    })
    cands = generate_feeds_candidates(tg, ontology)
    pairs = {(c.source, c.target) for c in cands}
    assert ("vav_a", "zone_a") in pairs
    assert ("vav_a", "zone_b") in pairs


def test_pump_to_coil_tier(ontology):
    tg = make_tg("t4", {
        "pump": ("Chilled_Water_Pump", None),
        "coil": ("Chilled_Water_Coil", None),
        "vav": ("VAV", None),
    })
    cands = generate_feeds_candidates(tg, ontology)
    pairs = {(c.source, c.target) for c in cands}
    assert ("pump", "coil") in pairs
    assert ("pump", "vav") not in pairs  # pump is not an AHU; no tier permits this


def test_untyped_nodes_produce_no_candidates(ontology):
    tg = make_tg("t5", {"a": (None, None), "b": (None, None)})
    assert generate_feeds_candidates(tg, ontology) == []
    assert generate_haspart_candidates(tg, ontology) == []
    assert generate_haspoint_candidates(tg, ontology) == []


def test_coverage_reports_missed_true_edges_explicitly():
    from hvac_benchmark.experiment.candidates import Candidate

    candidates = [Candidate("a", "b", "feeds", "test"), Candidate("a", "c", "feeds", "test")]
    true_edges = {("a", "b"), ("a", "d")}  # "a->d" is not in the candidate set
    report = candidate_coverage(candidates, true_edges)
    assert report.n_true_edges == 2
    assert report.n_covered == 1
    assert report.n_missed == 1
    assert report.missed_edges == (("a", "d"),)
    assert 0.49 < report.coverage_rate < 0.51


def test_full_coverage_rate_is_one():
    from hvac_benchmark.experiment.candidates import Candidate

    candidates = [Candidate("a", "b", "feeds", "test")]
    report = candidate_coverage(candidates, {("a", "b")})
    assert report.coverage_rate == 1.0
    assert report.n_missed == 0
