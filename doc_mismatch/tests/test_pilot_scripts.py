"""The offline tools: export (anonymization, completeness, ordering, timing), backup (consistent, verified, restorable),
and the follow-up / participant CLI. The planted names below are the point of the export tests: none may survive."""
import io
import json
import os
import sqlite3
import sys
import tarfile
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
os.environ.setdefault("PILOT_DATA_DIR", tempfile.mkdtemp(prefix="pilot_scripts_test_"))

import pytest  # noqa: E402

from pilot import cases as CS, config, db, visit as V  # noqa: E402
from pilot.case_schema import DecisionRequest, IntentRequest  # noqa: E402
from pilot.scripts import backup, export_cases, followups  # noqa: E402
from _pilot_flow import run_check  # noqa: E402

# deliberately identifying: a building code, a tenant's suite, an engineer's tag
AHU, VAV, ROOM = "NORTHWING-AHU-01", "VAV-ZK-17", "Suite 210 Kowalski Dental"
POINT = "BLDG7.NW.SF"
EMAIL, PHONE = "dana.k@clinic-example.com", "(312) 555-0142"
PLANTED = [AHU, VAV, ROOM, POINT, "Kowalski", EMAIL, PHONE, "555-0142"]

BUILDING = {
    "equipment": [{"id": AHU, "kind": "AHU"}, {"id": VAV, "kind": "VAV"}, {"id": ROOM, "kind": "Zone"}],
    "claims": {"vav_zone": {ROOM: VAV}, "ahu_vav": {VAV: AHU}},
    "control_system": {"points": {VAV: {"status": "V1.STS", "airflow": "V1.CFM"}, AHU: {"fan_status": POINT}, ROOM: {"temperature": "R210.T"}}},
}


@pytest.fixture(autouse=True)
def _fresh_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "pilot.db")
    monkeypatch.setattr(config, "VISITS_DIR", tmp_path / "visits")
    db.init_db(config.DB_PATH)


class Clock:
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


def _participant():
    with db.connect(config.DB_PATH) as conn:
        return db.create_participant(conn, role="contractor_tech", years_band="2to5", vav_band="some")


def _case_id(vid):
    with db.connect(config.DB_PATH) as conn:
        return db.get_case_for_room(conn, vid, 0)["id"]


def _full_case(clock, *, context=None):
    """A case with every link: complaint, a 14-minute check, root cause, repair, confirmed fix."""
    vid = V.create_visit(BUILDING, [ROOM], feel="too_hot", airflow="yes", context=context or dict(
        complaint_text=f"{ROOM} is hot; call {EMAIL} or {PHONE}", building_type="healthcare", own_hypotheses=["box_mechanical"]))
    V.submit_intent(vid, IntentRequest(kind="unsure"))
    started = V.submit_decision(vid, DecisionRequest(action="follow"))
    clock.advance(minutes=14)
    V.answer(vid, started["words"][0], reading_text="0.8 in. w.c.")
    for _ in range(40):
        step = V.get_current_step(vid)
        if step["kind"] == "conclude":
            break
        run_check(V, vid) if step["kind"] == "check" else V.answer(vid, "no")
    cid = _case_id(vid)
    with db.connect(config.DB_PATH) as conn:
        CS.record_root_cause(conn, cid, cause_id="actuator_fail", text=None, how_confirmed="measured", client_ts=None)
        CS.record_repair(conn, cid, actions=["replaced_part"], text=f"swapped it, tenant is {EMAIL}", repaired_on="2026-10-02", client_ts=None)
        CS.record_outcome(conn, cid, fixed="yes", note=None, client_ts=None)
    return vid, cid


def _export(tmp_path, **kw):
    out = tmp_path / "export"
    stats = export_cases.export(tmp_path, out, **kw)
    cases = [json.loads(line) for line in (out / "cases.jsonl").read_text().splitlines()]
    return stats, cases, out


# ------------------------------------------------------------------------------------------------- export: content

def test_a_full_case_exports_as_one_ordered_complete_sequence(tmp_path, clock):
    _participant()
    _, cid = _full_case(clock)
    stats, cases, _ = _export(tmp_path)
    assert stats["exported"] == 1 and stats["complete"] == 1
    rec = cases[0]
    assert rec["case_id"] == cid and rec["complete"] is True
    assert rec["completeness"] == dict(complaint=True, timed_check=True, root_cause=True, repair=True, confirmed_fixed=True)
    first = rec["steps"][0]
    assert first["type"] == "check" and first["n"] == 1
    assert first["seconds"] == 840.0 and first["effective_minutes"] == 14.0, "14 minutes from tapping start to the result"
    assert first["intent"]["choice"] == "unsure" and first["suggested"]["check"] == first["check"] and first["followed_suggestion"] is True
    assert first["reading_text"] == "0.8 in. w.c."
    assert [s["n"] for s in rec["steps"]] == list(range(1, len(rec["steps"]) + 1))
    assert rec["root_cause"]["cause_id"] == "actuator_fail" and rec["repair"]["actions"] == ["replaced_part"] and rec["outcome"]["fixed"] == "yes"
    assert rec["participant"] == dict(role="contractor_tech", years_band="2to5", vav_band="some")
    assert rec["tool_conclusion"] is not None and rec["context"]["own_hypotheses"]["groups"] == ["box_mechanical"]


def test_minutes_correction_sits_beside_the_raw_timing(tmp_path, clock):
    _participant()
    vid = V.create_visit(BUILDING, [ROOM], feel="too_hot", airflow="yes")
    V.submit_intent(vid, IntentRequest(kind="unsure"))
    started = V.submit_decision(vid, DecisionRequest(action="follow"))
    clock.advance(minutes=3)
    V.answer(vid, started["words"][0], minutes_correction=11)
    step = _export(tmp_path)[1][0]["steps"][0]
    assert step["seconds"] == 180.0 and step["minutes_correction"] == 11 and step["effective_minutes"] == 11


def test_substitute_skip_and_external_steps_keep_intent_and_suggestion(tmp_path, clock):
    _participant()
    vid = V.create_visit(BUILDING, [ROOM], feel="too_cold", airflow="no")
    V.submit_intent(vid, IntentRequest(kind="other", text="look at the trend log"))
    revealed = V.get_current_step(vid)
    V.submit_decision(vid, DecisionRequest(action="external", external_text="trend log", reason="not_relevant"))
    clock.advance(minutes=5)
    V.answer(vid, result_text="setpoint changed")
    V.submit_decision(vid, DecisionRequest(action="skip", reason="already_known"))
    steps = _export(tmp_path)[1][0]["steps"]
    assert [s["type"] for s in steps][:2] == ["external", "skipped"]
    ext, skipped = steps[0], steps[1]
    assert ext["seconds"] == 300.0 and ext["intent"]["text"] == "look at the trend log" and ext["suggested"]["check"] == revealed["name"]
    assert skipped["check"] == revealed["name"] and skipped["decision"]["reason"] == "already_known"
    assert skipped["intent"]["text"] == "look at the trend log", "the intent given before the suggestion stays attached through an off-list check"


def test_completeness_is_per_link_and_a_partial_case_is_not_complete(tmp_path, clock):
    _participant()
    vid = V.create_visit(BUILDING, [ROOM], feel="too_hot", airflow="yes")
    run_check(V, vid)
    cid = _case_id(vid)
    with db.connect(config.DB_PATH) as conn:
        CS.record_root_cause(conn, cid, cause_id="not_determined", text=None, how_confirmed="not_confirmed", client_ts=None)
    rec = _export(tmp_path)[1][0]
    assert rec["completeness"] == dict(complaint=True, timed_check=True, root_cause=False, repair=False, confirmed_fixed=False)
    assert rec["complete"] is False


def test_a_partly_fixed_case_is_not_counted_as_confirmed_fixed(tmp_path, clock):
    _participant()
    _, cid = _full_case(clock)
    with db.connect(config.DB_PATH) as conn:
        CS.record_outcome(conn, cid, fixed="partial", note=None, client_ts=None)
    rec = _export(tmp_path)[1][0]
    assert rec["outcome"]["fixed"] == "partial" and rec["complete"] is False


def test_followups_are_exported(tmp_path, clock):
    _participant()
    _, cid = _full_case(clock)
    clock.advance(days=8)
    with db.connect(config.DB_PATH) as conn:
        CS.record_followup(conn, cid, window_days=7, recurred="no", note=None, recorded_by="developer", client_ts=None)
    fu = _export(tmp_path)[1][0]["followups"]
    assert [(f["window_days"], f["recurred"], f["recorded_by"]) for f in fu] == [(7, "no", "developer")]


# ------------------------------------------------------------------------------------------------- export: anonymization

def test_no_planted_name_survives_in_any_exported_file(tmp_path, clock):
    _participant()
    _full_case(clock)
    _, _, out = _export(tmp_path)
    for name in ("cases.jsonl", "checks.csv", "SUMMARY.txt"):
        text = (out / name).read_text()
        for planted in PLANTED:
            assert planted not in text, f"{planted!r} leaked into {name}"
    text = (out / "cases.jsonl").read_text()
    assert "ahu_1" in text and "vav_1" in text and "room_1" in text and "[email]" in text and "[phone]" in text


def test_aliases_are_per_visit_and_never_carry_a_raw_id(tmp_path, clock):
    _participant()
    aliases = export_cases.build_aliases(BUILDING)
    assert aliases[AHU] == "ahu_1" and aliases[VAV] == "vav_1" and aliases[ROOM] == "room_1" and aliases[POINT].startswith("point_")
    scrub = export_cases.make_scrubber(aliases)
    assert scrub(f"At box {VAV}, in {ROOM}, read {POINT}") == "At box vav_1, in room_1, read point_" + aliases[POINT].split("_")[1]
    assert scrub({"cause": ["wrong", VAV], "n": 3}) == {"cause": ["wrong", "vav_1"], "n": 3}, "ranked-cause tuples carry equipment ids too"
    assert scrub("call 312-555-0142 or a@b.co") == "call [phone] or [email]"


def test_short_ids_are_not_substituted_inside_ordinary_words():
    scrub = export_cases.make_scrubber(export_cases.build_aliases(
        {"equipment": [{"id": "A1", "kind": "AHU"}, {"id": "VAV-2", "kind": "VAV"}]}))
    assert scrub("A1 readings are available") == "A1 readings are available", "ids under 3 characters are left alone"
    assert scrub("box VAV-2") == "box vav_1"
    assert scrub("VAV-22 is different") == "VAV-22 is different", "an id is only replaced as a whole token"


def test_drop_free_text_removes_every_free_text_field(tmp_path, clock):
    _participant()
    _full_case(clock)
    rec = _export(tmp_path, drop_text=True)[1][0]
    assert rec["context"]["complaint_text"] is None and rec["repair"]["text"] is None
    assert rec["steps"][0]["reading_text"] is None
    assert rec["completeness"]["complaint"] is True, "completeness is judged before the text is dropped"
    assert rec["root_cause"]["cause_id"] == "actuator_fail", "structured fields are untouched"


# ------------------------------------------------------------------------------------------------- export: what is excluded

def test_cases_without_an_acknowledged_participant_are_excluded_by_default(tmp_path, clock):
    _full_case(clock)                                      # no participant exists yet
    stats, cases, _ = _export(tmp_path)
    assert stats["excluded_unacknowledged"] == 1 and cases == []
    stats, cases, _ = _export(tmp_path, include_unacknowledged=True)
    assert stats["exported"] == 1 and cases[0]["participant"] is None


def test_a_case_whose_building_file_is_missing_is_never_exported_raw(tmp_path, clock):
    _participant()
    vid, _ = _full_case(clock)
    (config.VISITS_DIR / vid / "building.json").unlink()
    stats, cases, out = _export(tmp_path)
    assert stats["excluded_no_building"] == 1 and cases == []
    assert "building file missing" in (out / "SUMMARY.txt").read_text()


def test_export_opens_the_database_read_only(tmp_path, clock):
    _participant()
    _full_case(clock)
    before = (tmp_path / "pilot.db").read_bytes()
    _export(tmp_path)
    assert (tmp_path / "pilot.db").read_bytes() == before


# ------------------------------------------------------------------------------------------------- backup

def test_backup_is_verified_restorable_and_matches_the_source(tmp_path, clock):
    _participant()
    vid, _ = _full_case(clock)
    path = backup.make_backup(tmp_path, tmp_path / "backups")
    assert path.name.startswith("pilot-backup-") and path.suffix == ".gz" and not list((tmp_path / "backups").glob("*.partial"))
    assert backup.verify_backup(path) == []
    with tarfile.open(path) as tar:
        names = tar.getnames()
        manifest = json.load(tar.extractfile("MANIFEST.json"))
    assert "pilot.db" in names and f"visits/{vid}/building.json" in names
    assert not any(n.startswith("uploads") for n in names), "photos are left out unless asked for"
    live = backup.row_counts(tmp_path / "pilot.db")
    assert manifest["row_counts"] == live and live["case_event"] > 0 and live["followup_due"] == 2


def test_backup_is_consistent_while_the_app_has_a_write_in_flight(tmp_path, clock):
    _participant()
    _full_case(clock)
    writer = sqlite3.connect(str(tmp_path / "pilot.db"))
    writer.execute("PRAGMA journal_mode=WAL")
    writer.execute("BEGIN")
    writer.execute("INSERT INTO participants (created_at, role) VALUES ('x', 'uncommitted')")
    try:
        path = backup.make_backup(tmp_path, tmp_path / "backups")
    finally:
        writer.rollback()
        writer.close()
    assert backup.verify_backup(path) == []
    with tarfile.open(path) as tar:
        manifest = json.load(tar.extractfile("MANIFEST.json"))
    assert manifest["row_counts"]["participants"] == 1, "an uncommitted write must not appear in the backup"


def test_photos_are_included_only_on_request(tmp_path, clock):
    _participant()
    _full_case(clock)
    (tmp_path / "uploads" / "abc").mkdir(parents=True)
    (tmp_path / "uploads" / "abc" / "bas.jpg").write_bytes(b"jpeg")
    with tarfile.open(backup.make_backup(tmp_path, tmp_path / "b1")) as tar:
        assert not any(n.startswith("uploads") for n in tar.getnames())
    with tarfile.open(backup.make_backup(tmp_path, tmp_path / "b2", photos=True)) as tar:
        assert "uploads/abc/bas.jpg" in tar.getnames()


def test_verify_catches_a_corrupt_or_tampered_backup(tmp_path, clock):
    _participant()
    _full_case(clock)
    good = backup.make_backup(tmp_path, tmp_path / "backups")
    garbage = tmp_path / "garbage.tar.gz"
    garbage.write_bytes(b"not a tarball")
    assert "not a readable backup" in backup.verify_backup(garbage)[0]
    # a tarball whose database no longer matches its manifest
    tampered = tmp_path / "tampered.tar.gz"
    with tarfile.open(good) as src, tarfile.open(tampered, "w:gz") as dst:
        for m in src.getmembers():
            data = src.extractfile(m).read() if m.isfile() else None
            if m.name == "pilot.db":
                data = data[:-4096] + b"\0" * 4096
            if data is None:
                dst.addfile(m)
            else:
                m.size = len(data)
                dst.addfile(m, io.BytesIO(data))
    assert backup.verify_backup(tampered), "a modified database must not verify"
    assert backup.main(["--verify", str(tampered)]) == 1 and backup.main(["--verify", str(good)]) == 0


def test_backup_refuses_when_there_is_no_database(tmp_path):
    with pytest.raises(SystemExit, match="no database"):
        backup.make_backup(tmp_path / "empty", tmp_path / "out")


# ------------------------------------------------------------------------------------------------- follow-up CLI

def test_followups_list_and_record(tmp_path, clock, capsys):
    _participant()
    vid, cid = _full_case(clock)
    d = ["--data-dir", str(tmp_path)]
    # the CLI compares against the real clock, so move the stored due date into the past rather than the clock forward
    with db.connect(config.DB_PATH) as conn:
        conn.execute("UPDATE followup_due SET due_at = '2000-01-01T00:00:00+00:00' WHERE window_days = 7")
    capsys.readouterr()
    assert followups.main(d + ["list"]) == 0
    out = capsys.readouterr().out
    assert "DUE OR OVERDUE (1)" in out and ROOM in out and f"case {cid:>4}" in out
    assert followups.main(d + ["record", str(cid), "7", "no", "--note", "called, fine"]) == 0
    assert followups.main(d + ["record", str(cid), "7", "yes"]) == 1, "an answered follow-up cannot be answered twice"
    capsys.readouterr()
    followups.main(d + ["list"])
    assert "DUE OR OVERDUE (0)" in capsys.readouterr().out
    with db.connect(config.DB_PATH) as conn:
        fu = [e["payload"] for e in db.get_events(conn, cid) if e["kind"] == "followup"]
    assert fu == [dict(window_days=7, recurred="no", note="called, fine", recorded_by="developer")]


def test_new_participant_starts_a_fresh_cohort(tmp_path):
    first = _participant()
    assert followups.main(["--data-dir", str(tmp_path), "new-participant"]) == 0
    with db.connect(config.DB_PATH) as conn:
        assert db.get_active_participant(conn) is None
        second = db.create_participant(conn, role="other", years_band="gt15", vav_band="daily")
    assert second != first
    with db.connect(config.DB_PATH) as conn:
        assert conn.execute("SELECT COUNT(*) FROM participants WHERE active = 1").fetchone()[0] == 1


def test_scripts_run_without_the_servers_secrets():
    """backup / export / followups are for a laptop holding a copy of the data: none may import pilot.config."""
    import subprocess
    code = ("import sys; sys.path.insert(0, %r); "
            "from pilot.scripts import backup, export_cases, followups; "
            "assert 'pilot.config' not in sys.modules, 'a script imported pilot.config'; print('ok')" % str(ROOT))
    env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "NOTIFY_EMAIL", "SMTP_FROM_EMAIL", "SMTP_APP_PASSWORD", "PILOT_DATA_DIR")}
    r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, cwd=str(ROOT))
    assert r.returncode == 0 and r.stdout.strip() == "ok", r.stderr
