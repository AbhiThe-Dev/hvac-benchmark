"""Sparse priors derived from plausible-parent counts and documented type
compatibility, without fitting to any evaluated edge.

For a candidate edge (s, t), the "plausible-parent count" is the number of
other candidates sharing target t after compatibility-rule filtering (i.e.
already conditioned on documented type compatibility). Absent any other
information, a target with only one physically-compatible candidate parent
should start out much more likely connected than one competing against a
dozen equally-compatible candidates; `prior = 1 / plausible_parent_count`
encodes exactly that and nothing else. A uniform-prior ablation (fixed 0.5
regardless of target) is provided for comparison.
"""

from __future__ import annotations

from .candidates import Candidate

PRIOR_FLOOR = 0.02
PRIOR_CEILING = 0.9


def sparse_priors(candidates: list[Candidate]) -> dict[tuple[str, str], float]:
    target_counts: dict[str, int] = {}
    for c in candidates:
        target_counts[c.target] = target_counts.get(c.target, 0) + 1

    priors: dict[tuple[str, str], float] = {}
    for c in candidates:
        raw = 1.0 / target_counts[c.target]
        priors[(c.source, c.target)] = min(PRIOR_CEILING, max(PRIOR_FLOOR, raw))
    return priors


def uniform_priors(candidates: list[Candidate], value: float = 0.5) -> dict[tuple[str, str], float]:
    return {(c.source, c.target): value for c in candidates}


def blueprint_priors(
    candidates: list[Candidate],
    claimed_edges: "frozenset[tuple[str, str]]",
    blueprint_confidence: float = 0.97,
    absent_prior: float = PRIOR_FLOOR,
) -> dict[tuple[str, str], float]:
    """Rare-deviation prior for the troubleshooting-against-a-blueprint mode:
    near-certain on blueprint-claimed edges, sparse-floor elsewhere. Every
    candidate in `candidates` gets a prior regardless of blueprint
    membership -- the candidate universe (not just the blueprint) is what
    troubleshooting trials test against, which is what makes an
    undocumented real connection ("removal" corruption) discoverable at
    all.
    """
    priors: dict[tuple[str, str], float] = {}
    for c in candidates:
        pair = (c.source, c.target)
        priors[pair] = blueprint_confidence if pair in claimed_edges else absent_prior
    return priors


def apply_symptom_relaxation(
    priors: dict[tuple[str, str], float],
    flagged_nodes: "frozenset[str]",
    relax: float = 0.5,
) -> dict[tuple[str, str], float]:
    """Blends a candidate's prior toward 0.5 (uncertainty) when either
    endpoint is a symptom-flagged node, simulating a technician's narrowed-
    but-not-diagnostic suspicion of a physical area. `relax` in [0, 1]: 0
    leaves priors unchanged, 1 fully resets affected candidates to 0.5.
    This narrows attention only through the prior (and therefore through
    expected information gain) -- it never reveals which specific candidate
    is the fault.
    """
    out: dict[tuple[str, str], float] = {}
    for (s, t), p in priors.items():
        if s in flagged_nodes or t in flagged_nodes:
            out[(s, t)] = p * (1 - relax) + 0.5 * relax
        else:
            out[(s, t)] = p
    return out
