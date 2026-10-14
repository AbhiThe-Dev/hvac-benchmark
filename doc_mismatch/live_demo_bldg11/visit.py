"""One visit of the bldg11 demo: the REAL v2 engine (same classes as the live demo in ../live_demo) on a real layout and point map, with a scripted scenario beside it.

Differences from ../live_demo/server.py, all deliberate and all disclosed in the UI:
  * the building is a subset of Mortar bldg11 (build_building.py), 83 boxes on two air handlers, not the 24-room synthetic example;
  * more complaints (six) and arrival order interleaved across the two air handlers;
  * the check list is the catalogue minus the checks whose point the real map does not have (bas_ahu_fan: no fan status; bas_controller: no controller status);
  * candidates for a wrong box are the NEAREST BY ID (`nearness="id"`, an option the tool ships and Addenda 24-26 studied), because with 49 boxes on a handler "same air handler" is no shortlist;
  * the drawings are rated `mostly_right`, the live CLI's own default (the live demo server leaves the prior at 0.15);
  * `model`: "shipped" = the joint model exactly as it is; "adjusted" = the same model with r_low (the chance a room on a low-static handler complains) cut from 0.5 to 0.10.
    The shipped model counts every SILENT room on a handler as evidence against a shared fault, which is right for 8 rooms and wrong for 49 (see README.md); "adjusted" is a tuning for
    this scenario, not a validated setting.
  * every step also carries the scenario's own answer (a hint the presenter can follow or ignore).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from docmismatch.troubleshoot import model as M  # noqa: E402
from docmismatch.troubleshoot.v1 import catalogue as K  # noqa: E402
from docmismatch.troubleshoot.v1 import causes as C  # noqa: E402
from docmismatch.troubleshoot.v1 import data as D  # noqa: E402
from docmismatch.troubleshoot.v1.engine import Obs, Question, make_case_v1  # noqa: E402
from docmismatch.troubleshoot.v2 import cli as V2CLI  # noqa: E402
from docmismatch.troubleshoot.v2.joint import JointModel, JointSettings  # noqa: E402
from docmismatch.troubleshoot.v2.policies import PriorSession  # noqa: E402

from build_building import OUT as BUILDING_DIR  # noqa: E402
from build_building import build_subset  # noqa: E402
from world import ScriptedWorld, load_scenario, truth_cause  # noqa: E402

BUILDING = BUILDING_DIR / "building_v2.json"
ITEMS = D.TIERS["T1"] | {"bas_access", "point_map"}               # the user's documentation profile: equipment list + claims + control-system access + point map, no attributes
MIN_RATE = V2CLI.LIVE_MIN_RATE_DEFAULT                           # the live shipped default
NO_REAL_POINT = ("bas_ahu_fan", "bas_controller")                 # the Brick file has no fan-status or controller-status point for these boxes and handlers
CHECKS = tuple(c for c in K.CATALOGUE if c.name not in NO_REAL_POINT)
SETTINGS = M.Settings(nearness="id").with_drawings("mostly_right")


def load_building() -> D.Building1:
    if not BUILDING.exists():
        BUILDING.parent.mkdir(parents=True, exist_ok=True)
        b, cover = build_subset()
        BUILDING.write_text(json.dumps(b))
        (BUILDING.parent / "coverage.json").write_text(json.dumps(cover, indent=1))
    return D.load_building_v1(BUILDING)


def coverage() -> dict:
    load_building()
    return json.loads((BUILDING.parent / "coverage.json").read_text())


def joint_settings(scenario: dict, model: str) -> JointSettings:
    if model.startswith("r_low="):                                  # a development hook for the sensitivity sweep, not offered in the UI
        return JointSettings(r_low=float(model.split("=")[1]))
    if model not in scenario["model"]:
        raise ValueError(f"model must be one of {sorted(scenario['model'])}")
    spec = scenario["model"][model]
    if spec.get("low_mix"):                                         # the general fix: a mixture over how many rooms a low-static fault starves (MIX_PROTOCOL.md); not tuned to this building
        return JointSettings(low_mix=tuple((float(r), float(w)) for r, w in spec["low_mix"]))
    return JointSettings() if spec["r_low"] is None else JointSettings(r_low=spec["r_low"])


class Visit:
    """All server-side state for the one visit this demo runs at a time (the same shape as ../live_demo/server.py's Visit, for n rooms)."""

    def __init__(self, model: str = "shipped"):
        self.scenario = load_scenario()
        self.model_name = model
        self.building = load_building()
        ctx = D.Context(**{k: v for k, v in self.scenario["context"].items() if k in D.CONTEXT_KEYS})
        self.cases = [make_case_v1(self.building, c["room"], ITEMS, SETTINGS, context=ctx, checks=CHECKS, min_rate=MIN_RATE) for c in self.scenario["complaints"]]
        self.model = JointModel(self.cases, joint_settings(self.scenario, model))
        self.world = ScriptedWorld(self.scenario, self.cases)
        self.room = 0
        self.memo = {}
        self.low_static_seen = set()
        self.at = None
        self.visit_minutes = 0.0
        self.visit_checks = 0
        self.conclusions = []
        self.pending = None
        self.pending_check = None
        self.sess = None
        self._start_room()

    # ------------------------------------------------------------------------------------------ setup
    def _start_room(self):
        i = self.room
        sess = PriorSession(self.cases[i], (self.model.causes[i], self.model.marg0[i]))
        sess.at = self.at
        for (a, name), word in self.memo.items():
            if a == self.cases[i].ahu:
                sess.log.append(Obs(name, self.cases[i].doc, word, 0.0))
        if self.cases[i].ahu in self.low_static_seen:
            sess.log.append(Obs("static_at_box", self.cases[i].doc, "abnormal", 0.0))
        self.sess = sess

    def room_info(self):
        cov = coverage()
        return [dict(id=c.member, name=c.member_name, ahu=c.ahu, documented_box=c.doc, story=s["story"], boxes_on_ahu=cov[c.ahu]["boxes"])
                for c, s in zip(self.cases, self.scenario["complaints"])]

    def prior_info(self) -> dict:
        """What the joint model believes about each air handler before any check (the point of the 'adjusted' switch)."""
        post0 = self.model.ahu_posterior_by_cause(self.model.initial())
        return {a: {k: round(float(x), 6) for k, x in d.items()} for a, d in post0.items()}

    # ------------------------------------------------------------------------------------------ the step the UI shows
    def _ranked(self, n=3):
        st = self.sess.status()
        return st, [dict(text=C.cause_text(c) if c[0] != "wrong" else f"Fed by {self.sess.label(c[1])}, not the documented box", p=round(float(p), 3)) for c, p in st["ranked"][:n]]

    def _shortlist(self):
        """For a room the tool could not settle: the two most likely causes and the single check that would help most, even if the tool judged it not worth its time (Session.shortlist)."""
        sl = self.sess.shortlist(2)
        label = lambda c: C.cause_text(c) if c[0] != "wrong" else f"Fed by {self.sess.label(c[1])}, not the documented box"  # noqa: E731
        nxt = sl["next"]
        return dict(candidates=[dict(text=label(c), p=round(p, 3)) for c, p in sl["candidates"]], mass=round(sl["mass"], 3),
                    next=None if nxt is None else dict(text=nxt.text, minutes=round(nxt.minutes, 1)))

    def current_step(self):
        step = self.sess.next_step()
        i = self.room
        if step is None:
            st, ranked = self._ranked()
            top = st["ranked"][0]
            truth = self.world.causes[i]
            leaf = dict(kind="conclude", room=i, conclusion=self.sess.describe(top[0]), belief=round(float(top[1]), 3), minutes_so_far=round(self.sess.elapsed, 1),
                        checks_so_far=st["n_checks"], forced=not st["concluded"], ranked=ranked, scripted_truth=self.scenario["complaints"][i]["story"], matches_script=tuple(top[0]) == truth,
                        shortlist=None if st["concluded"] else self._shortlist())
            self.visit_minutes += leaf["minutes_so_far"]
            self.visit_checks += leaf["checks_so_far"]
            self.conclusions.append(leaf)
            has_next = self.room + 1 < len(self.cases)
            leaf["has_next"] = has_next
            if has_next:
                nxt = self.cases[self.room + 1]
                carried = [f"{name.replace('_', ' ')}: {word}" for (a, name), word in self.memo.items() if a == nxt.ahu]
                if nxt.ahu in self.low_static_seen:
                    carried.append("low duct static already found on this air handler")
                leaf["carried_into_next"] = carried
                leaf["next_room_name"] = nxt.member_name
            leaf["visit_minutes"] = round(self.visit_minutes, 1)
            leaf["visit_checks"] = self.visit_checks
            self.pending = self.pending_check = None
            return leaf
        if isinstance(step, Question):
            self.pending = dict(kind="question", key=step.key)
            return dict(kind="question", room=i, name=step.key, text=step.text, words=list(step.options), scenario_answer=self.world.context.get(step.key))
        ck = step.check
        already = (self.sess.case.ahu, ck.name) in self.memo
        self.pending = dict(kind="check", name=ck.name, target=step.target)
        self.pending_check = ck
        return dict(kind="check", room=i, name=ck.name, text=step.text, minutes=round(step.minutes, 1), words=list(ck.words), p_pos=round(step.p_pos, 2),
                    scenario_answer=self.world.answer(i, ck, step.target),
                    memo_note=("Already read for an earlier room on this air handler -- free here." if already else
                               "A reading on the air handler itself: later rooms on the same air handler get this one for free." if ck.subject == "ahu" else None))

    def advance_room(self):
        if self.room + 1 >= len(self.cases):
            return dict(kind="visit_done", conclusions=self.conclusions, visit_minutes=round(self.visit_minutes, 1), visit_checks=self.visit_checks,
                        rooms=[dict(name=c.member_name) for c in self.cases], matches=sum(c["matches_script"] for c in self.conclusions), model=self.model_name)
        self.room += 1
        self.at = self.sess.at
        self._start_room()
        return self.current_step()

    def answer(self, word):
        if self.pending is None:
            raise ValueError("nothing is pending")
        if self.pending["kind"] == "question":
            self.sess.declare(self.pending["key"], word)
        else:
            name, target = self.pending["name"], self.pending["target"]
            ck = next(c for c in self.sess.case.checks if c.name == name)
            self.sess.report(word, check=name, target=target)
            if ck.subject == "ahu":
                self.memo[(self.sess.case.ahu, name)] = word
            elif name == "static_at_box" and word == "abnormal":
                self.low_static_seen.add(self.sess.case.ahu)
        return self.current_step()


def autoplay(model: str = "shipped") -> dict:
    """Run the whole visit answering every check with the scenario's own answer. Returns the trace, the conclusions and the totals (used by the UI's 'run it for me' and by the tests)."""
    v = Visit(model)
    trace, step = [], v.current_step()
    while True:
        if step["kind"] == "check":
            trace.append(dict(room=step["room"], room_name=v.cases[step["room"]].member_name, check=step["name"], minutes=step["minutes"], answer=step["scenario_answer"], shared=bool(step["memo_note"])))
            step = v.answer(step["scenario_answer"])
        elif step["kind"] == "question":
            trace.append(dict(room=step["room"], room_name=v.cases[step["room"]].member_name, question=step["name"], answer=step["scenario_answer"]))
            step = v.answer(step["scenario_answer"])
        elif step["kind"] == "conclude":
            step = v.advance_room()
        else:
            return dict(trace=trace, done=step, rooms=v.room_info(), prior=v.prior_info())
