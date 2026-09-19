"""Split-file merge fixtures: cross-file relationships must survive
merging, unresolved (non-confirmed) groupings must be excluded rather than
guessed, and structurally duplicate topologies must not inflate counts."""

from __future__ import annotations

from hvac_benchmark.graph.building_grouping import BuildingGroup, merge_all, merge_group
from hvac_benchmark.graph.inventory import flag_duplicates, inventory_topology
from hvac_benchmark.graph.networkx_build import build_topology_graph

from conftest import FIXTURES_DIR

PART_A = (FIXTURES_DIR / "split_building_part_a.ttl").read_bytes()
PART_B = (FIXTURES_DIR / "split_building_part_b.ttl").read_bytes()


def test_cross_file_relationship_survives_merge(ontology):
    group = BuildingGroup(
        "test_building",
        ("part_a.ttl", "part_b.ttl"),
        "experimental",
        "test fixture: two files documented as the same physical testbed",
    )
    files = {"part_a.ttl": PART_A, "part_b.ttl": PART_B}
    merged = merge_group(group, files, ontology)
    tg = build_topology_graph(merged.building_id, merged.config_type, merged.graph)

    # AHU_1 (typed in file A) must be recognized as feeding VAV_1 (relation
    # asserted in file B) -- this only works if both files share node
    # identity under the common base URI.
    ahu = next(n for n in tg.nodes() if tg.node_type(n) == "AHU")
    vav = next(n for n in tg.nodes() if tg.node_type(n) == "VAV")
    zone = next(n for n in tg.nodes() if tg.node_type(n) == "HVAC_Zone")
    assert (ahu, vav) in tg.edges_by_relation["feeds"]
    assert (vav, zone) in tg.edges_by_relation["feeds"]


def test_unmerged_files_do_not_spuriously_unify_or_silently_connect(ontology):
    """If the same two files are parsed as SEPARATE (unconfirmed) groups
    instead of merged, the cross-file relationship must not silently
    connect typed nodes from one file to typed nodes in the other."""
    group_a = BuildingGroup("part_a_only", ("part_a.ttl",), "experimental", "standalone")
    group_b = BuildingGroup("part_b_only", ("part_b.ttl",), "experimental", "standalone")
    files = {"part_a.ttl": PART_A, "part_b.ttl": PART_B}

    merged_a = merge_group(group_a, files, ontology)
    merged_b = merge_group(group_b, files, ontology)
    tg_a = build_topology_graph(merged_a.building_id, merged_a.config_type, merged_a.graph)
    tg_b = build_topology_graph(merged_b.building_id, merged_b.config_type, merged_b.graph)

    # file A alone has typed nodes but no relationships at all
    assert tg_a.edges_by_relation["feeds"] == set()
    # file B alone has the relationship triples, but AHU_1/VAV_1 there carry
    # no type (the type assertions live only in file A) -- so nothing about
    # file A's types leaks into file B's separate node identity space.
    ahu_nodes_in_b = [n for n in tg_b.nodes() if tg_b.node_type(n) == "AHU"]
    assert ahu_nodes_in_b == []


def test_ambiguous_grouping_is_excluded_not_merged(ontology):
    confirmed = BuildingGroup("ok", ("part_a.ttl",), "experimental", "evidence")
    ambiguous = BuildingGroup("ambiguous_case", ("part_b.ttl",), "unknown", "insufficient evidence", status="ambiguous")
    files = {"part_a.ttl": PART_A, "part_b.ttl": PART_B}

    merged, excluded = merge_all((confirmed, ambiguous), files, ontology)
    assert [m.building_id for m in merged] == ["ok"]
    assert [g.building_id for g in excluded] == ["ambiguous_case"]


def test_missing_member_file_excludes_group_rather_than_partial_merge(ontology):
    group = BuildingGroup("incomplete", ("part_a.ttl", "does_not_exist.ttl"), "experimental", "evidence")
    files = {"part_a.ttl": PART_A}
    merged, excluded = merge_all((group,), files, ontology)
    assert merged == []
    assert [g.building_id for g in excluded] == ["incomplete"]


def test_duplicate_topologies_are_flagged_and_do_not_inflate_counts(ontology):
    group_1 = BuildingGroup("building_1", ("part_a.ttl", "part_b.ttl"), "experimental", "evidence")
    files = {"part_a.ttl": PART_A, "part_b.ttl": PART_B}
    merged1 = merge_group(group_1, files, ontology)
    merged2 = merge_group(
        BuildingGroup("building_2_relabeled", ("part_a.ttl", "part_b.ttl"), "experimental", "evidence"),
        files, ontology,
    )
    tg1 = build_topology_graph(merged1.building_id, merged1.config_type, merged1.graph)
    tg2 = build_topology_graph(merged2.building_id, merged2.config_type, merged2.graph)

    inv1 = inventory_topology(tg1, merged1.parse_reports)
    inv2 = inventory_topology(tg2, merged2.parse_reports)
    flagged = flag_duplicates([inv1, inv2])

    assert flagged[0].is_duplicate_of is None
    assert flagged[1].is_duplicate_of == "building_1"

    # a naive "count every merged topology" would say 2 independent
    # buildings; the correct count excludes the flagged duplicate.
    independent_count = sum(1 for inv in flagged if inv.is_duplicate_of is None)
    assert independent_count == 1
