"""Pydantic request/response models, and the translator from the vision-extraction draft shape into the
flat building.json schema `docmismatch.troubleshoot.v1.data.load_building_v1` already loads unmodified.

The draft shape mirrors catalogue.py's existing CheckV1.point= keys (fan_status, static_pressure,
economizer_position, damper, airflow, reheat, status, temperature) -- those are themselves just
industry-standard HVAC/BAS terms, not anything that reveals the tool's reasoning. No cause names, weights,
or detection rates appear anywhere in this file or in what gets sent to the vision API (see
vision_extract.py's prompt) -- that mapping lives entirely in catalogue.py, server-side.
"""
from pydantic import BaseModel, Field

from .case_schema import CaseContext, Long, Reading, Short


class AhuPoints(BaseModel):
    fan_status: str | None = None
    static_pressure: str | None = None
    economizer_position: str | None = None


class BoxPoints(BaseModel):
    status: str | None = None
    airflow: str | None = None
    damper: str | None = None
    reheat: str | None = None


class AhuDraft(BaseModel):
    equipment_id: str
    points: AhuPoints = Field(default_factory=AhuPoints)


class BoxDraft(BaseModel):
    equipment_id: str
    serves_room: str
    points: BoxPoints = Field(default_factory=BoxPoints)
    zone_temperature_point: str | None = None


class BuildingDraft(BaseModel):
    """What the confirm screen shows and edits -- the technician-facing shape, not raw building.json."""
    ahu: AhuDraft
    boxes: list[BoxDraft]
    notes: str | None = None


def _non_empty(d: dict) -> dict:
    return {k: v for k, v in d.items() if v}


def draft_to_building_json(draft: BuildingDraft) -> dict:
    if not draft.boxes:
        raise ValueError("at least one box/zone is required")
    equipment = [{"id": draft.ahu.equipment_id, "kind": "AHU"}]
    vav_zone, ahu_vav, points = {}, {}, {}
    ahu_points = _non_empty(draft.ahu.points.model_dump())
    if ahu_points:
        points[draft.ahu.equipment_id] = ahu_points
    for box in draft.boxes:
        equipment.append({"id": box.equipment_id, "kind": "VAV"})
        equipment.append({"id": box.serves_room, "kind": "Zone"})
        vav_zone[box.serves_room] = box.equipment_id
        ahu_vav[box.equipment_id] = draft.ahu.equipment_id
        box_points = _non_empty(box.points.model_dump())
        if box_points:
            points[box.equipment_id] = box_points
        if box.zone_temperature_point:
            points[box.serves_room] = {"temperature": box.zone_temperature_point}
    building = {"equipment": equipment, "claims": {"vav_zone": vav_zone, "ahu_vav": ahu_vav}}
    if points:
        building["control_system"] = {"points": points}
    return building


class VerifyCodeRequest(BaseModel):
    code: str


class AnswerRequest(BaseModel):
    """`word` is the only thing the engine sees. The rest is recorded with the case and never forwarded:
    `reading_text` is free text ("0.8 in. w.c."), not the numeric `reading=` that Session.report() takes."""
    word: str | None = None                      # None only for a free-text ("external") check
    reading_text: Reading | None = None
    result_text: Short | None = None             # external check only
    minutes_correction: float | None = Field(default=None, ge=0, le=600)
    note: Long | None = None
    client_ts: str | None = None


class ConfirmIntakeRequest(BaseModel):
    draft: BuildingDraft
    room_ids: list[str]          # which of draft's boxes' serves_room ids are today's complaint(s)
    feel: str | None = None
    airflow: str | None = None
    context: CaseContext | None = None
