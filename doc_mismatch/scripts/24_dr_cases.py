"""Build cases for every building set of the DR study and write per-set jsonl + per-family diversity audit.

  physics_pipeline/.venv/bin/python doc_mismatch/scripts/24_dr_cases.py [--procs N]
Sets: existing (A-H), each DR suite. Observability is labelled under legacy noise (arm-independent). Uses only building physics; no model.
"""
import json, sys, time
import multiprocessing as mp
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.dr import cases as C, spec as DS  # noqa: E402

DR = ROOT.parent / "results" / "docmismatch" / "dr"
PER_FAMILY = 4
EXISTING = ["sys03_psz_ac", "sys07_vav_reheat", "vav_2ahu_2loops", "vav_3ahu_2loops", "dev_E", "dev_F", "dev_G", "dev_H"]


def job(a):
    tid = a
    from docmismatch.dr.pools import building_spec
    return tid, C.build_building_cases(tid, per_family=PER_FAMILY, spec=building_spec(tid))


def main():
    procs = int(sys.argv[sys.argv.index("--procs") + 1]) if "--procs" in sys.argv else 1
    spec = json.loads((DR / "spec.json").read_text())
    sets = {"existing": EXISTING}
    for s, v in spec["suites"].items():
        sets[s] = [b["id"] for b in v["buildings"]]
    tids = [t for v in sets.values() for t in v]
    t0 = time.time()
    with mp.get_context("fork").Pool(procs) as P:
        res = dict(P.map(job, tids, chunksize=1))
    audit, summary = {}, {}
    for name, ids in sets.items():
        hard_clean, easy, counts = [], [], {}
        for t in ids:
            hc, e, c = res[t]
            hard_clean += hc; easy += e; counts[t] = c
        C.assign_groups(hard_clean)
        C.write_jsonl(hard_clean, DR / "cases" / f"cases_{name}.jsonl")
        C.write_jsonl(easy, DR / "cases" / f"easy_{name}.jsonl")
        hard = [c for c in hard_clean if c["label"] == 1]
        audit[name] = C.family_audit(hard_clean)
        summary[name] = dict(buildings=len(ids), hard=len(hard), clean=len(hard_clean) - len(hard), easy=len(easy),
                             observable={k: sum(1 for c in hard if c["observable"] == k) for k in ("true", "ambiguous", "false")}, generation_counts=counts)
        print(name, summary[name]["buildings"], "hard", len(hard), "clean", summary[name]["clean"], "easy", len(easy), summary[name]["observable"], flush=True)
    (DR / "case_audit.json").write_text(json.dumps(dict(summary=summary, audit=audit), indent=1))
    print(f"{time.time() - t0:.0f}s")


main()
