"""Drives one check through the pilot's ask-first flow: intent -> follow the suggestion -> result.
Imports are inside the functions so a test module can set its sys.path / env first."""


def run_check(V, visit_id, *, word=None):
    """Returns (the revealed step, the step after the result). `word` defaults to the check's first answer word."""
    from pilot.case_schema import DecisionRequest, IntentRequest
    V.submit_intent(visit_id, IntentRequest(kind="unsure"))
    revealed = V.get_current_step(visit_id)
    started = V.submit_decision(visit_id, DecisionRequest(action="follow"))
    return revealed, V.answer(visit_id, word or started["words"][0])


def http_check(c, headers, visit_id):
    """The same flow over HTTP; returns the step after the result."""
    c.post(f"/api/visits/{visit_id}/intent", headers=headers, json={"kind": "unsure"}).raise_for_status()
    step = c.post(f"/api/visits/{visit_id}/decision", headers=headers, json={"action": "follow"}).json()["step"]
    return c.post(f"/api/visits/{visit_id}/answer", headers=headers, json={"word": step["words"][0]}).json()["step"]
