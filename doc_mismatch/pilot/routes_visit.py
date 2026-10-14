"""Note: only AnswerRequest.`word` ever reaches the engine -- never a numeric `reading`/`expected`. That's deliberate:
bas_static/ahu_gauge/max_airflow/k_factor can raise ValueError if answered with a bare numeric reading and
no `attributes` on file (always true at T3-noattr) -- see test_pilot_engine_adapter.py's hazard test. The
`reading_text` a technician may type ("0.8 in. w.c.") is stored on the case record and never forwarded; do not
wire it to Session.report(reading=) without re-reading that test."""
from fastapi import APIRouter, Depends, HTTPException

from . import auth, visit as V
from .case_schema import AdvanceRequest, DecisionRequest, IntentRequest
from .schema import AnswerRequest

router = APIRouter(dependencies=[Depends(auth.require_token)])


@router.get("/api/session")
def check_session():
    """A token can exist in localStorage with no in-progress visit (fresh login, or one that just finished);
    the frontend calls this on boot to confirm that token is still genuinely valid before showing the
    new-visit form, rather than trusting its mere presence -- a revoked/expired token must never *look*
    logged in just because no visit-scoped call has happened yet to catch it."""
    return {"ok": True}


@router.get("/api/visits/{visit_id}")
def get_visit(visit_id: str):
    try:
        rooms = V.get_room_info(visit_id)
        step = V.get_current_step(visit_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="No such visit.")
    return {"rooms": rooms, "step": step}


def _run(fn, *args, **kwargs):
    try:
        return {"step": fn(*args, **kwargs)}
    except KeyError:
        raise HTTPException(status_code=404, detail="No such visit.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/visits/{visit_id}/intent")
def intent_visit(visit_id: str, body: IntentRequest):
    """What the technician would check next -- recorded before the tool's suggestion is revealed."""
    return _run(V.submit_intent, visit_id, body)


@router.post("/api/visits/{visit_id}/decision")
def decision_visit(visit_id: str, body: DecisionRequest):
    """Follow the suggestion, do another check, do an off-list check, or skip -- and start the clock (except skip)."""
    return _run(V.submit_decision, visit_id, body)


@router.post("/api/visits/{visit_id}/answer")
def answer_visit(visit_id: str, body: AnswerRequest):
    return _run(V.answer, visit_id, body.word, reading_text=body.reading_text, result_text=body.result_text,
                minutes_correction=body.minutes_correction, note=body.note, client_ts=body.client_ts)


@router.post("/api/visits/{visit_id}/advance")
def advance_visit(visit_id: str, body: AdvanceRequest | None = None):
    return _run(V.advance, visit_id, body.from_room if body else None)
