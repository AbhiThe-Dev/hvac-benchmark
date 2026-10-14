"""Compare manufacturers' troubleshooting claims (data/oem_claims.csv) with the physics matrix. Documents, not simulation.

    uv run python scripts/08_oem_compare.py --validate                 # check the claims file against the frozen schema
    uv run python scripts/08_oem_compare.py --make-sample              # write data/oem_verify_sample.csv for blind verification
    uv run python scripts/08_oem_compare.py [--out output]            # analysis and report (uses data/oem_verification.csv when present)
"""
import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hotwater_dx import oem as OE  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "output"))
    ap.add_argument("--claims", default=str(ROOT / "data" / "oem_claims.csv"))
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--make-sample", action="store_true")
    a = ap.parse_args()
    rows = OE.read_claims(Path(a.claims))
    problems = OE.validate(rows)
    print(f"{len(rows)} claims; {len(problems)} problems")
    for p in problems[:40]:
        print("  ", p)
    if a.validate:
        return
    if a.make_sample:
        sample = OE.verification_sample(rows)
        cols = ["claim_id", "manufacturer", "doc_title", "doc_url", "locator", "anchor", "symptom", "cause_text", "check_text", "expected_obs"]
        with open(ROOT / "data" / "oem_verify_sample.csv", "w", newline="") as f:
            wr = csv.writer(f)
            wr.writerow(cols)
            for r in sample:
                wr.writerow([r[c] for c in cols])
        print(f"wrote {len(sample)} claims to data/oem_verify_sample.csv (cause_id, check_id and direction are withheld)")
        return
    if problems:
        sys.exit("fix the claims file first")
    vpath = ROOT / "data" / "oem_verification.csv"
    ver = [r for r in csv.DictReader(open(vpath, newline="")) if r.get("claim_id")] if vpath.exists() else None
    vs = OE.verification_summary(rows, ver) if ver else None
    dropped = set(vs["dropped"]) if vs else set()
    cells = OE.load_cells(ROOT / "output" / "matrix.json")
    an = OE.analyse(rows, cells, dropped)
    sc = OE.scorecard(an, vs)
    OE.write_report(Path(a.out), an, vs, sc, rows)
    print("frozen hash", OE.frozen_hash())
    for k, ok, ev in sc:
        print(f"{k:4s} {'-' if ok is None else ('holds' if ok else 'FAILS'):6s} {ev[:400]}")
    # sensitivity (a deviation from the frozen access rule, see PREREGISTRATION.md Deviations): drop the pump-class rows whose PDF text was read through a third-party proxy
    proxy = {r["claim_id"] for r in rows if r["claim_id"].startswith("P-") and ".pdf" in r["doc_url"].lower()}
    an2 = OE.analyse(rows, cells, dropped | proxy)
    sc2 = OE.scorecard(an2, vs)
    OE.write_report(Path(a.out), an2, vs, sc2, rows, suffix="_no_proxy", note="sensitivity: without the rows read through a proxy")
    print(f"--- without the {len(proxy)} proxy-read rows ({an2['n_scored']} scored) ---")
    for k, ok, ev in sc2:
        print(f"{k:4s} {'-' if ok is None else ('holds' if ok else 'FAILS'):6s} {ev[:400]}")


if __name__ == "__main__":
    main()
