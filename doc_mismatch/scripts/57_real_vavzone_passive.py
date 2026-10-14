"""Passive `vav_zone` identifiability on real Mortar buildings (PREREGISTRATION_DR.md Addendum 17). Model-free: nothing is fitted; SEALED data and T1-T6 suites are never touched.

  .venv/bin/python doc_mismatch/scripts/57_real_vavzone_passive.py            # the pre-registered run (results cached: run once)
  .venv/bin/python doc_mismatch/scripts/57_real_vavzone_passive.py --smoke    # plumbing check on a SYNTHETIC world only; reads no Mortar data

Primary buildings bldg8 and bldg30 (all three channels), secondary bldg1 and bldg27 (channel 0 only, descriptive). Input: the frozen exports in data_cache/intake/mortar/.
Output: results/docmismatch/intake/vavzone_passive_report.md (+ a pickle next to it, git-ignored).
"""
import multiprocessing as mp
import pickle
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))
from docmismatch.dr import diagnosability as D  # noqa: E402
from docmismatch.dr import realdata_diag as R  # noqa: E402
from docmismatch.field_pool import build_field_pool  # noqa: E402
from docmismatch.intake import load_export  # noqa: E402

REPO = ROOT.parent
EXPORT = REPO / "data_cache" / "intake" / "mortar"
OUT = REPO / "results" / "docmismatch" / "intake"
PRIMARY, SECONDARY = ["bldg8", "bldg30"], ["bldg1", "bldg27"]
CHANNEL_SETS = {"ch0": (0,), "ch1": (1,), "ch2": (2,), "ch0+ch1": (0, 1), "ch0+ch2": (0, 2), "ch1+ch2": (1, 2), "all3": (0, 1, 2)}
LENGTHS = (3, 7, 14, 28, 42)
N_PERM_DESC = 2000
_G: dict = {}


def chunk_index(fb):
    """per day: (chunk id or -1, day within its chunk); a chunk = a run of days with data (here: one of the two 42-day windows)"""
    a = fb.active_days if fb.active_days is not None else np.ones(-(-fb.n_hours // 24), bool)
    cid, dic, c, k = -np.ones(len(a), int), np.zeros(len(a), int), -1, 0
    for d, act in enumerate(a):
        if act:
            if d == 0 or not a[d - 1]:
                c, k = c + 1, 0
            cid[d], dic[d] = c, k
            k += 1
    return cid, dic


def build(name, alpha, slice_days):
    fb, pairs, _ = _G[name]
    pool = build_field_pool(R.inject_coupling(fb, pairs, alpha), slice_days=slice_days, mask_uninformative=False, require_oat=False)
    sp = pool.slots["vav_zone"]
    E, truth, cands = R.restrict(sp.E, sp.owners, sp.members, pairs)
    return E, truth, cands, pool.field_slice_hours


def task(a):
    name, alpha, slice_days = a
    E, truth, cands, hours = build(name, alpha, slice_days)
    chans = (0, 1, 2) if name in PRIMARY or name.startswith("synthetic") else (0,)
    S = R.score_matrix(E, chans)
    r = R.perm_pvalue(S, truth)
    out = dict(name=name, alpha=alpha, slice_days=slice_days, acc=r["acc"], p=r["p"], n=len(truth), chance=1.0 / len(truth), n_slices=E.shape[0])
    if alpha == 0.0:
        out.update(E=E, truth=truth, cands=cands, hours=hours)
    return out


def describe(name, fb, r0, r_eng):
    """Reported-without-rules statistics of one building from its alpha=0 evidence."""
    E, truth, cands, hours = r0["E"], r0["truth"], r0["cands"], r0["hours"]
    cid, dic = chunk_index(fb)
    days = np.array(hours) // 24
    chunk, dday = cid[days], dic[days]
    chans_all = (0, 1, 2) if name in PRIMARY or name.startswith("synthetic") else (0,)
    out = dict(channel_sets={}, auroc={}, per_window={}, curve={})
    for cname, ch in CHANNEL_SETS.items():
        if not set(ch) <= set(chans_all):
            continue
        S = R.score_matrix(E, ch)
        pv = R.perm_pvalue(S, truth, n_perm=N_PERM_DESC)
        out["channel_sets"][cname] = dict(acc=pv["acc"], p=pv["p"], top3=R.top_k_accuracy(S, truth, 3))
    for k in chans_all:
        ym, yx = D.class_rows(E, truth, cands, k)
        out["auroc"][k] = (D.auroc_x_above_m(ym, yx), D.dprime(ym, yx), len(ym), len(yx))
    S_all = R.score_matrix(E, chans_all)
    out["top3"], out["top1"] = R.top_k_accuracy(S_all, truth, 3), R.rank1_from_scores(S_all, truth)["acc"]
    for c in sorted(set(chunk)):
        idx = np.flatnonzero(chunk == c)
        out["per_window"][int(c)] = dict(n_slices=len(idx), **R.rank1_from_scores(R.score_matrix(E, chans_all, idx), truth))
    for L in LENGTHS:
        idx = np.flatnonzero(dday < L)
        Sl = R.score_matrix(E, chans_all, idx)
        pv = R.perm_pvalue(Sl, truth, n_perm=N_PERM_DESC)
        out["curve"][L] = dict(n_slices=len(idx), acc=pv["acc"], p=pv["p"])
    if r_eng is not None:                                              # the engine-position slices, window-aggregated (comparable to Addendum 11's visit scale)
        Ee, te, ce, he = r_eng["E"], r_eng["truth"], r_eng["cands"], r_eng["hours"]
        grp = cid[np.array(he) // 24]
        w = D.rank1_accuracy(Ee, te, ce, grp, chans_all, pooled=False)
        out["tier1"] = dict(acc=w["acc"], chance=w["chance"], n_units=w["n_units"], n_slices=Ee.shape[0], n_groups=len(set(grp)))
    return out


def analyse(name, fb, pairs, sets):
    primary = name in PRIMARY or name.startswith("synthetic")
    _G[name] = (fb, pairs, sets)
    tasks = [(name, 0.0, "all")] + ([(name, 0.0, "engine")] + [(name, a, "all") for a in R.ALPHAS] if primary else [(name, 0.0, "engine")])
    return tasks


def render(res, gates, prim_names, sec_names, verdict_text):
    md = ["# Passive `vav_zone` identifiability on real Mortar buildings (Addendum 17)", "",
          "Model-free rank-1 identification of which box serves which zone, from the passive channels of Addendum 11 (`evidence.pair_errors`, raw values, three channels), on the pre-registered analysis set "
          "of two 42-day windows per building. Truth = the documented Brick assignment (not field-verified). p = permutation test (10,000 random one-to-one re-assignments, seed 0). Simulation reference "
          "(Addendum 11): window rank-1 0.109-0.143 vs chance 0.123.", "", f"## Verdict: **{verdict_text}**", "", "| gate | passed |", "|---|---|"]
    md += [f"| {g} | {'yes' if ok else '**NO**'} |" for g, ok in gates.items()]
    md += ["", "G1 = score-matrix code reproduces `rank1_accuracy` (1e-12); G2 = >= 8 pairs in each primary building; G3 = injected coupling (alpha = 1.0) recovered with accuracy >= 0.80 in both primary buildings.", "",
           "## Primary statistic (full record, all three channels)", "", "| building | analysis set | audit / series exclusions | rank-1 | chance | permutation p | permutation null (mean / 95th pct) | top-3 | min detectable coupling |", "|---|---|---|---|---|---|---|---|---|"]
    for b in prim_names:
        r = res.get(b)
        if not r:
            continue
        s = r["sets"]
        md.append(f"| {b} | {r['n']} pairs | {len(s['failed_audit'])} / {len(s['failed_series'])} | {r['acc']:.3f} | {r['chance']:.3f} | {r['p']:.4f} | {r['null_mean']:.3f} / {r['null_p95']:.3f} | {r['desc']['top3']:.3f} | "
                  f"{r['min_detectable'] if r['min_detectable'] is not None else 'not reached on the grid'} |")
    md += ["", "## Sensitivity control (coupling injected into the real data; rank-1 / p)", "", "| building | " + " | ".join(f"alpha {a}" for a in (0.0,) + R.ALPHAS) + " |", "|---|" + "---|" * (len(R.ALPHAS) + 1)]
    for b in prim_names:
        r = res.get(b)
        if r:
            md.append(f"| {b} | " + " | ".join(f"{r['inject'][a]['acc']:.3f} / {r['inject'][a]['p']:.4f}" for a in (0.0,) + R.ALPHAS) + " |")
    for b in prim_names + sec_names:
        r = res.get(b)
        if not r:
            continue
        d = r["desc"]
        md += ["", f"## {b} ({'primary' if b in prim_names else 'secondary, channel 0 only, descriptive'}): {r['n']} pairs", ""]
        if r["sets"]["failed_audit"] or r["sets"]["failed_series"]:
            md.append(f"Excluded: {len(r['sets']['failed_audit'])} by the label audit; {len(r['sets']['failed_series'])} by series usability, e.g. " + "; ".join(f"{p[0]} ({why})" for p, why in list(r["sets"]["failed_series"].items())[:4]) + "")
            md.append("")
        md += ["| channels | rank-1 | permutation p (2,000) | top-3 |", "|---|---|---|---|"]
        md += [f"| {c} | {v['acc']:.3f} | {v['p']:.4f} | {v['top3']:.3f} |" for c, v in d["channel_sets"].items()]
        md += ["", "Per-channel AUROC (true pairs have lower error; 0.5 = chance; simulation truth 0.600 / 0.523 / 0.437) and d': " + "; ".join(f"ch{k}: {v[0]:.3f} (d' {v[1]:.2f}; {v[2]} true / {v[3]} alternative readings)" for k, v in d["auroc"].items()), ""]
        if "tier1" in d:
            t = d["tier1"]
            md.append(f"Visit-scale (engine slice positions, window-aggregated, {t['n_slices']} slices in {t['n_groups']} window(s), {t['n_units']} units): rank-1 {t['acc']:.3f} vs chance {t['chance']:.3f}.")
            md.append("")
        md += ["Per window (all days of the window): " + "; ".join(f"window {w}: rank-1 {v['acc']:.3f} over {v['n_slices']} days (chance {v['chance']:.3f})" for w, v in d["per_window"].items()), "",
               "Accuracy against record length (first L days of each window, pooled): " + "; ".join(f"L={L}: {v['acc']:.3f} (p {v['p']:.3f}, {v['n_slices']} days)" for L, v in d["curve"].items()), ""]
    return "\n".join(md)


def main(smoke=False):
    t0 = time.time()
    if smoke:
        from test_realdata_diag import _noise_world
        buildings = {}
        for i, name in enumerate(["synthetic_a", "synthetic_b"]):
            fb, pairs = _noise_world(n=12, days=6, seed=i)
            buildings[name] = (fb, pairs, dict(pairs=pairs, failed_audit=[], failed_series={}))
        prim = list(buildings)
    else:
        cache = OUT / "vavzone_passive.pkl"
        if cache.exists():
            print("results exist; delete", cache, "to recompute (the pre-registered run is meant to be run once)")
            return
        buildings = {}
        for b in PRIMARY + SECONDARY:
            fb = load_export(EXPORT / b)
            labels = R.read_labels(EXPORT / b / "points.csv")
            need = ("flow", "t_dis") if b in PRIMARY else ("flow",)
            sets = R.analysis_set(fb, labels, need)
            buildings[b] = (fb, sets["pairs"], sets)
            print(f"{b}: analysis set {len(sets['pairs'])} pairs; {len(sets['failed_audit'])} failed the audit; {len(sets['failed_series'])} failed series checks", flush=True)
        prim = PRIMARY
    tasks = []
    for name, (fb, pairs, sets) in buildings.items():
        if len(pairs) >= 2:
            tasks += analyse(name, fb, pairs, sets)
    tasks.sort(key=lambda a: -len(buildings[a[0]][1]))                 # biggest buildings first
    with mp.get_context("fork").Pool(min(6, len(tasks))) as pool:
        done = pool.map(task, tasks, chunksize=1)
    print(f"evidence computed {time.time() - t0:.0f}s", flush=True)
    by = {}
    for r in done:
        by.setdefault(r["name"], {})[(r["alpha"], r["slice_days"])] = r
    res = {}
    for name, (fb, pairs, sets) in buildings.items():
        if name not in by:
            continue
        rr = by[name]
        r0 = rr[(0.0, "all")]
        pv = R.perm_pvalue(R.score_matrix(r0["E"], (0, 1, 2) if name in prim or name in PRIMARY else (0,)), r0["truth"])
        g1 = True
        if name in prim or name in PRIMARY:                            # G1: the score-matrix code reproduces rank1_accuracy on this very evidence
            ref = D.rank1_accuracy(r0["E"], r0["truth"], r0["cands"], np.zeros(r0["E"].shape[0], int), (0, 1, 2), pooled=True)["acc"]
            g1 = bool(abs(ref - r0["acc"]) < 1e-12)
        res[name] = dict(n=r0["n"], acc=r0["acc"], p=r0["p"], chance=r0["chance"], null_mean=pv["null_mean"], null_p95=pv["null_p95"], sets=sets, g1=g1,
                         desc=describe(name, fb, r0, rr.get((0.0, "engine"))),
                         inject={a: rr[(a, "all")] for a in (0.0,) + R.ALPHAS if (a, "all") in rr})
        res[name]["inject"] = {a: dict(acc=v["acc"], p=v["p"]) for a, v in res[name]["inject"].items()}
        if res[name]["inject"]:
            res[name]["min_detectable"] = R.min_detectable({a: v for a, v in res[name]["inject"].items() if a > 0})
    pr = {b: res[b] for b in prim if b in res}
    gates = {"G1 code path": all(r["g1"] for r in pr.values()) and len(pr) == len(prim),
             "G2 analysis set >= 8 pairs": all(r["n"] >= R.MIN_PAIRS for r in pr.values()) and len(pr) == len(prim),
             "G3 sensitivity (alpha 1.0 recovered)": all(r["inject"].get(R.GATE_ALPHA, {}).get("acc", 0) >= R.GATE_ACC for r in pr.values()) and len(pr) == len(prim)}
    v = R.verdict({b: dict(acc=r["acc"], p=r["p"]) for b, r in pr.items()}, gates)
    text = render(res, gates, list(prim), [] if smoke else SECONDARY, v)
    if smoke:
        print(text)
        print(f"\nSMOKE OK ({time.time() - t0:.0f}s): synthetic world only; no Mortar data read")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "vavzone_passive_report.md").write_text(text)
    slim = {b: {k: v for k, v in r.items() if k != "sets"} for b, r in res.items()}
    (OUT / "vavzone_passive.pkl").write_bytes(pickle.dumps(dict(res=slim, gates=gates, verdict=v)))
    print(text)


main(smoke="--smoke" in sys.argv)
