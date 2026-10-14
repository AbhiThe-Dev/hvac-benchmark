"""The simulated world of Addendum 30: a synthetic well-documented building, visits (events) with several complaints drawn from a generative model, and the simulated technician.
Nothing here is evidence about real buildings or technicians.

The building: 3 air handlers with 8 boxes and 8 rooms each. Documentation is complete and correct except where the world's `map` factor says otherwise (an event may have a box whose
TRUE air handler is not its documented one; a room's documented box may be wrong, as in v1).
An event: each air handler is ok / fan off / low static (probability `f`); each room has a local fault with probability RHO; rooms on a faulty air handler are affected with the
probability of its state; a room complains if it has a local fault or is affected; the first-order cause of a complaint is the upstream one if it is affected, else its local one.
The simulated technician answers a check on a room or box from the TRUE response of that check under the complaint's first-order cause, and a check on an air handler from the TRUE
response under that air handler's state.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .. import model as M
from ..building import Building, Equipment
from ..v1 import catalogue as K
from ..v1 import causes as C
from ..v1 import data as D
from ..v1.engine import CaseV1, make_case_v1
from .joint import FAN_SHARE, STATES, UPSTREAM

SEED = 30
N_AHU, PER_AHU = 3, 8
N_BOX = N_AHU * PER_AHU
RHO = 0.03
R_AFFECT = {"ahu_fan_off": 0.9, "low_static": 0.5}
MAX_REDRAW = 10000
TIER_ITEMS: dict[str, frozenset] = {"T2": D.TIERS["T2"], "T3": D.TIERS["T3"]}
TIER_NAMES = tuple(TIER_ITEMS)
TOOL_RATING = "mostly_right"
UPSTREAM_CAUSES = tuple((s,) for s in UPSTREAM)


def ahu_id(a: int) -> str:
    return f"AHU-{a}"


def true_reheat(i: int) -> bool:
    return i % 3 != 0


def make_building2() -> D.Building1:
    """24 rooms and boxes on 3 air handlers, with attributes and control-system points for everything (a well-documented building); the documentation is correct."""
    eq = {ahu_id(a): Equipment(ahu_id(a), "AHU", f"Area{a}") for a in range(N_AHU)}
    vz, av = {}, {}
    attrs, points = {}, {}
    for i in range(N_BOX):
        a = i // PER_AHU
        eq[f"VAV-{i}"], eq[f"Room-{i}"] = Equipment(f"VAV-{i}", "VAV", f"Area{a}"), Equipment(f"Room-{i}", "Zone", f"Area{a}")
        vz[f"Room-{i}"], av[f"VAV-{i}"] = f"VAV-{i}", ahu_id(a)
        attrs[f"VAV-{i}"] = dict(reheat="hydronic" if true_reheat(i) else "none", pressure_independent=True, k_factor=1000 + 100 * i, design_airflow_cfm=600 + 50 * i, inlet_diameter_in=6 + 2 * (i % 3))
        points[f"VAV-{i}"] = dict(status=f"V{i}.STS", airflow=f"V{i}.CFM", damper=f"V{i}.DMPR", reheat=f"V{i}.RH")
        points[f"Room-{i}"] = dict(temperature=f"V{i}.ZNT")
    for a in range(N_AHU):
        attrs[ahu_id(a)] = dict(static_setpoint_inwc=1.2)
        points[ahu_id(a)] = dict(fan_status=f"AHU{a}.SF", static_pressure=f"AHU{a}.DSP")
    return D.Building1(Building("synthetic joint", eq, {"vav_zone": vz, "ahu_vav": av}), attrs, points)


def tool_settings() -> M.Settings:
    return M.Settings().with_drawings(TOOL_RATING)


def tier_context(tier: str, room: int) -> D.Context:
    """Everything the tool could ask is declared, so it asks nothing: the technician has an instrument and no occupant is available; reheat follows the documented attributes (declared
    from them here so that a session and its stand-ins agree); control-system access is the tier's."""
    return D.Context(reheat="yes" if true_reheat(room) else "no", bas_access="yes" if "bas_access" in TIER_ITEMS[tier] else "no", instrument="yes", occupant="no")


def context_dict(tier: str, room: int) -> dict:
    c = tier_context(tier, room)
    return dict(reheat=c.reheat, bas_access=c.bas_access, instrument=c.instrument, occupant=c.occupant)


def make_cases(bld: D.Building1 | None = None) -> dict:
    """{(tier, room): the tool's v1 case for a complaint from that room}: the tool's assumptions, never the world's."""
    bld = bld or make_building2()
    s = tool_settings()
    return {(t, r): make_case_v1(bld, f"Room-{r}", TIER_ITEMS[t], settings=s, context=tier_context(t, r), member_name=f"Room {r}") for t in TIER_NAMES for r in range(N_BOX)}


# ---------------------------------------------------------------------------------------------- the world's parameters
@dataclass(frozen=True)
class WorldParams:
    f: float                     # per-air-handler probability of an upstream fault in the visit's window
    q_ahu: float                 # probability that a box's TRUE air handler is not its documented one
    p_wrong: float               # the world's P(the documented box of a room is wrong)
    rel_a: float                 # check reliability: every response probability moved this far toward 0.5
    extra_states: tuple = ()                            # Addendum 37: upstream states beyond ahu_fan_off/low_static, e.g. ("econ_fault",); empty by default (a no-op)
    extra_share: dict = field(default_factory=dict)     # each extra state's share of f, the FAN_SHARE equivalent
    extra_affect: dict = field(default_factory=dict)    # each extra state's P(a room on it complains), the R_AFFECT equivalent

    @property
    def states(self) -> tuple:
        return STATES + self.extra_states

    @property
    def upstream(self) -> tuple:
        return self.states[1:]

    def state_prior(self) -> np.ndarray:
        extra_total = sum(self.extra_share.values())
        base = np.array([FAN_SHARE, 1.0 - FAN_SHARE]) * (1.0 - extra_total)
        extra = np.array([self.extra_share[s] for s in self.extra_states])
        return np.concatenate(([1.0 - self.f], self.f * base, self.f * extra))

    def r_affect(self) -> dict:
        return {**R_AFFECT, **self.extra_affect}


def local_prior(case: CaseV1, p_wrong: float, room: int, upstream: tuple = UPSTREAM, extra_causes: tuple = (), shares: dict | None = None) -> tuple[list, np.ndarray]:
    """(causes, prior) of a room's LOCAL first-order cause in the world: v1's prior under the world's P(wrong), without the upstream causes, renormalised. `upstream`, `extra_causes` and
    `shares` (Addendum 37) let a study add upstream states beyond ahu_fan_off/low_static; the defaults reproduce today's behaviour exactly."""
    causes, prior = C.make_prior_v1(case.candidates, case.doc, M.Settings(p_wrong=p_wrong), docs=True, weights=case.weights, shares=shares, reheat=true_reheat(room),
                                    pressure_independent=True, extra_causes=extra_causes)
    p = np.array(prior, float)
    for u in upstream:
        p[causes.index((u,))] = 0.0
    return causes, p / p.sum()


# ---------------------------------------------------------------------------------------------- an event
@dataclass
class Event:
    idx: int
    i: int
    u: dict                      # air handler id -> state
    true_ahu: dict               # box id -> its TRUE air handler
    rooms: list                  # room numbers of the complaints, in arrival order
    causes: list                 # first-order cause of each complaint, in arrival order
    true_ahu_of: list            # the true air handler of each complaint's true box, in arrival order
    upstream: tuple = UPSTREAM   # Addendum 37: which cause ids count as upstream for `shared`, below; set by draw_event from the world that generated this event

    @property
    def n(self) -> int:
        return len(self.rooms)

    @property
    def shared(self) -> bool:
        """At least two complaints whose first-order cause is upstream on the same (true) air handler."""
        counts: dict = {}
        for c, a in zip(self.causes, self.true_ahu_of):
            if c[0] in self.upstream:
                counts[a] = counts.get(a, 0) + 1
        return any(v >= 2 for v in counts.values())

    @property
    def kind(self) -> str:
        return "single" if self.n == 1 else "shared" if self.shared else "multi"


def draw_event(idx: int, i: int, wp: WorldParams, cases: dict, extra_causes: tuple = (), shares: dict | None = None) -> Event:
    """Event `i` of cell `idx`, from the stream [SEED, idx, 0, i]; independent of every policy and tier. `extra_causes`/`shares` (Addendum 37) must match `wp.extra_states`: they tell
    `local_prior` which extra upstream cause(s), if any, to remove from each room's LOCAL prior (and at what relative rate) so the world's local and upstream stories do not double-count."""
    rng = np.random.default_rng([SEED, idx, 0, i])
    states, upstream, r_affect = wp.states, wp.upstream, wp.r_affect()
    sp = wp.state_prior()
    ahus = [ahu_id(a) for a in range(N_AHU)]
    priors = {r: local_prior(cases[("T2", r)], wp.p_wrong, r, upstream=upstream, extra_causes=extra_causes, shares=shares) for r in range(N_BOX)}
    for _ in range(MAX_REDRAW):
        u = {a: states[int(rng.choice(len(sp), p=sp))] for a in ahus}
        true_ahu = {}
        for b in range(N_BOX):
            doc = ahus[b // PER_AHU]
            flip, alt = rng.random() < wp.q_ahu, int(rng.integers(N_AHU - 1))
            others = [a for a in ahus if a != doc]
            true_ahu[f"VAV-{b}"] = others[alt] if flip else doc
        rooms, causes, tas = [], [], []
        for r in range(N_BOX):
            has_local, ci, ua = rng.random() < RHO, None, rng.random()
            cs, pr = priors[r]
            ci = int(rng.choice(len(cs), p=pr))
            local = cs[ci] if has_local else None
            tb = local[1] if local is not None and local[0] == "wrong" else f"VAV-{r}"
            ta = true_ahu[tb]
            state = u[ta]
            affected = state != "ok" and ua < r_affect[state]
            if has_local or affected:
                rooms.append(r)
                causes.append((state,) if affected else local)
                tas.append(ta)
        if rooms:
            order = rng.permutation(len(rooms))
            return Event(idx, i, u, true_ahu, [rooms[k] for k in order], [causes[k] for k in order], [tas[k] for k in order], upstream)
    raise RuntimeError("no event with a complaint after MAX_REDRAW draws")


# ---------------------------------------------------------------------------------------------- the simulated technician
class Oracle:
    """Answers checks for one event from the TRUE responses. `rng` supplies the draws (one stream per policy and tier)."""

    def __init__(self, event: Event, rel_a: float, rng: np.random.Generator, checks: tuple = K.CATALOGUE):
        self.event = event
        self.rng = rng
        self.tc = {c.name: c for c in K.degrade_all(checks, rel_a)}

    def p_room(self, i: int, ck_name: str, target: str) -> float:
        p = K.p_pos(self.tc[ck_name], self.event.causes[i], target, f"VAV-{self.event.rooms[i]}")
        return float(np.clip(p, M.RATE_FLOOR, 1.0 - M.RATE_FLOOR))

    def p_ahu(self, a: str, ck_name: str) -> float:
        ck = self.tc[ck_name]
        u = self.event.u[a]
        p = ck.bg if u == "ok" else ck.detects.get(u, ck.bg)
        return float(np.clip(p, M.RATE_FLOOR, 1.0 - M.RATE_FLOOR))

    def ask_room(self, i: int, ck: K.CheckV1, target: str) -> str:
        return ck.words[0] if self.rng.random() < self.p_room(i, ck.name, target) else ck.words[1]

    def ask_ahu(self, a: str, ck: K.CheckV1) -> str:
        return ck.words[0] if self.rng.random() < self.p_ahu(a, ck.name) else ck.words[1]
