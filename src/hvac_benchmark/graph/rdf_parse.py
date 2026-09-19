"""Parse a single Brick TTL file into an RDFLib graph with an explicit,
deterministic base URI, then normalize inverse relationships and documented
class-casing aliases against the reference Brick ontology.

Explicit base URIs matter here: every LBNL FDD file in this corpus declares
the *same* relative prefix (`@prefix bldg: <bldg-59#>`). Parsing two such
files without pinning a base URI risks either (a) both resolving against an
identical default base (e.g. rdflib's `about:blank`), silently aliasing
unrelated testbeds' `bldg:AHU` nodes onto the same URI, or (b) resolving
against incidental filesystem paths, making node identity depend on where
the cache happens to live. We always pass an explicit `publicID` so identity
is a deliberate choice: one shared base per verified building group, a
unique base per standalone file.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import rdflib

from ..data.ontology import BrickOntology

logger = logging.getLogger(__name__)

BRICK_NS = "https://brickschema.org/schema/Brick#"
RDF_TYPE = rdflib.RDF.type

CANONICAL_RELATIONS = ("feeds", "hasPart", "hasPoint", "hasLocation")


@dataclass
class ParseReport:
    triples_in: int
    triples_out: int
    inverse_edges_normalized: int
    class_aliases_applied: dict[str, str]
    unknown_classes: set[str]


def parse_brick_bytes(data: bytes, base_uri: str, fmt: str = "turtle") -> rdflib.Graph:
    g = rdflib.Graph()
    g.parse(data=data, format=fmt, publicID=base_uri)
    return g


def _local_name(term: rdflib.term.Identifier) -> str | None:
    s = str(term)
    if "#" in s:
        return s.rsplit("#", 1)[-1]
    return None


def normalize_graph(graph: rdflib.Graph, ontology: BrickOntology) -> tuple[rdflib.Graph, ParseReport]:
    """Rewrite inverse-predicate triples to canonical direction and fix
    documented class-casing aliases. Never adds a relationship that was not
    already asserted (directly or as its documented inverse)."""
    out = rdflib.Graph()
    inverse_count = 0
    aliases: dict[str, str] = {}
    unknown_classes: set[str] = set()
    known = ontology.known_classes()
    known_lower = {name.lower(): name for name in known}

    for s, p, o in graph:
        pred_name = _local_name(p)
        if pred_name and str(p).startswith(BRICK_NS):
            inverse = ontology.inverse_of(pred_name)
            if pred_name not in CANONICAL_RELATIONS and inverse in CANONICAL_RELATIONS:
                out.add((o, rdflib.URIRef(BRICK_NS + inverse), s))
                inverse_count += 1
                continue

        if p == RDF_TYPE:
            cls_name = _local_name(o)
            if cls_name and str(o).startswith(BRICK_NS) and cls_name not in known:
                canonical = known_lower.get(cls_name.lower())
                if canonical is not None:
                    aliases[cls_name] = canonical
                    out.add((s, p, rdflib.URIRef(BRICK_NS + canonical)))
                    continue
                unknown_classes.add(cls_name)

        out.add((s, p, o))

    report = ParseReport(
        triples_in=len(graph),
        triples_out=len(out),
        inverse_edges_normalized=inverse_count,
        class_aliases_applied=aliases,
        unknown_classes=unknown_classes,
    )
    return out, report
