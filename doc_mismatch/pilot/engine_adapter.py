"""The one integration point between the pilot app and the (unmodified) v1/v2 reasoning engine.

T3-noattr tier, `min_rate` = the live-shipped default, `econ_fault` enrolled using Addendum 37's exact
validated configuration (confirmed against doc_mismatch/tests/test_troubleshoot_econ.py) -- today's
live_demo/server.py has econ_fault OFF entirely (plain K.CATALOGUE, no extra_causes); turning it on here
is a deliberate pilot-only change, not a no-op.

JOINT MODEL: the pilot runs on the SEVERITY MIXTURE by default (`LOW_MIX`; live_demo_bldg11/MIX_PROTOCOL.md and README.md): instead of one fixed
share of "half of the rooms on a low-static air handler complain" (the shipped model, which gives a shared fault on a large air handler odds near
zero: it never reads the handler and the rooms get a weak guess), it considers 5%, 15%, 50% and 90% and lets the complaints pick. Set
`PILOT_JOINT_MODEL=shipped` to run the unmodified shipped model instead. The setting is part of `catalogue_hash()`, stored on every case.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]           # doc_mismatch/
sys.path.insert(0, str(ROOT / "src"))

from docmismatch.troubleshoot.v1 import catalogue as K  # noqa: E402
from docmismatch.troubleshoot.v1 import causes as C  # noqa: E402
from docmismatch.troubleshoot.v1 import data as D  # noqa: E402
from docmismatch.troubleshoot.v1.engine import CaseV1, Obs, Question, make_case_v1  # noqa: E402,F401 (Obs/Question re-exported for visit.py)
from docmismatch.troubleshoot.v2 import cli as V2CLI  # noqa: E402
from docmismatch.troubleshoot.v2.joint import JointModel, JointSettings  # noqa: E402
from docmismatch.troubleshoot.v2.policies import PriorSession  # noqa: E402

ITEMS = D.TIERS["T1"] | {"bas_access", "point_map"}      # T3-noattr: T1 + (T3 minus T2) -- no attributes
MIN_RATE = V2CLI.LIVE_MIN_RATE_DEFAULT                   # the live shipped default (0.02)
CHECKS = K.CATALOGUE + K.ECON_CHECKS
ECON_SHARE = 0.06                                        # Addendum 37's validated arm (test_troubleshoot_econ.py:61-62)
ECON_AFFECT = 0.15                                       # ditto (test_troubleshoot_econ.py:105)
ECON_SHARE_OF_F = 6.0 / 23.0                             # ditto
SHARES = {**C.DEFAULT_SHARES, C.ECON_FAULT.id: ECON_SHARE}


CAUSE_GROUPS = C.GROUPS                                  # group id -> plain description, for the technician's "what do you suspect?" chips


def load_building(path):
    return D.load_building_v1(path)


def build_cases(building: D.Building1, room_ids: list[str], *, feel: str | None = None, airflow: str | None = None) -> list[CaseV1]:
    """One CaseV1 per room, T3-noattr, econ_fault enrolled. Context is left fully undeclared (reheat/bas_access/
    instrument/occupant are asked live via the existing Question mechanism, or -- for bas_access specifically --
    simply default to True because "bas_access" is already a member of ITEMS)."""
    ctx = D.Context()
    return [make_case_v1(building, r, ITEMS, None, airflow=airflow, feel=feel, context=ctx,
                          checks=CHECKS, shares=SHARES, min_rate=MIN_RATE, extra_causes=(C.ECON_FAULT,))
            for r in room_ids]


# The severity mixture (weights sum to 1): P(a room on a low-static air handler complains) is 5%, 15%, 50% or 90%, each with weight 1/4, picked by the data.
LOW_MIX = ((0.05, 0.25), (0.15, 0.25), (0.5, 0.25), (0.9, 0.25))
JOINT_MODEL_ENV = "PILOT_JOINT_MODEL"                    # "mixed" (the default) or "shipped"; read at call time


def joint_model_name() -> str:
    v = os.environ.get(JOINT_MODEL_ENV, "mixed").strip().lower() or "mixed"
    if v not in ("mixed", "shipped"):
        raise ValueError(f"{JOINT_MODEL_ENV} must be 'mixed' or 'shipped', not {v!r}")
    return v


def joint_settings() -> JointSettings:
    kw = dict(extra_states=(C.ECON_FAULT.id,), extra_affect={C.ECON_FAULT.id: ECON_AFFECT}, extra_share={C.ECON_FAULT.id: ECON_SHARE_OF_F})
    if joint_model_name() == "mixed":
        kw["low_mix"] = LOW_MIX
    return JointSettings(**kw)


def build_joint_model(cases: list[CaseV1]) -> JointModel:
    return JointModel(cases, joint_settings())


# ------------------------------------------------------------------------------------------------- the hedge and the confidence cap
# A room that concludes "low duct static" without a box-level static reading of ITS OWN rests on the air handler's finding and on readings copied from other rooms. A fault of its own
# at that room's box (a failed actuator, a controller offline...) can hide behind that (the "folding" problem: live_demo_bldg11/README.md). On the registered 100 bldg11 visits
# (mixed setting) treating such a conclusion as not confident takes wrong-and-confident from 6.8% to 0.2% (8.3% to 1.5% with checks 25% worse), at no extra minutes and with the
# leading answer unchanged; the price is that 166 conclusions (126 of them right) are hedged. It is a safety measure, not an accuracy one.
HEDGE_CAP = 0.90                                         # the most confidence shown for a hedged conclusion (a room needs 0.95 to count as diagnosed)
HEDGE_NOTE = ("It is explained by the low duct static found at the air handler, but a fault in this room's own box is not ruled out: nothing was measured at this room itself, "
              "so the finding rests on the air handler and on readings carried over from other rooms. Fix the air handler first and check whether this room is still off.")


def has_own_box_static(sess) -> bool:
    """A real box-level static reading taken in THIS room's session. The zero-minute copy of another room's reading (the group-informing rule) does not count."""
    return any(o.check == "static_at_box" and o.minutes > 0 and o.outcome in ("abnormal", "normal") for o in sess.log)


def hedge_for(sess, cause: tuple, belief: float) -> dict | None:
    """None unless the leading cause is low static and the room has no box-level static reading of its own; otherwise what to show instead of a plain diagnosis."""
    if cause[0] != "low_static" or has_own_box_static(sess):
        return None
    return dict(hedged=True, raw_belief=round(float(belief), 3), belief=round(min(float(belief), HEDGE_CAP), 3), note=HEDGE_NOTE, rule_out=room_level_next(sess))


def room_level_next(sess) -> dict | None:
    """The check AT THIS ROOM (box or room, never the air handler: that finding is already made and cannot show whether this room has a fault of its own) that would sharpen the picture
    most per minute, without the 'worth its time' bar. Only a suggestion: it changes no belief, log or clock."""
    causes, post = sess.posterior()
    opts = [o for o in sess._options(causes, post) if o.check.subject != "ahu" and o.gain > sess.case.settings.min_gain and o.avail.state != "askable"]
    if not opts:
        return None
    best = max(opts, key=lambda o: (round(o.gain / o.minutes, 12), -o.minutes, o.check.name, str(o.target)))
    rec = sess._recommendation(best)
    return dict(check=best.check.name, text=rec.text, minutes=round(float(rec.minutes), 1))


def start_room_session(case: CaseV1, prior: tuple) -> PriorSession:
    return PriorSession(case, prior)


def involves_econ_fault(cause: tuple) -> bool:
    """`cause` is the tuple `Session.status()["ranked"][0][0]` / passed to `sess.describe()`."""
    return cause[0] == C.ECON_FAULT.id


# ------------------------------------------------------------------------------------------------- what the case record stores
def catalogue_hash() -> str:
    """Fingerprint of everything that decides what the tool recommends (checks and their minutes, the live
    min_rate, the cause shares). Stored on each case: replay depends on current code, so this says which code
    a stored recommendation came from. Includes the joint model (mixed or shipped)."""
    parts = [[c.name, c.family, c.access_min, c.do_min, c.wait_min] for c in CHECKS]
    fingerprint = [parts, MIN_RATE, sorted(SHARES.items()), ECON_AFFECT, ECON_SHARE_OF_F]
    if joint_model_name() == "mixed":                    # the shipped model keeps the fingerprint it always had
        fingerprint.append(["low_mix", [list(x) for x in LOW_MIX]])
    blob = json.dumps(fingerprint, sort_keys=True, default=str)
    return hashlib.sha1(blob.encode()).hexdigest()[:12]


def cause_id(cause: tuple) -> str:
    """The tool's cause tuple as one comparable string. ("wrong", j) and ("unlisted",) are both the drawings being
    wrong; the two lumps are conclusions too coarse to name a part (compare as 'doc_acts_fail' / 'doc_other')."""
    return "documentation_wrong" if cause[0] in ("wrong", "unlisted") else str(cause[0])


def ranked_snapshot(sess, k: int = 5) -> list[dict]:
    """The k most likely causes as the tool sees them right now. `cause` can name equipment ids; export aliases them."""
    return [dict(cause=list(c), id=cause_id(c), p=round(float(p), 4)) for c, p in sess.status()["ranked"][:k]]


def selectable_checks(sess) -> list[dict]:
    """Every check the technician could do instead of (or as well as) the recommendation, in catalogue order, with no
    ranking and no cost -- this feeds the ask-first picker, which must not leak what the tool prefers."""
    causes, post = sess.posterior()
    out = []
    for o in sess._options(causes, post):
        out.append(dict(name=o.check.name, target=o.target, family=o.check.family, text=sess._recommendation(o).text, words=list(o.check.words)))
    order = {c.name: i for i, c in enumerate(sess.case.checks)}
    out.sort(key=lambda d: (order.get(d["name"], 1_000), d["target"]))
    return out


def taxonomy_choices() -> list[dict]:
    """Causes a technician can confirm, grouped as causes.py groups them (the generic leaf 'other' is replaced by the
    free-text 'something else' option, so out-of-taxonomy findings are recorded as such)."""
    out = [dict(id=c.id, group=c.group, label=c.label) for c in C.ALL_BY_ID.values() if c.id != "other"]
    out.append(dict(id="documentation_wrong", group="documentation", label="The drawings were wrong: a different box or equipment serves this room"))
    return out
