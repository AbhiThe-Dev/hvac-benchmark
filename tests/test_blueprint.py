"""Corruption-generation logic for the troubleshooting-against-a-blueprint
mode: corrupted edges must actually differ from the true graph, and each
corruption type must be applied exactly as specified (removal drops a real
edge, fabrication adds a fake one, misattribution swaps a target's parent)."""

from __future__ import annotations

import networkx as nx
import pytest

from hvac_benchmark.experiment.blueprint import (
    CORRUPTION_TYPES,
    generate_blueprint,
    symptom_flagged_nodes,
)
from hvac_benchmark.experiment.priors import apply_symptom_relaxation, blueprint_priors
from hvac_benchmark.experiment.bayes import update as bayes_update
from hvac_benchmark.graph.networkx_build import TopologyGraph


def make_tg() -> TopologyGraph:
    """AHU feeding 3 VAVs, each VAV feeding its own zone, plus enough
    cross-candidate compatibility (any VAV can plausibly feed any zone
    under the Terminal_Unit->Location tier) to give misattribution an
    alternate parent to pick from."""
    g = nx.MultiDiGraph()
    g.add_node("AHU", brick_type="AHU", brick_types=["AHU"], location=None)
    edges = {"feeds": set(), "hasPoint": set(), "hasPart": set()}
    for i in range(3):
        vav, zone = f"VAV_{i}", f"Zone_{i}"
        g.add_node(vav, brick_type="VAV", brick_types=["VAV"], location=None)
        g.add_node(zone, brick_type="HVAC_Zone", brick_types=["HVAC_Zone"], location=None)
        g.add_edge("AHU", vav, relation="feeds")
        g.add_edge(vav, zone, relation="feeds")
        edges["feeds"].add(("AHU", vav))
        edges["feeds"].add((vav, zone))
    return TopologyGraph("blueprint_test", "test", g, edges)


def test_corrupted_blueprint_differs_from_true_graph(ontology):
    tg = make_tg()
    true_edges = set(tg.edges_by_relation["feeds"])
    for seed in range(20):
        bp = generate_blueprint(tg, ontology, severity=1, corruption_seed=seed)
        assert len(bp.events) == 1, "this fixture has ample candidates; severity=1 should always succeed"
        assert bp.claimed_edges != true_edges


@pytest.mark.parametrize("seed", range(60))
def test_each_corruption_event_matches_its_declared_type(ontology, seed):
    tg = make_tg()
    true_edges = set(tg.edges_by_relation["feeds"])
    bp = generate_blueprint(tg, ontology, severity=1, corruption_seed=seed)
    assert len(bp.events) == 1
    event = bp.events[0]
    assert event.corruption_type in CORRUPTION_TYPES

    if event.corruption_type == "removal":
        (pair,) = event.discordant_pairs
        assert pair in true_edges
        assert pair not in bp.claimed_edges
    elif event.corruption_type == "fabrication":
        (pair,) = event.discordant_pairs
        assert pair not in true_edges
        assert pair in bp.claimed_edges
    else:  # misattribution
        assert len(event.discordant_pairs) == 2
        dropped, added = event.discordant_pairs
        assert dropped[1] == added[1] == event.target  # same target
        assert dropped[0] != added[0]  # different parent
        assert dropped in true_edges and dropped not in bp.claimed_edges
        assert added not in true_edges and added in bp.claimed_edges


def test_all_three_corruption_types_appear_across_seeds(ontology):
    tg = make_tg()
    seen = set()
    for seed in range(200):
        bp = generate_blueprint(tg, ontology, severity=1, corruption_seed=seed)
        if bp.events:
            seen.add(bp.events[0].corruption_type)
    assert seen == set(CORRUPTION_TYPES)


def test_severity_controls_number_of_corruption_events(ontology):
    tg = make_tg()
    bp1 = generate_blueprint(tg, ontology, severity=1, corruption_seed=1)
    bp2 = generate_blueprint(tg, ontology, severity=2, corruption_seed=1)
    assert len(bp1.events) == 1
    assert len(bp2.events) == 2
    # every event corrupts a distinct target -- never double-corrupted
    targets = [e.target for e in bp2.events]
    assert len(targets) == len(set(targets))


def test_symptom_flagged_nodes_never_exposes_which_candidate_is_wrong(ontology):
    tg = make_tg()
    bp = generate_blueprint(tg, ontology, severity=1, corruption_seed=3)
    flagged = symptom_flagged_nodes(tg, bp)
    # flags are plain node ids only -- never a (source, target) pair, and
    # never something identifying the specific corrupted edge.
    assert all(isinstance(n, str) for n in flagged)
    assert bp.events[0].target in flagged


def test_blueprint_priors_are_near_certain_on_claimed_and_sparse_elsewhere(ontology):
    tg = make_tg()
    from hvac_benchmark.experiment.candidates import generate_feeds_candidates

    candidates = generate_feeds_candidates(tg, ontology)
    bp = generate_blueprint(tg, ontology, severity=1, corruption_seed=7)
    priors = blueprint_priors(candidates, bp.claimed_edges, blueprint_confidence=0.97, absent_prior=0.02)

    for c in candidates:
        pair = (c.source, c.target)
        if pair in bp.claimed_edges:
            assert priors[pair] == pytest.approx(0.97)
        else:
            assert priors[pair] == pytest.approx(0.02)


def test_blueprint_prior_belief_update_recovers_a_misattributed_edge(ontology):
    """Hand-constructed known-ambiguity case: force a misattribution so a
    real edge starts with a low (blueprint-absent) prior, then verify a
    single noiseless confirming observation flips belief decisively above
    the reconstruction threshold -- i.e. the blueprint-as-prior belief
    update behaves like ordinary Bayesian updating, just seeded from a
    different starting point than discovery mode's sparse prior."""
    tg = make_tg()
    from hvac_benchmark.experiment.candidates import generate_feeds_candidates

    candidates = generate_feeds_candidates(tg, ontology)

    # find a seed that produces a misattribution for a deterministic check
    bp = None
    for seed in range(200):
        candidate_bp = generate_blueprint(tg, ontology, severity=1, corruption_seed=seed)
        if candidate_bp.events and candidate_bp.events[0].corruption_type == "misattribution":
            bp = candidate_bp
            break
    assert bp is not None, "expected at least one misattribution across 200 seeds on this fixture"

    dropped, added = bp.events[0].discordant_pairs
    priors = blueprint_priors(candidates, bp.claimed_edges, blueprint_confidence=0.97, absent_prior=0.02)

    assert priors[dropped] == pytest.approx(0.02)  # true edge, but not blueprint-claimed
    assert priors[added] == pytest.approx(0.97)  # blueprint-claimed, but not true

    # noiseless confirming test of the true-but-unclaimed edge
    posterior_dropped = bayes_update(priors[dropped], observed=True, fp_rate=0.0, fn_rate=0.0)
    assert posterior_dropped == pytest.approx(1.0)

    # noiseless disconfirming test of the claimed-but-false edge
    posterior_added = bayes_update(priors[added], observed=False, fp_rate=0.0, fn_rate=0.0)
    assert posterior_added == pytest.approx(0.0)


def test_symptom_relaxation_pulls_flagged_region_toward_uncertainty(ontology):
    tg = make_tg()
    from hvac_benchmark.experiment.candidates import generate_feeds_candidates

    candidates = generate_feeds_candidates(tg, ontology)
    bp = generate_blueprint(tg, ontology, severity=1, corruption_seed=7)
    flagged = symptom_flagged_nodes(tg, bp)
    priors = blueprint_priors(candidates, bp.claimed_edges, blueprint_confidence=0.97, absent_prior=0.02)
    relaxed = apply_symptom_relaxation(priors, flagged, relax=0.5)

    for c in candidates:
        pair = (c.source, c.target)
        if c.source in flagged or c.target in flagged:
            assert relaxed[pair] == pytest.approx(priors[pair] * 0.5 + 0.25)
        else:
            assert relaxed[pair] == priors[pair]
