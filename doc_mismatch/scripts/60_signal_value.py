"""What a missing signal costs, and can a recorded signal or a technician's reading replace it? (PREREGISTRATION_DR.md Addendum 18)
Part A: signal-removal ceilings for four connection types over the 8 `EXISTING` training simulators. Part B: `ahu_vav` box-inlet-temperature substitutes (discharge-temperature proxies and
spot readings) over the 6 simulators with at least two air handlers. Model-free: nothing is fitted. Never touches SEALED data, T1-T6 suites or real data.
  .venv/bin/python doc_mismatch/scripts/60_signal_value.py
The raw results are pickled first; reporting can be re-run from the pickle.
"""
import pickle
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.data import load_base  # noqa: E402
from docmismatch.dr import diagnosability as D  # noqa: E402
from docmismatch.dr import signal_value as S  # noqa: E402
from docmismatch.dr.verifier_eval import EXISTING  # noqa: E402

REPO = ROOT.parent
OUT = REPO / "results/docmismatch/dr/signal_value"
CACHE = REPO / "results/docmismatch/dr/diagnosability/diagnosability.pkl"
CENSUS = REPO / "results/docmismatch/intake/mortar_census.md"
B_ORDER = ["sys03_psz_ac", "vav_2ahu_2loops", "vav_3ahu_2loops", "dev_F", "dev_G", "dev_H"]
A_SLOTS = ["ahu_vav", "loop_branch", "branch_coil", "coil_ahu"]


# ---------------------------------------------------------------------------------------------- computation
def compute_part_a(cache, t0):
    subset, g1 = {s: {} for s in A_SLOTS}, []
    for tid in EXISTING:
        base = load_base(tid)
        evs = D.level_evidence(base, "legacy", 0)
        for slot in A_SLOTS:
            if slot not in base.slot_edges:
                continue
            owners, members, truth, cands = D.slot_layout(base, slot)
            if not any(len(c) >= 2 for c in cands):
                continue
            acc = S.building_subset_acc(D.build_E(base, evs, slot), truth, cands, D.slice_groups())
            subset[slot][tid] = acc
            ref = cache[(tid, slot, "legacy")]["rank1_window"]
            for name, chs in D.CHANNEL_SETS.items():
                a, r = acc[S.SUBSET_INDEX[chs]], ref[name]["acc"]
                g1.append(dict(tid=tid, slot=slot, name=name, mine=float(a), cached=float(r), ok=bool((np.isnan(a) and np.isnan(r)) or abs(a - r) < 1e-9)))
        print(f"  A {tid} {time.time() - t0:.0f}s", flush=True)
    rows = {s: S.part_a_rows(s, np.array(list(subset[s].values())), 500, 0) for s in A_SLOTS}
    return dict(subset=subset, rows=rows, g1=g1)


def compute_part_b(cache, t0):
    blds = {t: S.from_base(t) for t in B_ORDER}
    out = dict(order=B_ORDER, checks={}, g1=[], g2={}, res={v: {} for v in S.VARIANTS}, shares={})
    for bi, tid in enumerate(B_ORDER):
        b = blds[tid]
        out["checks"][tid] = dict(n_owners=len(b.owners), n_boxes=len(b.members), has_reheat=b.reheat is not None, oracle_gap=S.oracle_identity_gap(b),
                                  season_ok=S.season_check(b), oat_window_mean=None if b.oat_window_mean is None else b.oat_window_mean.tolist())
        out["shares"][tid] = {v: S.selection_shares(b, v) for v in ("V1", "V2", "V3", "V4") if v != "V1" or b.reheat is not None}
        ref = cache[(tid, "ahu_vav", "legacy")]["rank1_window"]["ch0"]
        r0 = S.run_variant(b, "V0", bi, 0, offsets=(0.0,))[0.0]["all"]
        out["g1"].append(dict(tid=tid, mine=r0["acc"], cached=float(ref["acc"]), n_mine=r0["n_units"], n_cached=ref["n_units"],
                              ok=bool(abs(r0["acc"] - ref["acc"]) < 1e-9 and r0["n_units"] == ref["n_units"])))
        for vi, v in enumerate(S.VARIANTS):
            if v == "V1" and b.reheat is None:
                continue
            out["res"][v][tid] = S.run_variant(b, v, bi, vi)
            # G2, the null control, at offset 0 (one draw for the spot variants)
            rng = np.random.default_rng([S.BASE_SEED, bi, vi, 99])
            E, win = S.trended_E(b, v, np.zeros(len(b.members))) if v in S.TRENDED else S.spot_E(b, int(v[1:]), np.zeros(len(b.members)), rng)
            out["g2"].setdefault(v, {})[tid] = S.null_control(S.unit_weights(E, b.cands, win), b.truth, S.N_PERM, 0)
        print(f"  B {tid} {time.time() - t0:.0f}s", flush=True)
    return out


def pooled(res_v, tids, s, g):
    with np.errstate(all="ignore"):
        return float(np.nanmean([res_v[t][s][g]["acc"] for t in tids])) if tids else float("nan")


def analyse_b(pb):
    """pooled tables, gates and verdicts from the raw per-building results"""
    res = pb["res"]
    all_t = pb["order"]
    g1_ok = all(r["ok"] for r in pb["g1"])
    out = dict(g1_ok=g1_ok, variants={}, smallest_m={})
    for v in S.VARIANTS:
        tids = [t for t in all_t if t in res[v]]
        g2 = pb["g2"][v]
        g2_acc = float(np.mean([g2[t]["acc"] for t in tids]))
        g2_chance = float(np.mean([g2[t]["chance"] for t in tids]))
        g2_ok = bool(abs(g2_acc - g2_chance) <= S.NULL_TOL)
        pv = {(s, g): pooled(res[v], tids, s, g) for s in S.OFFSETS for g in S.GROUPS}
        pv0 = {(s, g): pooled(res["V0"], tids, s, g) for s in S.OFFSETS for g in S.GROUPS}
        ci = {(s, g): D.boot_mean([res[v][t][s][g]["acc"] for t in tids]) for s in S.OFFSETS for g in S.GROUPS}
        ent = dict(tids=tids, pooled=pv, pooled_v0=pv0, ci=ci, g2=dict(acc=g2_acc, chance=g2_chance, ok=g2_ok))
        if v != "V0":
            ent["eval"] = S.evaluate_variant(pv, pv0, gate_ok=g1_ok and g2_ok)
        out["variants"][v] = ent
    all6 = {(s, g): out["variants"]["V0"]["pooled"][(s, g)] for s in S.OFFSETS for g in S.GROUPS}
    for s in S.OFFSETS:
        out["smallest_m"][s] = S.smallest_m({int(v[1:]): out["variants"][v]["pooled"] for v in S.SPOTS}, all6, s)
    return out


# ---------------------------------------------------------------------------------------------- report
def f2(x):
    return "n/a" if x is None or not np.isfinite(x) else f"{x:.3f}"


def fci(d):
    return "n/a" if not d["n"] else f"{d['est']:.3f} [{d['lo']:.3f}, {d['hi']:.3f}]"


def report(pa, pb, ab):
    census = S.parse_census_measurements(CENSUS.read_text()) if CENSUS.exists() else {}
    L = ["# Signal value and substitutes (Addendum 18)", "",
         "Model-free; nothing fitted. Simulation only (`legacy` evidence, the Addendum 11 seeds). Every building counts equally. CIs are building-cluster bootstrap 95% (500 resamples); with six buildings they are wide, and verdicts use point estimates.", ""]
    # ---- gates
    g1a = all(r["ok"] for r in pa["g1"])
    L += ["## Gates and checks", "",
          f"- **G1 code path (Part A):** {len(pa['g1'])} cached Addendum-11 values (ch0 / ch1 / ch2 / all3 per building and slot) reproduced to 1e-9: **{'PASS' if g1a else 'FAIL'}**"
          + ("" if g1a else " -- mismatches: " + ", ".join(f"{r['tid']}/{r['slot']}/{r['name']}" for r in pa["g1"] if not r["ok"])),
          f"- **G1 code path (Part B):** V0 at offset 0 reproduces the cached `rank1_window['ch0']` (accuracy and unit count) for all {len(pb['g1'])} buildings: **{'PASS' if ab['g1_ok'] else 'FAIL'}**",
          "- **G2 null control** (true owners shuffled among boxes, 200 permutations, offset 0; pooled mean accuracy vs chance; tolerance 0.05):", ""]
    L += ["| variant | shuffled accuracy | chance | verdict |", "|---|---|---|---|"]
    for v in S.VARIANTS:
        g = ab["variants"][v]["g2"]
        L.append(f"| {v} {S.VARIANT_NAMES[v]} | {f2(g['acc'])} | {f2(g['chance'])} | {'PASS' if g['ok'] else 'FAIL'} |")
    L += ["", "- **C1 flow rules read no temperature:** by construction (unit test `test_hour_selection_reads_only_flow_or_reheat`).",
          "- **C2 oracle identity** (largest |t_dis - t_in|, noise-free, over reheat-off hours) and **C4 season labels** (winter windows colder than summer windows by `ENV|oat`):", "",
          "| building | handlers | boxes | reheat series | max abs(t_dis - t_in), reheat off (K) | winter colder than summer | window-mean outdoor temp, windows 0-7 |", "|---|---|---|---|---|---|---|"]
    for t in pb["order"]:
        c = pb["checks"][t]
        gap = "n/a" if c["oracle_gap"] is None else f"{c['oracle_gap']:.4f}"
        oat = "n/a" if c["oat_window_mean"] is None else " ".join(f"{x:.0f}" for x in c["oat_window_mean"])
        L.append(f"| {t} | {c['n_owners']} | {c['n_boxes']} | {'yes' if c['has_reheat'] else 'no'} | {gap} | {c['season_ok']} | {oat} |")
    L += ["", "- **C3 selection shares** (mean share of hours selected / share of (box, slice) readings valid, by season group):", "",
          "| building | rule | " + " | ".join(S.GROUPS) + " |", "|---|---|" + "---|" * len(S.GROUPS)]
    for t in pb["order"]:
        for v, sh in pb["shares"][t].items():
            L.append(f"| {t} | {v} {S.VARIANT_NAMES[v]} | " + " | ".join(f"{sh[g]['hours']:.2f} / {sh[g]['valid']:.2f}" for g in S.GROUPS) + " |")
    # ---- Part A
    L += ["", "## Part A -- which single missing signal costs the most", "",
          "CEILING = best building-mean window rank-1 over the non-empty channel subsets (equal-weight standardised average, Addendum 11's statistic); VALUE = CEILING(all channels) - CEILING(channels that do not read the signal). "
          "CRITICAL = VALUE >= 0.15 or no channel remains; MINOR = VALUE < 0.05. A model-free UPPER BOUND on what the channels can do, not what the engine does. The census column is descriptive only.", ""]
    names = {(0,): "ch0", (1,): "ch1", (2,): "ch2", (0, 1): "ch0+1", (0, 2): "ch0+2", (1, 2): "ch1+2", (0, 1, 2): "all3"}
    for slot in A_SLOTS:
        r = pa["rows"][slot]
        L += [f"### {slot}  ({r['n_buildings']} buildings; ceiling with every signal present {f2(r['ceiling_all'])})", "",
              "Building-mean rank-1 by channel subset: " + ", ".join(f"{names[s]} {f2(r['subset_means'][S.SUBSET_INDEX[s]])}" for s in S.SUBSETS), "",
              "| missing signal | channels left | CEILING left | VALUE lost [95% CI] | label | recorded in the Mortar census |", "|---|---|---|---|---|---|"]
        for row in sorted(r["rows"], key=lambda x: -(x["value"] if x["value"] is not None else 9)):
            who, sig = row["signal"]
            left = "none" if not row["remaining"] else "ch" + "+".join(map(str, row["remaining"]))
            val = "no channel left" if row["value"] is None else f"{row['value']:.3f} [{row['lo']:.3f}, {row['hi']:.3f}]"
            L.append(f"| {'handler/owner' if who == 'o' else 'member'} `{sig}` | {left} | {f2(row['ceiling'])} | {val} | **{row['label']}** | "
                     f"{S.census_availability(slot, row['signal'], census) if census else 'n/a'} |")
        L.append("")
    # ---- Part B
    L += ["## Part B -- can a recorded signal or a technician's reading replace `ahu_vav`'s box inlet temperature?", "",
          "Window-aggregated rank-1 of the ch0 form (mean |box inlet reading + offset - candidate handler supply temperature|), pooled over buildings (V1: the five with a reheat series). "
          f"Season groups: g0 = windows 0-1 (winter), g1 = 2-3, g2 = 4-5 (summer), g3 = 6-7; verdicts use g0 and g2. WORKS = rank-1 >= {S.BAR:.2f} and within {S.TOL:.2f} of V0 at the same offset and season.", "",
          "### Verdicts", "", "| variant | buildings | verdict | tolerated offset s* (K) | works at each offset (0 / 0.25 / 0.5 / 1 / 2) | baseline-limited seasons (same offsets) |", "|---|---|---|---|---|---|"]
    for v in S.VARIANTS[1:]:
        e = ab["variants"][v]["eval"]
        works = " / ".join("yes" if e["works_at"][s] else "no" for s in S.OFFSETS)
        lim = " / ".join(",".join(g for g in S.VERDICT_GROUPS if e["limited"][s][g]) or "-" for s in S.OFFSETS)
        L.append(f"| {v} {S.VARIANT_NAMES[v]} | {len(ab['variants'][v]['tids'])} | **{e['verdict']}** | {'none' if e['s_star'] is None else e['s_star']} | {works} | {lim} |")
    L += ["", "Smallest number of readings per box whose spot variant WORKS at each offset (among 1, 3, 6 and the 24-hour logger):", "",
          "| offset (K) | " + " | ".join(str(s) for s in S.OFFSETS) + " |", "|---|" + "---|" * len(S.OFFSETS),
          "| smallest m | " + " | ".join("none" if ab["smallest_m"][s] is None else str(ab["smallest_m"][s]) for s in S.OFFSETS) + " |", "",
          "### Rank-1 at offset 0 (pooled mean [CI]), all groups", "", "| variant | " + " | ".join(S.GROUPS) + " | chance (all) |", "|---|" + "---|" * (len(S.GROUPS) + 1)]
    for v in S.VARIANTS:
        ent = ab["variants"][v]
        ch = float(np.mean([pb["res"][v][t][0.0]["all"]["chance"] for t in ent["tids"]]))
        L.append(f"| {v} {S.VARIANT_NAMES[v]} | " + " | ".join(fci(ent["ci"][(0.0, g)]) for g in S.GROUPS) + f" | {ch:.3f} |")
    for g, label in (("g0", "winter (windows 0-1)"), ("g2", "summer (windows 4-5)")):
        L += ["", f"### Rank-1 by offset, {label} (pooled mean)", "", "| variant | " + " | ".join(f"{s} K" for s in S.OFFSETS) + " |", "|---|" + "---|" * len(S.OFFSETS)]
        for v in S.VARIANTS:
            L.append(f"| {v} {S.VARIANT_NAMES[v]} | " + " | ".join(f2(ab["variants"][v]["pooled"][(s, g)]) for s in S.OFFSETS) + " |")
    L += ["", "### Per building (all windows), offset 0 and 0.5 K", "", "| building | variant | 0 K | 0.5 K | units scored at 0 K | units skipped at 0 K |", "|---|---|---|---|---|---|"]
    for t in pb["order"]:
        for v in S.VARIANTS:
            if t in pb["res"][v]:
                a0, a5 = pb["res"][v][t][0.0]["all"], pb["res"][v][t][0.5]["all"]
                L.append(f"| {t} | {v} | {f2(a0['acc'])} | {f2(a5['acc'])} | {a0['n_units']:.0f} | {a0['n_skipped']:.0f} |")
    L += ["", "Chance is the mean of 1/|candidates| over the scored units; ties count 1/#tied. `sys03_psz_ac` is ten one-box packaged units (no reheat series, so no V1). "
          "The simulator's ducts are adiabatic and instantaneous (the true pair's noise-free ch0 error is zero), so V0 is optimistic and V1 is close to it by construction."]
    return "\n".join(L)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    cache = pickle.loads(CACHE.read_bytes())
    f = OUT / "signal_value.pkl"
    if f.exists():
        raw = pickle.loads(f.read_bytes())
        print("loaded from cache", flush=True)
    else:
        raw = dict(a=compute_part_a(cache, t0), b=compute_part_b(cache, t0))
        f.write_bytes(pickle.dumps(raw))
        print(f"computed {time.time() - t0:.0f}s", flush=True)
    ab = analyse_b(raw["b"])
    (OUT / "signal_value_report.md").write_text(report(raw["a"], raw["b"], ab))
    print(f"report written {time.time() - t0:.0f}s")
    print("G1(A) pass:", all(r["ok"] for r in raw["a"]["g1"]), "| G1(B) pass:", ab["g1_ok"], "| G2:", {v: ab["variants"][v]["g2"]["ok"] for v in S.VARIANTS})
    for v in S.VARIANTS[1:]:
        e = ab["variants"][v]["eval"]
        print(f"  {v} {S.VARIANT_NAMES[v]:24s} {e['verdict']:10s} s*={e['s_star']}")


if __name__ == "__main__":
    main()
