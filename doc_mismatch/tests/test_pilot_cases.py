"""Guards for the diagnostic case record (pilot/cases.py, case_schema.py, routes_case.py, and the intent / decision /
answer paths in visit.py). The reasoning engine itself is covered elsewhere; this file is about what the pilot
stores, in what order, and that a bad request can neither write a partial record nor break a visit."""
import json
import os
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]           # doc_mismatch/
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test-not-real")
os.environ.setdefault("NOTIFY_EMAIL", "dev@example.com")
os.environ.setdefault("SMTP_FROM_EMAIL", "dev@example.com")
os.environ.setdefault("SMTP_APP_PASSWORD", "not-a-real-app-password")
os.environ.setdefault("PILOT_DATA_DIR", tempfile.mkdtemp(prefix="pilot_cases_test_"))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from pilot import auth, cases as CS, config, db, engine_adapter as EA, visit as V  # noqa: E402
from pilot.app import app  # noqa: E402
from pilot.case_schema import DecisionRequest, IntentRequest  # noqa: E402
from _pilot_flow import run_check  # noqa: E402

BUILDING = {
    "equipment": [{"id": "AHU-1", "kind": "AHU"}, {"id": "VAV-X", "kind": "VAV"}, {"id": "Room-X", "kind": "Zone"}],
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


class Clock:
    """db._now() is the only clock the case record uses, so patching it makes durations exact."""
    def __init__(self):
        self.t = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.t.isoformat()

    def advance(self, **kw):
        self.t += timedelta(**kw)


@pytest.fixture
def clock(monkeypatch):
    c = Clock()
    monkeypatch.setattr(db, "_now", c)
    return c


def _visit(**kw):
    return V.create_visit(BUILDING, ["Room-X"], feel=kw.pop("feel", "too_hot"), airflow=kw.pop("airflow", "yes"), **kw)


def _events(vid, room=0):
    with db.connect(config.DB_PATH) as conn:
        case = db.get_case_for_room(conn, vid, room)
        return db.get_events(conn, case["id"])


def _kinds(vid):
    return [e["kind"] for e in _events(vid)]


def _room_log(vid):
    with db.connect(config.DB_PATH) as conn:
        return db.get_room_log(conn, vid, 0)


def _to_revealed(vid, kind="unsure", **kw):
    V.submit_intent(vid, IntentRequest(kind=kind, **kw))
    return V.get_current_step(vid)


def _to_conclusion(vid):
    for _ in range(60):
        step = V.get_current_step(vid)
        if step["kind"] == "check":
            run_check(V, vid)
        elif step["kind"] == "question":
            V.answer(vid, "no")
        elif step["kind"] == "conclude":
            return step
    pytest.fail("room never concluded")


# ------------------------------------------------------------------------------------------------- storage

def test_schema_init_is_idempotent_and_case_event_is_append_only():
    db.init_db(config.DB_PATH)
    db.init_db(config.DB_PATH)
    vid = _visit()
    with db.connect(config.DB_PATH) as conn:
        case = db.get_case_for_room(conn, vid, 0)
        db.append_event(conn, case["id"], "intent", {"kind": "unsure"})
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        with db.connect(config.DB_PATH) as conn:
            conn.execute("UPDATE case_event SET kind = 'x'")
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        with db.connect(config.DB_PATH) as conn:
            conn.execute("DELETE FROM case_event")
    assert _kinds(vid) == ["intent"]


def test_one_case_per_room_with_version_stamps():
    vid = V.create_visit({**BUILDING, "equipment": BUILDING["equipment"] + [{"id": "VAV-Y", "kind": "VAV"}, {"id": "Room-Y", "kind": "Zone"}],
                          "claims": {"vav_zone": {"Room-X": "VAV-X", "Room-Y": "VAV-Y"}, "ahu_vav": {"VAV-X": "AHU-1", "VAV-Y": "AHU-1"}}},
                         ["Room-X", "Room-Y"])
    with db.connect(config.DB_PATH) as conn:
        rows = [db.get_case_for_room(conn, vid, i) for i in (0, 1)]
    assert all(r for r in rows) and rows[0]["id"] != rows[1]["id"]
    assert {r["data_version"] for r in rows} == {CS.DATA_VERSION}
    assert {r["catalogue_hash"] for r in rows} == {EA.catalogue_hash()}


def test_visit_that_predates_the_case_record_gets_a_case_lazily():
    vid = _visit()
    with db.connect(config.DB_PATH) as conn:
        conn.execute("DELETE FROM cases")
    assert V.get_current_step(vid)["stage"] == "intent"
    with db.connect(config.DB_PATH) as conn:
        assert db.get_case_for_room(conn, vid, 0) is not None


# ------------------------------------------------------------------------------------------------- context

def test_context_is_stored_on_the_case():
    ctx = dict(complaint_text="Cold calls from the east corner", complaint_source="occupant", building_type="office",
               system_kind="vav_hot_water_reheat", equipment_age_band="10to20", readings=dict(zone_temp="78 F", duct_static="0.4 in. w.c."),
               alarms_text="none", own_hypotheses=["box_mechanical", "sensing"], own_hypotheses_text="maybe the stat")
    vid = _visit(context=ctx)
    with db.connect(config.DB_PATH) as conn:
        c = db.get_case_for_room(conn, vid, 0)
    assert (c["complaint_text"], c["building_type"], c["equipment_age_band"]) == ("Cold calls from the east corner", "office", "10to20")
    assert json.loads(c["readings_json"]) == ctx["readings"]
    assert json.loads(c["own_hypotheses_json"]) == dict(groups=["box_mechanical", "sensing"], text="maybe the stat")


def test_bad_context_is_rejected_before_anything_is_written():
    with pytest.raises(ValueError, match="cause group"):
        _visit(context=dict(own_hypotheses=["not_a_group"]))
    with pytest.raises(ValueError, match="earlier case"):
        _visit(context=dict(prior_case_id=999))
    with db.connect(config.DB_PATH) as conn:
        assert conn.execute("SELECT COUNT(*) FROM visits").fetchone()[0] == 0
    assert not config.VISITS_DIR.exists() or not list(config.VISITS_DIR.iterdir()), "no building file left behind"


def test_prior_case_link_is_stored():
    first = _visit()
    with db.connect(config.DB_PATH) as conn:
        first_case = db.get_case_for_room(conn, first, 0)["id"]
    second = _visit(context=dict(prior_case_id=first_case))
    with db.connect(config.DB_PATH) as conn:
        assert db.get_case_for_room(conn, second, 0)["prior_case_id"] == first_case


# ------------------------------------------------------------------------------------------------- ask first, then reveal

def test_intent_stage_withholds_everything_about_the_suggestion():
    vid = _visit()
    step = V.get_current_step(vid)
    assert step["stage"] == "intent"
    assert set(step) == {"kind", "stage", "room", "case_id", "picker"}, "no name, text, cost, likelihood, words or memo note before the intent"
    assert step["picker"], "the technician still gets the full list to choose from"
    assert all(set(p) == {"name", "target", "family", "text", "words"} for p in step["picker"]), "no ranking or cost in the picker"
    order = [c.name for c in EA.CHECKS]
    names = [p["name"] for p in step["picker"]]
    assert names == sorted(names, key=order.index), "catalogue order, not the tool's preference order"
    assert _kinds(vid) == [], "looking at the step records nothing"


def test_intent_writes_intent_then_exactly_one_suggestion_snapshot():
    vid = _visit()
    revealed = _to_revealed(vid)
    assert revealed["stage"] == "revealed" and revealed["name"] and revealed["text"] and revealed["words"]
    ev = _events(vid)
    assert [e["kind"] for e in ev] == ["intent", "suggestion_shown"]
    shown = ev[1]["payload"]
    assert shown["check"] == revealed["name"] and shown["target"]
    ps = [r["p"] for r in shown["ranked"]]
    assert 1 <= len(ps) <= 5 and ps == sorted(ps, reverse=True)
    assert all({"cause", "id", "p"} <= set(r) for r in shown["ranked"])
    assert shown["intent_matches"] is False
    # re-fetching the step must not write a second snapshot, and a second intent for the same step is refused
    V.get_current_step(vid)
    with pytest.raises(ValueError, match="already"):
        V.submit_intent(vid, IntentRequest(kind="unsure"))
    assert _kinds(vid) == ["intent", "suggestion_shown"]


def test_intent_naming_the_suggested_check_is_flagged_as_a_match():
    twin = _visit()
    suggested = _to_revealed(twin)["name"]                    # the engine is deterministic: the twin visit gets the same suggestion
    vid = _visit()
    _to_revealed(vid, kind="check", check=suggested)
    ev = _events(vid)
    assert ev[0]["payload"]["check"] == suggested
    assert ev[1]["payload"]["intent_matches"] is True


def test_intent_validation_leaves_no_trace():
    vid = _visit()
    with pytest.raises(ValueError, match="not available"):
        V.submit_intent(vid, IntentRequest(kind="check", check="no_such_check"))
    with pytest.raises(ValueError, match="say what"):
        V.submit_intent(vid, IntentRequest(kind="other", text="   "))
    assert _kinds(vid) == []
    assert V.get_current_step(vid)["stage"] == "intent"


def test_free_text_intent_is_recorded():
    vid = _visit()
    _to_revealed(vid, kind="other", text="look at the thermostat history")
    assert _events(vid)[0]["payload"] == dict(choice="other", check=None, target=None, text="look at the thermostat history")


def test_decision_requires_intent_first():
    vid = _visit()
    with pytest.raises(ValueError, match="first"):
        V.submit_decision(vid, DecisionRequest(action="follow"))
    with pytest.raises(ValueError, match="start a check"):
        V.answer(vid, "yes")
    assert _kinds(vid) == [] and _room_log(vid) == []


# ------------------------------------------------------------------------------------------------- follow / substitute / skip / external

def test_follow_records_decision_start_and_result_with_exact_timing(clock):
    vid = _visit()
    revealed = _to_revealed(vid)
    clock.advance(seconds=5)
    started = V.submit_decision(vid, DecisionRequest(action="follow"))
    assert started["stage"] == "in_progress" and started["name"] == revealed["name"] and started["external"] is False
    assert started["started_at"] == clock()
    clock.advance(minutes=14)
    V.answer(vid, started["words"][0], minutes_correction=20, note="had to find the ladder")
    ev = _events(vid)
    assert [e["kind"] for e in ev] == ["intent", "suggestion_shown", "decision", "check_started", "check_result"]
    start, result = ev[3], ev[4]
    assert datetime.fromisoformat(result["server_ts"]) - datetime.fromisoformat(start["server_ts"]) == timedelta(minutes=14)
    p = result["payload"]
    assert p["check"] == revealed["name"] and p["word"] == started["words"][0] and p["followed_suggestion"] is True
    assert p["minutes_correction"] == 20, "the technician's correction sits beside the raw timestamps, which are untouched"
    assert p["note"] == "had to find the ladder" and p["modeled_minutes"] > 0
    assert p["room_log_id"] == _room_log(vid)[0]["id"]


def test_the_next_step_starts_over_at_intent():
    vid = _visit()
    run_check(V, vid)
    step = V.get_current_step(vid)
    assert step["kind"] in ("check", "question", "conclude")
    if step["kind"] == "check":
        assert step["stage"] == "intent"


def test_substitute_is_reported_to_the_engine_and_marked_not_followed():
    vid = _visit()
    revealed = _to_revealed(vid)
    other = next(p for p in revealed["picker"] if p["name"] != revealed["name"])
    started = V.submit_decision(vid, DecisionRequest(action="substitute", check=other["name"], target=other["target"], reason="prefer_other_first"))
    assert started["name"] == other["name"] and started["action"] == "substitute"
    V.answer(vid, started["words"][0])
    assert [r["check_name"] for r in _room_log(vid)] == [other["name"]], "the engine saw the check the technician actually did"
    ev = _events(vid)
    dec = next(e for e in ev if e["kind"] == "decision")["payload"]
    assert dec["suggested"]["check"] == revealed["name"] and dec["reason"] == "prefer_other_first"
    assert next(e for e in ev if e["kind"] == "check_result")["payload"]["followed_suggestion"] is False


def test_bad_substitutions_are_refused_and_leave_no_trace():
    vid = _visit()
    revealed = _to_revealed(vid)
    before = _kinds(vid)
    with pytest.raises(ValueError, match="suggested check"):
        V.submit_decision(vid, DecisionRequest(action="substitute", check=revealed["name"]))
    with pytest.raises(ValueError, match="not available"):
        V.submit_decision(vid, DecisionRequest(action="substitute", check="no_such_check"))
    with pytest.raises(ValueError, match="say what"):
        V.submit_decision(vid, DecisionRequest(action="external", external_text=" "))
    assert _kinds(vid) == before and _room_log(vid) == []
    assert V.get_current_step(vid)["stage"] == "revealed"


def test_skip_closes_the_step_and_the_engine_moves_on():
    vid = _visit()
    revealed = _to_revealed(vid)
    nxt = V.submit_decision(vid, DecisionRequest(action="skip", reason="already_known", note="saw it on the way in"))
    log = _room_log(vid)
    assert [(r["check_name"], r["outcome"]) for r in log] == [(revealed["name"], "skip")]
    ev = _events(vid)
    dec = ev[-1]
    assert dec["kind"] == "decision" and dec["payload"]["action"] == "skip" and dec["payload"]["room_log_id"] == log[0]["id"]
    assert "check_started" not in [e["kind"] for e in ev], "a skipped check has no timer"
    if nxt["kind"] == "check":
        assert nxt["stage"] == "intent", "skip ended the step: the next one asks for intent again"


def test_external_check_is_logged_with_a_timer_but_never_reaches_the_engine(clock):
    vid = _visit()
    revealed = _to_revealed(vid)
    started = V.submit_decision(vid, DecisionRequest(action="external", external_text="trend log of the zone sensor", reason="not_relevant"))
    assert started["external"] is True and started["text"] == "trend log of the zone sensor" and started["name"] is None
    clock.advance(minutes=9)
    back = V.answer(vid, result_text="setpoint was changed Tuesday", minutes_correction=None)
    assert _room_log(vid) == [], "an off-catalogue check must not touch the engine's log"
    kinds = _kinds(vid)
    assert kinds == ["intent", "suggestion_shown", "decision", "check_started", "external_result"]
    # the suggestion stays shown and the intent stays recorded: the technician is not asked again
    assert back["stage"] == "revealed" and back["name"] == revealed["name"]
    V.submit_decision(vid, DecisionRequest(action="external", external_text="another"))
    with pytest.raises(ValueError, match="describe"):
        V.answer(vid, result_text=" ")


# ------------------------------------------------------------------------------------------------- bad input

def test_bad_word_is_refused_before_any_write_and_the_visit_still_loads():
    vid = _visit()
    _to_revealed(vid)
    started = V.submit_decision(vid, DecisionRequest(action="follow"))
    events_before, log_before = _kinds(vid), _room_log(vid)
    for bad in ("banana", None, "", "skip"):                  # 'skip' is a decision, not a result
        with pytest.raises(ValueError):
            V.answer(vid, bad)
    assert _kinds(vid) == events_before and _room_log(vid) == log_before
    assert V.get_current_step(vid) == started, "the visit replays cleanly: nothing poisonous reached room_log"
    V.answer(vid, started["words"][0])
    assert len(_room_log(vid)) == 1


def test_numeric_reading_text_is_stored_and_never_forwarded_to_the_engine(monkeypatch):
    from docmismatch.troubleshoot.v1 import engine as engine_mod
    seen = []
    real = engine_mod.Session.report

    def spy(self, *a, **kw):
        seen.append(kw)
        return real(self, *a, **kw)

    monkeypatch.setattr(engine_mod.Session, "report", spy)
    vid = _visit()
    _to_revealed(vid)
    started = V.submit_decision(vid, DecisionRequest(action="follow"))
    V.answer(vid, started["words"][0], reading_text="0.8 in. w.c.")
    assert _events(vid)[-1]["payload"]["reading_text"] == "0.8 in. w.c."
    assert seen and all("reading" not in kw and "expected" not in kw for kw in seen)
    V.get_current_step(vid)                                  # a full replay is also fine


def test_wrong_stage_answers_are_refused():
    vid = _visit()
    _to_revealed(vid)                                        # revealed, not started
    with pytest.raises(ValueError, match="start a check"):
        V.answer(vid, "yes")
    V.submit_decision(vid, DecisionRequest(action="follow"))
    with pytest.raises(ValueError, match="already in progress"):
        V.submit_decision(vid, DecisionRequest(action="skip"))


# ------------------------------------------------------------------------------------------------- close-out

def test_tool_conclusion_is_recorded_once_and_the_step_carries_the_case_id():
    vid = _visit()
    step = _to_conclusion(vid)
    for _ in range(3):
        V.get_current_step(vid)
    tc = [e for e in _events(vid) if e["kind"] == "tool_conclusion"]
    assert len(tc) == 1
    assert tc[0]["payload"]["text"] == step["conclusion"] and "id" in tc[0]["payload"]
    with db.connect(config.DB_PATH) as conn:
        assert step["case_id"] == db.get_case_for_room(conn, vid, 0)["id"]


def _case_id(vid):
    with db.connect(config.DB_PATH) as conn:
        return db.get_case_for_room(conn, vid, 0)["id"]


def test_root_cause_agreement_is_derived_not_asserted():
    vid = _visit()
    _to_conclusion(vid)
    tool_id = next(e for e in _events(vid) if e["kind"] == "tool_conclusion")["payload"]["id"]
    cid = _case_id(vid)
    with db.connect(config.DB_PATH) as conn:
        other_id = next(c["id"] for c in EA.taxonomy_choices() if c["id"] != tool_id)
        CS.record_root_cause(conn, cid, cause_id=other_id, text=None, how_confirmed="measured", client_ts=None)
        CS.record_root_cause(conn, cid, cause_id="other", text="refrigerant side", how_confirmed="observed_directly", client_ts=None)
        CS.record_root_cause(conn, cid, cause_id="not_determined", text=None, how_confirmed="not_confirmed", client_ts=None)
        if tool_id in CS.TAXONOMY_IDS:
            CS.record_root_cause(conn, cid, cause_id=tool_id, text=None, how_confirmed="measured", client_ts=None)
    rc = [e["payload"] for e in _events(vid) if e["kind"] == "root_cause"]
    lumpy = tool_id in CS.LUMPS
    assert rc[0]["in_taxonomy"] is True and rc[0]["agrees_with_tool"] is (None if lumpy else False)
    assert rc[1]["in_taxonomy"] is False and rc[1]["text"] == "refrigerant side", "an out-of-taxonomy finding is recorded as such"
    assert rc[2]["agrees_with_tool"] is None
    if tool_id in CS.TAXONOMY_IDS:
        assert rc[3]["agrees_with_tool"] is True


def test_close_out_validation_refuses_before_writing():
    vid = _visit()
    cid = _case_id(vid)
    with db.connect(config.DB_PATH) as conn:
        for bad in (dict(cause_id="made_up", text=None, how_confirmed=None, client_ts=None),
                    dict(cause_id="other", text="  ", how_confirmed=None, client_ts=None)):
            with pytest.raises(ValueError):
                CS.record_root_cause(conn, cid, **bad)
        with pytest.raises(ValueError, match="choose what was done"):
            CS.record_repair(conn, cid, actions=[], text=None, repaired_on=None, client_ts=None)
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            CS.record_repair(conn, cid, actions=["replaced_part"], text=None, repaired_on="Oct 3", client_ts=None)
    assert _kinds(vid) == []


def test_a_fix_closes_the_case_and_starts_7_and_30_day_followups(clock):
    vid = _visit()
    cid = _case_id(vid)
    with db.connect(config.DB_PATH) as conn:
        CS.record_repair(conn, cid, actions=["replaced_part"], text="actuator", repaired_on="2026-10-01", client_ts=None)
        CS.record_outcome(conn, cid, fixed="yes", note=None, client_ts=None)
        case = db.get_case(conn, cid)
        due = {d["window_days"]: d["due_at"] for d in [db.get_followup(conn, cid, 7), db.get_followup(conn, cid, 30)]}
    assert case["status"] == "closed" and case["closed_at"] == clock()
    assert datetime.fromisoformat(due[7]) - clock.t == timedelta(days=7) and datetime.fromisoformat(due[30]) - clock.t == timedelta(days=30)
    clock.advance(days=3)
    with db.connect(config.DB_PATH) as conn:
        CS.record_outcome(conn, cid, fixed="yes", note="still good", client_ts=None)     # a repeat must not move the dates
        assert db.get_followup(conn, cid, 7)["due_at"] == due[7]


def test_no_fix_means_no_followups():
    vid = _visit()
    cid = _case_id(vid)
    with db.connect(config.DB_PATH) as conn:
        CS.record_outcome(conn, cid, fixed="no", note=None, client_ts=None)
        assert db.get_followup(conn, cid, 7) is None and db.get_followup(conn, cid, 30) is None


def test_followups_come_due_get_answered_once_and_record_who_entered_them(clock):
    vid = _visit()
    cid = _case_id(vid)
    fresh = _case_id(_visit())                               # a case with no follow-ups scheduled
    with db.connect(config.DB_PATH) as conn:
        CS.record_outcome(conn, cid, fixed="yes", note=None, client_ts=None)
        assert db.due_followups(conn) == []
        clock.advance(days=8)
        assert [(d["case_id"], d["window_days"]) for d in db.due_followups(conn)] == [(cid, 7)]
        CS.record_followup(conn, cid, window_days=7, recurred="no", note=None, recorded_by="developer", client_ts=None)
        assert db.due_followups(conn) == []
        with pytest.raises(ValueError, match="already answered"):
            CS.record_followup(conn, cid, window_days=7, recurred="yes", note=None, recorded_by="technician", client_ts=None)
        with pytest.raises(ValueError, match="no follow-up is scheduled"):
            CS.record_followup(conn, fresh, window_days=7, recurred="no", note=None, recorded_by="technician", client_ts=None)
    fu = next(e for e in _events(vid) if e["kind"] == "followup")["payload"]
    assert fu == dict(window_days=7, recurred="no", note=None, recorded_by="developer")


# ------------------------------------------------------------------------------------------------- HTTP

@pytest.fixture
def http():
    app.dependency_overrides[auth.require_token] = lambda: "test-token"
    yield TestClient(app)
    app.dependency_overrides.clear()


PROFILE = dict(role="contractor_tech", years_band="2to5", vav_band="some", ack=True)


def test_new_routes_require_a_token():
    c = TestClient(app)
    for method, path in (("get", "/api/inbox"), ("get", "/api/participant"), ("get", "/api/cases/1/record"), ("get", "/api/choices"),
                         ("post", "/api/participant"), ("post", "/api/cases/1/root_cause"), ("post", "/api/visits/x/intent"),
                         ("post", "/api/visits/x/decision")):
        assert getattr(c, method)(path).status_code == 401, path


def test_participant_needs_the_notice_acknowledged_and_is_created_once(http):
    assert http.get("/api/participant").json()["active"] is False
    assert len(http.get("/api/participant").json()["notice"]) >= 3
    assert http.post("/api/participant", json=dict(PROFILE, ack=False)).status_code == 422
    first = http.post("/api/participant", json=PROFILE).json()["participant_id"]
    again = http.post("/api/participant", json=dict(PROFILE, role="other")).json()["participant_id"]
    assert first == again
    assert http.get("/api/participant").json()["active"] is True
    with db.connect(config.DB_PATH) as conn:
        assert conn.execute("SELECT COUNT(*) FROM participants").fetchone()[0] == 1


def test_cases_are_tied_to_the_active_participant(http):
    before = _visit()
    pid = http.post("/api/participant", json=PROFILE).json()["participant_id"]
    after = _visit()
    with db.connect(config.DB_PATH) as conn:
        assert db.get_case_for_room(conn, before, 0)["participant_id"] is None
        assert db.get_case_for_room(conn, after, 0)["participant_id"] == pid


def test_close_out_over_http_and_validation_errors_are_400s(http):
    vid = _visit()
    cid = _case_id(vid)
    assert http.post(f"/api/cases/{cid}/root_cause", json=dict(cause_id="made_up")).status_code == 400
    assert http.post(f"/api/cases/{cid}/root_cause", json=dict(cause_id="actuator_fail", how_confirmed="measured")).status_code == 200
    assert http.post(f"/api/cases/{cid}/root_cause", json=dict(cause_id="actuator_fail", how_confirmed="guessing")).status_code == 422
    assert http.post(f"/api/cases/{cid}/repair", json=dict(actions=["replaced_part"])).status_code == 200
    assert http.post(f"/api/cases/{cid}/repair", json=dict(actions=["magic"])).status_code == 422
    assert http.post(f"/api/cases/{cid}/outcome", json=dict(fixed="yes")).status_code == 200
    assert http.post("/api/cases/9999/outcome", json=dict(fixed="yes")).status_code == 404
    assert http.post(f"/api/cases/{cid}/followup", json=dict(window_days=7, recurred="no")).status_code == 200
    assert http.post(f"/api/cases/{cid}/followup", json=dict(window_days=7, recurred="no")).status_code == 400
    assert http.post(f"/api/cases/{cid}/followup", json=dict(window_days=14, recurred="no")).status_code == 422


def test_inbox_lists_open_cases_then_due_followups(http, clock):
    assert http.get("/api/inbox").json()["participant"] is False
    http.post("/api/participant", json=PROFILE)
    vid = _visit()
    cid = _case_id(vid)
    assert http.get("/api/inbox").json()["awaiting"] == [], "a case still being diagnosed is not waiting on close-out"
    _to_conclusion(vid)
    box = http.get("/api/inbox").json()
    assert [(a["case_id"], a["next_needed"], a["room"]) for a in box["awaiting"]] == [(cid, "root_cause", "Room-X")]
    http.post(f"/api/cases/{cid}/root_cause", json=dict(cause_id="actuator_fail"))
    assert http.get("/api/inbox").json()["awaiting"][0]["next_needed"] == "repair"
    http.post(f"/api/cases/{cid}/repair", json=dict(actions=["replaced_part"]))
    http.post(f"/api/cases/{cid}/outcome", json=dict(fixed="yes"))
    box = http.get("/api/inbox").json()
    assert box["awaiting"] == [] and box["followups"] == []
    clock.advance(days=8)
    box = http.get("/api/inbox").json()
    assert [(f["case_id"], f["window_days"]) for f in box["followups"]] == [(cid, 7)]
    assert box["recent"][0]["case_id"] == cid


def test_the_technicians_record_view_shows_everything_stored(http):
    vid = _visit(context=dict(complaint_text="too warm", building_type="school"))
    run_check(V, vid)
    cid = _case_id(vid)
    rec = http.get(f"/api/cases/{cid}/record").json()
    assert rec["case"]["complaint_text"] == "too warm" and rec["case"]["building_type"] == "school"
    assert [e["kind"] for e in rec["events"]] == _kinds(vid)
    assert http.get("/api/cases/9999/record").status_code == 404


def test_choices_come_from_the_tools_own_taxonomy(http):
    ch = http.get("/api/choices").json()
    ids = {c["id"] for c in ch["causes"]}
    assert {"actuator_fail", "econ_fault", "documentation_wrong"} <= ids and "other" not in ids
    assert "box_mechanical" in ch["cause_groups"]


def test_intent_and_decision_over_http(http):
    vid = _visit()
    r = http.post(f"/api/visits/{vid}/decision", json=dict(action="follow"))
    assert r.status_code == 400
    r = http.post(f"/api/visits/{vid}/intent", json=dict(kind="unsure"))
    assert r.status_code == 200 and r.json()["step"]["stage"] == "revealed"
    r = http.post(f"/api/visits/{vid}/decision", json=dict(action="follow"))
    assert r.json()["step"]["stage"] == "in_progress"
    assert http.post(f"/api/visits/{vid}/answer", json=dict(word="banana")).status_code == 400
    assert http.post(f"/api/visits/{vid}/answer", json=dict(word=r.json()["step"]["words"][0], minutes_correction=-1)).status_code == 422
    assert http.post("/api/visits/nope/intent", json=dict(kind="unsure")).status_code == 404
