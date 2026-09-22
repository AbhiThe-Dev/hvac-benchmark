"""Assemble the benchmark: select diverse, validated, observability-labelled cases;
add clean and easy cases; group them for leakage-free splits; audit diversity.

Design rules enforced here (see README):
  * one row per physical event; never several paraphrases/windows of one event;
  * diversity-first selection - fewer rows rather than padding with near-duplicates;
  * every case stores provenance and the full compatibility/plausibility record.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from .corruptions import HARD_FAMILIES, EASY_TYPES, Event, is_hard_ok, propose_easy, propose_hard
from .data import N_WINDOWS, SLOTS, Base, load_base
from .evidence import make_evidence
from .observability import event_observability
from .rules import apply_edits, true_doc

TOPOLOGIES = ("sys07_vav_reheat", "sys03_psz_ac", "vav_2ahu_2loops", "vav_3ahu_2loops")
TOPOLOGY_LETTER = {"sys07_vav_reheat": "A", "sys03_psz_ac": "B", "vav_2ahu_2loops": "C", "vav_3ahu_2loops": "D"}
HARD_TARGET_PER_FAMILY = 20
OBSERVABLE_QUOTA = 14  # of the 20, prefer observable ones; remainder keeps an ambiguous/unobservable slice
EASY_TARGET = 30
CLEAN_WINDOWS = tuple(range(N_WINDOWS))

PROVENANCE = {
    "topology_provenance": "synthetic_openstudio",
    "simulation_provenance": "energyplus_simulation",
    "mismatch_provenance": "synthetically_injected",
    "real_world_verified": False,
}
MODEL_SOURCE = {
    "sys07_vav_reheat": "vendored NREL/OpenStudio-resources baseline_sys07.osm, unmodified",
    "sys03_psz_ac": "vendored NREL/OpenStudio-resources baseline_sys03.osm, unmodified",
    "vav_2ahu_2loops": "built with build_models.py on the baseline_sys07 envelope",
    "vav_3ahu_2loops": "built with build_models.py on the baseline_sys07 envelope",
}


def _h(s: str) -> int:
    return int(hashlib.sha1(s.encode()).hexdigest()[:8], 16)


def edge_dict(base: Base, slot: str, o: str, m: str) -> dict:
    s = SLOTS[slot]
    src, dst = (o, m) if s["owner_first"] else (m, o)
    return {"src": src, "dst": dst, "relation": s["rel"], "slot": slot}


def _diverse_pick(cands: list[Event], k: int, rng: np.random.Generator, used: Counter, per_topo: Counter, topo_cap: int) -> list[Event]:
    """Greedy: repeatedly take the candidate whose components were used least so far,
    round-robin over topologies (bounded by topo_cap)."""
    chosen: list[Event] = []
    pool = list(cands)
    rng.shuffle(pool)
    while pool and len(chosen) < k:
        def cost(e: Event):
            comps = e.members() + e.owners()
            return (max(used[(e.topology, c)] for c in comps), sum(used[(e.topology, c)] for c in comps), per_topo[e.topology])
        pool = [e for e in pool if per_topo[e.topology] < topo_cap]
        if not pool:
            break
        best = min(pool, key=cost)
        pool.remove(best)
        chosen.append(best)
        per_topo[best.topology] += 1
        for c in best.members() + best.owners():
            used[(best.topology, c)] += 1
    return chosen


def build_cases(seed: int = 0) -> tuple[list[dict], dict]:
    bases = {t: load_base(t) for t in TOPOLOGIES}
    rng = np.random.default_rng(seed)
    hard_pool: dict[str, list[tuple[Event, dict, int, int]]] = defaultdict(list)
    n_proposed = Counter()
    n_rejected = Counter()
    for t, b in bases.items():
        for e in propose_hard(b):
            n_proposed[e.family] += 1
            if not is_hard_ok(e):
                n_rejected[e.family] += 1
                continue
            h = _h(e.event_id)
            window, ev_seed = h % N_WINDOWS, h % 1_000_003
            obs = event_observability(b, make_evidence(b, window, ev_seed), e)
            hard_pool[e.family].append((e, obs, window, ev_seed))

    selected: list[tuple[Event, dict, int, int]] = []
    for fam in HARD_FAMILIES:
        pool = hard_pool[fam]
        used, per_topo = Counter(), Counter()
        n_topo = len({e.topology for e, *_ in pool}) or 1
        topo_cap = -(-HARD_TARGET_PER_FAMILY // n_topo) + 2
        lookup = {e.event_id: (e, o, w, s) for e, o, w, s in pool}
        obs_true = [e for e, o, *_ in pool if o["observable"] == "true"]
        rest = [e for e, o, *_ in pool if o["observable"] != "true"]
        picked = _diverse_pick(obs_true, OBSERVABLE_QUOTA, rng, used, per_topo, topo_cap)
        picked += _diverse_pick(rest, HARD_TARGET_PER_FAMILY - len(picked), rng, used, per_topo, topo_cap)
        if len(picked) < HARD_TARGET_PER_FAMILY:  # top up from any remaining observable events
            left = [e for e in obs_true if e not in picked]
            picked += _diverse_pick(left, HARD_TARGET_PER_FAMILY - len(picked), rng, used, per_topo, topo_cap + 4)
        selected += [lookup[e.event_id] for e in picked]

    easy_sel: list[tuple[Event, dict, int, int]] = []
    easy_pool: dict[str, list[Event]] = defaultdict(list)
    for t, b in bases.items():
        for e in propose_easy(b):
            easy_pool[e.subtype].append(e)
    used, per_topo = Counter(), Counter()
    for sub in EASY_TYPES:
        picked = _diverse_pick(easy_pool[sub], EASY_TARGET // len(EASY_TYPES), rng, used, per_topo, 10**6)
        for e in picked:
            h = _h(e.event_id)
            easy_sel.append((e, {"observable": "n/a", "edges": []}, h % N_WINDOWS, h % 1_000_003))

    cases: list[dict] = []
    for e, obs, w, s in selected + easy_sel:
        cases.append(_case_from_event(bases[e.topology], e, obs, w, s))
    for t in TOPOLOGIES:
        for w in CLEAN_WINDOWS:
            cases.append(_clean_case(bases[t], w))
    _assign_groups(cases)
    audit = diversity_audit(cases, n_proposed, n_rejected, {f: len(hard_pool[f]) for f in HARD_FAMILIES})
    return cases, audit


def _case_from_event(b: Base, e: Event, obs: dict, window: int, ev_seed: int) -> dict:
    truth, doc = true_doc(b), apply_edits(true_doc(b), e.removed, e.added)
    touched = {(s, m) for s, _, m in e.removed + e.added}
    actual = [edge_dict(b, s, o, m) for s, es in truth.items() for o, m in es if (s, m) in touched]
    documented = [edge_dict(b, s, o, m) for s, es in doc.items() for o, m in es if (s, m) in touched]
    p = e.plaus
    # A swap keeps every owner's and member's edge count; a single-edge retarget does not.
    # Retargets therefore differ from the topology's (single, fixed) clean graph in degree
    # statistics, which a structure-only model can exploit -> reported as a separate slice.
    degree_preserving = (sorted(o for _, o, _ in e.removed) == sorted(o for _, o, _ in e.added)
                         and sorted(m for _, _, m in e.removed) == sorted(m for _, _, m in e.added))
    return {
        "degree_preserving": degree_preserving,
        "case_id": f"case_{e.event_id}",
        "physical_event_id": e.event_id,
        "building_id": b.tid,
        "topology_id": b.tid,
        "topology_letter": TOPOLOGY_LETTER[b.tid],
        "label": 1,
        "difficulty": e.difficulty,
        "corruption_type": e.family,
        "corruption_subtype": e.subtype,
        "removed": [list(x) for x in e.removed],
        "added": [list(x) for x in e.added],
        "actual_connection": actual,
        "documented_connection": documented,
        "plausibility_confounded": e.plausibility_confounded,
        "observable": obs["observable"],
        "observability_detail": obs["edges"],
        "compatibility_checks": {
            "same_class": p.same_class, "same_medium": p.same_medium, "same_relation": p.same_relation,
            "same_direction": p.same_direction, "replacement_differs": p.replacement_differs,
            "valid_cardinality": e.checks["valid_cardinality"], "no_duplicate_edge": e.checks["no_duplicate_edge"],
            "no_orphaned_equipment": e.checks["no_orphan_member"] and e.checks["no_orphan_owner"],
            "graph_valid": e.checks["graph_valid"], "capacity_plausible": p.capacity_ok, "size_plausible": p.size_ok,
            "physically_plausible": p.all() and e.checks["graph_valid"],
        },
        "evidence_window": window,
        "evidence_seed": ev_seed,
        "provenance": {**PROVENANCE, "model_source": MODEL_SOURCE[b.tid], "documentation_error": "synthetic", "simulation": "synthetic"},
    }


def _clean_case(b: Base, window: int) -> dict:
    eid = f"clean_{TOPOLOGY_LETTER[b.tid]}_w{window}"
    h = _h(eid)
    return {
        "case_id": f"case_{eid}", "physical_event_id": eid, "building_id": b.tid, "topology_id": b.tid,
        "topology_letter": TOPOLOGY_LETTER[b.tid], "label": 0, "difficulty": "clean", "corruption_type": "none",
        "corruption_subtype": "none", "degree_preserving": True, "removed": [], "added": [], "actual_connection": [], "documented_connection": [],
        "plausibility_confounded": False, "observable": "n/a", "observability_detail": [], "compatibility_checks": {},
        "evidence_window": window, "evidence_seed": h % 1_000_003,
        "provenance": {**PROVENANCE, "model_source": MODEL_SOURCE[b.tid], "documentation_error": "none", "simulation": "synthetic"},
    }


def _assign_groups(cases: list[dict]) -> None:
    """Leakage groups: cases within a topology+family that share a corrupted member
    component are chained together (union-find) and must never be split apart."""
    parent: dict[str, str] = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for c in cases:
        if c["label"] == 0:
            continue
        keys = [f"{c['topology_id']}|{c['corruption_type']}|{m}" for _, _, m in c["removed"] + c["added"]]
        for k in keys[1:]:
            parent[find(keys[0])] = find(k)
        find(keys[0])
    for c in cases:
        if c["label"] == 0:
            c["group_id"] = f"clean|{c['topology_id']}|w{c['evidence_window']}"
        else:
            keys = [f"{c['topology_id']}|{c['corruption_type']}|{m}" for _, _, m in c["removed"] + c["added"]]
            c["group_id"] = find(keys[0])


def diversity_audit(cases: list[dict], n_proposed: Counter, n_rejected: Counter, n_pool: dict) -> dict:
    out = {}
    fams = list(HARD_FAMILIES) + [f"easy_{t}" for t in EASY_TYPES]
    for fam in fams:
        rows = [c for c in cases if c["corruption_type"] == fam]
        if not rows:
            continue
        changed_members = {(c["topology_id"], m) for c in rows for _, _, m in c["removed"] + c["added"]}
        components = {(c["topology_id"], x) for c in rows for _, o, m in c["removed"] + c["added"] for x in (o, m)}
        actual_edges = {(c["topology_id"], e["src"], e["dst"]) for c in rows for e in c["actual_connection"]}
        repl = {(c["topology_id"], o) for c in rows for _, o, _ in c["added"]}
        subst = {(c["topology_id"], a["slot"], a["src"] if a["slot"] in ("ahu_vav", "vav_zone") else a["src"], a["dst"], d["src"], d["dst"])
                 for c in rows for a, d in _pair_actual_documented(c)}
        obs = Counter(c["observable"] for c in rows)
        out[fam] = {
            "rows": len(rows), "base_topologies": len({c["topology_id"] for c in rows}),
            "distinct_target_connections": len(actual_edges), "distinct_components": len(components),
            "distinct_changed_members": len(changed_members), "distinct_replacement_endpoints": len(repl),
            "distinct_actual_to_documented_substitutions": len(subst),
            "distinct_leakage_groups": len({c["group_id"] for c in rows}),
            "observable": dict(obs),
            "subtypes": dict(Counter(c["corruption_subtype"] for c in rows)),
            "degree_preserving_rows": sum(1 for c in rows if c["degree_preserving"]),
            "candidates_proposed": n_proposed.get(fam, 0), "candidates_passing_hard_filter": n_pool.get(fam, 0),
        }
    return out


def _pair_actual_documented(c: dict):
    """(actual_edge, documented_edge) pairs per changed member for substitution counting."""
    a_by = defaultdict(list)
    d_by = defaultdict(list)
    for e in c["actual_connection"]:
        m = e["src"] if e["slot"] in ("coil_ahu", "coil_vav", "fan_ahu") else e["dst"]
        a_by[(e["slot"], m)].append(e)
    for e in c["documented_connection"]:
        m = e["src"] if e["slot"] in ("coil_ahu", "coil_vav", "fan_ahu") else e["dst"]
        d_by[(e["slot"], m)].append(e)
    for k, av in a_by.items():
        for a in av:
            for d in d_by.get(k, []):
                if (a["src"], a["dst"]) != (d["src"], d["dst"]):
                    yield a, d


def write_cases(cases: list[dict], audit: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "cases.jsonl", "w") as f:
        for c in cases:
            f.write(json.dumps(c) + "\n")
    (out_dir / "diversity_audit.json").write_text(json.dumps(audit, indent=2))
