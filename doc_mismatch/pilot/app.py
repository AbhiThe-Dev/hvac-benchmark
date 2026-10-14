from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse

from . import config, db
from .logging_conf import log
from .routes_auth import router as auth_router
from .routes_case import router as case_router
from .routes_intake import router as intake_router
from .routes_visit import router as visit_router

STATIC_DIR = Path(__file__).with_name("static")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init_db(config.DB_PATH)
    config.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    config.VISITS_DIR.mkdir(parents=True, exist_ok=True)
    log.info("pilot app started, data dir=%s", config.DATA_DIR)
    yield


app = FastAPI(title="HVAC Troubleshooting Assistant -- Pilot", lifespan=lifespan)


@app.middleware("http")
async def access_log(request: Request, call_next):
    response = await call_next(request)
    auth_header = request.headers.get("authorization", "")
    token_prefix = auth_header[len("Bearer "):][:8] if auth_header.startswith("Bearer ") else "-"
    log.info("%s %s -> %s (token %s..., from %s)", request.method, request.url.path, response.status_code,
              token_prefix, request.client.host if request.client else "?")
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    log.exception("unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"error": "Something went wrong on our end. Try again, or note the time and tell the developer."})


app.include_router(auth_router)
app.include_router(intake_router)
app.include_router(visit_router)
app.include_router(case_router)


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")
