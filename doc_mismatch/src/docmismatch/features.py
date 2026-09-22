"""Per-documented-edge feature rows for one case.

Inputs are ONLY the documented graph and the case's physical evidence: no node
ids, no labels, no knowledge of which edit was applied. Every row is one
documented edge (or one "orphan slot" where documentation omits a required
connection). Edge label = 1 iff the documented edge was added by the corruption.
"""

from __future__ import annotations

from collections import Counter, defaultdict

import numpy as np

from .data import SLOT_NAMES, SLOTS, Base
from .evidence import CLOSURE_SLOTS, closure_residual, make_context, make_evidence, pair_errors
from .rules import MAX_PER_OWNER_CLASS, Doc, apply_edits, true_doc

EPS = 1e-9
N_CH = 3
FEATURE_NAMES: list[str] = (
    [f"slot={s}" for s in SLOT_NAMES]
    + [f"ch{c}_{n}" for c in range(N_CH) for n in ("logerr", "par_margin", "par_rank", "child_margin", "child_rank")]
    + ["clos_gain", "clos_best_alt", "clos_margin", "has_par_alt", "has_child_alt", "extra_owner", "card_violation", "orphan_slot"]
    + [f"ch{c}_missing" for c in range(N_CH)]
)
N_FEATURES = len(FEATURE_NAMES)


def _margin(e: float, alts: list[float]) -> tuple[float, float]:
    alts = [a for a in alts if not np.isnan(a)]
    if not alts or np.isnan(e):
        return 0.0, 0.5
    m = min(alts)
    return (e - m) / (abs(e) + abs(m) + EPS), float(np.mean([a < e for a in alts]))


def case_doc(base: Base, case: dict) -> Doc:
    return apply_edits(true_doc(base), [tuple(x) for x in case["removed"]], [tuple(x) for x in case["added"]])


def case_rows(base: Base, case: dict) -> list[dict]:
    doc = case_doc(base, case)
    truth = true_doc(base)
    ev = make_evidence(base, case["evidence_window"], case["evidence_seed"], sensor=case.get("sensor"))
    ctx = make_context(base, ev)
    added = {(s, o, m) for s, o, m in map(tuple, case["added"])}
    rows: list[dict] = []
    for slot in SLOT_NAMES:
        t_edges = truth.get(slot, [])
        d_edges = doc.get(slot, [])
        if not t_edges and not d_edges:
            continue
        owners = sorted({o for o, _ in t_edges})
        members = sorted({m for _, m in t_edges})
        E = {}
        if slot != "fan_ahu":
            for o in owners:
                for m in members:
                    if base.cls(o) == base.cls(o):  # all pairs; class filtering applied when reading alternatives
                        E[(o, m)] = pair_errors(base, ev, slot, o, m, slice(None), ctx)
        by_member = defaultdict(list)
        by_owner = defaultdict(list)
        for o, m in d_edges:
            by_member[m].append(o)
            by_owner[o].append(m)
        cap = MAX_PER_OWNER_CLASS[slot]
        s_one_hot = [1.0 if s == slot else 0.0 for s in SLOT_NAMES]
        for o, m in d_edges:
            feat = list(s_one_hot)
            has_pa = has_ca = 0.0
            if slot != "fan_ahu":
                par_alts = [x for x in owners if x != o and base.cls(x) == base.cls(o)]
                child_alts = [x for x in members if x != m and base.cls(x) == base.cls(m)]
                has_pa, has_ca = float(bool(par_alts)), float(bool(child_alts))
                missing = []
                for c in range(N_CH):
                    e = E[(o, m)][c]
                    pm, pr = _margin(e, [E[(x, m)][c] for x in par_alts])
                    cm, cr = _margin(e, [E[(o, x)][c] for x in child_alts])
                    miss = bool(np.isnan(e))
                    missing.append(float(miss))
                    feat += [0.0 if miss else float(np.log1p(max(e, 0.0) * 10.0)), pm, pr, cm, cr]
            else:
                feat += [0.0] * (5 * N_CH)
                missing = [1.0] * N_CH
            cg = cb = cmg = 0.0
            if slot in CLOSURE_SLOTS:
                S = by_owner[o]
                r_with = closure_residual(ev, o, S, slot=slot)
                r_wo = closure_residual(ev, o, [x for x in S if x != m], slot=slot)
                cg = (r_with - r_wo) / (r_with + r_wo + EPS)
                alt_g = []
                for x in [x for x in owners if x != o and base.cls(x) == base.cls(o)]:
                    Sx = by_owner.get(x, [])
                    r0 = closure_residual(ev, x, Sx, slot=slot)
                    r1 = closure_residual(ev, x, Sx + [m], slot=slot)
                    alt_g.append((r1 - r0) / (r1 + r0 + EPS))
                cb = min(alt_g) if alt_g else 0.0
                cmg = (cg - cb) if alt_g else 0.0
            n_own = len(by_member[m])
            per_class = Counter(base.cls(x) for x in by_owner[o])
            card_v = float(cap is not None and per_class[base.cls(m)] > cap)
            feat += [cg, cb, cmg, has_pa, has_ca, float(n_own > 1), card_v, 0.0] + missing
            assert len(feat) == N_FEATURES
            rows.append({"slot": slot, "owner": o, "member": m, "x": np.array(feat, dtype=np.float32),
                         "y": 1.0 if (slot, o, m) in added else 0.0, "kind": "edge"})
        # orphan slots: a member the documentation leaves without any owner
        for m in members:
            if not by_member[m]:
                feat = list(s_one_hot) + [0.0] * (5 * N_CH + 4) + [0.0, 0.0, 0.0, 1.0] + [0.0] * N_CH
                assert len(feat) == N_FEATURES
                rows.append({"slot": slot, "owner": None, "member": m, "x": np.array(feat, dtype=np.float32), "y": 1.0, "kind": "orphan"})
    return rows
