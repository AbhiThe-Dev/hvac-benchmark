"""Benchmark cases for the expansion topologies, using the unchanged corruption + plausibility + observability machinery of build.py.

  .venv/bin/python doc_mismatch/scripts/20_make_sim_cases.py

Writes results/docmismatch/cases_dev_extra.jsonl (dev_E..H) and results/docmismatch/cases_sealed_sim.jsonl (seal_S1..S4);
never touches cases.jsonl / cases_calibration.jsonl. Case selection is model-free (physics-only observability audit).
"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import build  # noqa: E402

RES = ROOT.parent / "results" / "docmismatch"
MAN = RES / "active" / "sim_manifest.json"
SPEC = RES / "active" / "sim_spec.json"


def make(ids: list[str], letters: dict[str, str], seed: int):
    src = {t: f"built with build_ext.py from sim_spec.json (parametric envelope + multi-AHU VAV-reheat HVAC), role in spec" for t in ids}
    with mock.patch.object(build, "TOPOLOGIES", tuple(ids)), \
            mock.patch.dict(build.TOPOLOGY_LETTER, letters), mock.patch.dict(build.MODEL_SOURCE, src):
        return build.build_cases(seed=seed)


def summarise(cases):
    hard = [c for c in cases if c["difficulty"] == "hard"]
    return {
        "n_cases": len(cases), "by_difficulty": dict(Counter(c["difficulty"] for c in cases)),
        "hard_by_family": dict(Counter(c["corruption_type"] for c in hard)),
        "hard_by_observable": dict(Counter(c["observable"] for c in hard)),
        "hard_family_x_observable": {f"{c[0]}|{c[1]}": n for c, n in Counter((c["corruption_type"], c["observable"]) for c in hard).items()},
        "hard_by_topology": dict(Counter(c["topology_id"] for c in hard)),
        "degree_preserving": dict(Counter(str(c["degree_preserving"]) for c in hard)),
        "by_topology": dict(Counter(c["topology_id"] for c in cases)),
    }


if __name__ == "__main__":
    man = json.loads(MAN.read_text())
    assert man["spec_sha256"] == hashlib.sha256(SPEC.read_bytes()).hexdigest()
    assert all(man["generation"][t]["status"] == "ok" for t in man["dev_topologies"] + man["sealed_topologies"]), "generate topologies first"
    plan = [("dev_extra", man["dev_topologies"], dict(zip(man["dev_topologies"], "EFGH")), 100, "cases_dev_extra.jsonl"),
            ("sealed_sim", man["sealed_topologies"], {t: t.split("_")[1] for t in man["sealed_topologies"]}, 200, "cases_sealed_sim.jsonl")]
    man["cases"] = {}
    for name, ids, letters, seed, fname in plan:
        cases, audit = make(ids, letters, seed)
        with open(RES / fname, "w") as f:
            for c in cases:
                f.write(json.dumps(c) + "\n")
        man["cases"][name] = {"file": f"results/docmismatch/{fname}", "sha256": hashlib.sha256((RES / fname).read_bytes()).hexdigest(),
                              "build_cases_seed": seed, **summarise(cases),
                              "diversity_audit": {k: {kk: vv for kk, vv in v.items() if kk in ("rows", "base_topologies", "distinct_leakage_groups", "observable", "candidates_proposed", "candidates_passing_hard_filter")} for k, v in audit.items()}}
        print(name, man["cases"][name]["n_cases"], man["cases"][name]["hard_by_family"], man["cases"][name]["hard_by_observable"], flush=True)
    MAN.write_text(json.dumps(man, indent=1))
