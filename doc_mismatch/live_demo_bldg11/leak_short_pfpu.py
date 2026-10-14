"""LEAK_SHORT_NOTES.md (EXPLORATORY; the protocol and predictions were hashed before any value of the new rules was computed): a discharge-temperature check for a leaking reheat valve, and a five-minute
average near maximum airflow for the airflow check, on the LBNL PFPU simulated fault set.

  .venv/bin/python doc_mismatch/live_demo_bldg11/leak_short_pfpu.py

Writes results/docmismatch/leak_short/report.md and rates.csv.
"""
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import measure_pfpu as M  # noqa: E402

OUT = HERE.parent.parent / "results" / "docmismatch" / "leak_short"
STORED = json.load(open(HERE.parent.parent / "results" / "docmismatch" / "lbnl_pfpu" / "summary.json"))["hits"]
TREND = json.load(open(HERE.parent.parent / "results" / "docmismatch" / "trend_study" / "trend_pfpu_summary.json"))
ZONES = M.ZONES
DT_F, CMD_OFF = 3.0, 0.02
EVAL_EVERY, W24 = 15, 1440
THETA_LEAK, MIN_EL = 0.20, 60
THETA_RH, MIN_CALL = 0.50, 15
NEEDED = {"SYS_CTL", "SA_TEMP"} | {f"{s}_{z}" for z in ZONES for s in ("VAV_DAT", "VAV_FAN_CS", "RH_VLV", "RH_VLV_DM", "VAV_PM_CFM", "VAV_PM_CFM_SP")}


def window_counts(idx, Wm, *series):
    out = []
    for s in series:
        cs = np.cumsum(s.astype(np.int64))
        out.append(cs[idx] - cs[idx - Wm])
    return out


def one_zone(df, z):
    c = lambda s: df[f"{s}_{z}"].to_numpy(float)  # noqa: E731
    op = (df["SYS_CTL"].to_numpy() == 1)
    cmd, pos, dat, fan = c("RH_VLV_DM"), c("RH_VLV"), c("VAV_DAT"), c("VAV_FAN_CS")
    sa, flow, sp = df["SA_TEMP"].to_numpy(float), c("VAV_PM_CFM"), c("VAV_PM_CFM_SP")
    # existing reheat rule (as measure_pfpu.py)
    ok_rh = op & np.isfinite(pos) & np.isfinite(cmd)
    called = ok_rh & (cmd > 0.10)
    rhflag = called & (np.abs(pos - cmd) > 0.10)
    # Test 1: discharge-temperature rule
    elig = op & np.isfinite(dat) & np.isfinite(sa) & np.isfinite(cmd) & (cmd <= CMD_OFF) & (fan == 0)
    leak = elig & ((dat - sa) > DT_F)
    # airflow
    with np.errstate(divide="ignore", invalid="ignore"):
        rel = np.abs(flow - sp) / sp
    ok_a = op & np.isfinite(flow) & np.isfinite(sp) & (sp > 0)
    a_flag = ok_a & (rel > 0.10)
    row = dict(rh_snap=float(rhflag[ok_rh].mean()), leak_snap=float(leak[elig].mean()) if elig.any() else float("nan"), leak_eligible_share=float(elig.sum() / max(op.sum(), 1)), air_snap=float(a_flag[ok_a].mean()))
    # 24 h windows at every 15th Operate minute
    idx = np.flatnonzero(op)[::EVAL_EVERY]; idx = idx[idx >= W24]
    n_c, n_rh, n_el, n_lk = window_counts(idx, W24, called, rhflag, elig, leak)
    rhA = (n_c >= MIN_CALL) & (n_rh >= THETA_RH * np.maximum(n_c, 1))
    leakB = (n_el >= MIN_EL) & (n_lk >= THETA_LEAK * np.maximum(n_el, 1))
    row.update(rh_24=float(rhA.mean()), leak_24=float(leakB.mean()), either_24=float((rhA | leakB).mean()))
    # Test 2: five-minute mean of the relative airflow error
    m5 = pd.Series(np.where(ok_a, rel, np.nan)).rolling(5, min_periods=5).mean().to_numpy()
    q = np.quantile(sp[ok_a], 2 / 3) if ok_a.any() else np.inf
    for tag, mask in (("hd", ok_a & (sp >= q)), ("all", ok_a)):
        e = np.flatnonzero(mask & np.isfinite(m5))[::EVAL_EVERY]
        row[f"five_{tag}"] = float((m5[e] > 0.10).mean()) if len(e) else float("nan")
        row[f"snap_at_{tag}"] = float(a_flag[e].mean()) if len(e) else float("nan")
    return row


def main():
    rows = []
    with zipfile.ZipFile(M.ZIP) as zf:
        fz = M.find_fault_zone(zf)
        names = sorted(n for n in zf.namelist() if n.lower().endswith(".csv") and "__MACOSX" not in n)
        for n in names:
            fam, sev = M.classify(n)
            with zf.open(n) as f:
                df = pd.read_csv(f, usecols=lambda col: col in NEEDED)
            for z in ZONES:
                rows.append(dict(family=fam, severity=sev, zone=z, role="faulted" if z == fz else "healthy", **one_zone(df, z)))
            print("done", Path(n).name, flush=True)
    d = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    d.to_csv(OUT / "rates.csv", index=False)
    f = d[d.role == "faulted"]

    def fm(fam, col, sevs=None):
        g = f[f.family == fam]
        if sevs is not None:
            g = g[g.severity.isin(sevs)]
        g = g.groupby("severity")[col].mean()
        return float(g.mean()), float(g.min()), float(g.max())

    leaks = [s for s in f[f.family == "reheat_valve"].severity.unique() if s.startswith("leak")]
    stuck = [s for s in f[f.family == "reheat_valve"].severity.unique() if s.startswith("stuck")]
    g1 = abs(fm("reheat_valve", "rh_snap")[0] - STORED["reheat_valve|bas_reheat"]) <= 0.01
    g2 = abs(fm("pi2_unstable", "air_snap")[0] - STORED["pi2_unstable|bas_airflow"]) <= 0.01
    L = ["# Two suggested reliability improvements on the LBNL PFPU simulated fault set (exploratory; LEAK_SHORT_NOTES.md hashed before any value of the new rules was computed)", "",
         f"SIMULATED data (best case; hit rates are at most plausible upper bounds, false-alarm rates plausible lower bounds); faulted box {fz}; the box is fan-powered, the tool targets single-duct boxes.", "",
         "## Gates", "", f"- G1 the existing reheat rule's snapshot rate on stuck+leak equals the stored 0.0790: **{'PASS' if g1 else 'FAIL'}** ({fm('reheat_valve', 'rh_snap')[0]:.4f})",
         f"- G2 the airflow snapshot rate on the unstable loop equals the stored 0.2734: **{'PASS' if g2 else 'FAIL'}** ({fm('pi2_unstable', 'air_snap')[0]:.4f})", ""]
    if not (g1 and g2):
        L += ["**REGISTERED OUTCOME: NO RESULT (a gate failed).**", ""]
    # ---------------- test 1
    L += ["## Test 1: discharge temperature above supply temperature (more than 3 degF, no heat called, box fan off), for a leaking reheat valve", "",
          "| fault | severity | existing rule, snapshot | existing rule, 24 h | discharge-temperature rule, snapshot | discharge-temperature rule, 24 h | either rule, 24 h | share of Operate minutes the leak rule can judge |", "|---|---|---|---|---|---|---|---|"]
    for (fam, sev), g in f[f.family == "reheat_valve"].groupby(["family", "severity"], sort=False):
        L.append(f"| {fam} | {sev} | {g.rh_snap.iloc[0]:.2f} | {g.rh_24.iloc[0]:.2f} | {g.leak_snap.iloc[0]:.2f} | {g.leak_24.iloc[0]:.2f} | {g.either_24.iloc[0]:.2f} | {g.leak_eligible_share.iloc[0]:.0%} |")
    pool = lambda col: fm("reheat_valve", col)[0]  # noqa: E731
    L += ["", "| family | existing rule 24 h | discharge-temperature rule 24 h | either rule 24 h | catalogue today |", "|---|---|---|---|---|",
          f"| leak (3 severities) | {fm('reheat_valve', 'rh_24', leaks)[0]:.2f} | {fm('reheat_valve', 'leak_24', leaks)[0]:.2f} | {fm('reheat_valve', 'either_24', leaks)[0]:.2f} | 0.75 |",
          f"| stuck (5 severities) | {fm('reheat_valve', 'rh_24', stuck)[0]:.2f} | {fm('reheat_valve', 'leak_24', stuck)[0]:.2f} | {fm('reheat_valve', 'either_24', stuck)[0]:.2f} | 0.75 |",
          f"| **stuck + leak (8)** | **{pool('rh_24'):.2f}** | {pool('leak_24'):.2f} | **{pool('either_24'):.2f}** | 0.75 |", ""]
    h = d[(d.role == "healthy") | (d.family == "fault_free")]
    fa_leak_s, fa_leak_24, fa_five = float(h.leak_snap.mean()), float(h.leak_24.mean()), float(h.five_hd.mean())
    L += [f"False alarms of the discharge-temperature rule (fault-free run and the three healthy boxes of every faulted run): snapshot {fa_leak_s:.3f}, 24 h window {fa_leak_24:.3f}.", ""]
    # ---------------- test 2
    L += ["## Test 2: a five-minute average of the airflow miss near maximum airflow", "",
          "| fault | snapshot, all minutes | snapshot at the near-maximum minutes | five-minute mean at the near-maximum minutes | five-minute mean, all minutes | 24 h window (earlier) |", "|---|---|---|---|---|---|"]
    t24 = TREND["windows_24h"]
    res2 = {}
    for fam in ("damper_stuck", "airflow_bias", "pi2_unstable"):
        a, b, c, e = fm(fam, "air_snap")[0], fm(fam, "snap_at_hd")[0], fm(fam, "five_hd")[0], fm(fam, "five_all")[0]
        res2[fam] = dict(snap=a, snap_hd=b, five_hd=c, five_all=e)
        L.append(f"| {fam} | {a:.2f} | {b:.2f} | **{c:.2f}** | {e:.2f} | {t24[fam]:.2f} |")
    L += ["", f"False alarms of the five-minute mean at the near-maximum minutes (fault-free run and healthy boxes): {fa_five:.3f}; of the snapshot at the same minutes: {float(h.snap_at_hd.mean()):.3f}.", "",
          "## Verdicts (rule fixed beforehand)", ""]
    sharper1 = (pool("either_24") - pool("rh_24") >= 0.15) and fa_leak_24 <= 0.05
    sharper2 = (res2["pi2_unstable"]["five_hd"] - res2["pi2_unstable"]["snap_hd"] >= 0.15) and fa_five <= 0.05
    L += [f"- Test 1, discharge-temperature rule on stuck+leak, either rule against the existing rule alone: **{'SHARPER' if sharper1 else 'NOT SHARPER'}** ({pool('rh_24'):.2f} to {pool('either_24'):.2f}; false alarms {fa_leak_24:.3f})",
          f"- Test 2, five-minute mean on the unstable loop against the snapshot at the same minutes: **{'SHARPER' if sharper2 else 'NOT SHARPER'}** ({res2['pi2_unstable']['snap_hd']:.2f} to {res2['pi2_unstable']['five_hd']:.2f}; false alarms {fa_five:.3f})", "",
          "## Predictions (written before any value of the new rules was computed)", ""]
    stuck_by = f[(f.family == "reheat_valve") & f.severity.isin(stuck)].groupby("severity")["leak_snap"].mean()
    P = [("L1 (leaks flagged at 0.60 or more on average, snapshot)", fm("reheat_valve", "leak_snap", leaks)[0] >= 0.60, f"{fm('reheat_valve', 'leak_snap', leaks)[0]:.2f}"),
         ("L2 (valves stuck at 100%, 80%, 50% flagged at 0.80 or more each; stuck at 0% at 0.05 or less)", all(stuck_by[s] >= 0.80 for s in ("stuck 100%", "stuck 80%", "stuck 50%")) and stuck_by["stuck 0%"] <= 0.05, ", ".join(f"{s.replace('stuck ', '')} {stuck_by[s]:.2f}" for s in stuck_by.index)),
         ("L3 (discharge-temperature rule false alarms at most 0.05, snapshot)", fa_leak_s <= 0.05, f"{fa_leak_s:.3f}"),
         ("L4 ('either rule', 24 h, stuck+leak at 0.60 or more)", pool("either_24") >= 0.60, f"{pool('either_24'):.2f}"),
         ("S1 (five-minute mean flags the unstable loop between 0.15 and 0.60 near maximum)", 0.15 <= res2["pi2_unstable"]["five_hd"] <= 0.60, f"{res2['pi2_unstable']['five_hd']:.2f}"),
         ("S2 (damper stuck and sensor bias stay at 0.95 or more under the five-minute mean)", res2["damper_stuck"]["five_hd"] >= 0.95 and res2["airflow_bias"]["five_hd"] >= 0.95, f"{res2['damper_stuck']['five_hd']:.2f}, {res2['airflow_bias']['five_hd']:.2f}"),
         ("S3 (five-minute mean false alarms at most 0.02)", fa_five <= 0.02, f"{fa_five:.3f}")]
    L += [f"- {p}: **{'HELD' if ok else 'FAILED'}** ({det})" for p, ok, det in P] + [""]
    (OUT / "report.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
