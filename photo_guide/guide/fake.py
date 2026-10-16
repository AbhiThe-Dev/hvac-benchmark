"""Canned guidance for exercising the UI and the renderer without an API key (server.py --fake). NOT model output: the marks land on a fixed
place in whatever photo is sent, so use it to check the screens, never to judge accuracy."""
from .schema import Guidance, parse_guidance


def fake_guidance(check: dict, image, note: str = "") -> Guidance:
    return parse_guidance({
        "can_help": True,
        "what_i_see": "(canned demo answer, not from the model)",
        "tools_needed": ["a multimeter (the meter with the dial)"],
        "steps": [
            {"instruction": "Turn the meter dial to AC volts, the V with a wavy line.", "label": "", "target": None, "look_for": "The screen shows V with a wavy line.", "if_stuck": "Look for the wavy line next to the V on the dial."},
            {"instruction": "Find the main part in the middle of the photo.", "label": "Main part", "target": {"kind": "box", "coords": [300, 300, 700, 700]}, "look_for": "A boxy part with wires.", "if_stuck": "Step back and retake the photo."},
            {"instruction": "Touch the red probe to the small spot marked here.", "label": "Terminal", "target": {"kind": "point", "coords": [500, 500]}, "look_for": "A number on the meter screen.", "if_stuck": "Ask someone to point it out."},
        ],
        "normal_looks_like": "Between 22 and 26 volts.",
        "abnormal_looks_like": "Zero, or outside 22 to 26.",
    })
