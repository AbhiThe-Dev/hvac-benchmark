"""The verification ladder (pilot/ladder.py). The rule under test: a rung is NEVER granted on inference. Evidence has to be
stated -- and the things that look like confirmation but are not (the repair working, ruling out the others, hearsay, a
measurement with no statement about when) must not move the label up."""
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
os.environ.setdefault("PILOT_DATA_DIR", tempfile.mkdtemp(prefix="pilot_ladder_test_"))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from pilot import auth, cases as CS, config, db, visit as V  # noqa: E402
from pilot.app import app  # noqa: E402
from pilot.ladder import verification  # noqa: E402
from pilot.scripts import export_cases  # noqa: E402


# ------------------------------------------------------------------------------------------------- the pure function

def ev(kind, **payload):
    return dict(kind=kind, payload=payload, server_ts="2026-10-01T09:00:00+00:00")


def rc(cause="actuator_fail", how="measured", before=True):
    return ev("root_cause", cause_id=cause, how_confirmed=how, confirmed_before_repair=before)


def rp(*actions, text=None):
    return ev("repair", actions=list(actions), text=text)


def oc(fixed):
    return ev("outcome", fixed=fixed)


def fu(window, recurred):
    return ev("followup", window_days=window, recurred=recurred)


def rungs(events):
    return tuple(verification(events)["rungs"].values())


def test_nothing_recorded_is_level_zero():
    v = verification([])
    assert v["level"] == 0 and v["name"] == "no cause named" and rungs([]) == (False, False, False, False) and v["caveats"] == []
    assert [l["done"] for l in v["lines"]] == [False] * 4 and v["lines"][0]["text"] == "No cause named yet"


def test_a_named_cause_alone_is_suspected():
    v = verification([rc(how="not_confirmed", before=None)])
    assert v["level"] == 1 and v["rungs"]["suspected"] and not v["rungs"]["physically_confirmed"]


def test_seen_or_measured_before_the_repair_is_physically_confirmed():
    for how in ("observed_directly", "measured"):
        v = verification([rc(how=how, before=True)])
        assert v["level"] == 2 and v["rungs"]["physically_confirmed"], how
    assert "before the repair" in verification([rc(how="measured", before=True)])["lines"][1]["text"]


@pytest.mark.parametrize("how,before,expected_caveat", [
    ("measured", None, "pre_repair_unknown"),                   # measured, but never said when: not granted on inference
    ("observed_directly", None, "pre_repair_unknown"),
    ("measured", False, "physical_confirmation_after_repair"),
    ("repair_fixed_it", False, None),                           # the repair working is a repair result, not a pre-repair confirmation
    ("ruled_out_others", None, None),                           # inference by elimination is not physical
    ("other_tech_or_vendor", None, None),                       # hearsay is not physical
    ("not_confirmed", None, None),
    (None, None, None),
])
def test_only_a_stated_pre_repair_physical_confirmation_counts(how, before, expected_caveat):
    v = verification([rc(how=how, before=before)])
    assert not v["rungs"]["physically_confirmed"] and v["level"] == 1, "suspected, and no more"
    assert (expected_caveat in v["caveats"]) if expected_caveat else not v["caveats"]


def test_the_two_wordings_for_a_missing_before_statement_are_different():
    unknown = verification([rc(how="measured", before=None)])["lines"][1]["text"]
    after = verification([rc(how="measured", before=False)])["lines"][1]["text"]
    assert "not whether that was before the repair" in unknown and "only after the repair" in after


def test_not_determined_names_no_cause_even_with_a_repair_and_a_fix():
    v = verification([rc(cause="not_determined", how="not_confirmed", before=None), rp("replaced_part"), oc("yes")])
    assert v["level"] == 0 and not any(v["rungs"].values())
    assert "fixed_without_named_cause" in v["caveats"] and v["lines"][0]["text"] == "You couldn't determine the cause"


def test_a_real_repair_that_worked_is_repair_confirmed_with_or_without_physical_confirmation():
    full = verification([rc(), rp("replaced_part"), oc("yes")])
    assert full["level"] == 3 and rungs([rc(), rp("replaced_part"), oc("yes")]) == (True, True, True, False)
    guessed = verification([rc(how="not_confirmed", before=None), rp("replaced_part"), oc("yes")])
    assert guessed["level"] == 3 and guessed["rungs"]["physically_confirmed"] is False, "suspected, replaced it, it worked: repair-confirmed, never physical"


@pytest.mark.parametrize("fixed,caveat", [("no", "repair_did_not_fix"), ("partial", "repair_partly_fixed"), ("unknown", "outcome_unknown")])
def test_a_repair_that_did_not_clearly_work_is_not_repair_confirmed(fixed, caveat):
    v = verification([rc(), rp("replaced_part"), oc(fixed)])
    assert not v["rungs"]["repair_confirmed"] and v["level"] == 2 and caveat in v["caveats"]


def test_no_outcome_yet_is_not_a_failure_and_says_so():
    v = verification([rc(), rp("replaced_part")])
    assert not v["rungs"]["repair_confirmed"] and v["caveats"] == [] and v["lines"][2]["text"] == "Not yet recorded whether it worked"


@pytest.mark.parametrize("actions", [("no_repair_needed",), ("deferred_or_referred",), ("no_repair_needed", "deferred_or_referred")])
def test_recording_that_nothing_was_repaired_cannot_confirm_a_repair(actions):
    v = verification([rc(), rp(*actions), oc("yes")])
    assert not v["rungs"]["repair_confirmed"] and {"no_repair_made", "fixed_without_repair"} <= set(v["caveats"])


def test_a_fix_with_no_repair_event_at_all_is_flagged_not_credited():
    v = verification([rc(), oc("yes")])
    assert not v["rungs"]["repair_confirmed"] and "fixed_without_repair" in v["caveats"]
    assert v["lines"][2]["text"] == "Fixed, but no repair was recorded"


def test_a_repair_described_only_in_text_counts_but_is_flagged():
    v = verification([rc(), rp(text="reseated the connector"), oc("yes")])
    assert v["rungs"]["repair_confirmed"] and "repair_text_only" in v["caveats"]


def test_a_multi_part_repair_still_counts_but_cannot_be_pinned_to_one_cause():
    v = verification([rc(), rp("replaced_part", "reconfigured_controls"), oc("yes")])
    assert v["rungs"]["repair_confirmed"] and "multi_action_repair" in v["caveats"]
    assert "multi_action_repair" not in verification([rc(), rp("replaced_part", "no_repair_needed"), oc("yes")])["caveats"], "a non-fix is not a second repair"


def test_stayed_fixed_needs_a_confirmed_fix_and_a_clean_follow_up():
    base = [rc(), rp("replaced_part"), oc("yes")]
    assert verification(base + [fu(7, "no")])["stayed_fixed_days"] == 7 and verification(base + [fu(7, "no")])["level"] == 4
    both = verification(base + [fu(7, "no"), fu(30, "no")])
    assert both["stayed_fixed_days"] == 30 and both["level"] == 4 and all(both["rungs"].values())
    assert verification(base + [fu(7, "unsure")])["level"] == 3, "'not sure' proves nothing either way"
    assert verification([rc(), rp("replaced_part"), oc("partial"), fu(7, "no")])["level"] == 2, "follow-ups on a fix that was only partial do not count"
    assert verification([rc(), fu(7, "no")])["rungs"]["stayed_fixed"] is False, "no recorded fix, nothing to have stayed"


def test_a_recurrence_anywhere_defeats_stayed_fixed_and_is_named():
    base = [rc(), rp("replaced_part"), oc("yes")]
    v = verification(base + [fu(7, "no"), fu(30, "yes")])
    assert not v["rungs"]["stayed_fixed"] and v["level"] == 3 and "recurred_within_30_days" in v["caveats"]
    assert verification(base + [fu(7, "yes")])["lines"][3]["text"] == "It came back within 7 days"


def test_the_latest_answer_wins_and_a_revised_cause_is_flagged():
    v = verification([rc(cause="actuator_fail"), rc(cause="damper_mech", how="observed_directly", before=True)])
    assert v["level"] == 2 and "cause_revised" in v["caveats"]
    assert "cause_revised" not in verification([rc(how="not_confirmed", before=None), rc(how="measured", before=True)])["caveats"], "same cause, better evidence: not a revision"
    assert verification([rp("replaced_part"), oc("partial"), oc("yes"), rc()])["rungs"]["repair_confirmed"], "a later 'yes' replaces an earlier 'partly'"


def test_the_ladder_text_is_what_the_record_shows_not_a_score():
    lines = verification([rc(), rp("replaced_part"), oc("yes"), fu(7, "no")])["lines"]
    assert [l["rung"] for l in lines] == ["suspected", "physically_confirmed", "repair_confirmed", "stayed_fixed"]
    assert lines[3]["text"] == "Still fixed at 7 days (the 30-day check is still to come)"
    assert lines[2]["text"] == "The repair fixed it" and lines[1]["text"] == "Confirmed by measuring it before the repair"


def test_the_function_reads_only_events_and_never_needs_the_server():
    code = ("import sys; sys.path.insert(0, %r); from pilot.ladder import verification; "
            "assert 'pilot.config' not in sys.modules and 'pilot.engine_adapter' not in sys.modules; print('ok')" % str(ROOT))
    import subprocess
    env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "NOTIFY_EMAIL", "SMTP_FROM_EMAIL", "SMTP_APP_PASSWORD", "PILOT_DATA_DIR")}
    r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, cwd=str(ROOT))
    assert r.returncode == 0 and r.stdout.strip() == "ok", r.stderr


# ------------------------------------------------------------------------------------------------- recording the new answer

BUILDING = {
    "equipment": [{"id": "AHU-1", "kind": "AHU"}, {"id": "VAV-1", "kind": "VAV"}, {"id": "Room-X", "kind": "Zone"}],
    "claims": {"vav_zone": {"Room-X": "VAV-1"}, "ahu_vav": {"VAV-1": "AHU-1"}},
    "control_system": {"points": {"VAV-1": {"status": "V1.STS"}, "AHU-1": {"fan_status": "A1.SF"}, "Room-X": {"temperature": "R1.T"}}},
}


@pytest.fixture(autouse=True)
def _fresh(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "pilot.db")
    monkeypatch.setattr(config, "VISITS_DIR", tmp_path / "visits")
    db.init_db(config.DB_PATH)


def _case():
    vid = V.create_visit(BUILDING, ["Room-X"], feel="too_hot", airflow="yes", context=dict(complaint_text="hot"))
    with db.connect(config.DB_PATH) as conn:
        return vid, db.get_case_for_room(conn, vid, 0)["id"]


def _root_cause(cid, **kw):
    with db.connect(config.DB_PATH) as conn:
        CS.record_root_cause(conn, cid, cause_id=kw.pop("cause_id", "actuator_fail"), text=None, client_ts=None, **kw)
        return db.get_events(conn, cid)[-1]["payload"]


def test_before_repair_is_kept_for_physical_methods_and_forced_or_refused_elsewhere():
    _, cid = _case()
    assert _root_cause(cid, how_confirmed="measured", confirmed_before_repair=True)["confirmed_before_repair"] is True
    assert _root_cause(cid, how_confirmed="observed_directly", confirmed_before_repair=False)["confirmed_before_repair"] is False
    assert _root_cause(cid, how_confirmed="measured")["confirmed_before_repair"] is None, "unanswered stays unanswered"
    assert _root_cause(cid, how_confirmed="repair_fixed_it")["confirmed_before_repair"] is False, "the repair working is after the repair by definition"
    for how in ("ruled_out_others", "other_tech_or_vendor", "not_confirmed", None):
        assert _root_cause(cid, how_confirmed=how)["confirmed_before_repair"] is None, how


@pytest.mark.parametrize("how", ["repair_fixed_it", "ruled_out_others", "other_tech_or_vendor", "not_confirmed", None])
def test_claiming_a_pre_repair_confirmation_the_method_cannot_support_is_refused_and_writes_nothing(how):
    _, cid = _case()
    with pytest.raises(ValueError):
        _root_cause(cid, how_confirmed=how, confirmed_before_repair=True)
    with db.connect(config.DB_PATH) as conn:
        assert [e for e in db.get_events(conn, cid) if e["kind"] == "root_cause"] == []


@pytest.fixture
def http():
    app.dependency_overrides[auth.require_token] = lambda: "test-token"
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_the_record_view_carries_the_ladder_and_it_climbs_as_the_technician_fills_things_in(http):
    _, cid = _case()
    ladder = lambda: http.get(f"/api/cases/{cid}/record").json()["ladder"]       # noqa: E731
    assert ladder()["level"] == 0
    assert http.post(f"/api/cases/{cid}/root_cause", json=dict(cause_id="actuator_fail", how_confirmed="measured")).status_code == 200
    assert ladder()["level"] == 1 and "pre_repair_unknown" in ladder()["caveats"]
    http.post(f"/api/cases/{cid}/root_cause", json=dict(cause_id="actuator_fail", how_confirmed="measured", confirmed_before_repair=True))
    assert ladder()["level"] == 2
    http.post(f"/api/cases/{cid}/repair", json=dict(actions=["replaced_part"]))
    http.post(f"/api/cases/{cid}/outcome", json=dict(fixed="yes"))
    assert ladder()["level"] == 3
    http.post(f"/api/cases/{cid}/followup", json=dict(window_days=7, recurred="no"))
    assert ladder()["level"] == 4 and ladder()["stayed_fixed_days"] == 7
    assert [l["done"] for l in ladder()["lines"]] == [True] * 4


def test_the_api_rejects_a_non_boolean_and_a_contradiction(http):
    _, cid = _case()
    assert http.post(f"/api/cases/{cid}/root_cause", json=dict(cause_id="actuator_fail", how_confirmed="measured", confirmed_before_repair="maybe")).status_code == 422
    assert http.post(f"/api/cases/{cid}/root_cause", json=dict(cause_id="actuator_fail", how_confirmed="not_confirmed", confirmed_before_repair=True)).status_code == 400


# ------------------------------------------------------------------------------------------------- the export

def _export(tmp_path):
    out = tmp_path / "export"
    stats = export_cases.export(tmp_path, out)
    recs = [json.loads(line) for line in (out / "cases.jsonl").read_text().splitlines()]
    rows = list(csv.DictReader((out / "cases.csv").open()))
    return stats, recs, rows, out


def _participant():
    with db.connect(config.DB_PATH) as conn:
        return db.create_participant(conn, role="contractor_tech", years_band="2to5", vav_band="some")


def test_export_carries_the_ladder_per_case_and_a_cases_table(tmp_path):
    _participant()
    _, solid = _case()
    _, guessed = _case()
    _, bare = _case()
    with db.connect(config.DB_PATH) as conn:
        CS.record_root_cause(conn, solid, cause_id="actuator_fail", text=None, how_confirmed="measured", confirmed_before_repair=True, client_ts=None)
        CS.record_repair(conn, solid, actions=["replaced_part"], text=None, repaired_on=None, client_ts=None)
        CS.record_outcome(conn, solid, fixed="yes", note=None, client_ts=None)
        CS.record_root_cause(conn, guessed, cause_id="damper_mech", text=None, how_confirmed="measured", client_ts=None)       # never said when
        CS.record_repair(conn, guessed, actions=["replaced_part", "adjusted_or_reset"], text=None, repaired_on=None, client_ts=None)
        CS.record_outcome(conn, guessed, fixed="yes", note=None, client_ts=None)
    stats, recs, rows, out = _export(tmp_path)
    by_id = {r["case_id"]: r for r in recs}
    assert by_id[solid]["verification"]["level"] == 3 and by_id[solid]["verification"]["rungs"]["physically_confirmed"] is True
    assert "lines" not in by_id[solid]["verification"], "the technician's sentences are not part of the dataset"
    g = by_id[guessed]["verification"]
    assert g["level"] == 3 and g["rungs"]["physically_confirmed"] is False and {"pre_repair_unknown", "multi_action_repair"} <= set(g["caveats"])
    assert by_id[bare]["verification"]["level"] == 0
    table = {int(r["case_id"]): r for r in rows}
    assert table[solid]["ladder_level"] == "3" and table[solid]["physically_confirmed"] == "True" and table[solid]["caveats"] == ""
    assert table[guessed]["caveats"] == "pre_repair_unknown;multi_action_repair" and table[guessed]["physically_confirmed"] == "False"
    assert table[solid]["root_cause"] == "actuator_fail" and table[solid]["confirmed_before_repair"] == "True" and table[solid]["role"] == "contractor_tech"
    summary = (out / "SUMMARY.txt").read_text()
    assert "no cause named 1, suspected 0, physically confirmed before repair 0, repair confirmed 2, stayed fixed 0" in summary


def test_a_case_recorded_before_the_ladder_existed_exports_without_error(tmp_path):
    """Old root_cause events have no confirmed_before_repair at all. They must read as 'not stated', never as 'before'."""
    _participant()
    _, cid = _case()
    with db.connect(config.DB_PATH) as conn:
        db.append_event(conn, cid, "root_cause", dict(cause_id="actuator_fail", text=None, in_taxonomy=True, how_confirmed="measured",
                                                      tool_cause_id=None, agrees_with_tool=None))
    _, recs, rows, _ = _export(tmp_path)
    v = recs[0]["verification"]
    assert v["level"] == 1 and "pre_repair_unknown" in v["caveats"] and rows[0]["confirmed_before_repair"] == ""
