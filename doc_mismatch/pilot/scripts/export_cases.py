"""Export the case record for analysis, anonymized. Run it on your own machine against a backup (see backup.py), not on
the server; there is deliberately no HTTP export endpoint.

    cd doc_mismatch && ../.venv/bin/python -m pilot.scripts.export_cases --data-dir <unpacked backup> --out <folder>

Writes cases.jsonl (one case per line: the whole sequence, in order), cases.csv (one row per case: completeness and the
verification ladder), checks.csv (one row per step) and SUMMARY.txt.

Each case carries `complete`: true only when it has every link of the sequence this dataset exists for:
complaint -> a timed check with a result -> a confirmed root cause -> a repair -> the complaint confirmed fixed.

Each case also carries `verification` (see pilot/ladder.py): how far the root-cause label was actually checked, as four
independent rungs (suspected, physically confirmed BEFORE the repair, repair-confirmed, stayed fixed at follow-up), the
highest `level` reached, and `caveats` that weaken it (multi_action_repair, cause_revised, pre_repair_unknown,
repair_did_not_fix, recheck_contradicts_fix, recurred_within_N_days ...). `topology` is what the drawings claim for the room (AHU, box, room, which BAS points exist, reheat), what
the topology-verifying checks said (duct_trace direct; the two commanding checks indirect, where a "no" is inconclusive),
and `verified`: whether the drawings were wrong, right, suspected wrong or unverified, and on what basis. `rechecks` lists the one-tap re-checks (the test that found
the fault, repeated after the repair: now_ok / still_wrong / unsure) and `verification.recheck` summarizes them; a re-check only ever
adds a caveat and never grants a rung. `complete` and the ladder answer different questions: `complete` is
whether the chain of records exists; the ladder is how far to trust its label. Filter on the caveats you will not accept.

ANONYMIZATION happens before anything is written. Equipment, room and BAS point names are replaced with aliases
assigned per visit (ahu_1, vav_1, room_1, point_1), so the same alias in two visits does NOT mean the same equipment; to
follow a repeat failure use `prior_case_id`. Emails and phone numbers in free text are masked, and photos, raw vision
output and file paths are never exported. Free text cannot be
made safe by pattern: a name typed into a note survives. Read the free-text fields before sharing a file, or pass
--drop-free-text to leave them out. Cases with no acknowledged participant are excluded unless you ask.
"""
import argparse
import csv
import json
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from .. import db
from .. import topology as TOPO
from ..ladder import LEVEL_NAMES, verification
from .backup import default_data_dir

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE = re.compile(r"(?<![\w.])(?:\+?\d{1,2}[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]?\d{3}[\s.-]?\d{4}(?![\w])")
FREE_TEXT_KEYS = {"complaint_text", "alarms_text", "text", "note", "external_text", "result_text", "reading_text", "other"}
ALIAS_PREFIX = {"AHU": "ahu", "VAV": "vav", "Zone": "room"}
MIN_ALIAS_LEN = 3                       # shorter ids would match inside ordinary words


# ------------------------------------------------------------------------------------------------- anonymization

def build_aliases(building: dict) -> dict[str, str]:
    aliases, counts = {}, {k: 0 for k in ALIAS_PREFIX}
    for eq in building.get("equipment", []):
        kind = eq.get("kind")
        if kind in ALIAS_PREFIX and eq.get("id") and eq["id"] not in aliases:
            counts[kind] += 1
            aliases[eq["id"]] = f"{ALIAS_PREFIX[kind]}_{counts[kind]}"
    n = 0
    for pts in ((building.get("control_system") or {}).get("points") or {}).values():
        for tag in pts.values():
            if tag and tag not in aliases:
                n += 1
                aliases[tag] = f"point_{n}"
    return aliases


def make_scrubber(aliases: dict[str, str]):
    keys = sorted((k for k in aliases if len(k) >= MIN_ALIAS_LEN), key=len, reverse=True)
    pattern = re.compile(r"(?<![A-Za-z0-9])(" + "|".join(re.escape(k) for k in keys) + r")(?![A-Za-z0-9])") if keys else None

    def scrub_str(s: str) -> str:
        if pattern:
            s = pattern.sub(lambda m: aliases[m.group(1)], s)
        return PHONE.sub("[phone]", EMAIL.sub("[email]", s))

    def walk(o):
        if isinstance(o, str):
            return scrub_str(o)
        if isinstance(o, list):
            return [walk(x) for x in o]
        if isinstance(o, dict):
            return {k: walk(v) for k, v in o.items()}
        return o
    return walk


def drop_free_text(o):
    if isinstance(o, list):
        return [drop_free_text(x) for x in o]
    if isinstance(o, dict):
        return {k: (None if k in FREE_TEXT_KEYS and v else drop_free_text(v)) for k, v in o.items()}
    return o


# ------------------------------------------------------------------------------------------------- assembling a case

def _t(e) -> datetime:
    return datetime.fromisoformat(e["server_ts"])


def _fresh():
    return dict(intent=None, shown=None, decision=None, started=None)


def _step_common(cur) -> dict:
    sh = cur["shown"]["payload"] if cur["shown"] else None
    it = cur["intent"]["payload"] if cur["intent"] else None
    dec = cur["decision"]["payload"] if cur["decision"] else None
    return dict(
        intent=it,
        suggested=None if sh is None else dict(check=sh["check"], target=sh["target"], text=sh["text"], modeled_minutes=sh["minutes"], p_pos=sh["p_pos"],
                                               gain=sh["gain"], ranked=sh["ranked"], intent_matches=sh.get("intent_matches")),
        decision=None if dec is None else dict(action=dec["action"], reason=dec.get("reason"), note=dec.get("note")),
    )


def build_steps(events: list[dict]) -> list[dict]:
    """The case's events as ordered steps. A step ends with a result, a skip, or a question answer; an off-catalogue
    check ends only its own timer, and the suggestion it was a response to stays attached to the next step."""
    steps, cur = [], _fresh()

    def timing(started, ended, correction):
        if started is None:
            return dict(started_at=None, resulted_at=ended["server_ts"], seconds=None, minutes_correction=correction, effective_minutes=correction)
        secs = round((_t(ended) - _t(started)).total_seconds(), 1)
        return dict(started_at=started["server_ts"], resulted_at=ended["server_ts"], seconds=secs, minutes_correction=correction,
                    effective_minutes=correction if correction is not None else round(secs / 60, 2))

    for e in events:
        k, p = e["kind"], e["payload"]
        if k == "intent":
            cur["intent"] = e
        elif k == "suggestion_shown":
            cur["shown"] = e
        elif k == "decision":
            cur["decision"] = e
            if p["action"] == "skip":
                steps.append(dict(type="skipped", at=e["server_ts"], check=p["check"], target=p["target"], **_step_common(cur)))
                cur = _fresh()
        elif k == "check_started":
            cur["started"] = e
        elif k == "check_result":
            common = _step_common(cur)
            it, sh = common["intent"], common["suggested"]
            steps.append(dict(
                type="check", check=p["check"], target=p["target"], word=p["word"], reading_text=p.get("reading_text"), note=p.get("note"),
                modeled_minutes=p.get("modeled_minutes"), followed_suggestion=p.get("followed_suggestion"),
                intent_matched_action=None if not it or it.get("choice") != "check" else it.get("check") == p["check"],
                **timing(cur["started"], e, p.get("minutes_correction")), **common))
            cur = _fresh()
        elif k == "external_result":
            steps.append(dict(type="external", external_text=p.get("external_text"), result_text=p.get("result_text"), note=p.get("note"),
                              **timing(cur["started"], e, p.get("minutes_correction")), **_step_common(cur)))
            cur["decision"] = cur["started"] = None
        elif k == "question_answer":
            steps.append(dict(type="question", at=e["server_ts"], key=p["key"], answer=p["answer"]))
            cur = _fresh()
    if any(cur.values()):
        steps.append(dict(type="open", stage="in_progress" if cur["decision"] else "revealed" if cur["intent"] else "none", **_step_common(cur)))
    for i, s in enumerate(steps, 1):
        s["n"] = i
    return steps


def _latest(events, kind):
    return next((e["payload"] for e in reversed(events) if e["kind"] == kind), None)


def build_case(case: dict, events: list[dict], visit: dict | None, participant: dict | None, building: dict | None = None) -> dict:
    steps = build_steps(events)
    rc, rp, oc, tool = _latest(events, "root_cause"), _latest(events, "repair"), _latest(events, "outcome"), _latest(events, "tool_conclusion")
    feel = (visit or {}).get("feel")
    completeness = dict(
        complaint=bool(case["complaint_text"]) or feel in ("too_hot", "too_cold"),
        timed_check=any(s["type"] == "check" and s["seconds"] is not None for s in steps),
        root_cause=rc is not None and rc["cause_id"] != "not_determined",
        repair=rp is not None,
        confirmed_fixed=oc is not None and oc["fixed"] == "yes")
    load = lambda s: json.loads(s) if s else None          # noqa: E731
    rooms = json.loads(visit["room_ids_json"]) if visit else []
    topology = (TOPO.build(building, rooms[case["room_index"]], events, case["system_kind"], rooms)
                if building is not None and case["room_index"] < len(rooms) else None)
    return dict(
        case_id=case["id"], prior_case_id=case["prior_case_id"], data_version=case["data_version"], catalogue_hash=case["catalogue_hash"],
        participant=None if participant is None else {k: participant[k] for k in ("role", "years_band", "vav_band")},
        opened_at=case["opened_at"], closed_at=case["closed_at"], status=case["status"],
        visit=dict(feel=feel, airflow=(visit or {}).get("airflow"), n_rooms=len(json.loads(visit["room_ids_json"])) if visit else None),
        context=dict(complaint_text=case["complaint_text"], complaint_source=case["complaint_source"], building_type=case["building_type"],
                     system_kind=case["system_kind"], equipment_age_band=case["equipment_age_band"], readings=load(case["readings_json"]),
                     alarms_text=case["alarms_text"], own_hypotheses=load(case["own_hypotheses_json"])),
        steps=steps, tool_conclusion=tool, root_cause=rc, repair=rp, outcome=oc,
        verification={k: v for k, v in verification(events).items() if k != "lines"}, topology=topology,
        rechecks=[e["payload"] | {"at": e["server_ts"]} for e in events if e["kind"] == "post_repair_check"],
        followups=[e["payload"] | {"at": e["server_ts"]} for e in events if e["kind"] == "followup"],
        completeness=completeness, complete=all(completeness.values()))


CSV_COLUMNS = ["case_id", "step", "type", "check", "target", "intent_choice", "intent_check", "suggested_check", "suggested_modeled_minutes", "suggested_p_pos",
               "intent_matched_suggestion", "decision", "reason", "followed_suggestion", "intent_matched_action", "word", "reading_text", "started_at",
               "resulted_at", "seconds", "minutes_correction", "effective_minutes", "modeled_minutes"]


CASE_COLUMNS = ["case_id", "complete", "ladder_level", "ladder_name", "suspected", "physically_confirmed", "repair_confirmed", "stayed_fixed", "stayed_fixed_days",
                "caveats", "recheck_state", "drawings_status", "drawings_basis", "drawings_conflict", "actual_box_known", "n_boxes_on_ahu_seen",
                "visit_rooms_on_same_ahu", "reheat_declared", "topology_checks", "root_cause", "in_taxonomy", "how_confirmed", "confirmed_before_repair", "agrees_with_tool", "fixed", "n_steps", "n_timed_checks",
                "effective_minutes", "role", "years_band", "vav_band", "building_type", "system_kind", "prior_case_id"]


def topology_columns(topo: dict | None) -> dict:
    if topo is None:
        return dict(drawings_status=None, drawings_basis=None, drawings_conflict=None, actual_box_known=None, n_boxes_on_ahu_seen=None,
                    visit_rooms_on_same_ahu=None, reheat_declared=None, topology_checks=None)
    v, d = topo["verified"], topo["documented"]
    return dict(drawings_status=v["status"], drawings_basis=v["basis"], drawings_conflict=v["conflict"],
                actual_box_known=v["actual_box"] not in (None, *TOPO.SENTINELS) if v["status"] == "wrong" else None,
                n_boxes_on_ahu_seen=d["n_boxes_on_ahu_seen"], visit_rooms_on_same_ahu=d["visit_rooms_on_same_ahu"],
                reheat_declared=topo["reheat"]["declared"], topology_checks=len(topo["evidence"]))


def case_row(rec: dict) -> dict:
    v, rc, oc, p, ctx = rec["verification"], rec["root_cause"] or {}, rec["outcome"] or {}, rec["participant"] or {}, rec["context"]
    timed = [s for s in rec["steps"] if s["type"] == "check" and s["seconds"] is not None]
    return dict(case_id=rec["case_id"], complete=rec["complete"], ladder_level=v["level"], ladder_name=v["name"], **v["rungs"],
                stayed_fixed_days=v["stayed_fixed_days"], caveats=";".join(v["caveats"]), recheck_state=v["recheck"]["state"], **topology_columns(rec["topology"]), root_cause=rc.get("cause_id"), in_taxonomy=rc.get("in_taxonomy"),
                how_confirmed=rc.get("how_confirmed"), confirmed_before_repair=rc.get("confirmed_before_repair"), agrees_with_tool=rc.get("agrees_with_tool"),
                fixed=oc.get("fixed"), n_steps=len(rec["steps"]), n_timed_checks=len(timed),
                effective_minutes=round(sum(s["effective_minutes"] or 0 for s in timed), 2), role=p.get("role"), years_band=p.get("years_band"),
                vav_band=p.get("vav_band"), building_type=ctx["building_type"], system_kind=ctx["system_kind"], prior_case_id=rec["prior_case_id"])


def csv_rows(rec: dict):
    for s in rec["steps"]:
        it, sh, dec = s.get("intent") or {}, s.get("suggested") or {}, s.get("decision") or {}
        yield dict(case_id=rec["case_id"], step=s["n"], type=s["type"], check=s.get("check"), target=s.get("target"), intent_choice=it.get("choice"),
                   intent_check=it.get("check"), suggested_check=sh.get("check"), suggested_modeled_minutes=sh.get("modeled_minutes"),
                   suggested_p_pos=sh.get("p_pos"), intent_matched_suggestion=sh.get("intent_matches"), decision=dec.get("action"), reason=dec.get("reason"),
                   followed_suggestion=s.get("followed_suggestion"), intent_matched_action=s.get("intent_matched_action"), word=s.get("word"),
                   reading_text=s.get("reading_text"), started_at=s.get("started_at"), resulted_at=s.get("resulted_at"), seconds=s.get("seconds"),
                   minutes_correction=s.get("minutes_correction"), effective_minutes=s.get("effective_minutes"), modeled_minutes=s.get("modeled_minutes"))


# ------------------------------------------------------------------------------------------------- the export

def export(data_dir: Path, out_dir: Path, *, include_unacknowledged: bool = False, drop_text: bool = False) -> dict:
    db_path = data_dir / "pilot.db"
    if not db_path.exists():
        raise SystemExit(f"no database at {db_path}")
    out_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    stats = dict(cases=0, exported=0, complete=0, excluded_unacknowledged=0, excluded_no_building=0, steps=0, timed_checks=0, ladder=[0] * 5)
    try:
        with open(out_dir / "cases.jsonl", "w") as jl, open(out_dir / "checks.csv", "w", newline="") as cf, \
                open(out_dir / "cases.csv", "w", newline="") as kf:
            writer = csv.DictWriter(cf, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            case_writer = csv.DictWriter(kf, fieldnames=CASE_COLUMNS)
            case_writer.writeheader()
            for row in conn.execute("SELECT * FROM cases ORDER BY id").fetchall():
                case = dict(row)
                stats["cases"] += 1
                part = conn.execute("SELECT * FROM participants WHERE id = ?", (case["participant_id"],)).fetchone()
                if not include_unacknowledged and (part is None or part["notice_ack_at"] is None):
                    stats["excluded_unacknowledged"] += 1
                    continue
                bpath = data_dir / "visits" / case["visit_id"] / "building.json"
                if not bpath.exists():
                    stats["excluded_no_building"] += 1          # cannot alias what cannot be listed: never export it raw
                    continue
                visit = conn.execute("SELECT * FROM visits WHERE id = ?", (case["visit_id"],)).fetchone()
                events = db.get_events(conn, case["id"])
                building = json.loads(bpath.read_text())
                rec = build_case(case, events, dict(visit) if visit else None, dict(part) if part else None, building)
                rec = make_scrubber(build_aliases(building))(rec)
                if drop_text:
                    rec = drop_free_text(rec)
                jl.write(json.dumps(rec, sort_keys=True) + "\n")
                for r in csv_rows(rec):
                    writer.writerow(r)
                case_writer.writerow(case_row(rec))
                stats["ladder"][rec["verification"]["level"]] += 1
                stats["exported"] += 1
                stats["complete"] += rec["complete"]
                stats["steps"] += len(rec["steps"])
                stats["timed_checks"] += sum(1 for s in rec["steps"] if s["type"] == "check" and s["seconds"] is not None)
    finally:
        conn.close()
    lines = [f"cases in database: {stats['cases']}", f"exported: {stats['exported']} ({stats['complete']} complete)",
             f"steps: {stats['steps']}, of which timed checks: {stats['timed_checks']}",
             "verification ladder, cases at each level: " + ", ".join(f"{name} {n}" for name, n in zip(LEVEL_NAMES, stats["ladder"])),
             f"excluded, participant not acknowledged: {stats['excluded_unacknowledged']}",
             f"excluded, building file missing (cannot be anonymized): {stats['excluded_no_building']}",
             "free text: " + ("DROPPED" if drop_text else "kept (read it before sharing)")]
    (out_dir / "SUMMARY.txt").write_text("\n".join(lines) + "\n")
    return stats


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data-dir", type=Path, default=default_data_dir(), help="folder holding pilot.db and visits/ (e.g. an unpacked backup)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--include-unacknowledged", action="store_true", help="also export cases whose participant never acknowledged the notice")
    ap.add_argument("--drop-free-text", action="store_true")
    a = ap.parse_args(argv)
    export(a.data_dir, a.out, include_unacknowledged=a.include_unacknowledged, drop_text=a.drop_free_text)
    print((a.out / "SUMMARY.txt").read_text(), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
