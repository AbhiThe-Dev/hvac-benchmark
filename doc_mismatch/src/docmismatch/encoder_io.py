"""Bridge between documented graphs and the existing pretrained encoder
(`results/pretrain/encoder`, `hvac_benchmark.pretrain`). The encoder sees only
the documented topology (Brick class tokens + feeds/hasPart/hasPoint edges); it
never sees the physical evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import networkx as nx
import numpy as np
import torch

from hvac_benchmark.data.cache import FileCache
from hvac_benchmark.data.ontology import BrickOntology
from hvac_benchmark.graph.networkx_build import TopologyGraph
from hvac_benchmark.pretrain.data import RELATIONS, GraphExample, example_from_topology
from hvac_benchmark.pretrain.model import ConnectionModel, ModelConfig, load_pretrained

from .data import SLOTS, Base
from .features import case_doc
from .rules import Doc

REPO = Path(__file__).resolve().parents[3]


class EncoderKit:
    def __init__(self, encoder_dir: Path = REPO / "results" / "pretrain" / "encoder", cache_dir: Path = REPO / "data_cache"):
        self.ontology = BrickOntology.load(FileCache(cache_dir))
        self.pretrained = load_pretrained(encoder_dir)
        for p in self.pretrained.parameters():
            p.requires_grad_(False)
        self.vocab = self.pretrained.vocab
        self.dim = self.pretrained.config.dim

    def fresh(self, seed: int) -> ConnectionModel:
        """Same architecture/vocab, random init (no pretraining)."""
        torch.manual_seed(seed)
        c = self.pretrained.config
        return ConnectionModel(ModelConfig(c.dim, c.n_layers, c.dropout, c.n_tokens), self.vocab)

    def pretrained_copy(self) -> ConnectionModel:
        import copy
        m = copy.deepcopy(self.pretrained)
        for p in m.parameters():
            p.requires_grad_(True)
        return m

    def example(self, base: Base, doc: Doc, name: str) -> GraphExample:
        g = nx.MultiDiGraph()
        for nid, n in base.nodes.items():
            if n["kind"] == "Weather":
                continue
            g.add_node(nid, brick_type=n["brick_type"], brick_types=[n["brick_type"]], location=None)
        rel: dict[str, set] = {r: set() for r in RELATIONS}
        for slot, edges in doc.items():
            s = SLOTS[slot]
            for o, m in edges:
                src, dst = (o, m) if s["owner_first"] else (m, o)
                g.add_edge(src, dst, relation=s["rel"])
                rel[s["rel"]].add((src, dst))
        tg = TopologyGraph(name, "synthetic", g, rel)
        return example_from_topology(tg, self.ontology, self.vocab)


def row_indices(ex: GraphExample, rows: list[dict]) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """src, dst, relation index and validity mask for each feature row."""
    pos = {n: i for i, n in enumerate(ex.node_ids)}
    src = np.zeros(len(rows), dtype=np.int64)
    dst = np.zeros(len(rows), dtype=np.int64)
    rel = np.zeros(len(rows), dtype=np.int64)
    ok = np.zeros(len(rows), dtype=bool)
    for i, r in enumerate(rows):
        if r["owner"] is None:
            continue
        s = SLOTS[r["slot"]]
        a, b = (r["owner"], r["member"]) if s["owner_first"] else (r["member"], r["owner"])
        src[i], dst[i], rel[i], ok[i] = pos[a], pos[b], RELATIONS.index(s["rel"]), True
    return torch.from_numpy(src), torch.from_numpy(dst), torch.from_numpy(rel), torch.from_numpy(ok)


def edge_z(model: ConnectionModel, h: torch.Tensor, src, dst, ok) -> torch.Tensor:
    z = ConnectionModel.edge_features(h, src, dst)
    return z * ok[:, None].float()


@torch.no_grad()
def frozen_features(model: ConnectionModel, ex: GraphExample, rows: list[dict]):
    model.eval()
    src, dst, rel, ok = row_indices(ex, rows)
    h = model.encode(ex)
    return edge_z(model, h, src, dst, ok).numpy()


@torch.no_grad()
def zero_shot_scores(model: ConnectionModel, ex: GraphExample, rows: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    """Pretrained decoder plausibility logit of each documented edge, (a) with the
    edge visible in the graph ("present": the audit setting) and (b) hidden while
    scoring it (the pretraining regime, "masked"). Orphan rows get +inf-plausible (no anomaly)."""
    model.eval()
    src, dst, rel, ok = row_indices(ex, rows)
    h = model.encode(ex)
    present = np.full(len(rows), np.nan)
    masked = np.full(len(rows), np.nan)
    for i, r in enumerate(rows):
        if not ok[i]:
            continue
        ri = int(rel[i])
        present[i] = model.score(h, src[i : i + 1], dst[i : i + 1], ri).item()
        e = ex.edges[RELATIONS[ri]]
        keep = np.ones(len(e), dtype=bool)
        keep[(e[:, 0] == int(src[i])) & (e[:, 1] == int(dst[i]))] = False
        hm = model.encode(ex, {RELATIONS[ri]: keep})
        masked[i] = model.score(hm, src[i : i + 1], dst[i : i + 1], ri).item()
    return present, masked
