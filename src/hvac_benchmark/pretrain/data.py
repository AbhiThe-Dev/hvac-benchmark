"""Corpus selection and featurization for connection-plausibility pretraining.

Turns the merged Brick topologies (see `graph.building_grouping`) into
`GraphExample`s: integer arrays only, no torch, no RDF objects, so the same
featurization can be applied to any `TopologyGraph` later (e.g. the
fine-tuning project's documented-vs-actual wiring graphs).

Design choices that matter for transfer:

- Node features are a multi-hot over the *full Brick class hierarchy*
  (a node's own classes plus every `rdfs:subClassOf`/`equivalentClass`
  ancestor from the reference ontology). A subclass never seen in the
  pretraining corpus still lands on its trained ancestors.
- `rec:` classes (Room, HVACZone, Floor, Building) are read straight from the
  RDF because `build_topology_graph` keeps only Brick-namespace types; they
  are given the `Location` ancestor so they behave like Brick locations.
- Node URIs/names are never used: naming is arbitrary per building and would
  not transfer.
"""

from __future__ import annotations

import logging
import os
import warnings
from dataclasses import dataclass, field

import networkx as nx
import numpy as np
import rdflib

from ..data.cache import FileCache
from ..data.ontology import BrickOntology
from ..graph.building_grouping import MORTAR_CORPUS_GROUPS, REAL_CORPUS_GROUPS, BuildingGroup, merge_all
from ..graph.networkx_build import TopologyGraph, build_topology_graph

logger = logging.getLogger(__name__)

RELATIONS = ("feeds", "hasPart", "hasPoint")
CATEGORIES = ("Equipment", "Location", "Point", "Other")
EQUIPMENT, LOCATION, POINT, OTHER = range(4)

REC_NS = "https://w3id.org/rec#"
UNTYPED = "<untyped>"
DEFAULT_REC_CLASSES = ("Building", "Floor", "Room", "HVACZone", "Zone", "Space", "Wing", "Level", "Campus", "Site")

# Only `config_type == "experimental"` groups are real systems (all MORTAR
# buildings plus the ORNL FRP `rtu_exp`); every other LBNL file is a simulation
# model -- see the provenance table in `graph.building_grouping`.
REAL_CONFIG_TYPE = "experimental"


def is_real(example: "GraphExample") -> bool:
    return example.config_type == REAL_CONFIG_TYPE


@dataclass(frozen=True)
class TypeVocab:
    """Fixed token list: every Brick class, selected `rec:` classes, and an
    untyped fallback. Saved with checkpoints so featurization is reproducible
    without the training corpus."""

    tokens: tuple[str, ...]

    @classmethod
    def build(
        cls,
        ontology: BrickOntology,
        rec_classes: tuple[str, ...] = DEFAULT_REC_CLASSES,
        extra_brick_classes: frozenset[str] = frozenset(),
    ) -> "TypeVocab":
        brick = sorted(ontology.known_classes() | extra_brick_classes)
        return cls(tuple(brick) + tuple(f"rec:{c}" for c in rec_classes) + (UNTYPED,))

    @property
    def index(self) -> dict[str, int]:
        return {t: i for i, t in enumerate(self.tokens)}

    @property
    def pad_index(self) -> int:
        return len(self.tokens)


@dataclass
class GraphExample:
    building_id: str
    config_type: str
    node_ids: list[str]
    type_tokens: np.ndarray  # (N, K) vocab indices, padded with vocab.pad_index
    is_leaf: np.ndarray  # (N, K) True where the token is one of the node's own classes
    primary: np.ndarray  # (N,) vocab index of the node's primary class (baselines, hard negatives)
    category: np.ndarray  # (N,) index into CATEGORIES
    edges: dict[str, np.ndarray] = field(default_factory=dict)  # relation -> (E, 2) node indices

    @property
    def n_nodes(self) -> int:
        return len(self.node_ids)


def rec_types(graph: rdflib.Graph) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for s, o in graph.subject_objects(rdflib.RDF.type):
        if str(o).startswith(REC_NS):
            out.setdefault(str(s), set()).add("rec:" + str(o)[len(REC_NS):])
    return out


# Some corpus files (notably MORTAR) use Brick classes newer than the pinned
# v1.3.0 reference ontology (e.g. `Target_Zone_Air_Temperature_Setpoint`), so
# the ontology has no ancestors for them. Brick's own naming convention ends
# a point class with its point kind, so for *unknown classes only* the suffix
# gives a coarse ancestor. Heuristic; known classes always use the ontology.
POINT_KIND_SUFFIXES = ("Setpoint", "Sensor", "Command", "Status", "Parameter", "Alarm", "Limit")


def ancestor_names(ontology: BrickOntology, cls_name: str) -> set[str]:
    if cls_name in ontology.known_classes():
        return set(ontology.ancestors(cls_name))
    anc = {cls_name}
    for suffix in POINT_KIND_SUFFIXES:
        if cls_name.endswith("_" + suffix):
            anc |= {suffix, "Point"}
    return anc


def example_from_topology(
    tg: TopologyGraph,
    ontology: BrickOntology,
    vocab: TypeVocab,
    rdf_graph: rdflib.Graph | None = None,
) -> GraphExample:
    """Featurize any `TopologyGraph`. Pass the merged RDF graph when available
    so `rec:` node classes are recovered."""
    index = vocab.index
    recs = rec_types(rdf_graph) if rdf_graph is not None else {}
    node_ids = sorted(tg.nodes())  # canonical order: set iteration is hash-seed dependent
    node_pos = {n: i for i, n in enumerate(node_ids)}

    rows_all: list[list[int]] = []
    rows_leaf: list[set[int]] = []
    primary = np.zeros(len(node_ids), dtype=np.int64)
    category = np.full(len(node_ids), OTHER, dtype=np.int64)
    for i, node in enumerate(node_ids):
        brick = list(tg.nx_graph.nodes[node].get("brick_types") or [])
        rec = sorted(recs.get(node, ()))
        own = {index[t] for t in brick + rec if t in index}
        anc_names: set[str] = set()
        for t in brick:
            anc_names |= ancestor_names(ontology, t)
        if rec:
            anc_names.add("Location")
        anc = {index[t] for t in anc_names if t in index} - own
        if not own and not anc:
            own = {index[UNTYPED]}
        rows_all.append(sorted(own) + sorted(anc))
        rows_leaf.append(own)
        first = (brick + rec)[0] if (brick or rec) else UNTYPED
        primary[i] = index.get(first, index[UNTYPED])
        if "Point" in anc_names:
            category[i] = POINT
        elif "Equipment" in anc_names:
            category[i] = EQUIPMENT
        elif "Location" in anc_names:
            category[i] = LOCATION

    k = max(len(r) for r in rows_all) if rows_all else 1
    tokens = np.full((len(node_ids), k), vocab.pad_index, dtype=np.int64)
    leaf = np.zeros((len(node_ids), k), dtype=bool)
    for i, row in enumerate(rows_all):
        tokens[i, : len(row)] = row
        leaf[i, : len(row)] = [t in rows_leaf[i] for t in row]

    edges: dict[str, np.ndarray] = {}
    for rel in RELATIONS:
        pairs = sorted((node_pos[s], node_pos[t]) for s, t in tg.edges_by_relation.get(rel, ()) if s != t)
        edges[rel] = np.array(pairs, dtype=np.int64).reshape(-1, 2)
    return GraphExample(tg.building_id, tg.config_type, node_ids, tokens, leaf, primary, category, edges)


def duplicate_groups(examples: list[GraphExample], vocab: TypeVocab) -> list[list[int]]:
    """Indices of examples with an identical typed structure (WL hash). The
    corpus has real duplicates (e.g. `mortar_bldg30` == `mortar_smc`,
    `pfpu` == `sfpu`); they must land on the same side of any split."""
    by_hash: dict[str, list[int]] = {}
    for idx, ex in enumerate(examples):
        g = nx.DiGraph()
        for i in range(ex.n_nodes):
            g.add_node(i, t=vocab.tokens[ex.primary[i]])
        for rel, e in ex.edges.items():
            for s, t in e:
                g.add_edge(int(s), int(t), r=rel)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            h = nx.weisfeiler_lehman_graph_hash(g, node_attr="t", edge_attr="r", iterations=3)
        by_hash.setdefault(h, []).append(idx)
    return list(by_hash.values())


def select_groups(
    groups: tuple[BuildingGroup, ...],
    include_simulated: bool = False,
    exclude_ids: frozenset[str] = frozenset(),
) -> list[BuildingGroup]:
    return [
        g
        for g in groups
        if (include_simulated or g.config_type == REAL_CONFIG_TYPE) and g.building_id not in exclude_ids
    ]


def _merged_topologies(cache: FileCache, ontology: BrickOntology, include_simulated: bool, exclude_ids):
    files = {
        fn: cache.get_bytes(fn)
        for fn in os.listdir(cache.cache_dir)
        if fn.endswith(".ttl") and not fn.startswith("brick_ontology")
    }
    groups = select_groups(REAL_CORPUS_GROUPS + MORTAR_CORPUS_GROUPS, include_simulated, exclude_ids)
    merged, excluded = merge_all(tuple(groups), files, ontology)
    for g in excluded:
        logger.warning("skipping %s: files missing from cache", g.building_id)
    return merged


def load_corpus(
    cache: FileCache,
    ontology: BrickOntology,
    include_simulated: bool = False,
    exclude_ids: frozenset[str] = frozenset(),
) -> tuple[list[GraphExample], TypeVocab]:
    """Real buildings (MORTAR + the ORNL FRP `rtu_exp`) from the on-disk cache
    (never the network). With `include_simulated`, the simulated LBNL models
    are returned too; callers separate them with `is_real`.
    The vocab is the ontology's classes plus any Brick classes the corpus uses
    that the ontology lacks. Buildings with no relation edges are dropped."""
    merged = _merged_topologies(cache, ontology, include_simulated, exclude_ids)
    unknown: set[str] = set()
    for m in merged:
        for r in m.parse_reports.values():
            unknown |= r.unknown_classes
    vocab = TypeVocab.build(ontology, extra_brick_classes=frozenset(unknown))
    examples = []
    for m in merged:
        tg = build_topology_graph(m.building_id, m.config_type, m.graph)
        ex = example_from_topology(tg, ontology, vocab, m.graph)
        if sum(len(e) for e in ex.edges.values()) == 0:
            logger.warning("skipping %s: no feeds/hasPart/hasPoint edges", ex.building_id)
            continue
        examples.append(ex)
    return examples, vocab


class NodePools:
    """Vectorized "random node sharing this key" sampler (key = primary type
    for hard negatives, category for easy ones)."""

    def __init__(self, keys: np.ndarray):
        self.keys = keys
        self.order = np.argsort(keys, kind="stable")
        uniq, starts, sizes = np.unique(keys[self.order], return_index=True, return_counts=True)
        self._start = dict(zip(uniq.tolist(), starts.tolist()))
        self._size = dict(zip(uniq.tolist(), sizes.tolist()))

    def sample(self, anchor_nodes: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
        k = self.keys[anchor_nodes]
        start = np.array([self._start[x] for x in k.tolist()], dtype=np.int64)
        size = np.array([self._size[x] for x in k.tolist()], dtype=np.int64)
        offs = (rng.random((len(anchor_nodes), n)) * size[:, None]).astype(np.int64)
        return self.order[start[:, None] + offs]
