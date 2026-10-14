"""A consistent backup of the pilot's data, as one .tar.gz. Today there is one machine, one volume and nothing else
holds a copy, so this is what stands between a dead volume and losing the case record.

The database is copied with SQLite's online backup API, which is safe while the app is writing (a plain `cp` of a
WAL-mode database is not). The tarball holds `pilot.db`, every visit's `building.json` (the export needs them to
alias equipment and room names) and a MANIFEST.json with row counts and a checksum. Photos are left out unless you
ask: they are not part of the case record and can show building names.

On the server (the app's secrets are not needed):

    fly ssh console -C "python -m pilot.scripts.backup --out /data/backups"
    fly ssh sftp get /data/backups/<the file it prints> .

then keep the .tar.gz somewhere that is not the Fly volume. Offline, against any data directory:

    cd doc_mismatch && ../.venv/bin/python -m pilot.scripts.backup --data-dir pilot/data --out ~/pilot-backups

To restore, unpack it and point PILOT_DATA_DIR at the folder. `--verify FILE` re-opens a tarball and checks it.
"""
import argparse
import hashlib
import io
import json
import os
import sqlite3
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

TABLES = ("visits", "room_log", "room_conclusion", "intake", "participants", "cases", "case_event", "followup_due")


def default_data_dir() -> Path:
    env = os.environ.get("PILOT_DATA_DIR")
    return Path(env) if env else Path(__file__).resolve().parents[1] / "data"


def row_counts(db_path: Path) -> dict:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        have = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in TABLES if t in have}
    finally:
        conn.close()


def snapshot_db(src: Path, dest: Path) -> None:
    source = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
    target = sqlite3.connect(str(dest))
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()


def make_backup(data_dir: Path, out_dir: Path, *, photos: bool = False, now: datetime | None = None) -> Path:
    db_path = data_dir / "pilot.db"
    if not db_path.exists():
        raise SystemExit(f"no database at {db_path}")
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    out_dir.mkdir(parents=True, exist_ok=True)
    final = out_dir / f"pilot-backup-{stamp}.tar.gz"
    with tempfile.TemporaryDirectory() as tmp:
        snap = Path(tmp) / "pilot.db"
        snapshot_db(db_path, snap)
        counts = row_counts(snap)
        manifest = dict(created_at=stamp, source=str(data_dir), row_counts=counts, photos_included=photos,
                        db_sha256=hashlib.sha256(snap.read_bytes()).hexdigest())
        partial = final.with_suffix(".partial")
        with tarfile.open(partial, "w:gz") as tar:
            tar.add(snap, arcname="pilot.db")
            for sub in ("visits", "uploads") if photos else ("visits",):
                if (data_dir / sub).is_dir():
                    tar.add(data_dir / sub, arcname=sub)
            blob = json.dumps(manifest, indent=1).encode()
            info = tarfile.TarInfo("MANIFEST.json")
            info.size = len(blob)
            tar.addfile(info, io.BytesIO(blob))
        partial.replace(final)                   # a half-written file never has the final name
    problems = verify_backup(final)
    if problems:
        final.unlink()
        raise SystemExit("backup failed verification, removed: " + "; ".join(problems))
    return final


def verify_backup(path: Path) -> list[str]:
    """Opens the tarball, restores the database from it and checks it against the manifest. Returns problems (empty = good)."""
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        try:
            with tarfile.open(path, "r:gz") as tar:
                names = set(tar.getnames())
                if not {"pilot.db", "MANIFEST.json"} <= names:
                    return [f"missing pilot.db or MANIFEST.json (has {sorted(names)[:5]})"]
                tar.extract("pilot.db", tmp, filter="data")
                manifest = json.load(tar.extractfile("MANIFEST.json"))
        except (tarfile.TarError, OSError, EOFError, ValueError) as e:
            return [f"not a readable backup: {e}"]
        db_path = Path(tmp) / "pilot.db"
        if hashlib.sha256(db_path.read_bytes()).hexdigest() != manifest["db_sha256"]:
            problems.append("database checksum does not match the manifest")
        conn = sqlite3.connect(str(db_path))
        try:
            check = conn.execute("PRAGMA integrity_check").fetchone()[0]
        finally:
            conn.close()
        if check != "ok":
            problems.append(f"integrity_check: {check}")
        if row_counts(db_path) != manifest["row_counts"]:
            problems.append("row counts differ from the manifest")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data-dir", type=Path, default=default_data_dir())
    ap.add_argument("--out", type=Path, required=False)
    ap.add_argument("--photos", action="store_true", help="also include uploads/ (photos; may show building names)")
    ap.add_argument("--verify", type=Path, help="check an existing backup instead of making one")
    a = ap.parse_args(argv)
    if a.verify:
        problems = verify_backup(a.verify)
        print("OK" if not problems else "PROBLEMS: " + "; ".join(problems))
        return 1 if problems else 0
    if a.out is None:
        ap.error("--out is required")
    path = make_backup(a.data_dir, a.out, photos=a.photos)
    with tarfile.open(path) as tar:
        manifest = json.load(tar.extractfile("MANIFEST.json"))
    print(f"{path}  ({path.stat().st_size:,} bytes)  verified")
    print("rows:", ", ".join(f"{t}={n}" for t, n in manifest["row_counts"].items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
