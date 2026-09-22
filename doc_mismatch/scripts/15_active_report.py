"""Aggregate the sequential-verification runs (sim + real) into results/docmismatch/active/active_results.md/json.

Stopping is derived post hoc from the never-stopped trajectories: a policy's choices up to step t do not depend on
when it would stop, so 'stop at the first n where P(doc) >= tau or <= 1-tau' is exactly the online rule.
All headline numbers are CLASS-BALANCED (wrong-documentation episodes and correct-documentation episodes weighted equally)
and carry cluster-bootstrap 95% CIs (clusters = benchmark event group / real day).
"""
import json, os, sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.active.engine import channel_cost

OUT = ROOT.parent / "results" / "docmismatch" / "active"
CAP = 24
POLS = ("active", "active_cost", "frozen", "random", "traversal", "rule_based")
RNG = np.random.default_rng(0)
NBOOT = 400


def load(name):
    import pickle
    return [r for r in pickle.load(open(OUT / name, "rb"))]


def stop_idx(traj, tau):
    hit = np.flatnonzero((traj >= tau) | (traj <= 1 - tau))
    return int(hit[0]) if len(hit) else CAP


def derive(r, tau, rho=None):
    t = r["traj"]
    n = stop_idx(t, tau)
    resolved = n < CAP or (t[CAP] >= tau or t[CAP] <= 1 - tau)
    say_correct = t[n] >= 0.5
    if rho is None:
        cost = float(r["cost_traj"][n])
    else:
        cost = float(sum(channel_cost(r["slot"], int(k), rho) for k in r["k_seq"][:n]))
    return dict(n=n, resolved=bool(resolved), ok=bool(say_correct == (not r["wrong"])), cost=cost, wrong=r["wrong"], group=r["group"], ep=r["ep"],
                pw_ok=bool(say_correct != r["wrong"]))


def bal(vals, wrongs):
    """class-balanced mean"""
    v, w = np.asarray(vals, float), np.asarray(wrongs, bool)
    parts = [v[w].mean() if w.any() else np.nan, v[~w].mean() if (~w).any() else np.nan]
    parts = [p for p in parts if not np.isnan(p)]
    return float(np.mean(parts)) if parts else np.nan


def cluster_boot(items, stat, nboot=NBOOT):
    """items: list of dicts with 'group'. stat(list_of_items)->float. Returns (point, lo, hi)."""
    groups = defaultdict(list)
    for it in items:
        groups[it["group"]].append(it)
    keys = list(groups)
    pt = stat(items)
    if len(keys) < 3:
        return pt, np.nan, np.nan
    bs = []
    for _ in range(nboot):
        pick = RNG.integers(0, len(keys), len(keys))
        s = stat([x for i in pick for x in groups[keys[i]]])
        if not np.isnan(s):
            bs.append(s)
    return pt, float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def fmt(t, d=2):
    pt, lo, hi = t
    return f"{pt:.{d}f} [{lo:.{d}f}, {hi:.{d}f}]" if not np.isnan(lo) else f"{pt:.{d}f}"


def select(R, setting, ctx, pol, rho=None, keep=lambda r: True):
    return [r for r in R if not r["unsupported"] and r["setting"] == setting and r["ctx"] == ctx and r["policy"] == pol
            and (rho is None or r.get("rho") == rho) and keep(r)]


def paired(R, setting, ctx, pol_a, pol_b, tau, metric, keep=lambda r: True, rho=None):
    """per-episode difference metric(a) - metric(b), joined on (ep, rep)."""
    A = {(r["ep"], r.get("rep", 0)): r for r in select(R, setting, ctx, pol_a, rho if pol_a == "active_cost" else None, keep)}
    B = {(r["ep"], r.get("rep", 0)): r for r in select(R, setting, ctx, pol_b, rho if pol_b == "active_cost" else None, keep)}
    items = []
    for k in A.keys() & B.keys():
        da, db = derive(A[k], tau), derive(B[k], tau)
        items.append(dict(group=A[k]["group"], wrong=A[k]["wrong"], d=metric(da) - metric(db)))
    return items


def paired_stat(items):
    return bal([i["d"] for i in items], [i["wrong"] for i in items]) if items else np.nan


def table_policies(R, setting, ctx, tau, keep, title):
    lines = [f"**{title}** (tau={tau})", "", "| policy | resolved | readings (cap 24) | readings | resolved | accuracy \\| resolved | forced-verdict accuracy | cost (rho=3) |", "|---|---|---|---|---|---|---|---|"]
    res = {}
    for pol in POLS:
        rows = select(R, setting, ctx, pol, 3.0 if pol == "active_cost" else None, keep)
        if not rows:
            continue
        D = [derive(r, tau, rho=3.0) for r in rows]
        stat = lambda f: (lambda its: bal([f(i) for i in its], [i["wrong"] for i in its]))  # noqa: E731
        n_all = cluster_boot(D, stat(lambda i: i["n"]))
        res_frac = cluster_boot(D, stat(lambda i: i["resolved"]))
        Dr = [d for d in D if d["resolved"]]
        n_res = cluster_boot(Dr, stat(lambda i: i["n"])) if Dr else (np.nan,) * 3
        acc_res = cluster_boot(Dr, stat(lambda i: i["ok"])) if Dr else (np.nan,) * 3
        acc_all = cluster_boot(D, stat(lambda i: i["ok"]))
        cost = cluster_boot(D, stat(lambda i: i["cost"]))
        lines.append(f"| {pol} | {fmt(res_frac)} | {fmt(n_all,1)} | {fmt(n_res,1)} | {len(Dr)}/{len(D)} | {fmt(acc_res)} | {fmt(acc_all)} | {fmt(cost,1)} |")
        res[pol] = dict(readings=n_all, readings_resolved=n_res, resolved=res_frac, acc_resolved=acc_res, acc_forced=acc_all, cost=cost, n=len(D))
    return lines, res


def trajectory_table(R, setting, ctx, keep, title):
    ns = (1, 2, 4, 8, 12, 24)
    lines = [f"**{title}** — verdict accuracy after n readings, no stopping (class-balanced)", "", "| policy | " + " | ".join(f"n={n}" for n in ns) + " |", "|---|" + "---|" * len(ns)]
    for pol in POLS:
        if pol == "active_cost":
            continue
        rows = select(R, setting, ctx, pol, None, keep)
        if not rows:
            continue
        cells = []
        for n in ns:
            ok = [(r["traj"][n] >= 0.5) != r["wrong"] for r in rows]
            cells.append(f"{bal(ok, [r['wrong'] for r in rows]):.2f}")
        lines.append(f"| {pol} | " + " | ".join(cells) + " |")
    return lines


def pareto_table(R, setting, ctx, keep, title):
    lines = [f"**{title}** — readings vs realised error among resolved episodes, by stopping threshold", "", "| policy | " + " | ".join(f"tau={t}: readings / error / resolved" for t in (0.8, 0.9, 0.95, 0.99)) + " |", "|---|---|---|---|---|"]
    for pol in ("active", "frozen", "random", "traversal", "rule_based"):
        rows = select(R, setting, ctx, pol, None, keep)
        cells = []
        for tau in (0.8, 0.9, 0.95, 0.99):
            D = [derive(r, tau) for r in rows]
            Dr = [d for d in D if d["resolved"]]
            w = lambda its, f: bal([f(i) for i in its], [i["wrong"] for i in its])  # noqa: E731
            cells.append(f"{w(D, lambda i: i['n']):.1f} / {1 - w(Dr, lambda i: i['ok']):.2f} / {w(D, lambda i: i['resolved']):.2f}" if Dr else "- / - / 0.00")
        lines.append(f"| {pol} | " + " | ".join(cells) + " |")
    return lines


def context_ablation(R, settings, keep, title, tau=0.95):
    """with-context vs one-pooled-distribution likelihood: same episodes, same policy, paired."""
    lines = [f"**{title}**", "", "| setting | policy | Δ readings (ctx − pooled) | Δ error among resolved | Δ verdict accuracy @8 readings | Δ log-loss @4 readings | Δ log-loss @8 readings |", "|---|---|---|---|---|---|---|"]
    out = {}
    for setting in settings:
        for pol in ("active", "random"):
            A = {(r["ep"], r.get("rep", 0)): r for r in select(R, setting, True, pol, None, keep)}
            B = {(r["ep"], r.get("rep", 0)): r for r in select(R, setting, False, pol, None, keep)}
            ks = A.keys() & B.keys()
            if not ks:
                continue
            def mk(f):
                its = []
                for k in ks:
                    its.append(dict(group=A[k]["group"], wrong=A[k]["wrong"], d=f(A[k]) - f(B[k]), da=A[k], db=B[k]))
                return its
            def ll(r, n):
                p = float(np.clip(r["traj"][n], 1e-4, 1 - 1e-4))
                return -np.log(1 - p if r["wrong"] else p)
            metrics = {
                "readings": lambda r: derive(r, tau)["n"],
                "acc8": lambda r: float((r["traj"][8] >= 0.5) != r["wrong"]),
                "ll4": lambda r: ll(r, 4), "ll8": lambda r: ll(r, 8),
            }
            cells = {}
            for name, f in metrics.items():
                cells[name] = cluster_boot(mk(f), paired_stat)
            # error among resolved: needs both resolved -> use resolved-in-either? use per-arm error rates
            def err_arm(arm):
                its = [derive((A if arm == 0 else B)[k], tau) for k in ks]
                its = [i for i in its if i["resolved"]]
                return its
            e_ctx, e_pool = err_arm(0), err_arm(1)
            gerr = lambda its: 1 - bal([i["ok"] for i in its], [i["wrong"] for i in its]) if its else np.nan  # noqa: E731
            lines.append(f"| {setting} | {pol} | {fmt(cells['readings'],1)} | {gerr(e_ctx):.2f} vs {gerr(e_pool):.2f} | {fmt(cells['acc8'])} | {fmt(cells['ll4'])} | {fmt(cells['ll8'])} |")
            out[f"{setting}|{pol}"] = {k: v for k, v in cells.items()}
    return lines, out


def cost_table(R, setting, keep, tau=0.95):
    lines = ["**Reading-cost sweep** (tier-1 = BAS temperature/point trend; tier-rho = needs a flow/power/energy trend; rho is swept, not measured)", "",
             "| rho | active (EIG) | active_cost (EIG/cost) | random | traversal | active_cost saving vs active |", "|---|---|---|---|---|---|"]
    out = {}
    for rho in (1.0, 3.0, 10.0):
        cells = {}
        for pol in ("active", "active_cost", "random", "traversal"):
            rows = select(R, setting, True, pol, rho if pol == "active_cost" else None, keep)
            D = [derive(r, tau, rho=rho) for r in rows]
            cells[pol] = cluster_boot(D, lambda its: bal([i["cost"] for i in its], [i["wrong"] for i in its])) if D else (np.nan,) * 3
        sav = paired(R, setting, True, "active_cost", "active", tau, lambda d: d["cost"], keep, rho=rho)
        # paired() derives with the run's own rho=None accounting; recompute with rho for both arms
        A = {(r["ep"], r.get("rep", 0)): r for r in select(R, setting, True, "active_cost", rho, keep)}
        B = {(r["ep"], r.get("rep", 0)): r for r in select(R, setting, True, "active", None, keep)}
        its = [dict(group=A[k]["group"], wrong=A[k]["wrong"], d=derive(A[k], tau, rho)["cost"] - derive(B[k], tau, rho)["cost"]) for k in A.keys() & B.keys()]
        lines.append(f"| {rho:g} | {fmt(cells['active'],1)} | {fmt(cells['active_cost'],1)} | {fmt(cells['random'],1)} | {fmt(cells['traversal'],1)} | {fmt(cluster_boot(its, paired_stat),1)} |")
        out[str(rho)] = {k: v for k, v in cells.items()}
    return lines, out


def by_slot(R, setting, ctx, tau, keep):
    lines = ["**By slot** (active vs traversal vs random)", "", "| slot | n episodes | active readings / acc\\|resolved / resolved | traversal | random |", "|---|---|---|---|---|"]
    slots = sorted({r["slot"] for r in select(R, setting, ctx, "active", None, keep)})
    for s in slots:
        cells = []
        n_ep = 0
        for pol in ("active", "traversal", "random"):
            rows = select(R, setting, ctx, pol, None, lambda r, s=s: r["slot"] == s and keep(r))
            D = [derive(r, tau) for r in rows]
            n_ep = len(D)
            Dr = [d for d in D if d["resolved"]]
            w = lambda its, f: bal([f(i) for i in its], [i["wrong"] for i in its])  # noqa: E731
            cells.append(f"{w(D, lambda i: i['n']):.1f} / {(w(Dr, lambda i: i['ok']) if Dr else float('nan')):.2f} / {w(D, lambda i: i['resolved']):.2f}")
        lines.append(f"| {s} | {n_ep} | " + " | ".join(cells) + " |")
    return lines


def main():
    md, js = [f"# Sequential active evidence-gathering — results (context model: {os.environ.get('DM_TAG', 'ctxfull')})", "", "Generated by `scripts/15_active_report.py`. All numbers are class-balanced with cluster-bootstrap 95% CIs (400 resamples).", ""], {}
    TAG = os.environ.get("DM_TAG", "ctxfull")
    sim = load(f"sim_{TAG}.pkl")
    obs = lambda r: r["wrong"] is False or r.get("obs") == "true"  # noqa: E731  hard-observable positives + matched clean edges
    notobs = lambda r: r["wrong"] is False or r.get("obs") in ("false", "ambiguous")  # noqa: E731
    md += ["## SIMULATION (4 topologies, hard-observable cases + matched correct edges; likelihood fitted on the other three topologies)", ""]
    for setting, desc in (("hist", "historian pull: readings from any of 48 day-slices across the year"), ("visit", "site visit: readings limited to one 6-week window's 6 day-slices (season given, not chosen)"),
                          ("visit_loso", "site visit in a season the likelihood was NOT trained on")):
        md += [f"### Setting `{setting}` — {desc}", ""]
        lines, res = table_policies(sim, setting, True, 0.95, obs, f"policies, context-conditioned likelihood, hard-observable")
        md += lines + [""]
        js[f"sim|{setting}|policies"] = res
        md += trajectory_table(sim, setting, True, obs, "accuracy trajectory") + [""]
        md += pareto_table(sim, setting, True, obs, "stopping-threshold trade-off") + [""]
    md += ["### Where it works and where it does not (hist, ctx)", ""] + by_slot(sim, "hist", True, 0.95, obs) + [""]
    md += ["### Hard NOT-observable / ambiguous positives (should NOT reach a confident correct-looking verdict)", ""]
    lines, res = table_policies(sim, "hist", True, 0.95, notobs, "policies on not-observable positives + clean")
    md += lines + [""]
    md += ["## Does conditioning the likelihood on operating context matter? (simulation)", ""]
    lines, res = context_ablation(sim, ("hist", "visit", "visit_loso"), obs, "context-conditioned vs one pooled distribution (paired, hard-observable)")
    md += lines + [""]
    js["sim|ctx_ablation"] = res
    md += ["## Reading cost", ""]
    lines, res = cost_table(sim, "hist", obs)
    md += lines + [""]
    js["sim|cost"] = res

    real = load(f"real_{TAG}.pkl")
    robs = lambda r: r["wrong"] is False or r.get("obs") == "observable"  # noqa: E731
    md += ["## REAL DATA (ORNL RTU-VAV, one research building, 14 days, 4 seasons; injected errors are synthetic swaps of point/zone documentation; truth = dataset naming)", ""]
    for setting, desc in (("lodo", "likelihood excludes only the test day (same-season neighbours remain)"), ("loso", "likelihood excludes the test day's whole season"),
                          ("hist_loso", "readings from every block of the season; likelihood excludes that season")):
        md += [f"### Setting `{setting}` — {desc}", ""]
        lines, res = table_policies(real, setting, True, 0.95, robs, "policies, context-conditioned likelihood, day-level-observable swaps")
        md += lines + [""]
        js[f"real|{setting}|policies"] = res
        md += trajectory_table(real, setting, True, robs, "accuracy trajectory") + [""]
        md += pareto_table(real, setting, True, robs, "stopping-threshold trade-off") + [""]
    md += ["### By slot (real, loso, ctx)", ""] + by_slot(real, "loso", True, 0.95, robs) + [""]
    md += ["## Does conditioning on context matter? (real)", ""]
    lines, res = context_ablation(real, ("lodo", "loso", "hist_loso"), robs, "context-conditioned vs one pooled distribution (paired)")
    md += lines + [""]
    js["real|ctx_ablation"] = res
    (OUT / f"active_results_{TAG}.md").write_text("\n".join(md))
    (OUT / f"active_results_{TAG}.json").write_text(json.dumps(js, default=lambda o: float(o) if isinstance(o, (np.floating, np.integer)) else str(o), indent=1))
    print("\n".join(md))


main()
