"""`hvac-pretrain`: grouped cross-validation of the pretraining task against
baselines, then a final fit on every training building that is saved as a
reusable encoder plus per-node embeddings."""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import asdict
from pathlib import Path

import numpy as np

from ..data.cache import FileCache
from ..data.ontology import BrickOntology
from .data import RELATIONS, duplicate_groups, is_real, load_corpus
from .evaluate import GNNScorer, RandomScorer, TypePriorScorer, evaluate
from .model import ModelConfig, save_pretrained
from .train import TrainConfig, train

logger = logging.getLogger(__name__)


def grouped_folds(groups: list[list[int]], k: int, seed: int) -> list[list[int]]:
    """Assign duplicate-groups to folds, balancing by group size, so no
    duplicate building straddles train and test."""
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(groups))
    folds: list[list[int]] = [[] for _ in range(k)]
    for gi in sorted(order, key=lambda g: -len(groups[g])):
        min(folds, key=len).extend(groups[gi])
    return folds


def run_cv(examples, vocab, model_config, cfg, k: int, extra_train=()) -> dict:
    """Grouped CV over `examples` (real buildings). `extra_train` (e.g.
    simulated buildings) is added to every training fold and never tested."""
    groups = duplicate_groups(examples, vocab)
    folds = grouped_folds(groups, k, cfg.seed)
    per_fold = []
    for f, test_idx in enumerate(folds):
        test = [examples[i] for i in test_idx]
        train_ex = [examples[i] for i in range(len(examples)) if i not in set(test_idx)]
        model, _ = train(train_ex + list(extra_train), vocab, model_config, cfg, log_every=cfg.epochs)
        scorers = [GNNScorer(model), TypePriorScorer(train_ex, vocab), RandomScorer()]
        fold = {"test_buildings": [e.building_id for e in test]}
        for sc in scorers:
            fold[sc.name] = evaluate(sc, test, seed=cfg.seed)
        per_fold.append(fold)
        logger.info("fold %d/%d done (%d test buildings)", f + 1, k, len(test))
    return {"n_duplicate_groups": len(groups), "duplicate_groups": [[examples[i].building_id for i in g] for g in groups if len(g) > 1], "folds": per_fold}


def summarize_cv(cv: dict) -> dict:
    """Pool per-fold metrics weighted by the number of evaluated edges."""
    out: dict = {}
    for sc in ("gnn", "type_prior", "random"):
        out[sc] = {}
        for rel in RELATIONS:
            out[sc][rel] = {}
            for v in ("all", "within_type"):
                cells = [f[sc][rel][v] for f in cv["folds"] if f[sc][rel][v]["n"]]
                n = sum(c["n"] for c in cells)
                out[sc][rel][v] = {"n": n} | {
                    m: (sum(c[m] * c["n"] for c in cells) / n if n else float("nan")) for m in ("mrr", "hits@1", "hits@3")
                }
    return out


def format_summary(summary: dict) -> str:
    lines = []
    for v in ("all", "within_type"):
        lines.append(f"\n[{v}] held-out-building MRR / Hits@1 / Hits@3   (n edge-sides)")
        for rel in RELATIONS:
            n = summary["gnn"][rel][v]["n"]
            row = "  ".join(
                f"{sc}: {summary[sc][rel][v]['mrr']:.3f}/{summary[sc][rel][v]['hits@1']:.3f}/{summary[sc][rel][v]['hits@3']:.3f}"
                for sc in ("gnn", "type_prior", "random")
            )
            lines.append(f"  {rel:9s} {row}   (n={n})")
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser(prog="hvac-pretrain", description=__doc__)
    p.add_argument("--cache-dir", default="data_cache")
    p.add_argument("--out-dir", default="results/pretrain")
    p.add_argument("--folds", type=int, default=5, help="grouped CV folds; 0 skips CV")
    p.add_argument("--epochs", type=int, default=TrainConfig.epochs)
    p.add_argument("--dim", type=int, default=ModelConfig.dim)
    p.add_argument("--layers", type=int, default=ModelConfig.n_layers)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument(
        "--include-simulated", action="store_true",
        help="ablation: add the simulated LBNL models to TRAINING only; evaluation stays on real buildings",
    )
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    cache = FileCache(Path(args.cache_dir))
    ontology = BrickOntology.load(cache)
    everything, vocab = load_corpus(cache, ontology, args.include_simulated)
    examples = [e for e in everything if is_real(e)]
    simulated = [e for e in everything if not is_real(e)]
    logger.info(
        "corpus: %d real buildings (%d nodes); %d simulated used as extra training data",
        len(examples), sum(e.n_nodes for e in examples), len(simulated),
    )

    model_config = ModelConfig(dim=args.dim, n_layers=args.layers)
    cfg = TrainConfig(epochs=args.epochs, seed=args.seed)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    report: dict = {}
    if args.folds:
        cv = run_cv(examples, vocab, model_config, cfg, args.folds, simulated)
        summary = summarize_cv(cv)
        report = {"cv_summary": summary, "cv": cv}
        text = format_summary(summary)
        print(text)
        (out / "cv_report.json").write_text(json.dumps(report, indent=2))
        (out / "cv_summary.txt").write_text(text + "\n")

    model, history = train(examples + simulated, vocab, model_config, cfg)
    save_pretrained(
        model,
        out / "encoder",
        metadata={
            "train_config": asdict(cfg),
            "real_buildings": [e.building_id for e in examples],
            "simulated_buildings_in_training": [e.building_id for e in simulated],
            "loss_history": history,
            "cv_summary": report.get("cv_summary"),
        },
    )
    import torch

    with torch.no_grad():
        arrays = {}
        for e in examples + simulated:
            arrays[f"{e.building_id}__emb"] = model.encode(e).numpy()
            arrays[f"{e.building_id}__nodes"] = np.array(e.node_ids)
    np.savez_compressed(out / "node_embeddings.npz", **arrays)
    logger.info("saved encoder to %s", out / "encoder")


if __name__ == "__main__":
    main()
