from fastapi import APIRouter, HTTPException

from . import auth
from .logging_conf import log
from .schema import VerifyCodeRequest

router = APIRouter()


@router.post("/api/request-code")
def request_code():
    try:
        auth.request_login_code()
    except Exception:
        log.exception("sending login code failed")
        raise HTTPException(status_code=502, detail="Couldn't send the code. Try again shortly.")
    return {"sent": True}


@router.post("/api/verify-code")
def verify_code(body: VerifyCodeRequest):
    token = auth.verify_login_code(body.code)
    if token is None:
        raise HTTPException(status_code=401, detail="That code is wrong, expired, or already used. Request a new one.")
    return {"token": token}
