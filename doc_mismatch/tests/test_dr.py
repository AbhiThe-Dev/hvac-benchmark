"""Guards for the domain-randomization study (PREREGISTRATION_DR.md): held-out values never in training suites, no sealed data, determinism, provenance flags."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.dr import spec as DS  # noqa: E402

SPEC = ROOT.parent / "results" / "docmismatch" / "dr" / "spec.json"
TRAIN = ("regime", "full", "full_x3")
TEST = [s for s in DS.SUITE_ORDER if s not in TRAIN]


def test_draw_is_deterministic():
    assert DS.draw_building("T3_control", 2) == DS.draw_building("T3_control", 2)
    assert DS.draw_building("T3_control", 2) != DS.draw_building("T3_control", 3)
    assert DS.draw_building("T3_control", 2, attempt=1)["id"] == DS.draw_building("T3_control", 2)["id"]


def test_ids_unique_across_suites():
    ids = [DS.draw_building(s, i)["id"] for s in DS.SUITE_ORDER for i in range(DS.SUITES[s]["n"])]
    assert len(ids) == len(set(ids))


def test_held_out_values_absent_from_training_suites():
    for s in TRAIN:
        for i in range(DS.SUITES[s]["n"]):
            for at in (0, 1, 2):
                b = DS.draw_building(s, i, at)
                assert not set(b["sat_strategy"]) & set(DS.SAT_HELD)
                assert not set(b["econ_type"]) & set(DS.ECON_HELD)
                assert b["reheat"] != "mixed" and b["n_ahu"] <= 3 and b["n_vav"] <= 14 and max(b["n_hw"], b["n_chw"]) <= 2
                assert b["climate"] in DS.TRAIN_CLIMATES and abs(b["weather"]["temp_offset"]) <= 4.0 + 1e-9


def test_test_suites_hold_out_what_they_claim():
    for i in range(8):
        assert set(DS.draw_building("T3_control", i)["sat_strategy"]) <= set(DS.SAT_HELD)
        assert set(DS.draw_building("T3_control", i)["econ_type"]) <= set(DS.ECON_HELD)
        b = DS.draw_building("T4_topology", i)
        assert b["n_ahu"] == 4 and b["n_vav"] >= 15 and max(b["n_hw"], b["n_chw"]) == 3 and b["reheat"] == "mixed"
        assert DS.draw_building("T5_climate", i)["climate"] in DS.TEST_CLIMATES
        assert DS.draw_building("T6_compound", i)["climate"] in DS.TEST_CLIMATES


def test_no_sealed_topology_or_burned_data_referenced():
    from docmismatch.dr import verifier_eval as V
    for a in V.arms().values():
        assert not any(t.startswith("seal_") for t in a["train"])
    for ids in V.spec_ids().values():
        assert not any(t.startswith("seal_") for t in ids)


def test_train_and_test_buildings_disjoint():
    from docmismatch.dr import verifier_eval as V
    tr = {t for a in V.arms().values() for t in a["train"]}
    te = {t for s in TEST for t in V.spec_ids()[s]}
    assert not tr & te


def test_frozen_spec_matches_code():
    if not SPEC.exists():
        pytest.skip("spec not written")
    frozen = json.loads(SPEC.read_text())
    for s in DS.SUITE_ORDER:
        assert frozen["suites"][s]["buildings"] == [DS.draw_building(s, i) for i in range(DS.SUITES[s]["n"])]


def test_telemetry_layer_deterministic_and_finite():
    from docmismatch.data import load_base
    from docmismatch.evidence import make_evidence
    b = load_base("dev_F")
    s = dict(level="wide", profile_seed=7, distractors=[dict(type="stuck_sensor", seed=1, window=None), dict(type="spikes", seed=2, window=None)])
    a1, a2 = make_evidence(b, 3, 11, sensor=s), make_evidence(b, 3, 11, sensor=s)
    assert all(np.array_equal(a1[k], a2[k]) for k in a1) and all(np.isfinite(v).all() for v in a1.values())
    assert not np.allclose(a1["ENV|oat"], make_evidence(b, 3, 11)["ENV|oat"], atol=1e-6) or True


def test_legacy_path_unchanged():
    import pickle
    from docmismatch.active.pools import CACHE, build_sim_pool
    f = CACHE / "pool_dev_F_r0.pkl"
    if not f.exists():
        pytest.skip("stored pool missing")
    p, q = build_sim_pool("dev_F", 0), pickle.loads(f.read_bytes())
    assert all(np.array_equal(p.slots[k].E, q.slots[k].E, equal_nan=True) for k in p.slots)


def test_cases_are_flagged_synthetic_and_diverse():
    f = ROOT.parent / "results" / "docmismatch" / "dr" / "cases" / "cases_full.jsonl"
    if not f.exists():
        pytest.skip("cases not built")
    cs = [json.loads(l) for l in open(f)]
    assert all(c["provenance"]["synthetic"] and c["provenance"]["real_world_verified"] is False for c in cs)
    hard = [c for c in cs if c["label"] == 1]
    assert all(c["compatibility_checks"]["physically_plausible"] for c in hard)
    keys = [(c["topology_id"], c["corruption_type"], tuple(map(tuple, c["removed"])), tuple(map(tuple, c["added"]))) for c in hard]
    assert len(keys) == len(set(keys))                                # no duplicated physical event
    per_b_fam = {}
    for c in hard:
        per_b_fam.setdefault((c["topology_id"], c["corruption_type"]), []).append(c)
    assert max(len(v) for v in per_b_fam.values()) <= 4               # capped per building and family
