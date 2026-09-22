"""Aggregate the S-V decision rows into the DR-study tables (PREREGISTRATION_DR.md sec 6/7). Writes verifier_results.{json,md}.
  .venv/bin/python doc_mismatch/scripts/29_dr_report_verifier.py [--boot 400]
"""
import json, pickle, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.dr import analysis as AN
from docmismatch.dr.pools import DR_DIR

B = int(sys.argv[sys.argv.index("--boot") + 1]) if "--boot" in sys.argv else 400
ARMS = ["baseline", "noise_only", "regime", "full", "full_x3"]
SUITES = ["T1_in_range", "T2_regime", "T3_control", "T4_topology", "T5_climate", "T6_compound"]
VER = DR_DIR / "verifier"
SHIFT = ["T3_control", "T4_topology", "T5_climate", "T6_compound"]


def load(arm):
    out = {}
    for f in sorted(VER.glob(f"rows_{arm}_*.pkl")):
        d = pickle.loads(f.read_bytes())
        out[d["fold"]] = d
    return out


def sel(rows, layer, pol, unit=None):
    return [r for r in rows if r["layer"] == layer and r["policy"] == pol and (unit is None or r["unit"] == unit)]


def cond_rows(D, cond, suite, layer, pol, tel="estimated"):
    """condition -> Rows. seen: fold seen; unseen: pooled unseen_s*; days: fold days (training buildings)."""
    if cond == "seen":
        d = D.get("seen"); rows = sel(d["rows"], layer, pol, f"{suite}|{tel}") if d else []
    elif cond == "unseen":
        rows = [r for k, d in D.items() if k.startswith("unseen_s") for r in sel(d["rows"], layer, pol, f"{suite}|estimated")]
    else:
        d = D.get("days"); rows = sel(d["rows"], layer, pol, "train_bldgs|days") if d else []
    return AN.Rows(rows) if rows else None


def fmt(x, d=3):
    return "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:.{d}f}"


def cell(b, k):
    v = b[k]
    return f"{fmt(v['est'])} [{fmt(v['lo'])}, {fmt(v['hi'])}]"


def main():
    D = {a: load(a) for a in ARMS}
    D = {a: d for a, d in D.items() if d}
    res = {"boot": B, "cond": {}, "diff": {}, "family": {}, "overlap": {}, "telemetry": {}}
    md = ["# S-V (sequential verifier): domain-randomization study results", "",
          f"Building-cluster bootstrap CIs ({B} resamples). Metrics are class-balanced (wrong-documentation and correct-documentation episodes weighted equally). "
          "`acc` = accuracy among answered verdicts of the plain 0.95 stopping rule, `cov` = answered share, `forced` = accuracy of the verdict at the end of the budget with no abstention, "
          "`ece` = posterior calibration over all episodes, `gap` = stated confidence minus realised accuracy among answered (positive = overconfident).", ""]
    for pol in ("active", "random"):
        for layer in ("none", "new"):
            res["cond"][f"{pol}|{layer}"] = {}
            md += [f"## policy `{pol}`, decision layer `{layer}` " + ("(plain stopping rule)" if layer == "none" else "(reliability layer fitted on the arm's inner leave-one-building-out records)"), ""]
            for cond in ("days", "seen", "unseen"):
                md += [f"### condition: {dict(days='unseen days, seen buildings (training buildings, adjacent windows) - in-distribution reference', seen='seen seasons, unseen buildings/regimes', unseen='UNSEEN season on unseen buildings/regimes (compound where the suite is shifted)')[cond]}", "",
                       "| suite | arm | n eps | n buildings | answered | acc | cov | forced | ece | gap |", "|---|---|---|---|---|---|---|---|---|---|"]
                suites = ["(training buildings)"] if cond == "days" else SUITES
                for su in suites:
                    for arm in ARMS:
                        if arm not in D:
                            continue
                        R = cond_rows(D[arm], cond, su, layer, pol)
                        if R is None or R.n == 0:
                            continue
                        b = AN.boot(R, B=B)
                        res["cond"][f"{pol}|{layer}"][f"{cond}|{su}|{arm}"] = b
                        md.append(f"| {su} | {arm} | {b['n_eps']} | {b['n_bldg']} | {b['n_answered']} | {cell(b,'acc')} | {cell(b,'cov')} | {cell(b,'forced')} | {cell(b,'ece')} | {cell(b,'gap')} |")
                md.append("")
    # paired differences vs baseline (primary policy active, plain rule) on shifted suites
    md += ["## Paired differences vs `baseline` (policy `active`, plain rule; same test episodes; positive = better than baseline)", "",
           "| condition | suite | arm | d acc | d cov | d forced | d ece (neg = better) |", "|---|---|---|---|---|---|---|"]
    for cond in ("seen", "unseen"):
        for su in SUITES:
            RB = cond_rows(D["baseline"], cond, su, "none", "active") if "baseline" in D else None
            for arm in ARMS[1:]:
                if arm not in D or RB is None:
                    continue
                RA = cond_rows(D[arm], cond, su, "none", "active")
                if RA is None:
                    continue
                dd = {k: AN.boot_diff(RA, RB, k, B=B) for k in ("acc", "cov", "forced", "ece")}
                res["diff"][f"{cond}|{su}|{arm}"] = dd
                md.append(f"| {cond} | {su} | {arm} | " + " | ".join(f"{fmt(dd[k]['est'])} [{fmt(dd[k]['lo'])}, {fmt(dd[k]['hi'])}]" for k in ("acc", "cov", "forced", "ece")) + " |")
    md.append("")
    # generalisation gap: days (in-dist) minus shifted suite, per arm (forced accuracy and acc)
    md += ["## Generalization gap = in-distribution (unseen days, own training buildings) minus shifted suite (policy `active`, plain rule)", "",
           "| arm | metric | in-dist (days) | " + " | ".join(SUITES) + " | seen-season mean drop | unseen-season mean drop |", "|---|---|---|" + "---|" * (len(SUITES) + 2)]
    for arm in ARMS:
        if arm not in D:
            continue
        R0 = cond_rows(D[arm], "days", None, "none", "active")
        if R0 is None:
            continue
        for k in ("acc", "forced"):
            v0 = AN.STATS[k](R0)
            vs = {c: [AN.STATS[k](cond_rows(D[arm], c, su, "none", "active")) if cond_rows(D[arm], c, su, "none", "active") is not None else np.nan for su in SUITES] for c in ("seen", "unseen")}
            md.append(f"| {arm} | {k} | {fmt(v0)} | " + " | ".join(fmt(x) for x in vs["seen"]) + f" | {fmt(v0 - np.nanmean(vs['seen']))} | {fmt(v0 - np.nanmean(vs['unseen']))} |")
    md.append("")
    # telemetry sensitivity (seen season)
    md += ["## Test telemetry sensitivity (seen seasons, policy `active`, plain rule): acc / forced accuracy by test telemetry, pooled over T1..T6", "",
           "| arm | legacy | estimated | wide | wide+distractors |", "|---|---|---|---|---|"]
    for arm in ARMS:
        if arm not in D or "seen" not in D[arm]:
            continue
        cells = []
        for tel in ("legacy", "estimated", "wide", "wide_distractors"):
            rows = [r for su in SUITES for r in sel(D[arm]["seen"]["rows"], "none", "active", f"{su}|{tel}")]
            if not rows:
                cells.append("n/a"); continue
            b = AN.boot(AN.Rows(rows), names=("acc", "forced"), B=max(100, B // 4)); res["telemetry"][f"{arm}|{tel}"] = b
            cells.append(f"{fmt(b['acc']['est'])} / {fmt(b['forced']['est'])}")
        md.append(f"| {arm} | " + " | ".join(cells) + " |")
    md.append("")
    # by corruption family (seen seasons, estimated telemetry, T2..T6 pooled), policy active
    md += ["## By corruption family (seen seasons, estimated telemetry, suites T2-T6 pooled, policy `active`, plain rule): acc / cov / forced", "",
           "| family | arm | n eps | acc | cov | forced |", "|---|---|---|---|---|---|"]
    fams = ["wrong_ahu_mapping", "vav_zone_swap", "plant_loop_mapping", "sensor_mapping", "same_medium_branch", "parallel_peer_swap"]
    for fam in fams:
        for arm in ARMS:
            if arm not in D or "seen" not in D[arm]:
                continue
            rows = [r for su in SUITES[1:] for r in sel(D[arm]["seen"]["rows"], "none", "active", f"{su}|estimated") if r["family"] == fam]
            if len(rows) < 20:
                continue
            b = AN.boot(AN.Rows(rows), names=("acc", "cov", "forced"), B=max(100, B // 4)); res["family"][f"{fam}|{arm}"] = b
            md.append(f"| {fam} | {arm} | {b['n_eps']} | {cell(b,'acc')} | {cell(b,'cov')} | {cell(b,'forced')} |")
    md.append("")
    # distractor overlap
    md += ["## Distractor faults: episodes whose owner/candidate/member nodes carry a tracked distractor vs not (telemetry `wide_distractors`, seen seasons, policy `active`, plain rule)", "",
           "| arm | overlap | n eps | acc | forced |", "|---|---|---|---|---|"]
    for arm in ARMS:
        if arm not in D or "seen" not in D[arm]:
            continue
        ov = D[arm]["seen"]["overlap"]
        for flag in (True, False):
            rows = [r for su in SUITES for r in sel(D[arm]["seen"]["rows"], "none", "active", f"{su}|wide_distractors") if ov.get(f"{su}|wide_distractors|{r['ep']}", False) == flag]
            if len(rows) < 20:
                continue
            b = AN.boot(AN.Rows(rows), names=("acc", "forced"), B=max(100, B // 4)); res["overlap"][f"{arm}|{flag}"] = b
            md.append(f"| {arm} | {'yes' if flag else 'no'} | {b['n_eps']} | {cell(b,'acc')} | {cell(b,'forced')} |")
    (VER.parent / "verifier_results.json").write_text(json.dumps(res, indent=1, default=float))
    (VER.parent / "verifier_results.md").write_text("\n".join(md))
    print("\n".join(md[:60]))


main()
