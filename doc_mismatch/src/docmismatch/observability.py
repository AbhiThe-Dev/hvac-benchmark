"""Phase 8: is there enough physical evidence to tell the true connection from the
documented one? Independent of any trained model.

For each changed member we compare the physics-consistency error of the TRUE
owner against the DOCUMENTED (wrong) owner in each of B disjoint time blocks and
each evidence channel (3 pairwise channels + set-level closure for AHU/loop
slots). Channel c "separates" the pair if the true owner has the smaller error
in >= 5/6 blocks with a mean relative gap >= 0.2. A case is
  observable   = some changed edge separates on some channel,
  unobservable = no changed edge has any channel with gap >= 0.08 and a majority of block wins,
  ambiguous    = otherwise.
(Taking the best of four channels is deliberately generous to "observable"; the
0.2-gap / 5-of-6 rule is the guard against noise-level wins.)
"""

from __future__ import annotations

import numpy as np

from .data import HOURS_PER_WINDOW, Base
from .evidence import CLOSURE_SLOTS, closure_residual, make_context, pair_errors
from .rules import Doc, apply_edits, true_doc

N_BLOCKS = 6
WIN_HI, GAP_HI = 5, 0.20
WIN_LO, GAP_LO = 3, 0.08


def _blocks():
    step = HOURS_PER_WINDOW // N_BLOCKS
    return [slice(i * step, (i + 1) * step) for i in range(N_BLOCKS)]


def _gap(err_doc: float, err_true: float) -> float:
    if np.isnan(err_doc) or np.isnan(err_true):
        return 0.0  # channel uninformative for this pair: no evidence either way
    return (err_doc - err_true) / (abs(err_doc) + abs(err_true) + 1e-9)


def edge_separation(base: Base, ev, slot: str, o_true: str, o_doc: str, m: str, doc_true: Doc, doc_new: Doc) -> dict:
    """gaps[channel] = list over blocks of relative (doc - true) error gap."""
    gaps = {c: [] for c in range(4)}
    for sl in _blocks():
        ctx = make_context(base, ev, sl)
        et = pair_errors(base, ev, slot, o_true, m, sl, ctx)
        ed = pair_errors(base, ev, slot, o_doc, m, sl, ctx)
        for c in range(3):
            gaps[c].append(_gap(ed[c], et[c]))
        if slot in CLOSURE_SLOTS:
            rt = rd = 0.0
            for o in {o_true, o_doc}:
                rt += closure_residual(ev, o, [mm for oo, mm in doc_true[slot] if oo == o], sl, slot)
                rd += closure_residual(ev, o, [mm for oo, mm in doc_new[slot] if oo == o], sl, slot)
            gaps[3].append(_gap(rd, rt))
        else:
            gaps[3].append(0.0)
    return gaps


def classify_gaps(gaps: dict) -> tuple[str, dict]:
    best = {}
    status = "unobservable"
    for c, g in gaps.items():
        g = np.array(g)
        wins, mean = int((g > 0).sum()), float(g.mean())
        best[c] = {"wins": wins, "mean_gap": round(mean, 3)}
        if wins >= WIN_HI and mean >= GAP_HI:
            status = "observable"
        elif status != "observable" and wins > WIN_LO and mean >= GAP_LO:
            status = "ambiguous"
    return status, best


def event_observability(base: Base, ev, event) -> dict:
    doc_true = true_doc(base)
    doc_new = apply_edits(doc_true, event.removed, event.added)
    true_owner = {(s, m): o for s, es in doc_true.items() for o, m in es}
    per_edge, statuses = [], []
    for slot, o_doc, m in event.added:
        o_true = true_owner.get((slot, m))
        if o_true is None or o_true == o_doc:
            continue
        gaps = edge_separation(base, ev, slot, o_true, o_doc, m, doc_true, doc_new)
        st, detail = classify_gaps(gaps)
        per_edge.append({"slot": slot, "member": m, "true_owner": o_true, "documented_owner": o_doc, "status": st, "channels": detail})
        statuses.append(st)
    if not statuses:
        return {"observable": "n/a", "edges": []}
    if "observable" in statuses:
        overall = "true"
    elif all(s == "unobservable" for s in statuses):
        overall = "false"
    else:
        overall = "ambiguous"
    return {"observable": overall, "edges": per_edge}
