"""Policy-view leakage prevention: opaque identifiers must not encode real
names, true degree, target relationships, or a truth-derived order."""

from __future__ import annotations

import networkx as nx

from hvac_benchmark.experiment.candidates import Candidate
from hvac_benchmark.experiment.policy_view import build_policy_view
from hvac_benchmark.graph.networkx_build import TopologyGraph


def make_rich_tg() -> TopologyGraph:
    g = nx.MultiDiGraph()
    names = {
        "AHU_1": ("AHU", None),
        "VAV_Box_202": ("VAV", None),
        "Terminal_Room_202": ("HVAC_Zone", None),
        "VAV_Box_105": ("VAV", None),
        "Terminal_Room_105": ("HVAC_Zone", None),
    }
    for n, (t, loc) in names.items():
        g.add_node(n, brick_type=t, brick_types=[t], location=loc)
    edges = {"feeds": {("AHU_1", "VAV_Box_202"), ("VAV_Box_202", "Terminal_Room_202"),
                       ("AHU_1", "VAV_Box_105"), ("VAV_Box_105", "Terminal_Room_105")},
             "hasPoint": set(), "hasPart": set()}
    return TopologyGraph("t", "test", g, edges)


def test_opaque_ids_never_contain_real_names():
    tg = make_rich_tg()
    candidates = [
        Candidate("AHU_1", "VAV_Box_202", "feeds", "r"),
        Candidate("AHU_1", "VAV_Box_105", "feeds", "r"),
        Candidate("VAV_Box_202", "Terminal_Room_202", "feeds", "r"),
        Candidate("VAV_Box_105", "Terminal_Room_105", "feeds", "r"),
    ]
    view = build_policy_view(tg, candidates, seed=1)

    real_name_fragments = ("AHU", "VAV", "202", "105", "Terminal", "Room", "Box")
    for opaque_id in view.nodes:
        assert not any(frag in opaque_id for frag in real_name_fragments)
    for c in view.candidates:
        assert not any(frag in c.source for frag in real_name_fragments)
        assert not any(frag in c.target for frag in real_name_fragments)


def test_opaque_id_matching_numeric_suffixes_do_not_encode_the_true_pairing():
    """VAV_Box_202 / Terminal_Room_202 share a numeric suffix that IS the
    true connection in the source data; the opaque view must not let a
    policy recover that correlation from id structure."""
    tg = make_rich_tg()
    candidates = [
        Candidate("VAV_Box_202", "Terminal_Room_202", "feeds", "r"),
        Candidate("VAV_Box_105", "Terminal_Room_105", "feeds", "r"),
        Candidate("VAV_Box_202", "Terminal_Room_105", "feeds", "r"),  # false pair, must look equally plausible
        Candidate("VAV_Box_105", "Terminal_Room_202", "feeds", "r"),  # false pair
    ]
    view = build_policy_view(tg, candidates, seed=3)
    # opaque ids are just sequential N#### tokens -- no shared substring
    # signals a true pairing the way the real names' shared "202"/"105" do.
    for c in view.candidates:
        assert c.source[0] == "N" and c.target[0] == "N"
        assert len(c.source) == len(c.target) == 5


def test_view_exposes_no_degree_or_relationship_information():
    tg = make_rich_tg()
    candidates = [Candidate(s, t, "feeds", "r") for s, t in tg.edges_by_relation["feeds"]]
    view = build_policy_view(tg, candidates, seed=5)
    for node in view.nodes.values():
        assert not hasattr(node, "degree")
        assert not hasattr(node, "true_targets")
        assert not hasattr(node, "neighbors")
    # the only fields present are id, type, and opaque location
    assert set(vars(next(iter(view.nodes.values())))) == {"opaque_id", "brick_type", "location_opaque"}


def test_id_assignment_order_is_seed_shuffled_not_insertion_order():
    tg = make_rich_tg()
    candidates = [Candidate(s, t, "feeds", "r") for s, t in tg.edges_by_relation["feeds"]]
    view_a = build_policy_view(tg, candidates, seed=1)
    view_b = build_policy_view(tg, candidates, seed=2)
    # same real nodes should generally map to different opaque ids across seeds
    assert view_a.real_to_opaque != view_b.real_to_opaque


def test_candidate_order_is_shuffled_not_generation_order():
    tg = make_rich_tg()
    candidates = [Candidate(s, t, "feeds", "r") for s, t in sorted(tg.edges_by_relation["feeds"])]
    view = build_policy_view(tg, candidates, seed=9)
    original_pairs = [(c.source, c.target) for c in candidates]
    opaque_pairs_in_original_order = [
        (view.real_to_opaque[s], view.real_to_opaque[t]) for s, t in original_pairs
    ]
    view_pairs = [(c.source, c.target) for c in view.candidates]
    assert view_pairs != opaque_pairs_in_original_order
