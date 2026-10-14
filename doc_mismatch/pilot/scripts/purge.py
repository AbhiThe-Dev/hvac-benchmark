"""Permanently delete one visit's case record, or everything recorded for one participant (a withdrawal).

    python -m pilot.scripts.purge list
    python -m pilot.scripts.purge case 12                      # dry run: shows exactly what would go
    python -m pilot.scripts.purge case 12 --reason withdrawal_request --execute
    python -m pilot.scripts.purge participant 3 --orphan-intakes --reason withdrawal_request --execute

On the server: fly ssh console -C "python -m pilot.scripts.purge --data-dir /data participant 3". Offline, against any
data directory: --data-dir <folder holding pilot.db>. It never imports pilot.config, so it needs none of the app's secrets.

NOTHING is deleted unless you pass --execute. The default is a dry run that prints the plan and changes nothing.

SCOPE. A case is purged together with its whole VISIT: the rooms of one visit share a building file, photos and a
vision-model transcript, so there is no clean way to remove one room and keep the rest. Per visit this removes the
case rows, every case_event (the append-only triggers are dropped and restored inside one transaction, and a failure
rolls the whole thing back with the triggers intact), follow-up dates, the engine's room_log and conclusions, the
visit row, its intake rows (raw vision output) and the visit's folder and photos on disk. `participant` also removes
the participant record. A return-visit link from someone else's case to a purged one is cleared, not followed.

REAL DELETION. SQLite keeps deleted rows in free pages and in the write-ahead log, so the script turns on
secure_delete, checkpoints and truncates the log, and vacuums the file afterwards.

WHAT THIS CANNOT REACH (it prints these every time): backup tarballs you already made (pass --backups <folder> and it opens each
tarball and says which ones hold the data), exports you already wrote, Fly volume snapshots (they expire on Fly's schedule), and pilot.log, which holds
request lines (ids and paths, no content). A purge is only as complete as you make the copies.
"""
import argparse
import json
import shutil
import sqlite3
import sys
import tarfile
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .. import db
from .backup import default_data_dir

REASONS = ("withdrawal_request", "data_error", "test_data", "other")      # a fixed list on purpose: a free-text reason would be the one place a name could get typed


@dataclass
class Plan:
    scope: str
    target: int
    visit_ids: list = field(default_factory=list)
    case_ids: list = field(default_factory=list)
    participant_ids: list = field(default_factory=list)
    intake_ids: list = field(default_factory=list)           # linked to the visits: always removed
    orphan_intake_ids: list = field(default_factory=list)    # unconfirmed intakes in the participant's window
    delete_orphans: bool = False
    folders: list = field(default_factory=list)              # visit and photo folders that exist on disk
    counts: dict = field(default_factory=dict)
    in_progress: list = field(default_factory=list)
    relinked: int = 0
    errors: list = field(default_factory=list)

    @property
    def all_intakes(self) -> list:
        return self.intake_ids + (self.orphan_intake_ids if self.delete_orphans else [])


def _marks(n: int) -> str:
    return ",".join("?" * n) or "NULL"


def _count(conn, sql: str, ids: list) -> int:
    return conn.execute(sql.format(m=_marks(len(ids))), ids).fetchone()[0] if ids else 0


def _fill(conn, plan: Plan, data_dir: Path) -> Plan:
    v, c, i = plan.visit_ids, plan.case_ids, plan.all_intakes
    folders = [data_dir / "visits" / x for x in v] + [data_dir / "uploads" / x for x in i]
    plan.folders = [p for p in folders if p.exists()]
    plan.counts = dict(
        visits=len(v), cases=len(c), participants=len(plan.participant_ids), intakes=len(i),
        case_events=_count(conn, "SELECT COUNT(*) FROM case_event WHERE case_id IN ({m})", c),
        followups=_count(conn, "SELECT COUNT(*) FROM followup_due WHERE case_id IN ({m})", c),
        room_log=_count(conn, "SELECT COUNT(*) FROM room_log WHERE visit_id IN ({m})", v),
        room_conclusions=_count(conn, "SELECT COUNT(*) FROM room_conclusion WHERE visit_id IN ({m})", v),
        folders=len(plan.folders))
    plan.in_progress = [r[0] for r in conn.execute(f"SELECT id FROM visits WHERE status != 'done' AND id IN ({_marks(len(v))})", v)] if v else []
    plan.relinked = (conn.execute(f"SELECT COUNT(*) FROM cases WHERE prior_case_id IN ({_marks(len(c))}) AND id NOT IN ({_marks(len(c))})", c + c).fetchone()[0]
                     if c else 0)
    return plan


def _visits_of(conn, case_ids: list) -> list:
    return sorted({r[0] for r in conn.execute(f"SELECT visit_id FROM cases WHERE id IN ({_marks(len(case_ids))})", case_ids)}) if case_ids else []


def plan_case(conn, case_id: int, data_dir: Path) -> Plan:
    plan = Plan("case", case_id)
    row = conn.execute("SELECT visit_id, participant_id FROM cases WHERE id = ?", (case_id,)).fetchone()
    if row is None:
        plan.errors.append(f"no case {case_id}")
        return plan
    plan.visit_ids = [row["visit_id"]]
    plan.case_ids = [r[0] for r in conn.execute("SELECT id FROM cases WHERE visit_id = ? ORDER BY id", (row["visit_id"],))]
    plan.intake_ids = [r[0] for r in conn.execute("SELECT id FROM intake WHERE visit_id = ?", (row["visit_id"],))]
    return _fill(conn, plan, data_dir)


def plan_participant(conn, pid: int, data_dir: Path, orphan_intakes: bool) -> Plan:
    plan = Plan("participant", pid, delete_orphans=orphan_intakes)
    p = conn.execute("SELECT * FROM participants WHERE id = ?", (pid,)).fetchone()
    if p is None:
        plan.errors.append(f"no participant {pid}")
        return plan
    plan.participant_ids = [pid]
    own = [r[0] for r in conn.execute("SELECT id FROM cases WHERE participant_id = ?", (pid,))]
    plan.visit_ids = _visits_of(conn, own)
    plan.case_ids = [r[0] for r in conn.execute(f"SELECT id FROM cases WHERE visit_id IN ({_marks(len(plan.visit_ids))}) ORDER BY id", plan.visit_ids)] if plan.visit_ids else []
    strangers = sorted(set(plan.case_ids) - set(own))
    if strangers:
        plan.errors.append(f"visit(s) of this participant also hold case(s) {strangers} of someone else; a visit cannot be split, so nothing was planned")
    plan.intake_ids = [r[0] for r in conn.execute(f"SELECT id FROM intake WHERE visit_id IN ({_marks(len(plan.visit_ids))})", plan.visit_ids)] if plan.visit_ids else []
    nxt = conn.execute("SELECT MIN(created_at) FROM participants WHERE created_at > ?", (p["created_at"],)).fetchone()[0]
    sql, params = "SELECT id FROM intake WHERE visit_id IS NULL AND created_at >= ?", [p["created_at"]]
    if nxt:
        sql, params = sql + " AND created_at < ?", params + [nxt]
    plan.orphan_intake_ids = [r[0] for r in conn.execute(sql, params)]
    return _fill(conn, plan, data_dir)


# ------------------------------------------------------------------------------------------------- doing it

def execute(db_path: Path, plan: Plan, reason: str) -> dict:
    """One transaction for every row; files only after it commits (a failed DB step must never leave rows pointing at deleted files)."""
    db.init_db(db_path)                                       # makes sure purge_log exists on an older database
    v, c, i, pids = plan.visit_ids, plan.case_ids, plan.all_intakes, plan.participant_ids
    conn = sqlite3.connect(str(db_path), timeout=30, isolation_level=None)
    conn.execute("PRAGMA secure_delete=ON")
    conn.execute("PRAGMA foreign_keys=ON")
    triggers = conn.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger' AND tbl_name='case_event'").fetchall()
    try:
        conn.execute("BEGIN IMMEDIATE")
        try:
            for name, _ in triggers:
                conn.execute(f'DROP TRIGGER "{name}"')
            ph = lambda xs: _marks(len(xs))                   # noqa: E731
            if c:
                conn.execute(f"UPDATE cases SET prior_case_id = NULL WHERE prior_case_id IN ({ph(c)}) AND id NOT IN ({ph(c)})", c + c)
                conn.execute(f"DELETE FROM followup_due WHERE case_id IN ({ph(c)})", c)
                conn.execute(f"DELETE FROM case_event WHERE case_id IN ({ph(c)})", c)
                conn.execute(f"DELETE FROM cases WHERE id IN ({ph(c)})", c)
            if v:
                conn.execute(f"DELETE FROM room_log WHERE visit_id IN ({ph(v)})", v)
                conn.execute(f"DELETE FROM room_conclusion WHERE visit_id IN ({ph(v)})", v)
            if i:
                conn.execute(f"DELETE FROM intake WHERE id IN ({ph(i)})", i)
            if v:
                conn.execute(f"DELETE FROM visits WHERE id IN ({ph(v)})", v)
            if pids:
                conn.execute(f"DELETE FROM participants WHERE id IN ({ph(pids)})", pids)
            conn.execute("INSERT INTO purge_log (purged_at, scope, target_id, reason, counts_json) VALUES (?,?,?,?,?)",
                         (db._now(), plan.scope, plan.target, reason, json.dumps(plan.counts)))
            for _, sql in triggers:
                conn.execute(sql)
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        restored = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='case_event'")}
        if restored != {n for n, _ in triggers}:
            raise RuntimeError("the append-only triggers were not restored; restore pilot.db from a backup before running the app")
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.execute("VACUUM")
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        conn.close()
    failed = []
    for folder in plan.folders:
        try:
            shutil.rmtree(folder)
        except OSError as e:
            failed.append(f"{folder}: {e}")
    return dict(removed=len(plan.folders) - len(failed), failed=failed)


# ------------------------------------------------------------------------------------------------- output

def render(plan: Plan, dry: bool) -> str:
    n = plan.counts
    out = ["PURGE PLAN" + ("  (dry run: nothing has been changed)" if dry else "")]
    if plan.errors:
        return "\n".join(out + [f"cannot proceed: {e}" for e in plan.errors])
    out += [f"scope: {plan.scope} {plan.target}",
            f"  visits {n['visits']}   cases {n['cases']}   case events {n['case_events']}   follow-ups {n['followups']}",
            f"  engine log rows {n['room_log']}   conclusions {n['room_conclusions']}   intakes (vision output) {n['intakes']}   participant records {n['participants']}",
            f"  folders to remove from disk (building files, photos): {n['folders']}"]
    if plan.relinked:
        out.append(f"  {plan.relinked} case(s) elsewhere name one of these as the earlier case; that link will be cleared")
    if plan.in_progress:
        out.append(f"  WARNING: {len(plan.in_progress)} visit(s) not finished; the technician's open page will fall back to the start screen")
    if plan.scope == "participant" and plan.orphan_intake_ids and not plan.delete_orphans:
        out.append(f"  {len(plan.orphan_intake_ids)} unconfirmed intake(s) (photos read but no visit started) fall in this participant's window; "
                   f"they are KEPT. Add --orphan-intakes to delete them too, after checking they are theirs.")
    return "\n".join(out)


def backup_holds(tarball: Path, plan: Plan) -> str:
    """'yes' / 'no' / 'unreadable': does this backup's database contain any of the cases or participants being purged?
    (Ids are AUTOINCREMENT, so an id in an older backup is the same row.)"""
    try:
        with tempfile.TemporaryDirectory() as tmp, tarfile.open(tarball, "r:gz") as tar:
            tar.extract("pilot.db", tmp, filter="data")
            conn = sqlite3.connect(f"file:{tmp}/pilot.db?mode=ro", uri=True)
            try:
                for table, ids in (("cases", plan.case_ids), ("participants", plan.participant_ids)):
                    if ids and conn.execute(f"SELECT COUNT(*) FROM {table} WHERE id IN ({_marks(len(ids))})", ids).fetchone()[0]:
                        return "yes"
                return "no"
            finally:
                conn.close()
    except (tarfile.TarError, OSError, EOFError, KeyError, sqlite3.Error):
        return "unreadable"


def not_reached(backups: Path | None, plan: Plan | None = None) -> str:
    lines = ["NOT removed by this command:",
             "  - backup tarballs already made, exports already written, and copies of either",
             "  - Fly volume snapshots (they expire on Fly's schedule)",
             "  - pilot.log: request lines with ids and paths, no content"]
    if backups is not None and plan is not None:
        found = sorted(backups.glob("pilot-backup-*.tar.gz")) if backups.is_dir() else []
        verdicts = {t: backup_holds(t, plan) for t in found}
        holding = [t for t, v in verdicts.items() if v == "yes"]
        unknown = [t for t, v in verdicts.items() if v == "unreadable"]
        lines.append(f"  backups in {backups}: {len(found)} checked, {len(holding)} still hold this data"
                     + (f", {len(unknown)} could not be read (assume they do)" if unknown else "") if found else f"  no backup tarballs found in {backups}")
        lines += [f"      HOLDS  {t.name}" for t in holding] + [f"      ?      {t.name}" for t in unknown]
    return "\n".join(lines)


def cmd_list(conn, data_dir: Path) -> int:
    print("PARTICIPANTS")
    for p in conn.execute("SELECT p.*, (SELECT COUNT(*) FROM cases c WHERE c.participant_id = p.id) AS n FROM participants p ORDER BY p.id"):
        print(f"  {p['id']:>3}  {'active' if p['active'] else 'ended '}  {p['role']}/{p['years_band']}/{p['vav_band']}  since {p['created_at'][:10]}  cases {p['n']}")
    print("CASES")
    for c in conn.execute("SELECT c.id, c.visit_id, c.room_index, c.participant_id, c.opened_at, c.status, v.room_ids_json FROM cases c "
                          "LEFT JOIN visits v ON v.id = c.visit_id ORDER BY c.id"):
        try:
            room = json.loads(c["room_ids_json"])[c["room_index"]]
        except (TypeError, IndexError):
            room = "?"
        print(f"  {c['id']:>3}  participant {c['participant_id'] if c['participant_id'] is not None else '-':<3} {c['opened_at'][:10]}  {c['status']:<6}  visit {c['visit_id'][:8]}  {room}")
    n = conn.execute("SELECT COUNT(*) FROM intake WHERE visit_id IS NULL").fetchone()[0]
    print(f"UNCONFIRMED INTAKES (photos read, no visit started): {n}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data-dir", type=Path, default=default_data_dir())
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    for name in ("case", "participant"):
        p = sub.add_parser(name)
        p.add_argument("id", type=int)
        p.add_argument("--execute", action="store_true", help="actually delete (without this it is a dry run)")
        p.add_argument("--reason", choices=REASONS, help="required with --execute")
        p.add_argument("--backups", type=Path, help="a folder of backup tarballs to list as still holding the data")
        if name == "participant":
            p.add_argument("--orphan-intakes", action="store_true", help="also delete unconfirmed intakes made during this participant's time")
    a = ap.parse_args(argv)

    db_path = a.data_dir / "pilot.db"
    if not db_path.exists():
        print(f"no database at {db_path}", file=sys.stderr)
        return 2
    ro = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    ro.row_factory = sqlite3.Row
    try:
        if a.cmd == "list":
            return cmd_list(ro, a.data_dir)
        plan = plan_case(ro, a.id, a.data_dir) if a.cmd == "case" else plan_participant(ro, a.id, a.data_dir, a.orphan_intakes)
    finally:
        ro.close()

    print(render(plan, dry=not a.execute))
    if plan.errors:
        return 1
    if not a.execute:
        extra = " --orphan-intakes" if a.cmd == "participant" and a.orphan_intakes else ""
        print(f"\nTo do it:  python -m pilot.scripts.purge --data-dir {a.data_dir} {a.cmd} {a.id}{extra} --reason <{'|'.join(REASONS)}> --execute")
        print("\n" + not_reached(a.backups, plan))
        return 0
    if a.reason is None:
        print("--reason is required with --execute", file=sys.stderr)
        return 2
    result = execute(db_path, plan, a.reason)
    print(f"\nPURGED. Folders removed: {result['removed']}. The database was checkpointed and vacuumed.")
    for f in result["failed"]:
        print(f"  COULD NOT REMOVE {f}  (the database rows are already gone; delete it by hand)", file=sys.stderr)
    print("\n" + not_reached(a.backups, plan))
    return 1 if result["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
