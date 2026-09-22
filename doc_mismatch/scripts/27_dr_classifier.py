"""S-C study (case-level detector +/- pretrained encoder) across DR arms. Caches prepared data and scores.

  physics_pipeline/.venv/bin/python doc_mismatch/scripts/27_dr_classifier.py prep  --procs 9
  physics_pipeline/.venv/bin/python doc_mismatch/scripts/27_dr_classifier.py run   --procs 9 [--arms ...] [--seeds 3] [--variants ...]
Scores -> results/docmismatch/dr/classifier/scores_<arm>_<fold>.pkl  (dict[(fold, variant, seed)] -> {case_id: score}) plus the case metadata.
"""
import json, pickle, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.classify import make_split  # noqa: E402
from docmismatch.dr import classifier_eval as CE, verifier_eval as V  # noqa: E402

arg = lambda k, d: (sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d)  # noqa: E731
PROCS = int(arg("--procs", "1"))
SUITES = ["T1_in_range", "T2_regime", "T3_control", "T4_topology", "T5_climate", "T6_compound"]
TEST_TEL = ("estimated", "legacy", "wide")
DATA = CE.OUT / "prepared.pkl"


def all_cases():
    ids = V.spec_ids()
    A = V.arms()
    cases = []
    seen = set()
    for arm, a in A.items():
        key = (tuple(a["train"]), a["tel"])
        if key in seen:
            continue
        seen.add(key)
        cases += CE.tagged(V.cases_for(a["train"]), a["tel"])
    for su in SUITES:
        for tel in TEST_TEL:
            cases += CE.tagged(V.cases_for(ids[su]), tel)
    for c in cases:
        c["role"] = "train" if any(c["topology_id"] in a["train"] for a in A.values()) else "test"
    by_id = {}
    for c in cases:
        by_id[c["case_id"]] = c
    return list(by_id.values())


def prep():
    CE.OUT.mkdir(parents=True, exist_ok=True)
    cases = all_cases()
    print(len(cases), "case instances to prepare", flush=True)
    t0 = time.time()
    data = CE.prepare_parallel(cases, PROCS)
    DATA.write_bytes(pickle.dumps(data))
    (CE.OUT / "cases_meta.json").write_text(json.dumps({c["case_id"]: {k: c[k] for k in ("topology_id", "label", "difficulty", "corruption_type", "observable", "group_id", "evidence_window", "telemetry", "base_case_id")} for c in cases}))
    print(f"prepared {len(data)} in {time.time() - t0:.0f}s", flush=True)


def run():
    meta = json.loads((CE.OUT / "cases_meta.json").read_text())
    A = V.arms()
    ids = V.spec_ids()
    arms = arg("--arms", ",".join(A)).split(",")
    seeds = list(range(int(arg("--seeds", "3"))))
    variants = arg("--variants", ",".join(CE.VARIANTS)).split(",")
    test_by_su = {su: {tel: [k for k, m in meta.items() if m["topology_id"] in ids[su] and m["telemetry"] == tel] for tel in TEST_TEL} for su in SUITES}
    for arm in arms:
        a = A[arm]
        train_all = [k for k, m in meta.items() if m["topology_id"] in a["train"] and m["telemetry"] == a["tel"]]
        cs = [dict(meta[k], case_id=k) for k in train_all]
        sp = make_split(cs, a["train"])
        tasks = []
        # seen: train on all arm cases, score all test cases (every telemetry) + 'days' held-out cases of the training buildings
        test_all = [k for su in SUITES for tel in TEST_TEL for k in test_by_su[su][tel]]
        for v in variants:
            for s in seeds:
                tasks.append(("seen", v, s, train_all, test_all))
                tasks.append(("days", v, s, sp["train"], sp["val"]))
                for ss in range(4):
                    tr = [k for k in train_all if CE.SEASON_OF_WINDOW[meta[k]["evidence_window"]] != ss]
                    sc = [k for su in SUITES for k in test_by_su[su]["estimated"] if CE.SEASON_OF_WINDOW[meta[k]["evidence_window"]] == ss]
                    tasks.append((f"unseen_s{ss}", v, s, tr, sc))
        f = CE.OUT / f"scores_{arm}.pkl"
        if f.exists():
            print("cached", arm); continue
        t0 = time.time()
        print(f"[{arm}] {len(tasks)} training runs, train cases {len(train_all)}", flush=True)
        scores = CE.run_tasks(tasks, DATA, PROCS)
        f.write_bytes(pickle.dumps(scores))
        print(f"[{arm}] done {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    {"prep": prep, "run": run}[sys.argv[1]]()
