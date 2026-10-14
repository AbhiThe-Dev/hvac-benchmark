"""Branching expert decision trees, and the machine that runs them on a visit (PREREGISTRATION_DR.md Addendum 43). Simulation only; nothing here is evidence about real technicians.

A tree is plain data (JSON): nodes that do a check from the tool's own catalogue and branch on the result, and leaves that name a cause. It is run on the SAME visits, with the SAME answer
table (`study_llm.TableOracle`), the SAME check minutes (the tool's own accountant: v1's `Session` used only to charge minutes, track the technician's location and apply fallback costs for
missing data, exactly as `study_fast_v1.Doer` does for the stand-ins), the SAME 12-checks-per-complaint limit and the SAME scoring as the adaptive tool. What differs is only the decision
logic: a fixed, human-written branching procedure instead of a belief that is updated after every answer.

DSL (also given, without the tool's numbers, to the independent authors of Addendum 43's trees L1 and L2):
  {"name": str, "preamble": node | null, "root": node}
  check:        {"op": "check", "check": [names...], "target": "box" | "ahu", "pos": node, "neg": node, "na": node?, "memo_only": bool?, "why": str?}
                does the FIRST available check of the list; follows `pos` when the answer is the check's positive word (abnormal / yes), else `neg`; follows `na` (default: `neg`) when none
                of the listed checks can be done in this data tier or on this box. `target: "ahu"` is a reading of the air handler: it is remembered for every complaint on that air handler
                (free after the first time; the same quantity read by another route counts: bas_static = ahu_gauge, bas_ahu_fan = ahu_visit). `memo_only: true` never does the check: it only
                consults what is already known (`na` when nothing is known).
  conclude:     {"op": "conclude", "cause": id, "sure": bool}     sure = the diagnosis is declared (a "concluded" complaint); not sure = a best guess, not declared
  find_feeder:  {"op": "find_feeder"}                              the documented box is wrong: v0's standard procedure (`study_fast_v1.walk_alternatives`) names the real box ("wrong", j) and
                                                                   concludes; if no candidate responds the answer is ("unlisted",), not declared
  escalate:     {"op": "escalate", "guess": id}                    could not find it: not declared; `guess` is the best guess that is still scored
  done:         {"op": "done"}                                     ends a preamble path
`preamble` runs once, BEFORE the individual complaints, for each air handler that has two or more complaints in the visit (its checks are charged to the first of them). `root` runs once
per complaint, in arrival order. A complaint's own checks are limited to MAX_CHECKS_PER_COMPLAINT (a node that would exceed it ends the complaint as not declared, guess 'other').
"""

from __future__ import annotations

import json
from pathlib import Path

from ..building import Equipment  # noqa: F401  (kept so the module imports the same package surface as its siblings)
from ..v1 import catalogue as K
from ..v1 import causes as C
from ..v1 import data as D
from ..v1.engine import CaseV1
from ..v1.study_fast_v1 import Doer, walk_alternatives  # noqa: F401  (walk_alternatives: the reference `find_feeder` is tested against)
from .joint import MAX_CHECKS_PER_COMPLAINT
from .world2 import Oracle

AHU_FAMILY = {"bas_static": "static", "ahu_gauge": "static", "bas_ahu_fan": "fan", "ahu_visit": "fan"}
OPS = ("check", "conclude", "find_feeder", "escalate", "done")
LEAF_OPS = ("conclude", "find_feeder", "escalate", "done")
MAX_NODES = 800                 # a hand-drawn flowchart reuses sub-branches by reference; this counts them as a tree (every copy), so it is generous
GUESS_IDS = tuple(C.BY_ID) + ("unlisted",)


# ---------------------------------------------------------------------------------------------- validation
def _walk(node: dict, path: str, depth: int, out: list, seen: list) -> None:
    seen.append(path)
    if depth > 40:
        out.append(f"{path}: deeper than 40 levels")
        return
    if not isinstance(node, dict) or node.get("op") not in OPS:
        out.append(f"{path}: not a node with op in {OPS}")
        return
    op = node["op"]
    if op == "check":
        names = node.get("check")
        if not isinstance(names, list) or not names or any(n not in K.BY_NAME for n in names):
            out.append(f"{path}: check must be a non-empty list of catalogue names, got {names!r}")
            return
        tgt = node.get("target")
        if tgt not in ("box", "ahu"):
            out.append(f"{path}: target must be 'box' or 'ahu', got {tgt!r}")
        else:
            subj = {K.BY_NAME[n].subject for n in names}
            if tgt == "ahu" and subj != {"ahu"}:
                out.append(f"{path}: target 'ahu' needs air-handler checks only, got {names}")
            if tgt == "box" and "ahu" in subj:
                out.append(f"{path}: target 'box' cannot use air-handler checks {[n for n in names if K.BY_NAME[n].subject == 'ahu']}")
        if node.get("memo_only") and tgt != "ahu":
            out.append(f"{path}: memo_only is for target 'ahu'")
        for br in ("pos", "neg"):
            if br not in node:
                out.append(f"{path}: missing {br!r}")
            else:
                _walk(node[br], f"{path}.{br}", depth + 1, out, seen)
        if "na" in node:
            _walk(node["na"], f"{path}.na", depth + 1, out, seen)
    elif op == "conclude":
        if node.get("cause") not in C.BY_ID or not isinstance(node.get("sure"), bool):
            out.append(f"{path}: conclude needs a cause id of the cause tree and a boolean `sure`, got {node.get('cause')!r}, {node.get('sure')!r}")
    elif op == "escalate":
        if node.get("guess") not in GUESS_IDS:
            out.append(f"{path}: escalate needs a guess in {GUESS_IDS}, got {node.get('guess')!r}")


def validate(tree: dict) -> list[str]:
    """Problems with a tree (empty when it is sound): unknown checks or causes, a missing branch, an air-handler check on the wrong target, a `done` outside the preamble, a size limit."""
    out: list[str] = []
    if not isinstance(tree, dict) or "root" not in tree or "name" not in tree:
        return ["tree needs 'name' and 'root'"]
    seen: list = []
    _walk(tree["root"], "root", 0, out, seen)
    pre = tree.get("preamble")
    if pre is not None:
        pseen: list = []
        _walk(pre, "preamble", 0, out, pseen)
        seen += pseen
        out += _only_ahu(pre, "preamble")
    out += _no_done(tree["root"], "root")
    if len(seen) > MAX_NODES:
        out.append(f"{len(seen)} nodes (limit {MAX_NODES})")
    return out


def _only_ahu(node: dict, path: str) -> list[str]:
    if not isinstance(node, dict):
        return []
    out = []
    if node.get("op") == "check":
        if node.get("target") != "ahu":
            out.append(f"{path}: the preamble may only check the air handler")
        for br in ("pos", "neg", "na"):
            if br in node:
                out += _only_ahu(node[br], f"{path}.{br}")
    elif node.get("op") != "done":
        out.append(f"{path}: the preamble may only end in `done`, found {node.get('op')!r}")
    return out


def _no_done(node: dict, path: str) -> list[str]:
    if not isinstance(node, dict):
        return []
    if node.get("op") == "done":
        return [f"{path}: `done` is only for the preamble"]
    out = []
    if node.get("op") == "check":
        for br in ("pos", "neg", "na"):
            if br in node:
                out += _no_done(node[br], f"{path}.{br}")
    return out


def count_nodes(node: dict) -> int:
    n = 1
    if node.get("op") == "check":
        n += sum(count_nodes(node[b]) for b in ("pos", "neg", "na") if b in node)
    return n


def leaves(node: dict, path: str = "root") -> list[tuple[str, dict]]:
    if node.get("op") == "check":
        return [x for b in ("pos", "neg", "na") if b in node for x in leaves(node[b], f"{path}.{b}")]
    return [(path, node)]


def load_tree(path: str | Path) -> dict:
    t = json.loads(Path(path).read_text())
    problems = validate(t)
    if problems:
        raise ValueError(f"{path}: " + "; ".join(problems[:6]))
    return t


# ---------------------------------------------------------------------------------------------- the machine
class _Visit:
    """Runs one tree on one visit. All state is per-visit; the tree is never mutated."""

    def __init__(self, tree: dict, cases: list[CaseV1], oracle: Oracle, ctxs: list[dict]):
        self.tree, self.cases, self.n = tree, cases, len(cases)
        self.doers = []
        for i, case in enumerate(cases):
            ask = (lambda i_: (lambda ck, tgt: oracle.ask_ahu(cases[i_].ahu, ck) if ck.subject == "ahu" else oracle.ask_room(i_, ck, tgt)))(i)
            self.doers.append(Doer(case, ctxs[i], ask))
        self.at: str | None = None
        self.own = [0] * self.n
        self.memo_ahu: dict = {}                       # (ahu id, 'static' | 'fan' | name) -> bool (True = positive / abnormal)
        self.memo_box: list[dict] = [dict() for _ in range(self.n)]
        self.trace: list = []
        self.guess: list = [None] * self.n
        self.concluded = [False] * self.n

    # ---- one check node
    def _available(self, i: int, ck: K.CheckV1) -> bool:
        d = self.doers[i]
        return D.availability(ck, d.s.view(), d.s._eq(ck)).state != "unavailable"

    def _do(self, i: int, ck: K.CheckV1) -> bool:
        d = self.doers[i]
        d.s.at = self.at
        pos = d.do(ck, self.cases[i].doc)
        self.at = d.s.at
        self.own[i] += 1
        self.trace.append((i, ck.name, self.cases[i].doc, ck.words[0] if pos else ck.words[1]))
        return pos

    def check(self, i: int, node: dict) -> str:
        """The branch to follow: 'pos', 'neg', 'na', or 'cap' (the complaint's check limit is reached)."""
        by = {c.name: c for c in self.cases[i].checks}
        ahu = node["target"] == "ahu"
        for name in node["check"]:
            ck = by[name]
            if ahu:
                key = (self.cases[i].ahu, AHU_FAMILY.get(name, name))
                if key in self.memo_ahu:
                    return "pos" if self.memo_ahu[key] else "neg"
                if node.get("memo_only"):
                    continue
            elif name in self.memo_box[i]:
                return "pos" if self.memo_box[i][name] else "neg"
            if node.get("memo_only") or not self._available(i, ck):
                continue
            if self.own[i] >= MAX_CHECKS_PER_COMPLAINT:
                return "cap"
            pos = self._do(i, ck)
            if ahu:
                self.memo_ahu[key] = pos
            else:
                self.memo_box[i][name] = pos
            return "pos" if pos else "neg"
        return "na"

    # ---- walking
    def walk(self, i: int, node: dict, pre: bool = False):
        """Returns None for a preamble that ended in `done`, else (guess, concluded)."""
        while True:
            op = node["op"]
            if op == "check":
                br = self.check(i, node)
                if br == "cap":
                    return (("other",), False)
                if br == "na" and "na" not in node:
                    br = "neg"
                node = node[br]
                continue
            if op == "done":
                return None
            if op == "conclude":
                return ((node["cause"],), bool(node["sure"]))
            if op == "escalate":
                return ((node["guess"],), False)
            if op == "find_feeder":
                return self.find_feeder(i)
            raise ValueError(f"unknown op {op!r}")

    def find_feeder(self, i: int):
        """v0's procedure (`study_fast_v1.walk_alternatives`: the cheaper act-and-watch check on each alternative box in candidate order, the first yes names that box) under this
        complaint's check limit: if the limit is reached before every candidate has been tried, the answer is 'unlisted', not declared."""
        case, d = self.cases[i], self.doers[i]
        observers = [c for c in case.checks if c.kind == "act_observe"]
        for j in case.candidates:
            if j == case.doc:
                continue
            if self.own[i] >= MAX_CHECKS_PER_COMPLAINT:
                return (("unlisted",), False)
            ck = min(observers, key=lambda c: c.minutes(self.at, j))
            d.s.at = self.at
            pos = d.do(ck, j)
            self.at = d.s.at
            self.own[i] += 1
            self.trace.append((i, ck.name, j, ck.words[0] if pos else ck.words[1]))
            if pos:
                return (("wrong", j), True)
        return (("unlisted",), False)

    def run(self) -> dict:
        pre = self.tree.get("preamble")
        if pre is not None:
            groups: dict = {}
            for i, c in enumerate(self.cases):
                groups.setdefault(c.ahu, []).append(i)
            for a, idx in groups.items():
                if len(idx) >= 2:
                    self.walk(idx[0], pre, pre=True)
        for i in range(self.n):
            self.guess[i], self.concluded[i] = self.walk(i, self.tree["root"])
        return dict(minutes=float(sum(d.s.elapsed for d in self.doers)), n_checks=int(sum(self.own)), guess=self.guess, concluded=self.concluded, trace=self.trace)


def run_tree(tree: dict, cases: list[CaseV1], oracle: Oracle, ctxs: list[dict]) -> dict:
    """The result of `policies.run_policy`'s shape: minutes, n_checks, guess (a cause tuple per complaint), concluded (per complaint), trace."""
    return _Visit(tree, cases, oracle, ctxs).run()


# ---------------------------------------------------------------------------------------------- Tree E: written from the guides and the technicians' own order (Addendum 43)
# Structure sources (not numbers): the order of ControlsHub 3.2 (a box that does not respond: air handler, controller status, 24 VAC, control signal, manual damper), 4.2 (a box that
# reads the wrong airflow: reading against setpoint, controller pressure against a gauge, static at the inlet, K-factor, maximum setpoint), 5.2 (airflow at the diffuser) and 9.2 (zone
# schedule and setpoint); the PNNL VAV maintenance checklist and performance monitoring page; top-down narrowing from the air handler when several rooms complain (the Smart Buildings
# Academy webinar and the experienced building engineer's own order); and the two real calls replayed in Addendum 38 (zone schedule and setpoint first; a heat stage before the contactors).
# Every `sure` below follows one rule that does not look at any rate: a cause is DECLARED on a finding that is either (a) a reading that names only that cause (power missing, signal missing,
# controller offline, fan stopped, damper stuck by hand, controller pressure disagreeing with the gauge) or (b) two different checks that both see it; a single check that also fires
# for several other causes, or a diagnosis by elimination, is only a best guess unless `decisive` (tree Ed) is set.
def tree_E(decisive: bool = False) -> dict:
    chk = lambda names, pos, neg, target="box", na=None, memo=False, why="": {  # noqa: E731
        "op": "check", "check": list(names), "target": target, "pos": pos, "neg": neg, **({"na": na} if na is not None else {}), **({"memo_only": True} if memo else {}), **({"why": why} if why else {})}
    con = lambda cause, sure=True, why="": {"op": "conclude", "cause": cause, "sure": bool(sure), **({"why": why} if why else {})}  # noqa: E731
    esc = lambda guess, why="": {"op": "escalate", "guess": guess, **({"why": why} if why else {})}  # noqa: E731
    STATIC, FAN = ("bas_static", "ahu_gauge"), ("bas_ahu_fan", "ahu_visit")
    ONE = lambda cause, why="": con(cause, True, why)  # noqa: E731                      # a reading that names only this cause
    GUESS = lambda cause, why="": con(cause, decisive, why)  # noqa: E731                # a finding that several causes share, or an elimination

    def confirmed(cause: str, second: tuple, why: str = "", target: str = "box") -> dict:
        """A first finding that several causes share: declared only if a second, different check agrees (tree Ed declares it at once)."""
        if decisive:
            return con(cause, True, why)
        return chk(second, con(cause, True, why + " (confirmed)"), con(cause, False, why + " (unconfirmed)"), target, na=con(cause, False, why + " (nothing to confirm with)"))

    # ---- what is left when nothing on the box, the air handler or the room explains it: is the documented box even the one that serves the room?
    def documentation() -> dict:
        return chk(("override_diffuser",), esc("other", "the box feeds the room and acts: the cause is elsewhere"),
                   chk(("confirm_acts",), {"op": "find_feeder", "why": "the box moves but the room does not follow it: the drawings are wrong"},
                       esc("actuator_fail", "the box does not move when commanded"), na=esc("other")),
                   why="command the documented box to full cooling: does the diffuser airflow follow?", na=esc("other"))

    # ---- the box delivers what it is asked, the room is still wrong (BAS): zone inputs first, then heating, then the room's own airflow and load
    def flow_ok() -> dict:
        capacity = chk(("design_load",), confirmed("capacity_design", ("flow_hood",), "design load against the box", ), documentation(), na=documentation())
        room_air = chk(("flow_hood",), chk(("diffuser_duct",), ONE("duct_diffuser", "diffuser or duct fault seen"), capacity,
                                           why="airflow at the diffuser is low although the box reads right: look at the diffuser and duct"), capacity,
                       why="airflow at the diffuser")
        thermostat = chk(("thermostat",), ONE("zone_sensor_setpoint", "the room's own thermostat is wrong"), room_air, why="thermostat against a reference thermometer")
        reheat = chk(("bas_reheat",), confirmed("reheat_fail", ("reheat_coil",), "heat called for, valve or stage not responding"), thermostat, na=thermostat,
                     why="the box has reheat: is it responding?")
        return chk(("bas_zone",), confirmed("zone_sensor_setpoint", ("thermostat",), "setpoint, schedule or mode wrong in the control system"), reheat,
                   why="the room's setpoint, schedule and mode are the cheapest and commonest explanation")

    # ---- the box does not act on its command: controller, power, signal, mechanics, then the box's own inlet pressure
    def actuation() -> dict:
        static_box = chk(("static_at_box",), ONE("low_static", "the inlet is starved although the air handler reads right: a restriction upstream of this box"), GUESS("actuator_fail", "power, signal and shaft are fine: by elimination, the actuator"),
                         why="a pinned-open damper with low flow can also be a starved inlet")
        manual = chk(("manual_damper_test",), ONE("damper_mech", "shaft stuck or binding"), static_box, why="turn the shaft by hand")
        signal = chk(("control_signal",), ONE("signal_fault", "no control signal at the actuator"), manual, why="control signal with the box commanded open")
        power = chk(("power_24vac",), ONE("no_power", "no 24 VAC at the actuator"), signal, why="24 VAC at the actuator")
        return chk(("bas_controller", "controller_leds"), ONE("controller_comms", "controller offline or faulted"), power, why="controller status first: free in the control system")

    # ---- the damper follows its command but the flow is off its setpoint: the flow reading, the controller's set-up, or the box being too small
    def sensing() -> dict:
        capacity = chk(("design_load",), confirmed("capacity_design", ("flow_hood",), "design load against the box"), esc("other"), na=esc("other"))
        hunting = chk(("bas_hunting",), confirmed("controller_config", ("max_airflow", "k_factor"), "damper and flow swinging"), capacity, why="five-minute look for hunting")
        maxflow = chk(("max_airflow",), confirmed("controller_config", ("k_factor",), "maximum setpoint differs from the design value"), hunting, why="maximum airflow setpoint against design")
        kfac = chk(("k_factor",), confirmed("controller_config", ("max_airflow",), "K-factor differs from the nameplate"), maxflow, why="programmed K-factor against the nameplate")
        ports = chk(("sensing_ports",), confirmed("flow_sensor", ("flow_vs_gauge",), "ports or tubing faulty"), kfac, why="flow ports and tubing")
        return chk(("flow_vs_gauge",), ONE("flow_sensor", "the controller's pressure disagrees with the gauge"), ports, why="controller's pressure reading against a gauge on the taps")

    # ---- the box does not deliver its setpoint: the air handler first (free in the control system, and one reading speaks for the whole air handler), then the box
    def flow_bad() -> dict:
        upstream = chk(FAN, con("ahu_fan_off", True, "airflow low, duct static low and the fan stopped: three findings agree"),
                       con("low_static", True, "airflow low and duct static low: two different checks agree"), "ahu", why="duct static is low: is the fan stopped?")
        local = chk(("bas_damper",), actuation(), sensing(), why="the air handler is fine: does the damper do what it is told?")
        return chk(STATIC, upstream, local, "ahu", why="a box that cannot deliver: duct static of its air handler")

    # ---- no control-system access at all: the physical order
    def physical() -> dict:
        capacity = chk(("design_load",), confirmed("capacity_design", ("flow_hood",), "design load against the box"), documentation(), na=documentation())
        reheat = chk(("reheat_coil",), ONE("reheat_fail", "the reheat valve, coil or element is faulty"), capacity, na=capacity, why="airflow is right at the diffuser: heating side")
        stuck_air = chk(FAN, con("ahu_fan_off", True, "inlet static low and the fan stopped"), con("low_static", True, "inlet static low and the fan running"), "ahu", why="inlet static is low: is the fan stopped?")
        at_box = chk(("controller_leds", "bas_controller"), ONE("controller_comms", "controller dead or off the network"),
                     chk(("power_24vac",), ONE("no_power", "no 24 VAC"), chk(("control_signal",), ONE("signal_fault", "no control signal"),
                         chk(("manual_damper_test",), ONE("damper_mech", "shaft stuck"),
                             chk(("sensing_ports",), confirmed("flow_sensor", ("flow_vs_gauge",), "ports or tubing faulty"), GUESS("actuator_fail", "power, signal and shaft fine: by elimination, the actuator"))))),
                     why="at the box: controller, power, signal, shaft")
        box_side = chk(("static_at_box",), stuck_air, at_box, why="inlet static of the box")
        room_air = chk(("flow_hood",), chk(("diffuser_duct",), ONE("duct_diffuser", "diffuser or duct fault seen"), box_side, why="low at the diffuser: diffuser and duct first"), reheat, why="airflow at the diffuser")
        return chk(("thermostat",), ONE("zone_sensor_setpoint", "the room's own thermostat is wrong"), room_air, why="no control system: start in the room with the thermostat")

    # ---- the visit's preamble: several complaints on one air handler -> read it once, first
    preamble = chk(STATIC, chk(FAN, {"op": "done"}, {"op": "done"}, "ahu"), {"op": "done"}, "ahu", why="two or more complaints on one air handler: read the shared parent first")
    # ---- the root, once per complaint. A reading of the air handler already known from an earlier complaint is used without being repeated.
    known_bad = chk(("bas_airflow", "flow_hood"), chk(FAN, con("ahu_fan_off", True, "air handler already found stopped; this box is starved too"),
                                                       con("low_static", True, "air handler already found low; this box is starved too"), "ahu", memo=True),
                    flow_ok(), why="the shared air handler is already known to be wrong: is THIS box starved by it?", na=flow_ok())
    root = chk(STATIC, known_bad, chk(("bas_airflow",), flow_bad(), flow_ok(), na=physical(), why="measured airflow against setpoint splits delivery faults from room-side faults"), "ahu", memo=True,
               why="already known from an earlier complaint on this air handler?", na=chk(("bas_airflow",), flow_bad(), flow_ok(), na=physical()))
    return {"name": "E_decisive" if decisive else "E_confirming", "preamble": preamble, "root": root}
