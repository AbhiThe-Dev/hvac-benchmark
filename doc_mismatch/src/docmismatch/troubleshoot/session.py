"""One troubleshooting session: recommend a check, take the technician's answer, update, repeat until one cause reaches `tau` or nothing more would help.

The belief is always recomputed from the prior and the log of answers, so adding a piece of equipment the technician finds (`add_candidate`) re-scores everything already done.
Answers: "yes" / "no" (evidence), "unsure" (the check was done and took the time, but tells us nothing), "skip" (not done: no time, no evidence, not offered again).
`entries` counts what the technician typed or tapped, so the input burden is measurable.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import model as M
from .building import Case, id_ranks, id_weight

OUTCOMES = ("yes", "no", "unsure", "skip")


@dataclass(frozen=True)
class Recommendation:
    check: M.CheckType
    target: str
    text: str
    minutes: float
    p_yes: float
    gain: float
    why: str


class Session:
    def __init__(self, case: Case, strategy: str = "entropy", rng: np.random.Generator | None = None):
        if strategy not in M.STRATEGIES:
            raise ValueError(f"strategy must be one of {M.STRATEGIES}, not {strategy!r}")
        self.case = case
        self.strategy = strategy
        self.rng = rng if rng is not None else np.random.default_rng(0)
        self.log: list[tuple[str, str, str]] = []          # (check name, target, outcome)
        self.elapsed = 0.0
        self.at: str | None = None                         # where the technician is (the last place a check was done)
        self.entries = case.entries0
        self._pending: tuple[str, str] | None = None

    @property
    def pending(self) -> tuple[str, str] | None:
        """(check name, target) of the recommendation awaiting an answer"""
        return self._pending

    # ------------------------------------------------------------------------------------------ belief
    def _menu(self) -> tuple[M.CheckType, ...]:
        return self.case.settings.menu(self.case.slot)

    def _check(self, name: str) -> M.CheckType:
        for c in self._menu():
            if c.name == name:
                return c
        raise KeyError(f"no check {name!r} for slot {self.case.slot!r}")

    def posterior(self) -> tuple[list[M.Cause], np.ndarray]:
        c = self.case
        causes, post = M.make_prior(c.slot, c.candidates, c.doc, c.settings, c.airflow, c.weights)
        for name, target, outcome in self.log:
            if outcome in ("yes", "no"):
                post = M.update(post, M.p_yes(c.slot, self._check(name), target, causes, c.doc), outcome)
        return causes, post

    def _options(self, causes: list[M.Cause], post: np.ndarray) -> list[M.Option]:
        c = self.case
        done = {(n, t) for n, t, _ in self.log}
        out = []
        for ck in self._menu():
            for t in ([c.doc] if ck.doc_only else c.candidates):
                if (ck.name, t) in done:
                    continue
                py = M.p_yes(c.slot, ck, t, causes, c.doc)
                gain, pyes = M.expected_gain(post, py)
                out.append(M.Option(ck, t, ck.minutes(self.at, t), py, gain, pyes))
        return out

    # ------------------------------------------------------------------------------------------ the loop
    def recommend(self) -> Recommendation | None:
        """The next check, or None when a cause has reached `tau` or no remaining check would change the belief."""
        causes, post = self.posterior()
        self._pending = None
        if post.max() >= self.case.settings.tau:
            return None
        opt = M.select(self.strategy, self._options(causes, post), self.case.settings.min_gain, self.rng)
        if opt is None:
            return None
        self._pending = (opt.check.name, opt.target)
        why = f"about {opt.pyes:.0%} likely to come back yes; expected to sharpen the picture by {opt.gain:.2f} bits for {opt.minutes:.0f} minutes"
        return Recommendation(opt.check, opt.target, opt.check.describe(self.case.building.label(opt.target), self.case.member_name), opt.minutes, opt.pyes, opt.gain, why)

    def report(self, outcome: str, check: str | None = None, target: str | None = None) -> None:
        """Record the answer to the pending recommendation, or to any check the technician chose to do instead (`check=`, `target=`)."""
        if outcome not in OUTCOMES:
            raise ValueError(f"outcome must be one of {OUTCOMES}, not {outcome!r}")
        if check is None:
            if self._pending is None:
                raise RuntimeError("no pending recommendation: call recommend() first, or pass check= and target=")
            check, target = self._pending
        ck = self._check(check)
        if target not in self.case.candidates or (ck.doc_only and target != self.case.doc):
            raise ValueError(f"{check!r} cannot be done on {target!r}")
        if any((n, t) == (check, target) for n, t, _ in self.log):
            raise ValueError(f"{check!r} on {target!r} is already recorded")
        self.log.append((check, target, outcome))
        if outcome != "skip":
            self.elapsed += ck.minutes(self.at, target)
            self.at = target
        self.entries += 1
        self._pending = None

    def add_candidate(self, equipment_id: str) -> None:
        """The technician found another piece of equipment that could feed it. Everything already answered is re-scored with it in the picture."""
        c = self.case
        eq = c.building.equipment.get(equipment_id)
        if eq is None:
            raise KeyError(f"{equipment_id!r} is not in the equipment list")
        if eq.kind != M.SLOT_OWNER_KIND[c.slot]:
            raise ValueError(f"{equipment_id!r} is a {eq.kind}; this question needs a {M.SLOT_OWNER_KIND[c.slot]}")
        if equipment_id in c.candidates:
            raise ValueError(f"{equipment_id!r} is already a candidate")
        area = c.building.equipment[c.doc].area
        c.candidates.append(equipment_id)
        if c.settings.nearness == "id":
            rk = id_ranks(c.building, M.SLOT_OWNER_KIND[c.slot])
            c.weights[equipment_id] = id_weight(rk[c.doc], rk[equipment_id], c.settings.id_decay)
        else:
            c.weights[equipment_id] = 1.0 if (area is None or eq.area == area) else c.settings.other_area_weight
        self.entries += 1
        self._pending = None

    # ------------------------------------------------------------------------------------------ reading it back
    def describe(self, cause: M.Cause) -> str:
        b, c = self.case.building, self.case
        tag = cause[0]
        if tag == "wrong":
            return f"The documented feeder ({b.label(c.doc)}) is not the feeder: {c.member_name} is fed by {b.label(cause[1])}."
        if tag == "unlisted":
            return "None of the listed equipment feeds it: something else does (or the problem is not the layout)."
        if tag == "doc_acts_fail":
            return f"{b.label(c.doc)} feeds it but does not act when commanded: check its actuator and damper."
        if tag == "doc_other":
            return f"{b.label(c.doc)} feeds it and acts, so this is not a layout or actuation problem: look at setpoint, sensor or capacity (outside this tool's scope)."
        if tag == "doc_ok":
            return f"The documented air handler ({b.label(c.doc)}) feeds it."
        raise ValueError(cause)

    def status(self) -> dict:
        causes, post = self.posterior()
        order = np.argsort(-post, kind="stable")
        ranked = [(causes[i], float(post[i])) for i in order]
        concluded = ranked[0][1] >= self.case.settings.tau
        stalled = (not concluded) and M.select(self.strategy, self._options(causes, post), self.case.settings.min_gain, self.rng) is None
        return dict(ranked=ranked, concluded=concluded, conclusion=self.describe(ranked[0][0]) if concluded else None, stalled=stalled,
                    elapsed=self.elapsed, n_checks=sum(1 for *_, o in self.log if o != "skip"), entries=self.entries, at=self.at)
