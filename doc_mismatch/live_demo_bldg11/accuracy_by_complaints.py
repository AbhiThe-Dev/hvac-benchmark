"""Accuracy by number of complaints per visit, tabulated from the registered Addendum 31 raw results (results/docmismatch/troubleshoot_joint2/joint2_raw.pkl; no new simulation).
Exploratory tabulation: the complaint count is not assigned, so visits with more complaints are mostly shared-cause visits.

  .venv/bin/python doc_mismatch/live_demo_bldg11/accuracy_by_complaints.py
"""
import pickle, sys
import numpy as np
sys.path.insert(0, "doc_mismatch/src")
raw = pickle.load(open("results/docmismatch/troubleshoot_joint2/joint2_raw.pkl", "rb"))
print("cells:", [str(c["cell"]) for c in raw][:18])
def collect(pol, rel=None):
    N, C, K = [], [], []
    for c in raw:
        if rel and c["cell"].rel != rel: continue
        p = c["pol"][pol]
        N.append(np.asarray(c["n_compl"])); C.append(np.asarray(p["correct"])); K.append(np.asarray(c["kind"]))
    return np.concatenate(N), np.concatenate(C), np.concatenate(K)
def table(pol, rel=None, kind=None):
    n, cor, kd = collect(pol, rel)
    rows = []
    rng = np.random.default_rng(1)
    for k in (1, 2, 3, 4, 5):
        m = (n == k) if k < 5 else (n >= 5)
        if kind: m &= (kd == kind)
        if m.sum() == 0: rows.append((k, 0, None, None, None)); continue
        per = cor[m].sum() / n[m].sum()
        allr = float((cor[m] == n[m]).mean())
        idx = [rng.integers(m.sum(), size=m.sum()) for _ in range(500)]
        nn, cc = n[m], cor[m]
        lo, hi = np.percentile([cc[i].sum() / nn[i].sum() for i in idx], [2.5, 97.5])
        rows.append((k, int(m.sum()), per, (lo, hi), allr))
    return rows
for pol in (("T3", "tool_ticket_memo2"), ("T2", "tool_ticket_memo2"), ("T3", "tool_joint2")):
    for rel in (None, "R0"):
        print(f"\n== {pol}  checks: {'as the tool assumes (R0 cells)' if rel else 'all 18 cells pooled'}")
        print(" complaints | visits | per-complaint accuracy (95% CI) | visits with EVERY complaint right")
        for k, nv, per, ci, allr in table(pol, rel):
            lab = f"{k}" if k < 5 else "5+"
            print(f"  {lab:>3} | {nv:>5} | " + (f"{100*per:5.1f}% ({100*ci[0]:.0f}-{100*ci[1]:.0f}) | {100*allr:5.1f}%" if nv else "—"))
print("\n== by kind, T3 routine, R0 cells, 2 complaints")
for kind in ("multi", "shared"):
    for k, nv, per, ci, allr in table(("T3", "tool_ticket_memo2"), "R0", kind)[:3]:
        if nv: print(f"  {kind} n={k}: visits {nv}, per-complaint {100*per:.1f}%, all right {100*allr:.1f}%")
