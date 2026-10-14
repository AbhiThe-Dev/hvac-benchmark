"""Scoring for the work-order text screen (PREREGISTRATION_DR.md Addendum 32, Stage 1). Pure functions over already-loaded labels; the labels are model-made and NOT expert-verified."""
import json
import random
import re
from pathlib import Path

from . import workorders as W

STOP_LLM_ONLY = 0.10
STOP_PRECISION = 0.70
BOOT = 2000
BOOT_SEED = 32
_NULLS = ("", "null", "none", "n/a", "false")


def norm(s):
    return re.sub(r"\s+", " ", str(s or "").lower()).strip()


def load_jsonl(paths):
    out = {}
    for p in paths:
        for n, line in enumerate(Path(p).read_text().splitlines(), 1):
            if not line.strip():
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"{p} line {n}: not JSON ({e})")
            if not isinstance(o, dict) or "sid" not in o:
                raise ValueError(f"{p} line {n}: no sid")
            if o["sid"] in out:
                raise ValueError(f"duplicate sid {o['sid']}")
            out[o["sid"]] = o
    return out


def check_coverage(objs, sids, name):
    """Every sid exactly once (load_jsonl rejects repeats), nothing extra, all four kinds present."""
    missing = [s for s in sids if s not in objs]
    extra = [s for s in objs if s not in set(sids)]
    bad = [s for s, o in objs.items() if not all(k in o for k in W.KINDS)]
    if missing or extra or bad:
        raise ValueError(f"{name}: {len(missing)} missing {missing[:5]}, {len(extra)} extra {extra[:5]}, {len(bad)} lacking a kind {bad[:5]}")


def as_bool(v):
    return v is True or (isinstance(v, str) and v.strip().lower() == "true")


def labels(objs):
    return {s: {k: as_bool(o[k]) for k in W.KINDS} for s, o in objs.items()}


def quote_of(v):
    return None if v is None or norm(v) in _NULLS else str(v)


def extraction(objs, desc):
    """{sid: {kind: (extracted, supported)}}: supported = a quote was given and its words appear literally in the description."""
    out = {}
    for s, o in objs.items():
        d = norm(desc[s])
        out[s] = {}
        for k in W.KINDS:
            q = quote_of(o[k])
            out[s][k] = (q is not None, q is not None and norm(q) in d)
    return out


def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return None if pe == 1 else (po - pe) / (1 - pe)


def agreement(l1, l2):
    sids = sorted(l1)
    out = {}
    for k in W.KINDS:
        a, b = [l1[s][k] for s in sids], [l2[s][k] for s in sids]
        out[k] = {"n": len(sids), "agree": sum(x == y for x, y in zip(a, b)), "l1_true": sum(a), "l2_true": sum(b), "both_true": sum(x and y for x, y in zip(a, b)), "kappa": kappa(a, b)}
    return out


def disputes(l1, l2):
    return [(s, k) for s in sorted(l1) for k in W.KINDS if l1[s][k] != l2[s][k]]


def reference(l1, l2, adjudicated):
    """Common answer where the labellers agree, the adjudicated ruling where they differ. adjudicated = {sid: {kind: bool}}. Raises if a dispute has no ruling."""
    ref, open_ = {}, []
    for s in l1:
        ref[s] = {}
        for k in W.KINDS:
            if l1[s][k] == l2[s][k]:
                ref[s][k] = l1[s][k]
            elif k in adjudicated.get(s, {}):
                ref[s][k] = bool(adjudicated[s][k])
            else:
                open_.append((s, k))
    if open_:
        raise ValueError(f"{len(open_)} disputes without a ruling, e.g. {open_[:5]}")
    return ref


def per_order(ref, ext, desc):
    """One record per order: the reference truth, the keyword hits, the extractor's confirmed statements."""
    out = {}
    for s in ref:
        kw = W.keyword_hits(desc[s])
        out[s] = {"truth": ref[s], "kw": kw, "ext": {k: ext[s][k][0] for k in W.KINDS}, "conf": {k: ext[s][k][0] and ext[s][k][1] and ref[s][k] for k in W.KINDS},
                  "unsupported": {k: ext[s][k][0] and not ext[s][k][1] for k in W.KINDS}}
        out[s]["llm_only"] = any(out[s]["conf"][k] and not kw[k] for k in W.DECISIVE)
        out[s]["any_decisive"] = any(ref[s][k] for k in W.DECISIVE)
        out[s]["kw_any_decisive"] = any(ref[s][k] and kw[k] for k in W.DECISIVE)
    return out


def _mean(x):
    x = list(x)
    return sum(x) / len(x) if x else float("nan")


def by_university(rows, uni):
    g = {}
    for s in rows:
        g.setdefault(uni[s], []).append(s)
    return g


def share(rows, uni, eligible, fn):
    """(equal-weight mean over universities, volume-weighted mean, min, max) of the share of orders with fn(record) true."""
    g = by_university(rows, uni)
    per = {u: _mean(fn(rows[s]) for s in ss) for u, ss in g.items()}
    tot = sum(eligible[u] for u in per)
    return {"equal": _mean(per.values()), "volume": sum(per[u] * eligible[u] for u in per) / tot, "min": min(per.values()), "max": max(per.values()), "per_university": per}


def llm_only_for(rows, uni, eligible, kinds):
    """Exploratory: the LLM-only share counting only these kinds."""
    return share(rows, uni, eligible, lambda r: any(r["conf"][k] and not r["kw"][k] for k in kinds))


def statement_counts(rows, kinds):
    ext = sum(r["ext"][k] for r in rows.values() for k in kinds)
    conf = sum(r["conf"][k] for r in rows.values() for k in kinds)
    return ext, conf


def kind_table(rows, uni, eligible):
    out = {}
    for k in W.KINDS:
        truth = sum(r["truth"][k] for r in rows.values())
        kw_tp = sum(r["truth"][k] and r["kw"][k] for r in rows.values())
        kw_pos = sum(r["kw"][k] for r in rows.values())
        ext_pos, conf = statement_counts(rows, (k,))
        out[k] = {"prevalence": share(rows, uni, eligible, lambda r, k=k: r["truth"][k]), "truth_n": truth,
                  "kw_recall": kw_tp / truth if truth else None, "kw_precision": kw_tp / kw_pos if kw_pos else None, "kw_n": kw_pos,
                  "ext_recall": conf / truth if truth else None, "ext_precision": conf / ext_pos if ext_pos else None, "ext_n": ext_pos,
                  "ext_unsupported": sum(r["unsupported"][k] for r in rows.values())}
    return out


def _ci(x):
    x = sorted(v for v in x if v == v)
    return (x[int(0.025 * len(x))], x[min(len(x) - 1, int(0.975 * len(x)))]) if x else (float("nan"), float("nan"))


def stop_figures(rows, uni, eligible, seed=BOOT_SEED, n=BOOT):
    """The two figures the frozen stop rule reads, with 95% bootstrap intervals (orders resampled within university)."""
    llm = share(rows, uni, eligible, lambda r: r["llm_only"])
    ext, conf = statement_counts(rows, W.DECISIVE)
    prec = conf / ext if ext else None
    rng = random.Random(seed)
    g = by_university(rows, uni)
    b_llm, b_prec = [], []
    for _ in range(n):
        per, e, c = [], 0, 0
        for ss in g.values():
            pick = [ss[rng.randrange(len(ss))] for _ in ss]
            per.append(_mean(rows[s]["llm_only"] for s in pick))
            for s in pick:
                e += sum(rows[s]["ext"][k] for k in W.DECISIVE)
                c += sum(rows[s]["conf"][k] for k in W.DECISIVE)
        b_llm.append(_mean(per))
        b_prec.append(c / e if e else float("nan"))
    return {"llm_only": llm, "llm_only_ci": _ci(b_llm), "precision": prec, "precision_ci": _ci(b_prec), "statements": ext, "confirmed": conf}


def verdict(f):
    """The frozen Stage 1 rule: STOP if the LLM-only share (equal weight over universities) is below 10% or the pooled precision over B/C/D is below 70%."""
    p = f["precision"]
    stop = f["llm_only"]["equal"] < STOP_LLM_ONLY or p is None or p < STOP_PRECISION
    why = []
    if f["llm_only"]["equal"] < STOP_LLM_ONLY:
        why.append(f"LLM-only share {100 * f['llm_only']['equal']:.1f}% is below {100 * STOP_LLM_ONLY:.0f}%")
    if p is None or p < STOP_PRECISION:
        why.append("precision " + ("undefined (no statements extracted)" if p is None else f"{100 * p:.0f}% is below {100 * STOP_PRECISION:.0f}%"))
    straddle = [name for name, val, ci, thr in (("LLM-only share", f["llm_only"]["equal"], f["llm_only_ci"], STOP_LLM_ONLY), ("precision", p, f["precision_ci"], STOP_PRECISION)) if val is not None and ci[0] < thr < ci[1]]
    volume_differs = (f["llm_only"]["volume"] < STOP_LLM_ONLY) != (f["llm_only"]["equal"] < STOP_LLM_ONLY)
    return {"stop": stop, "why": why, "straddles": straddle, "volume_weight_differs": volume_differs}
