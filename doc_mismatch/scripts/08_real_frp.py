"""Real-data evidence-vs-structure test on the ORNL FRP RTU-VAV data (see docmismatch.real_frp)."""
import json, pickle, sys, time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.real_frp import *  # noqa
from docmismatch import real_frp as R

OUT = ROOT.parent / "results" / "docmismatch" / "real_frp"
OUT.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    t0 = time.time()
    wins = R.load_windows()
    events = R.all_events()
    W, Ev = len(wins), len(events)
    score = np.zeros((Ev, W)); clean = np.zeros(W); obs = np.empty((Ev, W), dtype=object)
    for w, win in enumerate(wins):
        bd = R.make_bundle(win["series"])
        S = {slot: R.edge_score_matrix(R.slot_matrix(bd, slot)) for slot in R.SLOTS}
        clean[w] = R.doc_score(S, None)
        for e, ev in enumerate(events):
            score[e, w] = R.doc_score(S, ev)
            obs[e, w] = R.observability(win["series"], ev)
    print(f"scored {Ev} events x {W} windows in {time.time() - t0:.0f}s", flush=True)
    pickle.dump({"events": events, "wins": [{k: v for k, v in w.items() if k != 'series'} for w in wins], "score": score, "clean": clean, "obs": obs}, open(OUT / "rule_scores.pkl", "wb"))
