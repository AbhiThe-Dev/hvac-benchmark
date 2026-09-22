"""Does the encoder spot a wrong-but-structurally-normal existing edge?

The pretraining task ranks a *missing* edge against corruptions; downstream
use is judging an edge that is *present* but possibly wrong. This module
measures the downstream-shaped skill directly on held-out real buildings:

For a true edge (s, t), pick s' (or t') sharing the true endpoint's Brick
class such that the swapped edge does not already exist, and form the graph
with the swap applied (G' = G - (s,t) + (s',t)). The scorer must prefer the
true edge over the wrong one. Two protocols:

- `present`: score both edges in G' (the wrong edge is visible to the
  encoder, as in a real documented-vs-actual audit; the true edge is absent,
  an input the encoder saw during pretraining).
- `masked`: hide the suspect edge and score both in G - (s,t); this is the
  pretraining regime, and equals within-class ranking.

Accuracy counts ties as 0.5. Baselines: a degree heuristic (prefer the
endpoint with more existing edges of that relation) and chance.
"""

from __future__ import annotations

import numpy as np
import torch

from .data import RELATIONS, GraphExample
from .model import ConnectionModel


def _without(ex: GraphExample, rel: str, edge: tuple[int, int]) -> dict[str, np.ndarray]:
    keep = {r: np.ones(len(ex.edges[r]), dtype=bool) for r in RELATIONS}
    e = ex.edges[rel]
    keep[rel][(e[:, 0] == edge[0]) & (e[:, 1] == edge[1])] = False
    return keep


def _with_swap(ex: GraphExample, rel: str, old: tuple[int, int], new: tuple[int, int]) -> GraphExample:
    e = ex.edges[rel]
    e = e[~((e[:, 0] == old[0]) & (e[:, 1] == old[1]))]
    edges = dict(ex.edges)
    edges[rel] = np.vstack([e, np.array([new], dtype=np.int64)])
    return GraphExample(ex.building_id, ex.config_type, ex.node_ids, ex.type_tokens, ex.is_leaf, ex.primary, ex.category, edges)


def swap_cases(
    ex: GraphExample, rel: str, side: str, max_cases: int, rng: np.random.Generator, degree_offset: int | None = None
):
    """Yield (true_edge, wrong_edge) with the wrong endpoint drawn from the
    true endpoint's Brick class and not already connected to the anchor.

    Any single-edge swap changes degrees: the true endpoint loses an edge and
    the wrong one gains one, so "prefer the lower-degree node" is a free
    signal that a real audit does not hand you (on the target side it is an
    "orphan" giveaway and always perfect). With `degree_offset`, only peers
    whose degree equals the true endpoint's degree minus the offset (so that
    the two candidates tie in the scored graph) are used, so degree carries no information. The offset depends on the
    protocol: 2 for `present` (true endpoint has d-1, wrong has d'+1 after the
    swap, so d' = d-2), 1 for `masked` (both edges hidden: d-1 vs d')."""
    e = ex.edges[rel]
    known = set(map(tuple, e.tolist()))
    col = 0 if side == "source" else 1
    deg = np.bincount(e[:, col], minlength=ex.n_nodes)
    out = []
    for i in rng.permutation(len(e)):
        s, t = map(int, e[i])
        moved = (s, t)[col]
        peers = np.flatnonzero(ex.primary == ex.primary[moved])
        peers = peers[peers != moved]
        if degree_offset is not None:
            peers = peers[deg[peers] == deg[moved] - degree_offset]
        rng.shuffle(peers)
        for p in peers:
            wrong = (int(p), t) if col == 0 else (s, int(p))
            if wrong not in known and wrong[0] != wrong[1]:
                out.append(((s, t), wrong))
                break
        if len(out) >= max_cases:
            break
    return out


def _degree(ex: GraphExample, rel: str, node: int, col: int, removed: tuple[int, int]) -> int:
    e = ex.edges[rel]
    return int(((e[:, col] == node)).sum()) - int(removed[col] == node)


def evaluate_swap_detection(
    model: ConnectionModel,
    examples: list[GraphExample],
    max_cases: int = 60,
    seed: int = 0,
    degree_offset: int | None = None,
) -> dict[str, float]:
    """{'<rel>/<side>/<protocol>': accuracy} plus 'degree' baseline and
    '/n' counts. `degree_offset` restricts to source-side swaps that are degree-neutral
    under the protocol it matches (2 = present, 1 = masked); read only that protocol."""
    rng = np.random.default_rng(seed)
    hits: dict[str, list[float]] = {}
    with torch.no_grad():
        for ex in examples:
            for r, rel in enumerate(RELATIONS[:2]):  # feeds, hasPart: equipment/location connections
                if len(ex.edges[rel]) < 2:
                    continue
                for side in ("source",) if degree_offset is not None else ("source", "target"):
                    col = 0 if side == "source" else 1
                    for true, wrong in swap_cases(ex, rel, side, max_cases, rng, degree_offset):
                        base = f"{rel}/{side}"
                        for proto in ("present", "masked"):
                            g = _with_swap(ex, rel, true, wrong) if proto == "present" else ex
                            keep = _without(ex, rel, true) if proto == "masked" else None
                            h = model.encode(g, keep)
                            ts = model.score(h, torch.tensor([true[0]]), torch.tensor([true[1]]), r).item()
                            ws = model.score(h, torch.tensor([wrong[0]]), torch.tensor([wrong[1]]), r).item()
                            hits.setdefault(f"{base}/{proto}", []).append(1.0 if ts > ws else 0.5 if ts == ws else 0.0)
                        # degree heuristic, computed on the graph that still contains the wrong edge
                        gw = _with_swap(ex, rel, true, wrong)
                        dt = _degree(gw, rel, true[col], col, (-1, -1))
                        dw = _degree(gw, rel, wrong[col], col, (-1, -1))
                        hits.setdefault(f"{base}/degree", []).append(1.0 if dt > dw else 0.5 if dt == dw else 0.0)
    out = {k: float(np.mean(v)) for k, v in hits.items()}
    out.update({f"{k}/n": float(len(v)) for k, v in hits.items()})
    return out


def cross_validated_swap_detection(
    examples, vocab, model_config, train_cfg, folds: int = 5, degree_offset: int | None = None, max_cases: int = 200
) -> dict[str, float]:
    """Retrain per grouped fold (as `cli.run_cv` does) and pool swap-detection
    accuracy over the held-out buildings, weighted by case count."""
    from .cli import grouped_folds
    from .data import duplicate_groups
    from .train import train

    sums: dict[str, float] = {}
    counts: dict[str, float] = {}
    for test_idx in grouped_folds(duplicate_groups(examples, vocab), folds, train_cfg.seed):
        held = set(test_idx)
        model, _ = train([e for i, e in enumerate(examples) if i not in held], vocab, model_config, train_cfg, log_every=10**9)
        r = evaluate_swap_detection(model, [examples[i] for i in test_idx], max_cases, train_cfg.seed, degree_offset)
        for k, v in r.items():
            if not k.endswith("/n"):
                n = r[k + "/n"]
                sums[k] = sums.get(k, 0.0) + v * n
                counts[k] = counts.get(k, 0.0) + n
    out = {k: sums[k] / counts[k] for k in sums}
    out.update({f"{k}/n": counts[k] for k in counts})
    return out


def main() -> None:
    import argparse
    from pathlib import Path

    from ..data.cache import FileCache
    from ..data.ontology import BrickOntology
    from .data import load_corpus
    from .model import ModelConfig
    from .train import TrainConfig

    p = argparse.ArgumentParser(description="Swap-detection CV (see module docstring).")
    p.add_argument("--cache-dir", default="data_cache")
    p.add_argument("--layers", type=int, default=2)
    p.add_argument("--seeds", type=int, default=3)
    p.add_argument("--epochs", type=int, default=40)
    args = p.parse_args()
    cache = FileCache(Path(args.cache_dir))
    examples, vocab = load_corpus(cache, BrickOntology.load(cache))
    # degree_offset 2 = degree-neutral for `present`; 1 = degree-neutral for `masked`;
    # None = unmatched (degree/orphan artifacts inflate every number).
    for label, offset, proto in (("unmatched", None, "present"), ("degree-matched", 2, "present"), ("degree-matched", 1, "masked")):
        for seed in range(args.seeds):
            r = cross_validated_swap_detection(
                examples, vocab, ModelConfig(n_layers=args.layers), TrainConfig(epochs=args.epochs, seed=seed), 5, offset
            )
            for k in sorted(r):
                if k.endswith(f"/{proto}") or (offset is None and k.endswith("/degree")):
                    print(f"{label:15s} seed={seed} {k:28s} acc={r[k]:.3f} n={int(r[k + '/n'])}")


if __name__ == "__main__":
    main()
