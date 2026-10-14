"""System topology for one case: what the drawings claim, what was found out about whether they are right, and what the
building file says exists to measure with. Pure functions of the confirmed building file and the case's events: no server,
no engine, so the offline export can use it. Nothing here is asked of the technician, with ONE exception recorded elsewhere
(`root_cause.actual_box`, asked only when the drawings were wrong).

What is NOT here, because the building file does not have it and technicians rarely know it: duct branches and which boxes
share one, upstream/downstream order along a trunk, the plant, where the static-pressure sensor sits. The file holds exactly
AHU -> VAV box -> room claims plus which BAS points were read off the photo.

The counts are of what was photographed or confirmed on the confirm screen ("seen"), NOT a survey of the air handler: an AHU
serving 20 boxes shows however many boxes were in the photo.
"""

TRACE = "duct_trace"                                    # DIRECT: follow the duct from the diffuser back to its box
ACT = ("override_room", "override_diffuser")            # INDIRECT: command a box and watch the room (a "no" can just be a dead actuator)
SENTINELS = ("not_listed", "not_sure")                  # the technician's answers when the real box is not one of the known ones


def _latest(events: list[dict], kind: str) -> dict | None:
    return next((e["payload"] for e in reversed(events) if e["kind"] == kind), None)


def building_view(building: dict, room: str) -> dict:
    """The drawings' claim for one room (`room` is the zone id), and what exists around it, from the confirmed building file."""
    claims = building.get("claims") or {}
    vav_zone, ahu_vav = claims.get("vav_zone") or {}, claims.get("ahu_vav") or {}
    box = vav_zone.get(room)
    ahu = ahu_vav.get(box) if box else None
    points = (building.get("control_system") or {}).get("points") or {}
    present = lambda eid: sorted(k for k, v in (points.get(eid) or {}).items() if v)          # noqa: E731
    boxes = sorted(b for b, a in ahu_vav.items() if ahu is not None and a == ahu)
    rooms = sorted(z for z, b in vav_zone.items() if b in boxes)
    box_points = present(box) if box else []
    return dict(ahu=ahu, box=box, room=room, boxes_on_ahu_seen=boxes, rooms_on_ahu_seen=rooms, n_boxes_on_ahu_seen=len(boxes),
                n_rooms_on_ahu_seen=len(rooms), ahu_points=present(ahu) if ahu else [], box_points=box_points,
                zone_temperature_point=bool((points.get(room) or {}).get("temperature")), reheat_point="reheat" in box_points)


def candidate_boxes(building: dict) -> list[str]:
    return [e["id"] for e in building.get("equipment", []) if e.get("kind") == "VAV"]


def evidence(events: list[dict]) -> list[dict]:
    """What the checks that bear on "which box serves this room" said. `duct_trace` is a direct test of the layout. The two
    commanding checks are indirect: a "yes" is good evidence the box serves the room, but a "no" is INCONCLUSIVE (the actuator
    may simply be dead). 'unsure'/'skip' are not evidence."""
    out = []
    for e in events:
        p = e["payload"]
        if e["kind"] != "check_result" or p.get("check") not in (TRACE, *ACT) or p.get("word") not in ("yes", "no"):
            continue
        direct = p["check"] == TRACE
        reading = "serves_room" if p["word"] == "yes" else ("not_this_box" if direct else "inconclusive")
        out.append(dict(check=p["check"], target=p["target"], word=p["word"], direct=direct, reading=reading))
    return out


def verified(events: list[dict], documented_box: str | None) -> dict:
    """Were the drawings right for this room? `status`: wrong / right / suspected_wrong / unverified, with the `basis`.
    Never inferred from an unrelated root cause: confirming a failed actuator does not prove the drawings were right.
    The technician's own "the drawings were wrong" outranks a trace; a disagreement between them is flagged, not hidden."""
    rc, tool = _latest(events, "root_cause"), _latest(events, "tool_conclusion")
    traces = {}
    for e in evidence(events):
        if e["check"] == TRACE:
            traces[e["target"]] = e["word"]                                         # the latest trace per box wins
    traced_here = traces.get(documented_box)
    traced_elsewhere = next((t for t, w in traces.items() if t != documented_box and w == "yes"), None)

    tool_claim = None
    if tool and tool.get("id") == "documentation_wrong":
        cause = tool.get("cause") or []
        tool_claim = dict(box=cause[1] if len(cause) > 1 else "not_listed")

    tech_wrong = rc is not None and rc["cause_id"] == "documentation_wrong"
    actual, status, basis = None, "unverified", None
    if tech_wrong:
        status, basis, actual = "wrong", "technician", rc.get("actual_box") or traced_elsewhere
    elif traced_here == "no":
        status, basis, actual = "wrong", "duct_trace", traced_elsewhere
    elif traced_here == "yes":
        status, basis = "right", "duct_trace"
    elif traced_elsewhere:
        status, basis, actual = "wrong", "duct_trace", traced_elsewhere
    elif tool_claim:
        status, basis = "suspected_wrong", "tool"
    conflict = bool(tech_wrong and traced_here == "yes")
    return dict(status=status, basis=basis, actual_box=actual, conflict=conflict, tool_claim=tool_claim)


def build(building: dict, room: str, events: list[dict], system_kind: str | None, visit_rooms: list[str] | None = None) -> dict:
    doc = building_view(building, room)
    # how many of THIS visit's complaint rooms hang off the same air handler (the shared-cause situation), counting this one
    doc["visit_rooms_on_same_ahu"] = sum(1 for z in (visit_rooms or [room]) if building_view(building, z)["ahu"] == doc["ahu"])
    answers = [e["payload"]["answer"] for e in events if e["kind"] == "question_answer" and e["payload"].get("key") == "reheat"]
    return dict(documented=doc, reheat=dict(declared=answers[-1] if answers else None, system_kind=system_kind, reheat_point_documented=doc["reheat_point"]),
                evidence=evidence(events), verified=verified(events, doc["box"]))
