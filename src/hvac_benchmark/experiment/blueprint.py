"""Corrupted-blueprint generation for the troubleshooting-against-a-blueprint
evaluation mode.

A "blueprint" starts as a topology's true `feeds` edge set and is then
deliberately corrupted at a small, controlled number of points to simulate
stale/wrong documentation (an undocumented connection, a documented
connection that was never built or was decommissioned, or a rewire that was
never reflected in the docs).

The candidate universe used by troubleshooting trials is exactly the same
physically-plausible candidate set discovery mode uses
(`generate_feeds_candidates`) -- the blueprint only changes which *prior*
each candidate starts with, never which candidates exist. This is required
for a *removal* corruption (a real, undocumented connection) to be
discoverable at all: if the candidate universe were restricted to
blueprint-claimed edges, a removed edge could never be tested.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..data.ontology import BrickOntology
from ..graph.networkx_build import TopologyGraph
from .candidates import generate_feeds_candidates

CORRUPTION_TYPES: tuple[str, ...] = ("removal", "fabrication", "misattribution")


@dataclass(frozen=True)
class CorruptionEvent:
    corruption_type: str  # one of CORRUPTION_TYPES
    # candidate pair(s) whose blueprint claim now disagrees with the truth.
    # Removal/fabrication touch one pair; misattribution touches two (the
    # true parent it dropped and the wrong parent it added), but still
    # counts as *one* corruption event/severity unit -- a single target's
    # documented parent is wrong, not two independent facts.
    discordant_pairs: tuple[tuple[str, str], ...]
    target: str


@dataclass(frozen=True)
class Blueprint:
    building_id: str
    severity: int  # requested severity; len(events) is the actual achieved count
    corruption_seed: int
    claimed_edges: frozenset[tuple[str, str]]
    events: tuple[CorruptionEvent, ...]

    @property
    def discordant_pairs(self) -> frozenset[tuple[str, str]]:
        out: set[tuple[str, str]] = set()
        for e in self.events:
            out.update(e.discordant_pairs)
        return frozenset(out)


def generate_blueprint(
    tg: TopologyGraph,
    ontology: BrickOntology,
    severity: int,
    corruption_seed: int,
) -> Blueprint:
    """Attempts to construct `severity` corruption events, choosing among
    the three corruption types uniformly at random (seeded). On a topology
    too small or under-connected to safely construct that many distinct,
    non-overlapping corruptions (e.g. no alternate plausible parent exists
    for a misattribution), returns a `Blueprint` with fewer events than
    requested rather than guessing or double-corrupting the same target --
    callers should check `len(blueprint.events)` rather than assume it
    equals `severity`.
    """
    true_edges = set(tg.edges_by_relation["feeds"])
    candidates = generate_feeds_candidates(tg, ontology)
    candidate_pairs = [(c.source, c.target) for c in candidates]
    false_candidate_pairs = [p for p in candidate_pairs if p not in true_edges]

    by_target: dict[str, list[str]] = {}
    for s, t in candidate_pairs:
        by_target.setdefault(t, []).append(s)

    rng = np.random.RandomState(corruption_seed)

    claimed = set(true_edges)
    events: list[CorruptionEvent] = []

    # sorted(), not list(): set iteration order depends on the per-process
    # string hash seed, which made the same corruption_seed pick different
    # corruptions in different processes (unreproducible across runs, and
    # different between parallel workers and a serial run).
    true_edges_order = sorted(true_edges)
    rng.shuffle(true_edges_order)
    false_order = list(false_candidate_pairs)
    rng.shuffle(false_order)

    used_true_idx = 0
    used_false_idx = 0
    used_targets: set[str] = set()

    attempts = 0
    max_attempts = severity * 20 + 50
    while len(events) < severity and attempts < max_attempts:
        attempts += 1
        corruption_type = CORRUPTION_TYPES[rng.randint(0, len(CORRUPTION_TYPES))]

        if corruption_type == "removal":
            if used_true_idx >= len(true_edges_order):
                continue
            s, t = true_edges_order[used_true_idx]
            used_true_idx += 1
            if t in used_targets or (s, t) not in claimed:
                continue
            claimed.discard((s, t))
            used_targets.add(t)
            events.append(CorruptionEvent("removal", ((s, t),), t))

        elif corruption_type == "fabrication":
            if used_false_idx >= len(false_order):
                continue
            s, t = false_order[used_false_idx]
            used_false_idx += 1
            if (s, t) in claimed or t in used_targets:
                continue
            claimed.add((s, t))
            used_targets.add(t)
            events.append(CorruptionEvent("fabrication", ((s, t),), t))

        else:  # misattribution
            if used_true_idx >= len(true_edges_order):
                continue
            s, t = true_edges_order[used_true_idx]
            used_true_idx += 1
            if t in used_targets or (s, t) not in claimed:
                continue
            alt_parents = [p for p in by_target.get(t, []) if p != s and (p, t) not in true_edges]
            if not alt_parents:
                continue
            s_wrong = alt_parents[rng.randint(0, len(alt_parents))]
            claimed.discard((s, t))
            claimed.add((s_wrong, t))
            used_targets.add(t)
            events.append(CorruptionEvent("misattribution", ((s, t), (s_wrong, t)), t))

    return Blueprint(
        building_id=tg.building_id,
        severity=severity,
        corruption_seed=corruption_seed,
        claimed_edges=frozenset(claimed),
        events=tuple(events),
    )


def symptom_flagged_nodes(tg: TopologyGraph, blueprint: Blueprint) -> frozenset[str]:
    """Nodes flagged as 'suspect' by a simulated technician noticing
    abnormal behavior near a corruption site: the corrupted target itself,
    plus its immediate neighbors in the TRUE graph (parents and children
    under any relation) -- the same locality information a technician would
    have from physically walking the area. Never exposes which specific
    edge is wrong, only which nodes are in the vicinity.
    """
    flagged: set[str] = set()
    for event in blueprint.events:
        t = event.target
        flagged.add(t)
        for edges in tg.edges_by_relation.values():
            for s, o in edges:
                if o == t:
                    flagged.add(s)
                if s == t:
                    flagged.add(o)
    return frozenset(flagged)
