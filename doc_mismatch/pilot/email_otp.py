"""Sends the login code to config.NOTIFY_EMAIL (always -- the developer's own inbox, never the person at
the keyboard) via the developer's own Gmail account (SMTP + an App Password) -- stdlib only, no third-party
email service or domain needed. Gmail's regular-account sending limit (~500/day) is far more than this
pilot needs over a week."""
import smtplib
from email.message import EmailMessage

from . import config

SMTP_HOST, SMTP_PORT = "smtp.gmail.com", 587


def send_login_code(code: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = "Service Call Assistant: a login was requested"
    msg["From"] = config.SMTP_FROM_EMAIL
    msg["To"] = config.NOTIFY_EMAIL
    msg.set_content(
        f"Someone requested access to the pilot app. Code: {code}\n\n"
        f"It expires in {config.LOGIN_CODE_TTL_MINUTES} minutes and works once. Only share it with the "
        f"technician yourself, and only if you're expecting this request."
    )
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as s:
        s.starttls()
        s.login(config.SMTP_FROM_EMAIL, config.SMTP_APP_PASSWORD)
        s.send_message(msg)
