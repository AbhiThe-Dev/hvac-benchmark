"""Pre-registered metrics C1-C4 (PREREGISTRATION.md section 4) with cluster-bootstrap CIs, from decision rows (readiness.apply_layers).

All statistics are class-balanced (wrong-documentation and correct-documentation episodes weighted equally) unless stated, and every CI is a
percentile cluster bootstrap (clusters: real = day, sim = event group); one shared set of bootstrap resamples is used for every cell so cells are coherent.
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np

COLS = ("n", "ans", "ok", "res_n", "res_ans", "flag", "flag_bad", "ans_bad", "crossed", "flag_res", "n_read_ans")
CI = {c: i for i, c in enumerate(COLS)}
BINS = (0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0001)


class Data:
    """Decision rows of ONE layer, indexed for cluster-bootstrap statistics."""

    def __init__(self, rows: list[dict], resolvable: dict | None = None, nboot: int = 2000, seed: int = 0):
        self.rows = rows
        self.G = sorted({r["cluster"] for r in rows}, key=str)
        gi = {g: i for i, g in enumerate(self.G)}
        R = len(rows)
        self.cl = np.array([gi[r["cluster"]] for r in rows], int)
        self.wr = np.array([r["wrong"] for r in rows], bool)
        self.ans = np.array([r["state"] != "FLAGGED" for r in rows], bool)
        self.ok = np.array([(r["say_correct"] == (not r["wrong"])) for r in rows], bool)
        self.crossed = np.array([r["crossed"] for r in rows], bool)
        self.n = np.array([r["n"] for r in rows], float)
        self.conf = np.array([r.get("conf_cal", np.nan) if r.get("conf_cal") is not None else np.nan for r in rows], float)
        key = lambda r: (r["ep"], r["rep"], r["setting"])  # noqa: E731
        self.res = np.array([bool(resolvable.get(key(r), False)) if resolvable is not None else False for r in rows], bool)
        self.has_res = resolvable is not None
        self.bad = ~self.res | (self.crossed & ~self.ok)
        self.season = np.array([r["season"] for r in rows], dtype=object)
        self.family = np.array([r["family"] for r in rows], dtype=object)
        self.slot = np.array([r["slot"] for r in rows], dtype=object)
        self.setting = np.array([r["setting"] for r in rows], dtype=object)
        rng = np.random.default_rng(seed)
        idx = rng.integers(0, len(self.G), (nboot, len(self.G)))
        self.W = np.stack([np.bincount(i, minlength=len(self.G)) for i in idx]).astype(float)   # (B,G) resample counts
        self._cache = {}

    def M(self, mask=None):
        """cluster x class x column sums for the episodes in mask"""
        m = np.ones(len(self.rows), bool) if mask is None else mask
        cols = np.zeros((len(self.rows), len(COLS)))
        a, ok, f = self.ans, self.ok, ~self.ans
        cols[:, CI["n"]] = 1
        cols[:, CI["ans"]] = a
        cols[:, CI["ok"]] = a & ok
        cols[:, CI["res_n"]] = self.res
        cols[:, CI["res_ans"]] = self.res & a
        cols[:, CI["flag"]] = f
        cols[:, CI["flag_bad"]] = f & self.bad
        cols[:, CI["ans_bad"]] = a & self.bad
        cols[:, CI["crossed"]] = self.crossed
        cols[:, CI["flag_res"]] = f & self.res
        cols[:, CI["n_read_ans"]] = np.where(a, self.n, 0.0)
        out = np.zeros((len(self.G), 2, len(COLS)))
        for k, w in ((0, self.wr), (1, ~self.wr)):
            sel = m & w
            np.add.at(out[:, k, :], self.cl[sel], cols[sel])
        return out

    def boot(self, Mx, fn):
        """(point, lo, hi) of fn(S) where S = summed (2, C) stats; nan when undefined"""
        pt = fn(Mx.sum(0))
        Sb = np.einsum("bg,gkc->bkc", self.W, Mx)
        vals = np.array([fn(s) for s in Sb])
        vals = vals[np.isfinite(vals)]
        if len(vals) < 50 or not np.isfinite(pt):
            return pt, np.nan, np.nan
        return pt, float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


# ---------------------------------------------------------------------------------------------- statistics on summed stats S (2, C)
def _c(S, k):
    return S[:, CI[k]]


def acc_bal(S):
    """P(verdict right | answered) under a balanced prior over the two episode classes"""
    n, a, o = _c(S, "n"), _c(S, "ans"), _c(S, "ok")
    if (n == 0).any():
        return np.nan
    den = (a / n).sum()
    return float((o / n).sum() / den) if den > 0 else np.nan


def cov_bal(S):
    n, a = _c(S, "n"), _c(S, "ans")
    return float(np.mean(a / np.maximum(n, 1))) if (n > 0).all() else np.nan


def acc_plain(S):
    a = _c(S, "ans").sum()
    return float(_c(S, "ok").sum() / a) if a > 0 else np.nan


def bad_share(S, which):
    """which = 'flag' or 'ans': class-balanced share of flagged / answered episodes that are 'bad' (unresolvable or would have been answered wrongly)"""
    tot, bad = _c(S, which), _c(S, which + "_bad" if which == "flag" else "ans_bad")
    n = _c(S, "n")
    if (n == 0).any() or tot.sum() == 0:
        return np.nan
    # class-balanced: weight by 1/n_class
    return float((bad / n).sum() / (tot / n).sum()) if (tot / n).sum() > 0 else np.nan


def fmt(t, d=3):
    pt, lo, hi = t
    if not np.isfinite(pt):
        return "n/a"
    return f"{pt:.{d}f} [{lo:.{d}f}, {hi:.{d}f}]" if np.isfinite(lo) else f"{pt:.{d}f}"


# ---------------------------------------------------------------------------------------------- criteria
def c2_status(pt, lo, n_ans, n_cl):
    if n_ans < 8 or n_cl < 5 or not np.isfinite(pt):
        return "insufficient"
    if pt >= 0.93 and lo >= 0.90:
        return "PASS"
    if pt >= 0.93:
        return "INCONCLUSIVE"
    return "FAIL"


def c2_table(D: Data, dims=("all", "season", "family", "slot", "cell")):
    out = {}
    for dim in dims:
        if dim == "all":
            groups = {"all": np.ones(len(D.rows), bool)}
        elif dim == "cell":
            keys = sorted({(s, f, sl) for s, f, sl in zip(D.season, D.family, D.slot)}, key=str)
            groups = {"|".join(map(str, k)): (D.season == k[0]) & (D.family == k[1]) & (D.slot == k[2]) for k in keys}
        else:
            arr = {"season": D.season, "family": D.family, "slot": D.slot}[dim]
            groups = {str(v): arr == v for v in sorted(set(arr), key=str)}
        tab = {}
        for name, m in groups.items():
            Mx = D.M(m)
            S = Mx.sum(0)
            n_ans = int(_c(S, "ans").sum())
            n_cl = int(((Mx[:, :, CI["ans"]].sum(1)) > 0).sum())
            acc = D.boot(Mx, acc_bal)
            cov = D.boot(Mx, cov_bal)
            tab[name] = dict(n=int(_c(S, "n").sum()), answered=n_ans, clusters=n_cl, acc=acc, acc_plain=acc_plain(S), coverage=cov,
                             flag_rate=1.0 - float(_c(S, 'ans').sum() / max(_c(S, 'n').sum(), 1)), status=c2_status(acc[0], acc[1], n_ans, n_cl))
        out[dim] = tab
    return out


def c1_table(Ds: dict, base_policies=("random", "traversal_block", "traversal", "frozen"), setting=None):
    """Ds: policy -> Data (same layer). Paired readings-to-answer among episodes answered by BOTH, plus coverage comparison."""
    A = Ds["active"]
    out = {}
    ka = {(r["ep"], r["rep"], r["setting"]): i for i, r in enumerate(A.rows)}
    for b in base_policies:
        if b not in Ds:
            continue
        B = Ds[b]
        kb = {(r["ep"], r["rep"], r["setting"]): i for i, r in enumerate(B.rows)}
        pairs = [(ka[k], kb[k]) for k in ka.keys() & kb.keys() if A.ans[ka[k]] and B.ans[kb[k]] and (setting is None or k[2] == setting)]
        M = np.zeros((len(A.G), 2, 2))
        gmap = {g: i for i, g in enumerate(A.G)}
        for ia, ib in pairs:
            g = gmap[A.rows[ia]["cluster"]]
            k = 0 if A.wr[ia] else 1
            M[g, k, 0] += 1
            M[g, k, 1] += B.n[ib] - A.n[ia]
        if not pairs:
            out[b] = dict(n_pairs=0)
            continue

        def fn(S):
            if (S[:, 0] == 0).any():
                return np.nan
            return float(np.mean(S[:, 1] / S[:, 0]))
        pt = fn(M.sum(0))
        Sb = np.einsum("bg,gkc->bkc", A.W, M)
        v = np.array([fn(s) for s in Sb]); v = v[np.isfinite(v)]
        ci = (pt, float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) if len(v) > 50 else (pt, np.nan, np.nan)
        ma = np.ones(len(A.rows), bool) if setting is None else A.setting == setting
        mb = np.ones(len(B.rows), bool) if setting is None else B.setting == setting
        covd_pt = cov_bal(A.M(ma).sum(0)) - cov_bal(B.M(mb).sum(0))
        Sa, Sbb = np.einsum("bg,gkc->bkc", A.W, A.M(ma)), np.einsum("bg,gkc->bkc", A.W, B.M(mb))
        cd = np.array([cov_bal(x) - cov_bal(y) for x, y in zip(Sa, Sbb)]); cd = cd[np.isfinite(cd)]
        cov_ci = (covd_pt, float(np.percentile(cd, 2.5)), float(np.percentile(cd, 97.5))) if len(cd) > 50 else (covd_pt, np.nan, np.nan)
        out[b] = dict(n_pairs=len(pairs), saved=ci, cov_diff=cov_ci, cov_active=cov_bal(A.M(ma).sum(0)), cov_base=cov_bal(B.M(mb).sum(0)),
                      status="PASS" if (np.isfinite(ci[1]) and ci[1] > 0 and covd_pt >= 0) else "FAIL")
    return out


def c3(D: Data):
    out = {}
    if not D.has_res:
        return dict(note="no resolvable labels")
    # (a) buckets
    a = {}
    for dim, arr in (("season", D.season), ("slot", D.slot)):
        for v in sorted(set(arr), key=str):
            m = arr == v
            Mx = D.M(m)
            S = Mx.sum(0)
            n_all, n_res = _c(S, "n").sum(), _c(S, "res_n").sum()
            share = n_res / n_all if n_all else 0.0
            cov_res = D.boot(Mx, lambda S_: float(_c(S_, "res_ans").sum() / _c(S_, "res_n").sum()) if _c(S_, "res_n").sum() > 0 else np.nan)
            binding = share >= 0.30
            a[f"{dim}={v}"] = dict(episodes=int(n_all), resolvable=int(n_res), resolvable_share=float(share), binding=bool(binding), coverage_of_resolvable=cov_res,
                                   status=("PASS" if cov_res[0] >= 0.30 else "FAIL") if binding else "n/a (resolvable share < 30%)")
    out["a_buckets"] = a
    Mx = D.M()
    fb = D.boot(Mx, lambda S: bad_share(S, "flag")); ab = D.boot(Mx, lambda S: bad_share(S, "ans"))
    Sb = np.einsum("bg,gkc->bkc", D.W, Mx)
    diff = np.array([bad_share(s, "flag") - bad_share(s, "ans") for s in Sb]); diff = diff[np.isfinite(diff)]
    dpt = fb[0] - ab[0]
    dci = (dpt, float(np.percentile(diff, 2.5)), float(np.percentile(diff, 97.5))) if len(diff) > 50 else (dpt, np.nan, np.nan)
    out["b_necessity"] = dict(flagged_bad_share=fb, answered_bad_share=ab, margin=dci, status="PASS" if (np.isfinite(dci[1]) and dci[1] > 0) else "FAIL",
                              n_flagged=int(_c(Mx.sum(0), "flag").sum()), n_answered=int(_c(Mx.sum(0), "ans").sum()))
    lost = D.boot(Mx, lambda S: float(_c(S, "flag_res").sum() / _c(S, "res_n").sum()) if _c(S, "res_n").sum() > 0 else np.nan)
    out["c_cost"] = dict(overall_resolvable_lost=lost, resolvable_total=int(_c(Mx.sum(0), "res_n").sum()),
                         by_bucket={k: dict(lost=(1 - v["coverage_of_resolvable"][0]) if np.isfinite(v["coverage_of_resolvable"][0]) else np.nan) for k, v in a.items()})
    # (a) passes only if every binding bucket passes
    binding = [v for v in a.values() if v["binding"]]
    out["status_a"] = "PASS" if binding and all(v["status"] == "PASS" for v in binding) else ("FAIL" if binding else "n/a")
    out["status"] = "PASS" if out["status_a"] == "PASS" and out["b_necessity"]["status"] == "PASS" else "FAIL"
    return out


def c4(cells: dict):
    """conditions (season x family x slot) whose C2 status is not PASS must be flagged >= 90% of the time"""
    rows, bad = [], []
    for name, c in cells.items():
        if c["status"] == "PASS":
            continue
        fr = c["flag_rate"]
        ok = np.isfinite(fr) and fr >= 0.90
        rows.append(dict(cell=name, c2=c["status"], flag_rate=fr, answered=c["answered"], episodes=c["n"], ok=bool(ok)))
        if not ok:
            bad.append(name)
    return dict(table=rows, violations=bad, status="PASS" if not bad else "FAIL", n_not_supported=len(rows),
                n_cells=len(cells))


def calibration(D: Data, answered_only=True):
    """reliability diagram of the calibrated confidence: bins 0.5-1.0; class-balanced accuracy per bin; ECE"""
    m = np.isfinite(D.conf) & D.crossed
    if answered_only:
        m &= D.ans
    conf = np.clip(np.maximum(D.conf, 1 - D.conf), 0.5, 1.0)   # conf is already P(correct); guard
    w = np.ones(len(D.rows))
    for c in (True, False):
        k = D.wr == c
        if (m & k).any():
            w[k] = 1.0 / max((m & k).sum(), 1)
    bins = []
    tot = w[m].sum()
    ece = 0.0
    for lo, hi in zip(BINS[:-1], BINS[1:]):
        b = m & (D.conf >= lo) & (D.conf < hi)
        if b.sum() == 0:
            continue
        ww = w[b]
        acc = float((ww * D.ok[b]).sum() / ww.sum())
        mc = float((ww * D.conf[b]).sum() / ww.sum())
        bins.append(dict(lo=lo, hi=min(hi, 1.0), n=int(b.sum()), mean_conf=mc, acc=acc))
        ece += ww.sum() / tot * abs(acc - mc)
    return dict(bins=bins, ece=float(ece) if bins else np.nan, n=int(m.sum()))


# ---------------------------------------------------------------------------------------------- driver
def resolvable_map(rows_new_active: list[dict]) -> dict:
    return {(r["ep"], r["rep"], r["setting"]): bool(r.get("full_answered", False) and r.get("full_correct", False)) for r in rows_new_active if "full_answered" in r}


def evaluate(rows: list[dict], primary_setting: str, nboot: int = 2000, seed: int = 0, layers=None) -> dict:
    """Full C1-C4 evaluation per layer. Criteria are judged on the primary reading-pool setting."""
    layers = layers or sorted({r["layer"] for r in rows})
    res_src = [r for r in rows if r["layer"] == "new" and r["policy"] == "active" and r["setting"] == primary_setting]
    resolvable = resolvable_map(res_src) if res_src else None
    out = {}
    for lay in layers:
        L = [r for r in rows if r["layer"] == lay and r["setting"] == primary_setting]
        Ds = {p: Data([r for r in L if r["policy"] == p], resolvable, nboot, seed) for p in sorted({r["policy"] for r in L})}
        A = Ds["active"]
        c2 = c2_table(A)
        o = dict(policies=sorted(Ds), n_episodes=len(A.rows), n_clusters=len(A.G))
        o["C1"] = c1_table(Ds)
        o["C2"] = c2
        o["C3"] = c3(A)
        o["C4"] = c4(c2["cell"])
        o["calibration_answered"] = calibration(A, True)
        o["calibration_crossed"] = calibration(A, False)
        # per-policy headline (same layer): answered coverage, accuracy among answered, mean readings among answered
        o["by_policy"] = {}
        for p, D in Ds.items():
            Mx = D.M()
            o["by_policy"][p] = dict(coverage=D.boot(Mx, cov_bal), acc=D.boot(Mx, acc_bal),
                                     readings_answered=D.boot(Mx, lambda S: float(np.mean(_c(S, "n_read_ans") / np.maximum(_c(S, "ans"), 1)))))
        o["C2_overall_status"] = c2["all"]["all"]["status"]
        out[lay] = o
    # other settings, informational
    others = sorted({r["setting"] for r in rows} - {primary_setting})
    for st in others:
        for lay in layers:
            L = [r for r in rows if r["layer"] == lay and r["setting"] == st and r["policy"] == "active"]
            if L:
                D = Data(L, None, min(nboot, 500), seed)
                out.setdefault(f"secondary_{st}", {})[lay] = dict(coverage=D.boot(D.M(), cov_bal), acc=D.boot(D.M(), acc_bal))
    return out


# ---------------------------------------------------------------------------------------------- markdown
def _row(*c):
    return "| " + " | ".join(str(x) for x in c) + " |"


def to_markdown(ev: dict, title: str, layers_to_show=None, max_cells=200) -> str:
    L = []
    L.append(f"# {title}\n")
    for lay in (layers_to_show or [k for k in ev if not k.startswith("secondary")]):
        o = ev[lay]
        L.append(f"## Layer `{lay}` ({o['n_episodes']} episodes per policy, {o['n_clusters']} clusters)\n")
        L.append("### Headline per policy (same layer; class-balanced; 95% cluster-bootstrap CI)\n")
        L.append(_row("policy", "answered coverage", "accuracy among answered", "readings among answered"))
        L.append(_row(*["---"] * 4))
        for p, v in o["by_policy"].items():
            L.append(_row(p, fmt(v["coverage"]), fmt(v["acc"]), fmt(v["readings_answered"], 1)))
        L.append("\n### C1 efficiency: readings saved by active vs baseline (paired, among episodes answered by both)\n")
        L.append(_row("baseline", "pairs", "readings saved", "coverage active - base", "status"))
        L.append(_row(*["---"] * 5))
        for b, v in o["C1"].items():
            if v.get("n_pairs", 0) == 0:
                L.append(_row(b, 0, "n/a", "n/a", "n/a"))
            else:
                L.append(_row(b, v["n_pairs"], fmt(v["saved"], 2), fmt(v["cov_diff"]), v["status"]))
        L.append("\n### C2 honest confidence (nominal 0.95; PASS: point>=0.93 and lower>=0.90; cells need >=8 answered and >=5 clusters)\n")
        for dim in ("all", "season", "family", "slot"):
            L.append(_row(dim, "episodes", "answered", "clusters", "accuracy among answered", "coverage", "status"))
            L.append(_row(*["---"] * 7))
            for k, v in o["C2"][dim].items():
                L.append(_row(k, v["n"], v["answered"], v["clusters"], fmt(v["acc"]), fmt(v["coverage"]), v["status"]))
            L.append("")
        cells = o["C2"]["cell"]
        L.append(f"Cells (season x family x slot): {len(cells)}; " + ", ".join(f"{s}: {sum(1 for c in cells.values() if c['status'] == s)}" for s in ("PASS", "INCONCLUSIVE", "FAIL", "insufficient")) + "\n")
        L.append("Calibration (answered verdicts), ECE = %s over n=%d\n" % (("%.3f" % o["calibration_answered"]["ece"]) if np.isfinite(o["calibration_answered"]["ece"]) else "n/a", o["calibration_answered"]["n"]))
        L.append(_row("conf bin", "n", "mean conf", "realised accuracy"))
        L.append(_row(*["---"] * 4))
        for b in o["calibration_answered"]["bins"]:
            L.append(_row(f"[{b['lo']:.2f},{b['hi']:.2f})", b["n"], f"{b['mean_conf']:.3f}", f"{b['acc']:.3f}"))
        L.append("\nCalibration (ALL crossed verdicts, answered or flagged), ECE = %s over n=%d\n" % (("%.3f" % o["calibration_crossed"]["ece"]) if np.isfinite(o["calibration_crossed"]["ece"]) else "n/a", o["calibration_crossed"]["n"]))
        L.append(_row("conf bin", "n", "mean conf", "realised accuracy"))
        L.append(_row(*["---"] * 4))
        for b in o["calibration_crossed"]["bins"]:
            L.append(_row(f"[{b['lo']:.2f},{b['hi']:.2f})", b["n"], f"{b['mean_conf']:.3f}", f"{b['acc']:.3f}"))
        c3_ = o["C3"]
        L.append("\n### C3 precise abstention\n")
        if "a_buckets" in c3_:
            L.append(_row("bucket", "episodes", "resolvable", "share", "coverage of resolvable", "status"))
            L.append(_row(*["---"] * 6))
            for k, v in c3_["a_buckets"].items():
                L.append(_row(k, v["episodes"], v["resolvable"], f"{v['resolvable_share']:.2f}", fmt(v["coverage_of_resolvable"]), v["status"]))
            b = c3_["b_necessity"]
            L.append(f"\n(b) flags carry information: share unresolvable-or-would-be-wrong: flagged {fmt(b['flagged_bad_share'])} vs answered {fmt(b['answered_bad_share'])}; margin {fmt(b['margin'])} -> {b['status']} (flagged n={b['n_flagged']}, answered n={b['n_answered']})")
            L.append(f"\n(c) coverage of resolvable cases lost to flags: {fmt(c3_['c_cost']['overall_resolvable_lost'])} of {c3_['c_cost']['resolvable_total']} resolvable episodes")
            L.append(f"\n**C3 status: {c3_['status']}** (a: {c3_['status_a']})\n")
        c4_ = o["C4"]
        L.append(f"### C4 knows its limits: {c4_['n_not_supported']} of {c4_['n_cells']} conditions are not C2-PASS; violations (flagged < 90%): {len(c4_['violations'])} -> **{c4_['status']}**\n")
        if c4_["table"]:
            L.append(_row("condition (season|family|slot)", "C2", "answered", "episodes", "flag rate", "ok"))
            L.append(_row(*["---"] * 6))
            for r in c4_["table"][:max_cells]:
                L.append(_row(r["cell"], r["c2"], r["answered"], r["episodes"], f"{r['flag_rate']:.2f}", "yes" if r["ok"] else "NO"))
        L.append("")
    return "\n".join(L)


def to_jsonable(x):
    if isinstance(x, dict):
        return {str(k): to_jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [to_jsonable(v) for v in x]
    if isinstance(x, (np.floating, np.integer)):
        return None if (isinstance(x, np.floating) and not np.isfinite(x)) else x.item()
    if isinstance(x, float) and not np.isfinite(x):
        return None
    if isinstance(x, np.bool_):
        return bool(x)
    return x
