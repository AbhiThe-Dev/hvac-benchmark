"""BEFORE/AFTER report for the selection/model fix (real + simulation), paired on the same episodes.

Usage: 13_selection_report.py OLD_TAG NEW_TAG [--ablation TAG1,TAG2,...]
Reads results/docmismatch/active/{sim,real}_<tag>.pkl (records written by scripts 12 / 14; OLD = original run, NEW = DM_SEL run) and writes
results/docmismatch/active/selection/selection_results.{md,json}.
Same conventions as 15_active_report.py: class-balanced (wrong-documentation and correct-documentation episodes weighted equally), 95%
cluster-bootstrap CIs (clusters = event group / real day-slot, 400 resamples), stopping derived post hoc from never-stopped trajectories,
sim = hard-observable positives + matched correct edges, real = day-level-observable swaps + all correct edges.
"""
import json, pickle, sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / "results" / "docmismatch" / "active"
SELDIR = OUT / "selection"
CAP = 24
NS = (1, 2, 4, 8, 12, 24)
RNG = np.random.default_rng(0)
NBOOT = 400
TAU = 0.95


def load(kind, tag):
    f = OUT / f"{kind}_{tag}.pkl"
    return pickle.load(open(f if f.exists() else SELDIR / f"{kind}_{tag}.pkl", "rb"))


def stop_idx(traj, tau):
    hit = np.flatnonzero((traj >= tau) | (traj <= 1 - tau))
    return int(hit[0]) if len(hit) else CAP


def derive(r, tau=TAU):
    t = r["traj"]
    n = stop_idx(t, tau)
    resolved = n < CAP or (t[CAP] >= tau or t[CAP] <= 1 - tau)
    return dict(n=n, resolved=bool(resolved), ok=bool((t[n] >= 0.5) == (not r["wrong"])), wrong=r["wrong"], group=r["group"])


def bal(vals, wrongs):
    v, w = np.asarray(vals, float), np.asarray(wrongs, bool)
    parts = [v[w].mean() if w.any() else np.nan, v[~w].mean() if (~w).any() else np.nan]
    parts = [p for p in parts if not np.isnan(p)]
    return float(np.mean(parts)) if parts else np.nan


def cluster_boot(items, stat, nboot=NBOOT):
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
    if np.isnan(pt):
        return "n/a"
    return f"{pt:.{d}f} [{lo:.{d}f}, {hi:.{d}f}]" if not np.isnan(lo) else f"{pt:.{d}f}"


def select(R, setting, ctx, pol, keep):
    return [r for r in R if not r["unsupported"] and r["setting"] == setting and r["ctx"] == ctx and r["policy"] == pol and keep(r)]


def key(r):
    return (r["ep"], r.get("rep", 0))


def wstat(f):
    return lambda its: bal([f(i) for i in its], [i["wrong"] for i in its])


def row_metrics(rows, with_ci=True):
    """resolved fraction, mean readings (cap 24), readings among resolved, accuracy among resolved, and forced accuracy at NS."""
    D = [derive(r) for r in rows]
    Dr = [d for d in D if d["resolved"]]
    ci = cluster_boot if with_ci else (lambda its, st: (st(its), np.nan, np.nan))
    out = dict(resolved=ci(D, wstat(lambda i: i["resolved"])), readings=ci(D, wstat(lambda i: i["n"])),
               readings_resolved=ci(Dr, wstat(lambda i: i["n"])) if Dr else (np.nan,) * 3,
               acc_resolved=ci(Dr, wstat(lambda i: i["ok"])) if Dr else (np.nan,) * 3, n_resolved=len(Dr), n=len(D))
    for n in NS:
        its = [dict(group=r["group"], wrong=r["wrong"], ok=bool((r["traj"][n] >= 0.5) == (not r["wrong"]))) for r in rows]
        out[f"acc{n}"] = ci(its, wstat(lambda i: i["ok"]))
    return out


def paired(A_rows, B_rows, f):
    """per-episode f(a) - f(b), joined on (ep, rep)."""
    A, B = {key(r): r for r in A_rows}, {key(r): r for r in B_rows}
    return [dict(group=A[k]["group"], wrong=A[k]["wrong"], d=f(A[k]) - f(B[k])) for k in A.keys() & B.keys()]


pstat = lambda its: bal([i["d"] for i in its], [i["wrong"] for i in its]) if its else np.nan  # noqa: E731


def acc_at(n):
    return lambda r: float((r["traj"][n] >= 0.5) == (not r["wrong"]))


def main_table(title, groups, settings, keep, lines, js, kind):
    """groups: list of (label, records, ctx, policy)."""
    for setting in settings:
        lines += [f"### {kind} / `{setting}`  ({title})", "",
                  "| arm | resolved | readings (cap 24) | readings among resolved | acc among resolved (nominal 0.95) | " + " | ".join(f"acc n={n}" for n in NS) + " |",
                  "|---|---|---|---|---|" + "---|" * len(NS)]
        for label, R, ctx, pol in groups:
            rows = select(R, setting, ctx, pol, keep)
            if not rows:
                continue
            m = row_metrics(rows)
            js[f"{kind}|{setting}|{label}"] = {k: v for k, v in m.items()}
            lines.append(f"| {label} | {fmt(m['resolved'])} | {fmt(m['readings'],1)} | {fmt(m['readings_resolved'],1)} ({m['n_resolved']}/{m['n']}) | {fmt(m['acc_resolved'])} | " + " | ".join(fmt(m[f'acc{n}']) for n in NS) + " |")
        lines.append("")


def paired_table(kind, setting, keep, comps, lines, js):
    """comps: list of (label, rowsA, rowsB)."""
    lines += [f"**{kind} / `{setting}` paired differences (A minus B), same episodes**", "",
              "| A vs B | forced acc n=1 | n=2 | n=4 | n=8 | n=12 | n=24 | readings (cap 24) | resolved |", "|---|---|---|---|---|---|---|---|---|"]
    for label, A, B in comps:
        if not A or not B:
            continue
        cells = [fmt(cluster_boot(paired(A, B, acc_at(n)), pstat)) for n in NS]
        cells += [fmt(cluster_boot(paired(A, B, lambda r: derive(r)["n"]), pstat), 1), fmt(cluster_boot(paired(A, B, lambda r: float(derive(r)["resolved"])), pstat))]
        js[f"{kind}|{setting}|paired|{label}"] = cells
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    lines.append("")


def main():
    old_tag, new_tag = sys.argv[1], sys.argv[2]
    SELDIR.mkdir(exist_ok=True)
    lines, js = [f"# Active selection fix: BEFORE (`{old_tag}`) vs AFTER (`{new_tag}`)", "",
                 "Generated by `scripts/13_selection_report.py`. Class-balanced; 95% cluster-bootstrap CIs (400 resamples); tau=0.95; stopping derived post hoc.", ""], {}
    for kind, settings, keep in (("real", ("lodo", "loso", "hist_loso"), lambda r: r["wrong"] is False or r.get("obs") == "observable"),
                                 ("sim", ("hist", "visit", "visit_loso"), lambda r: r["wrong"] is False or r.get("obs") == "true")):
        old, new = load(kind, old_tag), load(kind, new_tag)
        lines += [f"## {kind.upper()}", ""]
        groups = [("active BEFORE", old, True, "active"), ("**active AFTER**", new, True, "active"),
                  ("random BEFORE", old, True, "random"), ("random AFTER", new, True, "random"),
                  ("random_info AFTER (random over readings predicted informative)", new, True, "random_info"),
                  ("frozen BEFORE", old, True, "frozen"), ("frozen AFTER", new, True, "frozen"),
                  ("traversal BEFORE", old, True, "traversal"), ("traversal AFTER", new, True, "traversal"),
                  ("rule_based BEFORE", old, True, "rule_based"), ("rule_based AFTER", new, True, "rule_based")]
        main_table("context-conditioned likelihood; hard-observable", groups, settings, keep, lines, js, kind)
        for setting in settings:
            g = lambda R, pol, ctx=True: select(R, setting, ctx, pol, keep)  # noqa: E731
            comps = [("active BEFORE vs random BEFORE", g(old, "active"), g(old, "random")),
                     ("active AFTER vs random AFTER", g(new, "active"), g(new, "random")),
                     ("active AFTER vs random_info AFTER", g(new, "active"), g(new, "random_info")),
                     ("active AFTER vs traversal AFTER", g(new, "active"), g(new, "traversal")),
                     ("active AFTER vs frozen AFTER", g(new, "active"), g(new, "frozen")),
                     ("active AFTER vs active BEFORE", g(new, "active"), g(old, "active")),
                     ("random AFTER vs random BEFORE (model effect alone)", g(new, "random"), g(old, "random")),
                     ("pooled-context arm: active AFTER vs active BEFORE", g(new, "active", False), g(old, "active", False))]
            paired_table(kind, setting, keep, comps, lines, js)
    # ---- where the real deficit sits: by held-out season (point estimates; fall = 8 of 14 days)
    old, new = load("real", old_tag), load("real", new_tag)
    robs = lambda r: r["wrong"] is False or r.get("obs") == "observable"  # noqa: E731
    lines += ["## REAL: by season of the test day (point estimates, class-balanced within season; wrong-documentation episodes per season in brackets)", "",
              "| setting | season | arm | " + " | ".join(f"acc n={n}" for n in NS) + " |", "|---|---|---|" + "---|" * len(NS)]
    for setting in ("loso", "hist_loso"):
        for sname, sid in (("fall", 0), ("spring", 1), ("summer", 2), ("winter", 3)):
            for label, R, pol in (("active BEFORE", old, "active"), ("active AFTER", new, "active"), ("random", new, "random"), ("rule_based", new, "rule_based")):
                rows = [r for r in select(R, setting, True, pol, robs) if r["season"] == sid]
                w = [r["wrong"] for r in rows]
                if not rows or not any(w) or all(w):
                    continue
                lines.append(f"| {setting} | {sname} ({sum(w)}) | {label} | " + " | ".join(f"{bal([(r['traj'][n] >= 0.5) == (not r['wrong']) for r in rows], w):.2f}" for n in NS) + " |")
    lines.append("")
    # ---- ablations (descriptive: the components were designed before the runs, but nothing here is a held-out selection)
    if "--ablation" in sys.argv:
        tags = sys.argv[sys.argv.index("--ablation") + 1].split(",")
        for kind, settings, keep in (("real", ("lodo", "loso", "hist_loso"), robs), ("sim", ("hist", "visit"), lambda r: r["wrong"] is False or r.get("obs") == "true")):
            lines += [f"## ABLATION ({kind}, active policy, context-conditioned likelihood; same episodes)", "",
                      "| setting | variant | resolved | readings among resolved | acc among resolved | acc n=1 | n=4 | n=8 | n=24 |", "|---|---|---|---|---|---|---|---|---|"]
            for setting in settings:
                for tag in [old_tag] + tags + [new_tag]:
                    try:
                        R = load(kind, tag)
                    except FileNotFoundError:
                        continue
                    rows = select(R, setting, True, "active", keep)
                    if not rows:
                        continue
                    m = row_metrics(rows)
                    lines.append(f"| {setting} | {tag} | {fmt(m['resolved'])} | {fmt(m['readings_resolved'],1)} | {fmt(m['acc_resolved'])} | " + " | ".join(fmt(m[f'acc{n}']) for n in (1, 4, 8, 24)) + " |")
            lines.append("")
    (SELDIR / "selection_results.md").write_text("\n".join(lines))
    (SELDIR / "selection_results.json").write_text(json.dumps(js, default=lambda o: float(o) if isinstance(o, (np.floating, np.integer)) else str(o), indent=1))
    print("\n".join(lines))


main()
