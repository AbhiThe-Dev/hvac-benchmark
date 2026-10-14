"""What data a call-out has, and which checks that data lets the tool offer (working model v1).

DATA TIERS (explicit and selectable; a tier is a set of data items):
  T0  nothing but the technician's declaration that this is a VAV zone           -> no equipment list, no claims: no 'documented box is wrong' causes, generic targets
  T1  equipment list + the drawings' claims (this is v0's input)                  -> named boxes, candidates for a wrong claim, which air handler serves the box
  T2  T1 + attributes / design values (reheat type, K-factor, design airflow ...) -> expected values for readings, reheat known, design-load check possible
  T3  T2 + control-system access and a point map                                  -> control-system reads cost minutes, not a walk
  T4  T3 + trends                                                                 -> a label only: the trend layer is deliberately not built here (see active/ for that)

A check declares what it NEEDS (`Need(item, fallback_min)`): if the item is missing, `fallback_min` extra minutes make up for it (e.g. a control-system read takes 2 minutes with a
point map and 10 without); `None` means the check cannot be offered without it. Some items can be met by the technician: 'I can get into the control system', 'I have a gauge',
'someone is in the room', 'the box has reheat' (`Context`, declared as a tap and only asked when it decides whether the best check can be offered).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

from ..building import Building, load_building

ITEMS = ("equipment_list", "claims", "attributes", "bas_access", "point_map", "trends")
_T1 = frozenset({"equipment_list", "claims"})
_T2 = _T1 | {"attributes"}
_T3 = _T2 | {"bas_access", "point_map"}
TIERS: dict[str, frozenset] = {"T0": frozenset(), "T1": _T1, "T2": _T2, "T3": _T3, "T4": _T3 | {"trends"}}
TIER_TEXT = {"T0": "nothing but the declared equipment type", "T1": "equipment list + the drawings' claims (v0's input)", "T2": "T1 + attributes and design values",
             "T3": "T2 + control-system access and a point map", "T4": "T3 + trends (label only: no trend layer is built)"}


def tier_items(tier: str | frozenset | set) -> frozenset:
    """The data items of a named tier, or of an explicit set of items (used for study arms such as 'T2 plus control-system access but no point map')."""
    if isinstance(tier, str):
        if tier not in TIERS:
            raise ValueError(f"tier must be one of {sorted(TIERS)}, not {tier!r}")
        return TIERS[tier]
    items = frozenset(tier)
    if not items <= set(ITEMS):
        raise ValueError(f"unknown data items {sorted(items - set(ITEMS))}")
    return items


# ---------------------------------------------------------------------------------------------- the building, with attributes and a point map
ATTRIBUTE_KEYS = {"reheat": ("none", "hydronic", "electric"), "pressure_independent": (True, False), "k_factor": "positive number", "design_airflow_cfm": "positive number",
                  "inlet_diameter_in": "positive number", "static_setpoint_inwc": "positive number"}


@dataclass
class Building1:
    """A v0 `Building` (equipment list and claims) plus, per piece of equipment, optional attributes and control-system point names. Both are optional."""
    base: Building
    attrs: dict[str, dict]
    points: dict[str, dict[str, str]]

    @property
    def name(self) -> str:
        return self.base.name

    def label(self, eid: str) -> str:
        return self.base.label(eid)

    def point(self, eid: str, what: str) -> str | None:
        return self.points.get(eid, {}).get(what)


def _check_attrs(eid: str, a: dict) -> dict:
    for k, v in a.items():
        if k not in ATTRIBUTE_KEYS:
            raise ValueError(f"{eid}: unknown attribute {k!r}; known: {sorted(ATTRIBUTE_KEYS)}")
        allowed = ATTRIBUTE_KEYS[k]
        if isinstance(allowed, tuple):
            if v not in allowed:
                raise ValueError(f"{eid}: attribute {k!r} must be one of {allowed}, not {v!r}")
        elif isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0:
            raise ValueError(f"{eid}: attribute {k!r} must be a positive number, not {v!r}")
    return dict(a)


def load_building_v1(path: str | Path) -> Building1:
    """v0's JSON, plus an optional `attributes` object on each equipment entry and an optional `control_system: {"points": {equipment id: {what: point name}}}`.
    A v0 file loads as it is (no attributes, no points)."""
    d = json.loads(Path(path).read_text())
    base = load_building(path)
    attrs = {e["id"]: _check_attrs(e["id"], e["attributes"]) for e in d["equipment"] if e.get("attributes")}
    points = {eid: dict(p) for eid, p in d.get("control_system", {}).get("points", {}).items()}
    for eid in points:
        if eid not in base.equipment:
            raise ValueError(f"control_system point map names {eid!r}, which is not in the equipment list")
    return Building1(base, attrs, points)


# ---------------------------------------------------------------------------------------------- what the technician can declare
CONTEXT_KEYS = ("reheat", "bas_access", "instrument", "occupant")
QUESTIONS = {
    "reheat": "Does this box have a reheat coil or an electric heater?",
    "bas_access": "Can you get into the building control system for this box and its air handler?",
    "instrument": "Do you have a flow hood or a differential-pressure gauge with you?",
    "occupant": "Is someone in the room who can answer a few questions?",
}
ASK_KEY = {"feature:reheat": "reheat", "bas_access": "bas_access", "instrument": "instrument", "occupant": "occupant"}


@dataclass(frozen=True)
class Context:
    """Facts the technician declares ('yes' / 'no'; None = not declared). Each declaration is one entry, like a symptom. A declared fact overrides the tier's (a technician who says
    they cannot get into the control system today is believed even at T3)."""
    reheat: str | None = None
    bas_access: str | None = None
    instrument: str | None = None
    occupant: str | None = None

    def __post_init__(self):
        for k in CONTEXT_KEYS:
            if getattr(self, k) not in (None, "yes", "no"):
                raise ValueError(f"context {k!r} must be 'yes', 'no' or None, not {getattr(self, k)!r}")

    def declare(self, key: str, value: str) -> "Context":
        if key not in CONTEXT_KEYS:
            raise KeyError(f"unknown context item {key!r}; known: {CONTEXT_KEYS}")
        return replace(self, **{key: value})


def _declared(v: str | None) -> bool | None:
    return None if v is None else v == "yes"


# ---------------------------------------------------------------------------------------------- availability of a check
@dataclass(frozen=True)
class Need:
    item: str                        # an item of ITEMS, 'attr:<key>' (a documented attribute), 'instrument', 'occupant' or 'feature:reheat' / 'feature:pressure_independent'
    fallback_min: float | None = None    # extra minutes when it is missing; None = the check cannot be done without it


@dataclass(frozen=True)
class Avail:
    state: str                       # "offered" | "fallback" (offered at extra cost) | "askable" (offered if the technician declares `ask`) | "unavailable"
    extra_min: float = 0.0
    ask: tuple = ()
    missing: tuple = ()


class DataView:
    """The data and declared context of one call-out, answering 'do we have this item?' (True / False / None = not yet declared)."""

    def __init__(self, items: frozenset, building: Building1 | None, ctx: Context):
        self.items, self.building, self.ctx = items, building, ctx

    def attr(self, key: str, eq: str | None):
        if "attributes" in self.items and self.building is not None and eq is not None:
            return self.building.attrs.get(eq, {}).get(key)
        return None

    def have(self, item: str, eq: str | None = None) -> bool | None:
        if item in ("equipment_list", "claims", "attributes", "trends"):
            return item in self.items
        if item == "point_map":
            return "point_map" in self.items and self.building is not None and eq is not None and bool(self.building.points.get(eq))
        if item.startswith("attr:"):
            return self.attr(item[5:], eq) is not None
        if item == "bas_access":
            d = _declared(self.ctx.bas_access)
            return (True if "bas_access" in self.items else None) if d is None else d      # not on the tier and not declared: unknown, so worth asking
        if item in ("instrument", "occupant"):
            return _declared(getattr(self.ctx, item))
        if item == "feature:reheat":
            d = _declared(self.ctx.reheat)
            if d is not None:
                return d
            r = self.attr("reheat", eq)
            return None if r is None else r != "none"
        if item == "feature:pressure_independent":
            p = self.attr("pressure_independent", eq)
            return True if p is None else bool(p)
        raise KeyError(f"unknown need {item!r}")


def availability(check, view: DataView, eq: str | None) -> Avail:
    """Whether `check` (anything with `.needs` and `.feature`) can be offered now, and at what extra cost. `eq` = the equipment whose attributes / points the check uses."""
    needs = list(check.needs) + ([Need(f"feature:{check.feature}", None)] if check.feature else [])
    extra, ask = 0.0, []
    for n in needs:
        h = view.have(n.item, eq)
        if h is True:
            continue
        if n.fallback_min is not None:
            extra += n.fallback_min
        elif h is None and n.item in ASK_KEY:
            ask.append(ASK_KEY[n.item])
        else:
            return Avail("unavailable", 0.0, (), (n.item,))
    if ask:
        return Avail("askable", extra, tuple(ask))
    return Avail("fallback" if extra > 0 else "offered", extra)
