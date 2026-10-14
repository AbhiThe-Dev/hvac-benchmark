"""One v1 call-out: the case (what is known and how much data there is), and the session (recommend a check, take the observation, update, repeat).

Differences from v0's session: the causes are the v1 tree (causes.py) and the checks the v1 catalogue (catalogue.py); a check is offered only if the data tier and the declared
context allow it, at the fallback cost if data is missing (data.py); the technician can declare a few facts, asked only when the best next check cannot be offered without them;
an observation is yes / no for the four v0 checks and abnormal / normal (or a number compared with an expected value) for the reading checks, plus unsure and skip;
and discrepancies found along the way are logged as structured events. `compat_v0=True` builds the v0-equivalent tree (two lumps, four checks), which reproduces v0's session exactly.
The belief is always recomputed from the prior and the log, so a declared fact or an added candidate re-scores everything already answered.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .. import model as M
from ..building import Equipment, candidates_for, id_ranks, id_weight
from . import catalogue as K
from . import causes as C
from . import data as D
from . import graded as G

DEFAULT_MIN_RATE = 0.003              # bits per minute: a check that is expected to sharpen the belief by less than this per minute is not worth its time (PLACEHOLDER; v1 only, 0 switches it off)
RELIABILITY_NOTE = ("The confidence figures assume every check reads as reliably as the catalogue's rates say; those rates are placeholders (only override_room's come from a simulation). "
                    "If the checks in your building are less reliable, the real confidence is lower (in v0's simulations, worse checks made the tool confidently wrong about three to four times as often; v1 has not been measured yet).")
GENERIC_BOX = "the box"                # the documented box at T0: whichever box the technician finds serving the room
AIRFLOW_VALUES = ("yes", "no", "unsure")
FEEL_VALUES = ("too_hot", "too_cold", "unsure")


@dataclass
class CaseV1:
    """One complaint. `tier` is a label ('T0' ... or 'custom'); what the tool may use is `items`. At T0 the building is not kept, so nothing about it can leak in."""
    tier: str
    items: frozenset
    building: D.Building1 | None
    member: str | None
    member_name: str
    doc: str
    ahu: str | None
    candidates: list[str]
    weights: dict[str, float]
    settings: M.Settings
    checks: tuple
    shares: dict
    airflow: str | None
    feel: str | None
    ctx: D.Context
    compat_v0: bool
    entries0: int
    min_rate: float = 0.0
    extra_causes: tuple = ()                        # Addendum 37: leaves beyond causes.CAUSES this case's prior should include, e.g. (causes.ECON_FAULT,); empty by default
    cache: dict = field(default_factory=dict)      # p_pos rows by (check, target, causes), shared by every session of this case (so `checks` must not change)
    graded: bool = False                            # use how far off a numeric reading is, not only normal / abnormal (graded.py; exploratory, off by default)

    @property
    def docs(self) -> bool:
        """Do we have the drawings' claims (so that 'the documented box is wrong' means something)?"""
        return "claims" in self.items and self.building is not None

    def label(self, eid: str) -> str:
        return self.building.label(eid) if self.building is not None else eid


def make_case_v1(building: D.Building1 | None, member: str | None = None, tier: str | frozenset | set = "T1", settings: M.Settings | None = None, airflow: str | None = None,
                 feel: str | None = None, context: D.Context | None = None, checks: tuple | None = None, shares: dict | None = None, max_candidates: int = 8,
                 compat_v0: bool = False, member_name: str | None = None, min_rate: float | None = None, extra_causes: tuple = (), graded: bool = False) -> CaseV1:
    """`tier` is a name ('T0' ... 'T4') or an explicit set of data items. At T1 and up `building` and `member` (a room with a documented box) are required; at T0 they are ignored
    except for the room's name."""
    s = settings or M.Settings()
    items = D.tier_items(tier)
    if "claims" in items and "equipment_list" not in items or "attributes" in items and "equipment_list" not in items:
        raise ValueError("claims and attributes are about the equipment on the list: a tier with them needs 'equipment_list'")
    label = tier if isinstance(tier, str) else "custom"
    if airflow is not None and airflow not in AIRFLOW_VALUES:
        raise ValueError(f"airflow must be one of {AIRFLOW_VALUES} or None")
    if feel is not None and feel not in FEEL_VALUES:
        raise ValueError(f"feel must be one of {FEEL_VALUES} or None")
    ctx = context or D.Context()
    if "claims" in items:
        if building is None:
            raise ValueError(f"tier {label} uses the drawings' claims: give a building")
        claims = building.base.claims.get("vav_zone", {})
        if member not in claims:
            raise ValueError(f"no documented vav_zone claim for {member!r}; choose from {sorted(claims)}")
        if building.base.equipment[member].kind != "Zone":
            raise ValueError(f"{member!r} is a {building.base.equipment[member].kind}, not a Zone")
        doc = claims[member]
        cands, w = candidates_for(building.base, "vav_zone", doc, max_candidates, s)
        ahu = building.base.claims.get("ahu_vav", {}).get(doc)
        name = member_name or building.label(member)
    else:
        if compat_v0:
            raise ValueError("compat_v0 reproduces v0, which needs the equipment list and the claims (tier T1 or above)")
        name = member_name or (building.label(member) if building is not None and member in building.base.equipment else member) or "this room"
        building, doc, cands, w, ahu = None, GENERIC_BOX, [GENERIC_BOX], {GENERIC_BOX: 1.0}, None
    if compat_v0:
        if feel is not None or context not in (None, D.Context()) or checks is not None:
            raise ValueError("compat_v0 takes no feel, context or custom checks: it is v0")
        checks = K.v0_menu()
    if min_rate is None:
        min_rate = 0.0 if compat_v0 else DEFAULT_MIN_RATE
    if min_rate < 0:
        raise ValueError("min_rate must be >= 0")
    entries0 = 1 + (airflow is not None) + (feel is not None) + sum(getattr(ctx, k) is not None for k in D.CONTEXT_KEYS)
    return CaseV1(label, items, building, member, name, doc, ahu, cands, w, s, checks if checks is not None else K.CATALOGUE, shares or C.DEFAULT_SHARES, airflow, feel, ctx,
                  compat_v0, entries0, min_rate, extra_causes, graded=graded)


# ---------------------------------------------------------------------------------------------- what the session hands back
@dataclass(frozen=True)
class OptionV1:
    check: K.CheckV1
    target: str
    minutes: float
    py: np.ndarray                     # P(positive | each cause)
    gain: float
    pyes: float                        # overall P(positive)
    avail: D.Avail


@dataclass(frozen=True)
class Recommendation:
    check: K.CheckV1
    target: str
    text: str
    minutes: float
    p_pos: float
    gain: float
    why: str
    avail: D.Avail

    @property
    def p_yes(self) -> float:          # v0's name for the same quantity
        return self.p_pos


@dataclass(frozen=True)
class Question:
    """A fact the technician is asked to declare, because the best next check cannot be offered without it."""
    key: str
    text: str
    why: str
    options: tuple = ("yes", "no")


@dataclass(frozen=True)
class Obs:
    check: str
    target: str
    outcome: str                       # the check's own word ("yes"/"no", "abnormal"/"normal") or "unsure" / "skip"
    minutes: float
    reading: float | None = None
    expected: float | None = None


@dataclass(frozen=True)
class Event:
    """A discrepancy between the documentation and what was found. `type`: documented_owner_wrong | undocumented_equipment | documented_attribute_mismatch."""
    type: str
    at_min: float
    n_checks: int
    data: dict


OUTCOMES = ("yes", "no", "abnormal", "normal", "unsure", "skip")


class Session:
    def __init__(self, case: CaseV1, strategy: str = "entropy", rng: np.random.Generator | None = None):
        if strategy not in M.STRATEGIES:
            raise ValueError(f"strategy must be one of {M.STRATEGIES}, not {strategy!r}")
        self.case = case
        self.strategy = strategy
        self.rng = rng if rng is not None else np.random.default_rng(0)
        self.candidates = list(case.candidates)
        self.weights = dict(case.weights)
        self.extra: dict[str, Equipment] = {}              # equipment the technician found that is not on the list
        self.ctx = case.ctx
        self.log: list[Obs] = []
        self.declared: list[tuple[str, str]] = []
        self.events: list[Event] = []
        self.elapsed = 0.0
        self.at: str | None = None
        self.entries = case.entries0
        self._pending: tuple[str, str] | None = None
        self._question: Question | None = None
        self._by_name = {c.name: c for c in case.checks}
        self._noted: set = set()

    # ------------------------------------------------------------------------------------------ small helpers
    @property
    def pending(self) -> tuple[str, str] | None:
        """(check name, target) of the recommendation awaiting an answer"""
        return self._pending

    @property
    def pending_question(self) -> "Question | None":
        """The question awaiting a `declare`, if `next_step` last returned one"""
        return self._question

    def view(self) -> D.DataView:
        return D.DataView(self.case.items, self.case.building, self.ctx)

    def label(self, eid: str) -> str:
        return self.extra[eid].label if eid in self.extra else self.case.label(eid)

    def _check(self, name: str) -> K.CheckV1:
        try:
            return self._by_name[name]
        except KeyError:
            raise KeyError(f"no check {name!r} in this case's catalogue") from None

    def _eq(self, ck: K.CheckV1) -> str | None:
        """The equipment whose attributes and point names the check uses (None when unknown)."""
        c = self.case
        return {"box": c.doc if c.docs else None, "ahu": c.ahu, "zone": c.member if c.docs else None}[ck.subject]

    def _place(self, ck: K.CheckV1, target: str) -> str:
        c = self.case
        return {"target": target, "box": c.doc, "room": c.member or "room", "ahu": c.ahu or "ahu", "bas": "bas"}[ck.place]

    def _box_phrase(self, target: str) -> str:
        return f"box {self.label(target)}" if self.case.docs else f"the box serving {self.case.member_name}"

    def _row(self, ck: K.CheckV1, target: str, causes: list[tuple]) -> np.ndarray:
        key = (ck.name, target, tuple(causes))
        row = self.case.cache.get(key)
        if row is None:
            row = self.case.cache[key] = K.p_pos_row(ck, causes, target, self.case.doc)
        return row

    # ------------------------------------------------------------------------------------------ belief
    def _prior(self) -> tuple[list[tuple], np.ndarray]:
        c = self.case
        if c.compat_v0:
            return M.make_prior("vav_zone", self.candidates, c.doc, c.settings, c.airflow, self.weights)
        v = self.view()
        eq = c.doc if c.docs else None
        return C.make_prior_v1(self.candidates, c.doc, c.settings, docs=c.docs, airflow=c.airflow, feel=c.feel, weights=self.weights, shares=c.shares,
                               reheat=v.have("feature:reheat", eq) is not False, pressure_independent=bool(v.have("feature:pressure_independent", eq)), extra_causes=c.extra_causes)

    def posterior(self) -> tuple[list[tuple], np.ndarray]:
        causes, post = self._prior()
        for o in self.log:
            ck = self._check(o.check)
            if o.outcome in ck.words:
                row = self._row(ck, o.target, causes)
                z = self._z(ck, o) if self.case.graded else None
                post = G.update(post, z, row, ck.bg) if z is not None else M.update(post, row, "yes" if o.outcome == ck.words[0] else "no")
        return causes, post

    def _z(self, ck: K.CheckV1, o: Obs) -> float | None:
        """How many tolerances off the number the technician entered is, or None when there is no number or no two-sided band to compare it with (graded.py)."""
        if o.reading is None or ck.reading is None:
            return None
        return G.z_of(o.reading, ck.reading.band(self._attrs(self._eq(ck)), o.expected))

    def _options(self, causes: list[tuple], post: np.ndarray) -> list[OptionV1]:
        c, view = self.case, self.view()
        done = {(o.check, o.target) for o in self.log}
        out = []
        for ck in c.checks:
            av = D.availability(ck, view, self._eq(ck))
            if av.state == "unavailable":
                continue
            for t in ([c.doc] if (ck.is_reading or ck.doc_only) else self.candidates):
                if (ck.name, t) in done:
                    continue
                row = self._row(ck, t, causes)
                gain, pyes = M.expected_gain(post, row)
                out.append(OptionV1(ck, t, ck.minutes(self.at, self._place(ck, t), av.extra_min), row, gain, pyes, av))
        return out

    # ------------------------------------------------------------------------------------------ the loop
    def _choose(self, opts: list[OptionV1]) -> OptionV1 | None:
        """The strategy's pick among the options worth their time (expected gain per minute at least `case.min_rate`)."""
        r = self.case.min_rate
        return M.select(self.strategy, [o for o in opts if o.gain / o.minutes >= r] if r > 0 else opts, self.case.settings.min_gain, self.rng)

    def _best(self, allow_ask: bool) -> tuple[OptionV1 | None, bool]:
        """(the best option, concluded). With allow_ask=False options that need a declaration first are left out."""
        causes, post = self.posterior()
        self._pending = self._question = None
        if post.max() >= self.case.settings.tau:
            return None, True
        opts = self._options(causes, post)
        if not allow_ask:
            opts = [o for o in opts if o.avail.state != "askable"]
        return self._choose(opts), False

    def _recommendation(self, o: OptionV1) -> Recommendation:
        c, ck = self.case, o.check
        pt = None
        if ck.point is not None and self.view().have("point_map", self._eq(ck)):
            pt = self.case.building.point(self._eq(ck), ck.point)
        text = ck.describe(self._box_phrase(o.target), self.label(o.target), c.member_name, self.label(c.ahu) if c.ahu else "the air handler serving it")
        if pt:
            text += f" (control-system point: {pt})"
        spec = ck.reading
        if spec is not None:
            attrs = self._attrs(self._eq(ck))
            text += f" [{spec.describe(attrs)}]"
        word = ck.words[0]
        why = f"about {o.pyes:.0%} likely to come back {word}; expected to sharpen the picture by {o.gain:.2f} bits for {o.minutes:.0f} minutes"
        if o.avail.extra_min:
            why += f" (includes {o.avail.extra_min:.0f} extra minutes because some data is not on file)"
        return Recommendation(ck, o.target, text, o.minutes, o.pyes, o.gain, why, o.avail)

    def recommend(self) -> Recommendation | None:
        """The next check that can be offered as things stand, or None when a cause has reached `tau` or nothing left would change the belief. Never asks the technician anything."""
        o, _ = self._best(False)
        if o is None:
            return None
        self._pending = (o.check.name, o.target)
        return self._recommendation(o)

    def next_step(self) -> Recommendation | Question | None:
        """What to do next: a check, or a `Question` when the best check cannot be offered until the technician declares something (answer it with `declare`), or None when done."""
        o, _ = self._best(True)
        if o is None:
            return None
        if o.avail.state == "askable":
            key = o.avail.ask[0]
            self._question = Question(key, D.QUESTIONS[key], f"needed before '{o.check.name}', which is the most useful check right now")
            return self._question
        self._pending = (o.check.name, o.target)
        return self._recommendation(o)

    # ------------------------------------------------------------------------------------------ what the technician tells us
    def declare(self, key: str, value: str) -> None:
        """Record a declared fact ('yes' / 'no'). One entry. A declared reheat that contradicts the documented attribute is logged as a discrepancy."""
        if value not in ("yes", "no"):
            raise ValueError("declare 'yes' or 'no'")
        documented = self.view().attr("reheat", self.case.doc if self.case.docs else None) if key == "reheat" else None
        self.ctx = self.ctx.declare(key, value)
        self.declared.append((key, value))
        self.entries += 1
        self._pending = self._question = None
        if documented is not None and (documented != "none") != (value == "yes"):
            self._event("documented_attribute_mismatch", dict(equipment=self.case.doc, attribute="reheat", documented=documented, found=value))

    def _attrs(self, eq: str | None) -> dict:
        v = self.view()
        return v.building.attrs.get(eq, {}) if "attributes" in v.items and v.building is not None and eq is not None else {}

    def _event(self, type_: str, data: dict) -> None:
        self.events.append(Event(type_, self.elapsed, sum(1 for o in self.log if o.outcome != "skip"), data))

    def _canonical(self, ck: K.CheckV1, outcome: str, reading: float | None, expected: float | None) -> tuple[str, float | None]:
        if reading is not None:
            if ck.reading is None:
                raise ValueError(f"{ck.name!r} takes no numeric reading")
            derived = ck.reading.classify(reading, self._attrs(self._eq(ck)), expected)
            if outcome is not None and outcome not in ("unsure", "skip") and self._word(ck, outcome) != derived:
                raise ValueError(f"reading {reading} is {derived} against its expected value, not {outcome!r}")
            return derived, reading
        if outcome is None:
            raise ValueError("give an outcome, or a numeric reading")
        return self._word(ck, outcome), None

    @staticmethod
    def _word(ck: K.CheckV1, outcome: str) -> str:
        if outcome not in OUTCOMES:
            raise ValueError(f"outcome must be one of {OUTCOMES}, not {outcome!r}")
        if outcome in ("unsure", "skip") or outcome in ck.words:
            return outcome
        if ck.is_reading and outcome in ("yes", "no"):       # the question of a reading check is 'is it abnormal?'
            return ck.words[0] if outcome == "yes" else ck.words[1]
        raise ValueError(f"{ck.name!r} is answered {ck.words[0]}/{ck.words[1]}, not {outcome!r}")

    def report(self, outcome: str | None = None, check: str | None = None, target: str | None = None, *, reading: float | None = None, expected: float | None = None) -> None:
        """Record the answer to the pending recommendation, or to any check the technician chose to do instead (`check=`, `target=`; `target` defaults to the documented box).
        A reading check may be answered with a number (`reading=`, optionally `expected=`): it is compared with the expected value and recorded as normal or abnormal."""
        if check is None:
            if self._pending is None:
                raise RuntimeError("no pending recommendation: call recommend() or next_step() first, or pass check= (and target=)")
            check, target = self._pending
        ck = self._check(check)
        target = self.case.doc if target is None else target
        ok = target == self.case.doc if (ck.is_reading or ck.doc_only) else target in self.candidates
        if not ok:
            raise ValueError(f"{check!r} cannot be done on {target!r}")
        if any((o.check, o.target) == (check, target) for o in self.log):
            raise ValueError(f"{check!r} on {target!r} is already recorded")
        word, value = self._canonical(ck, outcome, reading, expected)
        eq = self._eq(ck)
        av = D.availability(ck, self.view(), eq)
        minutes = 0.0 if word == "skip" else ck.minutes(self.at, self._place(ck, target), av.extra_min)
        self.log.append(Obs(check, target, word, minutes, value, expected))
        if word != "skip":
            self.elapsed += minutes
            self.at = self._place(ck, target)
        self.entries += 1
        self._pending = None
        if value is not None and expected is not None and ck.reading.expected_attr:
            doc_val = self._attrs(eq).get(ck.reading.expected_attr)
            if doc_val is not None and ck.reading.classify(expected, {}, doc_val) == "abnormal":
                self._event("documented_attribute_mismatch", dict(equipment=eq, attribute=ck.reading.expected_attr, documented=doc_val, found=expected))
        self._note_conclusion()

    def _note_conclusion(self) -> None:
        causes, post = self.posterior()
        i = int(np.argmax(post))
        cause = causes[i]
        if post[i] >= self.case.settings.tau and cause[0] in ("wrong", "unlisted") and cause not in self._noted:
            self._noted.add(cause)
            found = cause[1] if cause[0] == "wrong" else None
            self._event("documented_owner_wrong", dict(member=self.case.member, documented=self.case.doc, found=found, belief=float(post[i]), basis="tool conclusion"))

    def add_candidate(self, equipment_id: str) -> None:
        """The technician found another piece of equipment on the list that could feed it. Everything already answered is re-scored with it in the picture."""
        c = self.case
        if not c.docs:
            raise ValueError("there is no equipment list at this tier: use add_equipment for a box you found")
        eq = c.building.base.equipment.get(equipment_id)
        if eq is None:
            raise KeyError(f"{equipment_id!r} is not in the equipment list; if it is real but undocumented use add_equipment")
        if eq.kind != M.SLOT_OWNER_KIND["vav_zone"]:
            raise ValueError(f"{equipment_id!r} is a {eq.kind}; this question needs a {M.SLOT_OWNER_KIND['vav_zone']}")
        if equipment_id in self.candidates:
            raise ValueError(f"{equipment_id!r} is already a candidate")
        area = c.building.base.equipment[c.doc].area
        self.candidates.append(equipment_id)
        if c.settings.nearness == "id":
            rk = id_ranks(c.building.base, M.SLOT_OWNER_KIND["vav_zone"])
            self.weights[equipment_id] = id_weight(rk[c.doc], rk[equipment_id], c.settings.id_decay)
        else:
            self.weights[equipment_id] = 1.0 if (area is None or eq.area == area) else c.settings.other_area_weight
        self.entries += 1
        self._pending = None

    def add_equipment(self, equipment_id: str, area: str | None = None, tag: str | None = None) -> None:
        """The technician found a box that is not on the equipment list at all. It becomes a candidate (weight 1: it was seen near the room) and a discrepancy is logged."""
        c = self.case
        if not c.docs:
            raise ValueError("there is no equipment list at this tier, so nothing can be undocumented")
        if equipment_id in c.building.base.equipment or equipment_id in self.extra:
            raise ValueError(f"{equipment_id!r} is already known: use add_candidate")
        self.extra[equipment_id] = Equipment(equipment_id, "VAV", area, tag)
        self.candidates.append(equipment_id)
        self.weights[equipment_id] = 1.0
        self.entries += 1
        self._pending = None
        self._event("undocumented_equipment", dict(id=equipment_id, kind="VAV", area=area, tag=tag, added_by="technician"))

    # ------------------------------------------------------------------------------------------ reading it back
    def describe(self, cause: tuple) -> str:
        c, tag = self.case, cause[0]
        doc = self.label(c.doc)
        if tag == "wrong":
            return f"The drawings say {doc} serves {c.member_name}, but it is fed by {self.label(cause[1])}. Start a new diagnosis on {self.label(cause[1])}."
        if tag == "unlisted":
            return "None of the listed boxes serves it: something not on the list does (or the layout is not the problem)."
        if tag in C.ALL_BY_ID:
            return f"{C.ALL_BY_ID[tag].label}: {C.ALL_BY_ID[tag].detail}."
        if tag == C.ACTS_FAIL:
            return f"{doc} feeds it but does not act when commanded: check its actuator, power, signal and damper."
        if tag == C.OTHER:
            return f"{doc} feeds it and acts, so this is not a layout or actuation problem: look at setpoint, sensor or capacity (outside this tool's scope)."
        raise ValueError(cause)

    def status(self) -> dict:
        causes, post = self.posterior()
        order = np.argsort(-post, kind="stable")
        ranked = [(causes[i], float(post[i])) for i in order]
        concluded = ranked[0][1] >= self.case.settings.tau
        stalled = (not concluded) and self._choose(self._options(causes, post)) is None
        return dict(ranked=ranked, concluded=concluded, conclusion=self.describe(ranked[0][0]) if concluded else None, stalled=stalled, elapsed=self.elapsed,
                    n_checks=sum(1 for o in self.log if o.outcome != "skip"), entries=self.entries, at=self.at, events=list(self.events), declared=list(self.declared))

    def shortlist(self, k: int = 2) -> dict:
        """What to say when the picture is not settled: the `k` leading causes with their probabilities, and the one check that would sharpen it most per minute WITHOUT the worth-its-time bar
        (`min_rate`) that decides when the tool stops on its own: 'most likely A or B; to be sure, do C' instead of a lone best guess. Changes nothing (no check is recommended, no belief, log or
        clock moves). `next` is a Recommendation, or None when no available check would change the belief."""
        causes, post = self.posterior()
        order = np.argsort(-post, kind="stable")[:k]
        cands = [(causes[i], float(post[i])) for i in order]
        opts = [o for o in self._options(causes, post) if o.gain > self.case.settings.min_gain and o.avail.state != "askable"]
        best = max(opts, key=lambda o: (round(o.gain / o.minutes, 12), -o.minutes, o.check.name, str(o.target))) if opts else None
        return dict(candidates=cands, mass=float(sum(p for _, p in cands)), next=self._recommendation(best) if best is not None else None)

    def export(self) -> dict:
        """The session as plain data (JSON-serialisable): for the technician's report and for later analysis."""
        st = self.status()
        c = self.case
        return dict(tier=c.tier, member=c.member, member_name=self.case.member_name, documented_box=self.case.doc, airflow=self.case.airflow, feel=self.case.feel,
                    declared=[list(d) for d in self.declared], checks=[dict(check=o.check, target=o.target, outcome=o.outcome, minutes=o.minutes, reading=o.reading, expected=o.expected) for o in self.log],
                    events=[dict(type=e.type, at_min=e.at_min, n_checks=e.n_checks, data=e.data) for e in self.events], concluded=st["concluded"], conclusion=st["conclusion"],
                    ranked=[[list(cause), p] for cause, p in st["ranked"][:5]], elapsed=st["elapsed"], entries=st["entries"], assumptions=self.assumptions())

    def assumptions(self) -> dict:
        """What the numbers in this session rest on, so that a report carries it. The reliability of the checks is the number the results are most sensitive to."""
        c = self.case
        return dict(check_reliability=RELIABILITY_NOTE, tau=c.settings.tau, min_rate_bits_per_min=c.min_rate, p_wrong=c.settings.p_wrong, p_acts_fail=c.settings.p_acts_fail,
                    minutes="placeholders", cause_shares="placeholders", validated_on_real_call_outs=False)
