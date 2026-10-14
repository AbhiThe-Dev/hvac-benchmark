"""Guards for the pilot's hedge on low-static conclusions (pilot/engine_adapter.py hedge_for, pilot/visit.py, pilot/cases.py): a room whose leading cause is low duct static and that has no box-level
static reading of its own is shown as "explained by low static, own fault not ruled out" with its confidence capped, never as "diagnosed". It changes no check and no leading answer.
No test here reads a study result."""
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
os.environ.setdefault("PILOT_DATA_DIR", tempfile.mkdtemp(prefix="pilot_test_"))

import pytest  # noqa: E402

from pilot import cases as CS, config, db, engine_adapter as EA, visit as V  # noqa: E402
from pilot.case_schema import DecisionRequest, IntentRequest  # noqa: E402


def _building(n):
    eq = [{"id": "AHU-1", "kind": "AHU"}] + [{"id": f"VAV-{i}", "kind": "VAV"} for i in range(n)] + [{"id": f"Room-{i}", "kind": "Zone"} for i in range(n)]
    pts = {f"VAV-{i}": {"status": f"V{i}.STS", "airflow": f"V{i}.CFM", "damper": f"V{i}.D", "reheat": f"V{i}.R"} for i in range(n)}
    pts["AHU-1"] = {"fan_status": "A.SF", "static_pressure": "A.SP", "economizer_position": "A.E"}
    pts.update({f"Room-{i}": {"temperature": f"R{i}.T"} for i in range(n)})
    return {"equipment": eq, "claims": {"vav_zone": {f"Room-{i}": f"VAV-{i}" for i in range(n)}, "ahu_vav": {f"VAV-{i}": "AHU-1" for i in range(n)}}, "control_system": {"points": pts}}


@pytest.fixture(autouse=True)
def _fresh_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "pilot.db")
    monkeypatch.setattr(config, "VISITS_DIR", tmp_path / "visits")
    monkeypatch.delenv(EA.JOINT_MODEL_ENV, raising=False)
    db.init_db(config.DB_PATH)
    yield


def _session(tmp_path, *obs):
    p = tmp_path / "b.json"
    p.write_text(json.dumps(_building(3)))
    cases = EA.build_cases(EA.load_building(p), ["Room-0", "Room-1", "Room-2"])
    model = EA.build_joint_model(cases)
    sess = EA.start_room_session(cases[1], (model.causes[1], model.marg0[1]))
    d = cases[1].doc
    for check, outcome, minutes in obs:
        sess.log.append(EA.Obs(check, d, outcome, minutes))
    return sess


FAN_OK_STATIC_LOW = [("bas_ahu_fan", "normal", 2.0), ("bas_static", "abnormal", 2.0)]


def _top(sess):
    cause, belief = sess.status()["ranked"][0]
    return cause, belief


def test_hedge_applies_to_low_static_without_an_own_box_reading(tmp_path):
    sess = _session(tmp_path, *FAN_OK_STATIC_LOW)
    cause, belief = _top(sess)
    assert cause[0] == "low_static" and not EA.has_own_box_static(sess)
    h = EA.hedge_for(sess, cause, belief)
    assert h and h["hedged"] and "not ruled out" in h["note"]


def test_a_zero_minute_copy_of_another_rooms_reading_does_not_count_as_the_rooms_own(tmp_path):
    sess = _session(tmp_path, *FAN_OK_STATIC_LOW, ("static_at_box", "abnormal", 0.0))
    assert not EA.has_own_box_static(sess)
    cause, belief = _top(sess)
    assert EA.hedge_for(sess, cause, belief) is not None


def test_an_own_box_reading_removes_the_hedge_but_an_unsure_answer_does_not(tmp_path):
    own = _session(tmp_path, *FAN_OK_STATIC_LOW, ("static_at_box", "abnormal", 6.0))
    cause, belief = _top(own)
    assert EA.has_own_box_static(own) and EA.hedge_for(own, cause, belief) is None
    unsure = _session(tmp_path, *FAN_OK_STATIC_LOW, ("static_at_box", "unsure", 6.0))
    cause, belief = _top(unsure)
    assert not EA.has_own_box_static(unsure) and EA.hedge_for(unsure, cause, belief) is not None


def test_other_leading_causes_are_not_hedged(tmp_path):
    sess = _session(tmp_path, ("bas_ahu_fan", "abnormal", 2.0))
    cause, belief = _top(sess)
    assert cause[0] == "ahu_fan_off" and EA.hedge_for(sess, cause, belief) is None


def test_the_cap_never_lets_a_hedged_conclusion_show_more_than_the_cap(tmp_path):
    sess = _session(tmp_path, *FAN_OK_STATIC_LOW)
    cause, _ = _top(sess)
    high = EA.hedge_for(sess, cause, 0.99)
    assert high["belief"] == EA.HEDGE_CAP == 0.90 and high["raw_belief"] == 0.99 and EA.HEDGE_CAP < 0.95
    low = EA.hedge_for(sess, cause, 0.80)
    assert low["belief"] == 0.80 and low["raw_belief"] == 0.80          # below the cap nothing is changed


def test_the_suggested_check_is_at_the_room_never_at_the_air_handler(tmp_path):
    sess = _session(tmp_path, *FAN_OK_STATIC_LOW)
    cause, belief = _top(sess)
    h = EA.hedge_for(sess, cause, belief)
    assert h["rule_out"] is not None
    ck = next(c for c in EA.CHECKS if c.name == h["rule_out"]["check"])
    assert ck.subject != "ahu" and h["rule_out"]["minutes"] > 0


def test_the_hedge_changes_no_belief_log_or_clock(tmp_path):
    sess = _session(tmp_path, *FAN_OK_STATIC_LOW)
    cause, belief = _top(sess)
    before = (list(sess.log), sess.elapsed, sess.posterior()[1].copy())
    EA.hedge_for(sess, cause, belief)
    after = (list(sess.log), sess.elapsed, sess.posterior()[1])
    assert before[0] == after[0] and before[1] == after[1] and (before[2] == after[2]).all()


# ------------------------------------------------------------------------------------------------- through a whole visit
def _drive(vid, choose=None):
    """Fan normal, static abnormal, everything else normal; `choose` may substitute the first check of the visit. Returns the list of conclusion steps."""
    concl, first = [], True
    for _ in range(60):
        st = V.get_current_step(vid)
        if st["kind"] == "question":
            V.answer(vid, "yes")
        elif st["kind"] == "check":
            V.submit_intent(vid, IntentRequest(kind="unsure"))
            rev = V.get_current_step(vid)
            pick = choose(rev) if (choose and first) else None
            first = False
            if pick:
                V.submit_decision(vid, DecisionRequest(action="substitute", check=pick["name"], target=pick["target"]))
                word = "abnormal"
            else:
                V.submit_decision(vid, DecisionRequest(action="follow"))
                word = "abnormal" if rev["name"] == "bas_static" else ("normal" if rev["words"][0] == "abnormal" else "no")
            V.answer(vid, word)
        elif st["kind"] == "conclude":
            concl.append(st)
            if not st["has_next"]:
                return concl
            V.advance(vid)
    pytest.fail("visit never finished")


def test_a_hedged_conclusion_flows_through_the_visit_and_into_the_case_record(tmp_path):
    vid = V.create_visit(_building(3), ["Room-0", "Room-1", "Room-2"], feel="too_hot", airflow="yes")
    concl = _drive(vid)
    assert len(concl) == 3 and all(c["hedged"] for c in concl)
    assert all(c["belief"] <= EA.HEDGE_CAP and "not ruled out" in c["hedge_note"] and c["raw_belief"] is not None for c in concl)
    done = V.advance(vid)
    assert done["kind"] == "visit_done" and [c["hedged"] for c in done["conclusions"]] == [True, True, True]
    assert V.get_current_step(vid) == done                                       # reopening gives the same answer
    with db.connect(config.DB_PATH) as conn:
        case = db.get_case_for_room(conn, vid, 0)
        tc = CS.last_event(db.get_events(conn, case["id"]), "tool_conclusion")
    assert tc["payload"]["hedged"] is True and tc["payload"]["raw_belief"] >= tc["payload"]["belief"] and "hedge_rule_out" in tc["payload"]


def test_a_room_that_takes_its_own_box_reading_is_not_hedged_while_the_others_still_are(tmp_path):
    vid = V.create_visit(_building(3), ["Room-0", "Room-1", "Room-2"], feel="too_hot", airflow="yes")
    concl = _drive(vid, choose=lambda rev: next(p for p in rev["picker"] if p["name"] == "static_at_box"))
    assert [c["hedged"] for c in concl] == [False, True, True]
    assert concl[0]["raw_belief"] is None and concl[0]["hedge_note"] is None
    done = V.advance(vid)
    assert [c["hedged"] for c in done["conclusions"]] == [False, True, True]
    with db.connect(config.DB_PATH) as conn:
        tc = CS.last_event(db.get_events(conn, db.get_case_for_room(conn, vid, 0)["id"]), "tool_conclusion")
    assert "hedged" not in tc["payload"]
