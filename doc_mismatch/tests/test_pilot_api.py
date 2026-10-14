"""HTTP-layer guards for the pilot app: the developer-relayed one-time-code login, the intake-extract-confirm
flow (vision call stubbed -- no real API key or network call), and that no response body ever leaks a raw
traceback."""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test-not-real")
os.environ.setdefault("NOTIFY_EMAIL", "dev@example.com")
os.environ.setdefault("SMTP_FROM_EMAIL", "dev@example.com")
os.environ.setdefault("SMTP_APP_PASSWORD", "not-a-real-app-password")
os.environ.setdefault("PILOT_DATA_DIR", tempfile.mkdtemp(prefix="pilot_api_test_"))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from pilot import config, db  # noqa: E402
from pilot.schema import BuildingDraft  # noqa: E402
from _pilot_flow import http_check  # noqa: E402

BUILDING_DRAFT = {
    "ahu": {"equipment_id": "AHU-1", "points": {"fan_status": "A1.SF"}},
    "boxes": [{"equipment_id": "VAV-X", "serves_room": "Room-X", "points": {"status": "V1.STS"}, "zone_temperature_point": "R1.T"}],
    "notes": None,
}


@pytest.fixture(autouse=True)
def _fresh_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "pilot.db")
    monkeypatch.setattr(config, "VISITS_DIR", tmp_path / "visits")
    monkeypatch.setattr(config, "UPLOADS_DIR", tmp_path / "uploads")
    db.init_db(config.DB_PATH)
    yield


def _bypass_cooldown():
    with db.connect(config.DB_PATH) as conn:
        conn.execute("UPDATE login_codes SET created_at = '2000-01-01T00:00:00+00:00'")


@pytest.fixture
def client(monkeypatch):
    # stub the vision call: no network, no real API key needed, deterministic draft
    import pilot.routes_intake as routes_intake

    def _fake_extract(bas_bytes, equip_bytes):
        return BuildingDraft.model_validate(BUILDING_DRAFT), '{"stub": true}'

    monkeypatch.setattr(routes_intake, "extract_building", _fake_extract)

    # stub the email send: no real SMTP call, no real Gmail credentials needed; capture what was "sent"
    import pilot.auth as auth_module
    sent = {}

    def _fake_send(code):
        sent["code"] = code

    monkeypatch.setattr(auth_module, "email_otp", type("M", (), {"send_login_code": staticmethod(_fake_send)}))

    import io
    from PIL import Image
    tiny = io.BytesIO()
    Image.new("RGB", (10, 10)).save(tiny, format="JPEG")
    tiny_bytes = tiny.getvalue()

    from pilot.app import app
    with TestClient(app) as c:
        yield c, tiny_bytes, sent


def _login(client) -> str:
    c, _, sent = client
    r = c.post("/api/request-code")
    assert r.status_code == 200
    assert "code" in sent
    r = c.post("/api/verify-code", json={"code": sent["code"]})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def test_request_code_always_sends_to_notify_email_never_to_a_caller_supplied_address(client):
    # the route takes no email at all now -- nothing a caller sends can redirect where the code goes
    c, _, sent = client
    r = c.post("/api/request-code")
    assert r.status_code == 200
    assert sent["code"] and len(sent["code"]) == 6


def test_wrong_code_rejected_right_code_still_works_after(client):
    c, _, sent = client
    c.post("/api/request-code")
    r = c.post("/api/verify-code", json={"code": "000000"})
    assert r.status_code == 401
    assert "Traceback" not in r.text
    r = c.post("/api/verify-code", json={"code": sent["code"]})
    assert r.status_code == 200


def test_code_is_single_use(client):
    c, _, sent = client
    c.post("/api/request-code")
    r1 = c.post("/api/verify-code", json={"code": sent["code"]})
    assert r1.status_code == 200
    r2 = c.post("/api/verify-code", json={"code": sent["code"]})
    assert r2.status_code == 401


def test_too_many_wrong_attempts_locks_out_the_code(client):
    c, _, sent = client
    c.post("/api/request-code")
    for _ in range(config.LOGIN_CODE_MAX_ATTEMPTS):
        c.post("/api/verify-code", json={"code": "000000"})
    r = c.post("/api/verify-code", json={"code": sent["code"]})
    assert r.status_code == 401          # even the real code no longer works once attempts are exhausted


def test_requesting_again_invalidates_the_previous_code(client):
    c, _, sent = client
    c.post("/api/request-code")
    first_code = sent["code"]
    _bypass_cooldown()   # isolate "does a new request kill the old code" from the resend-cooldown timing
    c.post("/api/request-code")
    r = c.post("/api/verify-code", json={"code": first_code})
    assert r.status_code == 401


def test_resend_within_cooldown_is_a_quiet_no_op_old_code_still_works(client):
    c, _, sent = client
    c.post("/api/request-code")
    first_code = sent["code"]
    r = c.post("/api/request-code")       # immediate resend, well inside the cooldown
    assert r.status_code == 200           # same generic response either way
    r = c.post("/api/verify-code", json={"code": first_code})
    assert r.status_code == 200           # the original code is still the live one


def test_second_successful_login_does_not_invalidate_the_first(client):
    """No session-kick tripwire by design: every code only ever reaches the developer, who decides whether
    to relay it, so there's no need to punish a second legitimate login (e.g. switching devices)."""
    c, _, sent = client
    first_token = _login(client)
    _bypass_cooldown()
    c.post("/api/request-code")
    second_token = c.post("/api/verify-code", json={"code": sent["code"]}).json()["token"]
    assert second_token != first_token
    assert c.get("/api/visits/whatever", headers={"Authorization": f"Bearer {first_token}"}).status_code == 404
    assert c.get("/api/visits/whatever", headers={"Authorization": f"Bearer {second_token}"}).status_code == 404


def test_api_routes_require_a_token(client):
    c, _, _ = client
    r = c.get("/api/visits/whatever")
    assert r.status_code == 401


def test_session_check_catches_a_revoked_token_with_no_visit_in_play(client):
    """Regression for the real gap found live: a token revoked server-side (e.g. after reworking login)
    must not keep *looking* authenticated client-side just because no visit-scoped call has happened yet
    to catch it -- /api/session is what the frontend's boot() calls to verify a stored token before
    showing the new-visit form."""
    c, _, _ = client
    token = _login(client)
    assert c.get("/api/session", headers={"Authorization": f"Bearer {token}"}).status_code == 200

    with db.connect(config.DB_PATH) as conn:
        db.revoke_all_sessions(conn)

    assert c.get("/api/session", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_full_intake_to_conclusion_flow(client):
    c, photo_bytes, _ = client
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    r = c.post("/api/intake/extract", headers=headers,
               files={"photo_bas": ("bas.jpg", photo_bytes, "image/jpeg"),
                      "photo_equipment": ("equip.jpg", photo_bytes, "image/jpeg")})
    assert r.status_code == 200, r.text
    intake_id = r.json()["intake_id"]
    assert r.json()["draft"]["ahu"]["equipment_id"] == "AHU-1"

    r = c.post(f"/api/intake/{intake_id}/confirm", headers=headers,
               json={"draft": BUILDING_DRAFT, "room_ids": ["Room-X"], "feel": "too_hot", "airflow": "yes"})
    assert r.status_code == 200, r.text
    visit_id = r.json()["visit_id"]
    assert r.json()["step"]["kind"] in ("check", "question")

    for _ in range(50):
        step = c.get(f"/api/visits/{visit_id}", headers=headers).json()["step"]
        if step["kind"] == "check":
            step = http_check(c, headers, visit_id)
        elif step["kind"] == "question":
            step = c.post(f"/api/visits/{visit_id}/answer", headers=headers, json={"word": "no"}).json()["step"]
        elif step["kind"] == "conclude":
            assert "involves_econ_fault" in step
            break
    else:
        pytest.fail("room never concluded")

    r = c.post(f"/api/visits/{visit_id}/advance", headers=headers)
    assert r.json()["step"]["kind"] == "visit_done"


def test_unknown_visit_is_a_clean_404_not_a_traceback(client):
    c, _, _ = client
    token = _login(client)
    r = c.get("/api/visits/does-not-exist", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404
    assert "Traceback" not in r.text and "File \"" not in r.text


def test_malformed_confirm_body_does_not_leak_internals(client):
    c, _, _ = client
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    bad_draft = {"ahu": {"equipment_id": "AHU-1"}, "boxes": [{"equipment_id": "VAV-X", "serves_room": "Room-X"}]}
    r = c.post("/api/intake/not-a-real-intake/confirm", headers=headers,
               json={"draft": bad_draft, "room_ids": ["Room-X"]})
    assert r.status_code == 404
    assert "Traceback" not in r.text
