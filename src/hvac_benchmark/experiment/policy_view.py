"""The policy-visible inventory: opaque identifiers, Brick types, and
independently-available location metadata only.

Policies never see real entity names (which can encode the very connections
being tested, e.g. `VAV_Box_202` / `Terminal_Room_202`), true node degree,
target relationships, or any truth-derived ordering. The mapping back to
real node identity is kept by the evaluation harness only and is never
passed to a policy's `select_next` call.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .candidates import Candidate
from ..graph.networkx_build import TopologyGraph


@dataclass(frozen=True)
class OpaqueNode:
    opaque_id: str
    brick_type: str | None
    location_opaque: str | None


@dataclass(frozen=True)
class OpaqueCandidate:
    index: int
    source: str
    target: str
    relation: str


@dataclass
class PolicyView:
    nodes: dict[str, OpaqueNode]
    candidates: tuple[OpaqueCandidate, ...]
    real_to_opaque: dict[str, str]
    opaque_to_real: dict[str, str]


def build_policy_view(tg: TopologyGraph, candidates: list[Candidate], seed: int) -> PolicyView:
    rng = np.random.RandomState(seed)

    node_set = sorted({c.source for c in candidates} | {c.target for c in candidates})
    order = rng.permutation(len(node_set))
    shuffled_nodes = [node_set[i] for i in order]

    real_to_opaque: dict[str, str] = {}
    for i, real in enumerate(shuffled_nodes):
        real_to_opaque[real] = f"N{i:04d}"
    opaque_to_real = {v: k for k, v in real_to_opaque.items()}

    locations = sorted({tg.node_location(n) for n in node_set if tg.node_location(n) is not None})
    loc_order = rng.permutation(len(locations))
    location_map = {locations[i]: f"L{j:03d}" for j, i in enumerate(loc_order)}

    nodes: dict[str, OpaqueNode] = {}
    for real in shuffled_nodes:
        opaque_id = real_to_opaque[real]
        loc = tg.node_location(real)
        nodes[opaque_id] = OpaqueNode(
            opaque_id=opaque_id,
            brick_type=tg.node_type(real),
            location_opaque=location_map.get(loc) if loc is not None else None,
        )

    cand_order = rng.permutation(len(candidates))
    opaque_candidates = tuple(
        OpaqueCandidate(
            index=i,
            source=real_to_opaque[candidates[orig_idx].source],
            target=real_to_opaque[candidates[orig_idx].target],
            relation=candidates[orig_idx].relation,
        )
        for i, orig_idx in enumerate(cand_order)
    )

    return PolicyView(
        nodes=nodes,
        candidates=opaque_candidates,
        real_to_opaque=real_to_opaque,
        opaque_to_real=opaque_to_real,
    )
