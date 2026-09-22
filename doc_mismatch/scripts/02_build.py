"""Stage 2 (root .venv): select cases, label observability, write cases.jsonl + diversity audit."""
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.build import build_cases, write_cases  # noqa: E402

OUT = ROOT.parent / "results" / "docmismatch"
if __name__ == "__main__":
    cases, audit = build_cases(seed=0)
    write_cases(cases, audit, OUT)
    print("total", len(cases), dict(Counter(c["difficulty"] for c in cases)))
    hdr = f"{'family':22s}{'rows':>5s}{'topos':>6s}{'targets':>8s}{'comps':>6s}{'repl':>5s}{'substs':>7s}{'groups':>7s}  observable"
    print(hdr)
    for fam, a in audit.items():
        print(f"{fam:22s}{a['rows']:5d}{a['base_topologies']:6d}{a['distinct_target_connections']:8d}{a['distinct_components']:6d}"
              f"{a['distinct_replacement_endpoints']:5d}{a['distinct_actual_to_documented_substitutions']:7d}{a['distinct_leakage_groups']:7d}  {a['observable']}"
              f"   (pool {a['candidates_passing_hard_filter']}/{a['candidates_proposed']})")
