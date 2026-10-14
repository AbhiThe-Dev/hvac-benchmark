"""Participant profile, the technician's inbox, case close-out (root cause, repair, outcome), the 7/30-day
follow-up, and the technician's view of what is stored. Every write takes the visit's lock (visit.py), the same one
the check-by-check routes use, so a close-out and an answer to the next room cannot interleave."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path as PathParam

from . import auth, cases as CS, db, config, engine_adapter, visit as V
from .case_schema import FollowupRequest, OutcomeRequest, ProfileRequest, RecheckRequest, RepairRequest, RootCauseRequest

router = APIRouter(dependencies=[Depends(auth.require_token)])
CaseId = Annotated[int, PathParam(ge=1, le=2**63 - 1)]       # outside this range a lookup would raise instead of answering 'no such case'


def _case_or_404(case_id: CaseId) -> dict:
    with db.connect(config.DB_PATH) as conn:
        case = db.get_case(conn, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="No such case.")
    return case


def _write(case_id: CaseId, fn, **kwargs) -> dict:
    case = _case_or_404(case_id)
    try:
        with V.lock_for(case["visit_id"]), db.connect(config.DB_PATH) as conn:
            event_id = fn(conn, case_id, **kwargs)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True, "event_id": event_id}


@router.get("/api/participant")
def get_participant():
    with db.connect(config.DB_PATH) as conn:
        p = db.get_active_participant(conn)
    return {"active": p is not None and p["notice_ack_at"] is not None, "notice": CS.NOTICE}


@router.post("/api/participant")
def create_participant(body: ProfileRequest):
    """Idempotent: a second call while a participant is active changes nothing (only the developer starts the next one)."""
    with db.connect(config.DB_PATH) as conn:
        p = db.get_active_participant(conn)
        pid = p["id"] if p else db.create_participant(conn, role=body.role, years_band=body.years_band, vav_band=body.vav_band)
    return {"active": True, "participant_id": pid}


@router.get("/api/choices")
def choices():
    """Vocabularies for the chips: the tool's own cause groups and causes, so what a technician confirms is comparable to what the tool concludes."""
    return {"cause_groups": engine_adapter.CAUSE_GROUPS, "causes": engine_adapter.taxonomy_choices()}


@router.get("/api/inbox")
def get_inbox():
    return CS.inbox(V.room_name)


@router.get("/api/cases/{case_id}/record")
def case_record(case_id: CaseId):
    rec = CS.record_view(case_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="No such case.")
    return rec


@router.post("/api/cases/{case_id}/root_cause")
def root_cause(case_id: CaseId, body: RootCauseRequest):
    return _write(case_id, CS.record_root_cause, cause_id=body.cause_id, text=body.text, how_confirmed=body.how_confirmed,
                  confirmed_before_repair=body.confirmed_before_repair, actual_box=body.actual_box, client_ts=body.client_ts)


@router.post("/api/cases/{case_id}/repair")
def repair(case_id: CaseId, body: RepairRequest):
    return _write(case_id, CS.record_repair, actions=body.actions, text=body.text, repaired_on=body.repaired_on, client_ts=body.client_ts)


@router.post("/api/cases/{case_id}/recheck")
def recheck(case_id: CaseId, body: RecheckRequest):
    return _write(case_id, CS.record_recheck, of_event_id=body.of_event_id, result=body.result, reading_text=body.reading_text, note=body.note,
                  client_ts=body.client_ts)


@router.post("/api/cases/{case_id}/outcome")
def outcome(case_id: CaseId, body: OutcomeRequest):
    return _write(case_id, CS.record_outcome, fixed=body.fixed, note=body.note, client_ts=body.client_ts)


@router.post("/api/cases/{case_id}/followup")
def followup(case_id: CaseId, body: FollowupRequest):
    return _write(case_id, CS.record_followup, window_days=body.window_days, recurred=body.recurred, note=body.note,
                  recorded_by="technician", client_ts=body.client_ts)
