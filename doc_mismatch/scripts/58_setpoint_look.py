"""DESCRIPTIVE look at the zone temperature setpoints in the downloaded Mortar buildings: how often each changes, how many values it takes, and whether a change is
zone-specific or shared with other zones at the same moment (a schedule). Exploratory; reads ONLY the setpoint streams and computes no relationship between a setpoint and
any box flow, discharge temperature or zone temperature (so the outcome of any later identification test is untouched).

  .venv/bin/python doc_mismatch/scripts/58_setpoint_look.py     ->  results/docmismatch/intake/setpoint_look.md

A change event = a sample whose value differs from the previous finite sample by more than 0.05 (the values look like degF). An event is INDIVIDUAL when at most 10% of the other
zones change within +-15 minutes of it, SHARED when at least 50% do (a schedule), otherwise MIXED; only events at which at least half of the other zones are reporting are classified.
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import mortar_adapter as M  # noqa: E402

REPO = ROOT.parent
MORTAR = REPO / "data_cache" / "timeseries" / "mortar"
OUT = REPO / "results" / "docmismatch" / "intake" / "setpoint_look.md"
BUILDINGS = ["bldg1", "bldg27", "bldg40", "bldg15"]                       # the buildings that trend zone temperature setpoints
STEP = 0.05
BIN = 900.0
PLAUSIBLE = (45.0, 95.0)          # degF assumed: a zone setpoint outside this range is a dropout / placeholder (0.0 appears), treated as missing


def setpoint_streams(building):
    """[(label, uuid)] of the Target_Zone_Air_Temperature_Setpoint points of the building's VAVs that have a timeseries, sorted by label"""
    from rdflib import RDF, RDFS, Graph, Namespace
    B, R = Namespace(M.BRICK_NS), Namespace(M.REF_NS)
    g = Graph()
    g.parse(str(REPO / "data_cache" / f"mortar__{building}.ttl"), format="turtle")
    out = []
    for v in g.subjects(RDF.type, B.VAV):
        for pt in g.objects(v, B.hasPoint):
            if (pt, RDF.type, B.Target_Zone_Air_Temperature_Setpoint) in g:
                u = [str(x) for r in g.objects(pt, R.hasExternalReference) for x in g.objects(r, R.hasTimeseriesId)]
                label = str(next(g.objects(pt, RDFS.label), pt))
                if u and "setpoint" in label.lower():                    # bldg1 also files a continuous "Zone Air Control Temp" under this class: not a setpoint
                    out.append((label, u[0]))
    return sorted(out)


def look(building):
    sp = setpoint_streams(building)
    data, missing = [], 0
    for label, u in sp:
        try:
            data.append((label,) + M.read_stream(MORTAR, u))
        except FileNotFoundError:
            missing += 1
    n = len(data)
    rows, ev_bins, ev_all, samp_bins, ev_step = [], [], [], [], []
    for label, t, v in data:
        bad = np.isfinite(v) & ((v < PLAUSIBLE[0]) | (v > PLAUSIBLE[1]))
        ok = np.isfinite(v) & ~bad
        tt, vv = t[ok], v[ok]
        top = np.unique(np.round(vv, 1), return_counts=True)
        modal_share = float(np.sort(top[1])[-3:].sum() / max(len(vv), 1))
        d = np.diff(vv)
        ch = np.abs(d) > STEP
        eb = np.floor(tt[1:][ch] / BIN).astype(np.int64)
        ev_all.append(eb)                                                  # one entry per event (aligned with ev_step)
        ev_bins.append(np.unique(eb))                                       # unique bins, for the look-ups in other streams
        samp_bins.append(np.unique(np.floor(tt / BIN).astype(np.int64)))
        ev_step.append(np.abs(d[ch]))
        step = float(np.median(np.diff(tt))) if len(tt) > 1 else float("nan")
        rows.append(dict(label=label, n=len(tt), years=(tt[-1] - tt[0]) / 86400 / 365.25 if len(tt) > 1 else 0.0, step_min=step / 60, distinct=len(np.unique(np.round(vv, 2))),
                         lo=float(vv.min()), hi=float(vv.max()), n_events=int(ch.sum()), implausible=float(bad.sum() / max(len(v), 1)), top3=modal_share))
    # classify every event by how many OTHER zones change (or report) within +-tol bins (15 minutes each)
    def classify(tol):
        out = []
        for i in range(n):
            B_ = ev_all[i]
            if len(B_) == 0:
                out.append(np.array([], dtype="U1"))
                continue
            chg = np.zeros(len(B_), int)
            rep = np.zeros(len(B_), int)
            for j in range(n):
                if j == i:
                    continue
                chg += (np.searchsorted(ev_bins[j], B_ - tol, "left") < np.searchsorted(ev_bins[j], B_ + tol, "right"))
                rep += (np.searchsorted(samp_bins[j], B_ - tol, "left") < np.searchsorted(samp_bins[j], B_ + tol, "right"))
            share = np.where(rep > 0, chg / np.maximum(rep, 1), np.nan)
            enough = rep >= 0.5 * (n - 1)
            out.append(np.where(~enough, "?", np.where(share <= 0.10, "I", np.where(share >= 0.50, "S", "M"))))
        return out

    cls = classify(1)
    cls_wide = classify(4)                                                  # robustness: +-1 hour
    hours = np.concatenate([((e * int(BIN)) % 86400) // 3600 for e in ev_all]) if ev_all else np.array([])
    ind_hours = np.concatenate([((e * int(BIN)) % 86400 // 3600)[c == "I"] for e, c in zip(ev_all, cls)]) if ev_all else np.array([])
    return rows, cls, ev_step, missing, cls_wide, ind_hours, len(setpoint_streams(building)) if False else n



def main():
    md = ["# Zone temperature setpoints in the Mortar buildings: a descriptive look (exploratory)", "",
          "Reads only the setpoint streams (no relationship with any box or zone measurement is computed). Samples outside 45-95 (degF assumed) are dropouts and treated as missing. Change event = a step larger than 0.05 between consecutive valid samples. INDIVIDUAL = at most 10% of the other zones "
          "change within +-15 min of the event; SHARED = at least 50% do (a schedule); MIXED = in between; '?' = fewer than half of the other zones were reporting. Whole record of each building, UTC clock.", ""]
    for b in BUILDINGS:
        rows, cls, steps, missing, cls_wide, ind_hours, _ = look(b)
        n = len(rows)
        allc = np.concatenate(cls) if cls else np.array([])
        tot = int(sum(r["n_events"] for r in rows))
        share = {k: int((allc == k).sum()) for k in ("I", "M", "S", "?")}
        ind = np.array([int((c == "I").sum()) for c in cls])
        yrs = np.array([r["years"] for r in rows])
        per_year = ind / np.maximum(yrs, 1e-9)
        istep = np.concatenate([s[c == "I"] for s, c in zip(steps, cls)]) if cls else np.array([])
        md += [f"## {b}: {n} zone setpoint streams" + (f" ({missing} without a downloaded stream)" if missing else ""), "",
               f"- Labels: e.g. `{rows[0]['label']}`" + (f" and `{rows[1]['label']}`" if n > 1 else "") + ".",
               f"- Record: median {np.median(yrs):.1f} years per stream, median sampling step {np.median([r['step_min'] for r in rows]):.0f} min; samples outside {PLAUSIBLE[0]:.0f}-{PLAUSIBLE[1]:.0f} (dropouts) removed: median {np.median([r['implausible'] for r in rows]):.1%} "
               f"(max {max(r['implausible'] for r in rows):.1%}); distinct values per stream: median {int(np.median([r['distinct'] for r in rows]))} (min {min(r['distinct'] for r in rows)}, max {max(r['distinct'] for r in rows)}); "
               f"share of samples at a stream's three most common values: median {np.median([r['top3'] for r in rows]):.0%}; setpoint range {min(r['lo'] for r in rows):.1f} to {max(r['hi'] for r in rows):.1f}.",
               f"- Change events: {tot} in total ({tot / n:.0f} per stream, {tot / n / np.median(yrs):.0f} per stream-year). Shared with other zones: {share['S']} ({share['S'] / max(tot, 1):.0%}); individual: {share['I']} ({share['I'] / max(tot, 1):.0%}); "
               f"mixed: {share['M']} ({share['M'] / max(tot, 1):.0%}); unclassifiable: {share['?']} ({share['?'] / max(tot, 1):.0%}).",
               f"- Robustness, +-1 hour instead of +-15 min: individual {int(sum((c == 'I').sum() for c in cls_wide))} ({sum((c == 'I').sum() for c in cls_wide) / max(tot, 1):.0%}), shared {int(sum((c == 'S').sum() for c in cls_wide))} "
               f"({sum((c == 'S').sum() for c in cls_wide) / max(tot, 1):.0%}).",
               (f"- Hour of day (UTC) of the individual events: the three busiest hours hold {np.sort(np.bincount(ind_hours.astype(int), minlength=24))[-3:].sum() / max(len(ind_hours), 1):.0%} of them (uniform would be 12.5%)." if len(ind_hours) else "- No individual events."),
               f"- Individual events per zone over the whole record: median {int(np.median(ind))}, quartiles {int(np.percentile(ind, 25))}-{int(np.percentile(ind, 75))}, min {int(ind.min())}, max {int(ind.max())}; zones with none: {int((ind == 0).sum())} of {n}; "
               f"per zone-year: median {np.median(per_year):.1f}.",
               f"- Size of individual changes (|step|): median {np.median(istep):.2f}, 90th percentile {np.percentile(istep, 90):.2f}." if len(istep) else "- No individual events.", ""]
    OUT.write_text("\n".join(md))
    print("\n".join(md))


main()
