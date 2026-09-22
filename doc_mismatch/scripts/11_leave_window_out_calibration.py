"""Own-topology threshold calibrated on clean documents from the OTHER evidence windows, tested on the held-out window
(leave-one-window-out over the 8 benchmark clean windows of each held-out topology; threshold = q-quantile 'higher' of the other 7)."""
import json, pickle, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.evaluate import FOLDS, LETTER, SEEDS
RES = ROOT.parent / "results" / "docmismatch"
cases = {c["case_id"]: c for c in (json.loads(l) for l in open(RES / "cases.jsonl"))}
raw = pickle.load(open(RES / "eval_owncal" / "raw.pkl", "rb"))["res"]
VS = ["evidence_only", "ev+random_frozen", "ev+pretrained_frozen", "ev+scratch_finetuned", "ev+pretrained_finetuned"]
res = {}
for q in (0.90, 1.0):
    print(f"--- quantile {q}: clean FPR (held-out window) / recall on hard-observable, by held-out topology ---")
    for v in VS:
        fp = {L: [] for L in "ABCD"}; rc = {L: [] for L in "ABCD"}
        for fold in ("loto_A", "loto_B", "loto_C", "loto_D"):
            L = FOLDS[fold]["test"]; sp = raw["splits"][fold]; uns = set(raw["unsup_cases"][fold])
            clean = {cases[i]["evidence_window"]: i for i in sp["test"] if cases[i]["label"] == 0}
            pos = [i for i in sp["test"] if cases[i]["difficulty"] == "hard" and cases[i]["observable"] == "true" and i not in uns]
            for s in SEEDS:
                sc = raw["scores"][(fold, v, s)]
                for w, iw in clean.items():
                    thr = np.quantile([sc[j] for ww, j in clean.items() if ww != w], q, method="higher")
                    fp[L].append(sc[iw] > thr)
                    rc[L].append(np.mean([sc[i] > thr for i in pos]))
        res[(q, v)] = ({L: float(np.mean(fp[L])) for L in "ABCD"}, {L: float(np.mean(rc[L])) for L in "ABCD"})
        f, r = res[(q, v)]
        print(f"  {v:26s} FPR " + " ".join(f"{L}={f[L]:.2f}" for L in "ABCD") + f" | mean {np.mean(list(f.values())):.2f}   recall " + " ".join(f"{L}={r[L]:.2f}" for L in "ABCD") + f" | mean {np.mean(list(r.values())):.2f}")
json.dump({f"{q}|{v}": {"fpr": a, "recall": b} for (q, v), (a, b) in res.items()}, open(RES / "eval_owncal" / "leave_window_out.json", "w"), indent=1)
