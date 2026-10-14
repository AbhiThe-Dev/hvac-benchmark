"""System topology (pilot/topology.py): what the drawings claim for a room, what the topology-verifying checks found, and whether
the drawings were right. The rules under test: nothing is inferred from an unrelated root cause; a commanding check that gets no
response is INCONCLUSIVE (a dead actuator looks the same as a wrong box); the one thing asked of the technician (`actual_box`)
is only accepted where it can be true, and is checked against this visit's own building."""
import csv
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]           # doc_mismatch/
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test-not-real")
os.environ.setdefault("NOTIFY_EMAIL", "dev@example.com")
os.environ.setdefault("SMTP_FROM_EMAIL", "dev@example.com")
os.environ.setdefault("SMTP_APP_PASSWORD", "not-a-real-app-password")
os.environ.setdefault("PILOT_DATA_DIR", tempfile.mkdtemp(prefix="pilot_topology_test_"))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from pilot import auth, cases as CS, config, db, topology as T, visit as V  # noqa: E402
from pilot.app import app  # noqa: E402
from pilot.case_schema import DecisionRequest, IntentRequest  # noqa: E402
from pilot.scripts import export_cases  # noqa: E402

AHU, A2 = "NORTHWING-AHU-01", "SOUTHWING-AHU-02"
B1, B2, B3 = "VAV-ZK-17", "VAV-ZK-18", "VAV-ZK-30"
R1, R2, R3 = "Suite 210 Kowalski Dental", "Suite 212 Larsen Law", "Suite 340 Okafor Realty"
BUILDING = {
    "equipment": [{"id": AHU, "kind": "AHU"}, {"id": A2, "kind": "AHU"}, {"id": B1, "kind": "VAV"}, {"id": B2, "kind": "VAV"}, {"id": B3, "kind": "VAV"},
                  {"id": R1, "kind": "Zone"}, {"id": R2, "kind": "Zone"}, {"id": R3, "kind": "Zone"}],
    "claims": {"vav_zone": {R1: B1, R2: B2, R3: B3}, "ahu_vav": {B1: AHU, B2: AHU, B3: A2}},
    "control_system": {"points": {
        AHU: {"fan_status": "BLDG7.NW.SF", "static_pressure": "BLDG7.NW.SP"},
        B1: {"status": "V17.STS", "airflow": "V17.CFM", "reheat": "V17.RHT"}, B2: {"status": "V18.STS"},
        R1: {"temperature": "R210.T"}}},
}


# ------------------------------------------------------------------------------------------------- the building

def test_the_drawings_claim_for_a_room_and_what_surrounds_it():
    d = T.building_view(BUILDING, R1)
    assert (d["ahu"], d["box"], d["room"]) == (AHU, B1, R1)
    assert d["boxes_on_ahu_seen"] == [B1, B2] and d["rooms_on_ahu_seen"] == [R1, R2] and (d["n_boxes_on_ahu_seen"], d["n_rooms_on_ahu_seen"]) == (2, 2)
    assert d["ahu_points"] == ["fan_status", "static_pressure"] and d["box_points"] == ["airflow", "reheat", "status"]
    assert d["zone_temperature_point"] is True and d["reheat_point"] is True
    other = T.building_view(BUILDING, R3)
    assert (other["ahu"], other["boxes_on_ahu_seen"]) == (A2, [B3]), "a room on a different air handler sees only its own"
    bare = T.building_view(BUILDING, R2)
    assert bare["box_points"] == ["status"] and bare["reheat_point"] is False and bare["zone_temperature_point"] is False


def test_a_room_the_drawings_do_not_mention_and_a_bare_building_do_not_crash():
    d = T.building_view(BUILDING, "Nowhere")
    assert d["box"] is None and d["ahu"] is None and d["boxes_on_ahu_seen"] == [] and d["ahu_points"] == []
    assert T.building_view({"equipment": []}, "x")["box"] is None
    assert T.candidate_boxes(BUILDING) == [B1, B2, B3] and T.candidate_boxes({}) == []


# ------------------------------------------------------------------------------------------------- the evidence

def ev(kind, id=0, **payload):
    return dict(id=id, kind=kind, payload=payload, server_ts="2026-10-01T09:00:00+00:00")


def result(check, target, word):
    return ev("check_result", check=check, target=target, word=word)


def test_only_the_topology_checks_count_and_a_commanding_no_is_inconclusive():
    events = [result("duct_trace", B1, "yes"), result("duct_trace", B2, "no"), result("override_room", B1, "yes"), result("override_diffuser", B2, "no"),
              result("bas_static", B1, "abnormal"), result("duct_trace", B1, "unsure"), result("override_room", B2, "skip")]
    got = [(e["check"], e["target"], e["direct"], e["reading"]) for e in T.evidence(events)]
    assert got == [("duct_trace", B1, True, "serves_room"), ("duct_trace", B2, True, "not_this_box"),
                   ("override_room", B1, False, "serves_room"), ("override_diffuser", B2, False, "inconclusive")], \
        "a dead actuator looks exactly like a wrong box, so only the duct trace can say 'not this box'"


# ------------------------------------------------------------------------------------------------- were the drawings right?

def rc(cause, actual=None):
    return ev("root_cause", cause_id=cause, actual_box=actual)


def tool(cause_id, cause):
    # built by hand: the payload's own "id" key would collide with ev()'s event-id parameter
    return dict(id=0, kind="tool_conclusion", payload=dict(id=cause_id, cause=cause), server_ts="2026-10-01T09:00:00+00:00")


@pytest.mark.parametrize("events,status,basis,actual,conflict", [
    ([], "unverified", None, None, False),
    ([rc("actuator_fail")], "unverified", None, None, False),                                    # a failed actuator does not prove the drawings right
    ([result("duct_trace", B1, "yes")], "right", "duct_trace", None, False),
    ([result("duct_trace", B1, "no")], "wrong", "duct_trace", None, False),
    ([result("duct_trace", B1, "no"), result("duct_trace", B2, "yes")], "wrong", "duct_trace", B2, False),
    ([result("duct_trace", B2, "yes")], "wrong", "duct_trace", B2, False),
    ([result("override_room", B1, "no")], "unverified", None, None, False),                      # inconclusive, not 'wrong'
    ([result("override_room", B1, "yes")], "unverified", None, None, False),                      # indirect evidence alone does not set the status
    ([tool("documentation_wrong", ["wrong", B2])], "suspected_wrong", "tool", None, False),
    ([tool("documentation_wrong", ["unlisted"])], "suspected_wrong", "tool", None, False),
    ([tool("documentation_wrong", ["wrong", B2]), rc("documentation_wrong", B2)], "wrong", "technician", B2, False),
    ([rc("documentation_wrong")], "wrong", "technician", None, False),                           # said wrong, did not say which box
    ([rc("documentation_wrong", "not_listed")], "wrong", "technician", "not_listed", False),
    ([result("duct_trace", B2, "yes"), rc("documentation_wrong")], "wrong", "technician", B2, False),   # the trace fills in the box they did not name
    ([result("duct_trace", B1, "yes"), rc("documentation_wrong")], "wrong", "technician", None, True),   # they disagree: flagged, technician wins
    ([result("duct_trace", B1, "no"), result("duct_trace", B1, "yes")], "right", "duct_trace", None, False),  # latest trace wins
    ([tool("documentation_wrong", ["wrong", B2]), result("duct_trace", B1, "yes")], "right", "duct_trace", None, False),  # a trace outranks the tool
])
def test_were_the_drawings_right(events, status, basis, actual, conflict):
    v = T.verified(events, B1)
    assert (v["status"], v["basis"], v["actual_box"], v["conflict"]) == (status, basis, actual, conflict)


def test_the_tools_claim_is_recorded_separately_from_what_was_verified():
    v = T.verified([tool("documentation_wrong", ["wrong", B2])], B1)
    assert v["tool_claim"] == dict(box=B2) and v["status"] == "suspected_wrong"
    assert T.verified([tool("documentation_wrong", ["unlisted"])], B1)["tool_claim"] == dict(box="not_listed")
    assert T.verified([tool("actuator_fail", ["actuator_fail"])], B1)["tool_claim"] is None


def test_reheat_is_what_was_declared_what_the_chip_says_and_whether_a_point_exists():
    events = [ev("question_answer", key="reheat", answer="no"), ev("question_answer", key="bas_access", answer="yes"), ev("question_answer", key="reheat", answer="yes")]
    t = T.build(BUILDING, R1, events, "vav_hot_water_reheat", [R1, R2, R3])
    assert t["reheat"] == dict(declared="yes", system_kind="vav_hot_water_reheat", reheat_point_documented=True), "the latest declaration wins"
    assert t["documented"]["visit_rooms_on_same_ahu"] == 2, "R1 and R2 share an air handler; R3 does not"
    none = T.build(BUILDING, R2, [], None)
    assert none["reheat"] == dict(declared=None, system_kind=None, reheat_point_documented=False) and none["documented"]["visit_rooms_on_same_ahu"] == 1


# ------------------------------------------------------------------------------------------------- the one thing asked

@pytest.fixture(autouse=True)
def _fresh(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "pilot.db")
    monkeypatch.setattr(config, "VISITS_DIR", tmp_path / "visits")
    db.init_db(config.DB_PATH)


def _visit(rooms=(R1,)):
    vid = V.create_visit(BUILDING, list(rooms), feel="too_hot", airflow="yes", context=dict(complaint_text="hot"))
    with db.connect(config.DB_PATH) as conn:
        return vid, db.get_case_for_room(conn, vid, 0)["id"]


def _root(cid, cause="documentation_wrong", **kw):
    with db.connect(config.DB_PATH) as conn:
        CS.record_root_cause(conn, cid, cause_id=cause, text=None, how_confirmed=kw.pop("how_confirmed", "observed_directly"), client_ts=None, **kw)
        return db.get_events(conn, cid)[-1]["payload"]


def test_which_box_is_kept_when_the_drawings_were_wrong_and_the_box_is_real():
    _, cid = _visit()
    assert _root(cid, actual_box=B2)["actual_box"] == B2
    assert _root(cid, actual_box="not_listed")["actual_box"] == "not_listed"
    assert _root(cid, actual_box="not_sure")["actual_box"] == "not_sure"
    assert _root(cid, actual_box="  ")["actual_box"] is None and _root(cid)["actual_box"] is None, "optional: blank is simply not answered"
    assert _root(cid, actual_box=B3)["actual_box"] == B3, "a box on another air handler is still one of this building's boxes"


def test_which_box_is_refused_where_it_cannot_be_true_and_writes_nothing():
    _, cid = _visit()
    with pytest.raises(ValueError, match="only applies when the drawings were wrong"):
        _root(cid, cause="actuator_fail", actual_box=B2)
    with pytest.raises(ValueError, match="not one of this building's other boxes"):
        _root(cid, actual_box="VAV-NOT-HERE")
    with pytest.raises(ValueError, match="not one of this building's other boxes"):
        _root(cid, actual_box=B1)                                                  # the box the drawings already name
    with pytest.raises(ValueError, match="not one of this building's other boxes"):
        _root(cid, actual_box=R2)                                                  # a room is not a box
    with db.connect(config.DB_PATH) as conn:
        assert [e for e in db.get_events(conn, cid) if e["kind"] == "root_cause"] == []


def test_if_the_building_file_cannot_be_read_only_the_two_open_answers_are_accepted(tmp_path):
    vid, cid = _visit()
    (config.VISITS_DIR / vid / "building.json").unlink()
    assert _root(cid, actual_box="not_sure")["actual_box"] == "not_sure"
    with pytest.raises(ValueError):
        _root(cid, actual_box=B2)


@pytest.fixture
def http():
    app.dependency_overrides[auth.require_token] = lambda: "test-token"
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_the_record_view_offers_the_other_boxes_and_the_api_takes_the_answer(http):
    _, cid = _visit()
    topo = http.get(f"/api/cases/{cid}/record").json()["topology"]
    assert topo == dict(documented_box=B1, boxes=[B2, B3]), "the drawings' own box is not offered as the answer"
    assert http.post(f"/api/cases/{cid}/root_cause", json=dict(cause_id="documentation_wrong", actual_box=B2)).status_code == 200
    assert http.post(f"/api/cases/{cid}/root_cause", json=dict(cause_id="documentation_wrong", actual_box="nope")).status_code == 400
    assert http.post(f"/api/cases/{cid}/root_cause", json=dict(cause_id="actuator_fail", actual_box=B2)).status_code == 400


# ------------------------------------------------------------------------------------------------- the export

def _export(tmp_path):
    with db.connect(config.DB_PATH) as conn:
        if db.get_active_participant(conn) is None:
            db.create_participant(conn, role="contractor_tech", years_band="2to5", vav_band="some")
    out = tmp_path / "export"
    export_cases.export(tmp_path, out)
    return [json.loads(line) for line in (out / "cases.jsonl").read_text().splitlines()], list(csv.DictReader((out / "cases.csv").open())), out


def _participant():
    with db.connect(config.DB_PATH) as conn:
        db.create_participant(conn, role="contractor_tech", years_band="2to5", vav_band="some")


def test_a_case_where_the_drawings_were_wrong_exports_the_whole_topology_aliased(tmp_path):
    _participant()
    _, cid = _visit(rooms=(R1, R2))
    _root(cid, actual_box=B2)
    recs, rows, out = _export(tmp_path)
    t = next(r for r in recs if r["case_id"] == cid)["topology"]
    assert t["documented"]["box"] == "vav_1" and t["documented"]["ahu"] == "ahu_1" and t["documented"]["room"] == "room_1"
    assert t["documented"]["boxes_on_ahu_seen"] == ["vav_1", "vav_2"] and t["documented"]["visit_rooms_on_same_ahu"] == 2
    assert t["documented"]["ahu_points"] == ["fan_status", "static_pressure"] and t["documented"]["reheat_point"] is True
    assert t["verified"]["status"] == "wrong" and t["verified"]["basis"] == "technician" and t["verified"]["actual_box"] == "vav_2"
    row = next(r for r in rows if r["case_id"] == str(cid))
    assert (row["drawings_status"], row["drawings_basis"], row["actual_box_known"], row["n_boxes_on_ahu_seen"], row["visit_rooms_on_same_ahu"]) == \
           ("wrong", "technician", "True", "2", "2")
    text = (out / "cases.jsonl").read_text() + (out / "cases.csv").read_text()
    for planted in (AHU, A2, B1, B2, B3, R1, R2, R3, "Kowalski", "Larsen", "BLDG7", "V17.CFM", "R210.T"):
        assert planted not in text, f"{planted!r} leaked through the topology block"


def test_a_duct_trace_done_in_the_live_flow_shows_up_as_direct_evidence(tmp_path):
    _participant()
    vid, cid = _visit()
    V.submit_intent(vid, IntentRequest(kind="unsure"))
    V.submit_decision(vid, DecisionRequest(action="substitute", check="duct_trace", target=B1))
    V.answer(vid, "yes")
    recs, rows, _ = _export(tmp_path)
    t = recs[0]["topology"]
    assert t["evidence"] == [dict(check="duct_trace", target="vav_1", word="yes", direct=True, reading="serves_room")]
    assert t["verified"]["status"] == "right" and t["verified"]["basis"] == "duct_trace" and rows[0]["topology_checks"] == "1"


def test_a_case_with_nothing_verified_says_so_instead_of_guessing(tmp_path):
    _participant()
    _, cid = _visit()
    _root(cid, cause="actuator_fail", how_confirmed="measured")
    recs, rows, _ = _export(tmp_path)
    v = recs[0]["topology"]["verified"]
    assert v["status"] == "unverified" and v["basis"] is None and rows[0]["drawings_status"] == "unverified" and rows[0]["actual_box_known"] == ""
