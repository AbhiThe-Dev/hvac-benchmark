"""Extra clean documents used ONLY to calibrate the decision threshold (never trained on, never scored as benchmark cases)."""
import hashlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.build import TOPOLOGIES, TOPOLOGY_LETTER, PROVENANCE, MODEL_SOURCE

OUT = ROOT.parent / "results" / "docmismatch"
rows = []
for t in TOPOLOGIES:
    for w in (6, 7):
        for k in range(12):
            eid = f"cal_{TOPOLOGY_LETTER[t]}_w{w}_s{k}"
            seed = int(hashlib.sha1(eid.encode()).hexdigest()[:8], 16) % 1_000_003
            rows.append({"case_id": f"case_{eid}", "physical_event_id": eid, "building_id": t, "topology_id": t, "topology_letter": TOPOLOGY_LETTER[t],
                         "label": 0, "difficulty": "calibration", "corruption_type": "none", "corruption_subtype": "none", "degree_preserving": True,
                         "removed": [], "added": [], "actual_connection": [], "documented_connection": [], "plausibility_confounded": False,
                         "observable": "n/a", "observability_detail": [], "compatibility_checks": {}, "evidence_window": w, "evidence_seed": seed,
                         "group_id": f"cal|{t}|w{w}", "provenance": {**PROVENANCE, "model_source": MODEL_SOURCE[t]}})
with open(OUT / "cases_calibration.jsonl", "w") as f:
    for r in rows:
        f.write(json.dumps(r) + "\n")
print(len(rows), "calibration clean documents")
