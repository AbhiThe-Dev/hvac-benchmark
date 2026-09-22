import os
"""Re-aggregate saved raw scores (no retraining) and write metrics/comparisons."""
import json, pickle, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT.parent / "results" / "docmismatch"; EVAL = OUT / os.environ.get("DM_EVAL_DIR", "eval_scalefree" if os.environ.get("DOCMISMATCH_FEATURES") == "scalefree" else "eval")
from docmismatch.evaluate import aggregate, paired_bootstrap

cases = [json.loads(l) for l in open(OUT / "cases.jsonl")]
raw = pickle.load(open(EVAL / "raw.pkl", "rb"))
res, zs = raw["res"], raw["zero_shot"]
metrics = aggregate(res, cases, zs)
(EVAL / "metrics.json").write_text(json.dumps(metrics, indent=1))
comps = {}
pairs = {"finetuned_ev": ("ev+pretrained_finetuned", "ev+scratch_finetuned"), "frozen_ev": ("ev+pretrained_frozen", "ev+random_frozen"),
         "finetuned_struct": ("struct+pretrained_finetuned", "struct+scratch_finetuned"), "frozen_struct": ("struct+pretrained_frozen", "struct+random_frozen"),
         "pretrained_ft_vs_evidence_only": ("ev+pretrained_finetuned", "evidence_only"), "pretrained_frozen_vs_evidence_only": ("ev+pretrained_frozen", "evidence_only"),
         "evidence_vs_struct": ("evidence_only", "struct_only")}
for name, (a, b) in pairs.items():
    for sl in ("hard_observable", "hard", "hard_not_observable", "hard_degree_preserving", "hard_observable_dp"):
        comps[f"loto/{name}/{sl}"] = paired_bootstrap(res, cases, a, b, sl, n_boot=int(os.environ.get("DM_NBOOT", "2000")))
        comps[f"spec_C/{name}/{sl}"] = paired_bootstrap(res, cases, a, b, sl, folds=("spec",), test_topos=("C",), n_boot=int(os.environ.get("DM_NBOOT", "2000")))
(EVAL / "comparisons.json").write_text(json.dumps(comps, indent=1))
print("ok")
