"""Invariants the benchmark's claims rest on. Run: .venv/bin/python -m pytest doc_mismatch/tests"""
import numpy as np

from docmismatch.data import SLOTS
from docmismatch.evaluate import FOLDS, LETTER
from docmismatch.classify import make_split
from docmismatch.evidence import closure_residual, make_evidence
from docmismatch.features import FEATURE_NAMES, case_doc, case_rows
from docmismatch.metrics import auprc_balanced, auroc, f1_balanced
from docmismatch.rules import apply_edits, structural_checks, true_doc


def test_counts_and_difficulty_mix(cases):
    d = {k: sum(c["difficulty"] == k for c in cases) for k in ("hard", "easy", "clean")}
    assert d["hard"] >= 100 and d["easy"] >= 25 and d["clean"] >= 30


def test_one_row_per_physical_event(cases):
    ids = [c["physical_event_id"] for c in cases]
    assert len(ids) == len(set(ids)), "a physical event must not appear as several rows"
    keys = [(c["topology_id"], tuple(map(tuple, c["removed"])), tuple(map(tuple, c["added"]))) for c in cases if c["label"] == 1]
    assert len(keys) == len(set(keys))


def test_corruption_is_documentation_only(cases, bases):
    """Truth is never mutated; clean and corrupted docs of a building share identical evidence."""
    c = next(c for c in cases if c["label"] == 1)
    b = bases[c["topology_id"]]
    before = {s: list(e) for s, e in b.slot_edges.items()}
    doc = case_doc(b, c)
    assert b.slot_edges == before
    assert doc != true_doc(b)
    # same (topology, window, seed) -> bit-identical evidence regardless of the documentation
    e1 = make_evidence(b, c["evidence_window"], c["evidence_seed"])
    e2 = make_evidence(b, c["evidence_window"], c["evidence_seed"])
    assert all(np.array_equal(e1[k], e2[k]) for k in e1)


def test_hard_cases_pass_every_filter(cases):
    for c in cases:
        if c["difficulty"] != "hard":
            continue
        k = c["compatibility_checks"]
        for name in ("same_class", "same_medium", "same_relation", "same_direction", "replacement_differs", "valid_cardinality",
                     "no_duplicate_edge", "no_orphaned_equipment", "graph_valid", "capacity_plausible", "size_plausible", "physically_plausible"):
            assert k[name] is True, (c["case_id"], name)
        assert c["plausibility_confounded"] is False
        assert c["provenance"]["real_world_verified"] is False


def test_easy_cases_are_flagged_confounded_and_not_hard(cases, bases):
    for c in cases:
        if c["difficulty"] == "easy":
            assert c["plausibility_confounded"] is True
            b = bases[c["topology_id"]]
            doc = case_doc(b, c)
            assert not all(structural_checks(b, doc).values()), "easy corruptions must break structure/medium/cardinality"


def test_clean_cases_have_identical_documentation(cases, bases):
    for c in cases:
        if c["label"] == 0:
            b = bases[c["topology_id"]]
            assert case_doc(b, c) == true_doc(b)
            assert c["removed"] == [] and c["added"] == []


def test_swaps_preserve_degrees_and_retargets_do_not(cases):
    for c in cases:
        if c["difficulty"] != "hard":
            continue
        if c["corruption_subtype"] in ("swap",) or c["corruption_type"] in ("sensor_mapping", "same_medium_branch", "parallel_peer_swap", "vav_zone_swap"):
            assert c["degree_preserving"]
        if c["corruption_subtype"] == "retarget":
            assert not c["degree_preserving"]


def test_features_do_not_read_labels(cases, bases):
    c = next(c for c in cases if c["difficulty"] == "hard")
    b = bases[c["topology_id"]]
    rows = case_rows(b, c)
    flipped = dict(c, label=0, corruption_type="none", corruption_subtype="none", difficulty="clean", observable="n/a", group_id="x")
    rows2 = case_rows(b, flipped)
    assert all(np.array_equal(a["x"], b2["x"]) for a, b2 in zip(rows, rows2)), "features may depend on the documentation and evidence only"
    assert not any("id" == n or n.startswith("node") for n in FEATURE_NAMES)


def test_no_group_leakage_in_any_fold(cases):
    for fold, d in FOLDS.items():
        train_topos = [LETTER[x] for x in d["train"]]
        sp = make_split(cases, train_topos)
        by = {c["case_id"]: c for c in cases}
        g_train = {by[i]["group_id"] for i in sp["train"]}
        g_val = {by[i]["group_id"] for i in sp["val"]}
        assert not (g_train & g_val), f"{fold}: a leakage group is on both sides of train/val"
        test_topos = {LETTER[x] for x in d["test"]}
        assert not ({by[i]["topology_id"] for i in sp["train"] + sp["val"]} & test_topos), f"{fold}: test topology seen in training"


def test_physics_conservation_in_truth(bases):
    """Sanity of the evidence itself: AHU flow = sum of VAV flows; loop heat = sum of branch heat."""
    for b in bases.values():
        ev = {k: v for k, v in b.ev.items()}
        for a in b.ids("AHU"):
            kids = [m for o, m in b.slot_edges["ahu_vav"] if o == a]
            assert closure_residual(ev, a, kids, slot="ahu_vav") < 1e-3
        for l in b.ids("HWL", "CHWL"):
            kids = [m for o, m in b.slot_edges["loop_branch"] if o == l]
            assert closure_residual(ev, l, kids, slot="loop_branch") < 0.05


def test_metrics_sanity():
    y = np.array([1, 1, 0, 0])
    assert auroc(y, np.array([3.0, 2.0, 1.0, 0.0])) == 1.0
    assert auroc(y, np.zeros(4)) == 0.5
    rng = np.random.default_rng(0)
    y = (rng.random(4000) < 0.8).astype(int)
    assert abs(auprc_balanced(y, rng.random(4000)) - 0.5) < 0.03  # chance = 0.5 regardless of prevalence
    assert f1_balanced(y, rng.random(4000), 2.0) == 0.0


def test_auprc_is_tie_safe():
    y = np.array([1] * 30 + [0] * 10)          # positives listed first: order must not matter
    const = np.zeros(40)
    assert abs(auprc_balanced(y, const) - 0.5) < 1e-9
    from docmismatch.metrics import auprc
    assert abs(auprc(y, const) - 0.75) < 1e-9
    assert auprc_balanced(y, np.r_[np.ones(30), np.zeros(10)]) == 1.0
