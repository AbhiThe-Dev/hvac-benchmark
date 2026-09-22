"""v2: recompute observability with uninformative channels masked (missing) instead of scored.
The case SELECTION is unchanged; only the `observable` labels can move. Old labels are kept in `observable_v1`."""
import json, sys, collections
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.data import load_base
from docmismatch.evidence import make_evidence
from docmismatch.observability import event_observability
from docmismatch.corruptions import Event
from docmismatch.rules import Plausibility

OUT = ROOT.parent / "results" / "docmismatch"
cases = [json.loads(l) for l in open(OUT / "eval_v1" / "cases_v1.jsonl")]
bases, moved = {}, collections.Counter()
for c in cases:
    c.setdefault("observable_v1", c["observable"])
    if c["difficulty"] == "hard":
        b = bases.setdefault(c["topology_id"], load_base(c["topology_id"]))
        e = Event(c["topology_id"], c["corruption_type"], c["corruption_subtype"], "hard", [tuple(x) for x in c["removed"]], [tuple(x) for x in c["added"]])
        o = event_observability(b, make_evidence(b, c["evidence_window"], c["evidence_seed"]), e)
        c["observable"], c["observability_detail"] = o["observable"], o["edges"]
        moved[(c["topology_letter"], c["observable_v1"], c["observable"])] += 1
with open(OUT / "cases.jsonl", "w") as f:
    for c in cases:
        f.write(json.dumps(c) + "\n")
print("label transitions (topology, v1 -> v2): count")
for k, v in sorted(moved.items()):
    if k[1] != k[2]:
        print("  CHANGED", k, v)
print("unchanged:", sum(v for k, v in moved.items() if k[1] == k[2]), " changed:", sum(v for k, v in moved.items() if k[1] != k[2]))
print("v2 counts:", collections.Counter(c["observable"] for c in cases if c["difficulty"] == "hard"), " v1:", collections.Counter(c["observable_v1"] for c in cases if c["difficulty"] == "hard"))
