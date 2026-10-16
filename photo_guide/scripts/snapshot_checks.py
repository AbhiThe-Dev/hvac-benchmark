"""Build photo_guide/checks.json from the main check catalogue (read-only).

This is the ONLY place the prototype touches the main model, and only at build time: the app reads the JSON. Only each check's
one-line text, its family/place, its two answer words and (where the catalogue gives one) its normal-reading band are copied. Cause
names, response rates and notes are deliberately left out, so nothing about the diagnostic reasoning can reach the API.

Run:  .venv/bin/python photo_guide/scripts/snapshot_checks.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "doc_mismatch" / "src"))
from docmismatch.troubleshoot.v1.catalogue import CATALOGUE, ECON_CHECKS  # noqa: E402

OUT = ROOT / "photo_guide" / "checks.json"

# What can plausibly be photographed as the thing being worked on. BAS-screen checks (bas_*), asking people, and the v0 checks are left out.
# hazards -> fixed safety text in guide/prompt.py (never written by the model). photo_hint -> shown BEFORE the photo is taken.
PHOTO_CHECKS = {
    "power_24vac": dict(hazards=["electric"], photo_hint="Open-door view of the whole VAV box, with the round actuator motor and the small wire terminals both visible."),
    "control_signal": dict(hazards=["electric"], photo_hint="The actuator motor and the controller it is wired to, close enough that you can see the wire terminals."),
    "manual_damper_test": dict(hazards=["moving", "electric"], photo_hint="The actuator on the side of the box and the metal shaft it turns, plus the small release button or lever if you can see one."),
    "damper_linkage": dict(hazards=["moving"], photo_hint="The actuator, the shaft and the arm or clamp that connects them to the damper, from the side."),
    "controller_leds": dict(hazards=["height", "electric"], photo_hint="The small controller circuit board with its blinking lights, with the wiring and the label next to it."),
    "sensing_ports": dict(hazards=[], photo_hint="The round air-inlet of the box where the small plastic tubes and the little pressure sensor connect."),
    "flow_vs_gauge": dict(hazards=[], photo_hint="The controller and the small tubes or taps on the box inlet, and the gauge if you have one."),
    "k_factor": dict(hazards=[], photo_hint="The label or sticker on the box (nameplate), close enough to read the numbers."),
    "static_at_box": dict(hazards=[], photo_hint="The round inlet of the box where the air comes in, with a few feet of the duct in front of it."),
    "reheat_coil": dict(hazards=["hot", "electric"], photo_hint="The heating coil or electric heater section on the outlet side of the box, with the pipes, valve or wiring."),
    "ahu_visit": dict(hazards=["height", "moving", "electric"], photo_hint="The front of the air handler showing its main fan section, status lights, and any display or door label."),
    "ahu_gauge": dict(hazards=["height"], photo_hint="The pressure gauge or display on or near the air handler, close enough to read it."),
    "ahu_economizer_test": dict(hazards=["height", "moving", "electric"], photo_hint="The outside-air damper section of the air handler or rooftop unit, showing the damper blades and the actuator."),
    "diffuser_duct": dict(hazards=["height"], photo_hint="The ceiling vent (diffuser) and, if reachable, the flexible duct above it."),
    "thermostat": dict(hazards=[], photo_hint="The wall thermostat or room sensor with its screen or dial visible."),
    "flow_hood": dict(hazards=["height"], photo_hint="The ceiling vent (diffuser) you will put the flow hood on, and the space around it."),
}

# the catalogue text uses {box}, {t}, {m}, {ahu}; the prototype has no building, so the plainest generic nouns stand in
GENERIC = dict(box="the VAV box", t="the VAV box", m="the room", ahu="the air handler")


def reading_hint(c) -> dict | None:
    if c.reading is None:
        return None
    try:
        band = c.reading.band({})
    except Exception:  # noqa: BLE001  (a band that needs documented attributes)
        band = None
    out = {"quantity": c.reading.quantity, "unit": c.reading.unit}
    if band is not None:
        lo, hi = band
        out["normal_low"] = None if lo == float("-inf") else lo
        out["normal_high"] = None if hi == float("inf") else hi
    return out


def main() -> None:
    by_name = {c.name: c for c in CATALOGUE + ECON_CHECKS}
    missing = sorted(set(PHOTO_CHECKS) - set(by_name))
    if missing:
        raise SystemExit(f"not in the catalogue any more: {missing}")
    rows = []
    for name, extra in PHOTO_CHECKS.items():
        c = by_name[name]
        rows.append(dict(name=name, family=c.family, place=c.place, text=c.text.format(**GENERIC),
                         words=list(c.words), reading=reading_hint(c), **extra))
    OUT.write_text(json.dumps(rows, indent=2) + "\n")
    print(f"wrote {len(rows)} checks to {OUT}")


if __name__ == "__main__":
    main()
