"""A JOINT session over the complaints of one visit (working model v2). Simulation-grade, unvalidated: every rate and minute is a placeholder.

v1 works one complaint at a time. Here several complaints (rooms) arrive together and the tool investigates them as one problem, because a fault at a shared parent (an air handler) can
explain several of them at once, and one reading of that parent then speaks for all its children.

THE MODEL. The complaints are grouped by their DOCUMENTED air handler. Per group there is one shared state u: `ok`, `ahu_fan_off` or `low_static`, with a prior. Given u the complaints
are independent. For a complaint with local-cause prior L over its causes (v1's prior with the two upstream causes removed) the joint probability of "this room complains AND its
first-order cause is c" is
    u = ok:                    rho * L(c)
    u = an upstream state s:   r_s                   for the upstream cause of s (the room is affected by the upstream fault: it complains)
                               (1 - r_s) * rho * L(c) for a local cause c (not affected, but has its own fault)
and the documented rooms of the group that did NOT complain each contribute the probability of not complaining under u. Observations of an air-handler check reweight u (one reading,
every complaint of the group hears it); observations of a room or box check reweight that complaint's causes exactly as in v1. Inference is exact: three states per group.

SELECTION. Every check that can be done (v1's availability, minutes and location rules) is an option: an air-handler check is ONE option per air handler that informs every complaint
of the group; room, box and act-and-watch checks are options per complaint and target. Score = expected reduction of the SUM over the group's complaints of the entropy of their
marginals, per minute; an option is worth doing if that is at least `min_rate` times the number of unconcluded complaints it informs (so the per-complaint rule is v1's).
A complaint is CONCLUDED when its leading marginal is at least tau AND a real observation has informed it (a check on it, or on its air handler): the pattern of complaints alone never
concludes, however strong (a clarification of Addendum 30 made before any comparison was read).
`lookahead=2` scores the top options by the gain of the option plus the best follow-up, per minute of both.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .. import model as M
from ..v1 import catalogue as K
from ..v1 import data as D
from ..v1.engine import CaseV1, Session

STATES = ("ok", "ahu_fan_off", "low_static")
UPSTREAM = STATES[1:]
FAN_SHARE = 5.0 / 17.0                # v1's placeholder shares of the two upstream causes, 0.05 : 0.12
MAX_CHECKS_PER_COMPLAINT = 12
LOOKAHEAD_TOP = 6
SEVERITY_SEP = "~"


def base_state(s: str) -> str:
    """The upstream cause a state stands for: severity levels of one cause ('low_static~1', 'low_static~2', ...) are separate states of the model that share the cause's id, its checks and
    its detection rates; every other state name is its own cause."""
    return s.split(SEVERITY_SEP, 1)[0]


@dataclass(frozen=True)
class JointSettings:
    """The joint model's assumptions (placeholders). `f`: probability that an air handler has an upstream fault in the visit's window; `rho`: per-room probability of a local fault;
    `r_fan`, `r_low`: probability that a room on an air handler in that state is affected (complains).
    `extra_states`, `extra_affect`, `extra_share` (Addendum 37): upstream states beyond `ahu_fan_off`/`low_static`, e.g. `("econ_fault",)`, each with its own affect rate
    (`extra_affect`, the `r_fan`/`r_low` equivalent) and its own share of `f` (`extra_share`, the `fan_share` equivalent, generalised). All empty by default, so `states`, `upstream`,
    `state_prior` and `affect` are then exactly what they were before this addendum -- algebraically, not just numerically (`extra_total` below is 0).
    `low_mix` (empty by default, which changes nothing): ((r, weight), ...), a mixture over HOW MANY of its rooms a low-static air handler starves, replacing the single `r_low`. Each level
    becomes its own state of the model ('low_static', 'low_static~1', ...) sharing low static's checks and cause, with its share `weight` of low static's prior; the data then pick the level.
    Weights must sum to 1; `r_low` is ignored when it is set. Why: a fixed `r_low` makes every SILENT room of a big air handler evidence against a shared fault (see live_demo_bldg11/README.md).
    `fan_mix` (empty by default, which changes nothing): the same for a fan-off air handler, replacing the single `r_fan` (states 'ahu_fan_off', 'ahu_fan_off~1', ...; they share fan off's checks and cause).
    """
    f: float = 0.03
    fan_share: float = FAN_SHARE
    rho: float = 0.03
    r_fan: float = 0.9
    r_low: float = 0.5
    extra_states: tuple = ()
    extra_affect: dict = field(default_factory=dict)
    extra_share: dict = field(default_factory=dict)
    low_mix: tuple = ()
    fan_mix: tuple = ()

    def __post_init__(self):
        if not 0.0 < self.f < 1.0:
            raise ValueError("f must be in (0, 1)")
        if not 0.0 < self.fan_share < 1.0:
            raise ValueError("fan_share must be in (0, 1)")
        if not 0.0 < self.rho < 1.0:
            raise ValueError("rho must be in (0, 1)")
        if not (0.0 < self.r_fan <= 1.0 and 0.0 < self.r_low <= 1.0):
            raise ValueError("r_fan and r_low must be in (0, 1]")
        if set(self.extra_states) != set(self.extra_affect) or set(self.extra_states) != set(self.extra_share):
            raise ValueError("extra_affect and extra_share must each give exactly one value per extra_state")
        if any(not 0.0 < v <= 1.0 for v in self.extra_affect.values()):
            raise ValueError("extra_affect values must be in (0, 1]")
        if sum(self.extra_share.values()) >= 1.0:
            raise ValueError("extra_share values must sum to less than 1")
        if self.low_mix:
            if any(not (0.0 < r <= 1.0 and w > 0.0) for r, w in self.low_mix):
                raise ValueError("low_mix: every level needs r in (0, 1] and a positive weight")
            if abs(sum(w for _, w in self.low_mix) - 1.0) > 1e-9:
                raise ValueError("low_mix weights must sum to 1")
        if self.fan_mix:
            if any(not (0.0 < r <= 1.0 and w > 0.0) for r, w in self.fan_mix):
                raise ValueError("fan_mix: every level needs r in (0, 1] and a positive weight")
            if abs(sum(w for _, w in self.fan_mix) - 1.0) > 1e-9:
                raise ValueError("fan_mix weights must sum to 1")

    @property
    def states(self) -> tuple:
        return (STATES + tuple(f"low_static{SEVERITY_SEP}{i}" for i in range(1, len(self.low_mix)))
                + tuple(f"ahu_fan_off{SEVERITY_SEP}{i}" for i in range(1, len(self.fan_mix))) + self.extra_states)

    @property
    def upstream(self) -> tuple:
        return self.states[1:]

    @property
    def state_prior(self) -> np.ndarray:
        extra_total = sum(self.extra_share.values())
        base = np.array([self.fan_share, 1.0 - self.fan_share]) * (1.0 - extra_total)
        extra = np.array([self.extra_share[s] for s in self.extra_states])
        if self.low_mix:                                                            # low static's share is split over its severity levels
            base = np.concatenate(([base[0]], base[1] * np.array([w for _, w in self.low_mix])))
        if self.fan_mix:                                                            # so is fan off's; its first level stays in the fan-off slot, the rest follow low static's levels (the order of `states`)
            fan = base[0] * np.array([w for _, w in self.fan_mix])
            base = np.concatenate(([fan[0]], base[1:], fan[1:]))
        return np.concatenate(([1.0 - self.f], self.f * base, self.f * extra))

    @property
    def affect(self) -> np.ndarray:
        """P(a room is affected | state), in `states` order."""
        low = [r for r, _ in self.low_mix] if self.low_mix else [self.r_low]
        fan = [r for r, _ in self.fan_mix] if self.fan_mix else [self.r_fan]
        return np.array([0.0, fan[0]] + low + fan[1:] + [self.extra_affect[s] for s in self.extra_states])

    @property
    def p_complain(self) -> np.ndarray:
        """P(a room complains | state)"""
        return 1.0 - (1.0 - self.affect) * (1.0 - self.rho)


def entropy_rows(m: np.ndarray) -> np.ndarray:
    """Entropy in bits along the last axis."""
    m = np.asarray(m, float)
    return -(m * np.log2(np.where(m > 0, m, 1.0))).sum(axis=-1)


def ahu_row(ck: K.CheckV1, upstream: tuple = UPSTREAM) -> np.ndarray:
    """P(positive | air-handler state), in `(ok, *upstream)` order, for a check whose subject is the air handler: the catalogue's detection level for each state, the false-alarm rate
    for `ok`. `upstream` defaults to the original two states (Addendum 37 generalises this to N; the default is a no-op)."""
    if not ck.is_reading:
        raise ValueError(f"{ck.name!r} is not a reading check")
    p = np.array([ck.bg] + [ck.detects.get(base_state(s), ck.bg) for s in upstream], float)
    return np.clip(p, M.RATE_FLOOR, 1.0 - M.RATE_FLOOR)


BEARS_ON_AHU = 0.5


def bears_on_ahu(ck: K.CheckV1, upstream: tuple = UPSTREAM) -> bool:
    """Does a check on a room or box speak about its air handler (Addendum 31)? A reading check that comes back abnormal with probability at least 0.5 under AT LEAST ONE upstream cause
    and at most 0.5 under every other cause and as a false alarm (Addendum 37 generalises "both" to "at least one": empirically identical to "both" across the whole catalogue whenever
    there are exactly the original two upstream causes, since the one check that qualifies, `static_at_box`, detects both of them strongly; the two rules only start to differ once a
    third upstream state exists). In v1's catalogue that is `static_at_box` alone: a flow hood or an airflow read responds to many local causes and does not qualify."""
    if not ck.is_reading or ck.subject == "ahu":
        return False
    others = [ck.bg] + [p for c, p in ck.detects.items() if c not in upstream]
    return any(ck.detects.get(base_state(s), ck.bg) >= BEARS_ON_AHU for s in upstream) and max(others) <= BEARS_ON_AHU


def rooms_per_ahu(case: CaseV1) -> dict[str, int]:
    """Documented rooms per documented air handler, from the building's claims."""
    b = case.building.base
    out: dict[str, int] = {}
    for room, box in b.claims.get("vav_zone", {}).items():
        a = b.claims.get("ahu_vav", {}).get(box)
        if a is not None:
            out[a] = out.get(a, 0) + 1
    return out


@dataclass
class State:
    """Everything observed so far. `lik[i]` = product of the likelihoods of complaint i's own (room and box) observations over its causes; `ahu_ll[a]` = log-likelihood of the
    observations of air handler a over its three states."""
    lik: list
    ahu_ll: dict
    done_c: frozenset = frozenset()
    done_a: frozenset = frozenset()
    at: str | None = None
    elapsed: float = 0.0
    n_checks: int = 0
    informed: frozenset = frozenset()       # complaints for which a real observation (not an 'unsure') has been taken: a check on them, or on their air handler

    def clone(self) -> "State":
        return State(list(self.lik), dict(self.ahu_ll), self.done_c, self.done_a, self.at, self.elapsed, self.n_checks, self.informed)


@dataclass
class GroupStats:
    idx: list
    W: np.ndarray                     # posterior over the group's states (3,)
    Z: np.ndarray                     # (k, 3): z_i(u) = sum_c J_i[u, c] lik_i[c]
    A: list                           # per complaint (3, n_causes): J_i * lik_i
    marg: list                        # per complaint: marginal over its causes
    H: float                          # sum of the marginals' entropies


@dataclass(frozen=True)
class JOption:
    kind: str                         # "complaint" | "ahu"
    who: object                       # complaint index | air handler id
    check: K.CheckV1
    target: str
    place: str
    minutes: float
    gain: float
    pyes: float
    audience: int
    avail: D.Avail

    @property
    def key(self) -> tuple:
        return (self.kind, self.who, self.check.name, self.target)


class JointModel:
    """The static part: the complaints (one v1 case each), their groups, priors and the joint tables. All the arithmetic on a `State` lives here."""

    def __init__(self, cases: list[CaseV1], js: JointSettings | None = None, children: dict | None = None, group_informing: bool = False, scale_audience: bool = True):
        if not cases:
            raise ValueError("at least one complaint")
        self.group_informing = group_informing                        # Addendum 31: a reading that bears on the air handler informs the whole group (off: Addendum 30's rule)
        self.scale_audience = scale_audience                          # Addendum 31, secondary arm: an air-handler reading's rate threshold is min_rate x its audience (True, Addendum 30) or min_rate (False)
        self.js = js or JointSettings()
        self.cases = list(cases)
        self.n = len(cases)
        self.ahu = []
        for c in cases:
            if not c.docs or c.ahu is None:
                raise ValueError("every complaint needs the drawings' claims and a documented air handler (tier T1 or above)")
            self.ahu.append(c.ahu)
        self.groups: dict[str, list[int]] = {}
        for i, a in enumerate(self.ahu):
            self.groups.setdefault(a, []).append(i)
        self.children = children if children is not None else rooms_per_ahu(cases[0])
        for a, idx in self.groups.items():
            if self.children.get(a, 0) < len(idx):
                raise ValueError(f"{len(idx)} complaints on {a!r} but only {self.children.get(a, 0)} documented rooms")
        self.upstream = self.js.upstream                              # Addendum 37: (ahu_fan_off, low_static) by default, longer once extra_states is set
        self.n_states = len(self.js.states)
        self.causes, self.L, self.J, self.marg0 = [], [], [], []
        pc = self.js.p_complain
        self.log_prior = np.log(self.js.state_prior)
        self.log_quiet = np.log1p(-pc)                                # log P(a room does not complain | u)
        affect = self.js.affect                                       # [0.0, r_fan, r_low, *extra_affect[s] for s in extra_states], aligned with self.js.states
        for c in cases:
            causes, prior = Session(c)._prior()
            missing = [u for u in self.upstream if (base_state(u),) not in causes]
            if missing:
                raise ValueError(f"the cause list must contain every upstream cause: missing {missing}")
            idx = {u: causes.index((base_state(u),)) for u in self.upstream}
            L = np.array(prior, float)
            for u in self.upstream:
                L[idx[u]] = 0.0
            L /= L.sum()
            J = np.zeros((self.n_states, len(causes)))
            J[0] = self.js.rho * L
            for k, u in enumerate(self.upstream, start=1):
                r = affect[k]
                J[k] = (1.0 - r) * self.js.rho * L
                J[k, idx[u]] = r
            self.causes.append(causes)
            self.L.append(L)
            self.J.append(J)
        self._rows: dict = {}
        self._views = [D.DataView(c.items, c.building, c.ctx) for c in cases]
        self.marg0 = self.marginals(self.initial())

    # ------------------------------------------------------------------------------------------ state and belief
    def initial(self) -> State:
        return State([np.ones(len(c)) for c in self.causes], {a: np.zeros(self.n_states) for a in self.groups})

    def group_stats(self, s: State, a: str) -> GroupStats:
        idx = self.groups[a]
        k = len(idx)
        Z = np.empty((k, self.n_states))
        A = []
        for t, i in enumerate(idx):
            Ai = self.J[i] * s.lik[i][None, :]
            A.append(Ai)
            Z[t] = Ai.sum(axis=1)
        logw = self.log_prior + (self.children[a] - k) * self.log_quiet + s.ahu_ll[a] + np.log(Z).sum(axis=0)
        W = np.exp(logw - logw.max())
        W /= W.sum()
        marg = [(W / Z[t]) @ A[t] for t in range(k)]
        return GroupStats(idx, W, Z, A, marg, float(sum(entropy_rows(m) for m in marg)))

    def all_stats(self, s: State) -> dict:
        return {a: self.group_stats(s, a) for a in self.groups}

    def marginals(self, s: State) -> list:
        out = [None] * self.n
        for a, g in self.all_stats(s).items():
            for t, i in enumerate(g.idx):
                out[i] = g.marg[t]
        return out

    def ahu_posterior(self, s: State) -> dict:
        return {a: g.W for a, g in self.all_stats(s).items()}

    def ahu_posterior_by_cause(self, s: State) -> dict:
        """The same posterior with severity levels of one cause added together: {air handler: {state name: probability}} over (ok, ahu_fan_off, low_static, *extra states), whatever `low_mix` is."""
        names = []
        for st in self.js.states:
            if base_state(st) not in names:
                names.append(base_state(st))
        out = {}
        for a, W in self.ahu_posterior(s).items():
            tot = dict.fromkeys(names, 0.0)
            for st, w in zip(self.js.states, W):
                tot[base_state(st)] += float(w)
            out[a] = tot
        return out

    # ------------------------------------------------------------------------------------------ what can be done
    def row(self, i: int, ck: K.CheckV1, target: str) -> np.ndarray:
        key = (i, ck.name, target)
        r = self._rows.get(key)
        if r is None:
            r = self._rows[key] = K.p_pos_row(ck, self.causes[i], target, self.cases[i].doc)
        return r

    def _eq(self, i: int, ck: K.CheckV1) -> str | None:
        c = self.cases[i]
        return {"box": c.doc, "ahu": c.ahu, "zone": c.member}[ck.subject]

    def place(self, i: int, ck: K.CheckV1, target: str) -> str:
        c = self.cases[i]
        return {"target": target, "box": c.doc, "room": c.member or "room", "ahu": c.ahu or "ahu", "bas": "bas"}[ck.place]

    def _avail(self, i: int, ck: K.CheckV1) -> D.Avail:
        return D.availability(ck, self._views[i], self._eq(i, ck))

    def options(self, s: State, stats: dict, tau: float, min_rate: float, min_gain: float = 1e-6) -> list[JOption]:
        """Every option worth its time (gain per minute at least `min_rate` x the number of unconcluded complaints it informs), with its expected gain."""
        out: list[JOption] = []
        for a, g in stats.items():
            live = [t for t, i in enumerate(g.idx) if g.marg[t].max() < tau or i not in s.informed]      # a diagnosis needs an observation: the pattern of complaints alone never concludes
            if not live:
                continue
            for t in live:
                i = g.idx[t]
                c = self.cases[i]
                items, rows = [], []
                for ck in c.checks:
                    if ck.subject == "ahu":
                        continue
                    av = self._avail(i, ck)
                    if av.state in ("unavailable", "askable"):
                        continue
                    for target in ([c.doc] if (ck.is_reading or ck.doc_only) else c.candidates):
                        if (i, ck.name, target) in s.done_c:
                            continue
                        pl = self.place(i, ck, target)
                        items.append((ck, target, pl, ck.minutes(s.at, pl, av.extra_min), av))
                        rows.append(self.row(i, ck, target))
                if items:
                    P = np.vstack(rows)
                    gains, pyes = self._gain_complaint(g, t, P)
                    for (ck, target, pl, mins, av), gn, py in zip(items, gains, pyes):
                        aud = len(live) if self.group_informing and bears_on_ahu(ck, self.upstream) else 1          # shown; the rate threshold of a room or box check stays min_rate (Addendum 30's)
                        if gn > min_gain and gn / mins >= min_rate:
                            out.append(JOption("complaint", i, ck, target, pl, mins, float(gn), float(py), aud, av))
            rep = g.idx[live[0]]
            rc = self.cases[rep]
            items, rows = [], []
            for ck in rc.checks:
                if ck.subject != "ahu" or (a, ck.name) in s.done_a:
                    continue
                av = self._avail(rep, ck)
                if av.state in ("unavailable", "askable"):
                    continue
                pl = self.place(rep, ck, a)
                items.append((ck, pl, ck.minutes(s.at, pl, av.extra_min), av))
                rows.append(ahu_row(ck, self.upstream))
            if items:
                gains, pyes = self._gain_ahu(g, np.vstack(rows))
                for (ck, pl, mins, av), gn, py in zip(items, gains, pyes):
                    if gn > min_gain and gn / mins >= min_rate * (len(live) if self.scale_audience else 1):
                        out.append(JOption("ahu", a, ck, a, pl, mins, float(gn), float(py), len(live), av))
        return out

    # ------------------------------------------------------------------------------------------ expected gains (vectorised over options)
    def _after(self, g: GroupStats, Wo: np.ndarray, skip: int | None = None) -> np.ndarray:
        """Summed entropy of the marginals of every complaint of the group except `skip`, for each row of the normalised state weights `Wo` (n_opt, 3)."""
        h = np.zeros(Wo.shape[0])
        for tj in range(len(g.idx)):
            if tj == skip:
                continue
            h += entropy_rows((Wo / g.Z[tj][None, :]) @ g.A[tj])
        return h

    def _gain_complaint(self, g: GroupStats, t: int, P: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """(expected gain in bits, P(positive)) of options on complaint g.idx[t] whose response rows are the rows of P (n_opt, n_causes)."""
        A, z, W, m = g.A[t], g.Z[t], g.W, g.marg[t]
        Zp, Zn = P @ A.T, (1.0 - P) @ A.T                                       # (n_opt, 3)
        tot, exp_h = 0.0, np.zeros(P.shape[0])
        pys = None
        for Zo, Po, pos in ((Zp, P, True), (Zn, 1.0 - P, False)):
            Wo = W[None, :] * Zo / z[None, :]
            prob = Wo.sum(axis=1)
            Wo = Wo / prob[:, None]
            mi = Po * m[None, :] / prob[:, None]
            h = entropy_rows(mi) + self._after(g, Wo, skip=t)
            exp_h += prob * h
            if pos:
                pys = prob
        return np.maximum(0.0, g.H - exp_h), pys

    def _gain_ahu(self, g: GroupStats, Q: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        exp_h = np.zeros(Q.shape[0])
        pys = None
        for Qo, pos in ((Q, True), (1.0 - Q, False)):
            Wo = g.W[None, :] * Qo
            prob = Wo.sum(axis=1)
            Wo = Wo / prob[:, None]
            exp_h += prob * self._after(g, Wo)
            if pos:
                pys = prob
        return np.maximum(0.0, g.H - exp_h), pys

    # ------------------------------------------------------------------------------------------ taking an observation
    def apply(self, s: State, o: JOption, positive: bool | None, minutes: float | None = None) -> State:
        """The state after `o` came back positive / negative. `positive=None`: unsure (the time is spent, nothing is learned)."""
        n = s.clone()
        mins = o.minutes if minutes is None else minutes
        n.elapsed += mins
        n.at = o.place
        n.n_checks += 1
        if o.kind == "complaint":
            n.done_c = s.done_c | {(o.who, o.check.name, o.target)}
            if positive is not None:
                r = self.row(o.who, o.check, o.target)
                lk = s.lik[o.who] * (r if positive else 1.0 - r)
                n.lik[o.who] = lk / lk.max()
                n.informed = s.informed | ({o.who} | set(self.groups[self.ahu[o.who]]) if self.group_informing and bears_on_ahu(o.check, self.upstream) else {o.who})
        else:
            n.done_a = s.done_a | {(o.who, o.check.name)}
            if positive is not None:
                q = ahu_row(o.check, self.upstream)
                n.ahu_ll = dict(s.ahu_ll)
                n.ahu_ll[o.who] = s.ahu_ll[o.who] + np.log(q if positive else 1.0 - q)
                n.informed = s.informed | set(self.groups[o.who])
        return n


def _score(o: JOption) -> tuple:
    return (round(o.gain / o.minutes, 12), -o.minutes, o.check.name, str(o.target), str(o.who))


class JointSession:
    """The loop: recommend one check for the whole visit, take the answer, update, repeat, until every complaint has a cause at `tau`, nothing is worth doing, or the check limit."""

    def __init__(self, cases: list[CaseV1], js: JointSettings | None = None, lookahead: int = 1, max_checks: int | None = None, group_informing: bool = False,
                 scale_audience: bool = True):
        if lookahead not in (1, 2):
            raise ValueError("lookahead must be 1 or 2")
        self.model = JointModel(cases, js, group_informing=group_informing, scale_audience=scale_audience)
        self.lookahead = lookahead
        s0 = cases[0].settings
        self.tau = s0.tau
        self.min_rate = cases[0].min_rate
        self.min_gain = s0.min_gain
        self.cap = max_checks if max_checks is not None else MAX_CHECKS_PER_COMPLAINT * len(cases)
        self.state = self.model.initial()
        self.log: list[tuple] = []                    # (kind, who, check name, target, outcome, minutes)
        self._pending: JOption | None = None

    # ------------------------------------------------------------------------------------------ belief
    @property
    def elapsed(self) -> float:
        return self.state.elapsed

    @property
    def n_checks(self) -> int:
        return self.state.n_checks

    def marginals(self) -> list:
        return self.model.marginals(self.state)

    def concluded(self) -> list[bool]:
        """Per complaint: the leading cause is at `tau` AND a real observation informs it."""
        return [bool(m.max() >= self.tau and i in self.state.informed) for i, m in enumerate(self.marginals())]

    # ------------------------------------------------------------------------------------------ the loop
    def _options(self, state: State) -> list[JOption]:
        return self.model.options(state, self.model.all_stats(state), self.tau, self.min_rate, self.min_gain)

    def _pick(self, opts: list[JOption]) -> JOption | None:
        if not opts:
            return None
        if self.lookahead == 1:
            return max(opts, key=_score)
        top = sorted(opts, key=_score, reverse=True)[:LOOKAHEAD_TOP]
        best, best_key = None, None
        for o in top:
            g, mins = self.two_step_value(o)
            key = (round(g / mins, 12),) + _score(o)[1:]
            if best_key is None or key > best_key:
                best, best_key = o, key
        return best

    def two_step_value(self, o: JOption) -> tuple[float, float]:
        """(expected gain, expected minutes) of doing `o` and then the best follow-up: the option's own gain and minutes plus, for each of its two outcomes weighted by its probability, the
        best one-step follow-up's gain and minutes (nothing when no follow-up is worth doing)."""
        g2, m2 = 0.0, 0.0
        for positive, prob in ((True, o.pyes), (False, 1.0 - o.pyes)):
            nxt = self._options(self.model.apply(self.state, o, positive))
            if nxt:
                f = max(nxt, key=_score)
                g2 += prob * f.gain
                m2 += prob * f.minutes
        return o.gain + g2, o.minutes + m2

    def recommend(self) -> JOption | None:
        """The next check for the visit, or None when every complaint is concluded, nothing left is worth its time, or the check limit is reached."""
        self._pending = None
        if self.state.n_checks >= self.cap:
            return None
        o = self._pick(self._options(self.state))
        self._pending = o
        return o

    def report(self, outcome: str, option: JOption | None = None) -> None:
        o = option or self._pending
        if o is None:
            raise RuntimeError("no pending recommendation: call recommend() first")
        ck = o.check
        if outcome in ("yes", "no") and ck.is_reading:
            outcome = ck.words[0] if outcome == "yes" else ck.words[1]
        if outcome not in (ck.words[0], ck.words[1], "unsure"):
            raise ValueError(f"{ck.name!r} is answered {ck.words[0]}/{ck.words[1]} or unsure, not {outcome!r}")
        positive = None if outcome == "unsure" else outcome == ck.words[0]
        self.state = self.model.apply(self.state, o, positive)
        self.log.append((o.kind, o.who, ck.name, o.target, outcome, o.minutes))
        self._pending = None

    # ------------------------------------------------------------------------------------------ reading it back
    def status(self) -> dict:
        marg = self.marginals()
        per = []
        for i, m in enumerate(marg):
            order = np.argsort(-m, kind="stable")
            ranked = [(self.model.causes[i][j], float(m[j])) for j in order]
            per.append(dict(room=self.model.cases[i].member, ranked=ranked, concluded=bool(ranked[0][1] >= self.tau and i in self.state.informed), guess=ranked[0][0]))
        opts = self._options(self.state) if self.state.n_checks < self.cap else []
        return dict(complaints=per, concluded=all(p["concluded"] for p in per), stalled=(not all(p["concluded"] for p in per)) and not opts, elapsed=self.elapsed,
                    n_checks=self.n_checks, ahu=self.model.ahu_posterior(self.state))
