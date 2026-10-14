"""Addendum 16, Part A: measured operating characteristics of a technician-style single-box override test (PREREGISTRATION_DR.md Addendum 16).
Nothing is fitted except the leave-one-building-out threshold rule; never touches SEALED data, T1-T6 suites or real data.
  .venv/bin/python doc_mismatch/scripts/52_override_eval.py
Reads the runs of scripts/51 (test-order seeds 1-3).
"""
import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import evidence as EV  # noqa: E402
from docmismatch.data import load_base  # noqa: E402
from docmismatch.dr import diagnosability as D  # noqa: E402
from docmismatch.dr import override_eval as O  # noqa: E402
from docmismatch.dr.pools import build_pool  # noqa: E402

RUNS = ROOT.parent / "results" / "docmismatch" / "perturbation" / "overrides"
OUT = ROOT.parent / "results" / "docmismatch" / "perturbation"
BUILDINGS = ["sys07_vav_reheat", "vav_2ahu_2loops", "vav_3ahu_2loops", "dev_E", "dev_F", "dev_G", "dev_H"]
SEASONS = ["july", "january"]
SEEDS = (1, 2, 3)
KINDS = ("full_cool", "close", "flow_only")
NOISES = ["none", "legacy", "harsh"]
N_DRAWS = 20
PRIMARY_D = 60


def load_run(kind, season, seed, tid):
    b = load_base(tid, RUNS / kind / season / f"seed{seed}")
    plan = json.loads((RUNS / kind / season / f"seed{seed}" / tid / "tests.json").read_text())["plan"]
    zones, vavs = sorted(b.ids("Zone")), sorted(b.ids("VAV"))
    own = {o: m for o, m in b.slot_edges["vav_zone"]}
    T = np.stack([b.ev[f"{z}|temp10"] for z in zones])
    return dict(b=b, plan=plan, zones=zones, vavs=vavs, own=own, T=T, n_boxes=len(vavs))


def code_path_checks():
    """series length and, for every `close` run, the shifted zero-flow window"""
    bad, n_runs = [], 0
    for kind in KINDS:
        for season in SEASONS:
            for s in SEEDS:
                for tid in BUILDINGS:
                    r = load_run(kind, season, s, tid)
                    n_runs += 1
                    if r["T"].shape[1] != (2 + r["n_boxes"]) * 144:
                        bad.append(("steps", kind, season, s, tid, r["T"].shape[1]))
                    if kind == "close":     # the box flow is zero in exactly the two hours of the shifted window, non-zero just before and just after
                        for t in r["plan"]:
                            f = r["b"].ev[f"{t['vav']}|flow"]
                            h = t["day"] * 24 + O.actual_start_hour(t["start_hour"], season)
                            if not (f[h] <= 1e-9 and f[h + 1] <= 1e-9 and f[h - 1] > 1e-9 and f[h + 2] > 1e-9):
                                bad.append(("window", kind, season, s, tid, t["vav"]))
    return n_runs, bad


def truth_check_against_pools():
    old = EV.MASK_CHANNELS
    EV.MASK_CHANNELS = True
    try:
        pools = {t: build_pool(t, 0, None) for t in BUILDINGS}
    finally:
        EV.MASK_CHANNELS = old
    bad = []
    for tid in BUILDINGS:
        r = load_run("full_cool", "july", SEEDS[0], tid)
        zone_of = {o: m for o, m in r["own"].items()}
        sp = pools[tid].slots["vav_zone"]
        for mi, mem in enumerate(sp.members):
            if zone_of.get(sp.owners[int(sp.truth[mi])]) != mem:
                bad.append((tid, mem))
    return bad


def compute(t0):
    res = dict(metric={}, scores={})
    for kind in KINDS:
        for season in SEASONS:
            for tid in BUILDINGS:
                acc = {}                                                         # (D, noise, method) -> lists of top1 / auroc
                pos = {(d, nz): [] for d in O.DURATIONS_MIN for nz in NOISES}
                neg = {(d, nz): [] for d in O.DURATIONS_MIN for nz in NOISES}
                for s in SEEDS:
                    r = load_run(kind, season, s, tid)
                    served = {t["vav"]: r["zones"].index(r["own"][t["vav"]]) for t in r["plan"]}
                    for nz in NOISES:
                        for draw in range(1 if nz == "none" else N_DRAWS):
                            rng = np.random.default_rng([1, s, draw, NOISES.index(nz), KINDS.index(kind), SEASONS.index(season), BUILDINGS.index(tid)])
                            Tn = r["T"] + (rng.normal(0.0, O.NOISE_SD[nz], r["T"].shape) if nz != "none" else 0.0)
                            for t in r["plan"]:
                                z = served[t["vav"]]
                                for d in O.DURATIONS_MIN:
                                    sc = O.test_scores(Tn, t["day"], t["start_hour"], d, kind, season=season)
                                    acc.setdefault((d, nz, "peers"), []).append((O.top1(sc, z), O.auroc(sc, z)))
                                    pos[(d, nz)].append(sc[z])
                                    neg[(d, nz)].extend(np.delete(sc, z).tolist())
                                if nz in ("none", "legacy"):
                                    sh = O.test_scores(Tn, t["day"], t["start_hour"], PRIMARY_D, kind, history=True, season=season)
                                    acc.setdefault((PRIMARY_D, nz, "history"), []).append((O.top1(sh, z), O.auroc(sh, z)))
                for k, v in acc.items():
                    a = np.array(v)
                    res["metric"][(kind, season, tid) + k] = dict(top1=float(a[:, 0].mean()), auroc=float(a[:, 1].mean()))
                for k in pos:
                    res["scores"][(kind, season, tid) + k] = (np.array(pos[k]), np.array(neg[k]))
            print(f"  scored {kind:9s} {season:8s} {time.time() - t0:.0f}s", flush=True)
    return res


def fmt(x):
    return f"{x['est']:.2f} [{x['lo']:.2f}, {x['hi']:.2f}]"


def metric(res, kind, season, d, nz, key="top1", method="peers"):
    return D.boot_mean([res["metric"][(kind, season, t, d, nz, method)][key] for t in BUILDINGS])


def loto_rates(res, kind, season, d, nz):
    """held-out (theta, TPR, FPR) per building with theta chosen on the other 6 buildings"""
    out = []
    for h in BUILDINGS:
        ptr = np.concatenate([res["scores"][(kind, season, t, d, nz)][0] for t in BUILDINGS if t != h])
        ntr = np.concatenate([res["scores"][(kind, season, t, d, nz)][1] for t in BUILDINGS if t != h])
        th = O.choose_theta(ptr, ntr)
        p, n = res["scores"][(kind, season, h, d, nz)]
        out.append((th, *O.rates_at(p, n, th)))
    return out


def first_working(res, kind, nz="legacy"):
    return next((d for d in O.DURATIONS_MIN if all(metric(res, kind, s, d, nz)["est"] >= 0.90 for s in SEASONS)), None)


def main():
    t0 = time.time()
    n_runs = len(KINDS) * len(SEASONS) * len(SEEDS) * len(BUILDINGS)
    _, bad = code_path_checks()
    bad += truth_check_against_pools()
    if bad:
        raise SystemExit(f"CODE-PATH CHECK FAILED ({len(bad)}): {bad[:5]}")
    print(f"code-path checks passed on {n_runs} runs {time.time() - t0:.0f}s", flush=True)
    f = OUT / "override_eval.pkl"
    if f.exists():
        res = pickle.loads(f.read_bytes())
        print("loaded from cache")
    else:
        res = compute(t0)
        f.write_bytes(pickle.dumps(res))

    md = ["# Addendum 16, Part A: measured operating characteristics of a technician-style override test", "",
          f"126 EnergyPlus runs (7 train-role VAV buildings x July / January x test-order seeds 1-3 x 3 commands), each holding one 2-hour override test of every box (one per day); {n_runs} runs passed the code-path checks "
          "(10-minute series length; for every `close` run the box flow is zero in exactly the two shifted hours and non-zero just before and after; run truth == pool `vav_zone` truth). Score = extra cooling (`full_cool`, `flow_only`) or extra warming (`close`) of a zone relative to its peers over the first D minutes versus the previous hour; "
          "zone-temperature noise `legacy` = 0.25 K, `harsh` = 0.5 K, 20 draws; 7 buildings counted equally; building-cluster bootstrap 95% CI (500). Simulation only.", ""]

    md += ["## Top-1 identification: the highest-scoring zone is the zone the tested box serves (chance about 0.10-0.17)", "",
           "| command | season | " + " | ".join(f"D = {d} min" for d in O.DURATIONS_MIN) + " | AUROC at D = 60 |", "|---|---|" + "---|" * (len(O.DURATIONS_MIN) + 1)]
    for kind in KINDS:
        for season in SEASONS:
            md.append(f"| {kind} | {season} | " + " | ".join(fmt(metric(res, kind, season, d, "legacy")) for d in O.DURATIONS_MIN) + f" | {fmt(metric(res, kind, season, PRIMARY_D, 'legacy', 'auroc'))} |")
    md += ["", "(`legacy` noise.) Noise robustness at D = 60 min:", "", "| command | season | no noise | legacy (0.25 K) | harsh (0.5 K) |", "|---|---|---|---|---|"]
    for kind in KINDS:
        for season in SEASONS:
            md.append(f"| {kind} | {season} | " + " | ".join(fmt(metric(res, kind, season, PRIMARY_D, nz)) for nz in NOISES) + " |")
    md += ["", "Peers-only (primary) versus history-corrected (secondary) top-1 at D = 60 min:", "", "| command | season | peers-only, legacy | history-corrected, legacy |", "|---|---|---|---|"]
    for kind in KINDS:
        for season in SEASONS:
            md.append(f"| {kind} | {season} | {fmt(metric(res, kind, season, PRIMARY_D, 'legacy'))} | {fmt(metric(res, kind, season, PRIMARY_D, 'legacy', method='history'))} |")

    md += ["", "## Measured rates of the rule \"the zone responds if its score >= theta\" (D = 60 min, `legacy` noise)", "",
           "Leave-one-building-out: theta = the smallest grid value with FPR <= 0.05 on the other 6 buildings; TPR / FPR measured on the held-out building (mean over buildings [95% CI]). The engine's ASSUMED rates are TPR 0.95, FPR 0.05.", "",
           "| command | season | mean theta (K) | measured TPR | measured FPR | vs assumed 0.95 / 0.05 |", "|---|---|---|---|---|---|"]
    verdicts = {}
    for kind in KINDS:
        per = {}
        for season in SEASONS:
            lr = loto_rates(res, kind, season, PRIMARY_D, "legacy")
            tpr, fpr = D.boot_mean([x[1] for x in lr]), D.boot_mean([x[2] for x in lr])
            per[season] = (tpr["est"], fpr["est"])
            md.append(f"| {kind} | {season} | {np.mean([x[0] for x in lr]):.2f} | {fmt(tpr)} | {fmt(fpr)} | " +
                      ("TPR below assumed" if tpr["est"] < 0.95 else "TPR at/above assumed") + "; " + ("FPR above assumed" if fpr["est"] > 0.05 else "FPR at/below assumed") + " |")
        held = all(v[0] >= 0.95 and v[1] <= 0.05 for v in per.values())
        better = all(v[0] >= 0.97 and v[1] <= 0.03 for v in per.values())
        verdicts[kind] = "assumed rates PESSIMISTIC (both seasons better by >= 0.02)" if better else ("assumed rates HELD" if held else "assumed rates OPTIMISTIC")
    md += ["", "ROC points, all 7 buildings pooled (D = 60 min, `legacy`): TPR / FPR at each threshold", "", "| command | season | " + " | ".join(f"theta = {th:g} K" for th in O.THETA_GRID) + " |", "|---|---|" + "---|" * len(O.THETA_GRID)]
    for kind in KINDS:
        for season in SEASONS:
            p = np.concatenate([res["scores"][(kind, season, t, PRIMARY_D, "legacy")][0] for t in BUILDINGS])
            n = np.concatenate([res["scores"][(kind, season, t, PRIMARY_D, "legacy")][1] for t in BUILDINGS])
            md.append(f"| {kind} | {season} | " + " | ".join("{:.2f} / {:.2f}".format(*O.rates_at(p, n, th)) for th in O.THETA_GRID) + " |")

    md += ["", "## Frozen readouts (Addendum 16, Part A)", ""]
    for kind in KINDS:
        fw = first_working(res, kind)
        fh = first_working(res, kind, "harsh")
        md.append(f"- **{kind}**: A1 shortest D with top-1 >= 0.90 in both seasons (legacy) = {f'{fw} min' if fw else 'not by 120 min'}; A4 same under harsh noise = {f'{fh} min' if fh else 'not by 120 min'}; A2 {verdicts[kind]}")
    (OUT / "override_eval_report.md").write_text("\n".join(md))
    print("\n".join(md))


main()
