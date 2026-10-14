"""Technician-guided troubleshooting, working model v0: causes, checks, priors, Bayes update and check selection. No trend data is used.

One complaint at a time: "the thing at `member` (a room, or a box) is not being fed the way the drawings say". The hypotheses are the possible causes:
  ("wrong", j)         the documented feeder is not the feeder; candidate j is
  ("unlisted",)        something not on the candidate list feeds it
  ("doc_acts_fail",)   `vav_zone` only: the documented box feeds the room but does not act when commanded (damper / actuator)
  ("doc_other",)       `vav_zone`: the documented box feeds the room and acts; the cause is elsewhere (setpoint, sensor, capacity: outside v0)
  ("doc_ok",)          `ahu_vav`: the documented air handler feeds the box
A check is a yes/no observation at a named place ("command box 2-05 to full cooling: does the room respond?"). Each has a hit rate (tpr), a false-alarm rate (fpr) and a time in
minutes (access to the place + doing it + waiting). The tool picks, by a chosen strategy, the check that tells the most per minute, updates the belief on the technician's answer,
and stops when one cause reaches `tau`.

EVERY NUMBER HERE THAT IS NOT MARKED OTHERWISE IS A PLACEHOLDER (priors, minutes, most hit rates). They are settings on purpose: the interviews are meant to replace them.
Only the `override_room` hit rates come from a measurement (simulation, PREREGISTRATION_DR.md Addendum 16).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np

EPS = 1e-9
RATE_FLOOR = 1e-4            # rates are clipped into [floor, 1 - floor] so one wrong answer never makes a cause impossible
PRIOR_FLOOR = 1e-6
Cause = tuple

SLOT_OWNER_KIND = {"vav_zone": "VAV", "ahu_vav": "AHU"}
SLOT_MEMBER_KIND = {"vav_zone": "Zone", "ahu_vav": "VAV"}
SLOT_DOC_RIGHT = {"vav_zone": (("doc_other",), ("doc_acts_fail",)), "ahu_vav": (("doc_ok",),)}


@dataclass(frozen=True)
class CheckType:
    name: str
    kind: str                     # "act_observe": act on candidate j, watch the member | "trace": follow the path from the member | "acts": does the documented box move at all
    text: str                     # {t} = target, {m} = the member's name
    tpr: float                    # P(yes | the check's premise is true)
    fpr: float                    # P(yes | it is not)
    access_min: float             # getting to the place (0 when the technician is already there)
    do_min: float
    wait_min: float               # waiting for the effect to show
    source: str = "ASSUMED placeholder"
    doc_only: bool = False        # offered on the documented equipment only

    def minutes(self, at: str | None, target: str) -> float:
        return (0.0 if at == target else self.access_min) + self.do_min + self.wait_min

    def describe(self, target: str, member: str) -> str:
        return self.text.format(t=target, m=member)


MENUS: dict[str, tuple[CheckType, ...]] = {
    "vav_zone": (
        CheckType("override_room", "act_observe", "Command box {t} to full cooling and watch whether the temperature in {m} responds", 0.98, 0.03, 6, 2, 30,
                  "rates measured in simulation (Addendum 16, 30+ minute window); minutes ASSUMED"),
        CheckType("override_diffuser", "act_observe", "Command box {t} to full cooling and check whether airflow at {m}'s diffuser rises", 0.90, 0.10, 6, 2, 3),
        CheckType("duct_trace", "trace", "Trace the duct from {m}'s diffuser back to its box: is it {t}?", 0.98, 0.02, 10, 15, 0,
                  "rates from active/physical.py (assumed there too); minutes ASSUMED"),
        CheckType("confirm_acts", "acts", "Command box {t} and confirm its damper actually moves", 0.95, 0.05, 6, 3, 0, doc_only=True),
    ),
    "ahu_vav": (
        CheckType("shutdown_watch", "act_observe", "Drop air handler {t}'s fan speed (or stop it) and check whether airflow at {m} falls", 0.95, 0.05, 15, 5, 5),
        CheckType("duct_trace", "trace", "Trace the duct from {m} back toward its air handler: is it {t}?", 0.95, 0.05, 10, 20, 0),
    ),
}


# The technician's one-word rating of a building's drawings -> the prior that a documented feeder is wrong. ASSUMED placeholder levels (not measurements); "mixed" is the default
# `Settings.p_wrong`, so leaving the rating unset changes nothing (PREREGISTRATION_DR.md Addendum 21).
DRAWINGS = {"mostly_right": 0.05, "mixed": 0.15, "poor": 0.30}


@dataclass(frozen=True)
class Settings:
    """Everything adjustable. Defaults are placeholders, not findings."""
    p_wrong: float = 0.15                  # prior that the documented feeder is wrong
    unlisted_share: float = 0.10           # share of `p_wrong` that is equipment not on the list
    p_acts_fail: float = 0.15              # `vav_zone`: prior that the documented box feeds the room but does not act
    no_airflow_multiplier: float = 3.0     # symptom "no air at the diffuser": multiplies (yes: divides) the acts-fail weight before normalising
    other_area_weight: float = 0.25        # nearness prior: a candidate outside the documented box's area counts this much of one inside it
    tau: float = 0.95                      # conclude when one cause reaches this
    min_gain: float = 1e-6                 # a check that would change the belief by less than this (bits) is not offered
    nearness: str = "area"                 # how candidates are ranked and weighted: "area" (same area as the documented feeder first; `other_area_weight`) | "id" (nearest in natural id order first)
    id_decay: float = 4.0                  # nearness = "id": a candidate k places away in id order counts exp(-k / id_decay) of the documented one (PLACEHOLDER, Addendum 25)
    menus: dict = field(default_factory=lambda: dict(MENUS))

    def __post_init__(self):
        if not (0 <= self.p_wrong <= 1 and 0 <= self.p_acts_fail <= 1 and self.p_wrong + self.p_acts_fail <= 1):
            raise ValueError("p_wrong and p_acts_fail must be probabilities that sum to at most 1")
        if not 0 < self.tau < 1:
            raise ValueError("tau must be in (0, 1)")
        if self.nearness not in ("area", "id"):
            raise ValueError("nearness must be 'area' or 'id'")
        if not self.id_decay > 0:
            raise ValueError("id_decay must be positive")

    def menu(self, slot: str) -> tuple[CheckType, ...]:
        return self.menus[slot]

    def with_drawings(self, level: str) -> "Settings":
        """A copy whose prior that the documented feeder is wrong is the level's: `mostly_right`, `mixed` (the default) or `poor`. Nothing else changes."""
        if level not in DRAWINGS:
            raise ValueError(f"drawings rating {level!r} is not one of {sorted(DRAWINGS)}")
        return replace(self, p_wrong=DRAWINGS[level])

    def with_check(self, slot: str, name: str, **changes) -> "Settings":
        """A copy with one check's numbers changed, e.g. `s.with_check("vav_zone", "duct_trace", access_min=3)`."""
        menu = tuple(replace(c, **changes) if c.name == name else c for c in self.menus[slot])
        if menu == self.menus[slot]:
            raise KeyError(f"no check {name!r} in the {slot!r} menu")
        return replace(self, menus={**self.menus, slot: menu})


# ---------------------------------------------------------------------------------------------- causes and priors
def make_prior(slot: str, candidates: list[str], doc: str, settings: Settings, airflow: str | None = None,
               weights: dict | None = None) -> tuple[list[Cause], np.ndarray]:
    """Cause list and prior. `candidates` includes `doc`; `weights` = nearness weight per candidate; `airflow` in {"yes", "no", "unsure", None} = is air coming out of the diffuser."""
    wrong = [c for c in candidates if c != doc]
    w = np.array([(weights or {}).get(c, 1.0) for c in wrong], float)
    p_unlisted = settings.p_wrong * settings.unlisted_share if wrong else settings.p_wrong
    listed = (settings.p_wrong - p_unlisted) * (w / w.sum() if len(w) else w)
    if slot == "vav_zone":
        act = settings.p_acts_fail * (settings.no_airflow_multiplier if airflow == "no" else 1.0 / settings.no_airflow_multiplier if airflow == "yes" else 1.0)
        raw = [1.0 - settings.p_wrong - settings.p_acts_fail, act]
    elif slot == "ahu_vav":
        raw = [1.0 - settings.p_wrong]
    else:
        raise ValueError(f"unsupported slot {slot!r}")
    causes = list(SLOT_DOC_RIGHT[slot]) + [("wrong", c) for c in wrong] + [("unlisted",)]
    p = np.maximum(np.array(raw + list(listed) + [p_unlisted], float), PRIOR_FLOOR)
    return causes, p / p.sum()


def truth(slot: str, kind: str, target: str, cause: Cause, doc: str) -> bool:
    """Would a perfect check of this kind on `target` say yes if `cause` were the truth?"""
    tag = cause[0]
    if slot == "vav_zone":
        if kind == "act_observe":        # command box `target`, watch the room: responds only if that box feeds it and acts
            return (tag == "wrong" and cause[1] == target) or (tag == "doc_other" and target == doc)
        if kind == "trace":              # the room's duct leads to `target`
            return (tag == "wrong" and cause[1] == target) or (tag in ("doc_other", "doc_acts_fail") and target == doc)
        if kind == "acts":               # only the documented box's actuation is a hypothesis
            return tag != "doc_acts_fail"
    if slot == "ahu_vav":
        if kind in ("act_observe", "trace"):
            return (tag == "wrong" and cause[1] == target) or (tag == "doc_ok" and target == doc)
    raise ValueError(f"no truth rule for slot={slot!r}, kind={kind!r}")


def p_yes(slot: str, check: CheckType, target: str, causes: list[Cause], doc: str, rates: CheckType | None = None) -> np.ndarray:
    """P(the technician reports yes | each cause). `rates` lets a simulator use the TRUE hit rates while the tool uses its own."""
    r = rates or check
    t = np.array([truth(slot, check.kind, target, c, doc) for c in causes])
    return np.clip(np.where(t, r.tpr, r.fpr), RATE_FLOOR, 1.0 - RATE_FLOOR)


# ---------------------------------------------------------------------------------------------- belief update and selection
def update(post: np.ndarray, py: np.ndarray, outcome: str) -> np.ndarray:
    like = py if outcome == "yes" else 1.0 - py
    p = post * like
    s = p.sum()
    return p / s if s > 0 else post


def entropy(p: np.ndarray) -> float:
    q = p[p > 0]
    return float(-(q * np.log2(q)).sum())


def expected_gain(post: np.ndarray, py: np.ndarray) -> tuple[float, float]:
    """(expected reduction in the entropy of the belief over causes, in bits; overall probability the answer is yes)"""
    pyes = float(post @ py)
    h = 0.0
    if pyes > EPS:
        h += pyes * entropy(post * py / pyes)
    if 1.0 - pyes > EPS:
        h += (1.0 - pyes) * entropy(post * (1.0 - py) / (1.0 - pyes))
    return max(0.0, entropy(post) - h), pyes


@dataclass(frozen=True)
class Option:
    check: CheckType
    target: str
    minutes: float
    py: np.ndarray
    gain: float
    pyes: float


STRATEGIES = ("entropy", "split_half", "random")


def select(strategy: str, options: list[Option], min_gain: float = 1e-6, rng: np.random.Generator | None = None) -> Option | None:
    """entropy: most expected information per minute (the standard one-step rule) | split_half: the check whose answer is closest to a coin flip, per minute (does not trust the
    prior as much: the safer choice when the prior is weak) | random: any informative check (a reference)."""
    live = [o for o in options if o.gain > min_gain]
    if not live:
        return None
    if strategy == "random":
        return live[int((rng or np.random.default_rng(0)).integers(len(live)))]
    if strategy == "entropy":
        score = lambda o: o.gain / o.minutes  # noqa: E731
    elif strategy == "split_half":
        score = lambda o: (1.0 - abs(2.0 * o.pyes - 1.0)) / o.minutes  # noqa: E731
    else:
        raise ValueError(f"strategy must be one of {STRATEGIES}, not {strategy!r}")
    return max(live, key=lambda o: (round(score(o), 12), -o.minutes, o.check.name, o.target))
