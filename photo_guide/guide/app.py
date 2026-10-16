"""The prototype server: GET /api/checks, POST /api/guide (photo + check -> annotated steps), POST /api/feedback. Standalone: it imports nothing
from pilot/ or docmismatch. Every run is saved under photo_guide/out/runs/<id>/ (local only, git-ignored) so outputs can be reviewed."""
from __future__ import annotations

import base64
import json
import time
import uuid
from pathlib import Path
from typing import Callable

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .image import BadImage, preprocess, to_jpeg
from .llm import model_name, request_guidance
from .prompt import load_checks, safety_lines
from .render import render_guidance
from .schema import GuideError

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
STATIC = ROOT / "static"


class Feedback(BaseModel):
    run_id: str
    kind: str                 # "placement" | "unclear" | "answer"
    step: int | None = None
    value: str = ""


def _data_url(jpeg: bytes) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(jpeg).decode("ascii")


def create_app(guide_fn: Callable = request_guidance, out_dir: Path = OUT) -> FastAPI:
    app = FastAPI(title="photo_guide prototype")
    checks = load_checks()

    @app.get("/")
    def index():
        return FileResponse(STATIC / "index.html")

    @app.get("/api/checks")
    def list_checks():
        return [dict(name=c["name"], text=c["text"], family=c["family"], photo_hint=c["photo_hint"], safety=safety_lines(c)) for c in checks.values()]

    @app.post("/api/guide")
    def guide(check: str = Form(...), note: str = Form(""), photo: UploadFile = File(...)):
        c = checks.get(check)
        if c is None:
            raise HTTPException(404, f"unknown check {check!r}")
        try:
            base = preprocess(photo.file.read())
        except BadImage as e:
            raise HTTPException(400, str(e)) from e
        t0 = time.time()
        try:
            g = guide_fn(c, base, note)
        except GuideError as e:
            raise HTTPException(502, str(e)) from e
        except RuntimeError as e:
            raise HTTPException(503, str(e)) from e
        seconds = round(time.time() - t0, 1)
        r = render_guidance(base, g)
        run_id = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
        run = out_dir / "runs" / run_id
        run.mkdir(parents=True, exist_ok=True)
        (run / "photo.jpg").write_bytes(to_jpeg(base))
        (run / "overview.jpg").write_bytes(r.overview)
        for i, b in enumerate(r.steps, 1):
            (run / f"step_{i}.jpg").write_bytes(b)
        (run / "guidance.json").write_text(json.dumps(dict(check=check, model=model_name(), seconds=seconds, note=note, guidance=g.model_dump()), indent=2))
        return dict(run_id=run_id, check=dict(name=c["name"], text=c["text"], words=c["words"]), safety=safety_lines(c), seconds=seconds,
                    guidance=g.model_dump(), overview=_data_url(r.overview), step_images=[_data_url(b) for b in r.steps], photo=_data_url(to_jpeg(base)))

    @app.post("/api/feedback")
    def feedback(fb: Feedback):
        if not (out_dir / "runs" / fb.run_id).is_dir():
            raise HTTPException(404, "unknown run")
        with (out_dir / "feedback.jsonl").open("a") as f:
            f.write(json.dumps(dict(ts=time.time(), **fb.model_dump())) + "\n")
        return {"ok": True}

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app


app = create_app()
