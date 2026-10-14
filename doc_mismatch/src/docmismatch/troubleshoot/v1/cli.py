"""Command-line front end for working model v1.
Interactive:  python -m docmismatch.troubleshoot.v1 --building examples/troubleshoot_example/building_v1.json --member Room-204
Scripted demo with a simulated technician:  python -m docmismatch.troubleshoot.v1 --demo --tier T3 --truth low_static
For each check: y / n (or a / n for a reading), a number (a reading, compared with its expected value), u (unsure), s (skip), + (add equipment I found), q (quit)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .. import model as M
from . import causes as C
from . import data as D
from .engine import RELIABILITY_NOTE, Question, Recommendation, Session, make_case_v1
from . import sim1, tables

EXAMPLE = Path(__file__).resolve().parents[4] / "examples" / "troubleshoot_example" / "building_v1.json"
V0_KEYS = {"y": "yes", "yes": "yes", "n": "no", "no": "no", "u": "unsure", "unsure": "unsure", "s": "skip", "skip": "skip"}
READ_KEYS = {"a": "abnormal", "abnormal": "abnormal", "y": "abnormal", "yes": "abnormal", "n": "normal", "normal": "normal", "no": "normal", "u": "unsure", "unsure": "unsure",
             "s": "skip", "skip": "skip"}


def _ranked(sess: Session, out, n: int = 3) -> None:
    out("  belief now: " + " | ".join(f"{C.cause_text(c) if c[0] != 'wrong' else 'fed by ' + sess.label(c[1])} {p:.0%}" for c, p in sess.status()["ranked"][:n]))


def _add_equipment(sess: Session, input_fn, out) -> None:
    if not sess.case.docs:
        out("  There is no equipment list at this tier, so there is nothing to add to.")
        return
    eid = input_fn("  Equipment id to add > ").strip()
    try:
        if sess.case.building is not None and eid in sess.case.building.base.equipment:
            sess.add_candidate(eid)
            out(f"  Added {eid}; earlier answers were re-scored with it included.")
        else:
            if input_fn(f"  {eid!r} is not on the equipment list. Record it as an undocumented box? [y/n] > ").strip().lower() in ("y", "yes"):
                sess.add_equipment(eid)
                out(f"  Recorded {eid} as undocumented equipment and added it as a candidate.")
    except (KeyError, ValueError) as e:
        out(f"  Could not add: {e}")


def _answer_check(sess: Session, rec: Recommendation, input_fn, out) -> str:
    """Take the technician's answer to one check. Returns 'answered', 'changed' (equipment was added: recommend again) or 'quit'."""
    ck = rec.check
    yn = "[y]es / [n]o" if not ck.is_reading else "[a]bnormal / [n]ormal / a number"
    keys = READ_KEYS if ck.is_reading else V0_KEYS
    while True:
        try:
            ans = input_fn(f"  Result? {yn} / [u]nsure / [s]kip / [+] add equipment / [q]uit > ").strip().lower()
        except EOFError:
            ans = "q"
        if ans in keys:
            sess.report(keys[ans])
            return "answered"
        if ans in ("q", "quit"):
            return "quit"
        if ans in ("+", "add"):
            _add_equipment(sess, input_fn, out)
            return "changed"
        if ck.reading is not None:
            try:
                value = float(ans)
            except ValueError:
                value = None
            if value is not None:
                expected = None
                if ck.reading.band(sess._attrs(sess._eq(ck))) is None:
                    try:
                        expected = float(input_fn("  Expected value to compare with > ").strip())
                    except ValueError:
                        out("  That is not a number.")
                        continue
                try:
                    sess.report(reading=value, expected=expected)
                    return "answered"
                except ValueError as e:
                    out(f"  {e}")
                    continue
        out("  Please answer " + ("a, n, a number, u, s, + or q." if ck.is_reading else "y, n, u, s, + or q."))


def run(sess: Session, input_fn=input, out=print) -> dict:
    """Step through a session. `input_fn` / `out` are injectable so the loop can be tested with scripted answers. Returns the final status."""
    c = sess.case
    out(f"\nComplaint: {c.member_name}. Data available: tier {c.tier}.")
    if c.docs:
        out(f"The drawings say it is fed by {sess.label(c.doc)}. Could be fed by: {', '.join(sess.label(x) for x in sess.candidates)}.")
    else:
        out("No equipment list or drawings claim on file: working on whichever box you find serving the room.")
    while True:
        step = sess.next_step()
        if step is None:
            st = sess.status()
            if st["concluded"]:
                out(f"\nLikely cause: {st['conclusion']}")
            else:
                out("\nNo further check is worth its time." if st["stalled"] else "\nStopped.")
                _ranked(sess, out)
            break
        if isinstance(step, Question):
            out(f"\n{step.text}  ({step.why})")
            try:
                ans = input_fn("  [y]es / [n]o / [s]kip (counts as no) > ").strip().lower()
            except EOFError:
                ans = "q"
            if ans in ("q", "quit"):
                out("\nStopped.")
                _ranked(sess, out)
                break
            sess.declare(step.key, "yes" if ans in ("y", "yes") else "no")
            continue
        out(f"\nNext check (about {step.minutes:.0f} min): {step.text}")
        out(f"  {step.why}")
        res = _answer_check(sess, step, input_fn, out)
        if res == "quit":
            out("\nStopped.")
            _ranked(sess, out)
            break
        if res == "answered":
            _ranked(sess, out)
    st = sess.status()
    out(f"\nSo far: {st['n_checks']} checks, about {st['elapsed']:.0f} minutes, {st['entries']} entries typed.")
    if st["n_checks"]:
        out(f"  Note: {RELIABILITY_NOTE}")
    for e in sess.events:
        out(f"  Discrepancy logged: {e.type} {json.dumps(e.data)}")
    return st


def _parse_context(s: str | None) -> D.Context:
    ctx = D.Context()
    for part in filter(None, (s or "").split(",")):
        k, _, v = part.partition("=")
        ctx = ctx.declare(k.strip(), v.strip())
    return ctx


def _parse_truth(s: str) -> tuple:
    if s.startswith("wrong:"):
        return ("wrong", s.split(":", 1)[1])
    if s in ("unlisted", C.ACTS_FAIL, C.OTHER) or s in C.BY_ID:
        return (s,)
    raise SystemExit(f"--truth must be a cause id ({', '.join(sorted(C.BY_ID))}), 'unlisted' or 'wrong:<box id>', not {s!r}")


def _auto_tier(b: D.Building1) -> str:
    return "T3" if b.points else "T2" if b.attrs else "T1"


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Technician-guided troubleshooting, working model v1 (placeholder numbers; see TROUBLESHOOT_V1.md)")
    ap.add_argument("--building", type=Path, default=EXAMPLE, help="building JSON (v0's, plus optional attributes and a control-system point map)")
    ap.add_argument("--tier", choices=["auto", *D.TIERS], default="auto", help="what data the tool may use (auto: the richest the building file supports)")
    ap.add_argument("--member", help="the room with the complaint")
    ap.add_argument("--room-name", help="T0 only: what to call the room")
    ap.add_argument("--airflow", choices=["yes", "no", "unsure"], help="is air coming out of the diffuser?")
    ap.add_argument("--feel", choices=["too_hot", "too_cold", "unsure"], help="what is the complaint?")
    ap.add_argument("--context", help="facts to declare up front, e.g. reheat=no,instrument=yes,bas_access=no,occupant=yes")
    ap.add_argument("--strategy", choices=M.STRATEGIES, default="entropy")
    ap.add_argument("--drawings", choices=sorted(M.DRAWINGS), default="mixed", help="how far you trust the drawings (v0's placeholder prior levels)")
    ap.add_argument("--nearness", choices=["area", "id"], default="area")
    ap.add_argument("--id-decay", type=float, default=4.0)
    ap.add_argument("--min-rate", type=float, help="stop when no check is expected to add this many bits per minute (default 0.003; 0 switches the stop off)")
    ap.add_argument("--compat-v0", action="store_true", help="the v0-equivalent tree and checks (reproduces v0)")
    ap.add_argument("--demo", action="store_true", help="answer for the technician (a simulated one; an illustration, not a result)")
    ap.add_argument("--truth", default="low_static", help="--demo: the real cause: a cause id, 'unlisted' or 'wrong:<box id>'")
    ap.add_argument("--noise", action="store_true", help="--demo: draw each answer from its response probability (default: the most likely answer)")
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--export", type=Path, help="write the session (checks, events, conclusion) as JSON")
    ap.add_argument("--tables", action="store_true", help="print the cause, check, reading and tier tables as markdown, and exit")
    a = ap.parse_args(argv)
    if a.tables:
        for name, t in tables.all_tables().items():
            print(f"<!-- BEGIN:{name} -->\n{t}\n<!-- END:{name} -->\n")
        return
    b = D.load_building_v1(a.building)
    tier = _auto_tier(b) if a.tier == "auto" else a.tier
    docs = "claims" in D.tier_items(tier)
    member = a.member
    if member is None:
        options = b.base.members("vav_zone")
        print("Where is the problem? Options: " + ", ".join(options))
        member = input("> ").strip() if not a.demo else ("Room-204" if "Room-204" in options else options[0])
    settings = M.Settings(nearness=a.nearness, id_decay=a.id_decay).with_drawings(a.drawings)
    case = make_case_v1(b, member, tier, settings, a.airflow, a.feel, _parse_context(a.context), compat_v0=a.compat_v0, member_name=a.room_name, min_rate=a.min_rate)
    sess = Session(case, a.strategy)
    if a.demo:
        truth = _parse_truth(a.truth)
        attr = b.attrs.get(case.doc, {}).get("reheat") if docs else None
        ctx = dict(reheat="no" if attr == "none" else "yes", bas_access="yes" if "bas_access" in D.tier_items(tier) else "no", instrument="yes", occupant="yes")
        world = sim1.World(truth, ctx)
        sim1.check_world(case, world)
        print(f"[demo] simulated technician; the real cause is {C.cause_text(truth) if truth[0] != 'wrong' else 'fed by ' + truth[1]}" + ("" if a.noise else " (each check answered with its most likely result)"))
        run(sess, sim1.technician_input(sess, world, np.random.default_rng(a.seed) if a.noise else None))
    else:
        run(sess)
    if a.export:
        a.export.write_text(json.dumps(sess.export(), indent=1))


if __name__ == "__main__":
    main()
