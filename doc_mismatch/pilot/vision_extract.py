"""Two on-site photos -> a BuildingDraft, via Anthropic's vision API with forced tool-use so the output is
schema-constrained JSON, never free text to parse.

The prompt is deliberately domain-vocabulary only -- standard HVAC/BAS terms (the same ones PNNL's own AFDD
guides use), nothing about this tool's cause tree, detection rates, or reasoning. That mapping (which point
feeds which check, with what reliability) lives entirely in catalogue.py and is never sent to the API. This
was a deliberate, carefully-reasoned decision from the pilot's design discussion -- preserve it exactly; do
not add cause names, weights, or "why we need this point" language to PROMPT or TOOL_SCHEMA below.
"""
import base64
import io
import json
from dataclasses import dataclass

from anthropic import Anthropic
from PIL import Image, ImageOps

from . import config
from .schema import BuildingDraft

MODEL = "claude-haiku-4-5-20251001"   # claude-sonnet-5-5/claude-opus-5-5 reject forced tool_choice ("type":"tool") as of this SDK; Haiku 4.5 supports it and is vision-capable
MAX_SIDE_PX = 1568          # Anthropic's own long-edge recommendation for vision inputs
JPEG_QUALITY = 85

PROMPT = (
    "You are helping a field HVAC technician record what is visible on two photos: (1) a building-automation-system "
    "(BAS) screen for one air handling unit (AHU) and the VAV box(es)/zone(s) it serves, and (2) an equipment "
    "nameplate, riser diagram, or as-built drawing showing equipment IDs and which VAV box serves which room. "
    "From the photos, extract only what is visible, using standard HVAC/BAS terminology, and do not guess anything "
    "not shown. Record: the AHU's equipment ID; each VAV box's equipment ID and which room/zone it serves; which "
    "AHU feeds each box; and, where visible, the on-screen label of each point: for the AHU -- supply fan status, "
    "duct static pressure, outdoor-air (economizer) damper position; for each VAV box -- damper position, airflow, "
    "reheat valve/stage command, controller/zone status; for each room -- its temperature point. Leave a field "
    "blank rather than guessing if it isn't clearly visible, and note anything illegible or ambiguous in `notes`."
)

TOOL_NAME = "record_building"
TOOL_SCHEMA = {
    "name": TOOL_NAME,
    "description": "Record the AHU, VAV boxes/zones, and BAS point labels visible in the two photos.",
    "input_schema": {
        "type": "object",
        "properties": {
            "ahu": {
                "type": "object",
                "properties": {
                    "equipment_id": {"type": "string"},
                    "points": {
                        "type": "object",
                        "properties": {
                            "fan_status": {"type": "string"},
                            "static_pressure": {"type": "string"},
                            "economizer_position": {"type": "string"},
                        },
                    },
                },
                "required": ["equipment_id"],
            },
            "boxes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "equipment_id": {"type": "string"},
                        "serves_room": {"type": "string"},
                        "points": {
                            "type": "object",
                            "properties": {
                                "status": {"type": "string"},
                                "airflow": {"type": "string"},
                                "damper": {"type": "string"},
                                "reheat": {"type": "string"},
                            },
                        },
                        "zone_temperature_point": {"type": "string"},
                    },
                    "required": ["equipment_id", "serves_room"],
                },
            },
            "notes": {"type": "string", "description": "Anything illegible, ambiguous, or not visible."},
        },
        "required": ["ahu", "boxes"],
    },
}


@dataclass
class PreparedImage:
    media_type: str
    base64_data: str


def preprocess_image(raw_bytes: bytes) -> PreparedImage:
    """Resize to a sane upload size and strip metadata (EXIF, including GPS) -- re-encoding via Pillow without
    passing exif= already drops it; we never read or forward the original file's metadata."""
    img = Image.open(io.BytesIO(raw_bytes))
    img = ImageOps.exif_transpose(img)          # apply orientation before dropping the EXIF that encoded it
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.thumbnail((MAX_SIDE_PX, MAX_SIDE_PX), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY)
    return PreparedImage(media_type="image/jpeg", base64_data=base64.b64encode(buf.getvalue()).decode("ascii"))


def _image_block(img: PreparedImage) -> dict:
    return {"type": "image", "source": {"type": "base64", "media_type": img.media_type, "data": img.base64_data}}


def extract_building(bas_photo: bytes, equipment_photo: bytes) -> tuple[BuildingDraft, str]:
    """Returns (draft, raw_tool_input_json_str) for the caller to show on the confirm screen and persist."""
    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    bas_img = preprocess_image(bas_photo)
    equip_img = preprocess_image(equipment_photo)
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        tools=[TOOL_SCHEMA],
        tool_choice={"type": "tool", "name": TOOL_NAME},
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT},
                _image_block(bas_img),
                _image_block(equip_img),
            ],
        }],
    )
    tool_use = next(b for b in response.content if b.type == "tool_use")
    draft = BuildingDraft.model_validate(tool_use.input)
    return draft, json.dumps(tool_use.input)
