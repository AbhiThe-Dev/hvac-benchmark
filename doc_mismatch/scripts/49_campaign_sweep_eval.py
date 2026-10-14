"""Addendum 15, Part A: how robust is the dither campaign? (PREREGISTRATION_DR.md Addendum 15). Nothing is fitted; never touches SEALED data, T1-T6 suites or real data.
Reads the fresh campaigns of scripts/48 (code seeds 4-6) and scores zone-to-box rank-1 accuracy per campaign length, over half-swing x override dropout (signals flow + t_dis) and,
at half-swing 1.5 K / no dropout, over the box signals the building logs.
  .venv/bin/python doc_mismatch/scripts/49_campaign_sweep_eval.py
"""
import pickle
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.data import load_base  # noqa: E402
from docmismatch.dr import diagnosability as D  # noqa: E402
from docmismatch.dr import perturbation as P  # noqa: E402

CAMP = ROOT.parent / "results" / "docmismatch" / "perturbation" / "campaigns15"
OUT = ROOT.parent / "results" / "docmismatch" / "perturbation"
BUILDINGS = ["sys07_vav_reheat", "vav_2ahu_2loops", "vav_3ahu_2loops", "dev_E", "dev_F", "dev_G", "dev_H"]
SEASONS = ["july", "january"]
SEEDS = (4, 5, 6)
LENGTHS = [24, 48, 96, 168, 288]
AMPLITUDES = (0.5, 1.0, 1.5)
DROPOUTS = (0.0, 0.25)
SIGNAL_SETS = {"flow+t_dis": ("flow", "t_dis"), "flow": ("flow",), "t_dis": ("t_dis",), "t_dis+reheat": ("t_dis", "reheat")}
NOISES = ["legacy", "harsh"]
PRE, N_DRAWS = 48, 20


def cfg_name(a, p):
    return f"a{a}_p{p}"


def truth_and_ids(b):
    zones, vavs = sorted(b.ids("Zone")), sorted(b.ids("VAV"))
    own = {m: o for o, m in b.slot_edges["vav_zone"]}
    return zones, vavs, np.array([vavs.index(own[z]) for z in zones])


def cell(a, p, season, tid, sigsets, noises):
    """{signal set: {noise: {L: rank-1 averaged over the 3 seeds}}} for one (configuration, season, building)"""
    per_seed = []
    for s in SEEDS:
        b = load_base(tid, CAMP / cfg_name(a, p) / season / f"seed{s}")
        zones, vavs, truth = truth_and_ids(b)
        r = {}
        for name in sigsets:
            U, Y = P.campaign_arrays(b.ev, zones, vavs, PRE, SIGNAL_SETS[name])
            r[name] = {nz: P.sweep(U, Y, truth, LENGTHS, nz, N_DRAWS, 1000 * s) for nz in noises}
        per_seed.append(r)
    return {name: {nz: {L: float(np.mean([r[name][nz][L] for r in per_seed])) for L in LENGTHS} for nz in noises} for name in sigsets}


def fmt(x):
    return f"{x['est']:.2f} [{x['lo']:.2f}, {x['hi']:.2f}]"


def est(res, a, p, season, name, nz, L):
    return D.boot_mean([res[(a, p, season, t)][name][nz][L] for t in BUILDINGS])["est"]


def first_working(res, a, p, name, nz="legacy"):
    """shortest L at which the mean rank-1 is >= 0.90 in BOTH seasons (None = not by 288 h)"""
    return next((L for L in LENGTHS if all(est(res, a, p, s, name, nz, L) >= 0.90 for s in SEASONS)), None)


def main():
    f = OUT / "campaign_sweep.pkl"
    if f.exists():
        res = pickle.loads(f.read_bytes())
        print("loaded from cache")
    else:
        res = {}
        for a in AMPLITUDES:
            for p in DROPOUTS:
                sigsets = list(SIGNAL_SETS) if (a, p) == (1.5, 0.0) else ["flow+t_dis"]
                for season in SEASONS:
                    for tid in BUILDINGS:
                        res[(a, p, season, tid)] = cell(a, p, season, tid, sigsets, NOISES)
                print(f"  scored {cfg_name(a, p)}", flush=True)
        f.write_bytes(pickle.dumps(res))

    md = ["# Addendum 15, Part A: robustness of the dither campaign", "",
          "Fresh campaigns (code seeds 4-6), 7 train-role topologies counted equally, both seasons; rank-1 = fraction of zones whose most-responsive box is the true serving box (chance about 0.10); "
          "`legacy` noise = the project's original telemetry noise; building-cluster bootstrap 95% CI (500). A cell WORKS if the mean rank-1 is >= 0.90 in BOTH seasons at that campaign length. Simulation only.", ""]

    md += ["## Amplitude x override dropout (signals flow + t_dis, `legacy` noise)", "",
           "| half-swing | dropout | season | " + " | ".join(f"{L} h" for L in LENGTHS) + " | shortest working L | swing-hours a x L |", "|---|---|---|" + "---|" * (len(LENGTHS) + 2)]
    for a in AMPLITUDES:
        for p in DROPOUTS:
            fw = first_working(res, a, p, "flow+t_dis")
            for i, season in enumerate(SEASONS):
                cells = [fmt(D.boot_mean([res[(a, p, season, t)]["flow+t_dis"]["legacy"][L] for t in BUILDINGS])) for L in LENGTHS]
                md.append(f"| {a} K | {p:.0%} | {season} | " + " | ".join(cells) + (f" | {fw if fw else 'not by 288 h'} | {a * fw:.0f} |" if (i == 0 and fw) else (" | not by 288 h | - |" if i == 0 else " | | |")))
    md += ["", "## Signals the building logs (half-swing 1.5 K, no dropout, `legacy` noise)", "",
           "| signal set | season | " + " | ".join(f"{L} h" for L in LENGTHS) + " | shortest working L |", "|---|---|" + "---|" * (len(LENGTHS) + 1)]
    for name in SIGNAL_SETS:
        fw = first_working(res, 1.5, 0.0, name)
        for i, season in enumerate(SEASONS):
            cells = [fmt(D.boot_mean([res[(1.5, 0.0, season, t)][name]["legacy"][L] for t in BUILDINGS])) for L in LENGTHS]
            md.append(f"| {name} | {season} | " + " | ".join(cells) + (f" | {fw if fw else 'not by 288 h'} |" if i == 0 else " | |"))
    md += ["", "## `harsh` noise (robustness; flow x N(1, 0.10), temperature + N(0, 1.0)), signals flow + t_dis, shortest working L", "",
           "| half-swing | dropout | shortest working L (harsh) |", "|---|---|---|"]
    for a in AMPLITUDES:
        for p in DROPOUTS:
            fw = first_working(res, a, p, "flow+t_dis", "harsh")
            md.append(f"| {a} K | {p:.0%} | {fw if fw else 'not by 288 h'} |")

    md += ["", "## Frozen readouts (Addendum 15)", ""]
    ok = [a for a in AMPLITUDES if (first_working(res, a, 0.0, "flow+t_dis") or 999) <= 168]
    md.append(f"- R1 smallest half-swing that works by L <= 168 h with no dropout: {min(ok) if ok else 'none'} K" + (f" (works at L = {first_working(res, min(ok), 0.0, 'flow+t_dis')} h)" if ok else ""))
    w = first_working(res, 1.5, 0.25, "flow+t_dis")
    md.append(f"- R2 half-swing 1.5 K with 25% overrides: works by L <= 168 h: {'yes' if (w or 999) <= 168 else 'no'}; by L <= 288 h: {'yes (L = %d h)' % w if w else 'no'}")
    md.append("- R3 signal sets that work by L <= 168 h at 1.5 K / no dropout: " + (", ".join(n for n in SIGNAL_SETS if (first_working(res, 1.5, 0.0, n) or 999) <= 168) or "none"))
    (OUT / "campaign_sweep_report.md").write_text("\n".join(md))
    print("\n".join(md))


main()
