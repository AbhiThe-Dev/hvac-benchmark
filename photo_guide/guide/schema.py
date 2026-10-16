"""The shape of what the model must return, and a strict check of it. Coordinates are on a 0-1000 grid over the photo (x left to right,
y top to bottom), whatever the photo's pixel size, so the renderer and the UI never depend on the resize."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

GRID = 1000
MAX_STEPS = 7
MIN_BOX = 20          # a box thinner than this (grid units) is widened so it can be seen


class GuideError(ValueError):
    """The model's answer cannot be used (malformed, or says it can help but gives no steps)."""


class Target(BaseModel):
    kind: Literal["point", "box"]
    coords: list[float]

    @model_validator(mode="after")
    def _shape(self):
        want = 2 if self.kind == "point" else 4
        if len(self.coords) != want:
            raise ValueError(f"a {self.kind} needs {want} numbers, got {len(self.coords)}")
        c = [min(max(v, 0.0), float(GRID)) for v in self.coords]
        if self.kind == "box":
            x0, y0, x1, y1 = c
            x0, x1 = sorted((x0, x1))
            y0, y1 = sorted((y0, y1))
            if x1 - x0 < MIN_BOX:
                x0, x1 = max(0.0, x0 - MIN_BOX / 2), min(float(GRID), x1 + MIN_BOX / 2)
            if y1 - y0 < MIN_BOX:
                y0, y1 = max(0.0, y0 - MIN_BOX / 2), min(float(GRID), y1 + MIN_BOX / 2)
            c = [x0, y0, x1, y1]
        self.coords = c
        return self


class Step(BaseModel):
    instruction: str = Field(min_length=3)
    label: str = ""                      # short name for the marked part, drawn on the photo
    target: Target | None = None         # None: a step about something that is not in this photo
    look_for: str = ""
    if_stuck: str = ""

    @field_validator("label", "look_for", "if_stuck", mode="before")
    @classmethod
    def _none_is_empty(cls, v):
        return "" if v is None else v      # the model sometimes sends null for 'nothing to say'

    @field_validator("instruction", "label", "look_for", "if_stuck")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


class Guidance(BaseModel):
    can_help: bool
    what_i_see: str = ""
    retake_hint: str = ""
    stop: bool = False
    stop_reason: str = ""
    tools_needed: list[str] = []
    steps: list[Step] = []
    normal_looks_like: str = ""
    abnormal_looks_like: str = ""

    @field_validator("what_i_see", "retake_hint", "stop_reason", "normal_looks_like", "abnormal_looks_like", mode="before")
    @classmethod
    def _none_is_empty(cls, v):
        # None, or stray punctuation like '","' (seen from the model on an unused field), means 'nothing'
        return "" if v is None or (isinstance(v, str) and not any(c.isalnum() for c in v)) else v

    @field_validator("tools_needed", "steps", mode="before")
    @classmethod
    def _none_is_empty_list(cls, v):
        return [] if v is None else v

    @model_validator(mode="after")
    def _consistent(self):
        if self.stop:
            self.steps = []              # a stop means: give no steps at all
            self.can_help = False
        elif self.can_help and not self.steps:
            raise ValueError("can_help is true but there are no steps")
        elif not self.can_help and not self.retake_hint:
            self.retake_hint = "I could not tell what this is. Take another photo that shows the whole part, in good light."
        self.steps = self.steps[:MAX_STEPS]
        return self


TOOL_NAME = "record_guidance"

_TARGET = {
    "type": ["object", "null"],
    "description": "Where this step happens in the photo. null if the step is not about anything visible in the photo (for example 'set your meter dial').",
    "properties": {
        "kind": {"type": "string", "enum": ["point", "box"], "description": "'point' for a small thing (a terminal, a light, a button); 'box' for a larger part."},
        "coords": {"type": "array", "items": {"type": "number"},
                   "description": "In PIXELS of the photo exactly as you see it (its width and height are stated in the message): x counts from the left edge, y from the top edge. A point: [x, y]. A box: [x_left, y_top, x_right, y_bottom]."},
    },
    "required": ["kind", "coords"],
}

TOOL_SCHEMA = {
    "name": TOOL_NAME,
    "description": "Record the step-by-step guidance for this one check, with where each step happens in the photo.",
    "input_schema": {
        "type": "object",
        "properties": {
            "can_help": {"type": "boolean", "description": "True if the photo shows enough of the right equipment to guide the check."},
            "what_i_see": {"type": "string", "description": "One plain sentence: what the photo shows."},
            "retake_hint": {"type": "string", "description": "If can_help is false: exactly what to photograph instead, in plain words. Otherwise empty."},
            "stop": {"type": "boolean", "description": "True ONLY if the photo shows something that makes it unsafe for a beginner to continue (exposed live wiring, damaged equipment, burning smell evidence, an unsafe working position)."},
            "stop_reason": {"type": "string", "description": "If stop is true: one plain sentence saying what is unsafe and to ask a qualified person. Otherwise empty."},
            "tools_needed": {"type": "array", "items": {"type": "string"}, "description": "Plain-word list of tools/things needed (e.g. 'a multimeter (the meter with the dial)')."},
            "steps": {
                "type": "array",
                "description": "3 to 7 steps, in order, one action each.",
                "items": {
                    "type": "object",
                    "properties": {
                        "instruction": {"type": "string", "description": "One action, at most 20 words, plain words."},
                        "label": {"type": "string", "description": "1-3 words naming the marked part, shown on the photo."},
                        "target": _TARGET,
                        "look_for": {"type": "string", "description": "What the person should see or read after this step."},
                        "if_stuck": {"type": "string", "description": "What to do if they cannot find it or it looks different."},
                    },
                    "required": ["instruction"],
                },
            },
            "normal_looks_like": {"type": "string", "description": "What a normal result looks like for this check, in plain words (include the number range if the check has one)."},
            "abnormal_looks_like": {"type": "string", "description": "What an abnormal result looks like, in plain words."},
        },
        "required": ["can_help", "what_i_see"],
    },
}


def pixels_to_grid(raw: dict, width: int, height: int) -> dict:
    """The model marks in pixels of the photo it was shown (that is how it localises, as the first eval showed: the grid protocol drew
    marks in the wrong place); everything downstream uses the 0-1000 grid, so convert BEFORE validation (which clamps to the grid).
    Anything that is not a well-formed target is left untouched for the validator to reject."""
    out = dict(raw)
    steps = []
    for s in raw.get("steps") or []:
        s = dict(s) if isinstance(s, dict) else s
        t = s.get("target") if isinstance(s, dict) else None
        if isinstance(t, dict) and isinstance(t.get("coords"), list) and all(isinstance(v, (int, float)) for v in t["coords"]):
            s["target"] = {**t, "coords": [v / (width if i % 2 == 0 else height) * GRID for i, v in enumerate(t["coords"])]}
        steps.append(s)
    if "steps" in raw:
        out["steps"] = steps
    return out


def parse_guidance(raw: dict) -> Guidance:
    try:
        return Guidance.model_validate(raw)
    except Exception as e:  # noqa: BLE001 (pydantic ValidationError and friends)
        raise GuideError(str(e)) from e
