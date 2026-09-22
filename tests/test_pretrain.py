"""Self-supervised connection-plausibility pretraining: featurization,
leakage-free masking, tie-aware metrics, training, and checkpoint reuse."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip("torch")

import networkx as nx  # noqa: E402

from hvac_benchmark.data.cache import FileCache  # noqa: E402
from hvac_benchmark.graph.networkx_build import TopologyGraph  # noqa: E402
from hvac_benchmark.pretrain.data import (  # noqa: E402
    LOCATION,
    POINT,
    NodePools,
    TypeVocab,
    ancestor_names,
    duplicate_groups,
    example_from_topology,
    is_real,
    load_corpus,
)
from hvac_benchmark.pretrain.evaluate import GNNScorer, RandomScorer, TypePriorScorer, _expected_metrics, evaluate  # noqa: E402
from hvac_benchmark.pretrain.model import build_mp_graph, load_pretrained, save_pretrained  # noqa: E402
from hvac_benchmark.pretrain.train import TrainConfig, make_holdout, train  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]


def make_tg(building_id, types, feeds=(), has_part=(), has_point=()):
    g = nx.MultiDiGraph()
    for node, t in types.items():
        g.add_node(node, brick_type=t, brick_types=[t] if t else [], location=None)
    return TopologyGraph(
        building_id, "test", g,
        {"feeds": set(feeds), "hasPart": set(has_part), "hasPoint": set(has_point)},
    )


def synthetic_building(building_id: str, n_vav: int = 6):
    types = {"ahu": "AHU"}
    feeds, points = [], []
    for i in range(n_vav):
        types[f"vav{i}"] = "VAV"
        types[f"t{i}"] = "Zone_Air_Temperature_Sensor"
        feeds.append(("ahu", f"vav{i}"))
        points.append((f"vav{i}", f"t{i}"))
    return make_tg(building_id, types, feeds=feeds, has_point=points)


@pytest.fixture(scope="module")
def vocab(ontology):
    return TypeVocab.build(ontology, extra_brick_classes=frozenset({"Target_Zone_Air_Temperature_Setpoint"}))


def test_unknown_brick_class_gets_point_ancestors_from_suffix(ontology):
    assert {"Setpoint", "Point"} <= ancestor_names(ontology, "Target_Zone_Air_Temperature_Setpoint")
    # a class the ontology knows is never second-guessed by the suffix rule
    assert ancestor_names(ontology, "VAV") == set(ontology.ancestors("VAV"))


def test_features_use_hierarchy_categories_and_canonical_order(ontology, vocab):
    tg = synthetic_building("b")
    ex = example_from_topology(tg, ontology, vocab)
    assert ex.node_ids == sorted(ex.node_ids)
    idx = {n: i for i, n in enumerate(ex.node_ids)}
    assert ex.category[idx["t0"]] == POINT
    tokens = {vocab.tokens[t] for t in ex.type_tokens[idx["vav0"]] if t != vocab.pad_index}
    assert {"VAV", "Terminal_Unit", "Equipment"} <= tokens  # own class + ancestors
    assert vocab.tokens[ex.primary[idx["vav0"]]] == "VAV"
    assert len(ex.edges["feeds"]) == 6 and len(ex.edges["hasPoint"]) == 6


def test_rec_room_is_a_location(ontology, vocab):
    import rdflib
    from hvac_benchmark.pretrain.data import REC_NS

    tg = make_tg("b", {"room": None, "vav": "VAV"}, feeds=[("vav", "room")])
    g = rdflib.Graph()
    g.add((rdflib.URIRef("room"), rdflib.RDF.type, rdflib.URIRef(REC_NS + "Room")))
    ex = example_from_topology(tg, ontology, vocab, g)
    assert ex.category[ex.node_ids.index("room")] == LOCATION


def test_holdout_edges_are_invisible_to_message_passing_and_degrees(ontology, vocab):
    ex = example_from_topology(synthetic_building("b"), ontology, vocab)
    keep = make_holdout(ex, 0.5, np.random.default_rng(0))
    assert (~keep["feeds"]).sum() == 3
    full, masked = build_mp_graph(ex), build_mp_graph(ex, keep)
    assert len(full.src[0]) == 6 and len(masked.src[0]) == 3
    ahu = ex.node_ids.index("ahu")
    assert full.deg_feat[ahu, 1] > masked.deg_feat[ahu, 1]  # ahu out-degree (reverse dir of feeds)


def test_single_edge_relations_are_never_fully_hidden(ontology, vocab):
    tg = make_tg("b", {"a": "AHU", "v": "VAV"}, feeds=[("a", "v")])
    ex = example_from_topology(tg, ontology, vocab)
    assert make_holdout(ex, 0.9, np.random.default_rng(0))["feeds"].all()


def test_node_pools_sample_only_same_key():
    keys = np.array([0, 1, 1, 2, 1, 0])
    pools = NodePools(keys)
    out = pools.sample(np.array([1, 0]), 50, np.random.default_rng(0))
    assert (keys[out[0]] == 1).all() and (keys[out[1]] == 0).all()


def test_expected_metrics_credit_ties_exactly_at_chance():
    mrr, h1, h3 = _expected_metrics(np.array([0]), np.array([3]))  # tied with 3 others
    assert mrr[0] == pytest.approx((1 + 1 / 2 + 1 / 3 + 1 / 4) / 4)
    assert h1[0] == pytest.approx(0.25) and h3[0] == pytest.approx(0.75)
    mrr, h1, _ = _expected_metrics(np.array([2]), np.array([0]))  # clean rank 3
    assert mrr[0] == pytest.approx(1 / 3) and h1[0] == 0.0


def test_duplicate_buildings_are_grouped(ontology, vocab):
    exs = [example_from_topology(synthetic_building(n), ontology, vocab) for n in ("a", "b")]
    exs.append(example_from_topology(synthetic_building("c", n_vav=3), ontology, vocab))
    assert [g for g in duplicate_groups(exs, vocab) if len(g) > 1] == [[0, 1]]


def test_training_beats_random_and_checkpoint_roundtrips(ontology, vocab, tmp_path):
    exs = [example_from_topology(synthetic_building(f"b{i}", n_vav=8), ontology, vocab) for i in range(6)]
    model, history = train(exs[:4], vocab, cfg=TrainConfig(epochs=15, seed=0), log_every=99)
    assert history[-1] < history[0]

    held_out = exs[4:]
    gnn = evaluate(GNNScorer(model), held_out)["feeds"]["all"]["mrr"]
    rnd = evaluate(RandomScorer(), held_out)["feeds"]["all"]["mrr"]
    prior = evaluate(TypePriorScorer(exs[:4], vocab), held_out)["feeds"]["all"]["mrr"]
    assert gnn > rnd and prior > rnd

    save_pretrained(model, tmp_path / "enc", {"note": "test"})
    reloaded = load_pretrained(tmp_path / "enc")
    with torch.no_grad():
        assert torch.allclose(model.encode(exs[5]), reloaded.encode(exs[5]), atol=1e-6)
    assert reloaded.vocab.tokens == vocab.tokens


def test_training_is_reproducible(ontology, vocab):
    exs = [example_from_topology(synthetic_building(f"b{i}"), ontology, vocab) for i in range(3)]
    _, h1 = train(exs, vocab, cfg=TrainConfig(epochs=3, seed=4), log_every=99)
    _, h2 = train(exs, vocab, cfg=TrainConfig(epochs=3, seed=4), log_every=99)
    assert h1 == h2


def test_real_corpus_excludes_simulated_and_flags_duplicates(ontology):
    cache = FileCache(REPO_ROOT / "data_cache")
    if not cache.has("mortar__bldg1.ttl"):
        pytest.skip("real corpus not cached")
    exs, vocab = load_corpus(cache, ontology)
    ids = {e.building_id for e in exs}
    # only confirmed-real systems: every LBNL file except the ORNL FRP is a simulation
    assert not ids & {"rtu_sim", "sdahu", "ddahu", "fcu", "pfpu", "sfpu", "chiller_plant", "boiler_plant"}
    assert {"mortar_bldg1", "rtu_exp"} <= ids
    assert all(is_real(e) for e in exs)
    with_sim, _ = load_corpus(cache, ontology, include_simulated=True)
    assert {"fcu", "pfpu", "rtu_sim"} <= {e.building_id for e in with_sim if not is_real(e)}
    groups = [{exs[i].building_id for i in g} for g in duplicate_groups(exs, vocab) if len(g) > 1]
    assert {"mortar_bldg30", "mortar_smc"} in groups
    assert (exs[0].primary == vocab.index["<untyped>"]).mean() < 0.5


def test_swap_cases_are_same_class_and_never_existing_edges(ontology, vocab):
    from hvac_benchmark.pretrain.detection import swap_cases

    ex = example_from_topology(synthetic_building("b", n_vav=6), ontology, vocab)
    known = set(map(tuple, ex.edges["feeds"].tolist()))
    for side in ("source", "target"):
        for (s, t), (ws, wt) in swap_cases(ex, "feeds", side, 50, np.random.default_rng(0)):
            assert (ws, wt) not in known
            moved, wrong = ((s, ws) if side == "source" else (t, wt))
            assert ex.primary[moved] == ex.primary[wrong] and moved != wrong


def test_degree_matched_swaps_leave_no_degree_signal(ontology, vocab):
    """Two AHUs with 5 and 3 VAVs: swapping a VAV from the 5-child AHU to the
    3-child AHU leaves both with 4 children in the swapped graph."""
    from hvac_benchmark.pretrain.detection import _with_swap, swap_cases

    types = {"a1": "AHU", "a2": "AHU"}
    feeds = []
    for i in range(5):
        types[f"v{i}"] = "VAV"; feeds.append(("a1", f"v{i}"))
    for i in range(5, 8):
        types[f"v{i}"] = "VAV"; feeds.append(("a2", f"v{i}"))
    ex = example_from_topology(make_tg("b", types, feeds=feeds), ontology, vocab)
    cases = swap_cases(ex, "feeds", "source", 50, np.random.default_rng(0), degree_offset=2)
    assert cases
    for true, wrong in cases:
        g = _with_swap(ex, "feeds", true, wrong)
        deg = np.bincount(g.edges["feeds"][:, 0], minlength=g.n_nodes)
        assert deg[true[0]] == deg[wrong[0]]
