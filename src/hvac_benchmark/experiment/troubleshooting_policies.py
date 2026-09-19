"""Reference policies specific to the troubleshooting-against-a-blueprint
evaluation mode.

`ActivePolicy` from `policies.py` is reused unmodified for this mode's
"active" policy -- its selection logic (argmax expected information gain,
tiebreak-array tie-breaking) is generic over any eig_fn, so it needs no
troubleshooting-specific variant, and none of `policies.py` is touched by
this module. The three policies defined here exist because they express
troubleshooting-specific behavior (trusting the blueprint outright,
sweeping only what it claims, or exhausting a symptom-flagged region) that
has no equivalent in discovery mode.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BlueprintLiteralPolicy:
    """Zero tests: trusts the blueprint completely. A reference point
    showing the cost of never verifying at all, not a real competitor on
    tests-needed."""

    name: str = "blueprint_literal"
    adaptive: bool = False

    def initial_ranking(self, view, ontology, tiebreak):
        return []

    def next_index(self, unresolved, eig_fn, tiebreak):
        raise NotImplementedError


@dataclass
class FullSweepPolicy:
    """Re-tests every blueprint-claimed edge, in a fixed seeded order,
    ignoring the informed prior entirely. By construction this can never
    surface a *removal* corruption (a real edge the blueprint doesn't claim
    at all) -- it only verifies what is already documented, which is
    exactly what makes it a fair "rote verification pass" reference rather
    than a fault-localization strategy."""

    name: str = "full_sweep"
    adaptive: bool = False

    def initial_ranking(self, view, ontology, tiebreak, blueprint_claimed_indices: "set[int] | None" = None):
        assert blueprint_claimed_indices is not None, "full_sweep requires blueprint_claimed_indices"
        return sorted(blueprint_claimed_indices, key=lambda i: tiebreak[i])

    def next_index(self, unresolved, eig_fn, tiebreak):
        raise NotImplementedError


@dataclass
class SymptomNaivePolicy:
    """Symptom-triggered sub-experiment only: exhaustively tests every
    candidate touching a symptom-flagged node, in fixed seeded order, with
    no expected-information-gain reasoning -- isolates how much value
    active selection adds on top of just narrowing by symptom area."""

    name: str = "symptom_naive"
    adaptive: bool = False

    def initial_ranking(self, view, ontology, tiebreak, flagged_opaque_nodes: "frozenset[str] | None" = None):
        assert flagged_opaque_nodes is not None, "symptom_naive requires flagged_opaque_nodes"
        in_region = [
            i
            for i, c in enumerate(view.candidates)
            if c.source in flagged_opaque_nodes or c.target in flagged_opaque_nodes
        ]
        return sorted(in_region, key=lambda i: tiebreak[i])

    def next_index(self, unresolved, eig_fn, tiebreak):
        raise NotImplementedError
