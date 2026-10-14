"""Request models for the diagnostic case record (see DATA.md). Every chip field is a Literal so a bad value is
rejected at the API edge, before anything is written. Cause ids are NOT enumerated here: they come from the
engine's taxonomy (causes.py) and are validated in cases.py, which keeps this file free of engine imports.

Numeric readings are free text with a unit ("0.8 in. w.c.") and are only ever stored -- never forwarded to
`Session.report(reading=)`, which raises for checks that take no numeric reading (see routes_visit.py's note).
"""
from typing import Annotated, Literal

from pydantic import BaseModel, Field

Short = Annotated[str, Field(max_length=200)]
SqlId = Annotated[int, Field(ge=1, le=2**63 - 1)]       # an id that arrives from outside must fit SQLite's INTEGER, or a lookup raises instead of answering 'not found'
Long = Annotated[str, Field(max_length=2000)]
Reading = Annotated[str, Field(max_length=40)]

ComplaintSource = Literal["occupant", "tenant_or_manager", "bas_alarm", "routine_round", "other"]
BuildingType = Literal["office", "retail", "school", "healthcare", "lab", "industrial", "residential", "other"]
SystemKind = Literal["vav_hot_water_reheat", "vav_electric_reheat", "vav_cooling_only", "other", "unknown"]
EquipmentAge = Literal["lt5", "5to10", "10to20", "gt20", "unknown"]

DecisionAction = Literal["follow", "substitute", "external", "skip"]
Reason = Literal["already_known", "cannot_do_now", "not_relevant", "prefer_other_first", "other"]
HowConfirmed = Literal["observed_directly", "measured", "repair_fixed_it", "ruled_out_others", "other_tech_or_vendor", "not_confirmed"]
RepairAction = Literal["replaced_part", "adjusted_or_reset", "reconfigured_controls", "cleaned_or_cleared", "repaired_wiring",
                       "corrected_documentation", "no_repair_needed", "deferred_or_referred", "other"]
Fixed = Literal["yes", "no", "partial", "unknown"]


class Readings(BaseModel):
    zone_temp: Reading | None = None
    zone_setpoint: Reading | None = None
    airflow: Reading | None = None
    airflow_setpoint: Reading | None = None
    damper_position: Reading | None = None
    duct_static: Reading | None = None
    discharge_temp: Reading | None = None
    other: Short | None = None


class CaseContext(BaseModel):
    """Entered once on the confirm screen, before any tool output is shown. Every field is optional."""
    complaint_text: Long | None = None
    complaint_source: ComplaintSource | None = None
    building_type: BuildingType | None = None
    system_kind: SystemKind | None = None
    equipment_age_band: EquipmentAge | None = None
    readings: Readings | None = None
    alarms_text: Long | None = None
    own_hypotheses: list[str] = Field(default_factory=list, max_length=12)     # causes.GROUPS keys, checked in cases.py
    own_hypotheses_text: Short | None = None
    prior_case_id: SqlId | None = None                                           # "this is a return visit for ..."


class ProfileRequest(BaseModel):
    role: Literal["contractor_tech", "in_house_engineer", "other"]
    years_band: Literal["lt2", "2to5", "5to15", "gt15"]
    vav_band: Literal["none", "some", "daily"]
    ack: Literal[True]                                                          # the notice was shown and acknowledged


class IntentRequest(BaseModel):
    """What the technician would check next, recorded BEFORE the suggestion is shown."""
    kind: Literal["check", "other", "unsure"]
    check: str | None = None
    target: str | None = None
    text: Short | None = None
    client_ts: str | None = None


class DecisionRequest(BaseModel):
    action: DecisionAction
    check: str | None = None          # substitute only
    target: str | None = None
    external_text: Short | None = None        # external only: a check that is not in the catalogue
    reason: Reason | None = None
    note: Long | None = None
    client_ts: str | None = None


class RootCauseRequest(BaseModel):
    cause_id: str                     # taxonomy id | documentation_wrong | other | not_determined
    text: Short | None = None         # required when cause_id == "other"
    how_confirmed: HowConfirmed | None = None
    confirmed_before_repair: bool | None = None      # only meaningful for "saw it" / "measured it"; see cases.record_root_cause
    actual_box: Short | None = None                  # only when the drawings were wrong: the box that really serves the room, or not_listed / not_sure
    client_ts: str | None = None


class RepairRequest(BaseModel):
    actions: list[RepairAction] = Field(default_factory=list, max_length=9)
    text: Long | None = None
    repaired_on: Annotated[str, Field(max_length=10)] | None = None            # YYYY-MM-DD
    client_ts: str | None = None


class OutcomeRequest(BaseModel):
    fixed: Fixed
    note: Long | None = None
    client_ts: str | None = None


class FollowupRequest(BaseModel):
    window_days: Literal[7, 30]
    recurred: Literal["yes", "no", "unsure"]
    note: Long | None = None
    client_ts: str | None = None


class RecheckRequest(BaseModel):
    """After the repair: the test that found the fault, repeated. `of_event_id` is the original check_result."""
    of_event_id: SqlId
    result: Literal["now_ok", "still_wrong", "unsure"]
    reading_text: Reading | None = None
    note: Long | None = None
    client_ts: str | None = None


class AdvanceRequest(BaseModel):
    """Which room the caller is leaving. Optional, but the frontend always sends it: it is what makes a double tap harmless."""
    from_room: Annotated[int, Field(ge=0, le=10_000)] | None = None
