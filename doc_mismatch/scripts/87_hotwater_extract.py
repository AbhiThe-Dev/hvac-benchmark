"""Hot-water / recirculation work-order extract from FMUCD (real work orders, CC BY 4.0), streamed from curl and never stored whole; the stream is hashed and the extract is only valid if the hash matches.
  curl -sSL --fail URL | .venv/bin/python doc_mismatch/scripts/87_hotwater_extract.py -     ->  results/docmismatch/hotwater/extract.csv
Keeps: every UNPLANNED order coded D2020 / D2090 / D2099 / D2001 (domestic water, other plumbing, general plumbing), plus any other UNPLANNED order, whatever its code, whose description matches HOT_RE
(to see how often hot-water work is coded elsewhere). Planned (PPM) orders are not kept. Says nothing about any technician or building of the user's.
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import workorders as W  # noqa: E402

OUT = ROOT.parent / "results/docmismatch/hotwater"
KEEP = ("UniversityID", "BuildingID", "BuildingName", "Type", "BuiltYear", "SystemCode", "SubsystemCode", "SubsystemDescription", "DescriptiveCode", "ComponentDescription", "WOID", "WODescription",
        "WOPriority", "WOStartDate", "WOEndDate", "WODuration", "PPM/UPM", "LaborCost", "MaterialCost", "TotalCost", "LaborHours")
PLUMB_SUBS = {"D2020", "D2090", "D2099", "D2001"}
HOT_RE = re.compile(r"hot water|\bdhw\b|domestic|re-?circ|water heater|\bwh[-\s]?\d|mixing valve|tempering|lukewarm|luke warm|no hot|not hot|cold water|\bhws\b|\bhwr\b|\bpress(?:ure)?\b.*water|water.*\bpress(?:ure)?\b|booster|\bprv\b|expansion tank|tankless|boiler.*domestic", re.I)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rd, header, h = W.open_rows(sys.stdin.buffer)
    ix = {k: header.index(k) for k in KEEP}
    width = len(header)
    rows = kept = 0
    with open(OUT / "extract_tmp.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(KEEP + ("why",))
        for r in rd:
            rows += 1
            if len(r) != width or r[ix["PPM/UPM"]].strip() != "UPM":
                continue
            plumb = r[ix["SystemCode"]].strip() == "D20" and r[ix["SubsystemCode"]].strip() in PLUMB_SUBS
            hot = bool(HOT_RE.search(r[ix["WODescription"]]))
            if plumb or hot:
                w.writerow([r[ix[k]] for k in KEEP] + [("plumb_code" if plumb else "") + ("+" if plumb and hot else "") + ("hot_kw" if hot else "")])
                kept += 1
    ok = h.sha.hexdigest() == W.FMUCD_SHA256 and h.n == W.FMUCD_BYTES
    meta = dict(rows=rows, kept=kept, bytes=h.n, sha256=h.sha.hexdigest(), hash_ok=ok)
    (OUT / "extract_meta.json").write_text(json.dumps(meta, indent=1) + "\n")
    print(json.dumps(meta))
    if not ok:
        sys.exit("HASH MISMATCH: extract not valid; leaving extract_tmp.csv, NOT promoting it")
    (OUT / "extract_tmp.csv").replace(OUT / "extract.csv")


if __name__ == "__main__":
    main()
