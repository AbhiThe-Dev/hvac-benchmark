"""The diagnostic case record: one `cases` row per complaint room, plus an append-only `case_event` log (db.py).

Which of the 16 fields each event serves is in DATA.md. The rules that matter:
  * events are only ever appended (the table's triggers abort UPDATE/DELETE); a typo is fixed by a new event;
  * the engine never sees anything stored here except the answer word, which still goes through room_log;
  * what the tool showed is stored when it is shown (`suggestion_shown`), not reconstructed later, because replay
    (visit._rehydrate) runs against whatever the catalogue is *today*.
"""
import json
import re
from datetime import datetime
from pathlib import Path

from . import db, engine_adapter as EA
from .ladder import PHYSICAL, POSITIVE, recheck_candidates, verification
from .topology import SENTINELS, building_view, candidate_boxes

DATA_VERSION = 1
TAXONOMY_IDS = {c["id"] for c in EA.taxonomy_choices()}
ROOT_CAUSE_IDS = TAXONOMY_IDS | {"other", "not_determined"}
LUMPS = {"doc_acts_fail", "doc_other"}               # tool conclusions too coarse to name a part: never counted as agree/disagree

# Shown on first use and served by GET /api/participant, so the screen and DATA.md say the same thing.
NOTICE = [
    "This app keeps a record of each call-out you run in it, so the tool can be checked against how call-outs really go.",
    "It records: the complaint and the building and system details you type in; the readings you enter; what you said you would check next; "
    "what the tool suggested and whether you followed it; each check you did, its result, and how long it took from when you tapped start.",
    "Later, if you choose to enter them: what the problem turned out to be, how you confirmed it, the repair, whether it fixed the complaint, "
    "and whether it came back.",
    "It does not record your name, employer, the building's name, or the address. Please do not type them into the free-text boxes. "
    "Photos you take are kept on the server and are not part of anything shared.",
    "The tool is an early research prototype and has not been validated on real call-outs. You are free to ignore its suggestions; "
    "recording that you did is useful.",
]

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _db_path():
    """config is imported lazily: it refuses to load without the server's secrets, and the offline tools
    (scripts/followups.py) reuse the record_* functions below with a path of their own."""
    from . import config
    return config.DB_PATH


def clean_ts(ts: str | None) -> str | None:
    """A device-clock timestamp, kept only if it parses; the server timestamp is the authoritative one."""
    if not ts:
        return None
    try:
        datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None
    return ts[:40]


# ------------------------------------------------------------------------------------------------- opening a case

def validate_context(ctx: dict | None) -> dict:
    ctx = dict(ctx or {})
    bad = [g for g in ctx.get("own_hypotheses", []) if g not in EA.CAUSE_GROUPS]
    if bad:
        raise ValueError(f"unknown cause group(s): {bad}")
    prior = ctx.get("prior_case_id")
    if prior is not None:
        with db.connect(_db_path()) as conn:
            if db.get_case(conn, prior) is None:
                raise ValueError("that earlier case does not exist")
    return ctx


def open_case(conn, visit_id: str, room_index: int, context: dict | None = None) -> int:
    ctx = dict(context or {})
    prior = ctx.pop("prior_case_id", None)
    groups, text = ctx.pop("own_hypotheses", []), ctx.pop("own_hypotheses_text", None)
    ctx["own_hypotheses"] = dict(groups=groups, text=text) if (groups or text) else None
    participant = db.get_active_participant(conn)
    return db.create_case(conn, visit_id, room_index, participant_id=participant["id"] if participant else None,
                          data_version=DATA_VERSION, catalogue_hash=EA.catalogue_hash(), prior_case_id=prior, context=ctx)


def open_cases(conn, visit_id: str, n_rooms: int, context: dict | None = None) -> list[int]:
    return [open_case(conn, visit_id, i, context) for i in range(n_rooms)]


# ------------------------------------------------------------------------------------------------- where a step is

def step_state(events: list[dict]) -> dict:
    """The events of the step in progress. A step ends with a check result, a question answer or a skip; an
    *external* (off-catalogue) check ends only its own timer, so the suggestion stays shown and the intent stays recorded."""
    empty = dict(intent=None, shown=None, decision=None, started=None)
    st = dict(empty)
    for e in events:
        k = e["kind"]
        if k in ("check_result", "question_answer") or (k == "decision" and e["payload"].get("action") == "skip"):
            st = dict(empty)
        elif k == "external_result":
            st["decision"] = st["started"] = None
        elif k == "intent":
            st["intent"] = e
        elif k == "suggestion_shown":
            st["shown"] = e
        elif k == "decision":
            st["decision"] = e
        elif k == "check_started":
            st["started"] = e
    return st


def stage_of(st: dict) -> str:
    """intent: suggestion withheld | revealed: suggestion shown, awaiting follow/other/skip | in_progress: timer running."""
    if st["decision"] is not None:
        return "in_progress"
    return "revealed" if st["intent"] is not None else "intent"


def last_event(events: list[dict], kind: str) -> dict | None:
    for e in reversed(events):
        if e["kind"] == kind:
            return e
    return None


# ------------------------------------------------------------------------------------------------- close-out

def record_tool_conclusion(conn, case_id: int, events: list[dict], *, cause: tuple, text: str, belief: float, forced: bool,
                            minutes: float, checks: int, hedge: dict | None = None) -> None:
    """Once per case (the step payload is rebuilt on every GET, so this must be idempotent). `belief` is what the technician was shown; for a hedged conclusion
    (engine_adapter.hedge_for) it is capped, and the model's own number is kept as `raw_belief`."""
    if last_event(events, "tool_conclusion") is not None:
        return
    payload = dict(cause=list(cause), id=EA.cause_id(cause), text=text, belief=belief, forced=forced, modeled_minutes=minutes, checks=checks)
    if hedge:
        payload.update(hedged=True, raw_belief=hedge["raw_belief"], hedge_rule_out=hedge["rule_out"])
    db.append_event(conn, case_id, "tool_conclusion", payload)


def _building(conn, visit_id: str) -> dict | None:
    """The visit's confirmed building file (None if it cannot be read). The export reads the same file from a backup."""
    visit = db.get_visit(conn, visit_id)
    try:
        return json.loads(Path(visit["building_path"]).read_text()) if visit else None
    except (OSError, ValueError):
        return None


def case_topology(conn, case: dict) -> dict | None:
    """What the close-out screen needs to ask "which box actually serves this room?": the drawings' box, and the other boxes in the building."""
    building = _building(conn, case["visit_id"])
    visit = db.get_visit(conn, case["visit_id"])
    if building is None or visit is None:
        return None
    room = visit["room_ids"][case["room_index"]]
    documented = building_view(building, room)["box"]
    return dict(documented_box=documented, boxes=[b for b in candidate_boxes(building) if b != documented])


def record_root_cause(conn, case_id: int, *, cause_id: str, text: str | None, how_confirmed: str | None, client_ts: str | None,
                      confirmed_before_repair: bool | None = None, actual_box: str | None = None) -> int:
    """`confirmed_before_repair` is the technician's own statement and the only thing that lets "saw it" / "measured it"
    count as a pre-repair confirmation on the verification ladder (ladder.py). It is only accepted where it can be true:
    "the repair fixed it" is by definition after the repair (stored as False, not asked), and a method that is not a
    physical confirmation (ruled out the others, told by someone, best guess) cannot be "before the repair" at all."""
    if cause_id not in ROOT_CAUSE_IDS:
        raise ValueError(f"unknown cause {cause_id!r}")
    text = (text or "").strip() or None
    if cause_id == "other" and not text:
        raise ValueError("describe what it was")
    actual_box = (actual_box or "").strip() or None
    if actual_box is not None:
        if cause_id != "documentation_wrong":
            raise ValueError("which box actually serves the room only applies when the drawings were wrong")
        if actual_box not in SENTINELS:
            topo = case_topology(conn, db.get_case(conn, case_id))
            if topo is None or actual_box not in topo["boxes"]:
                raise ValueError("that is not one of this building's other boxes (or it is the box the drawings already name)")
    if how_confirmed in PHYSICAL:
        before = confirmed_before_repair
    elif how_confirmed == "repair_fixed_it":
        if confirmed_before_repair is True:
            raise ValueError("a confirmation that came from the repair working cannot also be from before the repair")
        before = False
    else:
        if confirmed_before_repair is True:
            raise ValueError("only seeing or measuring the fault can count as confirmed before the repair")
        before = None
    tool = last_event(db.get_events(conn, case_id), "tool_conclusion")
    tool_id = tool["payload"]["id"] if tool else None
    agrees = None if (tool_id is None or tool_id in LUMPS or cause_id == "not_determined") else tool_id == cause_id
    return db.append_event(conn, case_id, "root_cause",
                           dict(cause_id=cause_id, text=text, in_taxonomy=cause_id in TAXONOMY_IDS, how_confirmed=how_confirmed,
                                confirmed_before_repair=before, actual_box=actual_box, tool_cause_id=tool_id, agrees_with_tool=agrees), clean_ts(client_ts))


def record_repair(conn, case_id: int, *, actions: list[str], text: str | None, repaired_on: str | None, client_ts: str | None) -> int:
    if repaired_on and not _DATE.match(repaired_on):
        raise ValueError("repaired_on must be YYYY-MM-DD")
    if not actions and not (text or "").strip():
        raise ValueError("choose what was done, or describe it")
    return db.append_event(conn, case_id, "repair", dict(actions=actions, text=(text or "").strip() or None, repaired_on=repaired_on),
                           clean_ts(client_ts))


def record_recheck(conn, case_id: int, *, of_event_id: int, result: str, reading_text: str | None, note: str | None, client_ts: str | None) -> int:
    """After a repair, the technician repeats the test that found the fault and says whether it is now fine. Stored as its own event, linked to
    the original result; it never goes through the engine (which refuses a repeat of a check already done). Only a check that FOUND something
    in this case can be re-checked, and only once a repair has been recorded: a "fine now" before any repair would be meaningless."""
    events = db.get_events(conn, case_id)
    original = next((e for e in events if e["id"] == of_event_id and e["kind"] == "check_result"), None)
    if original is None:
        raise ValueError("that check was not part of this case")
    if original["payload"].get("word") not in POSITIVE:
        raise ValueError("only a check that found something can be re-checked")
    if last_event(events, "repair") is None:
        raise ValueError("record what was done before re-checking")
    p = original["payload"]
    return db.append_event(conn, case_id, "post_repair_check",
                           dict(of_event_id=of_event_id, check=p["check"], target=p["target"], before_word=p["word"], before_reading_text=p.get("reading_text"),
                                result=result, reading_text=(reading_text or "").strip() or None, note=(note or "").strip() or None), clean_ts(client_ts))


def record_outcome(conn, case_id: int, *, fixed: str, note: str | None, client_ts: str | None) -> int:
    """Closes the case. A fix (or partial fix) starts the 7- and 30-day repeat-failure follow-ups."""
    eid = db.append_event(conn, case_id, "outcome", dict(fixed=fixed, note=(note or "").strip() or None), clean_ts(client_ts))
    db.close_case(conn, case_id)
    if fixed in ("yes", "partial"):
        db.create_followups(conn, case_id)
    return eid


def record_followup(conn, case_id: int, *, window_days: int, recurred: str, note: str | None, recorded_by: str, client_ts: str | None) -> int:
    due = db.get_followup(conn, case_id, window_days)
    if due is None:
        raise ValueError("no follow-up is scheduled for that case and window")
    if due["answered_event_id"] is not None:
        raise ValueError("that follow-up was already answered")
    eid = db.append_event(conn, case_id, "followup",
                          dict(window_days=window_days, recurred=recurred, note=(note or "").strip() or None, recorded_by=recorded_by),
                          clean_ts(client_ts))
    db.answer_followup(conn, case_id, window_days, eid)
    return eid


# ------------------------------------------------------------------------------------------------- what the technician sees

def next_needed(events: list[dict]) -> str | None:
    """What a finished-looking case still lacks, in the order it is usually known."""
    for kind in ("root_cause", "repair", "outcome"):
        if last_event(events, kind) is None:
            return kind
    return None


def inbox(room_name) -> dict:
    """Cases waiting on the technician, follow-ups that have come due, and recent cases for the 'return visit' picker.
    `room_name(visit_id, room_index)` is injected so this module never reads building files itself."""
    with db.connect(_db_path()) as conn:
        participant = db.get_active_participant(conn)
        pid = participant["id"] if participant else None
        cases = db.list_cases(conn, participant_id=pid, limit=60) if pid else []
        due = db.due_followups(conn, participant_id=pid) if pid else []
        events = {c["id"]: db.get_events(conn, c["id"]) for c in cases}

    def label(c):
        return dict(case_id=c["id"], room=room_name(c["visit_id"], c["room_index"]), opened_at=c["opened_at"], visit_id=c["visit_id"])

    awaiting = []
    for c in cases:
        ev = events[c["id"]]
        # the tool has finished (or the technician has started closing it out) but the outcome is not in
        if c["status"] == "open" and (last_event(ev, "tool_conclusion") or last_event(ev, "root_cause")):
            awaiting.append(dict(label(c), next_needed=next_needed(ev)))
    by_id = {c["id"]: c for c in cases}
    due_out = [dict(label(by_id[d["case_id"]]), window_days=d["window_days"], due_at=d["due_at"]) for d in due if d["case_id"] in by_id]
    return dict(participant=bool(participant), awaiting=awaiting, followups=due_out, recent=[label(c) for c in cases[:20]])


def record_view(case_id: int) -> dict | None:
    """Everything stored for one case, exactly as stored: what makes 'you can see what I keep' true."""
    with db.connect(_db_path()) as conn:
        case = db.get_case(conn, case_id)
        if case is None:
            return None
        events = db.get_events(conn, case_id)
        return dict(case=case, events=events, ladder=verification(events), topology=case_topology(conn, case), recheck=dict(candidates=recheck_candidates(events), can=last_event(events, "repair") is not None), followups=[
            dict(window_days=w, **{k: v for k, v in (db.get_followup(conn, case_id, w) or {}).items() if k in ("due_at", "answered_event_id")})
            for w in db.FOLLOWUP_WINDOWS if db.get_followup(conn, case_id, w)])
