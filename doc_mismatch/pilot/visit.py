"""Multi-visit state, replacing live_demo/server.py's single unsynchronized global `VISIT`.

Rehydration = replay, not serialization: Session/CaseV1 objects aren't trivially picklable, and
`room_log` is kept as the single source of truth anyway (an audit trail, and the only state that must
survive a restart). On every request the room up to and including the current one is rebuilt from
scratch and replayed through `Session.report()`/`declare()` in log order -- `elapsed`/`at`/the AHU-level
memo/low_static-seen state all fall out of that replay deterministically, exactly as
live_demo/server.py's Visit._start_room()/answer() compute them procedurally in memory.
"""
import json
import threading
import uuid
from pathlib import Path

from . import cases as CS, config, db, engine_adapter
from .engine_adapter import Obs, Question

_locks: dict[str, threading.RLock] = {}
_meta = threading.Lock()


def _lock_for(visit_id: str) -> threading.RLock:
    # RLock, not Lock: answer()/advance() call get_current_step() while already holding this visit's lock.
    with _meta:
        return _locks.setdefault(visit_id, threading.RLock())


lock_for = _lock_for        # the case routes (routes_case.py) write to the same visit and take the same lock


def create_visit(building_json: dict, room_ids: list[str], *, feel: str | None = None, airflow: str | None = None,
                 context: dict | None = None) -> str:
    """Writes the confirmed building JSON to disk, creates the visits row and one case per room, returns the new visit_id."""
    context = CS.validate_context(context)         # before anything is written
    visit_id = uuid.uuid4().hex
    visit_dir = config.VISITS_DIR / visit_id
    visit_dir.mkdir(parents=True, exist_ok=True)
    building_path = visit_dir / "building.json"
    building_path.write_text(json.dumps(building_json, indent=1))
    # fail fast here (bad extraction, e.g. missing claims.vav_zone) rather than on the first /answer call
    building = engine_adapter.load_building(building_path)
    engine_adapter.build_cases(building, room_ids, feel=feel, airflow=airflow)
    with db.connect(config.DB_PATH) as conn:
        db.create_visit(conn, visit_id, str(building_path), room_ids, feel, airflow, engine_adapter.MIN_RATE)
        CS.open_cases(conn, visit_id, len(room_ids), context)
    return visit_id


def _rehydrate(visit_id: str, visit: dict) -> dict:
    building = engine_adapter.load_building(Path(visit["building_path"]))
    cases = engine_adapter.build_cases(building, visit["room_ids"], feel=visit["feel"], airflow=visit["airflow"])
    model = engine_adapter.build_joint_model(cases)
    room_index = visit["current_room"]
    memo: dict[tuple[str, str], str] = {}
    low_static_seen: set[str] = set()
    sess = None
    with db.connect(config.DB_PATH) as conn:
        for i in range(room_index + 1):
            case = cases[i]
            sess = engine_adapter.start_room_session(case, (model.causes[i], model.marg0[i]))
            for (ahu, name), word in memo.items():
                if ahu == case.ahu:
                    sess.log.append(Obs(name, case.doc, word, 0.0))
            if case.ahu in low_static_seen:
                sess.log.append(Obs("static_at_box", case.doc, "abnormal", 0.0))
            by_name = {c.name: c for c in case.checks}
            for entry in db.get_room_log(conn, visit_id, i):
                if entry["entry_type"] == "report":
                    ck = by_name[entry["check_name"]]
                    sess.report(entry["outcome"], check=entry["check_name"], target=entry["target"])
                    if ck.subject == "ahu":
                        memo[(case.ahu, entry["check_name"])] = entry["outcome"]
                    elif entry["check_name"] == "static_at_box" and entry["outcome"] == "abnormal":
                        low_static_seen.add(case.ahu)
                else:
                    sess.declare(entry["declare_key"], entry["outcome"])
    step = sess.next_step()
    return dict(visit_id=visit_id, sess=sess, cases=cases, room_index=room_index, memo=memo, low_static_seen=low_static_seen, step=step)


def _load(visit_id: str) -> dict | None:
    """The visit, rebuilt up to its current room, with that room's case row and events. None once the visit is done."""
    with db.connect(config.DB_PATH) as conn:
        visit = db.get_visit(conn, visit_id)
    if visit is None:
        raise KeyError(visit_id)
    if visit["status"] == "done":
        return None
    ctx = _rehydrate(visit_id, visit)
    with db.connect(config.DB_PATH) as conn:
        case_row = db.get_case_for_room(conn, visit_id, ctx["room_index"])
        if case_row is None:                      # a visit that predates the case record
            CS.open_case(conn, visit_id, ctx["room_index"])
            case_row = db.get_case_for_room(conn, visit_id, ctx["room_index"])
        events = db.get_events(conn, case_row["id"])
    ctx.update(visit=visit, case_row=case_row, events=events)
    return ctx


def _check_payload(ctx: dict, rec) -> dict:
    case, memo = ctx["cases"][ctx["room_index"]], ctx["memo"]
    ck = rec.check
    already_memoed = (case.ahu, ck.name) in memo
    return dict(name=ck.name, text=rec.text, minutes=round(rec.minutes, 1), words=list(ck.words), p_pos=round(rec.p_pos, 2),
                memo_note=("Already read for an earlier room on this air handler -- free here." if already_memoed else
                           "A reading on the air handler itself: later rooms on the same air handler get this one for free." if ck.subject == "ahu" else None))


def _step_payload(ctx: dict) -> dict:
    sess, cases, room_index = ctx["sess"], ctx["cases"], ctx["room_index"]
    memo, low_static_seen, step = ctx["memo"], ctx["low_static_seen"], ctx["step"]
    case_id, events = ctx["case_row"]["id"], ctx["events"]
    case = cases[room_index]
    if step is None:
        st = sess.status()
        cause, belief = st["ranked"][0]
        conclusion_text = sess.describe(cause)
        forced = not st["concluded"]
        econ = engine_adapter.involves_econ_fault(cause)
        hedge = engine_adapter.hedge_for(sess, cause, belief)                       # low static with no box-level static reading of this room's own: not a plain diagnosis
        shown = hedge["belief"] if hedge else round(float(belief), 3)
        minutes_so_far, checks_so_far = round(sess.elapsed, 1), st["n_checks"]
        with db.connect(config.DB_PATH) as conn:
            db.save_room_conclusion(conn, ctx["visit_id"], room_index, conclusion_text=conclusion_text, belief=shown,
                                     minutes_so_far=minutes_so_far, checks_so_far=checks_so_far, forced=forced, involves_econ_fault=econ)
            CS.record_tool_conclusion(conn, case_id, events, cause=cause, text=conclusion_text, belief=shown, forced=forced,
                                       minutes=minutes_so_far, checks=checks_so_far, hedge=hedge)
            # running total through this room, for the frontend's header tally (only shown from the first conclude on)
            rows_so_far = db.get_conclusions(conn, ctx["visit_id"])
        leaf = dict(kind="conclude", room=room_index, case_id=case_id, conclusion=conclusion_text, tool_cause_id=engine_adapter.cause_id(cause),
                    belief=shown, hedged=bool(hedge), raw_belief=hedge["raw_belief"] if hedge else None, hedge_note=hedge["note"] if hedge else None,
                    rule_out=hedge["rule_out"] if hedge else None,
                    minutes_so_far=minutes_so_far, checks_so_far=checks_so_far, forced=forced, involves_econ_fault=econ,
                    visit_minutes=round(sum(r["minutes_so_far"] for r in rows_so_far), 1),
                    visit_checks=sum(r["checks_so_far"] for r in rows_so_far))
        has_next = room_index + 1 < len(cases)
        leaf["has_next"] = has_next
        if has_next:
            nxt = cases[room_index + 1]
            carried = [f"{name.replace('_', ' ')}: {word}" for (ahu, name), word in memo.items() if ahu == nxt.ahu]
            if nxt.ahu in low_static_seen:
                carried.append("low duct static already found on this air handler")
            leaf["carried_into_next"] = carried
            leaf["next_room_name"] = nxt.member_name
        return leaf
    if isinstance(step, Question):
        return dict(kind="question", stage="question", room=room_index, case_id=case_id, name=step.key, text=step.text, words=list(step.options))
    st = CS.step_state(events)
    stage = CS.stage_of(st)
    picker = engine_adapter.selectable_checks(sess)
    if stage == "intent":
        # Nothing about the suggestion -- not its name, text, kind, cost or likelihood -- may appear here: this is the
        # server-side half of the ask-first design. The picker is in catalogue order, with no ranking.
        return dict(kind="check", stage="intent", room=room_index, case_id=case_id, picker=picker)
    if stage == "revealed":
        return dict(kind="check", stage="revealed", room=room_index, case_id=case_id, picker=picker, **_check_payload(ctx, step))
    dec = st["decision"]["payload"]
    out = dict(kind="check", stage="in_progress", room=room_index, case_id=case_id, started_at=st["started"]["server_ts"], action=dec["action"])
    if dec["action"] == "external":
        return dict(out, name=None, text=dec["external_text"], words=[], external=True)
    chosen = next((p for p in picker if p["name"] == dec["check"] and p["target"] == dec["target"]), None)
    return dict(out, name=dec["check"], text=chosen["text"] if chosen else dec["check"], words=chosen["words"] if chosen else ["yes", "no"], external=False)


def _visit_done_payload(visit: dict) -> dict:
    with db.connect(config.DB_PATH) as conn:
        rows = db.get_conclusions(conn, visit["id"])
        case_ids = {c["room_index"]: c["id"] for c in (db.get_case_for_room(conn, visit["id"], i) for i in range(len(visit["room_ids"]))) if c}
        hedged = {}
        for room_index, case_id in case_ids.items():
            tc = CS.last_event(db.get_events(conn, case_id), "tool_conclusion")
            hedged[room_index] = bool(tc and tc["payload"].get("hedged"))
    building = engine_adapter.load_building(Path(visit["building_path"]))
    cases = engine_adapter.build_cases(building, visit["room_ids"], feel=visit["feel"], airflow=visit["airflow"])
    conclusions = [dict(room=r["room_index"], case_id=case_ids.get(r["room_index"]), conclusion=r["conclusion_text"], belief=r["belief"],
                         minutes_so_far=r["minutes_so_far"], checks_so_far=r["checks_so_far"],
                         forced=bool(r["forced"]), involves_econ_fault=bool(r["involves_econ_fault"]), hedged=hedged.get(r["room_index"], False)) for r in rows]
    return dict(kind="visit_done", conclusions=conclusions,
                visit_minutes=round(sum(r["minutes_so_far"] for r in rows), 1), visit_checks=sum(r["checks_so_far"] for r in rows),
                rooms=[dict(name=c.member_name) for c in cases])


def get_room_info(visit_id: str) -> list[dict]:
    with db.connect(config.DB_PATH) as conn:
        visit = db.get_visit(conn, visit_id)
        if visit is None:
            raise KeyError(visit_id)
        case_ids = {i: (db.get_case_for_room(conn, visit_id, i) or {}).get("id") for i in range(len(visit["room_ids"]))}
    building = engine_adapter.load_building(Path(visit["building_path"]))
    cases = engine_adapter.build_cases(building, visit["room_ids"], feel=visit["feel"], airflow=visit["airflow"])
    return [dict(id=c.member, name=c.member_name, ahu=c.ahu, documented_box=c.doc, case_id=case_ids[i]) for i, c in enumerate(cases)]


def room_name(visit_id: str, room_index: int) -> str:
    return get_room_info(visit_id)[room_index]["name"]


def get_current_step(visit_id: str) -> dict:
    with _lock_for(visit_id):
        ctx = _load(visit_id)
        if ctx is None:
            with db.connect(config.DB_PATH) as conn:
                visit = db.get_visit(conn, visit_id)
            return _visit_done_payload(visit)
        return _step_payload(ctx)


def _require_ctx(visit_id: str) -> dict:
    ctx = _load(visit_id)
    if ctx is None:
        raise ValueError("this visit is already complete")
    return ctx


def _require_check_step(ctx: dict):
    step = ctx["step"]
    if step is None:
        raise ValueError("this room has already concluded -- call advance instead")
    if isinstance(step, Question):
        raise ValueError("answer the question first")
    return step


def submit_intent(visit_id: str, req) -> dict:
    """Records what the technician would check next, THEN the suggestion that is now shown to them -- in that order,
    in one transaction. Nothing is written if the pick is not a check that exists here."""
    with _lock_for(visit_id):
        ctx = _require_ctx(visit_id)
        step = _require_check_step(ctx)
        st = CS.step_state(ctx["events"])
        if CS.stage_of(st) != "intent":
            raise ValueError("you have already said what you would check at this step")
        sess, case = ctx["sess"], ctx["cases"][ctx["room_index"]]
        intent = dict(choice=req.kind, check=None, target=None, text=None)      # not "kind": that is the event's own field
        if req.kind == "check":
            matches = [p for p in engine_adapter.selectable_checks(sess) if p["name"] == req.check and (req.target is None or p["target"] == req.target)]
            if not matches:
                raise ValueError("that check is not available here")
            pick = next((m for m in matches if m["target"] == case.doc), matches[0])
            intent.update(check=pick["name"], target=pick["target"])
        elif req.kind == "other":
            intent["text"] = (req.text or "").strip()
            if not intent["text"]:
                raise ValueError("say what you would check")
        shown = dict(check=step.check.name, target=step.target, text=step.text, minutes=round(step.minutes, 1), p_pos=round(step.p_pos, 3),
                     gain=round(step.gain, 3), why=step.why, ranked=engine_adapter.ranked_snapshot(sess),
                     free_via_memo=(case.ahu, step.check.name) in ctx["memo"],
                     intent_matches=req.kind == "check" and intent["check"] == step.check.name and intent["target"] == step.target)
        with db.connect(config.DB_PATH) as conn:
            db.append_event(conn, ctx["case_row"]["id"], "intent", intent, CS.clean_ts(req.client_ts))
            db.append_event(conn, ctx["case_row"]["id"], "suggestion_shown", shown)
    return get_current_step(visit_id)


def submit_decision(visit_id: str, req) -> dict:
    """follow / substitute / external start the clock; skip closes the step. All validation happens on the rebuilt
    (throwaway) session before the first write -- a bad request leaves no trace and cannot break the visit."""
    with _lock_for(visit_id):
        ctx = _require_ctx(visit_id)
        step = _require_check_step(ctx)
        st = CS.step_state(ctx["events"])
        if CS.stage_of(st) != "revealed":
            raise ValueError("choose what you would check first" if CS.stage_of(st) == "intent" else "a check is already in progress")
        sess, shown = ctx["sess"], st["shown"]["payload"]
        payload = dict(action=req.action, reason=req.reason, note=(req.note or "").strip() or None,
                       suggested=dict(check=shown["check"], target=shown["target"]))
        if req.action == "follow":
            payload.update(check=shown["check"], target=shown["target"])
        elif req.action == "substitute":
            if (req.check, req.target or step.target) == (shown["check"], shown["target"]):
                raise ValueError("that is the suggested check -- choose 'doing this check' instead")
            matches = [p for p in engine_adapter.selectable_checks(sess) if p["name"] == req.check and (req.target is None or p["target"] == req.target)]
            if not matches:
                raise ValueError("that check is not available here")
            pick = next((m for m in matches if m["target"] == ctx["cases"][ctx["room_index"]].doc), matches[0])
            payload.update(check=pick["name"], target=pick["target"])
        elif req.action == "external":
            payload["external_text"] = (req.external_text or "").strip()
            if not payload["external_text"]:
                raise ValueError("say what you are going to check")
        else:                                           # skip
            payload.update(check=shown["check"], target=shown["target"])
            try:
                sess.report("skip", check=shown["check"], target=shown["target"])
            except KeyError as e:
                raise ValueError(str(e)) from None
        ts = CS.clean_ts(req.client_ts)
        with db.connect(config.DB_PATH) as conn:
            if req.action == "skip":
                payload["room_log_id"] = db.append_report(conn, visit_id, ctx["room_index"], payload["check"], payload["target"], "skip")
                db.append_event(conn, ctx["case_row"]["id"], "decision", payload, ts)
            else:
                db.append_event(conn, ctx["case_row"]["id"], "decision", payload, ts)
                db.append_event(conn, ctx["case_row"]["id"], "check_started",
                                dict(check=payload.get("check"), target=payload.get("target"), external=req.action == "external"), ts)
    return get_current_step(visit_id)


def answer(visit_id: str, word: str | None = None, *, reading_text: str | None = None, result_text: str | None = None,
           minutes_correction: float | None = None, note: str | None = None, client_ts: str | None = None) -> dict:
    """The result of the check in progress, or the answer to a question. `word` is the only thing that reaches the
    engine; the rest is stored on the case. The word is validated on the rebuilt session BEFORE anything is written:
    a bad word used to land in room_log first and then fail every later replay of the visit."""
    with _lock_for(visit_id):
        ctx = _require_ctx(visit_id)
        step, sess, room_index = ctx["step"], ctx["sess"], ctx["room_index"]
        if step is None:
            raise ValueError("this room has already concluded -- call advance instead")
        case_id, ts = ctx["case_row"]["id"], CS.clean_ts(client_ts)
        if isinstance(step, Question):
            sess.declare(step.key, word if word is not None else "")        # raises unless yes/no
            with db.connect(config.DB_PATH) as conn:
                rl = db.append_declare(conn, visit_id, room_index, step.key, word)
                db.append_event(conn, case_id, "question_answer", dict(key=step.key, answer=word, room_log_id=rl), ts)
            return get_current_step(visit_id)
        st = CS.step_state(ctx["events"])
        if CS.stage_of(st) != "in_progress":
            raise ValueError("say what you would check and start a check before reporting its result")
        dec = st["decision"]["payload"]
        common = dict(minutes_correction=minutes_correction, note=(note or "").strip() or None, started_event_id=st["started"]["id"])
        if dec["action"] == "external":
            text = (result_text or "").strip()
            if not text:
                raise ValueError("describe what you found")
            with db.connect(config.DB_PATH) as conn:
                db.append_event(conn, case_id, "external_result", dict(common, external_text=dec["external_text"], result_text=text), ts)
            return get_current_step(visit_id)
        if word is None or word == "skip":
            raise ValueError("give the result (to skip a check, use the skip option instead)")
        # the wording is read BEFORE the engine records the check (afterwards it is no longer on the list of checks left to do);
        # the close-out screen's one-tap re-check shows it back to the technician
        text = next((c["text"] for c in engine_adapter.selectable_checks(sess) if c["name"] == dec["check"] and c["target"] == dec["target"]), None)
        try:
            sess.report(word, check=dec["check"], target=dec["target"])
        except KeyError as e:
            raise ValueError(str(e)) from None
        obs = sess.log[-1]
        with db.connect(config.DB_PATH) as conn:
            rl = db.append_report(conn, visit_id, room_index, dec["check"], dec["target"], word)
            db.append_event(conn, case_id, "check_result",
                            dict(common, check=dec["check"], target=dec["target"], text=text, word=obs.outcome, reading_text=(reading_text or "").strip() or None,
                                 room_log_id=rl, modeled_minutes=round(obs.minutes, 1), followed_suggestion=dec["action"] == "follow"), ts)
    return get_current_step(visit_id)


def advance(visit_id: str, from_room: int | None = None) -> dict:
    """Moves on from a room that has CONCLUDED. Two guards, because an unguarded advance silently abandons a complaint room (its case is
    left open with no record of why): the room must actually be finished, and the caller says which room it is leaving, so a double tap
    or a stale page is refused instead of skipping the next room. Advancing a visit that is already complete is a harmless no-op."""
    with _lock_for(visit_id):
        ctx = _load(visit_id)
        if ctx is None:
            return get_current_step(visit_id)
        if from_room is not None and from_room != ctx["room_index"]:
            raise ValueError("that room is already finished: the visit has moved on")
        if ctx["step"] is not None:
            raise ValueError("this room is not finished yet")
        next_room = ctx["room_index"] + 1
        with db.connect(config.DB_PATH) as conn:
            if next_room >= len(ctx["visit"]["room_ids"]):
                db.update_visit_progress(conn, visit_id, status="done")
            else:
                db.update_visit_progress(conn, visit_id, current_room=next_room)
    return get_current_step(visit_id)
