"""Can the current channels distinguish the candidates even in principle? (PREREGISTRATION_DR.md Addendum 11)
A model-free diagnosability ladder: per slot and channel, how well do true-owner pairs separate from alternative-owner pairs on
noise-free `truth`, `legacy`, and `estimated` evidence for the 8 EXISTING (train-role) topologies -- plus, for `vav_zone`, the same
metrics on the cached real ORNL DEV pool. Nothing is fitted. Never touches SEALED data or T1-T6 test-suite buildings.
  .venv/bin/python doc_mismatch/scripts/43_structural_diagnosability.py
"""
import pickle
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.active.real_pool import load_or_build_real  # noqa: E402
from docmismatch.data import load_base  # noqa: E402
from docmismatch.dr import diagnosability as D  # noqa: E402
from docmismatch.dr.pools import DR_DIR, sensor_setting  # noqa: E402
from docmismatch.dr.verifier_eval import EXISTING  # noqa: E402

OUT = DR_DIR / "diagnosability"
SLOTS = ["vav_zone", "loop_branch", "branch_coil", "coil_ahu", "ahu_vav"]
LEVELS = D.LEVELS


def fmt(x):
    return f"{x['est']:.3f} [{x['lo']:.3f}, {x['hi']:.3f}]" if x["n"] else "n/a"


def compute(t0):
    res = {}      # (tid, slot, level) -> building_metrics
    for tid in EXISTING:
        base = load_base(tid)
        slots = [s for s in SLOTS if s in base.slot_edges]
        if not slots:
            continue
        sensor = sensor_setting(tid, "estimated")
        evs = {lv: D.level_evidence(base, lv, 0, sensor) for lv in LEVELS}
        for slot in slots:
            owners, members, truth, cands = D.slot_layout(base, slot)
            if not any(len(c) >= 2 for c in cands):
                continue
            for lv in LEVELS:
                E = D.build_E(base, evs[lv], slot)
                res[(tid, slot, lv)] = D.building_metrics(E, truth, cands, D.slice_groups())
        print(f"  {tid}: {slots} done {time.time() - t0:.0f}s", flush=True)

    pool = load_or_build_real()
    sp = pool.slots["vav_zone"]
    truth = np.asarray(sp.truth)
    cands = [list(range(len(sp.owners))) for _ in range(len(sp.members))]
    res[("real_ornl", "vav_zone", "real")] = D.building_metrics(sp.E[:, :3], truth, cands, np.asarray(pool.group))
    return res


def agg(res, slot, level, getter):
    vals = [getter(v) for (t, s, lv), v in res.items() if s == slot and lv == level]
    return D.boot_mean(vals)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    f = OUT / "diagnosability.pkl"
    if f.exists():
        res = pickle.loads(f.read_bytes())
        print("loaded from cache", flush=True)
    else:
        res = compute(t0)
        f.write_bytes(pickle.dumps(res))
        print(f"done {time.time() - t0:.0f}s", flush=True)

    md = ["# Can the current channels distinguish the candidates even in principle? (Addendum 11)", "",
          "Model-free, nothing fitted. 8 `EXISTING` (train-role) topologies, equal weight per building, building-cluster bootstrap 95% CIs (500). "
          "AUROC = P(alternative-owner pair shows a larger error than the true-owner pair): 0.5 chance, 1.0 perfect. "
          "`truth` = noise-free series, `legacy` = original noise, `estimated` = DR real-DEV-estimated telemetry, `real` = cached ORNL DEV pool "
          "(one building; a CI is not available). Simulation-only except the `real` column; hourly reporting throughout.", ""]
    findings = []
    for slot in SLOTS:
        levels = [lv for lv in LEVELS if any(s == slot and l == lv for (_, s, l) in res)]
        if not levels:
            continue
        nb = len({t for (t, s, l) in res if s == slot and l == "truth"})
        has_real = ("real_ornl", slot, "real") in res
        cols = levels + (["real"] if has_real else [])
        md += [f"## {slot}  ({nb} buildings)", "", "### Per-channel AUROC (d' in the second table)", "",
               "| channel | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
        for k in range(3):
            row = [fmt(agg(res, slot, lv, lambda v, k=k: v["auroc"][k])) for lv in levels]
            if has_real:
                a = res[("real_ornl", slot, "real")]["auroc"][k]
                row.append(f"{a:.3f}")
            md.append(f"| ch{k} | " + " | ".join(row) + " |")
        md += ["", "| channel (d') | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
        for k in range(3):
            row = [fmt(agg(res, slot, lv, lambda v, k=k: v["dprime"][k])) for lv in levels]
            if has_real:
                row.append(f"{res[('real_ornl', slot, 'real')]['dprime'][k]:.3f}")
            md.append(f"| ch{k} | " + " | ".join(row) + " |")
        for mode, title in (("rank1_window", "window-aggregated (one 6-slice visit) -- PRIMARY"), ("rank1_pooled", "pooled over all slices -- robustness")):
            md += ["", f"### Rank-1 identification, {title}", "", "| channels | " + " | ".join(cols) + " | chance |", "|---|" + "---|" * (len(cols) + 1)]
            for name in D.CHANNEL_SETS:
                row = [fmt(agg(res, slot, lv, lambda v, name=name: v[mode][name]["acc"])) for lv in levels]
                if has_real:
                    row.append(f"{res[('real_ornl', slot, 'real')][mode][name]['acc']:.3f}")
                ch = agg(res, slot, "truth", lambda v, name=name: v[mode][name]["chance"])
                md.append(f"| {name} | " + " | ".join(row) + f" | {ch['est']:.3f} |")
        md.append("")

        # frozen reading rules (Addendum 11)
        for k in range(3):
            at, ae = (agg(res, slot, "truth", lambda v, k=k: v["auroc"][k])["est"], agg(res, slot, "estimated", lambda v, k=k: v["auroc"][k])["est"])
            if at < 0.60:
                findings.append(f"- {slot} ch{k}: STRUCTURALLY WEAK (AUROC truth {at:.3f} < 0.60)")
            elif at >= 0.75 and ae < at - 0.15:
                findings.append(f"- {slot} ch{k}: TELEMETRY-LIMITED (AUROC truth {at:.3f} -> estimated {ae:.3f})")
        if slot == "vav_zone":
            r_all = agg(res, slot, "truth", lambda v: v["rank1_window"]["all3"]["acc"])["est"]
            r_c1 = agg(res, slot, "truth", lambda v: v["rank1_window"]["ch1"]["acc"])["est"]
            r_all_p = agg(res, slot, "truth", lambda v: v["rank1_pooled"]["all3"]["acc"])["est"]
            r_c1_p = agg(res, slot, "truth", lambda v: v["rank1_pooled"]["ch1"]["acc"])["est"]
            tag = "INSTRUMENTATION-LIMITED" if r_all - r_c1 >= 0.15 else "not instrumentation-limited"
            findings.append(f"- vav_zone: {tag} (window rank-1 truth: all3 {r_all:.3f} vs ch1 {r_c1:.3f}, gap {r_all - r_c1:+.3f}; pooled robustness {r_all_p:.3f} vs {r_c1_p:.3f})")

    md += ["## Frozen reading rules (Addendum 11)", ""] + (findings or ["- no rule triggered"])
    (OUT / "diagnosability_report.md").write_text("\n".join(md))
    print("\n".join(md))


main()
