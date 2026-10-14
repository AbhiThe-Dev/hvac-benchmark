"""A simulated technician for v1, so the loop can be exercised and studied without a real one. Nothing here is evidence about real technicians.

A `World` is the truth of one call-out: the real cause, the facts the technician would declare if asked (does the box have reheat, can they get into the control system, do they have
a gauge, is the occupant there), and the TRUE response model of the checks (the tool's own by default; `catalogue.degrade_all` makes it worse than the tool believes). Every answer is
drawn from the TRUE response probability of the check under the real cause, so a tool whose assumed reliabilities are too optimistic is exposed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .. import model as M
from . import catalogue as K
from . import causes as C
from .engine import CaseV1, Question, Recommendation, Session


@dataclass
class World:
    truth: tuple
    context: dict = field(default_factory=lambda: dict(reheat="yes", bas_access="no", instrument="yes", occupant="yes"))
    true_checks: tuple | None = None          # default: the case's own catalogue (the tool's model is right)

    def check(self, case: CaseV1, name: str) -> K.CheckV1:
        return {c.name: c for c in (self.true_checks or case.checks)}[name]


def check_world(case: CaseV1, w: World) -> None:
    """Raise if the world is impossible for this case (a truth the tool's hypothesis space at this tier cannot contain, or a cause the box cannot have)."""
    t = w.truth[0]
    if t in ("wrong", "unlisted") and not case.docs:
        raise ValueError(f"truth {w.truth!r} is a documentation cause; tier {case.tier} has no documentation to be wrong")
    if t == "wrong" and w.truth[1] not in case.candidates:
        raise ValueError(f"truth {w.truth!r} names a box that is not a candidate")
    if t in C.BY_ID:
        need = C.BY_ID[t].needs
        if need == "reheat" and w.context.get("reheat") == "no":
            raise ValueError("reheat_fail is impossible on a box without reheat")
    if case.compat_v0 and t in C.BY_ID:
        raise ValueError("a v0-equivalent case has only v0's causes")


def p_true(case: CaseV1, w: World, ck_name: str, target: str) -> float:
    """P(the technician's answer is positive), from the TRUE response of the check under the real cause."""
    p = K.p_pos(w.check(case, ck_name), w.truth, target, case.doc)
    return float(np.clip(p, M.RATE_FLOOR, 1.0 - M.RATE_FLOOR))


def answer(case: CaseV1, w: World, rec: Recommendation, rng: np.random.Generator | None) -> str:
    """The technician's answer in the check's own words. `rng=None` gives the most likely answer (deterministic: used for scripted demonstrations)."""
    p = p_true(case, w, rec.check.name, rec.target)
    pos = (rng.random() < p) if rng is not None else (p >= 0.5)
    return rec.check.words[0] if pos else rec.check.words[1]


def simulate_v1(case: CaseV1, w: World, strategy: str = "entropy", rng: np.random.Generator | None = None, max_checks: int = 12, modal: bool = False) -> dict:
    """Run a session against the simulated technician. Stops when a cause reaches tau, after `max_checks` checks, or when nothing more would help. Questions are answered from
    `w.context` and count as entries, not as checks. `modal=True` answers each check with its most likely result instead of drawing."""
    check_world(case, w)
    rng = rng if rng is not None else np.random.default_rng(0)
    sess = Session(case, strategy, rng)
    seq, trace = [], []
    while len(sess.log) < max_checks:
        step = sess.next_step()
        if step is None:
            break
        if isinstance(step, Question):
            sess.declare(step.key, w.context[step.key])
            trace.append(("Q", step.key, w.context[step.key]))
            continue
        seq.append((step.check.name, step.target))
        ans = answer(case, w, step, None if modal else rng)
        trace.append(("C", step.check.name, step.target, ans))
        sess.report(ans)
    st = sess.status()
    guess = st["ranked"][0][0]
    return dict(truth=w.truth, guess=guess, correct=guess == w.truth, concluded=st["concluded"], stalled=st["stalled"], minutes=sess.elapsed, n_checks=st["n_checks"],
                n_questions=len(sess.declared), entries=st["entries"], sequence=seq, events=len(sess.events), trace=trace)


def replay(case: CaseV1, trace: list, strategy: str = "entropy") -> bool:
    """Feed a fresh session only the recorded answers and declarations of an episode and check that it asks the same questions and recommends the same checks in the same order: the
    tool's choices depend on the answers it has been given and on nothing about the world that produced them (in particular not on how reliable the checks really are)."""
    sess = Session(case, strategy)
    for item in trace:
        step = sess.next_step()
        if item[0] == "Q":
            if not isinstance(step, Question) or step.key != item[1]:
                return False
            sess.declare(step.key, item[2])
        else:
            if not isinstance(step, Recommendation) or (step.check.name, step.target) != (item[1], item[2]):
                return False
            sess.report(item[3])
    return True


def technician_input(sess: Session, w: World, rng: np.random.Generator | None = None, echo=print):
    """An `input_fn` for `cli.run`: answers the pending question or check the way the simulated technician would."""
    case = sess.case

    def fake_input(prompt: str) -> str:
        q = sess.pending_question
        if q is not None:
            ans = "y" if w.context[q.key] == "yes" else "n"
        else:
            name, target = sess.pending
            p = p_true(case, w, name, target)
            pos = (rng.random() < p) if rng is not None else (p >= 0.5)
            ans = ("y" if pos else "n")
        echo(f"{prompt}{ans}")
        return ans

    return fake_input
