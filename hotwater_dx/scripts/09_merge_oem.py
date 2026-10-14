"""Merge the readers' JSON parts (data/parts/*.json) into data/oem_claims.csv and validate against the frozen schema. Documents, not simulation.

    uv run python scripts/09_merge_oem.py
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hotwater_dx import oem as OE  # noqa: E402


def main() -> None:
    rows = []
    for p in sorted(q for q in (ROOT / "data" / "parts").glob("*.json") if not q.name.startswith("V")):
        part = json.loads(p.read_text())
        for r in part:
            r = {k: ("" if r.get(k) is None else str(r.get(k))) for k in OE.SCHEMA}
            rows.append(r)
        print(f"{p.name}: {len(part)} rows")
    with open(ROOT / "data" / "oem_claims.csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=OE.SCHEMA)
        wr.writeheader()
        wr.writerows(rows)
    problems = OE.validate(rows)
    print(f"{len(rows)} rows; {len(problems)} problems")
    for q in problems[:60]:
        print("  ", q)
    vers = []
    for p in sorted((ROOT / "data" / "parts").glob("V*.json")):
        vers += [{k: ("" if x.get(k) is None else str(x.get(k))) for k in ("claim_id", "status", "cause_id_blind", "check_id_blind", "dir_blind", "notes")} for x in json.loads(p.read_text())]
    if vers:
        with open(ROOT / "data" / "oem_verification.csv", "w", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=("claim_id", "status", "cause_id_blind", "check_id_blind", "dir_blind", "notes"))
            wr.writeheader()
            wr.writerows(vers)
        print(f"verification: {len(vers)} rows")
    sc = OE.scored(rows)
    print(f"scored rows (DIRECT, READ_FULL, deduplicated): {len(sc)}; manufacturers: {len({r['manufacturer'].strip().lower() for r in sc})}")


if __name__ == "__main__":
    main()
