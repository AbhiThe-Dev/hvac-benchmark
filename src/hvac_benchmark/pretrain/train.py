"""Masked-edge pretraining: hide a fraction of each building's feeds/hasPart/
hasPoint edges, encode what is left, and train the model to rank each hidden
true edge above corrupted ones (a sampled-softmax link-prediction loss).

Negatives replace one endpoint of the hidden edge. Half are "hard" (a node of
the same Brick class as the true endpoint -- right type, wrong place) and
half "easy" (any node of the same category: equipment / location / point).
Real edges are never used as negatives. No fault labels are involved.
"""

from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass, field

import numpy as np
import torch
import torch.nn.functional as F

from .data import RELATIONS, GraphExample, NodePools, TypeVocab
from .model import ConnectionModel, ModelConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TrainConfig:
    epochs: int = 40
    lr: float = 3e-3
    weight_decay: float = 1e-5
    mask_frac: float = 0.2
    n_neg: int = 16
    hard_frac: float = 0.5
    leaf_dropout: float = 0.2
    # hasPoint is abundant but is not equipment-to-equipment plausibility.
    relation_weights: tuple[tuple[str, float], ...] = (("feeds", 1.0), ("hasPart", 1.0), ("hasPoint", 0.3))
    seed: int = 0
    # Multithreaded CPU reductions are not bit-reproducible; these models are
    # small enough that one thread costs little.
    deterministic: bool = True


def make_holdout(example: GraphExample, frac: float, rng: np.random.Generator) -> dict[str, np.ndarray]:
    """Boolean keep-masks (False = held out). Relations with a single edge are
    left intact: hiding their only edge would leave nothing to condition on."""
    keep = {}
    for rel in RELATIONS:
        n = len(example.edges[rel])
        mask = np.ones(n, dtype=bool)
        if n >= 2:
            mask[rng.permutation(n)[: max(1, round(frac * n))]] = False
        keep[rel] = mask
    return keep


def _building_loss(
    model: ConnectionModel, ex: GraphExample, cfg: TrainConfig, rng: np.random.Generator
) -> torch.Tensor | None:
    keep = make_holdout(ex, cfg.mask_frac, rng)
    if all(m.all() for m in keep.values()):
        return None
    h = model.encode(ex, keep, cfg.leaf_dropout, rng)
    hard, easy = NodePools(ex.primary), NodePools(ex.category)
    n_hard = int(round(cfg.n_neg * cfg.hard_frac))
    weights = dict(cfg.relation_weights)
    n = ex.n_nodes
    total, denom = None, 0.0
    for r, rel in enumerate(RELATIONS):
        held = ex.edges[rel][~keep[rel]]
        if len(held) == 0:
            continue
        s, t = held[:, 0], held[:, 1]
        corrupt_tail = rng.random(len(held)) < 0.5
        anchor, replaced = np.where(corrupt_tail, s, t), np.where(corrupt_tail, t, s)
        neg = np.concatenate(
            [hard.sample(replaced, n_hard, rng), easy.sample(replaced, cfg.n_neg - n_hard, rng)], axis=1
        )
        all_keys = ex.edges[rel][:, 0] * n + ex.edges[rel][:, 1]
        neg_keys = np.where(corrupt_tail[:, None], anchor[:, None] * n + neg, neg * n + anchor[:, None])
        invalid = (neg == replaced[:, None]) | np.isin(neg_keys, all_keys)
        neg_src = np.where(corrupt_tail[:, None], s[:, None], neg)
        neg_dst = np.where(corrupt_tail[:, None], neg, t[:, None])

        pos_logit = model.score(h, torch.from_numpy(s), torch.from_numpy(t), r)
        neg_logit = model.score(h, torch.from_numpy(neg_src.ravel()), torch.from_numpy(neg_dst.ravel()), r)
        logits = torch.cat([pos_logit[:, None], neg_logit.view(len(held), -1)], dim=1)
        logits = logits.masked_fill(torch.cat([torch.zeros(len(held), 1, dtype=torch.bool), torch.from_numpy(invalid)], 1), -1e9)
        loss = F.cross_entropy(logits, torch.zeros(len(held), dtype=torch.long))
        w = weights.get(rel, 1.0)
        total = w * loss if total is None else total + w * loss
        denom += w
    return None if total is None else total / denom


def train(
    examples: list[GraphExample],
    vocab: TypeVocab,
    model_config: ModelConfig = ModelConfig(),
    cfg: TrainConfig = TrainConfig(),
    log_every: int = 10,
) -> tuple[ConnectionModel, list[float]]:
    prev_threads = torch.get_num_threads()
    if cfg.deterministic:
        torch.set_num_threads(1)
    try:
        return _train(examples, vocab, model_config, cfg, log_every)
    finally:
        torch.set_num_threads(prev_threads)


def _train(examples, vocab, model_config, cfg, log_every):
    torch.manual_seed(cfg.seed)
    rng = np.random.default_rng(cfg.seed)
    model = ConnectionModel(model_config, vocab)
    opt = torch.optim.Adam(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    history: list[float] = []
    start = time.time()
    for epoch in range(cfg.epochs):
        model.train()
        losses = []
        for i in rng.permutation(len(examples)):
            loss = _building_loss(model, examples[i], cfg, rng)
            if loss is None:
                continue
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step()
            losses.append(loss.item())
        history.append(float(np.mean(losses)))
        if (epoch + 1) % log_every == 0 or epoch == 0:
            logger.info("epoch %d/%d loss %.4f (%.0fs)", epoch + 1, cfg.epochs, history[-1], time.time() - start)
    model.eval()
    return model, history


def train_config_dict(cfg: TrainConfig) -> dict:
    return asdict(cfg)
