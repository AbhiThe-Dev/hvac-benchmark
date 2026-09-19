"""Noiseless exhaustive recovery: with complete candidate coverage and no
observation noise, every policy must reach perfect precision and recall by
the end of the (independent-edge) trial, since the budget guarantees every
candidate is tested at least once."""

from __future__ import annotations

import networkx as nx
import pytest

from hvac_benchmark.config import DEFAULT_CONFIG
from hvac_benchmark.experiment.runner import run_trial
from hvac_benchmark.graph.networkx_build import TopologyGraph


def make_tg() -> TopologyGraph:
    g = nx.MultiDiGraph()
    g.add_node("AHU", brick_type="AHU", brick_types=["AHU"], location=None)
    edges = {"feeds": set(), "hasPoint": set(), "hasPart": set()}
    for i in range(5):
        vav, zone = f"VAV_{i}", f"Zone_{i}"
        g.add_node(vav, brick_type="VAV", brick_types=["VAV"], location=None)
        g.add_node(zone, brick_type="HVAC_Zone", brick_types=["HVAC_Zone"], location=None)
        g.add_edge("AHU", vav, relation="feeds")
        g.add_edge(vav, zone, relation="feeds")
        edges["feeds"].add(("AHU", vav))
        edges["feeds"].add((vav, zone))
    return TopologyGraph("exhaustive_test", "test", g, edges)


@pytest.mark.parametrize("policy", ["active", "random", "traversal", "rule_based", "frozen_initial"])
@pytest.mark.parametrize("experiment", ["independent", "structured"])
def test_noiseless_exhaustive_recovery_reaches_perfect_precision_recall(ontology, policy, experiment):
    tg = make_tg()
    result = run_trial(tg, "feeds", ontology, experiment, policy, noise_level=0.0, seed=0, config=DEFAULT_CONFIG)
    final = result.trajectory[-1]
    assert final.precision == pytest.approx(1.0)
    assert final.recall == pytest.approx(1.0)
    assert result.n_missed_true_edges == 0  # candidate generation has full coverage on this fixture
