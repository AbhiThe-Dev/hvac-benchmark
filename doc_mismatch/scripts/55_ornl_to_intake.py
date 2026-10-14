"""Write the real ORNL RTU-VAV BASELINE days (DEV data; the sealed fault files are never read) as an intake-format export, as a check that the intake handles a real,
messy building export. Point naming follows the dataset's own columns; connections are the dataset's naming, NOT independently verified (`verified = unknown`).

  .venv/bin/python doc_mismatch/scripts/55_ornl_to_intake.py
  .venv/bin/python doc_mismatch/scripts/54_intake_check.py results/docmismatch/intake/ornl_rtu --report results/docmismatch/intake/ornl_rtu_report.md

Assumptions stated here rather than hidden: temperatures are degF and reheat power W (real_frp.py's documented units); RTU_SA_FLOW is taken as cfm (values ~3200; it is
only used for the normalised building load, so the unit does not matter); no time zone is given (the dataset does not say whether clocks follow daylight saving).
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import real_frp as R  # noqa: E402

OUT = ROOT.parent / "results" / "docmismatch" / "intake" / "ornl_rtu"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pts = [("RTU_OA_TEMP", "ENV", "Weather", "oat", "degF"), ("RTU_SA_TEMP", "RTU-1", "AHU", "sat", "degF"), ("RTU_MA_TEMP", "RTU-1", "AHU", "mat", "degF"),
           ("RTU_SA_FLOW", "RTU-1", "AHU", "flow", "cfm")]
    for r in R.ROOMS:
        pts += [(f"TERM_RM_TEMP_{r}", f"Zone-{r}", "Zone", "temp", "degF"), (f"VAV_RM_SAT_{r}", f"VAV-{r}", "VAV", "t_dis", "degF"), (f"VAV_RM_WATT_{r}", f"VAV-{r}", "VAV", "reheat", "W")]
    with open(OUT / "points.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["point_id", "equipment_id", "equipment_type", "signal", "unit", "logging"])
        w.writerows([[c, e, t, s, u, "interval"] for c, e, t, s, u in pts])
    with open(OUT / "connections.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["owner_id", "member_id", "slot", "verified", "true_owner", "source"])
        for r in R.ROOMS:
            w.writerow(["RTU-1", f"VAV-{r}", "ahu_vav", "unknown", "", "dataset point naming"])
            w.writerow([f"VAV-{r}", f"Zone-{r}", "vav_zone", "unknown", "", "dataset point naming"])
    cols = [c for c, *_ in pts]
    n = 0
    with open(OUT / "trends.csv", "w", newline="") as out:
        w = csv.writer(out)
        w.writerow(["Datetime"] + cols)
        for fname in R.SEASONS:                                     # the four BASELINE files only
            with open(R.DATA / fname) as fh:
                rd = csv.reader(fh)
                head = next(rd)
                idx = [head.index(c) for c in cols]
                for row in rd:
                    w.writerow([row[0]] + [row[i] for i in idx])
                    n += 1
    (OUT / "context.json").write_text(json.dumps({"building_id": "ornl_rtu_baseline", "notes": "LBNL FDD RTU dataset (ORNL FRP), baseline files only; connections = dataset naming, unverified"}, indent=1))
    print(f"wrote {OUT} ({n} one-minute rows, {len(cols)} points)")


main()
