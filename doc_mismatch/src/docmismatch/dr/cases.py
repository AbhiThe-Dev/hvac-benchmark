"""Case builder for the DR study: one uniform rule for every building (existing A-H and all DR buildings), so arms differ only in physics/telemetry.

Per building, per hard family: exhaustive proposals (`corruptions.propose_hard`) -> structural + physical-plausibility filter -> observability audit on a
deterministic subset -> greedy pick of `per_family` cases with DISTINCT changed members and distinct substitutions (one observable=true first, the rest
from ambiguous / unobservable so the unobservable slice is kept and labelled). One row per physical event; a hard event has exactly one evidence window.
Clean rows use one row per window (8 per building). Easy (implausible) rows are produced separately and never enter hard metrics.
Every row says it is synthetic and not real-world verified.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from .. import build as B
from ..corruptions import EASY_TYPES, HARD_FAMILIES, Event, is_hard_ok, propose_easy, propose_hard
from ..data import N_WINDOWS, Base, load_base
from ..evidence import make_evidence
from ..observability import event_observability
from ..rules import apply_edits, true_doc

PROV = {"topology_provenance": "synthetic_openstudio", "simulation_provenance": "energyplus_simulation", "mismatch_provenance": "synthetically_injected",
        "real_world_verified": False, "synthetic": True}
OBS_SUBSET = 40          # observability audits per (building, family): deterministic subset of the plausible proposals


def _h(s: str) -> int:
    return int(hashlib.sha1(s.encode()).hexdigest()[:8], 16)


def topo_signature(b: Base, spec: dict | None) -> str:
    n = lambda *k: len(b.ids(*k))  # noqa: E731
    rh = spec["reheat"] if spec else ("hydronic" if any(b.nodes[m].get("medium") == "hot_water" for _, m in b.slot_edges.get("coil_vav", [])) else "n/a")
    return f"ahu{n('AHU')}_vav{n('VAV')}_hw{n('HWL')}_chw{n('CHWL')}_{rh}"


def _pick(cands: list, k: int, used: Counter, rng: np.random.Generator) -> list:
    """greedy: prefer events whose changed members/owners were used least, i.e. distinct physical targets"""
    pool = list(cands)
    rng.shuffle(pool)
    out = []
    while pool and len(out) < k:
        best = min(pool, key=lambda e: (max((used[c] for c in e.members() + e.owners()), default=0), sum(used[c] for c in e.members() + e.owners())))
        pool.remove(best)
        out.append(best)
        for c in best.members() + best.owners():
            used[c] += 1
    return out


def _case(b: Base, e: Event, obs: dict, window: int, seed: int, sig: str, meta: dict) -> dict:
    truth, doc = true_doc(b), apply_edits(true_doc(b), e.removed, e.added)
    touched = {(s, m) for s, _, m in e.removed + e.added}
    actual = [B.edge_dict(b, s, o, m) for s, es in truth.items() for o, m in es if (s, m) in touched]
    documented = [B.edge_dict(b, s, o, m) for s, es in doc.items() for o, m in es if (s, m) in touched]
    p = e.plaus
    dp = sorted(o for _, o, _ in e.removed) == sorted(o for _, o, _ in e.added) and sorted(m for _, _, m in e.removed) == sorted(m for _, _, m in e.added)
    return {
        "degree_preserving": dp, "case_id": f"case_{e.event_id}", "physical_event_id": e.event_id, "building_id": b.tid, "topology_id": b.tid,
        "topology_signature": sig, "label": 1, "difficulty": e.difficulty, "corruption_type": e.family, "corruption_subtype": e.subtype,
        "removed": [list(x) for x in e.removed], "added": [list(x) for x in e.added], "actual_connection": actual, "documented_connection": documented,
        "plausibility_confounded": e.plausibility_confounded, "observable": obs["observable"], "observability_detail": obs["edges"],
        "compatibility_checks": {"same_class": p.same_class, "same_medium": p.same_medium, "same_relation": p.same_relation, "same_direction": p.same_direction,
                                 "replacement_differs": p.replacement_differs, "valid_cardinality": e.checks["valid_cardinality"], "no_duplicate_edge": e.checks["no_duplicate_edge"],
                                 "no_orphaned_equipment": e.checks["no_orphan_member"] and e.checks["no_orphan_owner"], "graph_valid": e.checks["graph_valid"],
                                 "capacity_plausible": p.capacity_ok, "size_plausible": p.size_ok, "physically_plausible": p.all() and e.checks["graph_valid"]},
        "evidence_window": window, "evidence_seed": seed, "provenance": {**PROV, "documentation_error": "synthetic"}, **meta,
    }


def _clean(b: Base, window: int, sig: str, meta: dict) -> dict:
    eid = f"clean_{b.tid}_w{window}"
    return {"case_id": f"case_{eid}", "physical_event_id": eid, "building_id": b.tid, "topology_id": b.tid, "topology_signature": sig, "label": 0, "difficulty": "clean",
            "corruption_type": "none", "corruption_subtype": "none", "degree_preserving": True, "removed": [], "added": [], "actual_connection": [], "documented_connection": [],
            "plausibility_confounded": False, "observable": "n/a", "observability_detail": [], "compatibility_checks": {}, "evidence_window": window,
            "evidence_seed": _h(eid) % 1_000_003, "provenance": {**PROV, "documentation_error": "none"}, **meta}


def build_building_cases(tid: str, per_family: int = 4, easy_per_type: int = 2, seed: int = 0, spec: dict | None = None) -> tuple[list[dict], list[dict], dict]:
    """(hard+clean cases, easy cases, counts). `spec` = the building's DR spec (or None for the existing A-H buildings)."""
    b = load_base(tid)
    sig = topo_signature(b, spec)
    meta = {"suite": spec["suite"] if spec else "existing", "synthetic_note": "SYNTHETIC building and SYNTHETIC documentation error; not real-world verified"}
    rng = np.random.default_rng(_h(f"{seed}|{tid}"))
    hard, counts = [], {}
    by_fam: dict[str, list] = defaultdict(list)
    n_prop = Counter()
    for e in propose_hard(b):
        n_prop[e.family] += 1
        if is_hard_ok(e):
            by_fam[e.family].append(e)
    for fam in HARD_FAMILIES:
        pool = by_fam[fam]
        order = sorted(pool, key=lambda e: _h(f"{seed}|{e.event_id}"))[:OBS_SUBSET]
        audited = []
        for e in order:
            h = _h(e.event_id)
            w, s = h % N_WINDOWS, h % 1_000_003
            audited.append((e, event_observability(b, make_evidence(b, w, s), e), w, s))
        look = {e.event_id: (e, o, w, s) for e, o, w, s in audited}
        used: Counter = Counter()
        obs_true = [e for e, o, *_ in audited if o["observable"] == "true"]
        rest = [e for e, o, *_ in audited if o["observable"] != "true"]
        n_true = min(len(obs_true), max(1, per_family // 2)) if per_family > 1 else min(len(obs_true), 1)
        picked = _pick(obs_true, n_true, used, rng)
        picked += _pick(rest, per_family - len(picked), used, rng)
        if len(picked) < per_family:
            picked += _pick([e for e in obs_true if e not in picked], per_family - len(picked), used, rng)
        for e in picked:
            ee, o, w, s = look[e.event_id]
            hard.append(_case(b, ee, o, w, s, sig, meta))
        counts[fam] = dict(proposed=n_prop[fam], plausible=len(pool), audited=len(audited), picked=len(picked))
    easy_pool: dict[str, list] = defaultdict(list)
    for e in propose_easy(b):
        easy_pool[e.subtype].append(e)
    easy = []
    for sub in EASY_TYPES:
        for e in _pick(easy_pool[sub], easy_per_type, Counter(), rng):
            h = _h(e.event_id)
            easy.append(_case(b, e, {"observable": "n/a", "edges": []}, h % N_WINDOWS, h % 1_000_003, sig, meta))
    clean = [_clean(b, w, sig, meta) for w in range(N_WINDOWS)]
    return hard + clean, easy, counts


def assign_groups(cases: list[dict]) -> None:
    B._assign_groups(cases)


def family_audit(cases: list[dict], sims_field: str = "topology_id") -> dict:
    """per hard family: rows, unique physical simulations, base topologies (signatures), distinct physical targets, distinct actual->documented substitutions, observability"""
    out = {}
    for fam in HARD_FAMILIES:
        rows = [c for c in cases if c["corruption_type"] == fam]
        if not rows:
            continue
        targets = {(c["topology_id"], e["src"], e["dst"]) for c in rows for e in c["actual_connection"]}
        subs = {(c["topology_id"], a["slot"], a["src"], a["dst"], d["src"], d["dst"]) for c in rows for a, d in B._pair_actual_documented(c)}
        out[fam] = {"rows": len(rows), "unique_physical_simulations": len({c[sims_field] for c in rows}), "base_topologies": len({c["topology_signature"] for c in rows}),
                    "distinct_physical_targets": len(targets), "distinct_actual_to_documented_pairs": len(subs),
                    "distinct_leakage_groups": len({c["group_id"] for c in rows}), "observable": dict(Counter(c["observable"] for c in rows)),
                    "degree_preserving_rows": sum(1 for c in rows if c["degree_preserving"])}
    return out


def write_jsonl(cases: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for c in cases:
            f.write(json.dumps(c) + "\n")
