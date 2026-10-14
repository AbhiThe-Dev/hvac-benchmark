"""A simulated technician, so the loop can be exercised and compared with a habit-order stand-in without a real technician.

The truth is one of the case's causes; every answer is drawn from the check's TRUE hit and false-alarm rates (`true_settings`, default: the tool's own). Passing different
`true_settings` tests what happens when the tool's assumed numbers are wrong. Nothing here is evidence about real technicians: `habit` in particular is an ASSUMED stand-in for
"check the box, then walk the alternatives", like the `traversal` policy in hvac_benchmark.
"""

from __future__ import annotations

import numpy as np

from . import model as M
from .building import Case
from .session import Session


def _result(case: Case, truth: M.Cause, guess: M.Cause, minutes: float, n_checks: int, concluded: bool, stalled: bool = False) -> dict:
    return dict(truth=truth, guess=guess, correct=guess == truth, concluded=concluded, stalled=stalled, minutes=minutes, n_checks=n_checks, entries=case.entries0 + n_checks)


def sample_truth(case: Case, rng: np.random.Generator, true_prior: np.ndarray | None = None) -> M.Cause:
    causes, prior = M.make_prior(case.slot, case.candidates, case.doc, case.settings, case.airflow, case.weights)
    p = np.asarray(true_prior if true_prior is not None else prior, float)
    return causes[int(rng.choice(len(causes), p=p / p.sum()))]


def simulate(case: Case, truth: M.Cause, strategy: str = "entropy", rng: np.random.Generator | None = None, true_settings: M.Settings | None = None,
             max_checks: int = 12, budget_min: float | None = None) -> dict:
    """Run a session against a simulated technician. Stops when a cause reaches tau, after `max_checks`, past `budget_min`, or when nothing more would help."""
    rng = rng if rng is not None else np.random.default_rng(0)
    sess = Session(case, strategy, rng)
    causes = sess.posterior()[0]
    if truth not in causes:
        raise ValueError(f"{truth!r} is not one of this case's causes")
    ti = causes.index(truth)
    true_menu = {c.name: c for c in (true_settings or case.settings).menu(case.slot)}
    while True:
        st = sess.status()
        if st["concluded"] or len(sess.log) >= max_checks or (budget_min is not None and sess.elapsed >= budget_min):
            break
        rec = sess.recommend()
        if rec is None:
            break
        py = M.p_yes(case.slot, rec.check, rec.target, causes, case.doc, rates=true_menu[rec.check.name])[ti]
        sess.report("yes" if rng.random() < py else "no")
    st = sess.status()
    return _result(case, truth, st["ranked"][0][0], sess.elapsed, st["n_checks"], st["concluded"], st["stalled"])


def simulate_habit(case: Case, truth: M.Cause, rng: np.random.Generator | None = None, true_settings: M.Settings | None = None) -> dict:
    """The stand-in for trial and error (ASSUMED): confirm the documented box acts, then try the cheapest 'act and watch' check on the documented box and each alternative in
    turn, concluding on the first yes; all no means an unlisted feeder. It has no belief to update, so it can be fooled by a false alarm."""
    rng = rng if rng is not None else np.random.default_rng(0)
    menu = case.settings.menu(case.slot)
    causes = M.make_prior(case.slot, case.candidates, case.doc, case.settings, case.airflow, case.weights)[0]
    if truth not in causes:
        raise ValueError(f"{truth!r} is not one of this case's causes")
    ti = causes.index(truth)
    true_menu = {c.name: c for c in (true_settings or case.settings).menu(case.slot)}
    state = dict(minutes=0.0, at=None, n=0)

    def ask(ck: M.CheckType, target: str) -> bool:
        state["minutes"] += ck.minutes(state["at"], target)
        state["at"] = target
        state["n"] += 1
        return bool(rng.random() < M.p_yes(case.slot, ck, target, causes, case.doc, rates=true_menu[ck.name])[ti])

    def done(guess: M.Cause) -> dict:
        return _result(case, truth, guess, state["minutes"], state["n"], True)

    acts = next((c for c in menu if c.kind == "acts"), None)
    if acts is not None and not ask(acts, case.doc):
        return done(("doc_acts_fail",))
    observers = [c for c in menu if c.kind == "act_observe"]
    for j in case.candidates:
        if ask(min(observers, key=lambda c: c.minutes(state["at"], j)), j):
            return done((SLOT_DOC_OK[case.slot],) if j == case.doc else ("wrong", j))
    return done(("unlisted",))


SLOT_DOC_OK = {"vav_zone": "doc_other", "ahu_vav": "doc_ok"}


def technician_input(sess: Session, truth: M.Cause, rng: np.random.Generator, echo=print, true_settings: M.Settings | None = None):
    """An `input_fn` for `cli.run` that answers the pending recommendation the way a simulated technician would when `truth` is the real cause."""
    case = sess.case
    causes = sess.posterior()[0]
    ti = causes.index(truth)
    true_menu = {c.name: c for c in (true_settings or case.settings).menu(case.slot)}

    def fake_input(prompt: str) -> str:
        name, target = sess.pending
        py = M.p_yes(case.slot, sess._check(name), target, causes, case.doc, rates=true_menu[name])[ti]
        ans = "y" if rng.random() < py else "n"
        echo(f"{prompt}{ans}")
        return ans

    return fake_input
