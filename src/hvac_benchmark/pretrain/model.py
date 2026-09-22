"""Relational GNN encoder + per-relation bilinear edge decoder.

The encoder is the reusable artifact: `ConnectionModel.encode(example)` gives
one embedding per node, computed from Brick class hierarchy features, degree
statistics, and typed-neighbourhood message passing. The decoder scores a
candidate edge `(source, relation, target)`; fine-tuning can reuse it as-is,
re-initialise it, or build a classifier on `edge_features`.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import torch
from torch import nn

from .data import RELATIONS, GraphExample, TypeVocab

N_DIRECTIONS = 2 * len(RELATIONS)  # each relation as forward and reverse messages


@dataclass(frozen=True)
class ModelConfig:
    dim: int = 64
    n_layers: int = 2
    dropout: float = 0.1
    n_tokens: int = 0  # filled from the vocab


@dataclass
class MPGraph:
    """Message-passing structure for one (possibly edge-masked) building."""

    n: int
    src: list[torch.Tensor]
    dst: list[torch.Tensor]
    inv_deg: list[torch.Tensor]  # (N, 1) per direction
    deg_feat: torch.Tensor  # (N, N_DIRECTIONS) log1p degree per direction


def build_mp_graph(example: GraphExample, keep: dict[str, np.ndarray] | None = None) -> MPGraph:
    """`keep[rel]` is a boolean mask over `example.edges[rel]`; masked-out
    edges are invisible to message passing *and* to the degree features, so a
    held-out edge cannot leak into its own prediction."""
    n = example.n_nodes
    src, dst, inv_deg, deg = [], [], [], []
    for rel in RELATIONS:
        e = example.edges[rel]
        if keep is not None and rel in keep:
            e = e[keep[rel]]
        for s, t in ((e[:, 0], e[:, 1]), (e[:, 1], e[:, 0])):  # forward, reverse
            d = np.bincount(t, minlength=n).astype(np.float32)
            src.append(torch.from_numpy(s.astype(np.int64)))
            dst.append(torch.from_numpy(t.astype(np.int64)))
            inv_deg.append(torch.from_numpy(1.0 / np.maximum(d, 1.0))[:, None])
            deg.append(np.log1p(d))
    return MPGraph(n, src, dst, inv_deg, torch.from_numpy(np.stack(deg, axis=1)))


class RGCNLayer(nn.Module):
    def __init__(self, dim: int, dropout: float):
        super().__init__()
        self.self_lin = nn.Linear(dim, dim)
        self.rel_lin = nn.ModuleList([nn.Linear(dim, dim, bias=False) for _ in range(N_DIRECTIONS)])
        self.norm = nn.LayerNorm(dim)
        self.drop = nn.Dropout(dropout)

    def forward(self, h: torch.Tensor, g: MPGraph) -> torch.Tensor:
        out = self.self_lin(h)
        for d, lin in enumerate(self.rel_lin):
            if len(g.src[d]) == 0:
                continue
            agg = torch.zeros_like(h).index_add_(0, g.dst[d], lin(h)[g.src[d]])
            out = out + agg * g.inv_deg[d]
        return h + self.drop(torch.relu(self.norm(out)))


class ConnectionModel(nn.Module):
    def __init__(self, config: ModelConfig, vocab: TypeVocab):
        super().__init__()
        self.config = ModelConfig(config.dim, config.n_layers, config.dropout, len(vocab.tokens))
        self.vocab = vocab
        d = config.dim
        self.type_emb = nn.Embedding(len(vocab.tokens) + 1, d, padding_idx=vocab.pad_index)
        self.deg_proj = nn.Linear(N_DIRECTIONS, d)
        self.layers = nn.ModuleList([RGCNLayer(d, config.dropout) for _ in range(config.n_layers)])
        self.rel_bilinear = nn.Parameter(torch.eye(d).repeat(len(RELATIONS), 1, 1) + 0.01 * torch.randn(len(RELATIONS), d, d))

    def encode(
        self,
        example: GraphExample,
        keep: dict[str, np.ndarray] | None = None,
        leaf_dropout: float = 0.0,
        rng: np.random.Generator | None = None,
    ) -> torch.Tensor:
        """Node embeddings (N, dim). `keep` hides edges (see `build_mp_graph`);
        `leaf_dropout` randomly hides a node's own class tokens, leaving its
        ancestors, so the model learns to rely on the class hierarchy."""
        tokens = example.type_tokens.copy()
        if leaf_dropout > 0.0:
            assert rng is not None
            drop = (rng.random((example.n_nodes, 1)) < leaf_dropout) & example.is_leaf
            # only drop when the node keeps at least one ancestor token
            has_anc = (~example.is_leaf & (tokens != self.vocab.pad_index)).any(axis=1, keepdims=True)
            tokens[drop & has_anc] = self.vocab.pad_index
        g = build_mp_graph(example, keep)
        h = torch.relu(self.type_emb(torch.from_numpy(tokens)).sum(dim=1) + self.deg_proj(g.deg_feat))
        for layer in self.layers:
            h = layer(h, g)
        return h

    def score(self, h: torch.Tensor, src: torch.Tensor, dst: torch.Tensor, rel: int) -> torch.Tensor:
        """Plausibility logit for edges `src -> dst` of relation index `rel`."""
        return ((h[src] @ self.rel_bilinear[rel]) * h[dst]).sum(-1) / math.sqrt(self.config.dim)

    def score_all(self, h: torch.Tensor, anchors: torch.Tensor, rel: int, anchor_is_source: bool) -> torch.Tensor:
        """(P, N) logits of each anchor against every node as the other endpoint."""
        w = self.rel_bilinear[rel]
        if anchor_is_source:
            return (h[anchors] @ w) @ h.T / math.sqrt(self.config.dim)
        return ((h @ w) @ h[anchors].T).T / math.sqrt(self.config.dim)

    @staticmethod
    def edge_features(h: torch.Tensor, src: torch.Tensor, dst: torch.Tensor) -> torch.Tensor:
        """`[h_s, h_t, h_s*h_t, |h_s-h_t|]` for downstream edge classifiers."""
        a, b = h[src], h[dst]
        return torch.cat([a, b, a * b, (a - b).abs()], dim=-1)


def save_pretrained(model: ConnectionModel, out_dir: str | Path, metadata: dict | None = None) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out / "weights.pt")
    (out / "config.json").write_text(json.dumps(asdict(model.config), indent=2))
    (out / "vocab.json").write_text(json.dumps(list(model.vocab.tokens)))
    (out / "metadata.json").write_text(json.dumps(metadata or {}, indent=2, default=str))


def load_pretrained(in_dir: str | Path) -> ConnectionModel:
    d = Path(in_dir)
    vocab = TypeVocab(tuple(json.loads((d / "vocab.json").read_text())))
    model = ConnectionModel(ModelConfig(**json.loads((d / "config.json").read_text())), vocab)
    model.load_state_dict(torch.load(d / "weights.pt", map_location="cpu", weights_only=True))
    model.eval()
    return model
