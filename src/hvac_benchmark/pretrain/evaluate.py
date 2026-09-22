"""Held-out-building evaluation of connection plausibility.

For every held-out building, a fraction of each relation's true edges is
hidden (from message passing too), then each hidden edge is ranked against
all *other* nodes of the same category (equipment / location / point) that
are not already a known true neighbour (filtered ranking), replacing either
endpoint. Ties are scored by their exact expectation under random
tie-breaking, so a scorer that cannot tell candidates apart is credited
exactly chance -- never an optimistic tie-break.

Two variants:
- `all`: candidates are every same-category node (type + structure signal).
- `within_type`: candidates are only nodes sharing the true endpoint's Brick
  class. A type-only scorer is at chance here by construction, so this
  isolates what the graph structure adds beyond class compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from .data import RELATIONS, GraphExample, TypeVocab
from .model import ConnectionModel
from .train import make_holdout

_HARMONIC = np.concatenate([[0.0], np.cumsum(1.0 / np.arange(1, 200_001))])


class RandomScorer:
    name = "random"

    def prepare(self, ex, keep):
        return None

    def scores(self, ctx, ex, anchors, r, anchor_is_source):
        return np.zeros((len(anchors), ex.n_nodes))


class TypePriorScorer:
    """Frequency of (source class, target class, relation) in the training
    buildings -- the type-compatibility signal alone, blind to structure."""

    name = "type_prior"

    def __init__(self, train_examples: list[GraphExample], vocab: TypeVocab, alpha: float = 1e-3):
        v = len(vocab.tokens)
        self.counts = np.zeros((len(RELATIONS), v, v))
        for ex in train_examples:
            for r, rel in enumerate(RELATIONS):
                e = ex.edges[rel]
                np.add.at(self.counts[r], (ex.primary[e[:, 0]], ex.primary[e[:, 1]]), 1.0)
        self.alpha = alpha

    def prepare(self, ex, keep):
        return None

    def scores(self, ctx, ex, anchors, r, anchor_is_source):
        c = self.counts[r]
        rows = c[ex.primary[anchors]][:, ex.primary] if anchor_is_source else c[:, ex.primary[anchors]][ex.primary].T
        return np.log(rows + self.alpha)


class GNNScorer:
    name = "gnn"

    def __init__(self, model: ConnectionModel):
        self.model = model.eval()

    def prepare(self, ex, keep):
        with torch.no_grad():
            return self.model.encode(ex, keep)

    def scores(self, h, ex, anchors, r, anchor_is_source):
        with torch.no_grad():
            return self.model.score_all(h, torch.from_numpy(anchors), r, anchor_is_source).numpy()


@dataclass
class _Acc:
    mrr: list
    hits1: list
    hits3: list


def _expected_metrics(greater: np.ndarray, equal: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Exact E[1/rank], E[rank<=1], E[rank<=3] under uniform random
    tie-breaking among `equal` tied competitors."""
    g, e = greater.astype(int), equal.astype(int)
    mrr = (_HARMONIC[g + e + 1] - _HARMONIC[g]) / (e + 1)
    hit = lambda k: np.clip((k - g) / (e + 1), 0.0, 1.0)
    return mrr, hit(1), hit(3)


def _rank_side(S, ex, anchors, truth, all_keys, anchor_is_source):
    n = ex.n_nodes
    ar = np.arange(n)[None, :]
    keys = anchors[:, None] * n + ar if anchor_is_source else ar * n + anchors[:, None]
    known = np.isin(keys, all_keys)
    is_truth = ar == truth[:, None]
    cand = (ex.category[None, :] == ex.category[truth][:, None]) & ~known & ~is_truth
    st = S[np.arange(len(truth)), truth][:, None]
    out = {}
    for variant, mask in (("all", cand), ("within_type", cand & (ex.primary[None, :] == ex.primary[truth][:, None]))):
        ok = mask.any(axis=1)  # no competitor -> rank is trivially 1; not informative
        greater = ((S > st) & mask).sum(1)[ok]
        equal = ((S == st) & mask).sum(1)[ok]
        out[variant] = _expected_metrics(greater, equal)
    return out


def evaluate(
    scorer, examples: list[GraphExample], seed: int = 0, mask_frac: float = 0.2
) -> dict[str, dict[str, dict[str, float]]]:
    """{relation: {variant: {mrr, hits@1, hits@3, n, mrr_macro}}}"""
    per_edge: dict = {rel: {v: [] for v in ("all", "within_type")} for rel in RELATIONS}
    per_building: dict = {rel: {v: [] for v in ("all", "within_type")} for rel in RELATIONS}
    for i, ex in enumerate(examples):
        keep = make_holdout(ex, mask_frac, np.random.default_rng(seed * 100_003 + i))
        ctx = scorer.prepare(ex, keep)
        for r, rel in enumerate(RELATIONS):
            held = ex.edges[rel][~keep[rel]]
            if len(held) == 0:
                continue
            all_keys = ex.edges[rel][:, 0] * ex.n_nodes + ex.edges[rel][:, 1]
            s, t = held[:, 0], held[:, 1]
            acc: dict = {v: [] for v in ("all", "within_type")}
            for anchors, truth, anchor_is_source in ((s, t, True), (t, s, False)):
                S = scorer.scores(ctx, ex, anchors, r, anchor_is_source)
                for v, m in _rank_side(S, ex, anchors, truth, all_keys, anchor_is_source).items():
                    acc[v].append(np.stack(m, axis=1))
            for v in acc:
                rows = np.concatenate(acc[v])
                if len(rows):
                    per_edge[rel][v].append(rows)
                    per_building[rel][v].append(rows[:, 0].mean())
    result: dict = {}
    for rel in RELATIONS:
        result[rel] = {}
        for v in ("all", "within_type"):
            rows = np.concatenate(per_edge[rel][v]) if per_edge[rel][v] else np.zeros((0, 3))
            result[rel][v] = {
                "mrr": float(rows[:, 0].mean()) if len(rows) else float("nan"),
                "hits@1": float(rows[:, 1].mean()) if len(rows) else float("nan"),
                "hits@3": float(rows[:, 2].mean()) if len(rows) else float("nan"),
                "n": int(len(rows)),
                "mrr_macro": float(np.mean(per_building[rel][v])) if per_building[rel][v] else float("nan"),
            }
    return result
