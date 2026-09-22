"""Aggregate S-C scores (case-level detector +/- pretrained encoder) into AUROC tables with building-cluster bootstrap CIs.
  .venv/bin/python doc_mismatch/scripts/29b_dr_report_classifier.py [--boot 400]"""
import json, pickle, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.dr import verifier_eval as V, classifier_eval as CE
from docmismatch.metrics import auroc

B = int(sys.argv[sys.argv.index("--boot") + 1]) if "--boot" in sys.argv else 400
ARMS = ["baseline", "noise_only", "regime", "full", "full_x3"]
SUITES = ["T1_in_range", "T2_regime", "T3_control", "T4_topology", "T5_climate", "T6_compound"]
SHIFT = SUITES[2:]
VAR = list(CE.VARIANTS)
FAM = ["wrong_ahu_mapping", "vav_zone_swap", "plant_loop_mapping", "sensor_mapping", "same_medium_branch", "parallel_peer_swap"]


def fmt(x, d=3):
    return "n/a" if x is None or not np.isfinite(x) else f"{x:.{d}f}"


class Cell:
    """cases (ids), seed-wise scores -> mean-over-seeds AUROC with building-cluster bootstrap"""

    def __init__(self, ids, meta, scores_by_seed, fam=None):
        ids = [i for i in ids if all(i in sc for sc in scores_by_seed)]
        ids = [i for i in ids if (meta[i]["label"] == 0) or (meta[i]["difficulty"] == "hard" and meta[i]["observable"] == "true" and (fam is None or meta[i]["corruption_type"] == fam))]
        self.ids = ids
        self.y = np.array([meta[i]["label"] for i in ids])
        self.b = np.array([meta[i]["topology_id"] for i in ids])
        self.S = np.array([[sc[i] for i in ids] for sc in scores_by_seed]) if ids else np.zeros((0, 0))

    def stat(self, w=None):
        if len(self.ids) == 0:
            return np.nan
        vals = []
        for s in self.S:
            if w is None:
                vals.append(auroc(self.y, s))
            else:
                k = w > 0
                # weighted AUROC via repeat expansion (counts are small integers)
                idx = np.repeat(np.arange(len(w)), w.astype(int))
                vals.append(auroc(self.y[idx], s[idx]))
        return float(np.nanmean(vals))

    def boot(self, B=B, seed=0):
        e = self.stat()
        if len(self.ids) == 0:
            return dict(est=e, lo=np.nan, hi=np.nan, n_pos=0, n_neg=0)
        ub = np.unique(self.b); idx = {u: np.flatnonzero(self.b == u) for u in ub}
        rng = np.random.default_rng(seed); v = []
        for _ in range(B):
            pick = rng.choice(ub, len(ub)); w = np.zeros(len(self.ids))
            for u in ub:
                w[idx[u]] = (pick == u).sum()
            v.append(self.stat(w))
        v = np.array(v)
        return dict(est=e, lo=float(np.nanpercentile(v, 2.5)), hi=float(np.nanpercentile(v, 97.5)), n_pos=int((self.y == 1).sum()), n_neg=int((self.y == 0).sum()), n_bldg=len(ub))


def paired(A, Bc, B=B, seed=0):
    """AUROC(A) - AUROC(Bc), same case ids and same buildings resampled jointly (A and Bc must cover the same cases)"""
    common = [i for i in A.ids if i in set(Bc.ids)]
    if not common:
        return None
    ia = {i: k for k, i in enumerate(A.ids)}; ib = {i: k for k, i in enumerate(Bc.ids)}
    ka, kb = [ia[i] for i in common], [ib[i] for i in common]
    y = A.y[ka]; b = A.b[ka]; SA = A.S[:, ka]; SB = Bc.S[:, kb]
    def st(S, w):
        idx = np.repeat(np.arange(len(w)), w.astype(int)) if w is not None else slice(None)
        return float(np.nanmean([auroc(y[idx], s[idx]) for s in S]))
    est = st(SA, None) - st(SB, None)
    ub = np.unique(b); ix = {u: np.flatnonzero(b == u) for u in ub}; rng = np.random.default_rng(seed); v = []
    for _ in range(B):
        pick = rng.choice(ub, len(ub)); w = np.zeros(len(y))
        for u in ub: w[ix[u]] = (pick == u).sum()
        v.append(st(SA, w) - st(SB, w))
    return dict(est=est, lo=float(np.nanpercentile(v, 2.5)), hi=float(np.nanpercentile(v, 97.5)))


def main():
    meta = json.loads((CE.OUT / "cases_meta.json").read_text())
    ids_su = V.spec_ids()
    scores = {a: pickle.loads((CE.OUT / f"scores_{a}.pkl").read_bytes()) for a in ARMS if (CE.OUT / f"scores_{a}.pkl").exists()}
    A = V.arms()
    seeds = sorted({k[2] for sc in scores.values() for k in sc})
    def sbs(arm, fold, v):
        return [scores[arm][(fold, v, s)] for s in seeds if (fold, v, s) in scores[arm]]
    def ids_of(su, tel):
        return [k for k, m in meta.items() if m["topology_id"] in ids_su[su] and m["telemetry"] == tel]
    def cell(arm, v, cond, su, fam=None, tel="estimated"):
        if cond == "seen":
            return Cell(ids_of(su, tel), meta, sbs(arm, "seen", v), fam)
        if cond == "unseen":
            allsc = []
            for s in seeds:
                m = {}
                for ss in range(4):
                    m.update(scores[arm].get((f"unseen_s{ss}", v, s), {}))
                allsc.append(m)
            return Cell(ids_of(su, "estimated"), meta, allsc, fam)
        ids = [k for k in scores[arm].get(("days", v, seeds[0]), {})]
        return Cell(ids, meta, sbs(arm, "days", v), fam)
    md = ["# S-C (case-level detector, +/- pretrained encoder): domain-randomization study", "",
          f"AUROC of hard documentation errors (observable=true) vs clean documentation; mean over {len(seeds)} seeds; 95% CI = building-cluster bootstrap ({B}). "
          "Encoder = results/pretrain/encoder. Same head/recipe/splits for every variant.", ""]
    res = {}
    for cond, title in (("days", "unseen events/days, seen buildings (held-out event groups + clean windows 6,7 of the arm's own buildings)"), ("seen", "seen seasons, unseen buildings/regimes (estimated test telemetry)"),
                        ("unseen", "UNSEEN season on unseen buildings/regimes (compound where the suite is shifted)")):
        md += [f"## {title}", "", "| arm | variant | " + ("in-dist" if cond == "days" else " | ".join(SUITES)) + " |", "|---|---|" + "---|" * (1 if cond == "days" else len(SUITES))]
        for arm in scores:
            for v in VAR:
                cols = ["(train bldgs)"] if cond == "days" else SUITES
                out = []
                for su in cols:
                    b = cell(arm, v, cond, su).boot(); res[f"{cond}|{su}|{arm}|{v}"] = b
                    out.append(f"{fmt(b['est'])} [{fmt(b['lo'])}, {fmt(b['hi'])}]")
                md.append(f"| {arm} | {v} | " + " | ".join(out) + " |")
        md.append("")
    # DR effect: arm - baseline within variant, shifted suites pooled over suite cells (mean of per-suite paired diffs) and per-suite
    md += ["## Effect of domain randomization: AUROC(arm) - AUROC(baseline), same variant, same test cases (seen seasons)", "", "| variant | arm | " + " | ".join(SUITES) + " |", "|---|---|" + "---|" * len(SUITES)]
    for v in VAR:
        for arm in list(scores)[1:]:
            out = []
            for su in SUITES:
                d = paired(cell(arm, v, "seen", su), cell("baseline", v, "seen", su)); res[f"dr|{su}|{arm}|{v}"] = d
                out.append("n/a" if d is None else f"{fmt(d['est'])} [{fmt(d['lo'])}, {fmt(d['hi'])}]")
            md.append(f"| {v} | {arm} | " + " | ".join(out) + " |")
    md.append("")
    md += ["## Effect of the pretrained encoder (seen seasons): AUROC(variant) - AUROC(reference), within arm", "", "| arm | contrast | " + " | ".join(SUITES) + " |", "|---|---|" + "---|" * len(SUITES)]
    for arm in scores:
        for va, vb in (("ev+pretrained_frozen", "evidence_only"), ("ev+pretrained_finetuned", "evidence_only"), ("ev+pretrained_finetuned", "ev+scratch_finetuned"), ("ev+scratch_finetuned", "evidence_only")):
            out = []
            for su in SUITES:
                d = paired(cell(arm, va, "seen", su), cell(arm, vb, "seen", su)); res[f"enc|{su}|{arm}|{va}-{vb}"] = d
                out.append("n/a" if d is None else f"{fmt(d['est'])} [{fmt(d['lo'])}, {fmt(d['hi'])}]")
            md.append(f"| {arm} | {va} - {vb} | " + " | ".join(out) + " |")
    md.append("")
    md += ["## By corruption family (seen seasons, estimated telemetry, suites T2-T6 pooled): AUROC vs clean, evidence_only / ev+pretrained_finetuned", "", "| family | arm | evidence_only | ev+pretrained_finetuned |", "|---|---|---|---|"]
    for fam in FAM:
        for arm in scores:
            out = []
            for v in ("evidence_only", "ev+pretrained_finetuned"):
                ids = [k for su in SUITES[1:] for k in ids_of(su, "estimated")]
                c = Cell(ids, meta, sbs(arm, "seen", v), fam); b = c.boot(B=max(100, B // 4)); res[f"fam|{fam}|{arm}|{v}"] = b
                out.append(f"{fmt(b['est'])} [{fmt(b['lo'])}, {fmt(b['hi'])}] (n_pos {b['n_pos']})")
            md.append(f"| {fam} | {arm} | " + " | ".join(out) + " |")
    (CE.OUT.parent / "classifier_results.json").write_text(json.dumps(res, indent=1, default=float))
    (CE.OUT.parent / "classifier_results.md").write_text("\n".join(md))
    print("\n".join(md[:40]))


main()
