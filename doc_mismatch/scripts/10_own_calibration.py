"""Per-topology calibration test: threshold from the held-out topology's OWN clean calibration documents
(cal windows 6-7, 24 docs) vs the cross-topology threshold (other topologies' calibration documents).
Evaluated only on benchmark clean windows 0-5 (physically disjoint from the calibration windows)."""
import json, pickle, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.evaluate import FOLDS, LETTER, SEEDS
from docmismatch.classify import VARIANTS

RES = ROOT.parent / "results" / "docmismatch"
D = RES / "eval_owncal"
cases = {c["case_id"]: c for c in (json.loads(l) for l in open(RES / "cases.jsonl"))}
raw = pickle.load(open(D / "raw.pkl", "rb"))["res"]
Q = 0.90
VS = ["evidence_only", "ev+random_frozen", "ev+pretrained_frozen", "ev+scratch_finetuned", "ev+pretrained_finetuned"]
out = {}
for v in VS:
    rows = {"cross": [], "own": []}
    per = {"cross": {}, "own": {}}
    for fold, d in FOLDS.items():
        if fold == "spec":
            continue
        L = d["test"]; topo = LETTER[L]
        sp = raw["splits"][fold]; uns = set(raw["unsup_cases"][fold])
        neg = [i for i in sp["test"] if cases[i]["label"] == 0 and cases[i]["evidence_window"] <= 5]
        pos = [i for i in sp["test"] if cases[i]["difficulty"] == "hard" and cases[i]["observable"] == "true" and i not in uns]
        for mode in ("cross", "own"):
            fp, rc = [], []
            for s in SEEDS:
                sc = raw["scores"][(fold, v, s)]
                thr = np.quantile([sc[i] for i in (sp["cal"] if mode == "cross" else sp["cal_own"][topo])], Q, method="higher")
                fp.append(np.mean([sc[i] > thr for i in neg])); rc.append(np.mean([sc[i] > thr for i in pos]))
            per[mode][L] = (float(np.mean(fp)), float(np.mean(rc)), len(neg), len(pos))
    out[v] = per
    print(f"{v}")
    for mode in ("cross", "own"):
        p = per[mode]
        fpr = np.mean([p[L][0] for L in "ABCD"]); rec = np.mean([p[L][1] for L in "ABCD"])
        print(f"   {mode:5s} threshold: clean FPR by topology " + " ".join(f"{L}={p[L][0]:.2f}" for L in "ABCD") + f" | mean {fpr:.2f} | recall(hard-obs) " + " ".join(f"{L}={p[L][1]:.2f}" for L in "ABCD") + f" | mean {rec:.2f}")
json.dump({v: {m: {L: list(t) for L, t in d.items()} for m, d in per.items()} for v, per in out.items()}, open(D / "own_calibration.json", "w"), indent=1)
