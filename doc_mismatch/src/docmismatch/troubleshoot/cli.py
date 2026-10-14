"""Command-line front end. Interactive:  python -m docmismatch.troubleshoot --building examples/troubleshoot_example/building.json
Scripted demo with a simulated technician:  python -m docmismatch.troubleshoot --demo
The technician sees one suggested check at a time and answers y / n / u (unsure) / s (skip) / a (add equipment I found) / q (quit)."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from . import model as M
from .building import Building, load_building, make_case
from .session import Session

EXAMPLE = Path(__file__).resolve().parents[3] / "examples" / "troubleshoot_example" / "building.json"
KEYS = {"y": "yes", "yes": "yes", "n": "no", "no": "no", "u": "unsure", "unsure": "unsure", "s": "skip", "skip": "skip"}


def _ranked(sess: Session, out, n: int = 3) -> None:
    b, c = sess.case.building, sess.case
    names = {"wrong": lambda x: f"fed by {b.label(x[1])} instead", "unlisted": lambda x: "fed by something not on the list", "doc_acts_fail": lambda x: f"{b.label(c.doc)} feeds it but does not act",
             "doc_other": lambda x: f"{b.label(c.doc)} feeds it and acts (cause is elsewhere)", "doc_ok": lambda x: f"{b.label(c.doc)} is right"}
    out("  belief now: " + " | ".join(f"{names[k[0]](k)} {p:.0%}" for k, p in sess.status()["ranked"][:n]))


def run(sess: Session, input_fn=input, out=print) -> dict:
    """Step through a session. `input_fn` / `out` are injectable so the loop can be tested with scripted answers. Returns the final status."""
    c = sess.case
    out(f"\nComplaint: {c.member_name}. The drawings say it is fed by {c.building.label(c.doc)}.")
    out(f"Could be fed by: {', '.join(c.building.label(x) for x in c.candidates)}.")
    while True:
        st = sess.status()
        if st["concluded"]:
            out(f"\nLikely cause: {st['conclusion']}")
            break
        rec = sess.recommend()
        if rec is None:
            out("\nNo further check on the list would change the picture.")
            _ranked(sess, out)
            break
        out(f"\nNext check (about {rec.minutes:.0f} min): {rec.text}")
        out(f"  {rec.why}")
        while True:
            try:
                ans = input_fn("  Result? [y]es / [n]o / [u]nsure / [s]kip / [a]dd equipment / [q]uit > ").strip().lower()
            except EOFError:
                ans = "q"
            if ans in KEYS:
                sess.report(KEYS[ans])
                break
            if ans in ("q", "quit"):
                out("\nStopped.")
                _ranked(sess, out)
                return sess.status()
            if ans in ("a", "add"):
                eid = input_fn("  Equipment id to add > ").strip()
                try:
                    sess.add_candidate(eid)
                    out(f"  Added {eid}; earlier answers were re-scored with it included.")
                    rec = sess.recommend()
                except (KeyError, ValueError) as e:
                    out(f"  Could not add: {e}")
                if rec is None:
                    break
                out(f"\nNext check (about {rec.minutes:.0f} min): {rec.text}")
                continue
            out("  Please answer y, n, u, s, a or q.")
        _ranked(sess, out)
    st = sess.status()
    out(f"\nSo far: {st['n_checks']} checks, about {st['elapsed']:.0f} minutes, {st['entries']} entries typed.")
    return st


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Technician-guided troubleshooting, working model v0 (placeholder numbers; see TROUBLESHOOT.md)")
    ap.add_argument("--building", type=Path, default=EXAMPLE, help="building JSON (equipment list and the drawings' claims)")
    ap.add_argument("--slot", choices=sorted(M.SLOT_OWNER_KIND), default="vav_zone")
    ap.add_argument("--member", help="the room (vav_zone) or box (ahu_vav) with the complaint")
    ap.add_argument("--airflow", choices=["yes", "no", "unsure"], help="is air coming out of the diffuser?")
    ap.add_argument("--drawings", choices=sorted(M.DRAWINGS), default="mixed", help="how far do you trust this building's drawings? (mixed = the default prior; placeholder levels)")
    ap.add_argument("--nearness", choices=["area", "id"], default="area", help="rank candidates by shared area (default) or by distance in id order (placeholder decay)")
    ap.add_argument("--id-decay", type=float, default=4.0, help="with --nearness id: a candidate k places away in id order counts exp(-k / decay) of the documented one")
    ap.add_argument("--strategy", choices=M.STRATEGIES, default="entropy")
    ap.add_argument("--demo", action="store_true", help="answer for the technician: the room is really fed by another box")
    a = ap.parse_args(argv)
    b: Building = load_building(a.building)
    member = a.member
    if member is None:
        options = b.members(a.slot)
        print("Where is the problem? Options: " + ", ".join(options))
        member = input("> ").strip() if not a.demo else ("Room-204" if "Room-204" in options else options[0])
    case = make_case(b, member, a.slot, M.Settings(nearness=a.nearness, id_decay=a.id_decay).with_drawings(a.drawings), airflow=a.airflow)
    sess = Session(case, a.strategy)
    if a.demo:
        from .sim import technician_input
        truth = ("wrong", case.candidates[1]) if len(case.candidates) > 1 else sess.posterior()[0][0]
        print(f"[demo] simulated technician; the room is really fed by {b.label(truth[1])}")
        run(sess, technician_input(sess, truth, np.random.default_rng(3)))
    else:
        run(sess)


if __name__ == "__main__":
    main()
