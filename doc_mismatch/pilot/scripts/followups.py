"""The developer's side of the 7- and 30-day repeat-failure follow-up, and participant handover. The technician is
asked in the app when they next open it; this is for chasing the ones they have not answered, and for entering an
answer they gave you some other way. Works without the app's secrets (it never imports pilot.config).

    python -m pilot.scripts.followups list                       # due and overdue, then what is coming
    python -m pilot.scripts.followups record 12 7 no --note "called, still fine"
    python -m pilot.scripts.followups new-participant            # next login is asked for a profile again

On the server: fly ssh console -C "python -m pilot.scripts.followups list". Offline: add --data-dir <folder holding
pilot.db> (e.g. an unpacked backup). Answers entered here are stored as recorded_by=developer.
"""
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .. import cases as CS, db
from .backup import default_data_dir


def _room(conn, visit_id: str, room_index: int) -> str:
    row = conn.execute("SELECT room_ids_json FROM visits WHERE id = ?", (visit_id,)).fetchone()
    try:
        return json.loads(row["room_ids_json"])[room_index]
    except (TypeError, IndexError, KeyError):
        return "?"


def cmd_list(conn, horizon_days: int) -> int:
    now = datetime.now(timezone.utc)
    rows = conn.execute(
        "SELECT f.case_id, f.window_days, f.due_at, c.visit_id, c.room_index, c.participant_id FROM followup_due f "
        "JOIN cases c ON c.id = f.case_id WHERE f.answered_event_id IS NULL ORDER BY f.due_at").fetchall()
    due = [r for r in rows if datetime.fromisoformat(r["due_at"]) <= now]
    soon = [r for r in rows if now < datetime.fromisoformat(r["due_at"]) <= now + timedelta(days=horizon_days)]

    def show(title, items):
        print(f"{title} ({len(items)})")
        for r in items:
            days = (datetime.fromisoformat(r["due_at"]) - now).days
            print(f"  case {r['case_id']:>4}  {r['window_days']:>2}-day  {_room(conn, r['visit_id'], r['room_index']):<24} "
                  f"{'overdue ' + str(-days) + 'd' if days < 0 else 'in ' + str(days) + 'd'}   due {r['due_at'][:10]}")
    show("DUE OR OVERDUE", due)
    show(f"COMING IN THE NEXT {horizon_days} DAYS", soon)
    if due:
        print("\nrecord one with:  python -m pilot.scripts.followups record <case> <7|30> <yes|no|unsure> [--note ...]")
    return 0


def cmd_record(conn, case_id: int, window: int, recurred: str, note: str | None) -> int:
    try:
        CS.record_followup(conn, case_id, window_days=window, recurred=recurred, note=note, recorded_by="developer", client_ts=None)
    except ValueError as e:
        print(f"not recorded: {e}", file=sys.stderr)
        return 1
    print(f"recorded: case {case_id}, {window}-day, recurred={recurred}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data-dir", type=Path, default=default_data_dir())
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list")
    p.add_argument("--days", type=int, default=7, help="how far ahead to look (default 7)")
    p = sub.add_parser("record")
    p.add_argument("case_id", type=int)
    p.add_argument("window", type=int, choices=db.FOLLOWUP_WINDOWS)
    p.add_argument("recurred", choices=["yes", "no", "unsure"])
    p.add_argument("--note")
    sub.add_parser("new-participant")
    a = ap.parse_args(argv)

    db_path = a.data_dir / "pilot.db"
    if not db_path.exists():
        print(f"no database at {db_path}", file=sys.stderr)
        return 2
    with db.connect(db_path) as conn:
        if a.cmd == "list":
            return cmd_list(conn, a.days)
        if a.cmd == "record":
            return cmd_record(conn, a.case_id, a.window, a.recurred, a.note)
        n = db.deactivate_participants(conn)
        print(f"{n} participant(s) deactivated. The next person to open the app is shown the notice and asked for a profile; "
              f"their cases are kept apart from the previous participant's.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
