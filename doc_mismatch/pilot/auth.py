"""Every login request sends a one-time code to config.NOTIFY_EMAIL -- the developer's own inbox, never the
person asking for it (email_otp.py). The developer relays the code by hand, each time, only to whoever
should actually be let in. That makes every login a deliberate human decision rather than something an OTP
code alone could be silently forwarded to enable -- chosen over a per-technician-inbox code (or a session-
kick tripwire) specifically because it stops sharing before it happens, not just after. Session tokens
themselves are unchanged: opaque, server-side, revocable (scripts/revoke_sessions.py)."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Header, HTTPException

from . import config, db, email_otp


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def request_login_code() -> None:
    with db.connect(config.DB_PATH) as conn:
        latest = db.get_latest_login_code(conn)
        if latest is not None:
            age = datetime.now(timezone.utc) - datetime.fromisoformat(latest["created_at"])
            if age < timedelta(seconds=config.LOGIN_CODE_RESEND_COOLDOWN_SECONDS):
                return   # too soon to resend; the already-sent code is still usable
        code = f"{secrets.randbelow(1_000_000):06d}"
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=config.LOGIN_CODE_TTL_MINUTES)).isoformat()
        db.create_login_code(conn, _hash_code(code), expires_at)
    email_otp.send_login_code(code)


def verify_login_code(code: str) -> str | None:
    """Returns a fresh session token on success, None on any failure (wrong/expired/used code, too many
    attempts) -- callers should give the same generic error for all of these."""
    with db.connect(config.DB_PATH) as conn:
        latest = db.get_latest_login_code(conn)
        if latest is None or latest["used"] or latest["attempts"] >= config.LOGIN_CODE_MAX_ATTEMPTS:
            return None
        if datetime.now(timezone.utc) > datetime.fromisoformat(latest["expires_at"]):
            return None
        if not secrets.compare_digest(_hash_code(code or ""), latest["code_hash"]):
            db.increment_code_attempts(conn, latest["id"])
            return None
        db.mark_code_used(conn, latest["id"])
    return issue_token()[0]


def issue_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=config.SESSION_TTL_DAYS)).isoformat()
    with db.connect(config.DB_PATH) as conn:
        db.create_session(conn, token, expires_at)
    return token, expires_at


def validate_token(token: str) -> bool:
    with db.connect(config.DB_PATH) as conn:
        session = db.get_session(conn, token)
        if session is None or session["revoked"]:
            return False
        if datetime.now(timezone.utc) > datetime.fromisoformat(session["expires_at"]):
            return False
        db.touch_session(conn, token)
        return True


async def require_token(authorization: str = Header(default="")) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header.")
    token = authorization[len("Bearer "):]
    if not validate_token(token):
        raise HTTPException(status_code=401, detail="Session expired or invalid. Log in again.")
    return token
