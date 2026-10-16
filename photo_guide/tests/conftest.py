import io
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from guide.schema import Guidance  # noqa: E402


@pytest.fixture
def photo_bytes():
    img = Image.new("RGB", (1200, 800), (90, 100, 110))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def sample_raw():
    """What the model might return: a point, a box, and a step with no marked place."""
    return {
        "can_help": True,
        "what_i_see": "A VAV box with its cover off and a small actuator on the side.",
        "tools_needed": ["a multimeter (the meter with the dial)"],
        "steps": [
            {"instruction": "Turn the meter dial to AC volts, the V with a wavy line.", "label": "", "target": None},
            {"instruction": "Find the small black motor on the left side of the box.", "label": "Actuator", "target": {"kind": "box", "coords": [100, 300, 400, 600]}},
            {"instruction": "Touch the red probe to the terminal marked 24V.", "label": "24V terminal", "target": {"kind": "point", "coords": [250, 450]},
             "look_for": "A number near 24.", "if_stuck": "Ask someone to point it out."},
        ],
        "normal_looks_like": "Between 22 and 26 volts.",
        "abnormal_looks_like": "Zero, or outside 22 to 26.",
    }


@pytest.fixture
def sample(sample_raw):
    return Guidance.model_validate(sample_raw)
