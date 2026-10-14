"""False-alarm rate of the control-system readings from real Mortar trend data (EXPLORATORY; FALSE_ALARM_NOTES.md was written and hashed before any value was read).

  .venv/bin/python doc_mismatch/live_demo_bldg11/measure_false_alarm.py

bas_airflow: bldg30, measured against the recorded airflow setpoint. bas_static: bldg1, bldg8, bldg15, bldg40 against a PROXY for the setpoint (none is recorded). Only aggregate statistics are
written (no equipment or room identifiers). Needs the Mortar time series under data_cache/timeseries/mortar (not part of the repository).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import mortar_adapter as MA  # noqa: E402

OUT = REPO / "results" / "docmismatch" / "false_alarm"
MORTAR = REPO / "data_cache" / "timeseries" / "mortar"
BG_AIRFLOW, BG_STATIC = 0.05, 0.03                     # the catalogue's assumed false-alarm rates (bas_airflow, bas_static)
AIR_TOL, STATIC_TOL = 0.10, 0.20
WINDOW_HOURS = (2, 6, 24, 168)                         # post hoc window lengths (proxy B is the 2-hour one)
GATE_MIN_DISTINCT = 50                                 # a live airflow setpoint takes many values over a year; a configured limit takes a handful
MIN_ELIGIBLE = 500                                     # samples a box needs to be counted
LOAD_MIN = 0.20                                        # airflow rule applies above 20% of the box's maximum setpoint
IDX = MA._stream_index(str(MORTAR))


def read(u):
    t = pq.read_table(IDX[u], columns=["time", "value"])
    ts = t.column("time").to_numpy().astype("datetime64[ms]").astype(np.int64) / 1000.0
    v = t.column("value").to_numpy(zero_copy_only=False).astype(float)
    o = np.argsort(ts, kind="stable")
    return ts[o], v[o]


def airflow():
    pb = MA.parse_brick(REPO / "data_cache" / "mortar__bldg30.ttl", "bldg30")
    distinct = []                                                           # validity gate (FALSE_ALARM_DEVIATIONS.md D1): is the recorded 'setpoint' a live setpoint?
    for vav in pb.vavs:
        s_ = [u for c, _, u in pb.points.get(vav, []) if c == "Air_Flow_Setpoint" and u in IDX]
        if s_:
            distinct.append(len(np.unique(read(s_[0])[1])))
    distinct = np.array(distinct)
    gate = dict(boxes=int(len(distinct)), median_distinct_values=float(np.median(distinct)), min_distinct=int(distinct.min()), max_distinct=int(distinct.max()),
                boxes_with_one_value=int((distinct == 1).sum()), boxes_with_at_most_3_values=int((distinct <= 3).sum()), required_median=GATE_MIN_DISTINCT)
    if np.median(distinct) < GATE_MIN_DISTINCT:
        return dict(measurable=False, gate=gate)
    per, tert, allflags = [], {"low": [], "mid": [], "high": []}, []
    sys_sets = []                                                           # per box: (timestamps eligible, outside flag, flow < 5% of setpoint flag)
    for vav in pb.vavs:
        pts = pb.points.get(vav, [])
        f = [u for c, _, u in pts if c == "Supply_Air_Flow_Sensor" and u in IDX]
        s = [u for c, _, u in pts if c == "Air_Flow_Setpoint" and u in IDX]
        if not (f and s):
            continue
        tf, vf = read(f[0]); ts, vs = read(s[0])
        t, i, j = np.intersect1d(tf, ts, return_indices=True)
        flow, sp = vf[i], vs[j]
        elig = (sp >= LOAD_MIN * sp.max()) & np.isfinite(flow) & np.isfinite(sp) & (sp > 0)
        if elig.sum() < MIN_ELIGIBLE:
            continue
        out = np.abs(flow[elig] - sp[elig]) > AIR_TOL * sp[elig]
        per.append(out.mean()); allflags.append(out)
        sys_sets.append((t[elig], out, flow[elig] < 0.05 * sp[elig]))
        q = np.quantile(sp[elig], [1 / 3, 2 / 3])
        spe = sp[elig]
        for name, m in (("low", spe <= q[0]), ("mid", (spe > q[0]) & (spe <= q[1])), ("high", spe > q[1])):
            tert[name].append(out[m])
    per = np.array(per)
    pooled = float(np.concatenate(allflags).mean())
    # sensitivity: drop timestamps at which at least half of the reporting boxes read about zero against a high setpoint (a building-wide outage or dropout, which the check SHOULD flag)
    ts_all = np.concatenate([s[0] for s in sys_sets]); zero_all = np.concatenate([s[2] for s in sys_sets])
    uniq, inv = np.unique(ts_all, return_inverse=True)
    frac_zero = np.bincount(inv, weights=zero_all.astype(float)) / np.bincount(inv)
    outage = frac_zero[inv] >= 0.5
    out_all = np.concatenate([s[1] for s in sys_sets])
    pooled_clean = float(out_all[~outage].mean())
    per_clean = []
    pos = 0
    for s in sys_sets:
        n = len(s[1]); k = ~outage[pos:pos + n]; pos += n
        if k.sum() >= MIN_ELIGIBLE:
            per_clean.append(s[1][k].mean())
    return dict(measurable=True, gate=gate, boxes=len(per), eligible_samples=int(sum(len(a) for a in allflags)), pooled=pooled, median=float(np.median(per)), q1=float(np.quantile(per, .25)), q3=float(np.quantile(per, .75)),
                share_boxes_above_catalogue=float((per > BG_AIRFLOW).mean()), tercile={k: float(np.concatenate(v).mean()) for k, v in tert.items()},
                outage_share_of_eligible=float(outage.mean()), pooled_without_outages=pooled_clean, median_without_outages=float(np.median(per_clean)),
                share_boxes_above_catalogue_without_outages=float((np.array(per_clean) > BG_AIRFLOW).mean()))


def static():
    rows = []
    for b in ("bldg1", "bldg8", "bldg15", "bldg40"):
        pb = MA.parse_brick(REPO / "data_cache" / f"mortar__{b}.ttl", b)
        for ahu in pb.ahus:
            for c, _, u in pb.points.get(ahu, []):
                if c != "Supply_Air_Static_Pressure_Sensor" or u not in IDX:
                    continue
                t, v = read(u)
                # one instantaneous reading per 15-minute bin (what a technician's screen would show), never an average
                bins = np.floor(t / 900.0).astype(np.int64)
                keep = np.r_[True, np.diff(bins) > 0]
                t, v = t[keep], v[keep]
                v = np.where(np.isfinite(v), v, np.nan)
                lvl = np.nanmedian(v[v > 0.25 * np.nanpercentile(v, 99)])
                running = v >= 0.5 * lvl
                if running.sum() < MIN_ELIGIBLE:
                    continue
                a_out = np.abs(v[running] - lvl) > STATIC_TOL * lvl
                s = pd.Series(np.where(running, v, np.nan))
                loc = s.rolling(9, center=True, min_periods=5).median().to_numpy()               # +-1 hour of running samples
                okb = running & np.isfinite(loc) & (loc > 0)
                b_out = np.abs(v[okb] - loc[okb]) > STATIC_TOL * loc[okb]
                curve = {}
                for hours in WINDOW_HOURS:                                                       # POST HOC (added after the first run): how the rate grows as the proxy's window grows
                    w = int(hours * 4) | 1
                    lw = s.rolling(w, center=True, min_periods=max(3, w // 2)).median().to_numpy()
                    ok_w = running & np.isfinite(lw) & (lw > 0)
                    curve[hours] = float((np.abs(v[ok_w] - lw[ok_w]) > STATIC_TOL * lw[ok_w]).mean())
                rows.append(dict(building=b, running_samples=int(running.sum()), proxy_A=float(a_out.mean()), proxy_B=float(b_out.mean()), curve=curve))
    return rows


def airflow_lines(air):
    g = air["gate"]
    if not air["measurable"]:
        return [f"**NOT MEASURABLE with this data.** The recorded `Air_Flow_Setpoint` of the {g['boxes']} boxes takes {g['min_distinct']} to {g['max_distinct']} distinct values over the year (median {g['median_distinct_values']:.0f}; "
                f"{g['boxes_with_one_value']} boxes exactly one, {g['boxes_with_at_most_3_values']} at most three), where a live setpoint needs a median of at least {g['required_median']}. These are configured limits, not the setpoint a box tracks, so measured airflow against them says "
                "nothing about false alarms. No airflow rate is reported. (A first run without this gate printed 95% and a verdict; it was an artifact, see FALSE_ALARM_DEVIATIONS.md D1.)", "",
                "No downloaded building records a live airflow setpoint, so the catalogue's 5% for `bas_airflow` has no real-data check here."]
    return [f"Samples with setpoint at least 20% of the box's maximum; abnormal = |flow - setpoint| > 10% of setpoint. Catalogue assumes {BG_AIRFLOW:.0%}.", "", "| | share outside +-10% |", "|---|---|",
            f"| boxes counted / eligible samples | {air['boxes']} / {air['eligible_samples']:,} |", f"| pooled | {air['pooled']:.1%} |", f"| median box | {air['median']:.1%} |",
            "", f"Verdict: **{verdict(air['median'], BG_AIRFLOW)}**."]


def verdict(measured, bg):
    return "OPTIMISTIC" if measured > 2 * bg else "CONSERVATIVE" if measured < bg / 2 else "REASONABLE"


def main():
    air, st = airflow(), static()
    A = np.array([r["proxy_A"] for r in st]); B = np.array([r["proxy_B"] for r in st])
    vA, vB = verdict(float(np.median(A)), BG_STATIC), verdict(float(np.median(B)), BG_STATIC)
    L = ["# False-alarm rate of the control-system readings from real trend data (exploratory; FALSE_ALARM_NOTES.md hashed before any value was read)", "",
         "Only the false-alarm side can be measured here (no labelled faults). Any fault in the data raises the measured rate, so these are upper bounds on the true rate; the per-equipment median is the robust summary.", "",
         "## bas_airflow: measured airflow vs its recorded setpoint (bldg30, 1-minute data, about a year)", "",
         *airflow_lines(air), "",
         "## bas_static: duct static vs a PROXY for its setpoint (no building records the setpoint)", "",
         f"Running samples only; abnormal = more than 20% off the proxy. A = the handler's long-run median while running (over-states if the setpoint is reset); B = median of the surrounding two hours (under-states: a persistent low static is absorbed). Catalogue assumes {BG_STATIC:.0%}.", "",
         "| building | handlers | running samples | proxy A | proxy B |", "|---|---|---|---|---|"]
    for b in ("bldg1", "bldg8", "bldg15", "bldg40"):
        rs = [r for r in st if r["building"] == b]
        if rs:
            L.append(f"| {b} | {len(rs)} | {sum(r['running_samples'] for r in rs):,} | {', '.join(f'{r['proxy_A']:.1%}' for r in rs)} | {', '.join(f'{r['proxy_B']:.1%}' for r in rs)} |")
    L += ["", f"Median over {len(st)} handlers: proxy A {np.median(A):.1%}, proxy B {np.median(B):.1%}. Verdict (called only if both agree): "
              f"A {vA}, B {vB} -> **{vA if vA == vB else 'NOT CALLED (the two proxies disagree)'}**.", ""]
    L += ["### Post hoc (added after the first run): the rate against a proxy whose window grows", "",
          "| window around each reading | " + " | ".join(f"{h} h" if h < 168 else "7 days" for h in WINDOW_HOURS) + " | whole record (proxy A) |", "|---|" + "---|" * (len(WINDOW_HOURS) + 1),
          "| median over handlers | " + " | ".join(f"{np.median([r['curve'][h] for r in st]):.1%}" for h in WINDOW_HOURS) + f" | {np.median(A):.1%} |",
          "| range over handlers | " + " | ".join(f"{min(r['curve'][h] for r in st):.1%} to {max(r['curve'][h] for r in st):.1%}" for h in WINDOW_HOURS) + f" | {A.min():.1%} to {A.max():.1%} |", ""]
    # predictions
    L += ["## Predictions (written before the first value was read)", "",
          ("- F1 (airflow pooled above 5%, median box above 5%): NOT TESTABLE (the recorded setpoint is not live; FALSE_ALARM_DEVIATIONS.md D1)" if not air["measurable"] else f"- F1: pooled {air['pooled']:.1%}, median box {air['median']:.1%}"),
          f"- F2 (static proxy A median above 5%, proxy B median below 5%): {'HELD' if np.median(A) > .05 and np.median(B) < .05 else 'FAILED'} (A {np.median(A):.1%}, B {np.median(B):.1%})",
          ("- F3 (high-load third has a lower airflow share than the low-load third): NOT TESTABLE (same reason)" if not air["measurable"] else f"- F3: high {air['tercile']['high']:.1%}, low {air['tercile']['low']:.1%}"), ""]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.md").write_text("\n".join(L))
    (OUT / "summary.json").write_text(json.dumps(dict(airflow=air, static=st), indent=1))
    print("\n".join(L))


if __name__ == "__main__":
    main()
