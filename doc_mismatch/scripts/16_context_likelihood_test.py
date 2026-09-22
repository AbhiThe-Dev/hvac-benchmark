"""Policy-independent test: does conditioning the reading likelihood on operating context predict held-out readings better?

For each held-out unit (sim: topology, likelihood fitted on the others; real: season, fitted on the other seasons) and each
(slot, channel, class), compare the mean held-out log density of the readings under the context-conditioned model vs ONE pooled
distribution. Positive delta = context helps. Cluster bootstrap over pairs (readings of one pair are not independent).
"""
import json, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.active.model import fit_channel, tf, SD_FLOOR
from docmismatch.active.pools import compatible, load_or_build_sim
from docmismatch.active.real_pool import load_or_build_real

TOPOS = ["sys03_psz_ac", "sys07_vav_reheat", "vav_2ahu_2loops", "vav_3ahu_2loops"]
RNG = np.random.default_rng(1)


def logpdf(y, mu, v):
    return -0.5 * (np.log(2 * np.pi * v) + (y - mu) ** 2 / v)


def heldout_rows(pool, mask, slot, k):
    sp = pool.slots.get(slot)
    if sp is None:
        return None
    idx = np.where(mask)[0]
    out = []
    gid = 0
    for m in range(len(sp.members)):
        t = sp.truth[m]
        for o in range(len(sp.owners)):
            if o != t and not compatible(sp, o, t):
                continue
            v = sp.E[idx, k, o, m]
            f = np.isfinite(v)
            if f.any():
                out.append((tf(v[f]), pool.ctx[idx][f], np.full(f.sum(), 0 if o == t else 1), np.full(f.sum(), gid)))
            gid += 1
    if not out:
        return None
    return tuple(np.concatenate([o[i] for o in out]) for i in range(4))


def evaluate(train_pools, train_masks, test_pool, test_mask, slot, k, mode=True):
    rows = heldout_rows(test_pool, test_mask, slot, k)
    m1 = fit_channel(train_pools, slot, k, mode, train_masks)
    m0 = fit_channel(train_pools, slot, k, False, train_masks)
    if rows is None or m1 is None or m0 is None:
        return None
    y, c, z, g = rows
    res = {}
    for zi, zn in ((0, "M"), (1, "X")):
        s = z == zi
        if s.sum() < 20:
            continue
        ll = []
        for mod in (m1, m0):
            mm, sm, mx, sx, _ = mod.params(c[s])
            mu, sd = (mm, sm) if zn == "M" else (mx, sx)
            tau = mod.fit[zn].tau
            ll.append(logpdf(y[s], mu, sd ** 2 + tau ** 2))
        d = ll[0] - ll[1]
        res[zn] = (d, g[s])
    return res


def boot(items):
    d = np.concatenate([i[0] for i in items]); g = np.concatenate([i[1] + 100000 * n for n, i in enumerate(items)])
    ug = np.unique(g)
    sums = {u: (d[g == u].sum(), (g == u).sum()) for u in ug}
    pt = d.mean()
    bs = []
    for _ in range(300):
        pick = RNG.choice(ug, len(ug))
        s = sum(sums[u][0] for u in pick); n = sum(sums[u][1] for u in pick)
        bs.append(s / n)
    return float(pt), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)), int(len(d))


def summarize(per, label, lines, out):
    allitems = []
    for (slot, zn), items in sorted(per.items()):
        b = boot(items); out[f"{label}|{slot}|{zn}"] = b; allitems += items
        lines.append(f"| {label} | {slot} | {zn} | {b[0]:+.3f} [{b[1]:+.3f}, {b[2]:+.3f}] | {b[3]} |")
    b = boot(allitems); out[f"{label}|ALL"] = b
    lines.append(f"| **{label}** | **all** | **both** | **{b[0]:+.3f} [{b[1]:+.3f}, {b[2]:+.3f}]** | {b[3]} |")


def main():
    out, lines = {}, ["| data / context model | slot | class | mean Δ held-out log-density per reading (ctx − pooled) [95% CI] | n readings |", "|---|---|---|---|---|"]
    rp = load_or_build_real()
    for mode in (True, "mean", "oat"):
        tag = {True: "full", "mean": "mean-only", "oat": "OAT-only"}[mode]
        per_x, per_w, per_r = {}, {}, {}
        for test in TOPOS:
            tp = load_or_build_sim(test, 0)
            train = [load_or_build_sim(t, r) for t in TOPOS if t != test for r in (0, 1)]
            tm = [np.ones(p.n_slices, bool) for p in train]
            same = load_or_build_sim(test, 1)
            for slot in tp.slots:
                for k in range(3):
                    r = evaluate(train, tm, tp, np.ones(tp.n_slices, bool), slot, k, mode)
                    for zn, v in (r or {}).items():
                        per_x.setdefault((slot, zn), []).append(v)
                    for sn in range(4):   # SAME building (other noise draw), held-out season
                        r = evaluate([same], [same.season != sn], tp, tp.season == sn, slot, k, mode)
                        for zn, v in (r or {}).items():
                            per_w.setdefault((slot, zn), []).append(v)
        for s in range(4):
            for slot in rp.slots:
                for k in range(3):
                    r = evaluate([rp], [rp.season != s], rp, rp.season == s, slot, k, mode)
                    for zn, v in (r or {}).items():
                        per_r.setdefault((slot, zn), []).append(v)
        summarize(per_x, f"sim cross-building (LOTO) [{tag}]", lines, out)
        summarize(per_w, f"sim same-building, held-out season [{tag}]", lines, out)
        summarize(per_r, f"real, held-out season [{tag}]", lines, out)
    (ROOT.parent / "results" / "docmismatch" / "active" / "context_likelihood_test.md").write_text("\n".join(lines))
    (ROOT.parent / "results" / "docmismatch" / "active" / "context_likelihood_test.json").write_text(json.dumps(out, indent=1))
    print("\n".join(l for l in lines if "**" in l))


main()
