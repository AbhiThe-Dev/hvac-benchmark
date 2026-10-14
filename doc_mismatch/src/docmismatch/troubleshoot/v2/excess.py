"""Where does the joint tool's extra time go? (PREREGISTRATION_DR.md, exploratory note E1.) Simulation only; nothing here changes the tool or is evidence about real technicians.

Instrumented copies of the routine (`tool_ticket_memo2`) and the joint tool (`tool_joint2`) that make the same decisions as `policies.run_ticket(mode="memo2")` and `policies.run_joint(group_informing=True)` and also
record every step; an oracle that gives every policy the SAME answer to the SAME question (so a paired difference is the policies alone, not the luck of their answer streams); and two probes built on the joint
session: `CapSession` (the routine's per-complaint check cap) and `FocusSession` (complaints in arrival order).
"""

from __future__ import annotations

import dataclasses
import os
import zlib
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from ..v1.engine import Obs, make_case_v1
from . import joint as JT
from . import policies as P
from . import study_joint as J
from . import world2 as W

POLICIES = ("tool_ticket_memo2", "tool_joint2", "joint2_cap12", "joint2_focus")
CAP = JT.MAX_CHECKS_PER_COMPLAINT
FIELDS = ("minutes", "checks", "correct", "wc", "n", "kind", "moves", "travel", "beyond")     # what `run_event` returns, in order


def primary() -> tuple[int, W.WorldParams]:
    """(cell index, world parameters) of the primary cell of Addendum 30."""
    idx, cell = next((i, c) for i, c in enumerate(J.all_cells()) if c.is_primary)
    return idx, cell.params()


def cases_for(tau: float | None = None) -> dict:
    """{(tier, room): the tool's v1 case}, with the conclusion threshold `tau` (None: the tool's own 0.95)."""
    s = W.tool_settings() if tau is None else dataclasses.replace(W.tool_settings(), tau=tau)
    bld = W.make_building2()
    return {(t, r): make_case_v1(bld, f"Room-{r}", W.TIER_ITEMS[t], settings=s, context=W.tier_context(t, r), member_name=f"Room {r}") for t in W.TIER_NAMES for r in range(W.N_BOX)}


class Coupled(W.Oracle):
    """The answer to a question depends on the event, the question and `seed` only: the same for every policy and in any order."""

    def __init__(self, event: W.Event, rel_a: float, seed: int):
        super().__init__(event, rel_a, None)
        self.seed = seed

    def _u(self, key: tuple) -> float:
        return float(np.random.default_rng([self.seed, self.event.idx, self.event.i, zlib.crc32(repr(key).encode())]).random())

    def ask_room(self, i, ck, target):
        return ck.words[0] if self._u(("r", i, ck.name, target)) < self.p_room(i, ck.name, target) else ck.words[1]

    def ask_ahu(self, a, ck):
        return ck.words[0] if self._u(("a", a, ck.name)) < self.p_ahu(a, ck.name) else ck.words[1]


# ---------------------------------------------------------------------------------------------- instrumented copies of the two policies
def _step(kind, who, ck, target, word, minutes, at_before, place) -> dict:
    access = 0.0 if at_before == place else ck.access_min
    return dict(kind=kind, who=who, check=ck.name, subject=ck.subject, target=target, word=word, minutes=minutes, access=access, do=ck.do_min + ck.wait_min, moved=at_before != place)


def ticket_steps(cases: list, oracle, js: JT.JointSettings | None = None) -> dict:
    """`policies.run_ticket(mode="memo2")` with a record of every step."""
    model = JT.JointModel(cases, js)
    at, memo, low_static_seen = None, {}, set()
    steps, guess, concluded, minutes = [], [], [], 0.0
    for i, case in enumerate(cases):
        sess = P.PriorSession(case, (model.causes[i], model.marg0[i]))
        sess.at = at
        for (a, name), word in memo.items():
            if a == case.ahu:
                sess.log.append(Obs(name, case.doc, word, 0.0))
        if case.ahu in low_static_seen:
            sess.log.append(Obs("static_at_box", case.doc, "abnormal", 0.0))
        own = 0
        while own < JT.MAX_CHECKS_PER_COMPLAINT:
            step = sess.next_step()
            if step is None:
                break
            ck = step.check
            word = oracle.ask_ahu(case.ahu, ck) if ck.subject == "ahu" else oracle.ask_room(i, ck, step.target)
            before = sess.at
            sess.report(word)
            steps.append(_step("ticket", i, ck, step.target, word, sess.log[-1].minutes, before, sess.at))
            own += 1
            if ck.subject == "ahu":
                memo[(case.ahu, ck.name)] = word
            elif ck.name == "static_at_box" and word == "abnormal":
                low_static_seen.add(case.ahu)
        st = sess.status()
        guess.append(st["ranked"][0][0])
        concluded.append(bool(st["concluded"]))
        minutes += sess.elapsed
        at = sess.at
    return dict(minutes=minutes, guess=guess, concluded=concluded, steps=steps)


def joint_steps(cases: list, oracle, js: JT.JointSettings | None = None, session_cls=None, lookahead: int = 1, group_informing: bool = True, scale_audience: bool = True) -> dict:
    """`policies.run_joint` with a record of every step; `session_cls` swaps in a variant of the joint session."""
    sess = (session_cls or JT.JointSession)(cases, js, lookahead, group_informing=group_informing, scale_audience=scale_audience)
    steps = []
    while True:
        o = sess.recommend()
        if o is None:
            break
        ck = o.check
        word = oracle.ask_ahu(o.who, ck) if o.kind == "ahu" else oracle.ask_room(o.who, ck, o.target)
        before = sess.state.at
        sess.report(word)
        steps.append(_step("joint", o.who, ck, o.target, word, o.minutes, before, o.place))
    st = sess.status()
    return dict(minutes=sess.elapsed, guess=[p["guess"] for p in st["complaints"]], concluded=[bool(p["concluded"]) for p in st["complaints"]], steps=steps)


# ---------------------------------------------------------------------------------------------- the probes
class CapSession(JT.JointSession):
    """No further room or box check for a complaint that already has `PER` of its own (the routine's per-ticket cap); air-handler options are not capped."""
    PER = CAP

    def _options(self, state):
        n: dict = {}
        for who, _, _ in state.done_c:
            n[who] = n.get(who, 0) + 1
        return [o for o in super()._options(state) if o.kind == "ahu" or n.get(o.who, 0) < self.PER]


class FocusSession(JT.JointSession):
    """Complaints in arrival order: only air-handler options and those of the lowest-numbered complaint that still has an option are considered."""

    def _pick(self, opts):
        if not opts:
            return None
        focus = min((o.who for o in opts if o.kind == "complaint"), default=None)
        return super()._pick([o for o in opts if o.kind == "ahu" or o.who == focus])


def beyond_cap(steps: list, cap: int = CAP) -> float:
    """Minutes spent on room or box checks beyond the `cap`-th on the same complaint."""
    per: dict = {}
    for s in steps:
        if s["subject"] != "ahu":
            per.setdefault(s["who"], []).append(s["minutes"])
    return float(sum(sum(ms[cap:]) for ms in per.values()))


def run_event(pol: str, tier: str, ev: W.Event, oracle, cases: dict) -> tuple:
    """One policy on one event: (minutes, checks, complaints correct, concluded-and-wrong, complaints, kind, location changes, travel minutes, minutes beyond the 12th check on a complaint)."""
    cs = [cases[(tier, r)] for r in ev.rooms]
    if pol == "tool_ticket_memo2":
        r = ticket_steps(cs, oracle)
    elif pol == "tool_joint2":
        r = joint_steps(cs, oracle)
    elif pol == "joint2_cap12":
        r = joint_steps(cs, oracle, session_cls=CapSession)
    elif pol == "joint2_focus":
        r = joint_steps(cs, oracle, session_cls=FocusSession)
    else:
        raise ValueError(f"unknown policy {pol!r}")
    wc = sum(1 for g, t, c in zip(r["guess"], ev.causes, r["concluded"]) if c and g != t)
    st = r["steps"]
    return (r["minutes"], len(st), sum(g == t for g, t in zip(r["guess"], ev.causes)), wc, ev.n, ev.kind, sum(1 for s in st if s["moved"]), sum(s["access"] for s in st), beyond_cap(st))


def _job(args):
    tau, seeds, n0, n, policies = args
    idx, wp = primary()
    cases = cases_for(tau)
    events = [W.draw_event(idx, i, wp, cases) for i in range(n0, n0 + n)]
    return {(tau, seed, tier, pol): [run_event(pol, tier, ev, Coupled(ev, wp.rel_a, seed), cases) for ev in events] for seed in seeds for tier in W.TIER_NAMES for pol in policies}


def run_grid(taus, seeds, n0: int, n: int, policies=POLICIES[:2], workers: int | None = None) -> dict:
    """{(tau, seed, tier, policy): [run_event tuple per event]}; events `n0 .. n0+n-1` of the primary cell (the world's events, not the study's answer streams); deterministic."""
    jobs = [(t, tuple(seeds), n0, n, tuple(policies)) for t in taus]
    workers = workers if workers is not None else min(8, os.cpu_count() or 1, len(jobs))
    out: dict = {}
    if workers <= 1:
        for j in jobs:
            out.update(_job(j))
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for part in ex.map(_job, jobs):
                out.update(part)
    return out


# ---------------------------------------------------------------------------------------------- summaries
def _rows(res: dict, tau: float, tier: str, pol: str, sub: str) -> np.ndarray:
    """(seeds, events, fields) numeric array of one policy's results, for the events of subset `sub`."""
    seeds = sorted({k[1] for k in res if k[0] == tau})
    kinds = np.array([r[5] for r in res[(tau, seeds[0], tier, pol)]])
    m = np.ones(len(kinds), bool) if sub == "all" else kinds == sub
    return np.array([[[r[j] for j in (0, 1, 2, 3, 4, 6, 7, 8)] for r in res[(tau, s, tier, pol)]] for s in seeds], float)[:, m, :]


def summary(res: dict, tau: float, tier: str, pol: str, sub: str) -> dict:
    a = _rows(res, tau, tier, pol, sub)
    n = a[:, :, 4].sum()
    return dict(minutes=a[:, :, 0].mean(), checks=a[:, :, 1].mean(), correct=100 * (a[:, :, 2] / a[:, :, 4]).mean(), wc=100 * a[:, :, 3].sum() / n, moves=a[:, :, 5].mean(), travel=a[:, :, 6].mean(),
                beyond=a[:, :, 7].mean(), events=a.shape[1])


def paired(res: dict, tau: float, tier: str, first: str, second: str, sub: str, boot: int = 2000, seed: int = 7) -> dict:
    """First minus second, per event averaged over the answer seeds, mean and 95% percentile interval over events (bootstrap), for minutes and for % of complaints correct."""
    a, b = _rows(res, tau, tier, first, sub), _rows(res, tau, tier, second, sub)
    dm = (a[:, :, 0] - b[:, :, 0]).mean(0)
    dc = 100 * (a[:, :, 2] / a[:, :, 4] - b[:, :, 2] / b[:, :, 4]).mean(0)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(dm), (boot, len(dm)))
    lo = lambda d: tuple(np.percentile(d[idx].mean(1), [2.5, 97.5]))
    return dict(minutes=float(dm.mean()), minutes_ci=lo(dm), correct=float(dc.mean()), correct_ci=lo(dc))
