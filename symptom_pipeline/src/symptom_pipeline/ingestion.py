"""Ingest a documented topology from a Brick graph or an equipment/
connection table, with reviewed manual identity mapping from drawings.

Two things are produced together, always:

- a `contracts.DocumentedGraph` (equipment identities, claimed connections,
  provenance) -- the versioned, auditable ingestion contract, and
- an `hvac_benchmark.graph.networkx_build.TopologyGraph` built over the
  *same* node set -- required because candidate generation
  (`hvac_benchmark.experiment.candidates.generate_feeds_candidates`) and
  feature extraction both operate on `TopologyGraph`, not on this package's
  own contract types.

Node identity, Brick type, and location metadata are assumed identical
between the documented and actual topology in the v1 causal-training scope
(only *connections* differ, per the design doc's fixed-inventory
restriction) -- so one `TopologyGraph` legitimately serves both roles here.
Ingestion never uses `room_label` to exclude a candidate connection itself;
that exclusion already happens inside `generate_feeds_candidates` via
`hasLocation`-derived `node_location`, and only when both endpoints carry
independently asserted, disagreeing location metadata. `room_label` is kept
on `EquipmentIdentity` for audit/display only.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import networkx as nx
import rdflib
from hvac_benchmark.graph.networkx_build import TopologyGraph

from .contracts import DocumentedConnection, DocumentedGraph, EquipmentIdentity

BRICK_NS = "https://brickschema.org/schema/Brick#"
VALID_RELATIONS = ("feeds", "hasPart", "hasPoint")


def hash_source_files(paths: list[Path]) -> str:
    """sha256 over the sorted, concatenated bytes of every given file.

    Recorded on every `DocumentedGraph` because neither `hvac_benchmark`
    (no git checkout at the benchmark root) nor `physics_pipeline` (git
    checkout with uncommitted changes) can be relied on as a reproducible
    version pin by themselves.
    """
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.read_bytes())
    return digest.hexdigest()


@dataclass(frozen=True)
class IdentityMappingIssue:
    equipment_id: str
    issue: str


def _local(term: object) -> str:
    s = str(term)
    return s.rsplit("#", 1)[-1] if "#" in s else s


def load_documented_graph_from_brick(
    building_id: str,
    ttl_paths: list[Path],
    ingestion_source: str = "brick_ttl",
) -> tuple[DocumentedGraph, TopologyGraph]:
    """Load a documented topology directly from one or more Brick TTL files.

    This intentionally does not reuse `hvac_benchmark.graph.rdf_parse`'s
    multi-file inverse-normalization pipeline (that machinery exists to
    reconcile independently-sourced FDD testbed exports, which is not this
    package's ingestion scenario); it parses the TTL directly, recognizing
    only the same three canonical relations `hvac_benchmark` uses.
    """
    graph = rdflib.Graph()
    for path in ttl_paths:
        graph.parse(source=str(path), format="turtle")

    node_types: dict[str, set[str]] = {}
    node_locations: dict[str, str] = {}
    for s, p, o in graph:
        if p == rdflib.RDF.type and str(o).startswith(BRICK_NS):
            node_types.setdefault(str(s), set()).add(_local(o))
    for s, p, o in graph:
        if str(p) == BRICK_NS + "hasLocation" and isinstance(o, rdflib.URIRef):
            node_locations[str(s)] = str(o)

    nx_graph = nx.MultiDiGraph()
    edges_by_relation: dict[str, set[tuple[str, str]]] = {rel: set() for rel in VALID_RELATIONS}
    connections: list[DocumentedConnection] = []

    for node in set(node_types) | set(node_locations):
        nx_graph.add_node(node)

    for s, p, o in graph:
        pred_name = _local(p)
        if pred_name in VALID_RELATIONS and isinstance(s, rdflib.URIRef) and isinstance(o, rdflib.URIRef):
            nx_graph.add_node(str(s))
            nx_graph.add_node(str(o))
            nx_graph.add_edge(str(s), str(o), relation=pred_name)
            edges_by_relation[pred_name].add((str(s), str(o)))
            connections.append(DocumentedConnection(str(s), str(o), pred_name))

    equipment: list[EquipmentIdentity] = []
    for node in nx_graph.nodes():
        types = sorted(node_types.get(node, set()))
        brick_type = types[0] if types else "Unknown"
        nx_graph.nodes[node]["brick_type"] = types[0] if types else None
        nx_graph.nodes[node]["brick_types"] = types
        nx_graph.nodes[node]["location"] = node_locations.get(node)
        equipment.append(
            EquipmentIdentity(
                equipment_id=node,
                brick_type=brick_type,
                display_name=_local(node),
                room_label=node_locations.get(node),
                source_ref=f"{ingestion_source}:{node}",
            )
        )

    tg = TopologyGraph(
        building_id=building_id,
        config_type="symptom_pipeline_documented",
        nx_graph=nx_graph,
        edges_by_relation=edges_by_relation,
    )
    dg = DocumentedGraph(
        building_id=building_id,
        equipment=tuple(equipment),
        claimed_connections=tuple(connections),
        ingestion_source=ingestion_source,
        source_hash=hash_source_files(ttl_paths),
    )
    return dg, tg


def load_documented_graph_from_table(
    building_id: str,
    equipment_rows: list[dict],
    connection_rows: list[dict],
    source_paths: list[Path],
    ingestion_source: str = "equipment_table",
) -> tuple[DocumentedGraph, TopologyGraph]:
    """Load a documented topology from reviewed equipment/connection tables.

    `equipment_rows`: dicts with keys `equipment_id`, `brick_type`,
    `display_name`, and optionally `room_label`. `connection_rows`: dicts
    with keys `source_id`, `target_id`, `relation` (must be one of
    `VALID_RELATIONS`). Both are assumed to already be the product of a
    reviewed manual mapping from drawings -- this function validates
    structural consistency (see `validate_documented_graph`) but does not
    itself perform or check that review.
    """
    equipment = tuple(
        EquipmentIdentity(
            equipment_id=row["equipment_id"],
            brick_type=row["brick_type"],
            display_name=row.get("display_name", row["equipment_id"]),
            room_label=row.get("room_label"),
            source_ref=f"{ingestion_source}:{row['equipment_id']}",
        )
        for row in equipment_rows
    )
    connections = tuple(
        DocumentedConnection(row["source_id"], row["target_id"], row["relation"]) for row in connection_rows
    )
    dg = DocumentedGraph(
        building_id=building_id,
        equipment=equipment,
        claimed_connections=connections,
        ingestion_source=ingestion_source,
        source_hash=hash_source_files(source_paths) if source_paths else "unhashed:inline",
    )

    nx_graph = nx.MultiDiGraph()
    edges_by_relation: dict[str, set[tuple[str, str]]] = {rel: set() for rel in VALID_RELATIONS}
    for e in equipment:
        nx_graph.add_node(
            e.equipment_id,
            brick_type=e.brick_type,
            brick_types=[e.brick_type],
            location=e.room_label,
        )
    for c in connections:
        nx_graph.add_edge(c.source_id, c.target_id, relation=c.relation)
        edges_by_relation.setdefault(c.relation, set()).add((c.source_id, c.target_id))

    tg = TopologyGraph(
        building_id=building_id,
        config_type="symptom_pipeline_documented",
        nx_graph=nx_graph,
        edges_by_relation=edges_by_relation,
    )
    return dg, tg


def validate_documented_graph(dg: DocumentedGraph) -> list[IdentityMappingIssue]:
    """Structural validation only -- duplicate IDs, connections referencing
    equipment not in the inventory, and unrecognized relations. Does not
    (and cannot) validate that the reviewed identity mapping itself is
    physically correct; that remains a human review step.
    """
    issues: list[IdentityMappingIssue] = []
    seen_ids: set[str] = set()
    for e in dg.equipment:
        if e.equipment_id in seen_ids:
            issues.append(IdentityMappingIssue(e.equipment_id, "duplicate equipment_id"))
        seen_ids.add(e.equipment_id)

    for c in dg.claimed_connections:
        if c.source_id not in seen_ids:
            issues.append(IdentityMappingIssue(c.source_id, "connection source not in equipment inventory"))
        if c.target_id not in seen_ids:
            issues.append(IdentityMappingIssue(c.target_id, "connection target not in equipment inventory"))
        if c.relation not in VALID_RELATIONS:
            issues.append(IdentityMappingIssue(c.source_id, f"unrecognized relation {c.relation!r}"))
    return issues
