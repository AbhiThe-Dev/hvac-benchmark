"""Candidate edge generation via Brick subclass reasoning and explicit
physical compatibility rules.

Every candidate is generated from a documented compatibility tier keyed on
`rdfs:subClassOf` ancestry in the reference Brick ontology (never on literal
class-name string matches), so the same rules generalize across topologies.
Location exclusions are applied only when both endpoints carry independently
asserted `brick:hasLocation` metadata that disagrees; absent metadata never
excludes a pair, since that would be guessing.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..data.ontology import BrickOntology
from ..graph.networkx_build import TopologyGraph

# (source ancestor, target ancestor, human-readable rationale). Every tier is
# grounded in the compatibility patterns actually observed in the corpus
# during design (see README/data-inspection notes): AHU/RTU -> terminal
# units, AHU/RTU -> zones directly (single-duct systems with no terminal
# unit), terminal units -> zones/rooms, and plant-side pumps -> coils.
FEEDS_COMPATIBILITY_TIERS: tuple[tuple[str, str, str], ...] = (
    ("AHU", "Terminal_Unit", "air handling / rooftop unit supplies a terminal unit"),
    ("AHU", "Location", "air handling / rooftop unit supplies a zone or room directly"),
    ("Terminal_Unit", "Location", "terminal unit supplies a zone or room"),
    ("Pump", "Coil", "pump circulates water through a coil"),
)

HASPART_ANCESTOR = "Equipment"
HASPOINT_SOURCE_ANCESTORS: tuple[str, ...] = ("Equipment", "Location")
HASPOINT_TARGET_ANCESTOR = "Point"


@dataclass(frozen=True)
class Candidate:
    source: str
    target: str
    relation: str
    rationale: str


def _type_of(tg: TopologyGraph, node: str) -> str | None:
    return tg.node_type(node)


def _has_ancestor(ontology: BrickOntology, node_type: str | None, ancestor: str) -> bool:
    if node_type is None:
        return False
    return ancestor in ontology.ancestors(node_type)


def _location_excludes(tg: TopologyGraph, a: str, b: str) -> bool:
    loc_a, loc_b = tg.node_location(a), tg.node_location(b)
    return loc_a is not None and loc_b is not None and loc_a != loc_b


def generate_feeds_candidates(tg: TopologyGraph, ontology: BrickOntology) -> list[Candidate]:
    nodes = tg.nodes()
    candidates: list[Candidate] = []
    for source_anc, target_anc, rationale in FEEDS_COMPATIBILITY_TIERS:
        sources = [n for n in nodes if _has_ancestor(ontology, _type_of(tg, n), source_anc)]
        targets = [n for n in nodes if _has_ancestor(ontology, _type_of(tg, n), target_anc)]
        for s in sources:
            for t in targets:
                if s == t:
                    continue
                if _location_excludes(tg, s, t):
                    continue
                candidates.append(Candidate(s, t, "feeds", rationale))
    # de-duplicate (a pair could qualify under more than one tier)
    seen = set()
    deduped = []
    for c in candidates:
        key = (c.source, c.target)
        if key not in seen:
            seen.add(key)
            deduped.append(c)
    return deduped


def generate_haspart_candidates(tg: TopologyGraph, ontology: BrickOntology) -> list[Candidate]:
    nodes = [n for n in tg.nodes() if _has_ancestor(ontology, _type_of(tg, n), HASPART_ANCESTOR)]
    candidates = []
    for s in nodes:
        for t in nodes:
            if s == t or _location_excludes(tg, s, t):
                continue
            candidates.append(Candidate(s, t, "hasPart", "equipment may contain another piece of equipment"))
    return candidates


def generate_haspoint_candidates(tg: TopologyGraph, ontology: BrickOntology) -> list[Candidate]:
    nodes = tg.nodes()
    sources = [
        n for n in nodes if any(_has_ancestor(ontology, _type_of(tg, n), a) for a in HASPOINT_SOURCE_ANCESTORS)
    ]
    points = [n for n in nodes if _has_ancestor(ontology, _type_of(tg, n), HASPOINT_TARGET_ANCESTOR)]
    candidates = []
    for s in sources:
        for p in points:
            if s == p or _location_excludes(tg, s, p):
                continue
            candidates.append(Candidate(s, p, "hasPoint", "equipment or location may have a monitoring point"))
    return candidates


def generate_candidates(tg: TopologyGraph, relation: str, ontology: BrickOntology) -> list[Candidate]:
    if relation == "feeds":
        return generate_feeds_candidates(tg, ontology)
    if relation == "hasPart":
        return generate_haspart_candidates(tg, ontology)
    if relation == "hasPoint":
        return generate_haspoint_candidates(tg, ontology)
    raise ValueError(f"unknown relation {relation!r}")


@dataclass(frozen=True)
class CoverageReport:
    n_true_edges: int
    n_covered: int
    n_missed: int
    missed_edges: tuple[tuple[str, str], ...]

    @property
    def coverage_rate(self) -> float:
        return self.n_covered / self.n_true_edges if self.n_true_edges else float("nan")


def candidate_coverage(candidates: list[Candidate], true_edges: set[tuple[str, str]]) -> CoverageReport:
    """Excluded true edges are reported, never silently absorbed: any true
    edge missing from the candidate set remains a guaranteed false negative
    for every policy in the downstream experiment."""
    candidate_pairs = {(c.source, c.target) for c in candidates}
    missed = tuple(sorted(true_edges - candidate_pairs))
    covered = len(true_edges) - len(missed)
    return CoverageReport(
        n_true_edges=len(true_edges),
        n_covered=covered,
        n_missed=len(missed),
        missed_edges=missed,
    )
