"""A language model as the experienced technician (PREREGISTRATION_DR.md Addendum 33). Simulation only; a PILOT; nothing here is evidence about real technicians or buildings.

The world, the cell and the events are Addendum 30's primary cell. A stratified sample of visits is worked at two tiers (T2, T3) by the routine (`tool_ticket_memo2`), the joint tool
(`tool_joint2`), my rule-based stand-in (`fast_parent`) and a language model that works through a terminal (`Visit`). Every party gets identical answers to identical questions
(`TableOracle`) and is charged by the tool's own accountant (a v1 `Session` used only for minutes, location and fallback costs), so minutes are comparable.
"""

from __future__ import annotations

import json
import zlib
from dataclasses import dataclass

import numpy as np

from .. import study as S
from .. import study_rating as SG
from ..v1 import catalogue as K
from ..v1 import causes as C
from ..v1 import data as D
from ..v1.engine import Session
from ..v1.study_fast_v1 import break_even
from . import policies as P
from . import study_joint as J
from . import world2 as W
from .joint import MAX_CHECKS_PER_COMPLAINT

# ---------------------------------------------------------------------------------------------- frozen constants (Addendum 33)
SEED = 33
PRIMARY_IDX = next(i for i, c in enumerate(J.all_cells()) if c.is_primary)
TIERS = ("T2", "T3")
KINDS = ("single", "multi", "shared")
N_PER_KIND = 10
MAX_COMPLAINTS = 8
N_EVENTS = J.N_EPISODES
BOOT_B = 1000
PARTNERS = ("tool_ticket_memo2", "tool_joint2", "fast_parent")
ROUTINE = "tool_ticket_memo2"
COMPS = dict(P=("llm", ROUTINE), Q=("llm", "tool_joint2"), R=("llm", "fast_parent"), S=(ROUTINE, "fast_parent"))
P2_BAR, P6_BAR, P4_BAR, P8_BAR = 0.15, 0.05, 0.02, 0.5
LEAF_IDS = tuple(c.id for c in C.CAUSES)


class VisitError(ValueError):
    """A command the terminal refuses (nothing is charged)."""


# ---------------------------------------------------------------------------------------------- the world, the sample
def world(n: int = N_EVENTS):
    cases = W.make_cases()
    wp = J.all_cells()[PRIMARY_IDX].params()
    return cases, wp, [W.draw_event(PRIMARY_IDX, i, wp, cases) for i in range(n)]


def event_at(i: int, cases: dict | None = None):
    cases = cases or W.make_cases()
    return cases, J.all_cells()[PRIMARY_IDX].params(), W.draw_event(PRIMARY_IDX, i, J.all_cells()[PRIMARY_IDX].params(), cases)


def kind_shares(events: list) -> dict:
    """Kind shares among the eligible events (at most MAX_COMPLAINTS complaints): the weights of the 'all visits' estimate."""
    el = [e for e in events if e.n <= MAX_COMPLAINTS]
    return {k: sum(e.kind == k for e in el) / len(el) for k in KINDS}


def sample_visits(events: list, n_per_kind: int = N_PER_KIND, seed: int = SEED) -> list[dict]:
    """[{id, event, kind}] in the order the ids are numbered (a shuffle, so an id says nothing about the kind): `n_per_kind` eligible events of each kind, drawn without replacement."""
    rng = np.random.default_rng([seed, 1])
    chosen = []
    for kind in KINDS:
        pool = [e.i for e in events if e.kind == kind and e.n <= MAX_COMPLAINTS]
        take = rng.permutation(len(pool))[:n_per_kind]
        chosen += [(pool[t], kind) for t in sorted(take)]
    order = rng.permutation(len(chosen))
    return [dict(id=f"v{k + 1:02d}", event=chosen[o][0], kind=chosen[o][1]) for k, o in enumerate(order)]


# ---------------------------------------------------------------------------------------------- one set of answers for everyone
class TableOracle(W.Oracle):
    """The answer to a question is a fixed function of (event, complaint, check, target) or (event, air handler, check): the same whoever asks, in whatever order."""

    def __init__(self, event: W.Event, rel_a: float):
        super().__init__(event, rel_a, np.random.default_rng(0))

    def _u(self, key: str) -> float:
        return float(np.random.default_rng([SEED, self.event.idx, self.event.i, zlib.crc32(key.encode())]).random())

    def ask_room(self, i: int, ck: K.CheckV1, target: str) -> str:
        return ck.words[0] if self._u(f"room|{i}|{ck.name}|{target}") < self.p_room(i, ck.name, target) else ck.words[1]

    def ask_ahu(self, a: str, ck: K.CheckV1) -> str:
        return ck.words[0] if self._u(f"ahu|{a}|{ck.name}") < self.p_ahu(a, ck.name) else ck.words[1]


# ---------------------------------------------------------------------------------------------- the terminal
def cause_str(c: tuple | None) -> str:
    return "none" if c is None else f"wrong:{c[1]}" if c[0] == "wrong" else c[0]


class Visit:
    """One visit at one tier, worked one command at a time. `do` charges minutes with the tool's accountant (a `Session` per complaint whose location is kept in step); `conclude` gives a
    final diagnosis; `finish` ends the visit. Nothing about the truth is exposed except the answers of `do`."""

    def __init__(self, event: W.Event, tier: str, cases: dict, wp: W.WorldParams):
        self.ev, self.tier = event, tier
        self.cases = [cases[(tier, r)] for r in event.rooms]
        self.oracle = TableOracle(event, wp.rel_a)
        self.acct = []
        for case, r in zip(self.cases, event.rooms):
            s = Session(case)
            s.ctx = D.Context(**W.context_dict(tier, r))
            self.acct.append(s)
        self.n = len(self.cases)
        self.cap = MAX_CHECKS_PER_COMPLAINT * self.n
        self.at: str | None = None
        self.done: set = set()
        self.ahu_word: dict = {}
        self.log: list[dict] = []
        self.concl: dict[int, tuple] = {}
        self.finished = False
        self.charged = 0
        self.commands: list[list] = []

    # ---- helpers
    @property
    def minutes(self) -> float:
        return float(sum(s.elapsed for s in self.acct))

    def _open(self) -> None:
        if self.finished:
            raise VisitError("the visit has been finished")

    def _idx(self, n: int) -> int:
        if not 1 <= n <= self.n:
            raise VisitError(f"complaint {n}: choose 1 to {self.n}")
        return n - 1

    def _check(self, i: int, name: str) -> K.CheckV1:
        ck = next((c for c in self.cases[i].checks if c.name == name), None)
        if ck is None:
            raise VisitError(f"no check called {name!r}; the list is in `brief`")
        return ck

    def _avail(self, i: int, ck: K.CheckV1) -> D.Avail:
        s = self.acct[i]
        return D.availability(ck, s.view(), s._eq(ck))

    def _target(self, i: int, ck: K.CheckV1, target: str | None) -> str:
        case = self.cases[i]
        target = case.doc if target is None else target
        if ck.is_reading or ck.doc_only:
            if target != case.doc:
                raise VisitError(f"{ck.name} is done on the documented box {case.doc} only")
        elif target not in case.candidates:
            raise VisitError(f"{ck.name} can be done on the documented box {case.doc} or on one of {[c for c in case.candidates if c != case.doc]}, not on {target!r}")
        return target

    def minutes_now(self, i: int, ck: K.CheckV1, target: str | None = None) -> float | None:
        """Minutes this check would be charged now, from where the technician stands (None = cannot be done in this call-out)."""
        av = self._avail(i, ck)
        if av.state == "unavailable":
            return None
        case, s = self.cases[i], self.acct[i]
        if ck.subject == "ahu" and (case.ahu, ck.name) in self.ahu_word:
            return 0.0
        return ck.minutes(self.at, s._place(ck, self._target(i, ck, target)), av.extra_min)

    # ---- commands
    def do(self, name: str, n: int, target: str | None = None) -> dict:
        self._open()
        i = self._idx(n)
        ck = self._check(i, name)
        case = self.cases[i]
        target = self._target(i, ck, target)
        av = self._avail(i, ck)
        if av.state == "unavailable":
            raise VisitError(f"{name} cannot be done in this call-out: it needs {', '.join(av.missing)}")
        if ck.subject == "ahu":
            key = (case.ahu, ck.name)
            if key in self.ahu_word:
                return dict(answer=self.ahu_word[key], minutes=0.0, repeat=True, total=self.minutes, at=self.at, first=False)
        elif (i, ck.name, target) in self.done:
            raise VisitError(f"{name} on {target} for complaint {n} was already done; its answer does not change")
        if self.charged >= self.cap:
            raise VisitError(f"the limit of {self.cap} checks for this visit has been reached: conclude every complaint and finish")
        word = self.oracle.ask_ahu(case.ahu, ck) if ck.subject == "ahu" else self.oracle.ask_room(i, ck, target)
        s = self.acct[i]
        s.at = self.at
        s.report(word, ck.name, target)
        minutes = s.log[-1].minutes
        self.at = s.at
        if ck.subject == "ahu":
            self.ahu_word[(case.ahu, ck.name)] = word
        else:
            self.done.add((i, ck.name, target))
        self.charged += 1
        first = not self.log
        self.log.append(dict(check=ck.name, complaint=i, target=target, word=word, minutes=minutes, subject=ck.subject))
        self.commands.append(["do", name, n, target])
        return dict(answer=word, minutes=minutes, repeat=False, total=self.minutes, at=self.at, first=first)

    def parse_cause(self, i: int, text: str) -> tuple:
        case, t = self.cases[i], text.strip()
        if t == "unlisted":
            return ("unlisted",)
        if t.startswith("wrong:"):
            box = t[6:]
            if box == case.doc or box not in case.candidates:
                raise VisitError(f"wrong:<box> must name one of {[c for c in case.candidates if c != case.doc]}")
            return ("wrong", box)
        if t in C.BY_ID:
            spec = C.BY_ID[t]
            if spec.needs == "reheat" and self.acct[i].view().have("feature:reheat", case.doc) is False:
                raise VisitError(f"{t}: the box serving complaint {i + 1} has no reheat")
            return (t,)
        raise VisitError(f"unknown cause {text!r}: use one of {list(LEAF_IDS)}, wrong:<box> or unlisted")

    def conclude(self, n: int, cause: str, confidence: str) -> None:
        self._open()
        i = self._idx(n)
        if confidence not in ("confident", "unsure"):
            raise VisitError("confidence must be 'confident' or 'unsure'")
        self.concl[i] = (self.parse_cause(i, cause), confidence == "confident")
        self.commands.append(["conclude", n, cause, confidence])

    def finish(self) -> None:
        self._open()
        missing = [i + 1 for i in range(self.n) if i not in self.concl]
        if missing:
            raise VisitError(f"complaints without a conclusion: {missing}")
        self.finished = True
        self.commands.append(["finish"])

    def replay(self, commands: list[list]) -> "Visit":
        for c in commands:
            {"do": lambda a: self.do(*a), "conclude": lambda a: self.conclude(*a), "finish": lambda a: self.finish()}[c[0]](c[1:])
        return self

    # ---- outcome
    def result(self) -> dict:
        """The visit as the policies report theirs. An unconcluded complaint has guess None (wrong) and is not concluded."""
        guess = [self.concl[i][0] if i in self.concl else None for i in range(self.n)]
        conc = [bool(self.concl[i][1]) if i in self.concl else False for i in range(self.n)]
        return dict(minutes=self.minutes, n_checks=self.charged, guess=guess, concluded=conc, finished=self.finished, first_ahu=bool(self.log and self.log[0]["subject"] == "ahu"),
                    trace=[(t["complaint"], t["check"], t["target"], t["word"]) for t in self.log])


# ---------------------------------------------------------------------------------------------- what the technician reads
def ahu_ranges(cases: dict) -> str:
    b = next(iter(cases.values())).building
    ahu = b.base.claims["ahu_vav"]
    out = []
    for a in sorted(set(ahu.values())):
        boxes = sorted((k for k, v in ahu.items() if v == a), key=lambda s: int(s.split("-")[1]))
        out.append(f"{a} serves {', '.join(boxes)}")
    return "; ".join(out)


def generic_text(ck: K.CheckV1) -> str:
    return ck.text.format(box="the complaint's box", t="the target box", m="the complaint's room", ahu="the complaint's air handler")


def brief_text(v: Visit, sid: str, cases: dict) -> str:
    c0 = v.cases[0]
    b = c0.building
    L = [f"SESSION {sid}. You are at a building with {W.N_AHU} air handlers and {W.N_BOX} VAV boxes, one box per room (Room-0 ... Room-{W.N_BOX - 1}, served by VAV-0 ... VAV-{W.N_BOX - 1}).",
         f"THE DRAWINGS SAY: {ahu_ranges(cases)}. Room-k is served by VAV-k.", "",
         f"COMPLAINTS TODAY ({v.n}); the rooms not listed have no complaint:"]
    for i, (case, r) in enumerate(zip(v.cases, v.ev.rooms)):
        alts = [x for x in case.candidates if x != case.doc]
        L.append(f"  {i + 1}. {case.member}: the drawings say VAV-{r}, on {case.ahu}. If the drawings are wrong about its box, the alternatives to consider are {alts}.")
        if "attributes" in case.items:
            a = b.attrs.get(case.doc, {})
            aa = b.attrs.get(case.ahu, {})
            L.append(f"     design data on file: {case.doc} reheat {a.get('reheat')}, K-factor {a.get('k_factor')}, design airflow {a.get('design_airflow_cfm')} cfm, inlet {a.get('inlet_diameter_in')} in; "
                     f"{case.ahu} duct static setpoint {aa.get('static_setpoint_inwc')} in. w.c.")
    L += ["", "YOUR KIT AND ACCESS: a flow hood and a differential-pressure gauge; no occupant is available to ask. " +
          ("You can get into the building control system, and a point map exists (reads there are quick)." if "point_map" in c0.items else "You have NO access to the building control system (no control-system checks appear below).")]
    L += ["", "THE CHECKS YOU CAN DO (id | where | minutes if done now from scratch | what it tells you). `checks N` shows the minutes from where you then stand. "
          "Minutes include getting there, doing it and any waiting. A reading is 'abnormal' or 'normal'; the other checks answer 'yes' or 'no'. No check is perfectly reliable: an answer can be wrong in either direction.", ""]
    for ck in c0.checks:
        m = v.minutes_now(0, ck)
        if m is None:
            continue
        L.append(f"  {ck.name} | {'on a box you name' if ck.family == 'v0 check' else ck.family} | {m:g} min | {generic_text(ck)}")
    L += ["", "THE CAUSES YOU CAN CONCLUDE (use the id):"]
    for c in C.CAUSES:
        L.append(f"  {c.id}: {c.label} ({c.detail})" + ("; only if the box has reheat" if c.needs == "reheat" else ""))
    L += ["  wrong:<box>: the drawings are wrong about which box serves the room; it is the named alternative box", "  unlisted: the room is fed by a box that is not on the list",
          "", "COMMANDS (one per call):", "  brief | status | checks N | do CHECK N [TARGET_BOX] | conclude N CAUSE confident|unsure | finish",
          f"  N is the complaint number. Air-handler checks are read once and serve every complaint on that air handler (repeats cost nothing). "
          f"Checks on a box (the four 'command box...' and 'trace the duct' checks) can name a TARGET_BOX: the documented box or an alternative. The visit allows {v.cap} checks in all.",
          "  You must conclude every complaint before `finish`; you may change a conclusion by concluding again."]
    return "\n".join(L)


def checks_text(v: Visit, n: int) -> str:
    i = v._idx(n)
    L = [f"Minutes for complaint {n} ({v.cases[i].member}) from where you stand now ({v.at or 'start'}); a check already done is marked."]
    for ck in v.cases[i].checks:
        m = v.minutes_now(i, ck)
        if m is None:
            continue
        done = (v.cases[i].ahu, ck.name) in v.ahu_word if ck.subject == "ahu" else (i, ck.name, v.cases[i].doc) in v.done
        L.append(f"  {ck.name}: {m:g} min" + ("  [already done]" if done else ""))
    return "\n".join(L)


def status_text(v: Visit) -> str:
    L = [f"Minutes so far: {v.minutes:g}. Checks used: {v.charged} of {v.cap}. You are at: {v.at or 'the start'}."]
    for t in v.log:
        L.append(f"  complaint {t['complaint'] + 1}: {t['check']} on {t['target']} -> {t['word']} ({t['minutes']:g} min)")
    for i in range(v.n):
        c = v.concl.get(i)
        L.append(f"  conclusion {i + 1}: " + ("none yet" if c is None else f"{cause_str(c[0])} ({'confident' if c[1] else 'unsure'})"))
    return "\n".join(L)


def do_text(r: dict) -> str:
    if r["repeat"]:
        return f"ANSWER: {r['answer']}  (already read for this air handler; 0 min). Total so far: {r['total']:g} min."
    return f"ANSWER: {r['answer']}  (charged {r['minutes']:g} min; total so far {r['total']:g} min; you are now at {r['at']})"


# ---------------------------------------------------------------------------------------------- partners, scoring
def first_check_is_ahu(trace: list) -> bool:
    if not trace:
        return False
    name = next(x for x in trace[0] if isinstance(x, str) and x in K.BY_NAME)
    return K.BY_NAME[name].subject == "ahu"


def record(res: dict, ev: W.Event) -> dict:
    ok, wc, cn = J.score(res, ev)
    n = ev.n
    return dict(minutes=float(res["minutes"]), checks=float(res["n_checks"]), correct=int(ok), wc=int(wc), concluded=int(cn), n=n, acc=ok / n, wcr=wc / n, conc=cn / n,
                first_ahu=bool(res.get("first_ahu", first_check_is_ahu(res["trace"]) if "trace" in res else False)), abandoned=not res.get("finished", True))


def run_partners(ev: W.Event, tier: str, cases: dict, wp: W.WorldParams) -> dict:
    """{policy: record} on the TableOracle's answers."""
    cs = [cases[(tier, r)] for r in ev.rooms]
    ctxs = [W.context_dict(tier, r) for r in ev.rooms]
    out = {}
    for pol in PARTNERS:
        out[pol] = record(P.run_policy(pol, cs, TableOracle(ev, wp.rel_a), ctxs), ev)
    return out


def replay_policy(ev: W.Event, tier: str, cases: dict, wp: W.WorldParams, pol: str) -> tuple[float, int, float, int]:
    """Feed a partner's own action sequence through the terminal: (minutes, checks) as the terminal charges them, then the policy's own (gate G2)."""
    cs = [cases[(tier, r)] for r in ev.rooms]
    ctxs = [W.context_dict(tier, r) for r in ev.rooms]
    res = P.run_policy(pol, cs, TableOracle(ev, wp.rel_a), ctxs)
    v = Visit(ev, tier, cases, wp)
    v.cap = 10 ** 6                                                     # the stand-in's list has no cap; only the language model's visit does
    first_on = {}
    for i, c in enumerate(v.cases):
        first_on.setdefault(c.ahu, i)
    for t in res["trace"]:
        if t[0] == "group":                                         # fast_parent's air-handler question, asked through the first complaint on that air handler
            i, name, target = first_on[t[1]], t[2], t[3]
        elif t[0] == "ahu":                                         # the joint tool's air-handler option
            i, name, target = first_on[t[1]], t[2], None
        elif t[0] == "complaint":                                   # the joint tool's option on one complaint
            i, name, target = t[1], t[2], t[3]
        else:                                                       # the ticket tools' and the stand-in's (complaint, check, target, answer)
            i, name, target = t[0], t[1], t[2]
        v.do(name, i + 1, target)
    return v.minutes, v.charged, res["minutes"], res["n_checks"]


# ---------------------------------------------------------------------------------------------- analysis
def strat_arrays(recs: dict, visits: list[dict], tier: str, pol: str) -> dict:
    """{kind: {metric: array}} in the order of `visits`, from recs[(visit id, tier, pol)]."""
    out = {}
    for k in KINDS:
        rows = [recs[(v["id"], tier, pol)] for v in visits if v["kind"] == k]
        out[k] = {m: np.array([r[m] for r in rows], float) for m in ("minutes", "checks", "acc", "wcr", "conc", "first_ahu")}
    return out


def wmean(arr: dict, w: dict, metric: str, kinds=KINDS) -> float:
    ws = sum(w[k] for k in kinds)
    return float(sum(w[k] * arr[k][metric].mean() for k in kinds) / ws)


def wboot(diff: dict, w: dict, kinds, B: int, rng: np.random.Generator) -> tuple[float, float]:
    ws = sum(w[k] for k in kinds)
    tot = np.zeros(B)
    for k in kinds:
        n = len(diff[k])
        tot += w[k] * diff[k][rng.integers(0, n, (B, n))].mean(axis=1)
    lo, hi = np.percentile(tot / ws, [2.5, 97.5])
    return float(lo), float(hi)


def compare(A: dict, Bv: dict, w: dict, kinds, seed_key: tuple) -> dict:
    rng = np.random.default_rng([SEED, 5] + list(seed_key))
    d = {m: {k: A[k][m] - Bv[k][m] for k in kinds} for m in ("minutes", "acc", "wcr")}
    # the same resamples for every metric, so that the three intervals describe the same paired draws
    seeds = rng.integers(0, 2 ** 31, 3)
    ci = {m: wboot(d[m], w, kinds, BOOT_B, np.random.default_rng(int(s))) for m, s in zip(("minutes", "acc", "wcr"), seeds)}
    d_min, d_acc, d_wc = (sum(w[k] * d[m][k].mean() for k in kinds) / sum(w[k] for k in kinds) for m in ("minutes", "acc", "wcr"))
    base = wmean(Bv, w, "minutes", kinds)
    r_min = d_min / base if base > 0 else float("nan")
    ts, as_ = SG.time_state(r_min, ci["minutes"]), SG.acc_state(d_acc, ci["acc"])
    ma, mb = wmean(A, w, "minutes", kinds), base
    kind, wstar = break_even(ma, wmean(A, w, "acc", kinds), mb, wmean(Bv, w, "acc", kinds))
    return dict(d_min=d_min, r_min=r_min, d_acc=d_acc, d_wc=d_wc, ci_min=ci["minutes"], ci_acc=ci["acc"], ci_wc=ci["wcr"], time=ts, acc=as_, label=SG.label(ts, as_),
                safety=SG.safety_flag(d_wc, ci["wcr"]), break_even=kind, wrong_cost=wstar, minutes_a=ma, minutes_b=mb)


SUBS = dict(all=KINDS, single=("single",), multi=("multi",), shared=("shared",))


def analyze(recs: dict, visits: list[dict], shares: dict) -> dict:
    pols = ("llm",) + PARTNERS
    arr = {(t, p): strat_arrays(recs, visits, t, p) for t in TIERS for p in pols}
    summ, cmp_ = {}, {}
    for ti, t in enumerate(TIERS):
        for p in pols:
            for si, (sub, kinds) in enumerate(SUBS.items()):
                a = arr[(t, p)]
                summ[(t, p, sub)] = dict(n=sum(len(a[k]["minutes"]) for k in kinds), minutes=wmean(a, shares, "minutes", kinds), checks=wmean(a, shares, "checks", kinds), accuracy=wmean(a, shares, "acc", kinds),
                                         wrong_confident=wmean(a, shares, "wcr", kinds), concluded=wmean(a, shares, "conc", kinds), first_ahu=wmean(a, shares, "first_ahu", kinds))
        for ci_, (name, (a, b)) in enumerate(COMPS.items()):
            for si, (sub, kinds) in enumerate(SUBS.items()):
                cmp_[(t, name, sub)] = compare(arr[(t, a)], arr[(t, b)], shares, kinds, (ti, ci_, si))
    return dict(sum=summ, cmp=cmp_, counts={k: sum(v["kind"] == k for v in visits) for k in KINDS})


def predictions(an: dict) -> dict:
    s, c = an["sum"], an["cmp"]
    p = {}
    p["P1"] = (c[("T3", "P", "all")]["d_min"] >= 0, f"T3, LLM - routine: {c[('T3', 'P', 'all')]['d_min']:+.1f} min ({100 * c[('T3', 'P', 'all')]['r_min']:+.0f}%)")
    p["P2"] = (abs(c[("T2", "P", "all")]["r_min"]) < P2_BAR, f"T2, LLM - routine: {100 * c[('T2', 'P', 'all')]['r_min']:+.0f}%")
    p["P3"] = (all(c[(t, "P", "all")]["d_acc"] < 0 for t in TIERS), "accuracy LLM - routine: " + ", ".join(f"{t} {c[(t, 'P', 'all')]['d_acc']:+.3f}" for t in TIERS))
    p["P4"] = (all(c[(t, "P", "all")]["d_wc"] >= P4_BAR for t in TIERS), "wrong-and-confident LLM - routine: " + ", ".join(f"{t} {c[(t, 'P', 'all')]['d_wc']:+.3f}" for t in TIERS))
    p["P5"] = (all(c[(t, "P", "shared")]["d_min"] >= 0 for t in TIERS), "shared visits, minutes LLM - routine: " + ", ".join(f"{t} {c[(t, 'P', 'shared')]['d_min']:+.1f}" for t in TIERS))
    p["P6"] = (all(c[(t, "R", "all")]["d_acc"] >= P6_BAR for t in TIERS), "accuracy LLM - fast_parent: " + ", ".join(f"{t} {c[(t, 'R', 'all')]['d_acc']:+.3f}" for t in TIERS))
    p["P7"] = (c[("T2", "R", "all")]["d_min"] >= 0, f"T2, LLM - fast_parent: {c[('T2', 'R', 'all')]['d_min']:+.1f} min")
    p["P8"] = (all(s[(t, "llm", "shared")]["first_ahu"] >= P8_BAR for t in TIERS), "first check at the air handler, shared visits: " + ", ".join(f"{t} {100 * s[(t, 'llm', 'shared')]['first_ahu']:.0f}%" for t in TIERS))
    return p


def decision(an: dict) -> str:
    out = []
    for t in TIERS:
        e = an["cmp"][(t, "P", "all")]
        d = "THE LLM TECHNICIAN IS FASTER" if e["time"] == "FASTER" and e["acc"] != "LESS" else "THE ROUTINE IS FASTER" if e["time"] == "SLOWER" else "NO CLEAR SPEED DIFFERENCE AT THIS SIZE"
        out.append(f"{t}: {d} (accuracy {e['acc']})")
    return "; ".join(out)


# ---------------------------------------------------------------------------------------------- the audit of a session's transcript
def audit_tool_calls(tool_calls: list[dict], launcher: str) -> list[str]:
    """Violations in a list of {name, input} tool calls: anything other than a Bash command that runs the launcher (and nothing chained to it)."""
    bad = []
    for c in tool_calls:
        if c.get("name") == "SubagentHandback":                                              # the harness's own way of delivering a subagent's final report, not a technician tool
            continue
        cmd = str(c.get("input", {}).get("command", "")) if c.get("name") == "Bash" else None
        if cmd is None:
            bad.append(f"tool {c.get('name')!r}")
        elif not cmd.strip().startswith(launcher) or any(x in cmd for x in (";", "&&", "||", "|", "`", "$(", ">", "<", "\n")):
            bad.append(f"command {cmd[:80]!r}")
    return bad


def tool_calls_in_transcript(path) -> list[dict]:
    """Every tool call ({name, input}) in a session transcript (JSONL, one JSON object per line; the calls are found wherever they are nested)."""
    out = []

    def walk(o):
        if isinstance(o, dict):
            if o.get("type") == "tool_use" and "name" in o:
                out.append(dict(name=o["name"], input=o.get("input", {})))
            for x in o.values():
                walk(x)
        elif isinstance(o, list):
            for x in o:
                walk(x)

    for line in open(path):
        line = line.strip()
        if line:
            try:
                walk(json.loads(line))
            except json.JSONDecodeError:
                out.append(dict(name="UNREADABLE-LINE", input={}))
    return out


def dumps(obj) -> str:
    return json.dumps(obj, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
