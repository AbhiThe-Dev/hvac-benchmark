"""Run all folds x variants x seeds, then aggregate (Phase 16/17)."""

from __future__ import annotations

import multiprocessing as mp
import pickle
from collections import defaultdict
from pathlib import Path

import numpy as np
from .data import SLOT_NAMES as SLOT_NAMES_

from .classify import VARIANTS, make_split, regime_support, train_predict, unsupported_positive, zero_shot_case_scores
from .corruptions import HARD_FAMILIES
from .metrics import auprc, auprc_balanced, auroc, auroc_pairs, best_f1_threshold, f1_at, f1_balanced, fpr_at

LETTER = {"A": "sys07_vav_reheat", "B": "sys03_psz_ac", "C": "vav_2ahu_2loops", "D": "vav_3ahu_2loops"}
FOLDS = {
    "spec": dict(train="AB", test="CD"),  # the specified split: train A(+B), test on held-out topology C (D as a second test)
    "loto_A": dict(train="BCD", test="A"),
    "loto_B": dict(train="ACD", test="B"),
    "loto_C": dict(train="ABD", test="C"),
    "loto_D": dict(train="ABC", test="D"),
}
SEEDS = (0, 1, 2, 3, 4)

_DATA = None
_KIT = None


def _load_data(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def _init(path):
    global _DATA, _KIT
    from .encoder_io import EncoderKit
    with open(path, "rb") as f:
        _DATA = pickle.load(f)
    _KIT = EncoderKit()


def _task(t):
    fold, variant, seed, train_ids, score_ids = t
    return fold, variant, seed, train_predict(variant, seed, train_ids, score_ids, _DATA, _KIT)


def run_all(cases: list[dict], cal_cases: list[dict], data_pickle: Path, n_procs: int = 8, log=print) -> dict:
    tasks, splits = [], {}
    for fold, d in FOLDS.items():
        sp = make_split(cases, [LETTER[x] for x in d["train"]])
        test_ids = [c["case_id"] for c in cases if c["topology_id"] in [LETTER[x] for x in d["test"]]]
        cal_ids = [c["case_id"] for c in cal_cases if c["topology_id"] in [LETTER[x] for x in d["train"]]]
        cal_own = {LETTER[x]: [c["case_id"] for c in cal_cases if c["topology_id"] == LETTER[x]] for x in d["test"]}
        splits[fold] = {**sp, "test": test_ids, "cal": cal_ids, "cal_own": cal_own}
        for v in VARIANTS:
            for s in SEEDS:
                tasks.append((fold, v, s, sp["train"], sp["val"] + test_ids + cal_ids + [i for v in cal_own.values() for i in v]))
    log(f"{len(tasks)} training runs on {n_procs} processes")
    scores: dict = {}
    ctx = mp.get_context("spawn")
    with ctx.Pool(n_procs, initializer=_init, initargs=(str(data_pickle),)) as pool:
        for i, (fold, v, s, out) in enumerate(pool.imap_unordered(_task, tasks, chunksize=1)):
            scores[(fold, v, s)] = out
            if (i + 1) % 25 == 0:
                log(f"  {i + 1}/{len(tasks)} done")
    data = _load_data(data_pickle)
    sup = {f: regime_support(sp["train"], data) for f, sp in splits.items()}
    unsup = {f: sorted(i for i in sp["test"] if unsupported_positive(data[i], sup[f])) for f, sp in splits.items()}
    return {"scores": scores, "splits": splits, "support": {f: sorted(map(list, v)) if "ALL" not in v else ["ALL"] for f, v in sup.items()}, "unsup_cases": unsup}


# ---------------------------------------------------------------------------------------------
def _slice_cases(cases_by_id: dict, ids: list[str], name: str, unsupported: frozenset = frozenset()):
    """(positives, negatives) case-id lists for a named evaluation slice."""
    pos, neg = [], []
    for i in ids:
        c = cases_by_id[i]
        if c["label"] == 0:
            neg.append(i)
            continue
        if i in unsupported:
            continue  # a corrupted edge lives in a feature regime the head had no training support for: not scorable
        d, fam, obs = c["difficulty"], c["corruption_type"], c["observable"]
        keep = {
            "hard": d == "hard",
            "hard_observable": d == "hard" and obs == "true",
            "hard_ambiguous": d == "hard" and obs == "ambiguous",
            "hard_unobservable": d == "hard" and obs == "false",
            "hard_not_observable": d == "hard" and obs in ("ambiguous", "false"),
            "hard_degree_preserving": d == "hard" and c["degree_preserving"],
            "hard_degree_shift": d == "hard" and not c["degree_preserving"],
            "hard_observable_dp": d == "hard" and obs == "true" and c["degree_preserving"],
            "easy": d == "easy",
        }.get(name, d == "hard" and fam == name)
        if keep:
            pos.append(i)
    return pos, neg


def _metrics(sc: dict, cases_by_id, ids, name, thr, unsupported=frozenset()):
    pos, neg = _slice_cases(cases_by_id, ids, name, unsupported)
    if not pos or not neg:
        return None
    y = np.array([1] * len(pos) + [0] * len(neg))
    s = np.array([sc[i] for i in pos + neg])
    conc, tot = auroc_pairs(y, s)
    pred = s >= thr
    return {"n_pos": len(pos), "n_neg": len(neg), "auroc": conc / tot, "auprc": auprc(y, s), "auprc_bal": auprc_balanced(y, s),
            "f1": f1_at(y, s, thr), "f1_bal": f1_balanced(y, s, thr),
            "fpr_clean": fpr_at(y, s, thr), "recall": float(pred[y == 1].mean()), "conc": conc, "tot": tot,
            "tp": float((pred & (y == 1)).sum()), "fp": float((pred & (y == 0)).sum()), "fn": float((~pred & (y == 1)).sum())}


CAL_QUANTILE = 0.90


def _cal_threshold(sc, cal_ids):
    """Operating point from a pool of clean calibration documents (24 per training topology, never trained on):
    the 90th percentile of their scores, i.e. a target clean false-positive rate of ~10%."""
    return float(np.quantile([sc[i] for i in cal_ids], CAL_QUANTILE, method="higher"))


SLICES = ["hard", "hard_observable", "hard_not_observable", "hard_degree_preserving", "hard_degree_shift", "hard_observable_dp", "easy"] + list(HARD_FAMILIES)


def aggregate(res: dict, cases: list[dict], zero_shot: dict[str, dict[str, float]] | None = None) -> dict:
    """metrics[variant][view][slice] = mean-over-seeds dict.  views: 'loto_pooled', 'spec_C', 'spec_D', 'loto_<L>'."""
    by_id = {c["case_id"]: c for c in cases}
    splits, scores = res["splits"], res["scores"]
    uns = {f: set(res["unsup_cases"][f]) for f in splits}
    variants = list(VARIANTS) + list(zero_shot or {})
    out: dict = {}
    for v in variants:
        out[v] = defaultdict(dict)
        seed_list = SEEDS if v in VARIANTS else (0,)
        per_seed = defaultdict(list)  # (view, slice) -> metric dicts, one per (seed x test-topology fold)
        for s in seed_list:
            pooled = defaultdict(list)
            for fold, d in FOLDS.items():
                sp = splits[fold]
                sc = scores[(fold, v, s)] if v in VARIANTS else zero_shot[v]
                thr = _cal_threshold(sc, sp["cal"])
                unsup = frozenset(uns[fold])
                for L in d["test"]:
                    ids = [i for i in sp["test"] if by_id[i]["topology_id"] == LETTER[L]]
                    view = f"spec_{L}" if fold == "spec" else f"loto_{L}"
                    for sl in SLICES:
                        m = _metrics(sc, by_id, ids, sl, thr, unsup)
                        if m:
                            per_seed[(view, sl)].append(m)
                            if fold != "spec":
                                pooled[sl].append(m)
            for sl, ms in pooled.items():
                conc, tot = sum(m["conc"] for m in ms), sum(m["tot"] for m in ms)
                tp, fp, fn = sum(m["tp"] for m in ms), sum(m["fp"] for m in ms), sum(m["fn"] for m in ms)
                nneg = sum(m["n_neg"] for m in ms)
                per_seed[("loto_pooled", sl)].append({
                    "n_pos": sum(m["n_pos"] for m in ms), "n_neg": nneg, "auroc": conc / tot, "auprc": float(np.mean([m["auprc"] for m in ms])),
                    "auprc_bal": float(np.mean([m["auprc_bal"] for m in ms])),
                    "f1": 2 * tp / (2 * tp + fp + fn) if tp + fp + fn else 0.0,
                    "f1_bal": float(np.mean([m["f1_bal"] for m in ms])), "fpr_clean": fp / nneg if nneg else float("nan"),
                    "recall": tp / (tp + fn) if tp + fn else float("nan")})
        for (view, sl), ms in per_seed.items():
            KEYS = ("auroc", "auprc", "auprc_bal", "f1", "f1_bal", "fpr_clean", "recall")
            agg = {k: float(np.mean([m[k] for m in ms])) for k in KEYS}
            agg.update({k + "_sd": float(np.std([m[k] for m in ms])) for k in KEYS})
            agg["n_pos"], agg["n_neg"] = ms[0]["n_pos"], ms[0]["n_neg"]
            out[v][view][sl] = agg
    return {v: dict(views) for v, views in out.items()}


def paired_bootstrap(res: dict, cases: list[dict], a: str, b: str, slice_name: str = "hard_observable", n_boot: int = 2000, seed: int = 0, folds: tuple = ("loto_A", "loto_B", "loto_C", "loto_D"), test_topos: tuple | None = None):
    """Delta pooled-LOTO AUROC (a - b) with a group bootstrap over leakage groups (seed-averaged case scores)."""
    by_id = {c["case_id"]: c for c in cases}
    splits, scores = res["splits"], res["scores"]
    per_fold = {}
    for fold in folds:
        ids = [i for i in splits[fold]["test"] if test_topos is None or by_id[i]["topology_id"] in [LETTER[x] for x in test_topos]]
        pos, neg = _slice_cases(by_id, ids, slice_name, frozenset(res["unsup_cases"][fold]))
        ids2 = pos + neg
        sa = {i: np.mean([scores[(fold, a, s)][i] for s in SEEDS]) for i in ids2}
        sb = {i: np.mean([scores[(fold, b, s)][i] for s in SEEDS]) for i in ids2}
        per_fold[fold] = (pos, neg, sa, sb)

    def pooled(sample_groups, which):
        conc = tot = 0.0
        for fold, (pos, neg, sa, sb) in per_fold.items():
            sc = sa if which == "a" else sb
            p = [i for i in pos for _ in range(sample_groups.get(by_id[i]["group_id"], 0))]
            n = [i for i in neg for _ in range(sample_groups.get(by_id[i]["group_id"], 0))]
            if p and n:
                y = np.array([1] * len(p) + [0] * len(n))
                s = np.array([sc[i] for i in p + n])
                c, t = auroc_pairs(y, s)
                conc, tot = conc + c, tot + t
        return conc / tot if tot else float("nan")

    groups = sorted({by_id[i]["group_id"] for pos, neg, *_ in per_fold.values() for i in pos + neg})
    full = {g: 1 for g in groups}
    point = (pooled(full, "a"), pooled(full, "b"))
    rng = np.random.default_rng(seed)
    deltas = []
    for _ in range(n_boot):
        draw = rng.integers(0, len(groups), len(groups))
        cnt: dict = defaultdict(int)
        for j in draw:
            cnt[groups[j]] += 1
        da, db = pooled(cnt, "a"), pooled(cnt, "b")
        if not (np.isnan(da) or np.isnan(db)):
            deltas.append(da - db)
    lo, hi = np.percentile(deltas, [2.5, 97.5])
    return {"auroc_a": point[0], "auroc_b": point[1], "delta": point[0] - point[1], "ci95": [float(lo), float(hi)], "n_groups": len(groups)}
