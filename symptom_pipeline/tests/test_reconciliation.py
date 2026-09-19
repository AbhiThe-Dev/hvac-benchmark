"""Unit tests for `simulation.reconcile_realized_topology` on synthetic
`networkx.MultiDiGraph` pairs -- no OpenStudio needed, so these run in the
default (non-`physics`-marked) test suite.

These exist because the ONE intervention family this package's physics-
backed tests actually exercise (`reassign_coil`) never triggers the
clone/relocation branch of the reconciliation algorithm at all (confirmed:
`reassign_coil` creates and destroys nothing, so every node matches by
identical handle). The clone-matching branch is therefore validated here,
synthetically, against the exact shape `physics_pipeline.rewire
.clone_terminal_for_zone`-based operations would produce if a future pass
ever adds a fixed-inventory terminal-side intervention -- not against real
physics output. Say so plainly rather than implying it's been exercised
end to end.
"""

from __future__ import annotations

import networkx as nx

from symptom_pipeline.simulation import reconcile_realized_topology


def _node(g, node_id, brick_type, name=None):
    g.add_node(node_id, brick_type=brick_type, location=None, name=name or node_id)


def _edge(g, s, t):
    g.add_edge(s, t, relation="feeds")


def test_identical_graphs_reconcile_with_zero_discordant_pairs():
    g = nx.MultiDiGraph()
    _node(g, "AHU", "AHU")
    _node(g, "T1", "VAV")
    _node(g, "Z1", "HVAC_Zone")
    _edge(g, "AHU", "T1")
    _edge(g, "T1", "Z1")

    discordant, warnings = reconcile_realized_topology(g, g)
    assert discordant == frozenset()
    assert warnings == []


def test_reassign_coil_shaped_diff_reconciles_by_identical_handle():
    """Mirrors the ONE real intervention this package generates: no node
    is created or destroyed, only one pump->coil edge changes."""
    doc = nx.MultiDiGraph()
    _node(doc, "PUMP_A", "Pump")
    _node(doc, "PUMP_B", "Pump")
    _node(doc, "COIL", "Heating_Coil")
    _edge(doc, "PUMP_A", "COIL")

    real = nx.MultiDiGraph()
    _node(real, "PUMP_A", "Pump")
    _node(real, "PUMP_B", "Pump")
    _node(real, "COIL", "Heating_Coil")
    _edge(real, "PUMP_B", "COIL")  # moved from PUMP_A to PUMP_B, same coil handle

    discordant, warnings = reconcile_realized_topology(doc, real)
    assert discordant == frozenset({("PUMP_A", "COIL"), ("PUMP_B", "COIL")})
    assert warnings == []  # every node matched trivially by identical handle


def test_relocated_clone_reconciles_via_structural_signature():
    """Synthetic stand-in for a destroyed-and-recreated terminal (e.g. what
    `rewire.clone_terminal_for_zone` + a branch removal would produce): the
    documented terminal T1 (serving Z1) is destroyed; a new-handled clone
    T1_CLONE appears serving Z2 instead. Neither handle exists in both
    graphs, so identity has to come from the structural signature
    (brick_type + neighbor relation/type multiset), not from the handle or
    from location (which necessarily changes when equipment relocates).

    T1 is the ONLY node missing on the documented side and T1_CLONE the
    ONLY new node on the realized side, so this is a genuinely unique match
    -- see `test_ambiguous_structural_match_is_reported_not_guessed` below
    for the harder case where two same-typed siblings make the match
    genuinely undecidable and must be reported as such instead.
    """
    doc = nx.MultiDiGraph()
    _node(doc, "AHU", "AHU")
    _node(doc, "T1", "VAV")
    _node(doc, "Z1", "HVAC_Zone")
    _node(doc, "Z2", "HVAC_Zone")
    _edge(doc, "AHU", "T1")
    _edge(doc, "T1", "Z1")
    # Z2 has no terminal at all in the documented graph.

    real = nx.MultiDiGraph()
    _node(real, "AHU", "AHU")  # same handle, untouched
    _node(real, "T1_CLONE", "VAV")  # new handle: this is "the same equipment" as T1, relocated
    _node(real, "Z1", "HVAC_Zone")  # same handle, now unserved
    _node(real, "Z2", "HVAC_Zone")  # same handle
    _edge(real, "AHU", "T1_CLONE")
    _edge(real, "T1_CLONE", "Z2")  # T1's clone now feeds Z2 instead of Z1

    discordant, warnings = reconcile_realized_topology(doc, real)

    # T1 <-> T1_CLONE reconciled: same brick_type, same (feeds, AHU-type)
    # inbound signature, and each is the only candidate on its own side.
    assert any("reconciled destroyed-and-recreated node 'T1' -> 'T1_CLONE'" in w for w in warnings)

    # Reconciled identity means the diff is expressed in terms of T1, not
    # T1_CLONE: T1 no longer feeds Z1 (missing), T1 (via its clone) now
    # feeds Z2 (extra) -- exactly the one intended relocation, nothing else.
    assert discordant == frozenset({("T1", "Z1"), ("T1", "Z2")})


def test_ambiguous_structural_match_is_reported_not_guessed():
    """Two same-typed candidates on each side of the diff must never be
    silently matched by iteration order -- this is the safety net for
    exactly the multi-terminal collision risk `physics_pipeline`'s own
    CHANGELOG documents (cross-event collisions on identical-typed
    equipment)."""
    doc = nx.MultiDiGraph()
    _node(doc, "AHU", "AHU")
    _node(doc, "T1", "VAV")
    _node(doc, "T2", "VAV")
    _edge(doc, "AHU", "T1")
    _edge(doc, "AHU", "T2")

    real = nx.MultiDiGraph()
    _node(real, "AHU", "AHU")
    _node(real, "T1_NEW", "VAV")
    _node(real, "T2_NEW", "VAV")
    _edge(real, "AHU", "T1_NEW")
    _edge(real, "AHU", "T2_NEW")

    discordant, warnings = reconcile_realized_topology(doc, real)
    # Both T1 and T2 have IDENTICAL structural signatures (same brick_type,
    # same single inbound (feeds, AHU) edge, no outbound edges) -- genuinely
    # ambiguous, and must be reported as such for both.
    assert sum("ambiguous structural matches" in w for w in warnings) == 2
    # An ambiguous node is left unresolved: it shows up as both a removal
    # (documented id) and an addition (realized id), never silently paired.
    assert discordant == frozenset({("AHU", "T1"), ("AHU", "T2"), ("AHU", "T1_NEW"), ("AHU", "T2_NEW")})
