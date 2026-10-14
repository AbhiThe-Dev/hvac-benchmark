"""Check a building's control-system export: load it, convert it, and say which connection checks its recorded points can support.

  .venv/bin/python doc_mismatch/scripts/54_intake_check.py EXPORT_DIR [--report OUT.md] [--pool OUT.pkl]

EXPORT_DIR holds points.csv, trends.csv and optionally equipment.csv, connections.csv, context.json (formats: doc_mismatch/INTAKE.md).
--report writes the readiness report (always printed); --pool also builds the reading pool of the documented connections and pickles it. No model is fitted and
nothing is scored: this only says what the data can and cannot support.
"""
import argparse
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.field_pool import build_field_pool  # noqa: E402
from docmismatch.intake import load_export  # noqa: E402
from docmismatch.intake_report import report  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("export_dir")
    ap.add_argument("--report")
    ap.add_argument("--pool")
    a = ap.parse_args()
    fb = load_export(a.export_dir)
    text = report(fb)
    if a.report:
        Path(a.report).parent.mkdir(parents=True, exist_ok=True)
        Path(a.report).write_text(text)
    print(text)
    if a.pool:
        pool = build_field_pool(fb)
        Path(a.pool).write_bytes(pickle.dumps(pool))
        print(f"\npool: {pool.n_slices} day-slices in {len(set(pool.group))} window(s); slots " + ", ".join(f"{s} ({sp.E.shape[2]}x{sp.E.shape[3]})" for s, sp in pool.slots.items()))


main()
