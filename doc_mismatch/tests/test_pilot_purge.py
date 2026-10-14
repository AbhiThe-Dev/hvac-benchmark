"""scripts/purge.py: deleting a visit's case record or a participant's whole record. The things that must hold: a dry run
changes nothing; a purge removes everything of the target and nothing of anyone else; deleted text is not recoverable
from the database file; the append-only triggers come back; a failure rolls everything back; the audit row has counts
and no content."""
import json
import os
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]           # doc_mismatch/
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test-not-real")
os.environ.setdefault("NOTIFY_EMAIL", "dev@example.com")
os.environ.setdefault("SMTP_FROM_EMAIL", "dev@example.com")
os.environ.setdefault("SMTP_APP_PASSWORD", "not-a-real-app-password")
os.environ.setdefault("PILOT_DATA_DIR", tempfile.mkdtemp(prefix="pilot_purge_test_"))

import pytest  # noqa: E402

from pilot import cases as CS, config, db, visit as V  # noqa: E402
from pilot.case_schema import DecisionRequest, IntentRequest  # noqa: E402
from pilot.scripts import backup, purge  # noqa: E402
from _pilot_flow import run_check  # noqa: E402

GONE_ROOM, GONE_TEXT = "Suite 210 Kowalski Dental", "ZEBRAQUARTZ-complaint"
KEPT_ROOM, KEPT_TEXT = "Room B-12 Larsen", "KEEPME-complaint"


def building(room):
    return {"equipment": [{"id": "AHU-1", "kind": "AHU"}, {"id": "VAV-1", "kind": "VAV"}, {"id": room, "kind": "Zone"}],
            "claims": {"vav_zone": {room: "VAV-1"}, "ahu_vav": {"VAV-1": "AHU-1"}},
            "control_system": {"points": {"VAV-1": {"status": "V1.STS"}, "AHU-1": {"fan_status": "A1.SF"}, room: {"temperature": "R1.T"}}}}


@pytest.fixture(autouse=True)
def _fresh(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "pilot.db")
    monkeypatch.setattr(config, "VISITS_DIR", tmp_path / "visits")
    db.init_db(config.DB_PATH)


def _participant(role="contractor_tech"):
    with db.connect(config.DB_PATH) as conn:
        return db.create_participant(conn, role=role, years_band="2to5", vav_band="some")


def _intake(tmp_path, visit_id):
    iid = "intake" + visit_id[:6]
    folder = tmp_path / "uploads" / iid
    folder.mkdir(parents=True)
    (folder / "bas.jpg").write_bytes(b"jpegbytes")
    with db.connect(config.DB_PATH) as conn:
        db.create_intake(conn, iid, '{"raw": "VISIONRAW-%s"}' % visit_id, "{}", str(folder / "bas.jpg"), str(folder / "equipment.jpg"))
        db.confirm_intake(conn, iid, "{}", visit_id)
    return iid


def _visit(tmp_path, room, text, *, finish=True):
    """One visit with a check done, a close-out and follow-ups, an intake with a photo on disk."""
    vid = V.create_visit(building(room), [room], feel="too_hot", airflow="yes", context=dict(complaint_text=text))
    V.submit_intent(vid, IntentRequest(kind="other", text=f"look at {text}"))
    V.submit_decision(vid, DecisionRequest(action="external", external_text=f"{text} trend"))
    V.answer(vid, result_text=f"found {text}")
    for _ in range(40):
        step = V.get_current_step(vid)
        if step["kind"] == "conclude":
            break
        if step["kind"] == "question":
            V.answer(vid, "no")
        elif step["stage"] == "revealed":            # the off-list check above leaves the suggestion shown
            V.answer(vid, V.submit_decision(vid, DecisionRequest(action="follow"))["words"][0])
        else:
            run_check(V, vid)
    with db.connect(config.DB_PATH) as conn:
        cid = db.get_case_for_room(conn, vid, 0)["id"]
        CS.record_root_cause(conn, cid, cause_id="other", text=f"{text} cause", how_confirmed="measured", client_ts=None)
        CS.record_repair(conn, cid, actions=["replaced_part"], text=None, repaired_on=None, client_ts=None)
        CS.record_outcome(conn, cid, fixed="yes", note=None, client_ts=None)
    if finish:
        V.advance(vid)
    return vid, cid, _intake(tmp_path, vid)


@pytest.fixture
def world(tmp_path):
    """Participant A (to be purged) with two visits, then participant B with one. B's case names A's first case as the earlier visit."""
    pa = _participant()
    a1 = _visit(tmp_path, GONE_ROOM, GONE_TEXT)
    a2 = _visit(tmp_path, GONE_ROOM + " annex", GONE_TEXT + "-2")
    pb = _participant("in_house_engineer")
    b1 = _visit(tmp_path, KEPT_ROOM, KEPT_TEXT)
    with db.connect(config.DB_PATH) as conn:
        conn.execute("UPDATE cases SET prior_case_id = ? WHERE id = ?", (a1[1], b1[1]))
    return dict(pa=pa, pb=pb, a1=a1, a2=a2, b1=b1, dir=tmp_path)


def _rows(sql, *params):
    with db.connect(config.DB_PATH) as conn:
        return [tuple(r) for r in conn.execute(sql, params)]


def _db_bytes(tmp_path):
    return b"".join(p.read_bytes() for p in (tmp_path / "pilot.db", tmp_path / "pilot.db-wal") if p.exists())


def run(world, *args):
    return purge.main(["--data-dir", str(world["dir"]), *args])


# ------------------------------------------------------------------------------------------------- dry run and guards

def test_a_dry_run_changes_nothing_and_says_so(world, capsys):
    before = _db_bytes(world["dir"])
    assert run(world, "participant", str(world["pa"])) == 0
    out = capsys.readouterr().out
    assert "dry run" in out and "--execute" in out and "visits 2" in out and "cases 2" in out and "NOT removed" in out
    assert _db_bytes(world["dir"]) == before
    assert (world["dir"] / "visits" / world["a1"][0]).exists() and (world["dir"] / "uploads" / world["a1"][2]).exists()


def test_execute_needs_a_reason_and_unknown_targets_do_nothing(world, capsys):
    before = _db_bytes(world["dir"])
    assert run(world, "case", str(world["a1"][1]), "--execute") == 2
    assert run(world, "case", "9999", "--reason", "test_data", "--execute") == 1
    assert run(world, "participant", "9999", "--reason", "test_data", "--execute") == 1
    assert "no case 9999" in capsys.readouterr().out
    assert _db_bytes(world["dir"]) == before
    with pytest.raises(SystemExit):
        run(world, "case", "1", "--reason", "a free text name", "--execute")          # reasons are a fixed list


def test_it_does_not_need_the_servers_secrets():
    code = ("import sys; sys.path.insert(0, %r); from pilot.scripts import purge; "
            "assert 'pilot.config' not in sys.modules; print('ok')" % str(ROOT))
    env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "NOTIFY_EMAIL", "SMTP_FROM_EMAIL", "SMTP_APP_PASSWORD", "PILOT_DATA_DIR")}
    r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, cwd=str(ROOT))
    assert r.returncode == 0 and r.stdout.strip() == "ok", r.stderr


def test_list_shows_participants_cases_and_orphan_intakes(world, capsys):
    assert run(world, "list") == 0
    out = capsys.readouterr().out
    assert "PARTICIPANTS" in out and "contractor_tech" in out and "in_house_engineer" in out and GONE_ROOM in out and "UNCONFIRMED INTAKES" in out


# ------------------------------------------------------------------------------------------------- purging a visit

def test_purging_a_case_removes_its_whole_visit_and_nothing_else(world):
    a1, a2, b1 = world["a1"], world["a2"], world["b1"]
    assert run(world, "case", str(a1[1]), "--reason", "data_error", "--execute") == 0
    for table, col, val in (("cases", "id", a1[1]), ("visits", "id", a1[0]), ("room_log", "visit_id", a1[0]), ("room_conclusion", "visit_id", a1[0]),
                            ("intake", "id", a1[2]), ("case_event", "case_id", a1[1]), ("followup_due", "case_id", a1[1])):
        assert _rows(f"SELECT 1 FROM {table} WHERE {col} = ?", val) == [], table
    assert not (world["dir"] / "visits" / a1[0]).exists() and not (world["dir"] / "uploads" / a1[2]).exists()
    # the other visit of the same participant, and the other participant, are untouched and still work
    for vid, cid, iid in (a2, b1):
        assert _rows("SELECT COUNT(*) FROM case_event WHERE case_id = ?", cid)[0][0] > 5
        assert (world["dir"] / "visits" / vid).exists() and (world["dir"] / "uploads" / iid).exists()
        assert V.get_current_step(vid)["kind"] == "visit_done"
    assert _rows("SELECT COUNT(*) FROM participants")[0][0] == 2, "purging a case does not remove the participant"
    with pytest.raises(KeyError):
        V.get_current_step(a1[0])


def test_purging_a_participant_removes_all_of_theirs_and_their_record(world):
    a1, a2, b1 = world["a1"], world["a2"], world["b1"]
    assert run(world, "participant", str(world["pa"]), "--reason", "withdrawal_request", "--execute") == 0
    assert _rows("SELECT id FROM participants") == [(world["pb"],)]
    assert _rows("SELECT id FROM cases") == [(b1[1],)]
    assert {r[0] for r in _rows("SELECT id FROM visits")} == {b1[0]}
    assert {r[0] for r in _rows("SELECT id FROM intake")} == {b1[2]}
    assert _rows("SELECT COUNT(*) FROM case_event WHERE case_id IN (?, ?)", a1[1], a2[1])[0][0] == 0
    for gone in (a1, a2):
        assert not (world["dir"] / "visits" / gone[0]).exists() and not (world["dir"] / "uploads" / gone[2]).exists()
    assert V.get_current_step(b1[0])["kind"] == "visit_done"


def test_a_link_from_someone_elses_case_to_a_purged_one_is_cleared_not_followed(world, capsys):
    b1 = world["b1"]
    assert _rows("SELECT prior_case_id FROM cases WHERE id = ?", b1[1]) == [(world["a1"][1],)]
    run(world, "case", str(world["a1"][1]))
    assert "link will be cleared" in capsys.readouterr().out
    run(world, "case", str(world["a1"][1]), "--reason", "data_error", "--execute")
    assert _rows("SELECT prior_case_id FROM cases WHERE id = ?", b1[1]) == [(None,)]


def test_a_visit_still_in_progress_can_be_purged_with_a_warning(world, capsys):
    vid, cid, _ = _visit(world["dir"], "Room C-3 Open", "OPEN-complaint", finish=False)
    run(world, "case", str(cid))
    assert "not finished" in capsys.readouterr().out
    assert run(world, "case", str(cid), "--reason", "test_data", "--execute") == 0
    assert _rows("SELECT 1 FROM visits WHERE id = ?", vid) == []


def test_a_visit_holding_another_participants_case_is_refused_not_split(world, capsys):
    two = building("Room M-1")
    two["equipment"] += [{"id": "VAV-2", "kind": "VAV"}, {"id": "Room M-2", "kind": "Zone"}]
    two["claims"] = {"vav_zone": {"Room M-1": "VAV-1", "Room M-2": "VAV-2"}, "ahu_vav": {"VAV-1": "AHU-1", "VAV-2": "AHU-1"}}
    with db.connect(config.DB_PATH) as conn:
        conn.execute("UPDATE participants SET active = 0")
        conn.execute("UPDATE participants SET active = 1 WHERE id = ?", (world["pa"],))
    vid = V.create_visit(two, ["Room M-1", "Room M-2"], feel="too_hot", airflow="yes")
    with db.connect(config.DB_PATH) as conn:
        conn.execute("UPDATE cases SET participant_id = ? WHERE visit_id = ? AND room_index = 1", (world["pb"], vid))
    before = _db_bytes(world["dir"])
    assert run(world, "participant", str(world["pa"]), "--reason", "test_data", "--execute") == 1
    assert "cannot be split" in capsys.readouterr().out and _db_bytes(world["dir"]) == before
    assert _rows("SELECT COUNT(*) FROM participants")[0][0] == 2


# ------------------------------------------------------------------------------------------------- it is real deletion

def test_deleted_text_cannot_be_recovered_from_the_database_file(world):
    raw = _db_bytes(world["dir"])
    for planted in (GONE_ROOM, GONE_TEXT, "Kowalski"):
        assert planted.encode() in raw, f"{planted!r} should be in the database before the purge (else this test proves nothing)"
    assert KEPT_TEXT.encode() in raw
    run(world, "participant", str(world["pa"]), "--reason", "withdrawal_request", "--execute")
    raw = _db_bytes(world["dir"])
    gone_vision = [f"VISIONRAW-{world[k][0]}" for k in ("a1", "a2")]
    for planted in (GONE_ROOM, GONE_TEXT, "Kowalski", GONE_TEXT + "-2", *gone_vision):
        assert planted.encode() not in raw, f"{planted!r} is still in the database file or its write-ahead log"
    assert KEPT_TEXT.encode() in raw and KEPT_ROOM.encode() in raw, "the other participant's data must survive"
    assert f"VISIONRAW-{world['b1'][0]}".encode() in raw


def test_the_append_only_triggers_are_back_and_still_enforced(world):
    names_before = {r[0] for r in _rows("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='case_event'")}
    assert names_before == {"case_event_no_update", "case_event_no_delete"}
    run(world, "case", str(world["a1"][1]), "--reason", "data_error", "--execute")
    assert {r[0] for r in _rows("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='case_event'")} == names_before
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        with db.connect(config.DB_PATH) as conn:
            conn.execute("DELETE FROM case_event")
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        with db.connect(config.DB_PATH) as conn:
            conn.execute("UPDATE case_event SET kind = 'x'")
    # and the app can keep writing events for the survivors
    with db.connect(config.DB_PATH) as conn:
        db.append_event(conn, world["b1"][1], "correction", {"corrects_event_id": 1})


def test_a_failure_part_way_rolls_everything_back_including_the_triggers(world):
    with db.connect(config.DB_PATH) as conn:
        conn.execute("CREATE TRIGGER boom BEFORE INSERT ON purge_log BEGIN SELECT RAISE(ABORT, 'boom'); END")
    tables = ("cases", "case_event", "visits", "room_log", "room_conclusion", "intake", "participants", "followup_due")
    before = {t: _rows(f"SELECT COUNT(*) FROM {t}")[0][0] for t in tables}
    with pytest.raises(sqlite3.DatabaseError, match="boom"):
        run(world, "participant", str(world["pa"]), "--reason", "test_data", "--execute")
    assert {t: _rows(f"SELECT COUNT(*) FROM {t}")[0][0] for t in tables} == before
    assert {r[0] for r in _rows("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='case_event'")} == {"case_event_no_update", "case_event_no_delete"}
    assert (world["dir"] / "visits" / world["a1"][0]).exists(), "files are only removed after the database commit"
    assert _rows("SELECT COUNT(*) FROM purge_log")[0][0] == 0


# ------------------------------------------------------------------------------------------------- audit and the rest

def test_the_audit_row_records_that_it_happened_with_counts_and_no_content(world):
    run(world, "participant", str(world["pa"]), "--reason", "withdrawal_request", "--execute")
    (scope, target, reason, counts_json), = _rows("SELECT scope, target_id, reason, counts_json FROM purge_log")
    assert (scope, target, reason) == ("participant", world["pa"], "withdrawal_request")
    counts = json.loads(counts_json)
    assert counts["visits"] == 2 and counts["cases"] == 2 and counts["case_events"] > 10 and counts["intakes"] == 2 and counts["participants"] == 1
    blob = " ".join(str(c) for row in _rows("SELECT * FROM purge_log") for c in row)
    for planted in (GONE_ROOM, GONE_TEXT, "Kowalski"):
        assert planted not in blob


def _orphans(world):
    """An unconfirmed intake inside participant A's window (made as A began) and one inside B's (made as B began)."""
    folders = {}
    for name in ("orphan-in-a", "orphan-in-b"):
        folders[name] = world["dir"] / "uploads" / name
        folders[name].mkdir(parents=True)
        (folders[name] / "bas.jpg").write_bytes(b"x")
    with db.connect(config.DB_PATH) as conn:
        starts = {pid: conn.execute("SELECT created_at FROM participants WHERE id = ?", (pid,)).fetchone()[0] for pid in (world["pa"], world["pb"])}
        for name, pid in (("orphan-in-a", world["pa"]), ("orphan-in-b", world["pb"])):
            db.create_intake(conn, name, "{}", "{}", "p", "p")
            conn.execute("UPDATE intake SET created_at = ? WHERE id = ?", (starts[pid], name))
    return folders


def test_unconfirmed_intakes_are_kept_unless_asked_and_the_plan_says_so(world, capsys):
    folders = _orphans(world)
    run(world, "participant", str(world["pa"]))
    out = capsys.readouterr().out
    assert "1 unconfirmed intake" in out and "KEPT" in out
    run(world, "participant", str(world["pa"]), "--reason", "withdrawal_request", "--execute")
    assert {r[0] for r in _rows("SELECT id FROM intake WHERE visit_id IS NULL")} == {"orphan-in-a", "orphan-in-b"}
    assert all(f.exists() for f in folders.values())


def test_orphan_intakes_flag_deletes_only_those_in_the_participants_own_window(world):
    folders = _orphans(world)
    run(world, "participant", str(world["pa"]), "--orphan-intakes", "--reason", "withdrawal_request", "--execute")
    assert {r[0] for r in _rows("SELECT id FROM intake WHERE visit_id IS NULL")} == {"orphan-in-b"}
    assert not folders["orphan-in-a"].exists() and folders["orphan-in-b"].exists(), "B's unconfirmed intake is not A's to delete"


def test_backups_are_opened_and_only_those_holding_the_data_are_named(world, capsys, tmp_path):
    backups = tmp_path / "bk"
    holds = backup.make_backup(world["dir"], backups, now=__import__("datetime").datetime(2026, 10, 1, tzinfo=__import__("datetime").timezone.utc))
    run(world, "case", str(world["a1"][1]), "--reason", "data_error", "--execute", "--backups", str(backups))
    after = backup.make_backup(world["dir"], backups, now=__import__("datetime").datetime(2026, 10, 2, tzinfo=__import__("datetime").timezone.utc))
    (backups / "pilot-backup-20261003T000000Z.tar.gz").write_bytes(b"corrupt")
    capsys.readouterr()
    run(world, "case", str(world["a2"][1]), "--backups", str(backups))          # dry run on a case that is in the first backup and the second
    out = capsys.readouterr().out
    assert f"HOLDS  {holds.name}" in out and f"HOLDS  {after.name}" in out
    assert "?      pilot-backup-20261003T000000Z.tar.gz" in out and "could not be read" in out
    run(world, "case", str(world["a1"][1]), "--backups", str(backups))          # already purged: (error: no such case) must not crash
    assert holds.exists() and after.exists(), "the script lists old backups; it never touches them"


def test_a_backup_made_after_the_purge_is_not_said_to_hold_it(world, capsys, tmp_path):
    backups = tmp_path / "bk"
    run(world, "case", str(world["a1"][1]), "--reason", "data_error", "--execute")
    clean = backup.make_backup(world["dir"], backups)
    capsys.readouterr()
    run(world, "case", str(world["a2"][1]), "--backups", str(backups))
    out = capsys.readouterr().out
    assert "1 checked, 1 still hold this data" in out          # a2 is still live, so a backup taken now holds *it*
    # whereas a backup checked against the already-purged case a1's plan would be clean:
    plan = purge.Plan("case", world["a1"][1], case_ids=[world["a1"][1]])
    assert purge.backup_holds(clean, plan) == "no"
