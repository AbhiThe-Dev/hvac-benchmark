"""End-to-end behavior of `run_troubleshooting_trial` on a small,
hand-constructed, deterministically-corrupted fixture: verifies that (a)
active selection eventually flags a forced corruption under a noiseless
budget, and (b) `full_sweep` structurally cannot find a *removal*
corruption, since it only re-tests blueprint-claimed edges -- the
documented limitation of that baseline, not a bug.
"""

from __future__ import annotations

import networkx as nx

from hvac_benchmark.config import DEFAULT_CONFIG
from hvac_benchmark.experiment.blueprint import Blueprint, CorruptionEvent
from hvac_benchmark.experiment.troubleshooting_runner import run_troubleshooting_trial
from hvac_benchmark.graph.networkx_build import TopologyGraph


def make_tg() -> TopologyGraph:
    g = nx.MultiDiGraph()
    g.add_node("AHU", brick_type="AHU", brick_types=["AHU"], location=None)
    edges = {"feeds": set(), "hasPoint": set(), "hasPart": set()}
    for i in range(2):
        vav, zone = f"VAV_{i}", f"Zone_{i}"
        g.add_node(vav, brick_type="VAV", brick_types=["VAV"], location=None)
        g.add_node(zone, brick_type="HVAC_Zone", brick_types=["HVAC_Zone"], location=None)
        g.add_edge("AHU", vav, relation="feeds")
        g.add_edge(vav, zone, relation="feeds")
        edges["feeds"].add(("AHU", vav))
        edges["feeds"].add((vav, zone))
    return TopologyGraph("troubleshooting_test", "test", g, edges)


def _forced_removal_blueprint(tg: TopologyGraph) -> Blueprint:
    true_edges = set(tg.edges_by_relation["feeds"])
    removed = ("VAV_0", "Zone_0")
    assert removed in true_edges
    claimed = frozenset(true_edges - {removed})
    event = CorruptionEvent("removal", (removed,), "Zone_0")
    return Blueprint(
        building_id=tg.building_id, severity=1, corruption_seed=0, claimed_edges=claimed, events=(event,)
    )


def test_active_policy_eventually_flags_a_forced_removal(ontology):
    tg = make_tg()
    bp = _forced_removal_blueprint(tg)
    result = run_troubleshooting_trial(
        tg, ontology, bp, policy_name="active", symptom_mode=False, noise_level=0.0, seed=0, config=DEFAULT_CONFIG
    )
    assert result.n_tests_to_full_flag_sustained is not None


def test_full_sweep_cannot_find_a_removal_corruption(ontology):
    tg = make_tg()
    bp = _forced_removal_blueprint(tg)
    result = run_troubleshooting_trial(
        tg,
        ontology,
        bp,
        policy_name="full_sweep",
        symptom_mode=False,
        noise_level=0.0,
        seed=0,
        config=DEFAULT_CONFIG,
    )
    assert result.n_tests_to_full_flag_first is None
    assert result.n_tests_to_full_flag_sustained is None
    assert result.trajectory[-1].n_discordant_flagged == 0


def test_blueprint_literal_performs_zero_tests(ontology):
    tg = make_tg()
    bp = _forced_removal_blueprint(tg)
    result = run_troubleshooting_trial(
        tg,
        ontology,
        bp,
        policy_name="blueprint_literal",
        symptom_mode=False,
        noise_level=0.0,
        seed=0,
        config=DEFAULT_CONFIG,
    )
    assert result.n_tests_performed == 0
    assert result.n_tests_to_full_flag_first is None
