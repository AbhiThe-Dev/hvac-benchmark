"""Abstention / tiered-output evaluation for the sequential verifier (before vs after), simulation + real data.

Usage: 17_active_abstain.py [--sim sim_oat.pkl] [--real real_oat.pkl] [--tag oat] [--policies active,random,...] [--nboot 1000]
                            [--target 0.90] [--min-cov 0.10] [--max-flips 1] [--rebuild-inner] [--ctx oat] [--workers 8]
Works on any pickle with the format of sim_oat.pkl / real_oat.pkl in results/docmismatch/active/. Outputs to
results/docmismatch/active/abstention/abstention_<tag>.{md,json}.

Leakage control: the rule for held-out unit O (a topology in simulation; a season in real data) is fitted ONLY on inner
leave-one-unit-out verification runs on the other units (docmismatch.active.nested), never on O's outcomes, the benchmark
`obs` label or the `wrong` flag of O. `obs`, `wrong`, `slot` names are used for evaluation/reporting only.
The inner runs are cached in abstention/inner_<tag>_{sim,real}.pkl.
"""
import argparse, json, pickle, sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.active.abstain import (CONFIRMED, LOW_CONFIDENCE, REFUTED, UNRESOLVED_BUDGET, UNRESOLVED_NO_POWER, AbstentionRule, episode_features, nested_select)

GOAL = 0.95
FIXED = None
ACT = ROOT.parent / "results" / "docmismatch" / "active"
OUT = ACT / "abstention"
CAP = 24
OBS_NORM = {"true": "observable", "observable": "observable", "false": "unobservable", "unobservable": "unobservable", "ambiguous": "ambiguous", "n/a": "n/a"}
COLS = ("n", "cb", "okb", "ca", "oka", "flag", "lost", "catch", "badb", "bada", "nopower")
CI = {c: i for i, c in enumerate(COLS)}


# ---------------------------------------------------------------------------------------------- annotate
def annotate(records, rules, inner_policies, tau):
    """One row per outer record: before (plain stopping rule at tau) and after (abstention rule) outcomes."""
    rows = []
    for r in records:
        if r["unsupported"] or not r["ctx"] or r["policy"] in (None, "active_cost"):
            continue
        unit = r["topo"] if "topo" in r else r["season"]
        pol = r["policy"] if r["policy"] in inner_policies else "active"
        rule = rules.get((unit, pol))
        f = episode_features(r["traj"], tau)
        ok_b = f["crossed"] and f["say_correct"] == (not r["wrong"])
        d = rule.decide(r["slot"], r["traj"]) if rule is not None else None
        conf_a = d is not None and d.state in (CONFIRMED, REFUTED)
        rows.append(dict(setting=r["setting"], policy=r["policy"], slot=r["slot"], wrong=bool(r["wrong"]), obs=OBS_NORM.get(r.get("obs", "n/a"), "n/a"), group=r["group"],
                         unit=unit, cb=f["crossed"], okb=bool(ok_b), ca=conf_a, oka=bool(conf_a and d.say_correct == (not r["wrong"])), state=d.state if d else None, n=f["n"], ep=r["ep"]))
    return rows


def suff(rows):
    """per-group sufficient statistics: (G, 2 classes [wrong, right], len(COLS))"""
    g = defaultdict(lambda: np.zeros((2, len(COLS))))
    for x in rows:
        a = g[x["group"]][0 if x["wrong"] else 1]
        a[CI["n"]] += 1
        a[CI["cb"]] += x["cb"]; a[CI["okb"]] += x["okb"]; a[CI["ca"]] += x["ca"]; a[CI["oka"]] += x["oka"]
        a[CI["flag"]] += x["cb"] and not x["ca"]
        a[CI["lost"]] += x["okb"] and not x["ca"]
        a[CI["badb"]] += x["cb"] and not x["okb"]
        a[CI["bada"]] += x["ca"] and not x["oka"]
        a[CI["catch"]] += x["cb"] and not x["okb"] and not x["ca"]
        a[CI["nopower"]] += x["state"] == UNRESOLVED_NO_POWER
    return np.array(list(g.values())) if g else np.zeros((0, 2, len(COLS)))


def _bal(num, den):
    with np.errstate(invalid="ignore", divide="ignore"):
        v = num / den
    return np.nanmean(v, axis=-1) if np.isfinite(v).any() else np.nan


def metrics(S):
    """S: (..., 2, C) summed stats -> dict of metrics (class-balanced unless noted)."""
    c = lambda k: S[..., CI[k]]  # noqa: E731
    with np.errstate(invalid="ignore", divide="ignore"):
        bal = lambda a, b: np.nanmean(np.where(c(b) > 0, c(a) / np.maximum(c(b), 1), np.nan), axis=-1)  # noqa: E731
        pool = lambda a, b: c(a).sum(-1) / np.where(c(b).sum(-1) > 0, c(b).sum(-1), np.nan)  # noqa: E731
        prec = lambda a, b: (c(a) / np.where(c("n") > 0, c("n"), np.nan)).sum(-1) / (c(b) / np.where(c("n") > 0, c("n"), np.nan)).sum(-1)  # noqa: E731  prior-balanced P(verdict right | confident)
        return dict(prec_b=prec("okb", "cb"), prec_a=prec("oka", "ca"), cov_b=bal("cb", "n"), acc_b=bal("okb", "cb"), cov_a=bal("ca", "n"), acc_a=bal("oka", "ca"), flag=bal("flag", "n"),
                    lost=pool("lost", "okb"), caught=pool("catch", "badb"),
                    cw_pos_b=c("badb")[..., 0] / np.where(c("n")[..., 0] > 0, c("n")[..., 0], np.nan), cw_pos_a=c("bada")[..., 0] / np.where(c("n")[..., 0] > 0, c("n")[..., 0], np.nan),
                    cw_neg_b=c("badb")[..., 1] / np.where(c("n")[..., 1] > 0, c("n")[..., 1], np.nan), cw_neg_a=c("bada")[..., 1] / np.where(c("n")[..., 1] > 0, c("n")[..., 1], np.nan),
                    n=c("n").sum(-1))


def boot(rows, nboot, rng):
    """point estimates + cluster-bootstrap 95% CI per metric."""
    S = suff(rows)
    if len(S) == 0:
        return None
    pt = metrics(S.sum(0))
    if len(S) < 3:
        return {k: (float(v), np.nan, np.nan) for k, v in pt.items()}
    counts = rng.multinomial(len(S), np.full(len(S), 1 / len(S)), size=nboot)
    B = metrics(np.einsum("bg,gcx->bcx", counts, S))
    out = {}
    for k, v in pt.items():
        b = B[k][np.isfinite(B[k])]
        out[k] = (float(v), float(np.percentile(b, 2.5)) if len(b) > 20 else np.nan, float(np.percentile(b, 97.5)) if len(b) > 20 else np.nan)
    return out


def f(t, d=2):
    pt, lo, hi = t
    if pt is None or np.isnan(pt):
        return "-"
    return f"{pt:.{d}f} [{lo:.{d}f}, {hi:.{d}f}]" if not np.isnan(lo) else f"{pt:.{d}f}"


# ---------------------------------------------------------------------------------------------- populations
def populations(kind):
    if kind == "sim":
        return {"hard-observable + correct edges": lambda x: (not x["wrong"]) or x["obs"] == "observable",
                "NOT-observable/ambiguous positives + correct edges": lambda x: (not x["wrong"]) or x["obs"] in ("unobservable", "ambiguous")}
    return {"day-level-observable swaps + correct edges": lambda x: (not x["wrong"]) or x["obs"] == "observable",
            "unobservable/ambiguous swaps + correct edges": lambda x: (not x["wrong"]) or x["obs"] in ("unobservable", "ambiguous"),
            "all swaps + correct edges": lambda x: True}


_SEL = {}


def fit_rules(inner, units, policies, tau, target=None, goal=0.95, **kw):
    """Rule per (held-out unit, policy) from that unit's TRAINING records. target=None -> (target, by_sign) chosen by
    nested leave-one-training-unit-out selection (largest coverage whose nested accuracy among confident >= goal);
    a numeric target overrides the target only (by_sign still nested-selected)."""
    rules = {}
    for u in units:
        for p in policies:
            recs = [r for r in inner if r["outer"] == u and r["policy"] == p]
            if not recs:
                continue
            key = (id(inner), u, p, tau, goal, tuple(sorted(kw.items())))
            if key not in _SEL:
                _SEL[key] = nested_select(recs, p, tau=tau, goal=goal, **kw)
            sel = _SEL[key]
            rules[(u, p)] = AbstentionRule(tau=tau, target=sel["target"] if target is None else target, by_sign=sel["by_sign"], **kw).fit(recs)
            rules[(u, p)].selection = sel
    return rules


# ---------------------------------------------------------------------------------------------- report
def report(kind, R, inner, settings, pols, tau, kw, nboot, md, js, main_pol="active"):
    rng = np.random.default_rng(0)
    units = sorted({(r["topo"] if "topo" in r else r["season"]) for r in R if not r["unsupported"]})
    inner_pols = sorted({r["policy"] for r in inner})
    rules = fit_rules(inner, units, inner_pols, tau, target=FIXED, goal=GOAL, **kw)
    rows_all = annotate(R, rules, inner_pols, tau)
    pops = populations(kind)
    md.append(f"## {kind.upper()}")
    md.append("")
    # --- training-side reliability estimates (what the rule learned), per outer unit
    md.append(f"### What the rule learned from TRAINING units ({main_pol}); per held-out unit: slot coverage / cell reliability (acc, n_eff clusters, lower bound)")
    md.append("")
    md.append("Nested selection per held-out unit (target, cell-by-sign?) with goal accuracy %.2f: " % GOAL + "; ".join(f"{u}: target={rules[(u, main_pol)].selection['target']}, by_sign={rules[(u, main_pol)].selection['by_sign']} (nested cov {rules[(u, main_pol)].selection['cv_cov']:.2f}, acc {rules[(u, main_pol)].selection['cv_acc']:.2f}, worst slot {rules[(u, main_pol)].selection['cv_worst_slot']:.2f})" for u in units if (u, main_pol) in rules))
    md.append("")
    md.append("| held-out unit | slot | train coverage | confirm-cell acc (n_eff, LB) | refute-cell acc (n_eff, LB) | slot declined a priori |")
    md.append("|---|---|---|---|---|---|")
    for u in units:
        rl = rules.get((u, main_pol))
        if rl is None:
            continue
        for s in sorted(rl.cov):
            c1, c0 = (rl.cells.get((s, True)), rl.cells.get((s, False))) if rl.by_sign else (rl.cells.get((s, None)),) * 2
            fc = lambda c: f"{c['acc']:.2f} ({c['n_eff']}, {c['lb']:.2f})" if c else "n/a"  # noqa: E731
            md.append(f"| {u} | {s} | {rl.cov[s]:.2f} | {fc(c1)} | {fc(c0)} | {'yes' if rl.cov[s] < rl.min_cov else ''} |")
    md.append("")
    js[f"{kind}|selection"] = {f"{u}|{p}": {k: v for k, v in rl.selection.items() if k != "table"} for (u, p), rl in rules.items()}
    js[f"{kind}|rule_cells"] = {f"{u}|{s}": {"cov": rl.cov[s], "confirm": rl.cells.get((s, True)), "refute": rl.cells.get((s, False))} for u in units for rl in [rules.get((u, main_pol))] if rl for s in rl.cov}

    for setting in settings:
        rows = [x for x in rows_all if x["setting"] == setting]
        if not rows:
            continue
        md += [f"### Setting `{setting}`", ""]
        # headline: per policy per population
        md += ["**Before vs after, per policy and population** (tau=%.2f; before = plain stopping rule; after = abstention rule). Class-balanced, 95%% cluster-bootstrap CI." % tau, "",
               "| population | policy | coverage before | acc among confident BEFORE (recall-style / precision) | coverage after | acc among confident AFTER (recall-style / precision) | flagged instead of answered | confident-correct now flagged (price) | confident-wrong now flagged (caught) | confident-wrong rate on positives before -> after | false-alarm rate on correct edges before -> after |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        for pn, pf in pops.items():
            for p in pols:
                sub = [x for x in rows if x["policy"] == p and pf(x)]
                m = boot(sub, nboot, rng)
                if m is None:
                    continue
                js[f"{kind}|{setting}|{pn}|{p}"] = m
                md.append(f"| {pn} | {p} | {f(m['cov_b'])} | {f(m['acc_b'])} / {f(m['prec_b'])} | {f(m['cov_a'])} | {f(m['acc_a'])} / {f(m['prec_a'])} | {f(m['flag'])} | {f(m['lost'])} | {f(m['caught'])} | {f(m['cw_pos_b'])} -> {f(m['cw_pos_a'])} | {f(m['cw_neg_b'])} -> {f(m['cw_neg_a'])} |")
        md.append("")
        # by slot (main policy; all populations combined = observable + not observable = all positives + clean)
        md += [f"**By slot ({main_pol})**: all positives (any observability) + correct edges. For the sim, 'hard-observable' rows are broken out separately below.", "",
               "| slot | episodes | coverage before | acc BEFORE (recall-style / precision) | coverage after | acc AFTER (recall-style / precision) | flagged | declined a priori (frac) | price (conf-correct flagged) | caught (conf-wrong flagged) |", "|---|---|---|---|---|---|---|---|---|---|"]
        for s in sorted({x["slot"] for x in rows}):
            sub = [x for x in rows if x["policy"] == main_pol and x["slot"] == s]
            m = boot(sub, nboot, rng)
            if m is None:
                continue
            npw = np.mean([x["state"] == UNRESOLVED_NO_POWER for x in sub])
            js[f"{kind}|{setting}|slot={s}|{main_pol}"] = m
            md.append(f"| {s} | {len(sub)} | {f(m['cov_b'])} | {f(m['acc_b'])} / {f(m['prec_b'])} | {f(m['cov_a'])} | {f(m['acc_a'])} / {f(m['prec_a'])} | {f(m['flag'])} | {npw:.2f} | {f(m['lost'])} | {f(m['caught'])} |")
        md.append("")
        # by observability class
        md += [f"**By observability class ({main_pol})**: positives of that class only (correct edges excluded), so 'confident-wrong' = confident 'documentation is correct' on a wrong edge, or refuted with the right owner never occurs here.", "",
               "| observability | positives | resolved before | confident-wrong before | resolved after | confident-wrong after | flagged | acc among confident before -> after | of correctly-resolved-before, now flagged (price) |", "|---|---|---|---|---|---|---|---|---|"]
        for oc in ("observable", "unobservable", "ambiguous"):
            sub = [x for x in rows if x["policy"] == main_pol and x["wrong"] and x["obs"] == oc]
            if not sub:
                continue
            S = suff(sub).sum(0)[0]
            ci = boot_pos(sub, nboot, rng)
            md.append(f"| {oc} | {len(sub)} | {ci['cb']} | {ci['badb']} | {ci['ca']} | {ci['bada']} | {ci['flag']} | {ci['accb']} -> {ci['acca']} | {ci['lost']} |")
        md.append("")
        # tiers
        md += [f"**Output tiers ({main_pol}), all episodes, unweighted counts**", "", "| population | " + " | ".join((CONFIRMED, REFUTED, LOW_CONFIDENCE, UNRESOLVED_NO_POWER, UNRESOLVED_BUDGET)) + " |", "|---|---|---|---|---|---|"]
        for pn, pf in pops.items():
            sub = [x for x in rows if x["policy"] == main_pol and pf(x)]
            if not sub:
                continue
            md.append(f"| {pn} | " + " | ".join(f"{np.mean([x['state'] == st for x in sub]):.2f}" for st in (CONFIRMED, REFUTED, LOW_CONFIDENCE, UNRESOLVED_NO_POWER, UNRESOLVED_BUDGET)) + " |")
        md.append("")
        # curve
        for pop in list(pops.items())[:2]:
            md += curve(kind, R, inner, setting, main_pol, tau, kw, nboot, rng, js, pop)
    return rules


def boot_pos(sub, nboot, rng):
    S = suff(sub)
    pt = S.sum(0)[0]
    def mk(S_):
        n = S_[..., CI["n"]]
        return {k: S_[..., CI[k]] / np.maximum(n, 1) for k in ("cb", "badb", "ca", "bada", "flag")} | {"lost": S_[..., CI["lost"]] / np.maximum(S_[..., CI["okb"]], 1)} | {"accb": S_[..., CI["okb"]] / np.maximum(S_[..., CI["cb"]], 1), "acca": S_[..., CI["oka"]] / np.maximum(S_[..., CI["ca"]], 1)}
    P = mk(pt)
    counts = rng.multinomial(len(S), np.full(len(S), 1 / len(S)), size=nboot)
    B = mk(np.einsum("bg,gcx->bcx", counts, S)[:, 0, :]) if len(S) >= 3 else None
    out = {}
    for k in P:
        out[k] = f"{float(P[k]):.2f} [{np.percentile(B[k], 2.5):.2f}, {np.percentile(B[k], 97.5):.2f}]" if B is not None else f"{float(P[k]):.2f}"
    return out


def curve(kind, R, inner, setting, pol, tau, kw, nboot, rng, js, pop):
    """coverage vs confident accuracy as the abstention target varies, and as tau (plain stopping threshold) varies."""
    pn, pf = pop
    units = sorted({(r["topo"] if "topo" in r else r["season"]) for r in R if not r["unsupported"]})
    inner_pols = sorted({r["policy"] for r in inner})
    lines = [f"**Operating-point curve ({pol}, population: {pn}).** Left: abstention target (fixed tau={tau}). Right: no abstention, just a stricter stopping threshold tau (plain baseline).", "",
             "| abstention target | coverage | acc (recall-style / precision) | flagged | | tau only | coverage | acc (recall-style / precision) |", "|---|---|---|---|---|---|---|---|"]
    tg = [0.0, 0.5, 0.7, 0.8, 0.85, 0.9, 0.93, 0.95, 0.97, 0.99]
    tt = [0.8, 0.9, 0.95, 0.99, 0.999, 0.9999]
    cu = {"target": {}, "tau": {}}
    rows_t = []
    for t in tg:
        rules = fit_rules(inner, units, [pol] if pol in inner_pols else ["active"], tau, target=t, goal=GOAL, **kw)
        rows = [x for x in annotate(R, rules, inner_pols, tau) if x["setting"] == setting and x["policy"] == pol and pf(x)]
        m = boot(rows, max(nboot // 4, 100), rng)
        cu["target"][t] = m
        rows_t.append(m)
    rows_u = []
    for t in tt:
        rules = fit_rules(inner, units, [pol] if pol in inner_pols else ["active"], t, goal=GOAL, **kw)
        rows = [x for x in annotate(R, rules, inner_pols, t) if x["setting"] == setting and x["policy"] == pol and pf(x)]
        m = boot(rows, max(nboot // 4, 100), rng)
        cu["tau"][t] = m
        rows_u.append(m)
    for i in range(max(len(tg), len(tt))):
        a = f"{tg[i]:.2f} | {f(rows_t[i]['cov_a'])} | {f(rows_t[i]['acc_a'])} / {f(rows_t[i]['prec_a'])} | {f(rows_t[i]['flag'])}" if i < len(tg) and rows_t[i] else " | | | "
        b = f"{tt[i]} | {f(rows_u[i]['cov_b'])} | {f(rows_u[i]['acc_b'])} / {f(rows_u[i]['prec_b'])}" if i < len(tt) and rows_u[i] else " | | "
        lines.append(f"| {a} | | {b} |")
    lines.append("")
    js[f"{kind}|{setting}|curve|{pol}|{pn}"] = cu
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim", default="sim_oat.pkl"); ap.add_argument("--real", default="real_oat.pkl"); ap.add_argument("--tag", default="oat")
    ap.add_argument("--policies", default=None); ap.add_argument("--nboot", type=int, default=1000)
    ap.add_argument("--goal", type=float, default=0.95); ap.add_argument("--fixed-target", type=float, default=None); ap.add_argument("--min-cov", type=float, default=0.10); ap.add_argument("--max-flips", type=int, default=1)
    ap.add_argument("--q", type=float, default=0.50); ap.add_argument("--tau", type=float, default=0.95)
    ap.add_argument("--rebuild-inner", action="store_true"); ap.add_argument("--ctx", default="oat"); ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    global GOAL, FIXED
    FIXED = a.fixed_target
    GOAL = a.goal
    OUT.mkdir(exist_ok=True)
    sim = pickle.load(open(ACT / a.sim, "rb")) if a.sim != "none" else None
    real = pickle.load(open(ACT / a.real, "rb")) if a.real != "none" else None
    from docmismatch.active.engine import POLICIES
    seen = sorted({r["policy"] for R in (sim, real) if R for r in R if r["policy"] and r["policy"] != "active_cost"})
    pols = a.policies.split(",") if a.policies else seen
    inner_pols = [p for p in seen if p in POLICIES]
    ci_s, ci_r = OUT / f"inner_{a.tag}_sim.pkl", OUT / f"inner_{a.tag}_real.pkl"
    if a.rebuild_inner or not ((sim is None or ci_s.exists()) and (real is None or ci_r.exists())):
        from docmismatch.active.nested import run_inner_all
        isim, ireal = run_inner_all(sim, real, inner_pols or ["active"], ctx=a.ctx, workers=a.workers)
        if sim is not None: ci_s.write_bytes(pickle.dumps(isim))
        if real is not None: ci_r.write_bytes(pickle.dumps(ireal))
    kw = dict(q=a.q, min_cov=a.min_cov, max_flips=a.max_flips)
    md = [f"# Abstention / tiered output ({a.tag}) — generated by scripts/17_active_abstain.py", "",
          f"Rule parameters: {kw}, tau={a.tau}. Rule fitted on nested TRAINING runs only (see module docstrings). Pickles: sim={a.sim}, real={a.real}.", ""]
    js = {"params": kw | {"tau": a.tau}}
    if sim is not None:
        report("sim", sim, pickle.load(open(ci_s, "rb")), ("hist", "visit", "visit_loso"), pols, a.tau, kw, a.nboot, md, js)
    if real is not None:
        report("real", real, pickle.load(open(ci_r, "rb")), ("lodo", "loso", "hist_loso"), pols, a.tau, kw, a.nboot, md, js)
    (OUT / f"abstention_{a.tag}.md").write_text("\n".join(md))
    (OUT / f"abstention_{a.tag}.json").write_text(json.dumps(js, default=lambda o: float(o) if isinstance(o, (np.floating, np.integer)) else (list(o) if isinstance(o, tuple) else str(o)), indent=1))
    print("\n".join(md))


if __name__ == "__main__":
    main()
