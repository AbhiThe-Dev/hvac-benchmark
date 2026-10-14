"""The verification ladder: how far a case's root-cause label has actually been checked.

It is computed from the case's events alone (nothing extra is stored), by one pure function that has no imports from
the rest of the pilot, so the app and the offline export (which runs without the server's secrets) share one definition.

Four rungs. They are independent pieces of evidence, not a strict order: a case can be repair-confirmed without ever
having been physically confirmed first (suspected, replaced the part, it worked).

  suspected            a cause is named (the technician's, not just the tool's)
  physically_confirmed the fault itself was SEEN or MEASURED, and the technician says that was BEFORE the repair
  repair_confirmed     a real repair was made and the complaint is recorded as fixed ("yes", not "partly")
  stayed_fixed         repair_confirmed, and a 7- or 30-day follow-up says it did not come back (and none says it did)

`level` is the highest rung reached (0 = no cause named). A one-tap RE-CHECK (repeat the test that found the fault, after the repair) is
reported in `recheck` and can only add a caveat (`recheck_contradicts_fix`: recorded as fixed, but the same test still fails). It never
grants a rung: it is the technician's own answer, like "fixed: yes", just tied to a specific test. The rule that matters: **a rung is never granted on
inference.** "Measured it" with no statement about timing is NOT counted as before the repair (it is flagged
`pre_repair_unknown`); "the repair fixed it" is a repair result, never a pre-repair confirmation; "ruled out the others"
and "another tech told me" are not physical. `caveats` say what weakens an otherwise-granted rung, so an analyst can
choose how strict to be (e.g. drop `multi_action_repair` cases when attributing a fix to one cause).
"""

PHYSICAL = ("observed_directly", "measured")             # the fault itself was seen or measured
NOT_A_FIX = ("no_repair_needed", "deferred_or_referred")  # recorded under "what was done", but nothing was repaired
POSITIVE = ("abnormal", "yes")                          # a check result that FOUND something (every check's positive answer; the vocabulary is shared)
RECHECK_RESULTS = ("now_ok", "still_wrong", "unsure")
RUNGS = ("suspected", "physically_confirmed", "repair_confirmed", "stayed_fixed")
LEVEL_NAMES = ("no cause named", "suspected", "physically confirmed before repair", "repair confirmed", "stayed fixed")


def _latest(events: list[dict], kind: str) -> dict | None:
    return next((e["payload"] for e in reversed(events) if e["kind"] == kind), None)


def _positives(events: list[dict]) -> list[dict]:
    return [e for e in events if e["kind"] == "check_result" and e["payload"].get("word") in POSITIVE]


def recheck_candidates(events: list[dict], limit: int = 3) -> list[dict]:
    """The checks in this case that found something, newest last, each with the latest re-check recorded for it (or None).
    These are the checks worth repeating after a repair: the same test that said "wrong" should now say "fine"."""
    latest = {}
    for e in events:
        if e["kind"] == "post_repair_check":
            latest[e["payload"]["of_event_id"]] = dict(e["payload"], event_id=e["id"])
    out = []
    for e in _positives(events)[-limit:]:
        p = e["payload"]
        out.append(dict(of_event_id=e["id"], check=p["check"], target=p["target"], text=p.get("text"), before_word=p["word"],
                        before_reading_text=p.get("reading_text"), latest=latest.get(e["id"])))
    return out


def _recheck_state(events: list[dict]) -> dict:
    """What the re-checks say overall: 'still_wrong' if ANY re-checked test still fails, 'now_ok' if all that were decided are fine,
    'unsure' if only "couldn't tell" was recorded, None if none was re-checked. A re-check informs; it never grants a rung."""
    latest = {}
    for e in events:
        if e["kind"] == "post_repair_check":
            latest[e["payload"]["of_event_id"]] = e["payload"]["result"]
    results = list(latest.values())
    decided = [r for r in results if r != "unsure"]
    state = None if not results else "unsure" if not decided else "still_wrong" if "still_wrong" in decided else "now_ok"
    return dict(state=state, n=len(results))


def verification(events: list[dict]) -> dict:
    """`events` as db.get_events returns them (dicts with `kind` and `payload`), oldest first."""
    rcs = [e["payload"] for e in events if e["kind"] == "root_cause"]
    rc, rp, oc = (rcs[-1] if rcs else None), _latest(events, "repair"), _latest(events, "outcome")
    followups = {}
    for e in events:
        if e["kind"] == "followup":
            followups[e["payload"]["window_days"]] = e["payload"]["recurred"]
    caveats = []

    named = rc is not None and rc["cause_id"] != "not_determined"
    method = rc.get("how_confirmed") if rc else None
    before = rc.get("confirmed_before_repair") if rc else None
    physical = named and method in PHYSICAL and before is True
    if named and method in PHYSICAL and before is None:
        caveats.append("pre_repair_unknown")
    if named and method in PHYSICAL and before is False:
        caveats.append("physical_confirmation_after_repair")
    if len({r["cause_id"] for r in rcs}) > 1:
        caveats.append("cause_revised")

    actions = list((rp or {}).get("actions") or [])
    real = [a for a in actions if a not in NOT_A_FIX]
    text_only = rp is not None and not actions and bool(rp.get("text"))
    made_repair = rp is not None and (bool(real) or text_only)
    if rp is not None and not made_repair:
        caveats.append("no_repair_made")
    if text_only:
        caveats.append("repair_text_only")
    if len(real) > 1:
        caveats.append("multi_action_repair")

    fixed = oc.get("fixed") if oc else None
    repair_confirmed = named and made_repair and fixed == "yes"
    if made_repair and fixed in ("no", "partial", "unknown"):
        caveats.append({"no": "repair_did_not_fix", "partial": "repair_partly_fixed", "unknown": "outcome_unknown"}[fixed])
    if fixed == "yes" and not made_repair:
        caveats.append("fixed_without_repair")
    if fixed == "yes" and not named:
        caveats.append("fixed_without_named_cause")

    recheck = _recheck_state(events)
    if fixed == "yes" and recheck["state"] == "still_wrong":
        caveats.append("recheck_contradicts_fix")
    recurred = sorted(w for w, r in followups.items() if r == "yes")
    clean = sorted(w for w, r in followups.items() if r == "no")
    caveats += [f"recurred_within_{w}_days" for w in recurred]
    stayed = repair_confirmed and bool(clean) and not recurred
    stayed_days = max(clean) if stayed else None

    level = 4 if stayed else 3 if repair_confirmed else 2 if physical else 1 if named else 0
    rungs = dict(suspected=named, physically_confirmed=physical, repair_confirmed=repair_confirmed, stayed_fixed=stayed)
    return dict(level=level, name=LEVEL_NAMES[level], rungs=rungs, stayed_fixed_days=stayed_days, caveats=caveats, recheck=recheck,
                lines=_lines(rc, named, physical, method, before, rp, made_repair, fixed, repair_confirmed, followups, recurred, clean, stayed, recheck["state"]))


def _lines(rc, named, physical, method, before, rp, made_repair, fixed, repair_confirmed, followups, recurred, clean, stayed, recheck_state=None) -> list[dict]:
    """One plain sentence per rung, for the technician: what the record shows, not a score of them."""
    how = {"observed_directly": "seeing it", "measured": "measuring it"}.get(method, "")

    if named:
        s1 = "A cause is named"
    elif rc is not None:
        s1 = "You couldn't determine the cause"
    else:
        s1 = "No cause named yet"

    if physical:
        s2 = f"Confirmed by {how} before the repair"
    elif not named:
        s2 = "Needs a cause first"
    elif method in PHYSICAL and before is None:
        s2 = f"You confirmed it by {how}, but not whether that was before the repair"
    elif method in PHYSICAL:
        s2 = f"You confirmed it by {how} only after the repair"
    elif method == "repair_fixed_it":
        s2 = "Confirmed by the repair working, not before it"
    elif method is None:
        s2 = "How it was confirmed isn't recorded"
    else:
        s2 = "Not confirmed by seeing or measuring it"

    if repair_confirmed:
        s3 = {"now_ok": "The repair fixed it, and the re-check agrees", "still_wrong": "Recorded as fixed, but the re-check says it's still wrong"
              }.get(recheck_state, "The repair fixed it")
    elif rp is None:
        s3 = "Fixed, but no repair was recorded" if fixed == "yes" else "No repair recorded yet"
    elif not made_repair:
        s3 = "No repair was made"
    elif fixed is None:
        s3 = "Not yet recorded whether it worked"
    else:
        s3 = {"no": "The repair did not fix it", "partial": "The repair only partly fixed it", "unknown": "Not known yet whether it worked",
              "yes": "Fixed, but needs a named cause"}[fixed]

    if stayed:
        days = max(clean)
        s4 = f"Still fixed at {days} days" + (" (the 30-day check is still to come)" if days == 7 and 30 not in followups else "")
    elif recurred:
        s4 = f"It came back within {recurred[0]} days"
    elif not repair_confirmed:
        s4 = "Needs a confirmed fix first"
    else:
        s4 = "Asked again 7 and 30 days after the fix"

    warn = (False, False, repair_confirmed and recheck_state == "still_wrong", False)         # the rung holds on the record, but something conflicts with it
    return [dict(rung=r, done=d, text=t, warn=w) for r, d, t, w in zip(
        RUNGS, (named, physical, repair_confirmed, stayed), (s1, s2, s3, s4), warn)]
