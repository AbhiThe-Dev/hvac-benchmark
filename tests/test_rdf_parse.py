"""RDF normalization: inverse relationships are rewritten to canonical
direction (never inventing a new relationship), and documented class-casing
aliases are fixed without absorbing genuinely unknown classes."""

from __future__ import annotations

from hvac_benchmark.graph.rdf_parse import normalize_graph, parse_brick_bytes

INVERSE_FIXTURE = b"""
@prefix bldg: <bldg-y#> .
@prefix brick: <https://brickschema.org/schema/Brick#> .

bldg:VAV_1 a brick:VAV .
bldg:Zone_1 a brick:HVAC_Zone .
bldg:Zone_1 brick:isFedBy bldg:VAV_1 .
"""

ALIAS_FIXTURE = b"""
@prefix bldg: <bldg-z#> .
@prefix brick: <https://brickschema.org/schema/Brick#> .

bldg:Fan_1 a brick:Speed_status .
bldg:Weird_1 a brick:Totally_Not_A_Real_Brick_Class .
"""


def test_inverse_predicate_rewritten_to_canonical_direction(ontology):
    g = parse_brick_bytes(INVERSE_FIXTURE, base_uri="https://test.invalid/x/")
    normalized, report = normalize_graph(g, ontology)

    vav = next(s for s in normalized.subjects() if str(s).endswith("VAV_1"))
    zone = next(s for s in normalized.subjects() if str(s).endswith("Zone_1"))

    feeds_triples = [(s, o) for s, p, o in normalized if str(p).endswith("feeds")]
    is_fed_by_triples = [(s, o) for s, p, o in normalized if str(p).endswith("isFedBy")]

    assert (vav, zone) in feeds_triples
    assert is_fed_by_triples == []  # inverse predicate must not survive
    assert report.inverse_edges_normalized == 1
    # the triple count is preserved -- no new relationship was invented
    assert report.triples_out == report.triples_in


def test_never_invents_a_relationship_not_asserted_or_its_inverse(ontology):
    g = parse_brick_bytes(INVERSE_FIXTURE, base_uri="https://test.invalid/x2/")
    normalized, _ = normalize_graph(g, ontology)
    # only exactly the one feeds edge should exist -- nothing extra
    feeds_triples = [(s, o) for s, p, o in normalized if str(p).endswith("feeds")]
    assert len(feeds_triples) == 1


def test_known_casing_alias_is_fixed(ontology):
    g = parse_brick_bytes(ALIAS_FIXTURE, base_uri="https://test.invalid/y/")
    normalized, report = normalize_graph(g, ontology)
    assert report.class_aliases_applied.get("Speed_status") == "Speed_Status"
    fan_types = [str(o).rsplit("#", 1)[-1] for s, p, o in normalized if "Fan_1" in str(s) and str(p).endswith("type")]
    assert fan_types == ["Speed_Status"]


def test_genuinely_unknown_class_is_reported_not_silently_matched(ontology):
    g = parse_brick_bytes(ALIAS_FIXTURE, base_uri="https://test.invalid/y2/")
    _, report = normalize_graph(g, ontology)
    assert "Totally_Not_A_Real_Brick_Class" in report.unknown_classes
    assert "Totally_Not_A_Real_Brick_Class" not in report.class_aliases_applied
