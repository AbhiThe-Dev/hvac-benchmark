"""Write the a-priori generation spec + manifest hash BEFORE any expansion topology is simulated.

  python doc_mismatch/scripts/18_make_sim_spec.py            (refuses to overwrite an existing spec)
"""
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.sim_spec import draw_spec  # noqa: E402

ACT = ROOT.parent / "results" / "docmismatch" / "active"
SPEC, MAN = ACT / "sim_spec.json", ACT / "sim_manifest.json"

if __name__ == "__main__":
    if SPEC.exists():
        sys.exit(f"{SPEC} exists; the spec is frozen once written")
    ACT.mkdir(parents=True, exist_ok=True)
    spec = draw_spec()
    SPEC.write_text(json.dumps(spec, indent=1, sort_keys=True))
    h = hashlib.sha256(SPEC.read_bytes()).hexdigest()
    MAN.write_text(json.dumps({
        "spec_file": "results/docmismatch/active/sim_spec.json", "spec_sha256": h,
        "spec_written_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sim_spec_py_sha256": hashlib.sha256((ROOT / "src/docmismatch/sim_spec.py").read_bytes()).hexdigest(),
        "status": "spec_written_before_any_simulation",
        "dev_topologies": [t["id"] for t in spec["topologies"] if t["role"] == "dev"],
        "sealed_topologies": [t["id"] for t in spec["topologies"] if t["role"] == "sealed"],
    }, indent=1))
    print("spec sha256", h)
    for t in spec["topologies"]:
        print(t["id"], t["climate"], "ahu", t["n_ahu"], "vav", t["n_vav"], f'{t["floors"]}x{t["nx"]}x{t["ny"]}', "sat", t["ahu_sat"], t["sat_pattern"], "hw/chw", t["n_hw"], t["n_chw"], "occ", t["occ"])
