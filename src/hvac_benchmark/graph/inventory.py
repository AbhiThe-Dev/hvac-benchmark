"""Per-graph inventory and duplicate-topology detection.

Every usable graph is inventoried (node types, relation counts, unknown
classes) before it enters any experiment, and topologies whose structure is
a duplicate of one already counted are flagged so repeated fault scenarios
or re-exported copies of the same model never inflate the count of
independent buildings.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import networkx as nx

from .networkx_build import TopologyGraph
from .rdf_parse import ParseReport


@dataclass
class TopologyInventory:
    building_id: str
    config_type: str
    n_nodes: int
    node_type_counts: dict[str, int]
    relation_counts: dict[str, int]
    unknown_classes: set[str]
    class_aliases_applied: dict[str, str]
    structural_hash: str
    is_duplicate_of: str | None = None


def _structural_hash(tg: TopologyGraph) -> str:
    """A relation-typed Weisfeiler-Lehman hash over (node type, edges by
    relation), insensitive to node naming, so re-exports or copies of the
    same model under different labels are still caught."""
    g = nx.MultiDiGraph()
    for n in tg.nx_graph.nodes():
        g.add_node(n, label=tg.node_type(n) or "?")
    for u, v, data in tg.nx_graph.edges(data=True):
        g.add_edge(u, v, label=data.get("relation", "?"))
    simple = nx.DiGraph()
    for n, data in g.nodes(data=True):
        simple.add_node(n, label=data["label"])
    edge_labels = {}
    for u, v, data in g.edges(data=True):
        key = (u, v)
        edge_labels.setdefault(key, set()).add(data["label"])
        simple.add_edge(u, v)
    for (u, v), labels in edge_labels.items():
        simple.edges[u, v]["label"] = "|".join(sorted(labels))
    return nx.weisfeiler_lehman_graph_hash(simple, edge_attr="label", node_attr="label")


def inventory_topology(
    tg: TopologyGraph, parse_reports: dict[str, ParseReport]
) -> TopologyInventory:
    node_type_counts: dict[str, int] = {}
    for n in tg.nodes():
        t = tg.node_type(n) or "UNTYPED"
        node_type_counts[t] = node_type_counts.get(t, 0) + 1

    relation_counts = {rel: len(edges) for rel, edges in tg.edges_by_relation.items()}

    unknown_classes: set[str] = set()
    aliases: dict[str, str] = {}
    for report in parse_reports.values():
        unknown_classes |= report.unknown_classes
        aliases.update(report.class_aliases_applied)

    return TopologyInventory(
        building_id=tg.building_id,
        config_type=tg.config_type,
        n_nodes=tg.nx_graph.number_of_nodes(),
        node_type_counts=node_type_counts,
        relation_counts=relation_counts,
        unknown_classes=unknown_classes,
        class_aliases_applied=aliases,
        structural_hash=_structural_hash(tg),
    )


def flag_duplicates(inventories: list[TopologyInventory]) -> list[TopologyInventory]:
    """Mark topologies whose structural hash matches an earlier one in the
    list as duplicates (kept for inventory reporting, excluded from
    independent-building counts downstream)."""
    seen: dict[str, str] = {}
    for inv in inventories:
        if inv.structural_hash in seen:
            inv.is_duplicate_of = seen[inv.structural_hash]
        else:
            seen[inv.structural_hash] = inv.building_id
    return inventories
