"""Command-line front end for working model v2: one visit, several complaints, one investigation. Placeholder numbers throughout; see TROUBLESHOOT_V2.md.
Interactive:  python -m docmismatch.troubleshoot.v2 --building examples/troubleshoot_example/building_v2.json --complaints Room-1,Room-2,Room-3
Scripted demo with a simulated technician:  python -m docmismatch.troubleshoot.v2 --demo --tier T3 --complaints Room-0,Room-1,Room-2,Room-3 --truth low_static,low_static,low_static,low_static
For each check: y / n (or a / n for a reading), u (unsure), q (quit)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .. import model as M
from ..v1 import catalogue as K
from ..v1 import causes as C
from ..v1 import data as D
from ..v1.engine import RELIABILITY_NOTE, make_case_v1
from .joint import JointSession, JointSettings, JOption

EXAMPLE = Path(__file__).resolve().parents[4] / "examples" / "troubleshoot_example" / "building_v2.json"
# The live tool's default `min_rate` (PREREGISTRATION_DR.md, 2026-09-27, raised again 2026-09-29). 0.01 is confirmed across all 18 of Addendum 30's cells at both tiers (Addendum 35).
# 0.015 was a further step the user chose directly, checked only on the primary cell (Addendum 36 later found it NOT confirmed at the same 18-cell bar for T2, though T3 stayed clean).
# 0.02 is a further step still, taken for the user's own documentation profile (Exploratory note E2's "T3-noattr": BAS access + a point map, no attributes -- the common case per the
# user's own buildings): a fine sweep plus a 5-cell spot-check found it closes T3-noattr's gap against a language-model comparison for a small (<2pt) accuracy cost and no safety cost.
# T3 with real attributes tolerates 0.02 about as well as it tolerated 0.015 (a further ~0.6pt cost, primary cell); T2 (no BAS access at all, rare in the user's own buildings) takes a
# bigger additional hit (~1.8pt beyond 0.015's own cost, primary cell, not confirmed across the other 17 cells) -- a known, disclosed tradeoff, not an oversight. Named here (not just
# inlined in argparse) so other code (e.g. scripts/80) reads the live default from one place instead of duplicating the number.
LIVE_MIN_RATE_DEFAULT = 0.02
KEYS = {"y": "positive", "yes": "positive", "a": "positive", "abnormal": "positive", "n": "negative", "no": "negative", "normal": "negative", "u": "unsure", "unsure": "unsure"}
JOINT_NOTE = ("The joint model assumes each air handler is faulty with probability f in the visit's window, that a room on a faulty air handler complains with a stated probability, and that the "
              "drawings' air handler for every box is right; all of these are placeholders, not measurements.")


def _cause_text(sess: JointSession, i: int, cause: tuple) -> str:
    c = sess.model.cases[i]
    if cause[0] == "wrong":
        return f"fed by {c.label(cause[1])} instead of {c.label(c.doc)}"
    return C.cause_text(cause)


def _belief(sess: JointSession, out, top: int = 2) -> None:
    marg = sess.marginals()
    for i, m in enumerate(marg):
        order = np.argsort(-m, kind="stable")[:top]
        out(f"  {sess.model.cases[i].member_name}: " + " | ".join(f"{_cause_text(sess, i, sess.model.causes[i][j])} {m[j]:.0%}" for j in order))
    post = sess.model.ahu_posterior(sess.state)
    out("  air handlers: " + ", ".join(f"{sess.model.cases[sess.model.groups[a][0]].label(a)}: fan off {w[1]:.0%}, low static {w[2]:.0%}" for a, w in post.items()))


def describe_option(sess: JointSession, o: JOption) -> str:
    m = sess.model
    if o.kind == "complaint":
        c = m.cases[o.who]
        return o.check.describe(f"box {c.label(c.doc)}", c.label(o.target), c.member_name, c.label(c.ahu))
    c = m.cases[m.groups[o.who][0]]
    rooms = ", ".join(m.cases[i].member_name for i in m.groups[o.who])
    return o.check.describe(f"box {c.label(c.doc)}", c.label(c.doc), c.member_name, c.label(o.who)) + f"  [one reading speaks for: {rooms}]"


def run(sess: JointSession, input_fn=input, out=print) -> dict:
    """Step through a visit. `input_fn` / `out` are injectable so the loop can be tested with scripted answers. Returns the final status."""
    m = sess.model
    out(f"\nVisit with {m.n} complaint{'s' if m.n > 1 else ''}: " + "; ".join(f"{c.member_name} (drawings: {c.label(c.doc)} on {c.label(c.ahu)})" for c in m.cases) + ".")
    while True:
        o = sess.recommend()
        if o is None:
            st = sess.status()
            out("\nEvery complaint has a likely cause." if st["concluded"] else ("\nNo further check is worth its time." if st["stalled"] else "\nStopped at the check limit."))
            _belief(sess, out, 3)
            break
        for_whom = "" if o.audience <= 1 else f" (informs {o.audience} complaints)"
        out(f"\nNext check (about {o.minutes:.0f} min){for_whom}: {describe_option(sess, o)}")
        out(f"  about {o.pyes:.0%} likely to come back {o.check.words[0]}; expected to sharpen the picture by {o.gain:.2f} bits over the complaints it informs")
        yn = "[a]bnormal / [n]ormal" if o.check.is_reading else "[y]es / [n]o"
        while True:
            try:
                ans = input_fn(f"  Result? {yn} / [u]nsure / [q]uit > ").strip().lower()
            except EOFError:
                ans = "q"
            if ans in ("q", "quit"):
                out("\nStopped.")
                _belief(sess, out, 3)
                return sess.status()
            if ans in KEYS:
                k = KEYS[ans]
                sess.report("unsure" if k == "unsure" else o.check.words[0] if k == "positive" else o.check.words[1])
                break
            out("  Please answer " + ("a, n, u or q." if o.check.is_reading else "y, n, u or q."))
        _belief(sess, out)
    st = sess.status()
    out(f"\nSo far: {st['n_checks']} checks, about {st['elapsed']:.0f} minutes for the whole visit.")
    if st["n_checks"]:
        out(f"  Note: {RELIABILITY_NOTE}")
        out(f"  Note: {JOINT_NOTE}")
    return st


class DemoTechnician:
    """A simulated technician for the demo: answers each check with its most likely result under the given first-order cause of each complaint and the state of each air handler."""

    def __init__(self, sess: JointSession, truths: list[tuple], states: dict):
        self.sess, self.truths, self.states = sess, truths, states

    def p(self, o: JOption) -> float:
        ck = o.check
        if o.kind == "ahu":
            u = self.states.get(o.who, "ok")
            return float(ck.bg if u == "ok" else ck.detects.get(u, ck.bg))
        return float(K.p_pos(ck, self.truths[o.who], o.target, self.sess.model.cases[o.who].doc))

    def __call__(self, prompt: str) -> str:
        o = self.sess._pending
        ans = "y" if self.p(o) >= 0.5 else "n"
        print(f"{prompt}{ans}")
        return ans


def _parse_context(s: str | None) -> D.Context:
    ctx = D.Context()
    for part in filter(None, (s or "").split(",")):
        k, _, v = part.partition("=")
        ctx = ctx.declare(k.strip(), v.strip())
    return ctx


def _auto_tier(b: D.Building1) -> str:
    return "T3" if b.points else "T2"


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Technician-guided troubleshooting, working model v2: several complaints, one investigation (placeholder numbers; see TROUBLESHOOT_V2.md)")
    ap.add_argument("--building", type=Path, default=EXAMPLE, help="building JSON (v1's format: equipment, claims, attributes, control-system points)")
    ap.add_argument("--tier", choices=["auto", "T2", "T3"], default="auto", help="what data the tool may use (auto: the richest the building file supports)")
    ap.add_argument("--complaints", help="comma-separated rooms with a complaint (default: the first four rooms of the file's first air handler)")
    ap.add_argument("--context", default="instrument=yes,occupant=no", help="facts declared up front, e.g. instrument=yes,occupant=no,bas_access=no")
    ap.add_argument("--drawings", choices=sorted(M.DRAWINGS), default="mostly_right", help="how far you trust the drawings (this model was studied at mostly_right)")
    ap.add_argument("--f", type=float, default=JointSettings().f, help="prior probability that an air handler has an upstream fault (placeholder)")
    ap.add_argument("--lookahead", type=int, choices=(1, 2), default=1)
    ap.add_argument("--demo", action="store_true", help="answer for the technician (a simulated one; an illustration, not a result)")
    ap.add_argument("--truth", help="--demo: the real first-order cause of each complaint, comma-separated (cause ids; ahu_fan_off and low_static make the air handler faulty)")
    ap.add_argument("--export", type=Path, help="write the visit (checks, beliefs) as JSON")
    ap.add_argument("--min-rate", type=float, default=LIVE_MIN_RATE_DEFAULT, dest="min_rate",
                     help="bits per minute a check must be expected to sharpen the belief by, per minute, to be worth offering (default 0.02, 2026-09-29: 0.01 was confirmed across all 18 "
                          "of PREREGISTRATION_DR.md Addendum 30's cells at both tiers (Addendum 35: faster everywhere, no confidence cost anywhere, a real ~2-3 point T2 accuracy cost on "
                          "about a third of them); 0.015 was a further step the user chose directly (T2: 109->68 min, accuracy 0.799->0.770; T3: 64->52 min, 0.832->0.827), then found NOT "
                          "confirmed at the 18-cell bar for T2 (Addendum 36: only 5 of 18 cells clean) though T3 stayed a clean win everywhere; 0.02 is a further step still, taken for the "
                          "user's own documentation profile (Exploratory note E2's 'T3-noattr': BAS access + a point map, no documented attributes), where a fine sweep plus a 5-cell "
                          "spot-check found it closes a real gap against a language-model comparison for a small (<2pt) accuracy cost and no safety cost; this has NOT been confirmed "
                          "across all 18 cells for T2/T3 the way 0.01 was -- primary-cell only. The older placeholder, 0.003, was never tuned. v1's own tools and studies (single-complaint) "
                          "keep 0.003; this is v2's routine only)")
    a = ap.parse_args(argv)
    b = D.load_building_v1(a.building)
    tier = _auto_tier(b) if a.tier == "auto" else a.tier
    rooms = [r.strip() for r in a.complaints.split(",")] if a.complaints else b.base.members("vav_zone")[:4]
    settings = M.Settings().with_drawings(a.drawings)
    ctx = _parse_context(a.context)
    cases = [make_case_v1(b, r, tier, settings, context=ctx, min_rate=a.min_rate) for r in rooms]
    sess = JointSession(cases, JointSettings(f=a.f), a.lookahead)
    if a.demo:
        truths = [(t.strip(),) for t in (a.truth or ",".join(["low_static"] * len(rooms))).split(",")]
        if len(truths) != len(rooms):
            raise SystemExit("--truth needs one cause per complaint")
        for t in truths:
            if t[0] not in C.BY_ID:
                raise SystemExit(f"unknown cause {t[0]!r}; choose from {', '.join(sorted(C.BY_ID))}")
        states = {}
        for c, t in zip(cases, truths):
            if t[0] in ("ahu_fan_off", "low_static"):
                states[c.ahu] = t[0]
        print(f"[demo] simulated technician (most likely answers); real causes: {', '.join(t[0] for t in truths)}")
        run(sess, DemoTechnician(sess, truths, states))
    else:
        run(sess)
    if a.export:
        st = sess.status()
        a.export.write_text(json.dumps(dict(rooms=rooms, tier=tier, checks=[dict(kind=k, who=w, check=c, target=t, outcome=o, minutes=mn) for k, w, c, t, o, mn in sess.log],
                                            complaints=[dict(room=p["room"], ranked=[[list(c), pr] for c, pr in p["ranked"][:5]], concluded=p["concluded"]) for p in st["complaints"]],
                                            elapsed=st["elapsed"], assumptions=dict(check_reliability=RELIABILITY_NOTE, joint=JOINT_NOTE, validated_on_real_call_outs=False)), indent=1))


if __name__ == "__main__":
    main()
