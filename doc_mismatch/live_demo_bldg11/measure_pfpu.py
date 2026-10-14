"""Hit and false-alarm rates of `bas_airflow` and `bas_reheat` against the LBNL PFPU simulated fault set (EXPLORATORY; LBNL_PFPU_NOTES.md was written and hashed before any data value was read).

  .venv/bin/python doc_mismatch/live_demo_bldg11/measure_pfpu.py            # the measurement
  .venv/bin/python doc_mismatch/live_demo_bldg11/measure_pfpu.py --headers  # plumbing: member names and column names only

Reads the zip in place (data_cache/timeseries/lbnl_pfpu/, git-ignored). Only aggregate rates are written (results/docmismatch/lbnl_pfpu/).
"""
import io
import json
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
ZIP = REPO / "data_cache" / "timeseries" / "lbnl_pfpu" / "LBNL_FDD_PFPU_Data_Sets_all_3.zip"
OUT = REPO / "results" / "docmismatch" / "lbnl_pfpu"
ZONES = ("W", "E", "S", "I")
AIR_TOL, REHEAT_TOL, REHEAT_CALL = 0.10, 0.10, 0.10
BG = {"bas_airflow": 0.05, "bas_reheat": 0.05}
CAT = {"damper_stuck": 0.75, "airflow_bias": 0.50, "pi2_unstable": 0.50, "reheat_valve": 0.75}
SKIP_START_MIN = 30

# file name -> (fault family, severity label)
FAMILIES = [
    (r"FaultFree", "fault_free", "-"),
    (r"VAVDMPRStuck_(\d+)%", "damper_stuck", r"\1%"),
    (r"SensorBias_VAVAirflow_([+-]\d+)CFM", "airflow_bias", r"\1 cfm"),
    (r"VAVDMPRUnstable", "pi2_unstable", "-"),
    (r"RMTEMPUnstable", "pi1_unstable", "-"),
    (r"ReheatVLVStuck_(\d+)%", "reheat_valve", r"stuck \1%"),
    (r"ReheatVLVLeak_(\d+)%MaxFlow", "reheat_valve", r"leak \1%"),
    (r"ReheatCoilFouling_(Airside|Waterside)_(\w+)", "coil_fouling", r"\1 \2"),
    (r"SensorBias_RMTEMP_([+-]\d+)C", "room_temp_bias", r"\1 C"),
    (r"VAVFanRestrictFlow", "fan_restricted", "-"),
]


def classify(name):
    base = Path(name).name
    for pat, fam, sev in FAMILIES:
        m = re.search(pat, base)
        if m:
            return fam, m.expand(sev) if "\\" in sev else sev
    return None, None


def find(cols, stem, zone):
    """the column for point `stem` in zone `zone`: tolerant of the separator the files use"""
    for c in cols:
        if re.fullmatch(rf"{re.escape(stem)}[_ ]?{zone}", c.strip(), flags=re.I):
            return c
    return None


def headers():
    with zipfile.ZipFile(ZIP) as z:
        names = [n for n in z.namelist() if n.lower().endswith(".csv") and "__MACOSX" not in n]
        print(len(names), "csv members; first:", names[:3])
        with z.open(names[0]) as f:
            df = pd.read_csv(f, nrows=3)
        print("columns:", list(df.columns))
        print(df.iloc[:2, :6])
        print("unclassified members:", [n for n in names if classify(n)[0] is None])


def per_file(z, name):
    with z.open(name) as f:
        df = pd.read_csv(f)
    cols = list(df.columns)
    sysc = next((c for c in cols if c.strip().upper() == "SYS_CTL"), None)
    if sysc is None:
        raise KeyError(f"{name}: no SYS_CTL")
    operate = (df[sysc].to_numpy() == 1)
    # minutes since the start of each operate stretch
    since = np.zeros(len(df), int)
    run = 0
    for i, o in enumerate(operate):
        run = run + 1 if o else 0
        since[i] = run
    out = {}
    for zone in ZONES:
        cf, sp = find(cols, "VAV_PM_CFM", zone), find(cols, "VAV_PM_CFM_SP", zone)
        vp, vc = find(cols, "RH_VLV", zone), find(cols, "RH_VLV_DM", zone)
        if cf and sp:
            flow, setp = df[cf].to_numpy(float), df[sp].to_numpy(float)
            with np.errstate(divide="ignore", invalid="ignore"):
                air = np.abs(flow - setp) > AIR_TOL * setp
            ok = operate & np.isfinite(flow) & np.isfinite(setp) & (setp > 0)
            q = np.quantile(setp[ok], 2 / 3) if ok.any() else np.inf
            out[zone, "bas_airflow"] = dict(flag=air, ok=ok, high=ok & (setp >= q))
        if vp and vc:
            pos, cmd = df[vp].to_numpy(float), df[vc].to_numpy(float)
            rh = (cmd > REHEAT_CALL) & (np.abs(pos - cmd) > REHEAT_TOL)
            ok = operate & np.isfinite(pos) & np.isfinite(cmd)
            out[zone, "bas_reheat"] = dict(flag=rh, ok=ok, high=ok & False, heat_called=ok & (cmd > REHEAT_CALL), any_mismatch=(np.abs(pos - cmd) > REHEAT_TOL))
    return out, since


FZ = None                                              # the faulted box, found from the data (LBNL_PFPU_DEVIATIONS.md D1)


def find_fault_zone(z):
    """The box whose damper position is exactly constant in Operate mode in BOTH stuck-damper files (the documentation says west; the files say otherwise). No check rate is used."""
    found = []
    for fname in ("PFPU_VAVDMPRStuck_0%.csv", "PFPU_VAVDMPRStuck_100%.csv"):
        name = next(n for n in z.namelist() if n.endswith(fname))
        with z.open(name) as f:
            df = pd.read_csv(f, usecols=lambda c: c == "SYS_CTL" or c.startswith("VAV_DMPR_"))
        op = df["SYS_CTL"] == 1
        flat = [c[-1] for c in df.columns if c.startswith("VAV_DMPR_") and float(df[c][op].std()) < 1e-9]
        found.append(flat)
    assert len(found[0]) == 1 and found[0] == found[1], f"the faulted box is not identified uniquely: {found}"
    return found[0][0]


def rate(d, key="ok", skip=None):
    m = d[key] if skip is None else d[key] & skip
    return float(d["flag"][m].mean()) if m.sum() else float("nan"), int(m.sum())


def main():
    if "--headers" in sys.argv:
        return headers()
    global FZ
    rows = []
    with zipfile.ZipFile(ZIP) as z:
        FZ = find_fault_zone(z)
        print("faulted box found from the stuck-damper footprint:", FZ, flush=True)
        names = sorted(n for n in z.namelist() if n.lower().endswith(".csv") and "__MACOSX" not in n)
        for n in names:
            fam, sev = classify(n)
            if fam is None:
                continue
            d, since = per_file(z, n)
            for (zone, chk), v in d.items():
                r_all, n_all = rate(v)
                r_skip, _ = rate(v, skip=since > SKIP_START_MIN)
                r_high, n_high = rate(v, key="high") if v["high"].any() else (float("nan"), 0)
                extra = {}
                if chk == "bas_reheat":
                    rc, nc = rate(v, key="heat_called")
                    extra = dict(rate_while_heat_called=rc, share_of_operate_minutes_heat_called=float(v["heat_called"].sum() / max(v["ok"].sum(), 1)),
                                 rate_any_mismatch=float(v["any_mismatch"][v["ok"]].mean()))
                rows.append(dict(file=Path(n).name, family=fam, severity=sev, zone=zone, check=chk, rate=r_all, n=n_all, rate_after_startup=r_skip, rate_high_demand=r_high, **extra))
            print("done", Path(n).name, flush=True)
    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "rates.csv", index=False)
    report(df)


def hit(df, fam, chk, col="rate"):
    d = df[(df.family == fam) & (df.zone == FZ) & (df.check == chk)]
    return d.groupby("severity")[col].mean(), float(d.groupby("severity")[col].mean().mean())


def verdict_hit(m, c):
    return "OPTIMISTIC (informative)" if m < c - 0.15 else "CONSISTENT" if m <= c + 0.15 else "NO INFORMATION (above: a clean simulation can exceed real life)"


def verdict_fa(m, bg):
    return "OPTIMISTIC (informative)" if m > 2 * bg else "REASONABLE (informative)" if m >= bg / 2 else "NO INFORMATION (below: a clean simulation is cleaner than real life)"


def report(df):
    L = ["# LBNL PFPU simulated fault set: hit and false-alarm rates of two checks (exploratory; LBNL_PFPU_NOTES.md hashed before any value was read)", "",
         "SIMULATED data (HVACSIM+): a measured hit rate is at best a plausible upper bound on the real one, a false-alarm rate a plausible lower bound. One-minute Operate-mode samples; the faulted box is found from the data (the documentation says west; the files say south: LBNL_PFPU_DEVIATIONS.md D1).", ""]
    res = {}
    L += [f"## Hit rates (box {FZ} of the faulted run, the box the data show is faulted)", "", "| catalogue cause | simulated fault | check | catalogue | measured (mean over severities) | after start-up | high-demand third | range over severities | verdict |", "|---|---|---|---|---|---|---|---|---|"]
    spec = [("damper_stuck", "damper_stuck", "bas_airflow"), ("flow_sensor", "airflow_bias", "bas_airflow"), ("controller_config", "pi2_unstable", "bas_airflow"), ("reheat_fail (valve)", "reheat_valve", "bas_reheat")]
    catkey = {"damper_stuck": "damper_stuck", "airflow_bias": "airflow_bias", "pi2_unstable": "pi2_unstable", "reheat_valve": "reheat_valve"}
    for cause, fam, chk in spec:
        by, m = hit(df, fam, chk)
        _, m_skip = hit(df, fam, chk, "rate_after_startup")
        _, m_high = hit(df, fam, chk, "rate_high_demand")
        c = CAT[catkey[fam]]
        res[fam, chk] = m
        L.append(f"| {cause} | {fam} | {chk} | {c:.2f} | **{m:.2f}** | {m_skip:.2f} | {m_high:.2f} | {by.min():.2f} to {by.max():.2f} | {verdict_hit(m, c)} |")
    rv_any = float(df[(df.family == "reheat_valve") & (df.zone == FZ) & (df.check == "bas_reheat")].groupby("severity")["rate_any_mismatch"].mean().mean())
    L += ["", f"Post hoc sensitivity (added after the per-box table was seen, not part of the verdict): if `bas_reheat` also counts a valve that differs from its command when no heat is called for, the mean hit rate on reheat valve stuck or leaking is {rv_any:.2f}."]
    L += ["", f"Per severity (box {FZ}, `rate`):", "", "| fault | severity | bas_airflow | bas_reheat | reheat: share of Operate minutes with heat called for | reheat: rate while heat is called for |", "|---|---|---|---|---|---|"]
    w = df[(df.zone == FZ) & (df.family != "fault_free")]
    for (fam, sev), g in w.groupby(["family", "severity"], sort=False):
        a = g[g.check == "bas_airflow"]["rate"]; r = g[g.check == "bas_reheat"]
        L.append(f"| {fam} | {sev} | {a.iloc[0]:.2f} | {r['rate'].iloc[0]:.2f} | {r['share_of_operate_minutes_heat_called'].iloc[0]:.0%} | {r['rate_while_heat_called'].iloc[0]:.2f} |")
    L += ["", "## False-alarm rates", "", "| check | catalogue bg | fault-free run, four boxes | the three healthy boxes in faulted runs, median over runs (range) | verdict (fault-free) |", "|---|---|---|---|---|"]
    fa = {}
    for chk in ("bas_airflow", "bas_reheat"):
        ff = df[(df.family == "fault_free") & (df.check == chk)]["rate"]
        he = df[(df.family != "fault_free") & (df.zone != FZ) & (df.check == chk)].groupby("file")["rate"].mean()
        fa[chk] = float(ff.mean())
        L.append(f"| {chk} | {BG[chk]:.2f} | {ff.mean():.3f} ({', '.join(f'{x:.3f}' for x in ff)}) | {he.median():.3f} ({he.min():.3f} to {he.max():.3f}) | {verdict_fa(float(ff.mean()), BG[chk])} |")
    L += ["", "## Predictions (written before any value was read)", ""]
    d = res["damper_stuck", "bas_airflow"]; b = res["airflow_bias", "bas_airflow"]; p2 = res["pi2_unstable", "bas_airflow"]; rv = res["reheat_valve", "bas_reheat"]
    L += [f"- P1 (damper stuck, bas_airflow, within 0.15 of 0.75): {'HELD' if abs(d - 0.75) <= 0.15 else 'FAILED'} (measured {d:.2f})",
          f"- P2 (airflow-sensor bias, bas_airflow at most 0.25): {'HELD' if b <= 0.25 else 'FAILED'} (measured {b:.2f})",
          f"- P3 (unstable PI2, bas_airflow between 0.30 and 0.80): {'HELD' if 0.30 <= p2 <= 0.80 else 'FAILED'} (measured {p2:.2f})",
          f"- P4 (reheat valve stuck or leaking, bas_reheat below 0.60): {'HELD' if rv < 0.60 else 'FAILED'} (measured {rv:.2f})",
          f"- P5 (bas_airflow false alarms in the fault-free run at most 5%): {'HELD' if fa['bas_airflow'] <= 0.05 else 'FAILED'} (measured {fa['bas_airflow']:.3f})", ""]
    L += ["Not in the primary comparison (descriptive): coil fouling, room-temperature sensor bias, unstable PI1, restricted box fan; their rates are in `rates.csv`.", ""]
    (OUT / "report.md").write_text("\n".join(L))
    (OUT / "summary.json").write_text(json.dumps(dict(hits={f"{k[0]}|{k[1]}": v for k, v in res.items()}, false_alarm=fa), indent=1))
    print("\n".join(L))


if __name__ == "__main__":
    main()
