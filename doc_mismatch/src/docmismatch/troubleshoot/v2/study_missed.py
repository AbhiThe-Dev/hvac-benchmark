"""Does adding generated candidate causes the fixed model may have missed increase accuracy? (PREREGISTRATION_DR.md Addendum 44.) Simulation only; nothing here is evidence about real
buildings or technicians.

The fixed model is the shipped v1 tree (14 causes). The WORLD has, in addition, a few causes the model does not list (`HIDDEN`, each with a true response on the existing checks and a
true dedicated check). A blind proposer (a language model that sees only the model's own cause and check lists) writes candidate causes, each with a profile over the existing checks and
one dedicated check. Arms, all on the same simulated complaints and the same technician:
  A        the fixed model                                   (what ships)
  B_all    A + every proposed candidate, with the proposer's own profile and share  (the idea, as it would run)
  B_match  A + only the proposed candidates that match a hidden cause              (the idea with a perfect filter on decoys; an upper bound for B_all)
  D        A + the hidden causes with their TRUE profile and share but NO dedicated check   (naming a cause is not enough?)
  C        A + the hidden causes with their TRUE profile, share and dedicated check          (oracle upper bound)
A candidate can only help if it matches a real hidden cause; the rest are decoys that can only steal belief. Whether a proposal matches is decided by the frozen rubric `MATCH`.
"""

from __future__ import annotations

import json
import re
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

import numpy as np

from .. import model as M
from ..v1 import catalogue as K
from ..v1 import causes as C
from ..v1.engine import make_case_v1
from ..v1.sim1 import World, simulate_v1
from . import world2 as W

# ---------------------------------------------------------------------------------------------- frozen constants (Addendum 44)
SEED = 44
N_EPISODES = 1500
MS = (0.0, 0.05, 0.10, 0.20)              # P(an episode's true cause is a hidden one); 0.10 is the primary
PRIMARY_M = 0.10
TIERS = ("T2", "T3")
MIN_RATE = 0.02                           # the shipped v2 default
OTHER_MASS = 0.70                         # a lump's mass of the prior (1 - p_wrong - p_acts_fail at the tool's drawings rating) -- converts a share of ALL complaints to a share of the lump
SHARE_CAP = 0.20
BG = 0.04                                 # false-alarm rate of every dedicated check (the brief tells the proposer this)
BOOT_B = 2000
ARMS = ("A", "B_all", "B_match", "D", "C")
BAR_GAIN, BAR_LOSS_IN, BAR_LOSS_WC = 0.0, 0.02, 0.01     # frozen decision rule: lenient-overall gain CI lower bound > 0; in-model accuracy loss <= 2 pts; wrong-and-confident rise <= 1 pt

# ---------------------------------------------------------------------------------------------- the world's causes the model lacks (my choices; not sourced; Addendum 44 says so)
# `true`: P(abnormal) on an EXISTING reading check under that cause (others: the check's own false-alarm rate). `check`: the cause's true dedicated check.
HIDDEN = {
    "fire_damper_closed": dict(
        label="Fire or smoke damper in the branch duct closed", detail="a tripped fusible link or a stuck fire/smoke damper blocks the duct to the room; the box itself works",
        true=dict(flow_hood=0.92, bas_airflow=0.20, diffuser_duct=0.20),
        check=dict(name="fire_damper_inspect", place="box", do_min=10, hit=0.85)),
    "sat_off": dict(
        label="Supply air temperature wrong", detail="the air handler's discharge temperature is off (cooling coil, chilled-water valve, discharge setpoint, economizer lockout); airflow is normal",
        true=dict(bas_zone=0.20),
        check=dict(name="discharge_air_temp", place="ahu", do_min=4, hit=0.85)),
    "return_blocked": dict(
        label="No return path for the room's air", detail="a closed door without a transfer grille or a blocked plenum return pressurises the room and chokes the supply",
        true=dict(flow_hood=0.50, ask_occupant=0.35, diffuser_duct=0.20),
        check=dict(name="return_path_check", place="room", do_min=6, hit=0.80)),
    "envelope_load": dict(
        label="Envelope or load problem the box cannot meet", detail="solar gain, infiltration or an added partition makes the room's load exceed what the box was ever sized to remove, though the box performs to design",
        true=dict(ask_occupant=0.35, design_load=0.20, bas_damper=0.20),
        check=dict(name="envelope_inspect", place="room", do_min=8, hit=0.75)),
}
HIDDEN_IDS = tuple(HIDDEN)

# frozen matching rubric: a proposal matches a hidden cause if its id + label + detail matches the regex (generous on purpose; the matches are printed for audit)
MATCH = {
    "fire_damper_closed": r"fire|smoke|fusible",
    "sat_off": r"supply[ _-]?air[ _-]?temp|discharge[ _-]?(air|temp)|\bsat\b|cooling[ _-]?coil|chilled|\bchw\b|economi[sz]er",
    "return_blocked": r"return[ _-]?(air|path|grille|plenum)|transfer|no return|pressuri[sz]|undercut|plenum",
    "envelope_load": r"envelope|solar|window|glazing|infiltrat|insulation|partition|heat gain|sun load|thermal load",
}
LEVEL = K.LV


# ---------------------------------------------------------------------------------------------- registration of non-catalogue causes
def spec(cid: str, label: str = "", detail: str = "") -> C.CauseSpec:
    return C.CauseSpec(cid, "other", C.OTHER, 0.0, label or cid, detail or label or cid)


@contextmanager
def registered(specs):
    """Make cause ids known to `causes.ALL_BY_ID` (v0_tag, cause_text) for the duration; restores it. Existing lookups are untouched."""
    added = [s.id for s in specs if s.id not in C.ALL_BY_ID]
    for s in specs:
        C.ALL_BY_ID.setdefault(s.id, s)
    try:
        yield
    finally:
        for i in added:
            C.ALL_BY_ID.pop(i, None)


def hidden_specs() -> list:
    return [spec(h, v["label"], v["detail"]) for h, v in HIDDEN.items()]


# ---------------------------------------------------------------------------------------------- proposals
def load_proposals(path: Path, mode: str = "label_first") -> dict:
    d = json.loads(Path(path).read_text())
    name = d.get("proposer", path.stem) + ("" if mode == "label_first" else "f")
    return dict(proposer=name, candidates=list(d.get("candidates", []))[:6], mode=mode)


def match_cause(c: dict, mode: str = "label_first") -> str | None:
    """Which hidden cause a proposal names. "frozen" (the rubric as first written): id + label + detail concatenated, first regex hit. "label_first" (Deviation 1, the primary): id + label
    alone, and only if nothing matches there, the detail -- because a detail that merely MENTIONS another mechanism ("closed fire/transfer damper") mis-assigned one proposal."""
    def hit(text: str) -> str | None:
        text = text.lower()
        return next((h for h, rx in MATCH.items() if re.search(rx, text)), None)
    head = " ".join(str(c.get(k, "")) for k in ("id", "label"))
    if mode == "frozen":
        return hit(head + " " + str(c.get("detail", "")))
    return hit(head) or hit(str(c.get("detail", "")))


def sanitize(t: str) -> str:
    return str(t).replace("{", "(").replace("}", ")")


def level(x) -> float:
    return LEVEL[x] if isinstance(x, str) and x in LEVEL else float(np.clip(float(x), 0.02, 0.98))


def proposal_to_model(prop: dict, only_matched: bool = False) -> dict:
    """{'specs', 'shares', 'profiles': {cause id: {existing check: P}}, 'checks': [dedicated CheckV1 ...], 'rows': audit rows}. A candidate matching a hidden cause takes that cause's id (so a
    complaint with that true cause can be named correctly); a second candidate matching the same hidden cause, and every non-matching one, is a decoy under its own id."""
    p = prop["proposer"]
    specs, shares, profiles, checks, rows, taken = [], {}, {}, [], [], set()
    for c in prop["candidates"]:
        h = match_cause(c, prop.get("mode", "label_first"))
        matched = h is not None and h not in taken
        if matched:
            taken.add(h)
        cid = h if matched else f"{p}_{re.sub('[^a-z0-9_]', '_', str(c.get('id', 'x')).lower())}"
        rows.append(dict(proposer=p, id=c.get("id"), label=c.get("label"), matched=h if matched else None))
        if only_matched and not matched:
            continue
        specs.append(spec(cid, str(c.get("label", cid)), str(c.get("detail", ""))))
        shares[cid] = min(float(c.get("share", 0.03)), SHARE_CAP) / OTHER_MASS
        profiles[cid] = {k: level(v) for k, v in dict(c.get("profile", {})).items()}
        ck = c.get("check")
        if ck:
            checks.append(make_check(f"{p}_{re.sub('[^a-z0-9_]', '_', str(ck.get('name', cid)).lower())}", sanitize(ck.get("text", "do the check")), str(ck.get("place", "box")),
                                     float(np.clip(float(ck.get("do_min", 8)), 2, 20)), {cid: level(ck.get("hit", "good"))}))
    return dict(specs=specs, shares=shares, profiles=profiles, checks=checks, rows=rows)


def make_check(name: str, text: str, place: str, do_min: float, detects: dict) -> K.CheckV1:
    """A reading check on the catalogue's conventions: where the technician must be decides the access minutes and the data it needs."""
    place = place if place in ("box", "room", "ahu", "bas") else "box"
    if place == "bas":
        return K.CheckV1(name, "control system", text, "reading", "bas", "box", 0, do_min, 0, K.BAS, detects=detects, bg=BG, source="PROPOSED")
    if place == "ahu":
        return K.CheckV1(name, "at the air handler", text, "reading", "ahu", "ahu", 15, do_min, 0, (K.Need("claims", 10.0),), detects=detects, bg=BG, source="PROPOSED")
    if place == "room":
        return K.CheckV1(name, "in the room", text, "reading", "room", "zone", 5, do_min, 0, detects=detects, bg=BG, source="PROPOSED")
    return K.CheckV1(name, "at the box", text, "reading", "box", "box", 6, do_min, 0, detects=detects, bg=BG, source="PROPOSED")


def with_profiles(checks: tuple, profiles: dict) -> tuple:
    """The catalogue with each candidate's profile merged into the existing reading checks' `detects`."""
    out = []
    for ck in checks:
        add = {cid: pr[ck.name] for cid, pr in profiles.items() if ck.name in pr}
        out.append(replace(ck, detects={**ck.detects, **add}) if add and ck.is_reading else ck)
    return tuple(out)


# ---------------------------------------------------------------------------------------------- the arms (tool side) and the world (truth side)
def arm_models(proposals: list) -> dict:
    """{arm name: dict(specs, shares-extras, checks)} -- everything a tool needs beyond the catalogue/causes it already has. B arms carry the proposer's numbers; C and D the world's."""
    arms = {"A": dict(specs=[], shares={}, checks=K.CATALOGUE)}
    for prop in proposals:
        for tag, only in (("B_all", False), ("B_match", True)):
            m = proposal_to_model(prop, only_matched=only)
            arms[(tag, prop["proposer"])] = dict(specs=m["specs"], shares=m["shares"], checks=with_profiles(K.CATALOGUE, m["profiles"]) + tuple(m["checks"]), rows=m["rows"])
    return arms


def oracle_arm(m: float, dedicated: bool) -> dict:
    """The tool told the truth about the hidden causes (their true profile, a share matching the world, and, if `dedicated`, their true dedicated check)."""
    profiles = {h: {k: v for k, v in HIDDEN[h]["true"].items()} for h in HIDDEN}
    checks = with_profiles(K.CATALOGUE, profiles)
    if dedicated:
        checks += tuple(make_check(HIDDEN[h]["check"]["name"], f"the {HIDDEN[h]['check']['name']} check", HIDDEN[h]["check"]["place"], HIDDEN[h]["check"]["do_min"], {h: HIDDEN[h]["check"]["hit"]})
                        for h in HIDDEN)
    share = (m / len(HIDDEN)) / OTHER_MASS if m > 0 else 0.01
    return dict(specs=hidden_specs(), shares={h: share for h in HIDDEN}, checks=checks)


def world_checks(extra_names: dict) -> tuple:
    """The TRUE catalogue: the existing checks with the hidden causes' true profiles, the hidden causes' true dedicated checks, and, for every dedicated check any arm offers, the true response
    of that check: `extra_names` {check name: hidden cause id it truly detects, or None} (a proposed check detects the hidden cause its candidate matched, at that cause's true hit rate)."""
    base = with_profiles(K.CATALOGUE, {h: dict(HIDDEN[h]["true"]) for h in HIDDEN})
    dedicated = [make_check(HIDDEN[h]["check"]["name"], "true", HIDDEN[h]["check"]["place"], HIDDEN[h]["check"]["do_min"], {h: HIDDEN[h]["check"]["hit"]}) for h in HIDDEN]
    proposed = [make_check(n, "true", pl, 5.0, {h: HIDDEN[h]["check"]["hit"]} if h else {}) for n, (h, pl) in extra_names.items()]
    return base + tuple(dedicated) + tuple(proposed)


def tool_case(tier: str, room: int, arm: dict):
    bld = W.make_building2()
    shares = {**C.DEFAULT_SHARES, **arm["shares"]}
    return make_case_v1(bld, f"Room-{room}", W.TIER_ITEMS[tier], settings=W.tool_settings(), context=W.tier_context(tier, room), member_name=f"Room {room}", shares=shares,
                        extra_causes=tuple(arm["specs"]), checks=arm["checks"], min_rate=MIN_RATE)


def in_model_truth(room: int, tier: str, rng: np.random.Generator) -> tuple:
    case = W.make_cases()[(tier, room)]
    causes, prior = C.make_prior_v1(case.candidates, case.doc, case.settings, docs=case.docs, weights=case.weights, shares=case.shares, reheat=W.true_reheat(room), pressure_independent=True)
    return causes[int(rng.choice(len(causes), p=prior))]


# ---------------------------------------------------------------------------------------------- one episode, all arms
def episode(i: int, m: float, tier: str, cases_by_arm: dict, wchecks: tuple) -> dict:
    """Episode `i` of (m, tier): a complaint from room i % 24 with a true cause drawn from the world; every arm works the SAME complaint with the SAME answer stream seed."""
    rng = np.random.default_rng([SEED, int(round(m * 1000)), TIERS.index(tier), i])
    room = i % W.N_BOX
    hidden = rng.random() < m
    truth = (HIDDEN_IDS[int(rng.integers(len(HIDDEN_IDS)))],) if hidden else in_model_truth(room, tier, rng)
    ctx = W.context_dict(tier, room)
    out = dict(i=i, truth=truth, hidden=hidden)
    for name, case_by_room in cases_by_arm.items():
        case = case_by_room[room]
        r = simulate_v1(case, World(truth, ctx, true_checks=wchecks), rng=np.random.default_rng([SEED, 7, int(round(m * 1000)), TIERS.index(tier), i]))
        g = r["guess"]
        ok_strict = g == truth
        ok_len = ok_strict or (hidden and g == ("other",))
        out[name] = dict(guess=g, ok=ok_strict, ok_len=ok_len, concluded=bool(r["concluded"]), wc=bool(r["concluded"] and not ok_len), minutes=float(r["minutes"]), n_checks=int(r["n_checks"]))
    return out


def run_cell(m: float, tier: str, arms: dict, n: int = N_EPISODES) -> list:
    """The `n` episodes of one (m, tier) cell for every arm in `arms` {name: arm}."""
    with registered(hidden_specs() + [s for a in arms.values() for s in a["specs"]]):
        extra = {}
        for a in arms.values():
            for ck in a["checks"]:
                if ck.source == "PROPOSED":
                    # the true response of a proposed dedicated check: it detects the hidden cause its own candidate matched (the id == a hidden id), else nothing
                    hit = next((c for c in ck.detects if c in HIDDEN), None)
                    extra[ck.name] = (hit, ck.place)
        wchecks = world_checks(extra)
        cases = {name: {r: tool_case(tier, r, a) for r in range(W.N_BOX)} for name, a in arms.items()}
        return [episode(i, m, tier, cases, wchecks) for i in range(n)]
