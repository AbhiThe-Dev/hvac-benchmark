"""The policies of Addendum 30: what works an event (a visit with several complaints). All simulation-grade; the stand-ins are my constructions, not real technicians.

  tool_ticket        v1's tool, one independent session per complaint, in arrival order (what exists today)
  tool_ticket_nb     as above, each session's prior is the joint model's marginal at time zero (the neighbour question: how many rooms on its air handler do and do not complain)
  tool_ticket_memo   as above, and a reading of an air handler taken in one ticket is entered at no cost into every later ticket on that air handler
  tool_joint         the joint session (joint.py)
  tool_joint_la2     the joint session with two-step look-ahead
  fast_ticket        v1's `fast_list` stand-in, one complaint at a time
  fast_parent        an experienced technician's obvious rule: an air handler with two or more complaints first (fan check, then static reading); the first abnormal one names the cause for
                     every complaint of that air handler; otherwise each complaint by `fast_list`, skipping the air handler checks already done

Each returns a dict: minutes (the sum over the visit), n_checks, guess (one cause per complaint, in arrival order), concluded (per complaint; a stand-in always concludes), trace. The
technician's location carries over from one ticket to the next.
"""

from __future__ import annotations

import numpy as np

from ..v1 import catalogue as K
from ..v1 import data as D
from ..v1.engine import CaseV1, Obs, Question, Session
from ..v1.study_fast_v1 import Doer, available_readings, single_cause, walk_alternatives
from .joint import MAX_CHECKS_PER_COMPLAINT, JointModel, JointSession, JointSettings
from .world2 import Oracle

POLICIES = ("tool_ticket", "tool_ticket_nb", "tool_ticket_memo", "tool_joint", "tool_joint_la2", "fast_ticket", "fast_parent")
POLICIES2 = ("tool_ticket_memo2", "tool_joint2", "tool_joint2_la2", "tool_joint3")     # Addendum 31: the group-informing rule (indices 7-10, after Addendum 30's seven)
POLICY_INDEX = {p: i for i, p in enumerate(POLICIES + POLICIES2)}
LOOKAHEAD_POLICIES = ("tool_joint_la2",)
LOOKAHEAD_POLICIES2 = ("tool_joint2_la2",)
FAN_CHECKS = ("bas_ahu_fan", "ahu_visit")
STATIC_CHECKS = ("bas_static", "ahu_gauge")


class PriorSession(Session):
    """A v1 session whose prior over causes is given (the neighbour-informed prior); everything else is v1's, except that a session never concludes before a real observation has been
    taken (the pattern of complaints alone, however strong, is not a diagnosis; a clarification of Addendum 30, as for the joint session)."""

    def __init__(self, case: CaseV1, prior: tuple | None = None):
        super().__init__(case)
        self._given = prior

    def _prior(self):
        return self._given if self._given is not None else super()._prior()

    def _informed(self) -> bool:
        return any(o.outcome not in ("unsure", "skip") for o in self.log)

    def _best(self, allow_ask: bool):
        causes, post = self.posterior()
        if self._informed() or post.max() < self.case.settings.tau:
            return super()._best(allow_ask)
        self._pending = self._question = None                          # the prior alone is at tau: still look for the best check
        opts = self._options(causes, post)
        if not allow_ask:
            opts = [o for o in opts if o.avail.state != "askable"]
        return self._choose(opts), False

    def status(self) -> dict:
        st = super().status()
        if st["concluded"] and not self._informed():
            causes, post = self.posterior()
            st.update(concluded=False, conclusion=None, stalled=self._choose(self._options(causes, post)) is None)
        return st


def _ask(oracle: Oracle, cases: list, i: int):
    def ask(ck: K.CheckV1, target: str) -> str:
        return oracle.ask_ahu(cases[i].ahu, ck) if ck.subject == "ahu" else oracle.ask_room(i, ck, target)
    return ask


# ---------------------------------------------------------------------------------------------- the tool, ticket by ticket
def run_ticket(cases: list[CaseV1], oracle: Oracle, mode: str, js: JointSettings | None = None) -> dict:
    """`mode`: "plain" (v1's prior), "nb" (the joint model's marginal at time zero), "memo" (nb, and air handler readings are carried between tickets)."""
    if mode not in ("plain", "nb", "memo", "memo2"):
        raise ValueError("mode must be plain, nb, memo or memo2")
    model = JointModel(cases, js) if mode != "plain" else None
    at, memo, trace, low_static_seen = None, {}, [], set()
    guess, concluded, minutes, checks = [], [], 0.0, 0
    for i, case in enumerate(cases):
        sess = PriorSession(case, (model.causes[i], model.marg0[i]) if model is not None else None)
        sess.at = at
        if mode in ("memo", "memo2"):
            for (a, name), word in memo.items():
                if a == case.ahu:
                    sess.log.append(Obs(name, case.doc, word, 0.0))
        if mode == "memo2" and case.ahu in low_static_seen:                    # an abnormal inlet static reading at one box is a low-static duct for the air handler (Addendum 31)
            sess.log.append(Obs("static_at_box", case.doc, "abnormal", 0.0))
        own = 0
        while own < MAX_CHECKS_PER_COMPLAINT:
            step = sess.next_step()
            if step is None:
                break
            if isinstance(step, Question):
                raise RuntimeError(f"the tool asked {step.key!r}: every fact should have been declared")
            ck = step.check
            word = oracle.ask_ahu(case.ahu, ck) if ck.subject == "ahu" else oracle.ask_room(i, ck, step.target)
            trace.append((i, ck.name, step.target, word))
            sess.report(word)
            own += 1
            if ck.subject == "ahu":
                memo[(case.ahu, ck.name)] = word
            elif ck.name == "static_at_box" and word == "abnormal":
                low_static_seen.add(case.ahu)
        st = sess.status()
        guess.append(st["ranked"][0][0])
        concluded.append(bool(st["concluded"]))
        minutes += sess.elapsed
        checks += own
        at = sess.at
    return dict(minutes=minutes, n_checks=checks, guess=guess, concluded=concluded, trace=trace)


# ---------------------------------------------------------------------------------------------- the joint tool
def run_joint(cases: list[CaseV1], oracle: Oracle, js: JointSettings | None = None, lookahead: int = 1, group_informing: bool = False, scale_audience: bool = True) -> dict:
    sess = JointSession(cases, js, lookahead, group_informing=group_informing, scale_audience=scale_audience)
    trace = []
    while True:
        o = sess.recommend()
        if o is None:
            break
        ck = o.check
        word = oracle.ask_ahu(o.who, ck) if o.kind == "ahu" else oracle.ask_room(o.who, ck, o.target)
        trace.append((o.kind, o.who, ck.name, o.target, word))
        sess.report(word)
    st = sess.status()
    return dict(minutes=sess.elapsed, n_checks=sess.n_checks, guess=[p["guess"] for p in st["complaints"]], concluded=[bool(p["concluded"]) for p in st["complaints"]], trace=trace,
                ahu_posterior={a: w.tolist() for a, w in st["ahu"].items()})


# ---------------------------------------------------------------------------------------------- the stand-ins
def fast_run(case: CaseV1, ctx: dict, ask, at: str | None, skip: frozenset = frozenset()) -> tuple[dict, str | None]:
    """v1's `fast_list` (Addendum 28) with the technician's starting location and a set of checks to skip: the cheapest available reading that names one cause, first abnormal reading
    concludes that cause; else the alternative boxes are walked; else 'other'. Returns (result, location after)."""
    d = Doer(case, ctx, ask)
    d.s.at = at
    for _, name, ck in available_readings(case, d):
        cause = single_cause(ck)
        if cause is None or name in skip or (name, case.doc) in d.done:
            continue
        if d.do(ck, case.doc):
            return d.result(cause), d.s.at
    found = walk_alternatives(case, d)
    return d.result(found if found is not None else ("other",)), d.s.at


def run_fast_ticket(cases: list[CaseV1], oracle: Oracle, ctxs: list[dict]) -> dict:
    at, minutes, checks, guess, trace = None, 0.0, 0, [], []
    for i, case in enumerate(cases):
        r, at = fast_run(case, ctxs[i], _ask(oracle, cases, i), at)
        minutes += r["minutes"]
        checks += r["n_checks"]
        guess.append(r["guess"])
        trace += [(i,) + tuple(t[1:]) for t in r["trace"]]
    return dict(minutes=minutes, n_checks=checks, guess=guess, concluded=[True] * len(cases), trace=trace)


def run_fast_parent(cases: list[CaseV1], oracle: Oracle, ctxs: list[dict]) -> dict:
    n = len(cases)
    groups: dict[str, list[int]] = {}
    for i, c in enumerate(cases):
        groups.setdefault(c.ahu, []).append(i)
    at, minutes, checks, trace = None, 0.0, 0, []
    group_cause: dict[str, tuple] = {}
    group_done: dict[str, set] = {a: set() for a in groups}
    for a, idx in groups.items():
        if len(idx) < 2:
            continue
        rep = idx[0]
        d = Doer(cases[rep], ctxs[rep], _ask(oracle, cases, rep))
        d.s.at = at
        avail = {name: ck for _, name, ck in available_readings(cases[rep], d)}
        for names, cause in ((FAN_CHECKS, ("ahu_fan_off",)), (STATIC_CHECKS, ("low_static",))):
            usable = [(cost, nm) for cost, nm, _ in available_readings(cases[rep], d) if nm in names]
            if not usable:
                continue
            name = usable[0][1]
            group_done[a].add(name)
            if d.do(avail[name], cases[rep].doc):
                group_cause[a] = cause
                break
        for family in (FAN_CHECKS, STATIC_CHECKS):                     # a fan check answers the fan question for every check that asks it, and likewise the static reading
            if group_done[a] & set(family):
                group_done[a] |= set(family)
        at = d.s.at
        minutes += d.s.elapsed
        checks += len(d.trace)
        trace += [("group", a) + tuple(t[1:]) for t in d.trace]
    guess = [None] * n
    for i, case in enumerate(cases):
        if case.ahu in group_cause:
            guess[i] = group_cause[case.ahu]
            continue
        r, at = fast_run(case, ctxs[i], _ask(oracle, cases, i), at, skip=frozenset(group_done[case.ahu]))
        minutes += r["minutes"]
        checks += r["n_checks"]
        guess[i] = r["guess"]
        trace += [(i,) + tuple(t[1:]) for t in r["trace"]]
    return dict(minutes=minutes, n_checks=checks, guess=guess, concluded=[True] * n, trace=trace)


def run_policy(pol: str, cases: list[CaseV1], oracle: Oracle, ctxs: list[dict], js: JointSettings | None = None) -> dict:
    if pol == "tool_ticket":
        return run_ticket(cases, oracle, "plain")
    if pol == "tool_ticket_nb":
        return run_ticket(cases, oracle, "nb", js)
    if pol == "tool_ticket_memo":
        return run_ticket(cases, oracle, "memo", js)
    if pol == "tool_joint":
        return run_joint(cases, oracle, js, 1)
    if pol == "tool_joint_la2":
        return run_joint(cases, oracle, js, 2)
    if pol == "tool_ticket_memo2":
        return run_ticket(cases, oracle, "memo2", js)
    if pol == "tool_joint2":
        return run_joint(cases, oracle, js, 1, True)
    if pol == "tool_joint2_la2":
        return run_joint(cases, oracle, js, 2, True)
    if pol == "tool_joint3":
        return run_joint(cases, oracle, js, 1, True, False)
    if pol == "fast_ticket":
        return run_fast_ticket(cases, oracle, ctxs)
    if pol == "fast_parent":
        return run_fast_parent(cases, oracle, ctxs)
    raise ValueError(f"unknown policy {pol!r}")
