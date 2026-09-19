"""Fetch, cache, and query the reference Brick ontology.

Candidate generation uses this ontology's `rdfs:subClassOf` hierarchy for
genuine subclass reasoning (e.g. `RTU` sqsubseteq `AHU`, `VAV` sqsubseteq
`Terminal_Unit`) rather than a hand-rolled class table, and its documented
`owl:inverseOf` declarations to normalize inverse relationship predicates
(e.g. `isFedBy` -> `feeds`) without inventing new equivalences.
"""

from __future__ import annotations

import logging
from functools import lru_cache

import rdflib
import requests

from .cache import FileCache

logger = logging.getLogger(__name__)

BRICK_VERSION_TAG = "v1.3.0"
BRICK_TTL_URL = f"https://github.com/BrickSchema/Brick/releases/download/{BRICK_VERSION_TAG}/Brick.ttl"
BRICK_NS = rdflib.Namespace("https://brickschema.org/schema/Brick#")
RDFS = rdflib.RDFS
OWL = rdflib.OWL
LOGICAL_NAME = "brick_ontology__Brick.ttl"


def fetch_brick_ontology_bytes(cache: FileCache, max_retries: int = 3) -> bytes:
    if cache.has(LOGICAL_NAME):
        return cache.get_bytes(LOGICAL_NAME)
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(BRICK_TTL_URL, timeout=60)
            resp.raise_for_status()
            data = resp.content
            cache.put(
                LOGICAL_NAME,
                data,
                source="brick_ontology",
                archive_url=BRICK_TTL_URL,
                archive_entry_name="Brick.ttl",
                archive_entry_crc32=0,
                license="BSD-3-Clause (BrickSchema/Brick)",
                citation=f"BrickSchema/Brick {BRICK_VERSION_TAG} Brick.ttl",
                source_revision=BRICK_VERSION_TAG,
            )
            return data
        except requests.RequestException as exc:
            last_error = exc
            logger.warning("Brick ontology fetch attempt %d/%d failed: %s", attempt, max_retries, exc)
    raise RuntimeError(f"could not fetch Brick ontology after {max_retries} attempts") from last_error


@lru_cache(maxsize=1)
def _load_ontology_graph_from_bytes(data: bytes) -> rdflib.Graph:
    g = rdflib.Graph()
    g.parse(data=data, format="turtle")
    return g


class BrickOntology:
    """Thin wrapper exposing subclass-closure and inverse-property lookups."""

    def __init__(self, graph: rdflib.Graph):
        self.graph = graph
        self._ancestor_cache: dict[str, frozenset[str]] = {}
        self._inverse_map: dict[str, str] | None = None
        self._known_classes: frozenset[str] | None = None

    @classmethod
    def load(cls, cache: FileCache) -> "BrickOntology":
        data = fetch_brick_ontology_bytes(cache)
        return cls(_load_ontology_graph_from_bytes(data))

    def known_classes(self) -> frozenset[str]:
        if self._known_classes is None:
            classes = set()
            for s in self.graph.subjects(rdflib.RDF.type, OWL.Class):
                if str(s).startswith(str(BRICK_NS)):
                    classes.add(str(s).rsplit("#", 1)[-1])
            self._known_classes = frozenset(classes)
        return self._known_classes

    def ancestors(self, class_local_name: str) -> frozenset[str]:
        """Local names of all rdfs:subClassOf ancestors, plus the class
        itself, plus anything documented as owl:equivalentClass to any class
        already found (in either subject/object position, since equivalence
        is symmetric). The equivalentClass closure matters in practice: Brick
        1.3.0 declares some classes equivalent-but-not-subclass pairs (e.g.
        `AHU` / `Air_Handler_Unit`), and a corpus that happens to use the
        non-canonical name of such a pair must still match compatibility
        tiers written against the canonical name. Only documented axioms in
        the reference ontology are followed here -- never a guessed mapping
        across ontologies (e.g. no Brick/REC bridging is invented)."""
        if class_local_name in self._ancestor_cache:
            return self._ancestor_cache[class_local_name]
        cls = BRICK_NS[class_local_name]
        seen = {class_local_name}
        frontier = [cls]
        while frontier:
            c = frontier.pop()
            related = (
                list(self.graph.objects(c, RDFS.subClassOf))
                + list(self.graph.objects(c, OWL.equivalentClass))
                + list(self.graph.subjects(OWL.equivalentClass, c))
            )
            for parent in related:
                if isinstance(parent, rdflib.URIRef):
                    name = str(parent).rsplit("#", 1)[-1]
                    if name not in seen:
                        seen.add(name)
                        frontier.append(parent)
        result = frozenset(seen)
        self._ancestor_cache[class_local_name] = result
        return result

    def is_a(self, class_local_name: str, ancestor_local_name: str) -> bool:
        return ancestor_local_name in self.ancestors(class_local_name)

    def inverse_of(self, predicate_local_name: str) -> str | None:
        """Return the documented inverse predicate's local name, if any."""
        if self._inverse_map is None:
            mapping: dict[str, str] = {}
            for s, o in self.graph.subject_objects(OWL.inverseOf):
                if str(s).startswith(str(BRICK_NS)) and str(o).startswith(str(BRICK_NS)):
                    s_name = str(s).rsplit("#", 1)[-1]
                    o_name = str(o).rsplit("#", 1)[-1]
                    mapping[s_name] = o_name
                    mapping[o_name] = s_name
            self._inverse_map = mapping
        return self._inverse_map.get(predicate_local_name)
