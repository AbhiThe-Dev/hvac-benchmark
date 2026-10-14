"""Instant access revocation. Run with no args to revoke every issued session (e.g. after rotating who can
log in, or a suspected leak); pass a specific token to revoke just that one. Note: this clears sessions
(already-issued tokens), not outstanding login codes -- those already expire on their own (see
config.LOGIN_CODE_TTL_MINUTES) and are single-use regardless. Run from inside doc_mismatch/ so `pilot`
resolves as a package:

    cd doc_mismatch && ../.venv/bin/python -m pilot.scripts.revoke_sessions
    cd doc_mismatch && ../.venv/bin/python -m pilot.scripts.revoke_sessions <token>
"""
import sys

from .. import config, db

if __name__ == "__main__":
    with db.connect(config.DB_PATH) as conn:
        if len(sys.argv) > 1:
            db.revoke_session(conn, sys.argv[1])
            print(f"Revoked 1 session (token prefix {sys.argv[1][:8]}...).")
        else:
            n = db.revoke_all_sessions(conn)
            print(f"Revoked {n} active session(s). Existing tokens will no longer work; a fresh /api/request-code + /api/verify-code is required.")
