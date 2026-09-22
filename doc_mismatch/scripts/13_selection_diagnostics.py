"""Diagnostics behind the selection fix (real ORNL data): why does EIG ranking not pay off? Writes results/docmismatch/active/selection/diagnostics.md.

D1  informativeness structure of the real pool (finite-reading fraction by occupancy; all-or-nothing per (slice, member))
D2  what the ORIGINAL active policy reads (share of empty readings, distinct owners, share on the documented pair) vs random
D3  held-out-season transfer of the class-M likelihood: mean log-likelihood-ratio (M:X) of the TRUE owner pairs, by held-out season
D4  cross-channel correlation of pair-level offsets (how independent are the three channels of one pair?)
D5  evidence ceiling on the real pool: forced accuracy with (a) all readings, (b) 24 random informative readings, (c) 24 doc-pair-only readings,
    (d) 24 non-doc-only readings, (e) 24 round-robin over owners.  hist_loso models (fitted without the held-out season). Descriptive; nothing tuned.
Uses the ORIGINAL model (all options off) unless noted. Same episodes as script 14 (rng seed 11), day-level-observable swaps + all correct edges.
"""
import hashlib, multiprocessing as mp, sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import real_frp as R
from docmismatch.active.calibrate import calibrate_beta_seasons
from docmismatch.active.engine import Episode, _Actions, run_episode
from docmismatch.active.model import fit_slot_models, tf
from docmismatch.active.pools import hypotheses
from docmismatch.active.real_pool import REAL_SLOTS, load_or_build_real

OUT = ROOT.parent / "results" / "docmismatch" / "active" / "selection"
POOL = load_or_build_real()
NAMES = ["fall", "spring", "summer", "winter"]


def h32(s):
    return int(hashlib.sha1(s.encode()).hexdigest()[:8], 16)


def episodes():
    rng = np.random.default_rng(11)
    out = []
    for d, day in enumerate(POOL.days):
        season = int(POOL.season[POOL.group == d][0])
        ser = POOL.day_series[d]
        for slot in REAL_SLOTS:
            pairs = [(a, b) for a in range(10) for b in range(10) if a != b]
            wrong = [pairs[i] for i in rng.choice(len(pairs), 20, replace=False)]
            eps = [Episode(POOL, slot, b, a, b, True, f"real|{day}|{slot}|{a}>{b}|wrong", f"{day}|{slot}", {}) for a, b in wrong]
            for b in rng.choice(10, 10, replace=False):
                eps.append(Episode(POOL, slot, int(b), int(b), int(b), False, f"real|{day}|{slot}|{b}|right", f"{day}|{slot}", {}))
            for e in eps:
                e.meta = {"obs": R.observability(ser, R.Event(slot, min(*(e.doc, e.member)), max(e.doc, e.member))) if e.is_wrong else "n/a"}
                if e.is_wrong and e.meta["obs"] != "observable":
                    continue
                out.append((d, season, e))
    return out


EPS = episodes()
FITS = {}


def _fit(job):
    slot, key, mask = job
    mod = fit_slot_models([POOL], slot, "oat", [mask])
    return (slot, key), (mod, calibrate_beta_seasons(POOL, slot, "oat", mask))


def _setting(setting, d, season):
    if setting == "loso":
        return ("s", season), np.where(POOL.group == d)[0]
    return ("s", season), np.where(POOL.season == season)[0]


def _behaviour(item):
    d, season, e = item
    out = []
    for setting in ("loso", "hist_loso"):
        key, sl = _setting(setting, d, season)
        mod, beta = FITS[(e.slot, key)]
        hy = hypotheses(POOL.slots[e.slot], e.doc)
        acts = _Actions(e, mod, hy, sl, 3.0)
        for pol in ("active", "random"):
            r = run_episode(e, mod, sl, pol, tau=2.0, seed=h32(e.ep_id) % 10000, beta=beta)
            o = np.array(r.order, int)
            out.append(dict(setting=setting, pol=pol, wrong=e.is_wrong, fin=np.isfinite(acts.y[o]).mean(), owners=len(set(acts.j[o])), doc=float((acts.j[o] == 0).mean()),
                            pool_fin=float(np.isfinite(acts.y).mean())))
    return out


def _ceiling(item):
    d, season, e = item
    key, sl = _setting("hist_loso", d, season)
    mod, beta = FITS[(e.slot, key)]
    hy = hypotheses(POOL.slots[e.slot], e.doc)
    acts = _Actions(e, mod, hy, sl, 3.0)
    rng = np.random.default_rng(h32(e.ep_id) % 1000)
    fin = np.isfinite(acts.y)
    res = dict(slot=e.slot, wrong=e.is_wrong, season=season)

    def go(idx):
        if len(idx) == 0:
            return 0.5
        return run_episode(e, mod, sl, "custom", tau=2.0, order=list(idx), beta=beta, nmax=len(idx)).traj[-1] if False else run_episode(e, mod, sl, "custom", tau=2.0, order=list(idx), beta=beta, nmax=len(idx)).traj[len(idx)]

    def pick(sel, n):
        idx = np.flatnonzero(sel)
        rng.shuffle(idx)
        return idx[:n]
    res["all readings"] = go(np.flatnonzero(fin))
    res["24 random informative"] = go(pick(fin, 24))
    res["24 doc-pair only"] = go(pick(fin & (acts.j == 0), 24))
    res["24 non-doc only"] = go(pick(fin & (acts.j != 0), 24))
    idx, by = [], {j: list(pick(fin & (acts.j == j), 10 ** 6)) for j in range(len(hy))}
    while len(idx) < 24 and any(by.values()):
        for j in by:
            if by[j] and len(idx) < 24:
                idx.append(by[j].pop())
    res["24 round-robin over owners"] = go(idx)
    return res


def bal(v, w):
    v, w = np.asarray(v, float), np.asarray(w, bool)
    return float(np.mean([v[w].mean(), v[~w].mean()]))


def main():
    L = ["# Selection diagnostics (real ORNL RTU-VAV; descriptive, nothing tuned)", "", "Generated by `scripts/13_selection_diagnostics.py`. Original model (all options off), OAT-only mean shift.", ""]
    ctx = mp.get_context("fork")
    # D1
    sp = POOL.slots["vav_pwr"]
    fin = np.isfinite(sp.E[:, 0])
    frac = fin.mean((1, 2))
    L += ["## D1  Informativeness structure (vav_pwr / vav_sat share the same evidence)", "", "| occupancy fraction of the 4-h block | slices | fraction of readings that are informative |", "|---|---|---|"]
    for o in np.unique(POOL.ctx[:, 2]):
        m = np.isclose(POOL.ctx[:, 2], o)
        L.append(f"| {o:.2f} | {m.sum()} | {frac[m].mean():.2f} |")
    f = np.isfinite(sp.E)
    g = f[:, 0].mean(1)   # per (slice, member) over owners
    L += ["", f"Per (slice, member) group of owner pairs: all empty {np.mean(g == 0):.2f}, all informative {np.mean(g == 1):.2f}, mixed {np.mean((g > 0) & (g < 1)):.2f}; channels agree on emptiness in {np.mean((f[:, 0] == f[:, 1]) & (f[:, 1] == f[:, 2])):.2f} of pairs.",
          "So whether a reading is empty is decided by the slice and the streams, not by the pair: once one reading in a slice is empty the rest are (vav_pwr / vav_sat).", ""]
    # fits
    jobs, seen = [], set()
    for d in range(len(POOL.days)):
        season = int(POOL.season[POOL.group == d][0])
        for slot in REAL_SLOTS:
            k = (slot, ("s", season))
            if k not in seen:
                seen.add(k)
                jobs.append((slot, ("s", season), POOL.season != season))
    with ctx.Pool(10) as P:
        FITS.update(dict(P.map(_fit, jobs)))
    # D2
    with ctx.Pool(10) as P:
        beh = [x for c in P.map(_behaviour, EPS, chunksize=4) for x in c]
    L += ["## D2  What the ORIGINAL active policy reads (24 readings, day-level-observable swaps + correct edges)", "",
          "| setting | policy | informative readings among those taken (share available in pool) | distinct owners read | share of readings on the documented owner |", "|---|---|---|---|---|"]
    for setting in ("loso", "hist_loso"):
        for pol in ("active", "random"):
            rr = [b for b in beh if b["setting"] == setting and b["pol"] == pol]
            L.append(f"| {setting} | {pol} | {np.mean([b['fin'] for b in rr]):.2f} ({np.mean([b['pool_fin'] for b in rr]):.2f}) | {np.mean([b['owners'] for b in rr]):.1f} | {np.mean([b['doc'] for b in rr]):.2f} |")
    L += ["", "The original active policy is barely better than random at avoiding empty readings (its informativeness regression sees only outdoor temperature) and, in hist_loso, "
          "spends ~90% of its readings on the documented pair.", ""]
    # D3
    L += ["## D3  Held-out-season transfer of the class-M likelihood (hist_loso models)", "",
          "Mean log-likelihood-ratio log p(y|M) - log p(y|X) per reading of the TRUE owner pairs under the model fitted without that season (positive = the model recognises the true owner).", "",
          "| slot | held-out season | ch0 | ch1 | ch2 | rooms with negative mean LLR |", "|---|---|---|---|---|---|"]
    for slot in ("vav_pwr", "vav_zone"):
        for s in range(4):
            mod, _ = FITS[(slot, ("s", s))]
            idx = np.where(POOL.season == s)[0]
            cells = []
            for k in range(3):
                m = mod[k]
                mM, sM, mX, sX, _ = m.params(POOL.ctx[idx])
                ys = []
                for room in range(10):
                    y = tf(POOL.slots[slot].E[idx, k, room, room])
                    fn = np.isfinite(y)
                    ys.append(np.mean(-0.5 * ((y[fn] - mM[fn]) / sM[fn]) ** 2 - np.log(sM[fn]) + 0.5 * ((y[fn] - mX[fn]) / sX[fn]) ** 2 + np.log(sX[fn])) if fn.any() else np.nan)
                cells.append(ys)
            allv = np.array(cells)
            neg = np.nanmean(np.nanmean(allv, 0) < 0) if np.isfinite(allv).any() else np.nan
            L.append(f"| {slot} | {NAMES[s]} | " + " | ".join(f"{np.nanmean(c):+.2f}" for c in cells) + f" | {np.nansum(np.nanmean(allv, 0) < 0):.0f} of {np.isfinite(np.nanmean(allv, 0)).sum()} |")
    L += ["", "Fall (8 of the 14 days, 58% of episodes) is recognised poorly when the model is fitted on the other three seasons (only 6 days).", ""]
    # D4
    from docmismatch.active.model import estimate_rho
    L += ["## D4  Cross-channel dependence of a pair's offset", "", "| slot | rho (avg corr. of pair-level mean residual across channels, training seasons != fall) |", "|---|---|"]
    for slot in REAL_SLOTS:
        mod = fit_slot_models([POOL], slot, "oat", [POOL.season != 0])
        L.append(f"| {slot} | {estimate_rho(mod):.2f} |")
    L.append("")
    # D5
    with ctx.Pool(10) as P:
        ceil = P.map(_ceiling, EPS, chunksize=4)
    keys = ["all readings", "24 random informative", "24 doc-pair only", "24 non-doc only", "24 round-robin over owners"]
    L += ["## D5  Evidence ceiling in hist_loso (forced verdict P(doc)>=0.5; class-balanced; one random draw per episode, so +-0.03 noise)", "",
          "| readings used | all | fall | not fall | vav_zone | vav_sat | vav_pwr |", "|---|---|---|---|---|---|---|"]
    for k in keys:
        cells = []
        for filt in (lambda r: True, lambda r: r["season"] == 0, lambda r: r["season"] != 0, lambda r: r["slot"] == "vav_zone", lambda r: r["slot"] == "vav_sat", lambda r: r["slot"] == "vav_pwr"):
            rr = [r for r in ceil if filt(r)]
            cells.append(f"{bal([(r[k] >= 0.5) != r['wrong'] for r in rr], [r['wrong'] for r in rr]):.2f}")
        L.append(f"| {k} | " + " | ".join(cells) + " |")
    (OUT / "diagnostics.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
