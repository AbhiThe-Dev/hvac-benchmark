"""Convert the downloaded Mortar buildings to intake-format exports and report what each supports. Readiness only: nothing is fitted or scored.

  .venv/bin/python doc_mismatch/scripts/56_mortar_to_intake.py [building ...]

Reads data_cache/mortar__<bldg>.ttl (Brick) and data_cache/timeseries/mortar/ (Parquet streams); writes the exports (~300 MB, regenerable, git-ignored) to data_cache/intake/mortar/<bldg>/,
the small reports to results/docmismatch/intake/mortar/<bldg>/{conversion_notes.md,report.md}, and results/docmismatch/intake/mortar_readiness.md (one table across buildings). Assumptions (units, UTC clock, windows chosen by coverage): see mortar_adapter.py.
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.intake import load_export  # noqa: E402
from docmismatch.intake_report import report, slot_readiness  # noqa: E402
from docmismatch.mortar_adapter import convert_building  # noqa: E402

REPO = ROOT.parent
MORTAR = REPO / "data_cache" / "timeseries" / "mortar"
OUT = REPO / "results" / "docmismatch" / "intake"
EXPORT = REPO / "data_cache" / "intake" / "mortar"
BUILDINGS = ["bldg1", "bldg8", "bldg27", "bldg30", "bldg40", "bldg15"]      # bldg30 == smc (identical stream ids)


def main():
    todo = sys.argv[1:] or BUILDINGS
    rows, t0 = [], time.time()
    for b in todo:
        d, rep = EXPORT / b, OUT / "mortar" / b
        rep.mkdir(parents=True, exist_ok=True)
        s = convert_building(REPO / "data_cache" / f"mortar__{b}.ttl", MORTAR, d, b)
        (rep / "conversion_notes.md").write_text((d / "conversion_notes.md").read_text())
        if not s["windows"]:
            print(f"{b}: no export ({'; '.join(s['notes'])})", flush=True)
            rows.append((b, s, None))
            continue
        fb = load_export(d)
        (rep / "report.md").write_text(report(fb))
        rows.append((b, s, slot_readiness(fb)))
        print(f"{b}: {s['exported']} points, windows {[w['start'] for w in s['windows']]}, {time.time() - t0:.0f}s", flush=True)
    md = ["# Mortar buildings: what their recorded points support (readiness only)", "",
          "Each building is exported as two 42-day windows (chosen by data coverage only), US customary units assumed and range-checked, UTC clock, connections = the Brick model (not field-verified). "
          "Channel cells = share of the documented connections whose points are recorded, cover at least half the hours and vary beyond sensor noise. Per-building detail: `mortar/<bldg>/report.md`.", "",
          "| building | AHU / VAV / zones | exported points | windows (start, coverage) | dropped | ahu_vav ch0/ch1/ch2 | vav_zone ch0/ch1/ch2 |", "|---|---|---|---|---|---|---|"]
    fmt = lambda r: "not documented" if r is None else "/".join(f"{r['channels'].get(k, 0):.0%}" for k in range(3)) + f" ({r['status']})"  # noqa: E731
    for b, s, r in rows:
        if r is None:
            md.append(f"| {b} | {s['ahus']} / {s['vavs']} / {s['zones']} | - | none reached the coverage rule | - | - | - |")
            continue
        sig = ", ".join(f"{k} x{n}" for k, n in sorted(s["by_signal"].items()))
        win = "; ".join(f"{w['start']} ({w['coverage']:.0%})" for w in s["windows"])
        md.append(f"| {b} | {s['ahus']} / {s['vavs']} / {s['zones']} | {s['exported']} ({sig}) | {win} | {len(s['dropped'])} | {fmt(r.get('ahu_vav'))} | {fmt(r.get('vav_zone'))} |")
    (OUT / "mortar_readiness.md").write_text("\n".join(md))
    print("\n".join(md))


main()
