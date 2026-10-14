"""The one-tap re-check: after a repair, the technician repeats the test that found the fault and says whether it is now fine.
What must hold: only a test that FOUND something can be re-checked; a repair must be recorded first; it never touches the engine;
it never grants a ladder rung (it can only flag a contradiction); and the latest answer per test wins."""
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
os.environ.setdefault("PILOT_DATA_DIR", tempfile.mkdtemp(prefix="pilot_recheck_test_"))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from pilot import auth, cases as CS, config, db, visit as V  # noqa: E402
from pilot.app import app  # noqa: E402
from pilot.ladder import recheck_candidates, verification  # noqa: E402
from pilot.scripts import export_cases  # noqa: E402
from _pilot_flow import run_check  # noqa: E402


# ------------------------------------------------------------------------------------------------- the pure parts

class Events:
    """A tiny event log with ids, as db.get_events returns."""
    def __init__(self):
        self.items = []

    def add(self, kind, **payload):
        self.items.append(dict(id=len(self.items) + 1, kind=kind, payload=payload, server_ts="2026-10-01T09:00:00+00:00"))
        return self.items[-1]["id"]

    def result(self, word, check="bas_static", text=None, reading=None):
        return self.add("check_result", check=check, target="VAV-1", word=word, text=text, reading_text=reading)

    def recheck(self, of, result, reading=None):
        self.add("post_repair_check", of_event_id=of, result=result, reading_text=reading)


def fixed_case(ev, fixed="yes"):
    ev.add("root_cause", cause_id="low_static", how_confirmed="measured", confirmed_before_repair=True)
    ev.add("repair", actions=["replaced_part"], text=None)
    if fixed:
        ev.add("outcome", fixed=fixed)


def test_only_checks_that_found_something_are_candidates_newest_three():
    ev = Events()
    ids = [ev.result("normal", "a"), ev.result("abnormal", "b", text="B"), ev.result("yes", "c"), ev.result("unsure", "d"), ev.result("no", "e"),
           ev.result("abnormal", "f"), ev.result("abnormal", "g")]
    cands = recheck_candidates(ev.items)
    assert [c["check"] for c in cands] == ["c", "f", "g"], "positives only (abnormal / yes), the three most recent"
    assert [c["of_event_id"] for c in cands] == [ids[2], ids[5], ids[6]]
    assert all(c["latest"] is None for c in cands)
    assert recheck_candidates(ev.items, limit=10)[0]["text"] == "B"


def test_the_latest_recheck_per_test_is_attached_and_wins():
    ev = Events()
    a, b = ev.result("abnormal", "a"), ev.result("abnormal", "b")
    ev.recheck(a, "still_wrong", "0.2 in")
    ev.recheck(a, "now_ok", "0.9 in")
    ev.recheck(b, "unsure")
    cands = {c["check"]: c for c in recheck_candidates(ev.items)}
    assert cands["a"]["latest"]["result"] == "now_ok" and cands["a"]["latest"]["reading_text"] == "0.9 in" and cands["b"]["latest"]["result"] == "unsure"
    assert verification(ev.items)["recheck"] == dict(state="now_ok", n=2), "'couldn't tell' does not count against a decided 'fine'"


@pytest.mark.parametrize("answers,state", [([], None), (["unsure"], "unsure"), (["now_ok"], "now_ok"), (["still_wrong"], "still_wrong"),
                                           (["now_ok", "still_wrong"], "still_wrong"), (["now_ok", "unsure"], "now_ok")])
def test_the_overall_recheck_state(answers, state):
    ev = Events()
    for i, a in enumerate(answers):
        ev.recheck(ev.result("abnormal", f"c{i}"), a)
    assert verification(ev.items)["recheck"]["state"] == state


def test_a_recheck_never_grants_a_rung():
    ev = Events()
    fixed_case(ev, fixed=None)                    # a repair, but the outcome was never recorded
    before = verification(ev.items)
    ev.recheck(ev.result("abnormal", "bas_static"), "now_ok")
    after = verification(ev.items)
    assert before["rungs"] == after["rungs"] and before["level"] == after["level"] and not after["rungs"]["repair_confirmed"], \
        "'it's fine now' is not a repair confirmation: only the recorded outcome is"


def test_still_wrong_after_a_recorded_fix_is_flagged_but_does_not_remove_the_rung():
    ev = Events()
    chk = ev.result("abnormal", "bas_static")
    fixed_case(ev)
    ev.recheck(chk, "still_wrong")
    v = verification(ev.items)
    assert "recheck_contradicts_fix" in v["caveats"] and v["rungs"]["repair_confirmed"] and v["level"] == 3, "a caveat, not a verdict"
    assert v["lines"][2]["text"] == "Recorded as fixed, but the re-check says it's still wrong"
    assert [l["warn"] for l in v["lines"]] == [False, False, True, False], "shown as a warning, not a plain tick"
    ev.recheck(chk, "now_ok")
    assert not any(l["warn"] for l in verification(ev.items)["lines"]), "the latest answer wins"


def test_no_contradiction_is_claimed_where_nothing_was_called_fixed():
    for fixed in (None, "no", "partial", "unknown"):
        ev = Events()
        chk = ev.result("abnormal", "bas_static")
        fixed_case(ev, fixed=fixed)
        ev.recheck(chk, "still_wrong")
        assert "recheck_contradicts_fix" not in verification(ev.items)["caveats"], fixed


def test_a_confirming_recheck_changes_the_wording_only():
    ev = Events()
    chk = ev.result("abnormal", "bas_static")
    fixed_case(ev)
    plain = verification(ev.items)
    ev.recheck(chk, "now_ok")
    v = verification(ev.items)
    assert v["lines"][2]["text"] == "The repair fixed it, and the re-check agrees" and plain["lines"][2]["text"] == "The repair fixed it"
    assert v["caveats"] == plain["caveats"] and v["rungs"] == plain["rungs"]


# ------------------------------------------------------------------------------------------------- recording it

BUILDING = {
    "equipment": [{"id": "NORTHWING-AHU-01", "kind": "AHU"}, {"id": "VAV-ZK-17", "kind": "VAV"}, {"id": "Suite 210 Kowalski Dental", "kind": "Zone"}],
    "claims": {"vav_zone": {"Suite 210 Kowalski Dental": "VAV-ZK-17"}, "ahu_vav": {"VAV-ZK-17": "NORTHWING-AHU-01"}},
    "control_system": {"points": {"VAV-ZK-17": {"status": "V1.STS"}, "NORTHWING-AHU-01": {"fan_status": "BLDG7.NW.SF"}, "Suite 210 Kowalski Dental": {"temperature": "R1.T"}}},
}
ROOM = "Suite 210 Kowalski Dental"


@pytest.fixture(autouse=True)
def _fresh(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "pilot.db")
    monkeypatch.setattr(config, "VISITS_DIR", tmp_path / "visits")
    db.init_db(config.DB_PATH)


def _case():
    """A real case with one positive check done through the live flow (the first answer word is always the check's positive one)."""
    vid = V.create_visit(BUILDING, [ROOM], feel="too_hot", airflow="yes", context=dict(complaint_text="hot"))
    run_check(V, vid, word=None)
    with db.connect(config.DB_PATH) as conn:
        cid = db.get_case_for_room(conn, vid, 0)["id"]
        result = next(e for e in db.get_events(conn, cid) if e["kind"] == "check_result")
    return vid, cid, result


def _repair(cid, actions=("replaced_part",)):
    with db.connect(config.DB_PATH) as conn:
        CS.record_repair(conn, cid, actions=list(actions), text=None, repaired_on=None, client_ts=None)


def _recheck(cid, of, result="now_ok", **kw):
    with db.connect(config.DB_PATH) as conn:
        return CS.record_recheck(conn, cid, of_event_id=of, result=result, reading_text=kw.get("reading_text"), note=kw.get("note"), client_ts=None)


def _events(cid):
    with db.connect(config.DB_PATH) as conn:
        return db.get_events(conn, cid)


def test_a_check_result_now_keeps_the_checks_wording():
    _, _, result = _case()
    assert isinstance(result["payload"]["text"], str) and len(result["payload"]["text"]) > 20, "the wording is stored for the re-check screen"
    assert result["payload"]["word"] in ("abnormal", "yes")


def test_a_recheck_is_recorded_against_its_original_and_leaves_the_engine_alone():
    vid, cid, result = _case()
    _repair(cid)
    with db.connect(config.DB_PATH) as conn:
        log_before = db.get_room_log(conn, vid, 0)
    step_before = V.get_current_step(vid)
    eid = _recheck(cid, result["id"], "now_ok", reading_text="0.9 in. w.c.", note="verified on the gauge")
    p = next(e for e in _events(cid) if e["id"] == eid)["payload"]
    assert p == dict(of_event_id=result["id"], check=result["payload"]["check"], target=result["payload"]["target"], before_word=result["payload"]["word"],
                     before_reading_text=None, result="now_ok", reading_text="0.9 in. w.c.", note="verified on the gauge")
    with db.connect(config.DB_PATH) as conn:
        assert db.get_room_log(conn, vid, 0) == log_before, "the engine's log is untouched (it would refuse a repeat of the same check)"
    assert V.get_current_step(vid) == step_before, "the visit replays exactly as before"


def test_a_recheck_needs_a_repair_first():
    _, cid, result = _case()
    with pytest.raises(ValueError, match="record what was done"):
        _recheck(cid, result["id"])
    assert [e for e in _events(cid) if e["kind"] == "post_repair_check"] == []


def test_only_a_check_that_found_something_in_this_case_can_be_rechecked():
    vid, cid, result = _case()
    _repair(cid)
    with pytest.raises(ValueError, match="not part of this case"):
        _recheck(cid, 99999)
    with pytest.raises(ValueError, match="not part of this case"):
        _recheck(cid, _events(cid)[0]["id"])                                  # an event, but not a check_result
    vid2, cid2, other = _case()
    with pytest.raises(ValueError, match="not part of this case"):
        _recheck(cid, other["id"])                                            # another case's check
    with db.connect(config.DB_PATH) as conn:                                  # a check that came back clean
        clean = db.append_event(conn, cid, "check_result", dict(check="bas_airflow", target="VAV-ZK-17", word="normal", text="x", reading_text=None))
    with pytest.raises(ValueError, match="found something"):
        _recheck(cid, clean)
    assert [e for e in _events(cid) if e["kind"] == "post_repair_check"] == []


def test_a_repair_that_was_not_a_repair_still_allows_recording_what_the_test_now_says():
    """'No repair needed' is a recorded answer to 'what was done': the test can still be repeated (it may have cleared by itself)."""
    _, cid, result = _case()
    _repair(cid, actions=("no_repair_needed",))
    assert _recheck(cid, result["id"], "now_ok")


# ------------------------------------------------------------------------------------------------- over HTTP

@pytest.fixture
def http():
    app.dependency_overrides[auth.require_token] = lambda: "test-token"
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_the_api_offers_the_candidates_and_takes_the_answer(http):
    _, cid, result = _case()
    rec = http.get(f"/api/cases/{cid}/record").json()
    assert rec["recheck"]["can"] is False and [c["of_event_id"] for c in rec["recheck"]["candidates"]] == [result["id"]]
    assert http.post(f"/api/cases/{cid}/recheck", json=dict(of_event_id=result["id"], result="now_ok")).status_code == 400, "no repair yet"
    http.post(f"/api/cases/{cid}/repair", json=dict(actions=["replaced_part"]))
    http.post(f"/api/cases/{cid}/outcome", json=dict(fixed="yes"))
    assert http.post(f"/api/cases/{cid}/recheck", json=dict(of_event_id=result["id"], result="still_wrong", reading_text="0.2 in")).status_code == 200
    rec = http.get(f"/api/cases/{cid}/record").json()
    assert rec["recheck"]["can"] is True and rec["recheck"]["candidates"][0]["latest"]["result"] == "still_wrong"
    assert "recheck_contradicts_fix" in rec["ladder"]["caveats"] and rec["ladder"]["recheck"]["state"] == "still_wrong"


def test_the_api_rejects_a_bad_answer_and_an_unknown_case(http):
    _, cid, result = _case()
    assert http.post(f"/api/cases/{cid}/recheck", json=dict(of_event_id=result["id"], result="fixed")).status_code == 422
    assert http.post(f"/api/cases/{cid}/recheck", json=dict(of_event_id="x", result="now_ok")).status_code == 422
    assert http.post("/api/cases/9999/recheck", json=dict(of_event_id=1, result="now_ok")).status_code == 404


def test_the_recheck_route_requires_a_token():
    assert TestClient(app).post("/api/cases/1/recheck", json=dict(of_event_id=1, result="now_ok")).status_code == 401


# ------------------------------------------------------------------------------------------------- the export

def test_the_export_carries_the_rechecks_and_scrubs_their_wording(tmp_path):
    with db.connect(config.DB_PATH) as conn:
        db.create_participant(conn, role="contractor_tech", years_band="2to5", vav_band="some")
    _, cid, result = _case()
    _repair(cid)
    with db.connect(config.DB_PATH) as conn:
        CS.record_outcome(conn, cid, fixed="yes", note=None, client_ts=None)
    _recheck(cid, result["id"], "still_wrong", reading_text=f"still low at {ROOM}", note="call dana.k@clinic-example.com")
    out = tmp_path / "export"
    export_cases.export(tmp_path, out)
    rec = json.loads((out / "cases.jsonl").read_text().splitlines()[0])
    assert [r["result"] for r in rec["rechecks"]] == ["still_wrong"] and rec["rechecks"][0]["before_word"] == result["payload"]["word"]
    assert rec["verification"]["recheck"] == dict(state="still_wrong", n=1) and "recheck_contradicts_fix" in rec["verification"]["caveats"]
    row = next(csv.DictReader((out / "cases.csv").open()))
    assert row["recheck_state"] == "still_wrong" and "recheck_contradicts_fix" in row["caveats"]
    text = (out / "cases.jsonl").read_text() + (out / "cases.csv").read_text()
    for planted in ("Kowalski", "NORTHWING", "VAV-ZK-17", "dana.k@clinic-example.com", "BLDG7"):
        assert planted not in text, f"{planted!r} leaked through a re-check"
    assert "room_1" in text and "[email]" in text
