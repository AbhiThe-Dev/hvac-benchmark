"""Seeded synthetic AHU-VAV-zone graphs.

These are supplementary sanity checks only, never counted as real
topologies (see `config_type == "synthetic"` throughout the pipeline and
`results.md`'s explicit separate count).
"""

from __future__ import annotations

import networkx as nx
import numpy as np

from .networkx_build import TopologyGraph

N_SYNTHETIC_DEFAULT = 10
MIN_VAVS, MAX_VAVS = 3, 9
MIN_POINTS, MAX_POINTS = 1, 3


def make_synthetic_graph(seed: int) -> TopologyGraph:
    rng = np.random.RandomState(seed)
    building_id = f"synthetic_{seed:02d}"
    n_vavs = int(rng.randint(MIN_VAVS, MAX_VAVS + 1))

    nx_graph = nx.MultiDiGraph()
    edges_by_relation: dict[str, set[tuple[str, str]]] = {"feeds": set(), "hasPoint": set(), "hasPart": set()}

    ahu = f"{building_id}/AHU_1"
    nx_graph.add_node(ahu, brick_type="AHU", brick_types=["AHU"], location=None)

    point_counter = 0

    def add_points(entity: str, prefix: str):
        nonlocal point_counter
        n_points = int(rng.randint(MIN_POINTS, MAX_POINTS + 1))
        for _ in range(n_points):
            point_counter += 1
            point = f"{building_id}/{prefix}_Point_{point_counter}"
            nx_graph.add_node(point, brick_type="Point", brick_types=["Point"], location=None)
            nx_graph.add_edge(entity, point, relation="hasPoint")
            edges_by_relation["hasPoint"].add((entity, point))

    add_points(ahu, "AHU")

    for i in range(1, n_vavs + 1):
        vav = f"{building_id}/VAV_{i}"
        zone = f"{building_id}/Zone_{i}"
        nx_graph.add_node(vav, brick_type="VAV", brick_types=["VAV"], location=None)
        nx_graph.add_node(zone, brick_type="HVAC_Zone", brick_types=["HVAC_Zone"], location=None)

        nx_graph.add_edge(ahu, vav, relation="feeds")
        edges_by_relation["feeds"].add((ahu, vav))
        nx_graph.add_edge(vav, zone, relation="feeds")
        edges_by_relation["feeds"].add((vav, zone))
        nx_graph.add_edge(ahu, vav, relation="hasPart")
        edges_by_relation["hasPart"].add((ahu, vav))

        add_points(vav, f"VAV{i}")
        add_points(zone, f"Zone{i}")

    return TopologyGraph(
        building_id=building_id,
        config_type="synthetic",
        nx_graph=nx_graph,
        edges_by_relation=edges_by_relation,
    )


def make_all_synthetic_graphs(n: int = N_SYNTHETIC_DEFAULT) -> list[TopologyGraph]:
    return [make_synthetic_graph(seed) for seed in range(n)]
