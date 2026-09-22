import os
"""Stage 3 (root .venv): features, encoder embeddings, all folds/variants/seeds, aggregation, report."""
import json
import pickle
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT.parent / "results" / "docmismatch"
EVAL = OUT / os.environ.get("DM_EVAL_DIR", "eval_scalefree" if os.environ.get("DOCMISMATCH_FEATURES") == "scalefree" else "eval")

if __name__ == "__main__":
    from docmismatch.classify import prepare, zero_shot_case_scores
    from docmismatch.encoder_io import EncoderKit
    from docmismatch.evaluate import aggregate, paired_bootstrap, run_all

    EVAL.mkdir(parents=True, exist_ok=True)
    cases = [json.loads(l) for l in open(OUT / "cases.jsonl")]
    cal = [json.loads(l) for l in open(OUT / "cases_calibration.jsonl")]
    t0 = time.time()
    pkl = EVAL / "prepared.pkl"
    if not pkl.exists() or "--reprepare" in sys.argv:
        data = prepare(cases + cal, EncoderKit())
        with open(pkl, "wb") as f:
            pickle.dump(data, f)
    else:
        data = pickle.load(open(pkl, "rb"))
    print(f"prepared in {time.time() - t0:.0f}s", flush=True)
    res = run_all(cases, cal, pkl, n_procs=8)
    zs = {"zero_shot_pretrained_masked": zero_shot_case_scores(data, "masked"), "zero_shot_pretrained_present": zero_shot_case_scores(data, "present")}
    with open(EVAL / "raw.pkl", "wb") as f:
        pickle.dump({"res": res, "zero_shot": zs}, f)
    print(f"total {time.time() - t0:.0f}s; now run scripts/04_aggregate.py")
