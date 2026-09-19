"""Build a typed NetworkX graph from a normalized, merged Brick RDF graph."""

from __future__ import annotations

from dataclasses import dataclass, field

import networkx as nx
import rdflib

from .rdf_parse import CANONICAL_RELATIONS, RDF_TYPE

BRICK_NS = "https://brickschema.org/schema/Brick#"


def _local(term) -> str:
    s = str(term)
    return s.rsplit("#", 1)[-1] if "#" in s else s


@dataclass
class TopologyGraph:
    building_id: str
    config_type: str
    nx_graph: nx.MultiDiGraph
    edges_by_relation: dict[str, set[tuple[str, str]]] = field(default_factory=dict)

    def nodes(self) -> list[str]:
        return list(self.nx_graph.nodes())

    def node_type(self, node: str) -> str | None:
        return self.nx_graph.nodes[node].get("brick_type")

    def node_location(self, node: str) -> str | None:
        return self.nx_graph.nodes[node].get("location")


def build_topology_graph(building_id: str, config_type: str, graph: rdflib.Graph) -> TopologyGraph:
    nx_graph = nx.MultiDiGraph()
    edges_by_relation: dict[str, set[tuple[str, str]]] = {rel: set() for rel in ("feeds", "hasPoint", "hasPart")}

    node_types: dict[str, set[str]] = {}
    node_locations: dict[str, str] = {}

    for s, p, o in graph:
        if p == RDF_TYPE and str(o).startswith(BRICK_NS):
            node_types.setdefault(str(s), set()).add(_local(o))

    for s, p, o in graph:
        if str(p) == BRICK_NS + "hasLocation" and isinstance(o, rdflib.URIRef):
            node_locations[str(s)] = str(o)

    for node in set(node_types) | set(node_locations):
        nx_graph.add_node(node)

    for s, p, o in graph:
        pred_name = _local(p)
        if pred_name in ("feeds", "hasPoint", "hasPart") and isinstance(s, rdflib.URIRef) and isinstance(
            o, rdflib.URIRef
        ):
            nx_graph.add_node(str(s))
            nx_graph.add_node(str(o))
            nx_graph.add_edge(str(s), str(o), relation=pred_name)
            edges_by_relation[pred_name].add((str(s), str(o)))

    for node in nx_graph.nodes():
        types = sorted(node_types.get(node, set()))
        nx_graph.nodes[node]["brick_type"] = types[0] if types else None
        nx_graph.nodes[node]["brick_types"] = types
        nx_graph.nodes[node]["location"] = node_locations.get(node)

    return TopologyGraph(
        building_id=building_id,
        config_type=config_type,
        nx_graph=nx_graph,
        edges_by_relation=edges_by_relation,
    )
