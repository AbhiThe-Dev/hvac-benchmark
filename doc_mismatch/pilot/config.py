"""Loads .env (gitignored). No defaults for secrets -- fail loudly at startup rather than silently run unauthenticated."""
import os
from pathlib import Path

from dotenv import load_dotenv

PILOT_DIR = Path(__file__).resolve().parent
load_dotenv(PILOT_DIR / ".env")


def _require(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise RuntimeError(f"{name} is not set. Create {PILOT_DIR / '.env'} (see .env.example) before starting the pilot app.")
    return v


ANTHROPIC_API_KEY = _require("ANTHROPIC_API_KEY")

# Every login attempt -- no matter who clicks "request a code" -- sends the one-time code to THIS one
# inbox (the developer's own), via the developer's own Gmail account (SMTP_FROM_EMAIL/SMTP_APP_PASSWORD),
# not a third-party email service, so no domain is needed. The person at the keyboard never receives the
# code directly; the developer relays it by hand each time. That makes every login a deliberate, visible
# human decision rather than something an OTP code alone could be silently forwarded to enable.
NOTIFY_EMAIL = _require("NOTIFY_EMAIL").strip().lower()
SMTP_FROM_EMAIL = _require("SMTP_FROM_EMAIL")
SMTP_APP_PASSWORD = _require("SMTP_APP_PASSWORD")

DATA_DIR = Path(os.environ.get("PILOT_DATA_DIR", PILOT_DIR / "data"))
DB_PATH = DATA_DIR / "pilot.db"
LOG_PATH = DATA_DIR / "pilot.log"
UPLOADS_DIR = DATA_DIR / "uploads"
VISITS_DIR = DATA_DIR / "visits"
SESSION_TTL_DAYS = int(os.environ.get("PILOT_SESSION_TTL_DAYS", "10"))
LOGIN_CODE_TTL_MINUTES = int(os.environ.get("PILOT_CODE_TTL_MINUTES", "10"))
LOGIN_CODE_MAX_ATTEMPTS = int(os.environ.get("PILOT_CODE_MAX_ATTEMPTS", "5"))
LOGIN_CODE_RESEND_COOLDOWN_SECONDS = int(os.environ.get("PILOT_CODE_RESEND_COOLDOWN_SECONDS", "30"))
