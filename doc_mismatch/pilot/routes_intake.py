import base64
import json
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from . import auth, cases, config, db, visit as V
from .logging_conf import log
from .schema import ConfirmIntakeRequest, draft_to_building_json
from .vision_extract import extract_building, preprocess_image

router = APIRouter(dependencies=[Depends(auth.require_token)])
MAX_PHOTO_BYTES = 15_000_000


@router.post("/api/intake/extract")
async def extract(photo_bas: UploadFile = File(...), photo_equipment: UploadFile = File(...)):
    bas_bytes = await photo_bas.read()
    equip_bytes = await photo_equipment.read()
    if len(bas_bytes) > MAX_PHOTO_BYTES or len(equip_bytes) > MAX_PHOTO_BYTES:
        raise HTTPException(status_code=400, detail="One of those photos is too large. Try again.")

    try:
        draft, raw = extract_building(bas_bytes, equip_bytes)
    except Exception:
        log.exception("vision extraction failed")
        raise HTTPException(status_code=502, detail="Couldn't read those photos. Try retaking them, closer and in better light.")

    intake_id = uuid.uuid4().hex
    intake_dir = config.UPLOADS_DIR / intake_id
    intake_dir.mkdir(parents=True, exist_ok=True)
    # store the preprocessed (resized, EXIF-stripped) bytes we actually sent, never the raw upload
    (intake_dir / "bas.jpg").write_bytes(base64.b64decode(preprocess_image(bas_bytes).base64_data))
    (intake_dir / "equipment.jpg").write_bytes(base64.b64decode(preprocess_image(equip_bytes).base64_data))

    with db.connect(config.DB_PATH) as conn:
        db.create_intake(conn, intake_id, raw, draft.model_dump_json(),
                          str(intake_dir / "bas.jpg"), str(intake_dir / "equipment.jpg"))
    return {"intake_id": intake_id, "draft": draft.model_dump()}


@router.post("/api/intake/{intake_id}/confirm")
def confirm(intake_id: str, body: ConfirmIntakeRequest):
    with db.connect(config.DB_PATH) as conn:
        intake = db.get_intake(conn, intake_id)
    if intake is None:
        raise HTTPException(status_code=404, detail="No such intake. Start a new visit.")

    building_json = draft_to_building_json(body.draft)
    context = body.context.model_dump(exclude_none=True) if body.context else None
    try:
        cases.validate_context(context)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    try:
        visit_id = V.create_visit(building_json, body.room_ids, feel=body.feel, airflow=body.airflow, context=context)
    except Exception:
        log.exception("visit creation failed from intake %s", intake_id)
        raise HTTPException(status_code=400, detail="That building description isn't usable yet -- double-check "
                             "the AHU, box, and room IDs line up, then try confirming again.")

    with db.connect(config.DB_PATH) as conn:
        db.confirm_intake(conn, intake_id, json.dumps(building_json), visit_id)

    rooms = V.get_room_info(visit_id)
    step = V.get_current_step(visit_id)
    return {"visit_id": visit_id, "rooms": rooms, "step": step}
