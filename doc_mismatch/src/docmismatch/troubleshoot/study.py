"""Sensitivity map of the technician-guided tool against trial-and-error stand-ins (PREREGISTRATION_DR.md Addendum 19). Simulation only; nothing is fitted.

The tool always runs on its ASSUMED default `Settings`. The world it is run against (the "truth") varies over a 486-cell grid: how many candidates there are, how often the documentation is
wrong or the documented box does not act, how local the errors are, how reliable the checks really are and how long they really take. The simulated technician answers from the TRUE hit
rates and every policy is charged the TRUE minutes, while every policy chooses its checks with the assumed numbers. Two assumed habits stand in for trial and error.
"""

from __future__ import annotations

import itertools
import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, replace

import numpy as np

from . import model as M
from . import sim
from .building import Building, Case, Equipment, make_case
from .session import Session

# ---------------------------------------------------------------------------------------------- frozen constants (Addendum 19)
SEED = 19
N_EPISODES = 500
BOOT_B = 1000
MAX_CHECKS = 12
LEVELS = dict(K=(3, 6, 10), p_wrong=(0.05, 0.15, 0.30), p_act=(0.05, 0.15, 0.30), near=(0.05, 0.25, 1.0), rates=("assumed", "degraded"), costs=("assumed", "access_x3", "trace_cheap"))
FACTORS = tuple(LEVELS)
DEFAULT = dict(p_wrong=0.15, p_act=0.15, near=0.25, rates="assumed", costs="assumed")
POLICIES = ("entropy", "split_half", "random", "habit_A", "habit_B")
TOOL = POLICIES[:3]
HABITS = POLICIES[3:]
WIN_R, ACC_TOL = 0.10, 0.02
BROAD_W, BROAD_L, NONE_W, NONE_L = 0.60, 0.10, 0.20, 0.25
STRENGTH_W, WEAKNESS_L = 0.80, 0.25
G3_MIN = 0.92
MEMBER = "Room-0"


# ---------------------------------------------------------------------------------------------- the grid
@dataclass(frozen=True)
class Cell:
    K: int
    p_wrong: float
    p_act: float
    near: float
    rates: str
    costs: str

    @property
    def assumptions_correct(self) -> bool:
        return all(getattr(self, k) == v for k, v in DEFAULT.items())


def all_cells() -> list[Cell]:
    """The 486 cells, indexed in the lexicographic order of the factor levels as listed (the last factor varies fastest)."""
    return [Cell(*levels) for levels in itertools.product(*(LEVELS[f] for f in FACTORS))]


def true_settings(cell: Cell) -> M.Settings:
    """The world's real numbers for `vav_zone`. The unlisted share and the tool-side `tau` etc. stay at their defaults."""
    menu = []
    for c in M.MENUS["vav_zone"]:
        if cell.rates == "degraded" and c.name != "override_room":
            c = replace(c, tpr=max(c.tpr - 0.15, 0.55), fpr=min(c.fpr + 0.10, 0.45))
        if cell.costs == "access_x3":
            c = replace(c, access_min=c.access_min * 3)
        elif cell.costs == "trace_cheap" and c.name == "duct_trace":
            c = replace(c, access_min=3, do_min=5)
        menu.append(c)
    return replace(M.Settings(p_wrong=cell.p_wrong, p_acts_fail=cell.p_act, other_area_weight=cell.near), menus={"vav_zone": tuple(menu), "ahu_vav": M.MENUS["ahu_vav"]})


def make_building(K: int) -> Building:
    """One room documented to box 0; K boxes, ceil(K/2) in the room's area (box 0 included) and the rest in a second area."""
    n_same = (K + 1) // 2
    eq = {f"VAV-{i}": Equipment(f"VAV-{i}", "VAV", "A" if i < n_same else "B") for i in range(K)}
    eq[MEMBER] = Equipment(MEMBER, "Zone", "A")
    return Building(f"synthetic K={K}", eq, {"vav_zone": {MEMBER: "VAV-0"}})


def make_world(cell: Cell) -> tuple[Case, Case, dict]:
    """(the case as the tool believes it, the case with the TRUE numbers, the TRUE check menu by name)."""
    b = make_building(cell.K)
    assumed = make_case(b, MEMBER, "vav_zone", M.Settings(), max_candidates=cell.K)
    real = make_case(b, MEMBER, "vav_zone", true_settings(cell), max_candidates=cell.K)
    return assumed, real, {c.name: c for c in real.settings.menu("vav_zone")}


# ---------------------------------------------------------------------------------------------- policies with TRUE accounting
def _out(case: Case, truth: M.Cause, guess: M.Cause, minutes: float, seq: list, concluded: bool) -> dict:
    return dict(truth=truth, guess=guess, correct=guess == truth, concluded=concluded, minutes=minutes, n_checks=len(seq), sequence=seq)


def run_tool(case: Case, truth: M.Cause, rng: np.random.Generator, true_menu: dict, strategy: str = "entropy") -> dict:
    """`sim.simulate` with the TRUE minutes charged. The call order is the same as there, so with true == assumed the two agree exactly."""
    sess = Session(case, strategy, rng)
    causes = sess.posterior()[0]
    ti = causes.index(truth)
    minutes, at, seq = 0.0, None, []
    while True:
        st = sess.status()
        if st["concluded"] or len(sess.log) >= MAX_CHECKS:
            break
        rec = sess.recommend()
        if rec is None:
            break
        tck = true_menu[rec.check.name]
        py = M.p_yes(case.slot, rec.check, rec.target, causes, case.doc, rates=tck)[ti]
        minutes += tck.minutes(at, rec.target)
        at = rec.target
        seq.append((rec.check.name, rec.target))
        sess.report("yes" if rng.random() < py else "no")
    st = sess.status()
    return _out(case, truth, st["ranked"][0][0], minutes, seq, st["concluded"])


class _Asker:
    """Bookkeeping shared by the habits: ask a check, charge the TRUE minutes, draw the answer from the TRUE hit rates."""

    def __init__(self, case: Case, truth: M.Cause, rng: np.random.Generator, true_menu: dict):
        self.case, self.rng, self.true_menu = case, rng, true_menu
        self.causes = M.make_prior(case.slot, case.candidates, case.doc, case.settings, case.airflow, case.weights)[0]
        self.ti = self.causes.index(truth)
        self.minutes, self.at, self.seq = 0.0, None, []

    def ask(self, ck: M.CheckType, target: str) -> bool:
        tck = self.true_menu[ck.name]
        self.minutes += tck.minutes(self.at, target)
        self.at = target
        self.seq.append((ck.name, target))
        return bool(self.rng.random() < M.p_yes(self.case.slot, ck, target, self.causes, self.case.doc, rates=tck)[self.ti])


def run_habit_A(case: Case, truth: M.Cause, rng: np.random.Generator, true_menu: dict) -> dict:
    """`sim.simulate_habit` with the TRUE minutes charged: confirm the documented box moves, then the cheapest act-and-watch check (by ASSUMED minutes) on the documented box and each
    alternative in turn; the first yes concludes; all no means unlisted."""
    a = _Asker(case, truth, rng, true_menu)
    menu = case.settings.menu(case.slot)
    acts = next((c for c in menu if c.kind == "acts"), None)
    if acts is not None and not a.ask(acts, case.doc):
        return _out(case, truth, ("doc_acts_fail",), a.minutes, a.seq, True)
    observers = [c for c in menu if c.kind == "act_observe"]
    for j in case.candidates:
        if a.ask(min(observers, key=lambda c: c.minutes(a.at, j)), j):
            return _out(case, truth, (sim.SLOT_DOC_OK[case.slot],) if j == case.doc else ("wrong", j), a.minutes, a.seq, True)
    return _out(case, truth, ("unlisted",), a.minutes, a.seq, True)


def run_habit_B(case: Case, truth: M.Cause, rng: np.random.Generator, true_menu: dict) -> dict:
    """Trace first: a duct trace on the documented box, then on each alternative in candidate order; the first yes concludes. If the documented box's trace says yes, confirm it moves
    (no: acts-fail; yes: the cause is elsewhere). All no means unlisted."""
    a = _Asker(case, truth, rng, true_menu)
    menu = case.settings.menu(case.slot)
    trace = next(c for c in menu if c.kind == "trace")
    acts = next((c for c in menu if c.kind == "acts"), None)
    for j in case.candidates:
        if a.ask(trace, j):
            if j != case.doc:
                return _out(case, truth, ("wrong", j), a.minutes, a.seq, True)
            if acts is not None and not a.ask(acts, case.doc):
                return _out(case, truth, ("doc_acts_fail",), a.minutes, a.seq, True)
            return _out(case, truth, (sim.SLOT_DOC_OK[case.slot],), a.minutes, a.seq, True)
    return _out(case, truth, ("unlisted",), a.minutes, a.seq, True)


RUNNERS = {"entropy": lambda c, t, r, m: run_tool(c, t, r, m, "entropy"), "split_half": lambda c, t, r, m: run_tool(c, t, r, m, "split_half"),
           "random": lambda c, t, r, m: run_tool(c, t, r, m, "random"), "habit_A": run_habit_A, "habit_B": run_habit_B}


# ---------------------------------------------------------------------------------------------- one cell
def run_cell(idx: int, cell: Cell, n: int = N_EPISODES) -> dict:
    """`n` episodes per policy on the same `n` truths (seed [SEED, idx]); each policy's outcome draws use [SEED, idx, policy, episode]. Raw arrays only."""
    assumed, real, true_menu = make_world(cell)
    causes = M.make_prior("vav_zone", assumed.candidates, assumed.doc, assumed.settings, None, assumed.weights)[0]
    rng_t = np.random.default_rng([SEED, idx])
    truths = [sim.sample_truth(real, rng_t) for _ in range(n)]
    out = dict(idx=idx, cell=cell, n=n, causes=causes, policy={})
    for pi, name in enumerate(POLICIES):
        rows = [RUNNERS[name](assumed, t, np.random.default_rng([SEED, idx, pi, i]), true_menu) for i, t in enumerate(truths)]
        out["policy"][name] = dict(
            truth_idx=np.array([causes.index(t) for t in truths]), guess_idx=np.array([causes.index(r["guess"]) for r in rows]),
            minutes=np.array([r["minutes"] for r in rows], float), checks=np.array([r["n_checks"] for r in rows], float),
            concluded=np.array([r["concluded"] for r in rows], bool), correct=np.array([r["correct"] for r in rows], bool))
    return out


def _run_cell_args(args):
    return run_cell(*args)


def compute_cells(cells: list[tuple[int, Cell]], n: int = N_EPISODES, workers: int | None = None) -> list[dict]:
    """Deterministic whatever the number of workers (every cell has its own seeds)."""
    jobs = [(i, c, n) for i, c in cells]
    workers = workers if workers is not None else min(8, os.cpu_count() or 1)
    if workers <= 1 or len(jobs) == 1:
        return [_run_cell_args(j) for j in jobs]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_run_cell_args, jobs))


# ---------------------------------------------------------------------------------------------- summaries, classification, map reading
def summarize(res: dict) -> dict:
    out = {}
    for name, p in res["policy"].items():
        conc = p["concluded"]
        out[name] = dict(minutes=float(p["minutes"].mean()), accuracy=float(p["correct"].mean()), checks=float(p["checks"].mean()), entries=1.0 + float(p["checks"].mean()),
                         concluded=float(conc.mean()), unresolved=float((~conc).mean()), wrong_confident=float((conc & ~p["correct"]).mean()),
                         acc_concluded=float(p["correct"][conc].mean()) if conc.any() else float("nan"), per_correct=float(p["minutes"].mean() / max(p["correct"].mean(), 1e-12)))
    return out


def paired_ci(diff: np.ndarray, boot_idx: np.ndarray) -> tuple[float, float]:
    """95% interval of the mean of the paired per-episode differences over the bootstrap resamples `boot_idx` (B x n)."""
    m = diff[boot_idx].mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def classify_pair(m_t: float, m_h: float, a_t: float, a_h: float, ci_min: tuple[float, float]) -> tuple[str, bool]:
    """(WINS | LOSES | NEITHER, trade-off flag) for one tool policy against one habit."""
    r, d_acc = (m_t - m_h) / m_h, a_t - a_h
    tradeoff = r <= -WIN_R and d_acc < -ACC_TOL
    if r <= -WIN_R and d_acc >= -ACC_TOL and ci_min[1] < 0:
        return "WINS", False
    if r >= WIN_R and d_acc <= ACC_TOL and ci_min[0] > 0:
        return "LOSES", False
    return "NEITHER", tradeoff


def combine(labels: list[str]) -> str:
    """Against BOTH habits: WINS only if it wins against each, LOSES if it loses against either."""
    if "LOSES" in labels:
        return "LOSES"
    return "WINS" if all(x == "WINS" for x in labels) else "NEITHER"


def analyze_cell(res: dict, B: int = BOOT_B) -> dict:
    n = res["n"]
    boot = np.random.default_rng([SEED, res["idx"], 99]).integers(0, n, (B, n))
    summ = summarize(res)
    pol = res["policy"]
    cmp_, label, tradeoff = {}, {}, {}
    for t in TOOL:
        labs, flags = [], []
        for h in HABITS:
            d_min = pol[t]["minutes"] - pol[h]["minutes"]
            d_acc = pol[t]["correct"].astype(float) - pol[h]["correct"].astype(float)
            ci_min, ci_acc = paired_ci(d_min, boot), paired_ci(d_acc, boot)
            lab, flag = classify_pair(summ[t]["minutes"], summ[h]["minutes"], summ[t]["accuracy"], summ[h]["accuracy"], ci_min)
            cmp_[f"{t}|{h}"] = dict(d_min=float(d_min.mean()), r_min=float(d_min.mean() / summ[h]["minutes"]), d_acc=float(d_acc.mean()), ci_min=ci_min, ci_acc=ci_acc, label=lab, tradeoff=flag)
            labs.append(lab)
            flags.append(flag)
        label[t] = combine(labs)
        tradeoff[t] = any(flags)
    return dict(idx=res["idx"], cell=res["cell"], summary=summ, cmp=cmp_, label=label, tradeoff=tradeoff)


def map_fractions(labels: list[str]) -> tuple[float, float]:
    n = max(len(labels), 1)
    return sum(x == "WINS" for x in labels) / n, sum(x == "LOSES" for x in labels) / n


def map_reading(w: float, l: float) -> str:
    if w >= BROAD_W and l <= BROAD_L:
        return "HELPS BROADLY"
    if w < NONE_W or l > NONE_L:
        return "DOES NOT HELP"
    return "HELPS IN PART"


def marginals(cells: list[Cell], labels: list[str], factor: str) -> dict:
    """{level: (W, L, n)} of one factor."""
    out = {}
    for lv in LEVELS[factor]:
        sel = [lab for c, lab in zip(cells, labels) if getattr(c, factor) == lv]
        w, l = map_fractions(sel)
        out[lv] = (w, l, len(sel))
    return out


def departure(cell: Cell) -> int:
    """How many of the tool's three PRIOR assumptions (P(wrong), P(acts-fail), nearness) the truth departs from."""
    return sum(getattr(cell, k) != DEFAULT[k] for k in ("p_wrong", "p_act", "near"))


def predictions(cells: list[Cell], lab: dict[str, list[str]]) -> dict:
    """P1-P5 as operationalised before the run: each compares W between two extreme levels (P3: between zero and three departures from the tool's prior)."""
    W = lambda labels, sel: map_fractions([x for x, s in zip(labels, sel) if s])[0]  # noqa: E731
    ent, spl = lab["entropy"], lab["split_half"]
    at = lambda f, lv: [getattr(c, f) == lv for c in cells]  # noqa: E731
    p1 = (W(ent, at("K", 10)), W(ent, at("K", 3)))
    p2 = (W(ent, at("p_wrong", 0.30)), W(ent, at("p_wrong", 0.05)))
    dep = lambda k: [departure(c) == k for c in cells]  # noqa: E731
    p3 = (W(ent, dep(3)) - W(spl, dep(3)), W(ent, dep(0)) - W(spl, dep(0)))
    p4 = (W(ent, at("costs", "access_x3")), W(ent, at("costs", "assumed")))
    p5 = (W(spl, at("rates", "degraded")), W(ent, at("rates", "degraded")))
    return dict(P1=dict(holds=p1[0] > p1[1], values=p1), P2=dict(holds=p2[0] > p2[1], values=p2), P3=dict(holds=p3[0] < p3[1], values=p3),
                P4=dict(holds=p4[0] > p4[1], values=p4), P5=dict(holds=p5[0] >= p5[1], values=p5))


# ---------------------------------------------------------------------------------------------- gates
def g3_honesty(results: list[dict]) -> tuple[bool, dict]:
    """Accuracy among CONCLUDED `entropy` episodes >= G3_MIN in every assumptions-correct cell (a lower value would mean a defect in the belief update, not a finding)."""
    vals = {}
    for r in results:
        if r["cell"].assumptions_correct:
            p = r["policy"]["entropy"]
            vals[r["cell"].K] = float(p["correct"][p["concluded"]].mean()) if p["concluded"].any() else float("nan")
    return bool(vals) and all(v >= G3_MIN for v in vals.values()), vals


def g5_complete(results: list[dict], n_cells: int = 486, expected_idx: list[int] | None = None) -> tuple[bool, str]:
    """All expected cells present (default: indices 0..n_cells-1; a smoke run passes its own subset), every policy finite, and identical truths across the policies of a cell."""
    want = list(range(n_cells)) if expected_idx is None else sorted(expected_idx)
    if len(results) != len(want) or sorted(r["idx"] for r in results) != want:
        return False, f"{len(results)} cells present, expected {len(want)}"
    for r in results:
        if set(r["policy"]) != set(POLICIES):
            return False, f"cell {r['idx']}: policies {sorted(r['policy'])}"
        ref = r["policy"][POLICIES[0]]["truth_idx"]
        for name, p in r["policy"].items():
            if not np.isfinite(p["minutes"]).all() or len(p["minutes"]) != r["n"]:
                return False, f"cell {r['idx']} {name}: non-finite or short minutes"
            if not np.array_equal(p["truth_idx"], ref):
                return False, f"cell {r['idx']} {name}: truths differ from the other policies"
    return True, "ok"
