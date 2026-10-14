"""Part A of TREND_NOTES.md (EXPLORATORY; the protocol and predictions were hashed before any trend-window value was computed): the snapshot rules of measure_pfpu.py applied to a trailing window of the
box's trend, on the LBNL PFPU simulated fault set.

  .venv/bin/python doc_mismatch/live_demo_bldg11/trend_pfpu.py

Writes results/docmismatch/trend_study/trend_pfpu_report.md and trend_pfpu_summary.json (the 24 h window rates that Part B maps into the catalogue).
"""
import json
import sys
import zipfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import measure_pfpu as M  # noqa: E402

OUT = HERE.parent.parent / "results" / "docmismatch" / "trend_study"
STORED = HERE.parent.parent / "results" / "docmismatch" / "lbnl_pfpu" / "summary.json"
WINDOWS = {"24 h": 1440, "4 h": 240}
EVAL_EVERY = 15                    # evaluate at every 15th Operate minute
MIN_OP, MIN_CALL = 60, 15          # minutes of evidence a window needs
THETA_AIR, THETA_REHEAT = 0.20, 0.50
FAMILIES = ("damper_stuck", "airflow_bias", "pi2_unstable", "reheat_valve")


def window_rates(v_air, v_rh, Wm):
    """Share of evaluation minutes at which the trailing window is abnormal, for the airflow rule, the reheat rule and the loose reheat reading; and the share of reheat windows with no verdict."""
    out = {}
    # airflow
    op = v_air["ok"]; fl = v_air["flag"] & op
    idx = np.flatnonzero(op)[::EVAL_EVERY]; idx = idx[idx >= Wm]
    cs_op, cs_fl = np.cumsum(op), np.cumsum(fl)
    n_op, n_fl = cs_op[idx] - cs_op[idx - Wm], cs_fl[idx] - cs_fl[idx - Wm]
    out["air"] = float(((n_op >= MIN_OP) & (n_fl >= THETA_AIR * np.maximum(n_op, 1))).mean()) if len(idx) else float("nan")
    out["n_eval"] = int(len(idx))
    # reheat
    op = v_rh["ok"]; called = v_rh["heat_called"] & op; rh = v_rh["flag"] & op; anym = v_rh["any_mismatch"] & op
    idx = np.flatnonzero(op)[::EVAL_EVERY]; idx = idx[idx >= Wm]
    cs_op, cs_c, cs_rh, cs_any = np.cumsum(op), np.cumsum(called), np.cumsum(rh), np.cumsum(anym)
    n_op = cs_op[idx] - cs_op[idx - Wm]; n_c = cs_c[idx] - cs_c[idx - Wm]; n_rh = cs_rh[idx] - cs_rh[idx - Wm]; n_any = cs_any[idx] - cs_any[idx - Wm]
    verdict = n_c >= MIN_CALL
    abn = verdict & (n_rh >= THETA_REHEAT * np.maximum(n_c, 1))
    loose = abn | ((n_op >= MIN_OP) & (n_any >= 0.5 * np.maximum(n_op, 1)))
    out["rh"] = float(abn.mean()) if len(idx) else float("nan")
    out["rh_loose"] = float(loose.mean()) if len(idx) else float("nan")
    out["rh_no_verdict"] = float((~verdict).mean()) if len(idx) else float("nan")
    return out


def main():
    rows = []
    with zipfile.ZipFile(M.ZIP) as z:
        fz = M.find_fault_zone(z)
        names = sorted(n for n in z.namelist() if n.lower().endswith(".csv") and "__MACOSX" not in n)
        for n in names:
            fam, sev = M.classify(n)
            d, _ = M.per_file(z, n)
            for zone in M.ZONES:
                va, vr = d[zone, "bas_airflow"], d[zone, "bas_reheat"]
                row = dict(family=fam, severity=sev, role="faulted" if zone == fz else "healthy", zone=zone,
                           snap_air=float(va["flag"][va["ok"]].mean()), snap_rh=float(vr["flag"][vr["ok"]].mean()))
                for wn, Wm in WINDOWS.items():
                    for k, x in window_rates(va, vr, Wm).items():
                        row[f"{k}|{wn}"] = x
                rows.append(row)
            print("done", Path(n).name, flush=True)
    import pandas as pd
    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "trend_pfpu_rates.csv", index=False)
    stored = json.load(open(STORED))["hits"]
    f = df[df.role == "faulted"]

    def fam_mean(fam, col):
        g = f[f.family == fam].groupby("severity")[col].mean()
        return float(g.mean()), float(g.min()), float(g.max())

    snap = {"damper_stuck": ("snap_air", "damper_stuck|bas_airflow"), "airflow_bias": ("snap_air", "airflow_bias|bas_airflow"), "pi2_unstable": ("snap_air", "pi2_unstable|bas_airflow"), "reheat_valve": ("snap_rh", "reheat_valve|bas_reheat")}
    ga1 = {fam: abs(fam_mean(fam, col)[0] - stored[key]) <= 0.01 for fam, (col, key) in snap.items()}
    L = ["# Trend-window versions of two BAS checks on the LBNL PFPU simulated fault set (exploratory; TREND_NOTES.md hashed before any trend-window value was computed)", "",
         f"SIMULATED data; the faulted box is {fz}. A window = the trailing Operate-mode minutes, evaluated at every {EVAL_EVERY}th Operate minute. `bas_airflow` window abnormal when at least {THETA_AIR:.0%} of its minutes are flagged (at least {MIN_OP} minutes); "
         f"`bas_reheat` window abnormal when at least {THETA_REHEAT:.0%} of its heat-called minutes are flagged (at least {MIN_CALL} such minutes, else no verdict = not flagged).", "",
         "## Gate GA1: the snapshot rates recomputed here equal the stored ones (0.01)", ""]
    L += [f"- {fam}: recomputed {fam_mean(fam, col)[0]:.4f}, stored {stored[key]:.4f}: **{'PASS' if ga1[fam] else 'FAIL'}**" for fam, (col, key) in snap.items()]
    gate = all(ga1.values())
    if not gate:
        L += ["", "**REGISTERED OUTCOME: NO RESULT (GA1 failed).**"]
    L += ["", "## Hit rates in the faulted box (mean over severities; range in brackets)", "", "| fault | check | snapshot | 24 h window | 4 h window | catalogue today |", "|---|---|---|---|---|---|"]
    cat = {"damper_stuck": 0.75, "airflow_bias": 0.50, "pi2_unstable": 0.50, "reheat_valve": 0.75}
    res = {}
    for fam in FAMILIES:
        col_s = "snap_rh" if fam == "reheat_valve" else "snap_air"
        k = "rh" if fam == "reheat_valve" else "air"
        s, w24, w4 = fam_mean(fam, col_s), fam_mean(fam, f"{k}|24 h"), fam_mean(fam, f"{k}|4 h")
        res[fam] = dict(snapshot=s[0], w24=w24[0], w4=w4[0], w24_range=[w24[1], w24[2]])
        L.append(f"| {fam} | {'bas_reheat' if fam == 'reheat_valve' else 'bas_airflow'} | {s[0]:.2f} | **{w24[0]:.2f}** ({w24[1]:.2f} to {w24[2]:.2f}) | {w4[0]:.2f} ({w4[1]:.2f} to {w4[2]:.2f}) | {cat[fam]:.2f} |")
    loose24 = fam_mean("reheat_valve", "rh_loose|24 h")[0]; nov24 = fam_mean("reheat_valve", "rh_no_verdict|24 h")[0]
    L += ["", f"Reheat valve, 24 h window: no verdict (fewer than {MIN_CALL} heat-called minutes in the window) in {100*nov24:.0f}% of windows; post hoc sensitivity counting a valve that differs from its command when no heat is called: {loose24:.2f}.", "",
          "Per severity (24 h window, faulted box):", "", "| fault | severity | snapshot | 24 h window |", "|---|---|---|---|"]
    for (fam, sev), g in f[f.family.isin(FAMILIES)].groupby(["family", "severity"], sort=False):
        k, col_s = ("rh", "snap_rh") if fam == "reheat_valve" else ("air", "snap_air")
        L.append(f"| {fam} | {sev} | {g[col_s].iloc[0]:.2f} | {g[f'{k}|24 h'].iloc[0]:.2f} |")
    h = df[(df.role == "healthy") | (df.family == "fault_free")]
    fa = {k: float(h[f"{k}|24 h"].mean()) for k in ("air", "rh")}
    L += ["", f"False alarms of the 24 h window rules (fault-free run and the three healthy boxes of every faulted run): airflow {fa['air']:.3f}, reheat {fa['rh']:.3f} (a clean simulation: no information about real equipment).", "",
          "## Predictions (written before any trend-window value was computed)", ""]
    pi2, rv = res["pi2_unstable"], res["reheat_valve"]
    P = [("T1 (unstable damper loop, 24 h window between 0.60 and 0.95)", 0.60 <= pi2["w24"] <= 0.95, f"{pi2['w24']:.2f}"),
         ("T2 (reheat valve stuck/leaking, 24 h window between 0.25 and 0.60)", 0.25 <= rv["w24"] <= 0.60, f"{rv['w24']:.2f}"),
         ("T3 (damper stuck and airflow-sensor bias stay at 0.98 or above)", res["damper_stuck"]["w24"] >= 0.98 and res["airflow_bias"]["w24"] >= 0.98, f"{res['damper_stuck']['w24']:.3f}, {res['airflow_bias']['w24']:.3f}"),
         ("T4 (false alarms of the window rules at most 0.02)", fa["air"] <= 0.02 and fa["rh"] <= 0.02, f"airflow {fa['air']:.3f}, reheat {fa['rh']:.3f}"),
         ("T5 (4 h window lower than 24 h for the unstable loop and the reheat valve)", pi2["w4"] < pi2["w24"] and rv["w4"] < rv["w24"], f"loop {pi2['w4']:.2f} vs {pi2['w24']:.2f}; valve {rv['w4']:.2f} vs {rv['w24']:.2f}")]
    L += [f"- {p}: **{'HELD' if ok else 'FAILED'}** ({d})" for p, ok, d in P] + [""]
    (OUT / "trend_pfpu_report.md").write_text("\n".join(L))
    (OUT / "trend_pfpu_summary.json").write_text(json.dumps(dict(gate_ga1=gate, windows_24h={k: v["w24"] for k, v in res.items()}, windows_4h={k: v["w4"] for k, v in res.items()}, snapshot={k: v["snapshot"] for k, v in res.items()}, false_alarm=fa), indent=1))
    print("\n".join(L))


if __name__ == "__main__":
    main()
