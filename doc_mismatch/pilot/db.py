"""stdlib sqlite3 persistence. One visit = many real jobs over the pilot week; room_log is the single
source of truth for a room's session (replayed, never pickled -- see visit.py). WAL mode so a slow write
doesn't block concurrent reads from other routes."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS visits (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    building_path TEXT NOT NULL,
    room_ids_json TEXT NOT NULL,
    feel TEXT,
    airflow TEXT,
    min_rate REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'in_progress',
    current_room INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS room_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_id TEXT NOT NULL REFERENCES visits(id),
    room_index INTEGER NOT NULL,
    entry_type TEXT NOT NULL,      -- 'report' | 'declare'
    check_name TEXT,
    target TEXT,
    outcome TEXT NOT NULL,         -- 'report': the answer word (never a numeric reading). 'declare': 'yes'/'no'.
    declare_key TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS room_conclusion (
    visit_id TEXT NOT NULL REFERENCES visits(id),
    room_index INTEGER NOT NULL,
    conclusion_text TEXT NOT NULL,
    belief REAL NOT NULL,
    minutes_so_far REAL NOT NULL,
    checks_so_far INTEGER NOT NULL,
    forced INTEGER NOT NULL,
    involves_econ_fault INTEGER NOT NULL,
    PRIMARY KEY (visit_id, room_index)
);
CREATE TABLE IF NOT EXISTS intake (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    raw_tool_response TEXT,
    draft_building_json TEXT NOT NULL,
    confirmed_building_json TEXT,
    visit_id TEXT,
    photo_bas_path TEXT,
    photo_equipment_path TEXT
);
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    last_used_at TEXT,
    revoked INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS login_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    used INTEGER NOT NULL DEFAULT 0
);

-- Diagnostic case record (see DATA.md). room_log above stays the engine's replay input and is not extended:
-- visit.py's _rehydrate treats every non-'report' row as a declare.
CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    role TEXT,
    years_band TEXT,
    vav_band TEXT,
    notice_ack_at TEXT,
    active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_id TEXT NOT NULL REFERENCES visits(id),
    room_index INTEGER NOT NULL,
    participant_id INTEGER REFERENCES participants(id),
    opened_at TEXT NOT NULL,
    closed_at TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    prior_case_id INTEGER REFERENCES cases(id),
    data_version INTEGER NOT NULL,
    catalogue_hash TEXT NOT NULL,
    complaint_text TEXT,
    complaint_source TEXT,
    building_type TEXT,
    system_kind TEXT,
    equipment_age_band TEXT,
    readings_json TEXT,
    alarms_text TEXT,
    own_hypotheses_json TEXT,
    UNIQUE (visit_id, room_index)
);
-- Append-only: the triggers below make UPDATE/DELETE an error. Corrections are new 'correction' events.
CREATE TABLE IF NOT EXISTS case_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL REFERENCES cases(id),
    seq INTEGER NOT NULL,
    kind TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    client_ts TEXT,
    server_ts TEXT NOT NULL,
    UNIQUE (case_id, seq)
);
CREATE TRIGGER IF NOT EXISTS case_event_no_update BEFORE UPDATE ON case_event
BEGIN SELECT RAISE(ABORT, 'case_event is append-only'); END;
CREATE TRIGGER IF NOT EXISTS case_event_no_delete BEFORE DELETE ON case_event
BEGIN SELECT RAISE(ABORT, 'case_event is append-only'); END;
CREATE TABLE IF NOT EXISTS followup_due (
    case_id INTEGER NOT NULL REFERENCES cases(id),
    window_days INTEGER NOT NULL,
    due_at TEXT NOT NULL,
    answered_event_id INTEGER REFERENCES case_event(id),
    PRIMARY KEY (case_id, window_days)
);
-- Written by scripts/purge.py: THAT a purge happened and how much, never what it contained.
CREATE TABLE IF NOT EXISTS purge_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purged_at TEXT NOT NULL,
    scope TEXT NOT NULL,
    target_id INTEGER NOT NULL,
    reason TEXT NOT NULL,
    counts_json TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as conn:
        conn.executescript(SCHEMA)


@contextmanager
def connect(path: str | Path):
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ------------------------------------------------------------------------------------------------- visits

def create_visit(conn, visit_id: str, building_path: str, room_ids: list[str], feel: str | None, airflow: str | None, min_rate: float) -> None:
    now = _now()
    conn.execute(
        "INSERT INTO visits (id, created_at, updated_at, building_path, room_ids_json, feel, airflow, min_rate) VALUES (?,?,?,?,?,?,?,?)",
        (visit_id, now, now, building_path, json.dumps(room_ids), feel, airflow, min_rate),
    )


def get_visit(conn, visit_id: str) -> dict | None:
    row = conn.execute("SELECT * FROM visits WHERE id = ?", (visit_id,)).fetchone()
    if row is None:
        return None
    d = dict(row)
    d["room_ids"] = json.loads(d.pop("room_ids_json"))
    return d


def update_visit_progress(conn, visit_id: str, *, current_room: int | None = None, status: str | None = None) -> None:
    sets, params = [], []
    if current_room is not None:
        sets.append("current_room = ?")
        params.append(current_room)
    if status is not None:
        sets.append("status = ?")
        params.append(status)
    if not sets:
        return
    sets.append("updated_at = ?")
    params.append(_now())
    params.append(visit_id)
    conn.execute(f"UPDATE visits SET {', '.join(sets)} WHERE id = ?", params)


# ------------------------------------------------------------------------------------------------- room_log

def append_report(conn, visit_id: str, room_index: int, check_name: str, target: str, outcome: str) -> int:
    return conn.execute(
        "INSERT INTO room_log (visit_id, room_index, entry_type, check_name, target, outcome, created_at) VALUES (?,?,?,?,?,?,?)",
        (visit_id, room_index, "report", check_name, target, outcome, _now()),
    ).lastrowid


def append_declare(conn, visit_id: str, room_index: int, declare_key: str, value: str) -> int:
    return conn.execute(
        "INSERT INTO room_log (visit_id, room_index, entry_type, declare_key, outcome, created_at) VALUES (?,?,?,?,?,?)",
        (visit_id, room_index, "declare", declare_key, value, _now()),
    ).lastrowid


def get_room_log(conn, visit_id: str, room_index: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM room_log WHERE visit_id = ? AND room_index = ? ORDER BY id ASC",
        (visit_id, room_index),
    ).fetchall()
    return [dict(r) for r in rows]


def get_full_log(conn, visit_id: str) -> list[dict]:
    """Every room's log, in order -- used to replay memo/low-static state carried across rooms."""
    rows = conn.execute("SELECT * FROM room_log WHERE visit_id = ? ORDER BY id ASC", (visit_id,)).fetchall()
    return [dict(r) for r in rows]


# ------------------------------------------------------------------------------------------------- conclusions

def save_room_conclusion(conn, visit_id: str, room_index: int, *, conclusion_text: str, belief: float,
                          minutes_so_far: float, checks_so_far: int, forced: bool, involves_econ_fault: bool) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO room_conclusion (visit_id, room_index, conclusion_text, belief, minutes_so_far, checks_so_far, forced, involves_econ_fault) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (visit_id, room_index, conclusion_text, belief, minutes_so_far, checks_so_far, int(forced), int(involves_econ_fault)),
    )


def get_conclusions(conn, visit_id: str) -> list[dict]:
    rows = conn.execute("SELECT * FROM room_conclusion WHERE visit_id = ? ORDER BY room_index ASC", (visit_id,)).fetchall()
    return [dict(r) for r in rows]


# ------------------------------------------------------------------------------------------------- intake

def create_intake(conn, intake_id: str, raw_tool_response: str, draft_building_json: str,
                   photo_bas_path: str, photo_equipment_path: str) -> None:
    conn.execute(
        "INSERT INTO intake (id, created_at, raw_tool_response, draft_building_json, photo_bas_path, photo_equipment_path) VALUES (?,?,?,?,?,?)",
        (intake_id, _now(), raw_tool_response, draft_building_json, photo_bas_path, photo_equipment_path),
    )


def get_intake(conn, intake_id: str) -> dict | None:
    row = conn.execute("SELECT * FROM intake WHERE id = ?", (intake_id,)).fetchone()
    return dict(row) if row else None


def confirm_intake(conn, intake_id: str, confirmed_building_json: str, visit_id: str) -> None:
    conn.execute("UPDATE intake SET confirmed_building_json = ?, visit_id = ? WHERE id = ?",
                 (confirmed_building_json, visit_id, intake_id))


# ------------------------------------------------------------------------------------------------- sessions

def create_session(conn, token: str, expires_at: str) -> None:
    conn.execute("INSERT INTO sessions (token, created_at, expires_at) VALUES (?,?,?)", (token, _now(), expires_at))


def get_session(conn, token: str) -> dict | None:
    row = conn.execute("SELECT * FROM sessions WHERE token = ?", (token,)).fetchone()
    return dict(row) if row else None


def touch_session(conn, token: str) -> None:
    conn.execute("UPDATE sessions SET last_used_at = ? WHERE token = ?", (_now(), token))


def revoke_session(conn, token: str) -> None:
    conn.execute("UPDATE sessions SET revoked = 1 WHERE token = ?", (token,))


def revoke_all_sessions(conn) -> int:
    cur = conn.execute("UPDATE sessions SET revoked = 1 WHERE revoked = 0")
    return cur.rowcount


# ------------------------------------------------------------------------------------------------- login_codes

def create_login_code(conn, code_hash: str, expires_at: str) -> int:
    # only one recipient ever exists (config.NOTIFY_EMAIL) -- invalidate any still-unused code first, so only
    # the most recently sent one ever works
    conn.execute("UPDATE login_codes SET used = 1 WHERE used = 0")
    cur = conn.execute("INSERT INTO login_codes (code_hash, created_at, expires_at) VALUES (?,?,?)",
                        (code_hash, _now(), expires_at))
    return cur.lastrowid


def get_latest_login_code(conn) -> dict | None:
    row = conn.execute("SELECT * FROM login_codes ORDER BY id DESC LIMIT 1").fetchone()
    return dict(row) if row else None


def increment_code_attempts(conn, code_id: int) -> None:
    conn.execute("UPDATE login_codes SET attempts = attempts + 1 WHERE id = ?", (code_id,))


def mark_code_used(conn, code_id: int) -> None:
    conn.execute("UPDATE login_codes SET used = 1 WHERE id = ?", (code_id,))


# ------------------------------------------------------------------------------------------------- participants

def get_active_participant(conn) -> dict | None:
    row = conn.execute("SELECT * FROM participants WHERE active = 1 ORDER BY id DESC LIMIT 1").fetchone()
    return dict(row) if row else None


def create_participant(conn, *, role: str | None, years_band: str | None, vav_band: str | None) -> int:
    """Login is single-recipient, so there is no per-user identity to hang this on: exactly one participant is
    active at a time, and the developer starts the next one (scripts/followups.py new-participant)."""
    conn.execute("UPDATE participants SET active = 0 WHERE active = 1")
    now = _now()
    cur = conn.execute("INSERT INTO participants (created_at, role, years_band, vav_band, notice_ack_at) VALUES (?,?,?,?,?)",
                        (now, role, years_band, vav_band, now))
    return cur.lastrowid


def deactivate_participants(conn) -> int:
    return conn.execute("UPDATE participants SET active = 0 WHERE active = 1").rowcount


# ------------------------------------------------------------------------------------------------- cases

def create_case(conn, visit_id: str, room_index: int, *, participant_id: int | None, data_version: int, catalogue_hash: str,
                 prior_case_id: int | None = None, context: dict | None = None) -> int:
    ctx = context or {}
    cur = conn.execute(
        "INSERT INTO cases (visit_id, room_index, participant_id, opened_at, prior_case_id, data_version, catalogue_hash, "
        "complaint_text, complaint_source, building_type, system_kind, equipment_age_band, readings_json, alarms_text, own_hypotheses_json) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (visit_id, room_index, participant_id, _now(), prior_case_id, data_version, catalogue_hash,
         ctx.get("complaint_text"), ctx.get("complaint_source"), ctx.get("building_type"), ctx.get("system_kind"), ctx.get("equipment_age_band"),
         json.dumps(ctx["readings"]) if ctx.get("readings") else None, ctx.get("alarms_text"),
         json.dumps(ctx["own_hypotheses"]) if ctx.get("own_hypotheses") else None))
    return cur.lastrowid


def get_case(conn, case_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
    return dict(row) if row else None


def get_case_for_room(conn, visit_id: str, room_index: int) -> dict | None:
    row = conn.execute("SELECT * FROM cases WHERE visit_id = ? AND room_index = ?", (visit_id, room_index)).fetchone()
    return dict(row) if row else None


def list_cases(conn, *, participant_id: int | None = None, limit: int = 200) -> list[dict]:
    if participant_id is None:
        rows = conn.execute("SELECT * FROM cases ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM cases WHERE participant_id = ? ORDER BY id DESC LIMIT ?", (participant_id, limit)).fetchall()
    return [dict(r) for r in rows]


def close_case(conn, case_id: int) -> None:
    conn.execute("UPDATE cases SET status = 'closed', closed_at = ? WHERE id = ? AND status = 'open'", (_now(), case_id))


# ------------------------------------------------------------------------------------------------- case_event

def append_event(conn, case_id: int, kind: str, payload: dict, client_ts: str | None = None) -> int:
    """`seq` is assigned inside the INSERT so two writers cannot pick the same one (UNIQUE(case_id, seq) backs it up)."""
    cur = conn.execute(
        "INSERT INTO case_event (case_id, seq, kind, payload_json, client_ts, server_ts) "
        "SELECT ?, COALESCE(MAX(seq), 0) + 1, ?, ?, ?, ? FROM case_event WHERE case_id = ?",
        (case_id, kind, json.dumps(payload, sort_keys=True), client_ts, _now(), case_id))
    return cur.lastrowid


def get_events(conn, case_id: int) -> list[dict]:
    rows = conn.execute("SELECT * FROM case_event WHERE case_id = ? ORDER BY seq ASC", (case_id,)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["payload"] = json.loads(d.pop("payload_json"))
        out.append(d)
    return out


# ------------------------------------------------------------------------------------------------- followup_due

FOLLOWUP_WINDOWS = (7, 30)


def create_followups(conn, case_id: int, base_iso: str | None = None) -> None:
    """Idempotent: a later 'partial' -> 'yes' outcome does not move the dates."""
    base = datetime.fromisoformat(base_iso or _now())
    for w in FOLLOWUP_WINDOWS:
        conn.execute("INSERT OR IGNORE INTO followup_due (case_id, window_days, due_at) VALUES (?,?,?)",
                     (case_id, w, (base + timedelta(days=w)).isoformat()))


def get_followup(conn, case_id: int, window_days: int) -> dict | None:
    row = conn.execute("SELECT * FROM followup_due WHERE case_id = ? AND window_days = ?", (case_id, window_days)).fetchone()
    return dict(row) if row else None


def answer_followup(conn, case_id: int, window_days: int, event_id: int) -> None:
    conn.execute("UPDATE followup_due SET answered_event_id = ? WHERE case_id = ? AND window_days = ?", (event_id, case_id, window_days))


def due_followups(conn, *, participant_id: int | None = None, now_iso: str | None = None) -> list[dict]:
    """Unanswered follow-ups whose date has come, oldest first."""
    now_iso = now_iso or _now()
    sql = ("SELECT f.*, c.visit_id, c.room_index FROM followup_due f JOIN cases c ON c.id = f.case_id "
           "WHERE f.answered_event_id IS NULL AND f.due_at <= ?")
    params: list = [now_iso]
    if participant_id is not None:
        sql += " AND c.participant_id = ?"
        params.append(participant_id)
    return [dict(r) for r in conn.execute(sql + " ORDER BY f.due_at ASC", params).fetchall()]
