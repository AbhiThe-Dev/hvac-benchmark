"""Selection policies.

Every policy operates only on the opaque `PolicyView` (ids, Brick types,
independently-available location) plus, for the active policy, a live
expected-information-gain callback supplied by the runner. Fixed-order
policies compute their entire ranking once, up front, from information that
does not depend on any test outcome.

Tie-breaking uses a single, precomputed-once-per-trial `tiebreak` array (a
random permutation of candidate indices) rather than live draws from a
`RandomState` consumed on demand. This matters for a required invariant: in
the noiseless independent-edge experiment, expected information gain for
every *untested* candidate is static (edges don't share information), so
active selection and the frozen-initial-ranking control must produce
byte-identical trajectories. That only holds if both resolve ties against
the exact same fixed priority order; drawing tie-break randomness lazily
(once per decision for active, once in a single batched call for frozen)
would consume a shared `RandomState` in different patterns and could break
ties differently despite identical gain values.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

import numpy as np

from ..data.ontology import BrickOntology
from .policy_view import PolicyView

EigFn = Callable[[int], float]


class SelectionPolicy(Protocol):
    name: str
    adaptive: bool

    def initial_ranking(self, view: PolicyView, ontology: BrickOntology, tiebreak: np.ndarray) -> list[int]:
        ...

    def next_index(self, unresolved: list[int], eig_fn: EigFn, tiebreak: np.ndarray) -> int:
        ...


def make_tiebreak(n: int, seed: int) -> np.ndarray:
    """A fixed-once-per-trial random priority per candidate index (lower
    value = higher priority when breaking ties), shared by every policy in
    that trial so tie-breaking is comparable across policies."""
    return np.random.RandomState(seed).permutation(n)


def _seeded_tiebreak_sort(keys: list[tuple[float, ...]], tiebreak: np.ndarray) -> list[int]:
    """Stable descending sort on `keys` (higher first) with tie-breaking by
    the precomputed `tiebreak` priority (lower tiebreak value wins ties)."""
    n = len(keys)
    order = sorted(range(n), key=lambda i: (keys[i], -tiebreak[i]), reverse=True)
    return order


@dataclass
class RandomPolicy:
    name: str = "random"
    adaptive: bool = False

    def initial_ranking(self, view, ontology, tiebreak):
        return list(np.argsort(tiebreak))

    def next_index(self, unresolved, eig_fn, tiebreak):
        raise NotImplementedError


def _equipment_class_rank(brick_type: str | None, ontology: BrickOntology) -> int:
    """Fixed traversal precedence: supply equipment (AHU/RTU) first, then
    terminal units, then locations/zones, then anything else. This is a
    *modeled assumption* about unaided search order (supply-side outward),
    not an empirically observed technician traversal."""
    if brick_type is None:
        return 3
    ancestors = ontology.ancestors(brick_type)
    if "AHU" in ancestors or "Pump" in ancestors:
        return 0
    if "Terminal_Unit" in ancestors:
        return 1
    if "Location" in ancestors or "Coil" in ancestors:
        return 2
    return 3


@dataclass
class TraversalHeuristicPolicy:
    """Fixed equipment-class traversal from supply equipment toward
    terminals and zones, ordered by location where location metadata is
    available. This is a modeled assumption about unaided search order, not
    an empirically validated account of technician behavior -- no
    technician search sequences were observed or encoded."""

    name: str = "traversal"
    adaptive: bool = False

    def initial_ranking(self, view, ontology, tiebreak):
        keys = []
        for c in view.candidates:
            source_rank = _equipment_class_rank(view.nodes[c.source].brick_type, ontology)
            target_rank = _equipment_class_rank(view.nodes[c.target].brick_type, ontology)
            loc = view.nodes[c.source].location_opaque or ""
            # lower rank = earlier in traversal -> negate so higher key sorts first
            keys.append((-source_rank, -target_rank, loc))
        return _seeded_tiebreak_sort(keys, tiebreak)

    def next_index(self, unresolved, eig_fn, tiebreak):
        raise NotImplementedError


@dataclass
class RuleBasedPolicy:
    """Fixed descending type/location compatibility ranking, computed once
    and never reprioritized from posterior beliefs. Compatibility score
    prefers more specific (deeper in the Brick class hierarchy) equipment
    pairings and matching location metadata."""

    name: str = "rule_based"
    adaptive: bool = False

    def initial_ranking(self, view, ontology, tiebreak):
        keys = []
        for c in view.candidates:
            src_type = view.nodes[c.source].brick_type
            tgt_type = view.nodes[c.target].brick_type
            specificity = len(ontology.ancestors(src_type)) + len(ontology.ancestors(tgt_type)) if src_type and tgt_type else 0
            same_location = 1 if (
                view.nodes[c.source].location_opaque is not None
                and view.nodes[c.source].location_opaque == view.nodes[c.target].location_opaque
            ) else 0
            keys.append((same_location, specificity))
        return _seeded_tiebreak_sort(keys, tiebreak)

    def next_index(self, unresolved, eig_fn, tiebreak):
        raise NotImplementedError


@dataclass
class ActivePolicy:
    name: str = "active"
    adaptive: bool = True

    def initial_ranking(self, view, ontology, tiebreak):
        raise NotImplementedError("active policy selects adaptively; see next_index")

    def next_index(self, unresolved: list[int], eig_fn: EigFn, tiebreak: np.ndarray) -> int:
        # Argmax with tiebreak-array tie-breaking, without sorting the whole
        # unresolved set (matters for candidate sets in the thousands, e.g.
        # hasPoint on larger topologies).
        best_gain = float("-inf")
        best_tiebreak = None
        best_idx = None
        for idx in unresolved:
            g = eig_fn(idx)
            t = tiebreak[idx]
            if g > best_gain or (g == best_gain and t < best_tiebreak):
                best_gain = g
                best_tiebreak = t
                best_idx = idx
        return best_idx


@dataclass
class FrozenInitialPolicy:
    """Same expected-information-gain ranking Active would compute at step
    zero (before any observations), frozen and never recomputed. Isolates
    the benefit of *adapting* to observations from the benefit of a good
    starting priority order."""

    name: str = "frozen_initial"
    adaptive: bool = False

    def initial_ranking(self, view, ontology, tiebreak, eig_fn: EigFn | None = None):
        assert eig_fn is not None, "FrozenInitialPolicy requires an eig_fn evaluated at the initial belief state"
        gains = [eig_fn(i) for i in range(len(view.candidates))]
        return _seeded_tiebreak_sort([(g,) for g in gains], tiebreak)

    def next_index(self, unresolved, eig_fn, tiebreak):
        raise NotImplementedError


def make_policy(name: str) -> SelectionPolicy:
    return {
        "random": RandomPolicy(),
        "traversal": TraversalHeuristicPolicy(),
        "rule_based": RuleBasedPolicy(),
        "active": ActivePolicy(),
        "frozen_initial": FrozenInitialPolicy(),
    }[name]
