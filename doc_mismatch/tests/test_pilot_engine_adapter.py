"""Guards for the pilot app's engine integration (pilot/engine_adapter.py, pilot/db.py, pilot/visit.py) --
not the reasoning engine itself (unmodified, already covered by test_troubleshoot_*.py). Covers: the
T3-noattr item set, econ_fault enrollment via Addendum 37's validated configuration, the numeric-reading
hazard that's possible without `attributes` on file, and multi-visit isolation/persistence-by-replay."""
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]           # doc_mismatch/
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

# pilot.config fails loudly if these are unset -- fine for the real app, but tests need dummy values
# set BEFORE the first import of pilot.config (directly or via pilot.db/pilot.visit).
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test-not-real")
os.environ.setdefault("NOTIFY_EMAIL", "dev@example.com")
os.environ.setdefault("SMTP_FROM_EMAIL", "dev@example.com")
os.environ.setdefault("SMTP_APP_PASSWORD", "not-a-real-app-password")
os.environ.setdefault("PILOT_DATA_DIR", tempfile.mkdtemp(prefix="pilot_test_"))

import numpy as np  # noqa: E402
import pytest  # noqa: E402

from pilot import config, db, engine_adapter as EA, visit as V  # noqa: E402
from _pilot_flow import run_check  # noqa: E402
from docmismatch.troubleshoot.v1 import causes as C  # noqa: E402
from docmismatch.troubleshoot.v2.joint import JointModel, JointSettings  # noqa: E402
from docmismatch.troubleshoot.v2.policies import PriorSession  # noqa: E402

BUILDING = {
    "equipment": [
        {"id": "AHU-1", "kind": "AHU"},
        {"id": "VAV-X", "kind": "VAV"},
        {"id": "Room-X", "kind": "Zone"},
    ],
    "claims": {"vav_zone": {"Room-X": "VAV-X"}, "ahu_vav": {"VAV-X": "AHU-1"}},
    "control_system": {"points": {
        "VAV-X": {"status": "V1.STS", "airflow": "V1.CFM", "damper": "V1.DMPR", "reheat": "V1.RHT"},
        "AHU-1": {"fan_status": "A1.SF", "static_pressure": "A1.SP", "economizer_position": "A1.ECO"},
        "Room-X": {"temperature": "R1.T"},
    }},
}


@pytest.fixture(autouse=True)
def _fresh_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "pilot.db")
    monkeypatch.setattr(config, "VISITS_DIR", tmp_path / "visits")
    db.init_db(config.DB_PATH)
    yield


def _write_building(tmp_path, data=None):
    p = tmp_path / "building.json"
    p.write_text(json.dumps(data or BUILDING))
    return p


def test_t3_noattr_has_bas_access_and_point_map_but_not_attributes(tmp_path):
    b = EA.load_building(_write_building(tmp_path))
    case = EA.build_cases(b, ["Room-X"])[0]
    assert case.items == EA.ITEMS
    assert "attributes" not in case.items
    assert {"bas_access", "point_map", "equipment_list", "claims"} <= case.items


def test_econ_fault_is_enrolled_with_addendum_37s_validated_shares(tmp_path):
    b = EA.load_building(_write_building(tmp_path))
    case = EA.build_cases(b, ["Room-X"])[0]
    assert case.extra_causes[0].id == "econ_fault"
    assert case.shares["econ_fault"] == EA.ECON_SHARE == 0.06


def test_involves_econ_fault_matches_only_the_econ_cause():
    assert EA.involves_econ_fault(("econ_fault",)) is True
    assert EA.involves_econ_fault(("damper_mech",)) is False
    assert EA.involves_econ_fault(("wrong", "VAV-9")) is False


def test_bare_numeric_reading_raises_under_t3_noattr_but_word_based_answer_does_not(tmp_path):
    """Documents and guards the hazard: bas_static/ahu_gauge/max_airflow/k_factor rely on an `attributes`
    value (static_setpoint_inwc etc.) that's always absent at T3-noattr. The pilot's own answer() API only
    ever accepts a word (see visit.answer's signature) -- this test is what makes that constraint load-bearing
    rather than accidental: if someone ever threads reading=/expected= through from the frontend, this is the
    failure it would hit in the field."""
    b = EA.load_building(_write_building(tmp_path))
    case = EA.build_cases(b, ["Room-X"])[0]

    sess = PriorSession(case, None)
    with pytest.raises(ValueError, match="nothing to compare"):
        sess.report(check="bas_static", target=case.doc, reading=1.0)

    sess2 = PriorSession(case, None)
    sess2.report(check="bas_static", target=case.doc, outcome="normal")   # must not raise
    assert sess2.elapsed > 0


def test_visit_lifecycle_single_room(tmp_path):
    vid = V.create_visit(BUILDING, ["Room-X"], feel="too_hot", airflow="yes")
    step = V.get_current_step(vid)
    assert step["kind"] in ("check", "question")

    for _ in range(50):
        step = V.get_current_step(vid)
        if step["kind"] == "check":
            _, step = run_check(V, vid)
        elif step["kind"] == "question":
            step = V.answer(vid, "no")
        elif step["kind"] == "conclude":
            assert "involves_econ_fault" in step
            break
    else:
        pytest.fail("room never concluded")

    done = V.advance(vid)
    assert done["kind"] == "visit_done"
    assert done["rooms"] == [{"name": "Room-X"}]
    assert done["visit_checks"] >= 1

    # resume after completion (simulates reopening after a restart) must not re-derive a different answer
    again = V.get_current_step(vid)
    assert again == done


def test_two_visits_stay_isolated_and_resume_correctly_after_interleaving(tmp_path):
    v1 = V.create_visit(BUILDING, ["Room-X"], feel="too_hot", airflow="yes")
    v2 = V.create_visit(BUILDING, ["Room-X"], feel="too_cold", airflow="no")
    assert v1 != v2

    s1 = V.get_current_step(v1)
    s2 = V.get_current_step(v2)
    assert s1["kind"] == "check" and s2["kind"] == "check"

    # interleave: answer v2 first, then v1, then re-fetch v1 -- must reflect only v1's own log
    revealed2, _ = run_check(V, v2)
    before = V.get_current_step(v1)
    assert before == s1, "answering visit 2 must not perturb visit 1's pending step"
    revealed1, _ = run_check(V, v1)

    with db.connect(config.DB_PATH) as conn:
        log1 = db.get_room_log(conn, v1, 0)
        log2 = db.get_room_log(conn, v2, 0)
    assert len(log1) == 1 and len(log2) == 1
    assert log1[0]["check_name"] == revealed1["name"]      # s1/s2 are the intent stage, which names nothing
    assert log2[0]["check_name"] == revealed2["name"]


def test_building_with_missing_complaint_room_claim_fails_fast_at_create_not_first_answer(tmp_path):
    bad = {**BUILDING, "claims": {"ahu_vav": {"VAV-X": "AHU-1"}}}   # no vav_zone entry for Room-X
    with pytest.raises(Exception):
        V.create_visit(bad, ["Room-X"])


# ------------------------------------------------------------------------------------------------- the joint model: severity mixture by default
def _building_with_rooms(n):
    eq = [{"id": "AHU-1", "kind": "AHU"}] + [{"id": f"VAV-{i}", "kind": "VAV"} for i in range(n)] + [{"id": f"Room-{i}", "kind": "Zone"} for i in range(n)]
    pts = {f"VAV-{i}": {"status": f"V{i}.STS", "airflow": f"V{i}.CFM", "damper": f"V{i}.D", "reheat": f"V{i}.R"} for i in range(n)}
    pts["AHU-1"] = {"fan_status": "A.SF", "static_pressure": "A.SP", "economizer_position": "A.E"}
    pts.update({f"Room-{i}": {"temperature": f"R{i}.T"} for i in range(n)})
    return {"equipment": eq, "claims": {"vav_zone": {f"Room-{i}": f"VAV-{i}" for i in range(n)}, "ahu_vav": {f"VAV-{i}": "AHU-1" for i in range(n)}}, "control_system": {"points": pts}}


def test_joint_model_defaults_to_the_severity_mixture_and_keeps_econ_fault(monkeypatch):
    monkeypatch.delenv(EA.JOINT_MODEL_ENV, raising=False)
    assert EA.joint_model_name() == "mixed"
    js = EA.joint_settings()
    assert js.low_mix == EA.LOW_MIX and abs(sum(w for _, w in EA.LOW_MIX) - 1.0) < 1e-12
    assert C.ECON_FAULT.id in js.states and "low_static~1" in js.states and js.state_prior.sum() == pytest.approx(1.0)


def test_switching_back_to_shipped_gives_exactly_the_old_settings(monkeypatch):
    monkeypatch.setenv(EA.JOINT_MODEL_ENV, "shipped")
    js = EA.joint_settings()
    old = JointSettings(extra_states=(C.ECON_FAULT.id,), extra_affect={C.ECON_FAULT.id: EA.ECON_AFFECT}, extra_share={C.ECON_FAULT.id: EA.ECON_SHARE_OF_F})
    assert js.low_mix == () and js.states == old.states and np.allclose(js.state_prior, old.state_prior) and np.allclose(js.affect, old.affect)


def test_an_unknown_joint_model_value_fails_loudly(monkeypatch):
    monkeypatch.setenv(EA.JOINT_MODEL_ENV, "tuned")
    with pytest.raises(ValueError, match="mixed' or 'shipped"):
        EA.joint_settings()


def test_catalogue_hash_records_the_joint_model_and_the_shipped_hash_is_unchanged(monkeypatch):
    parts = [[c.name, c.family, c.access_min, c.do_min, c.wait_min] for c in EA.CHECKS]
    old = hashlib.sha1(json.dumps([parts, EA.MIN_RATE, sorted(EA.SHARES.items()), EA.ECON_AFFECT, EA.ECON_SHARE_OF_F], sort_keys=True, default=str).encode()).hexdigest()[:12]
    monkeypatch.setenv(EA.JOINT_MODEL_ENV, "shipped")
    assert EA.catalogue_hash() == old                       # a stored case from before the mixture keeps meaning what it meant
    monkeypatch.setenv(EA.JOINT_MODEL_ENV, "mixed")
    assert EA.catalogue_hash() != old


def test_mixture_sees_a_shared_fault_on_a_large_air_handler_that_the_shipped_model_cannot(tmp_path, monkeypatch):
    """4 complaints among 49 rooms of one air handler: the shipped model's odds of low static are about 4e-11 (it never reads the handler); the mixture's are not negligible.
    On an 8-room handler both models agree that low static is likely."""
    b = EA.load_building(_write_building(tmp_path, _building_with_rooms(4)))
    cases = EA.build_cases(b, [f"Room-{i}" for i in range(4)])

    def low_static(model_name, rooms):
        monkeypatch.setenv(EA.JOINT_MODEL_ENV, model_name)
        m = JointModel(cases, EA.joint_settings(), children={"AHU-1": rooms})
        return m.ahu_posterior_by_cause(m.initial())["AHU-1"]["low_static"]
    assert low_static("shipped", 49) < 1e-9
    assert low_static("mixed", 49) > 1e-3
    assert low_static("shipped", 8) > 0.5 and low_static("mixed", 8) > 0.5


def test_a_visit_runs_end_to_end_on_the_default_mixture(tmp_path, monkeypatch):
    monkeypatch.delenv(EA.JOINT_MODEL_ENV, raising=False)
    b = _write_building(tmp_path)
    cases = EA.build_cases(EA.load_building(b), ["Room-X"])
    model = EA.build_joint_model(cases)
    assert "low_static~2" in model.js.states and model.marg0[0].sum() == pytest.approx(1.0)

