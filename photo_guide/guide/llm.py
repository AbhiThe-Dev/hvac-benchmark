"""The model call. One forced single-tool request; the answer is validated and, if malformed, asked for once more."""
from __future__ import annotations

import base64
import os
from pathlib import Path

from dotenv import load_dotenv

from .image import to_jpeg
from .prompt import SYSTEM, user_text
from .schema import TOOL_NAME, TOOL_SCHEMA, GuideError, Guidance, parse_guidance, pixels_to_grid

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DEFAULT_MODEL = "claude-haiku-4-5-20251001"     # proven here with tool use + vision (pilot/vision_extract.py); override with GUIDE_MODEL
MAX_TOKENS = 3000
_NO_FORCE: dict[str, dict] = {}                 # model -> tool_choice learned at run time


def model_name() -> str:
    return os.environ.get("GUIDE_MODEL", DEFAULT_MODEL)


def _client():
    from anthropic import Anthropic
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set (put it in photo_guide/.env or export it)")
    return Anthropic(api_key=key)


def request_guidance(check: dict, image, note: str = "", client=None, model: str | None = None) -> Guidance:
    """`image` is a PIL image from image.preprocess. `client` is injectable for tests (anything with .messages.create)."""
    client = client or _client()
    b64 = base64.b64encode(to_jpeg(image)).decode("ascii")
    messages = [{"role": "user", "content": [
        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
        {"type": "text", "text": user_text(check, note, image.size)},
    ]}]
    last: Exception | None = None
    choice = _NO_FORCE.get(model or model_name(), {"type": "any"})   # one tool only, so 'any' forces it
    for _ in range(2):
        try:
            resp = client.messages.create(model=model or model_name(), max_tokens=MAX_TOKENS, system=SYSTEM, tools=[TOOL_SCHEMA], tool_choice=choice, messages=messages)
        except Exception as e:  # noqa: BLE001
            if choice["type"] != "auto" and "tool_choice" in str(e):
                # claude-sonnet-5-5 rejects forced tool use ('tool' and 'any'): fall back to 'auto'; the prompt says to reply only via the tool, and a reply without it is retried below
                choice = _NO_FORCE[model or model_name()] = {"type": "auto"}
                resp = client.messages.create(model=model or model_name(), max_tokens=MAX_TOKENS, system=SYSTEM, tools=[TOOL_SCHEMA], tool_choice=choice, messages=messages)
            else:
                raise
        use = next((b for b in resp.content if getattr(b, "type", "") == "tool_use" and b.name == TOOL_NAME), None)
        if use is None:
            last = GuideError("the model did not call the tool")
            continue
        try:
            return parse_guidance(pixels_to_grid(dict(use.input), *image.size))
        except GuideError as e:
            last = e
    raise GuideError(f"the model's answer could not be used: {last}")
