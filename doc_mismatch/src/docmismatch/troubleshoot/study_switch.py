"""Is a one-way "the drawings are mostly right" switch worth offering, and does it stay safe when the actuators or the checks are worse than assumed? (PREREGISTRATION_DR.md Addendum 22.)
Layouts real (Mortar Brick metadata); errors and answers simulated.

The switch has two states: off = the default prior (P(documented feeder wrong) 0.15) and on = 0.05 (the `mostly_right` level); `on_mild` (0.10) is a secondary arm. A cell is (condition, world,
regime, building): the condition sets how bad the actuators and checks really are, the world is the TRUE share of wrong drawings. In every cell the same 500 (room, cause) episodes are run by
`entropy` under each state and by the two stand-in habits, which never read the prior. Labels, readings and the paired bootstrap are those of Addendum 21 (`study_rating.py`); the tool's own
assumptions other than P(wrong) never change.
"""

from __future__ import annotations

import itertools
import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, replace

import numpy as np

from . import model as M
from . import sim
from . import study as S
from . import study_rating as SG
from . import study_real as SR
from .building import Building, make_case
from .realmaps import REGIME_CAPS, layout_problems  # noqa: F401  (re-exported for the script)

SEED = 22
N_EPISODES = 500
BOOT_B = 1000
REGIMES = REGIME_CAPS
STATES = ("off", "on", "on_mild")
BASE = "off"
LEVELS = {"off": 0.15, "on": 0.05, "on_mild": 0.10}
CONDITIONS = {"X0": (0.15, "assumed"), "X1": (0.30, "assumed"), "X2": (0.15, "degraded"), "X3": (0.30, "degraded")}      # (world P(acts-fail), hit rates)
CONDITION_TEXT = {"X0": "as assumed", "X1": "actuators fail more", "X2": "checks worse", "X3": "both"}
WORLDS = ("p05", "p15", "p30")
P_WRONG = {"p05": 0.05, "p15": 0.15, "p30": 0.30}
RIGHT_WORLD = "p05"                                       # the switch is right here; wrongly on in the other two
WRONG_WORLDS = ("p15", "p30")
POLICIES = tuple(f"entropy@{s}" for s in STATES) + S.HABITS
HABITS = S.HABITS
MIXES = {"equal": (1 / 3, 1 / 3, 1 / 3), "tilted": (0.6, 0.3, 0.1)}                   # weights of (p05, p15, p30)
S_LEVELS = (0.5, 1.0)
F_GRID = [round(0.01 * i, 2) for i in range(101)]
F_BAR = 0.50
BUDGET_ACC, BUDGET_WC = 0.01, 0.01
G3_MIN = 0.92
METRICS = SG.METRICS


def tool_name(state: str) -> str:
    return f"entropy@{state}"


def settings_for(state: str) -> M.Settings:
    if state == "off":
        return M.Settings()
    if state == "on":
        return M.Settings().with_drawings("mostly_right")
    if state == "on_mild":
        return replace(M.Settings(), p_wrong=LEVELS["on_mild"])
    raise ValueError(f"unknown switch state {state!r}")


def world_cell(condition: str, world: str) -> S.Cell:
    p_act, rates = CONDITIONS[condition]
    return S.Cell(0, P_WRONG[world], p_act, 0.25, rates, "assumed")


@dataclass(frozen=True)
class SwitchCell:
    condition: str
    world: str
    regime: str
    building: str


def all_switch_cells(buildings: list[str]) -> list[SwitchCell]:
    """Lexicographic: condition outermost (X0..X3), then world (5%, 15%, 30% wrong), then regime, then building (in the order given)."""
    return [SwitchCell(c, w, r, b) for c, w, r, b in itertools.product(CONDITIONS, WORLDS, REGIMES, buildings)]


def assumed_case(layout: Building, room: str, regime: str, state: str):
    return make_case(layout, room, "vav_zone", settings_for(state), max_candidates=REGIMES[regime])


def real_case(layout: Building, room: str, condition: str, world: str, regime: str):
    return make_case(layout, room, "vav_zone", S.true_settings(world_cell(condition, world)), max_candidates=REGIMES[regime])


# ---------------------------------------------------------------------------------------------- one cell
def run_switch_cell(idx: int, spec: SwitchCell, layout: Building, n: int = N_EPISODES) -> dict:
    """`n` episodes per policy on the same `n` (room, cause) draws (seed [SEED, idx]). The three states share the outcome stream [SEED, idx, 0, episode]; habit_A uses stream 1 and habit_B
    stream 2. Raw arrays only."""
    wc = world_cell(spec.condition, spec.world)
    true_menu = {c.name: c for c in S.true_settings(wc).menu("vav_zone")}
    rooms = sorted(layout.claims["vav_zone"])
    cases, reals = {}, {}

    def assumed(room, state):
        if (room, state) not in cases:
            cases[(room, state)] = assumed_case(layout, room, spec.regime, state)
        return cases[(room, state)]

    def real(room):
        if room not in reals:
            reals[room] = real_case(layout, room, spec.condition, spec.world, spec.regime)
        return reals[room]

    def causes(room):
        a = assumed(room, BASE)
        return M.make_prior("vav_zone", a.candidates, a.doc, a.settings, None, a.weights)[0]

    rng = np.random.default_rng([SEED, idx])
    picks = []
    for _ in range(n):
        room = rooms[int(rng.integers(len(rooms)))]
        picks.append((room, sim.sample_truth(real(room), rng)))
    out = dict(idx=idx, cell=spec, n=n, rooms=len(rooms), boxes=len({b for b in layout.claims["vav_zone"].values()}), K=np.array([len(assumed(r, BASE).candidates) for r, _ in picks], float), policy={})
    for name in POLICIES:
        if name.startswith("entropy@"):
            state, stream, runner = name.split("@")[1], 0, (lambda c, t, r, m: S.run_tool(c, t, r, m, "entropy"))
        else:
            state, stream, runner = BASE, 1 + HABITS.index(name), S.RUNNERS[name]                   # the habits never read the prior: they run on the default case
        rows = [runner(assumed(room, state), t, np.random.default_rng([SEED, idx, stream, i]), true_menu) for i, (room, t) in enumerate(picks)]
        out["policy"][name] = dict(
            truth_idx=np.array([causes(room).index(t) for room, t in picks]), guess_idx=np.array([causes(room).index(r["guess"]) for (room, _), r in zip(picks, rows)]),
            minutes=np.array([r["minutes"] for r in rows], float), checks=np.array([r["n_checks"] for r in rows], float),
            concluded=np.array([r["concluded"] for r in rows], bool), correct=np.array([r["correct"] for r in rows], bool))
    return out


def _run_args(args):
    return run_switch_cell(*args)


def compute_switch_cells(jobs: list[tuple[int, SwitchCell, Building]], n: int = N_EPISODES, workers: int | None = None) -> list[dict]:
    """Deterministic whatever the number of workers."""
    args = [(i, c, lay, n) for i, c, lay in jobs]
    workers = workers if workers is not None else min(8, os.cpu_count() or 1)
    if workers <= 1 or len(args) == 1:
        return [_run_args(a) for a in args]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_run_args, args, chunksize=1))


# ---------------------------------------------------------------------------------------------- analysis of one cell
def analyze_switch_cell(res: dict, B: int = BOOT_B) -> dict:
    """`on` and `on_mild` against `off` on the same episodes (labels of Addendum 21), and each state against the two habits (Addendum 19's rule; context only)."""
    n = res["n"]
    boot = np.random.default_rng([SEED, res["idx"], 99]).integers(0, n, (B, n))
    summ = S.summarize(res)
    pol = res["policy"]
    wc = {p: (v["concluded"] & ~v["correct"]).astype(float) for p, v in pol.items()}
    base = tool_name(BASE)
    cmp_ = {}
    for st in STATES:
        if st == BASE:
            continue
        t = tool_name(st)
        d_min, d_acc = pol[t]["minutes"] - pol[base]["minutes"], pol[t]["correct"].astype(float) - pol[base]["correct"].astype(float)
        d_wc, d_chk = wc[t] - wc[base], pol[t]["checks"] - pol[base]["checks"]
        ci_min, ci_acc, ci_wc = S.paired_ci(d_min, boot), S.paired_ci(d_acc, boot), S.paired_ci(d_wc, boot)
        r_min = float(d_min.mean() / summ[base]["minutes"])
        ts, as_ = SG.time_state(r_min, ci_min), SG.acc_state(float(d_acc.mean()), ci_acc)
        cmp_[st] = dict(d_min=float(d_min.mean()), r_min=r_min, d_acc=float(d_acc.mean()), d_wc=float(d_wc.mean()), d_checks=float(d_chk.mean()), ci_min=ci_min, ci_acc=ci_acc, ci_wc=ci_wc,
                        time=ts, acc=as_, label=SG.label(ts, as_), safety=SG.safety_flag(float(d_wc.mean()), ci_wc))
    ctx = {}
    for st in STATES:
        t, labs = tool_name(st), []
        for h in HABITS:
            d_min, d_acc = pol[t]["minutes"] - pol[h]["minutes"], pol[t]["correct"].astype(float) - pol[h]["correct"].astype(float)
            ci_min, ci_acc = S.paired_ci(d_min, boot), S.paired_ci(d_acc, boot)
            lab, flag = S.classify_pair(summ[t]["minutes"], summ[h]["minutes"], summ[t]["accuracy"], summ[h]["accuracy"], ci_min)
            entry = dict(label=lab, tradeoff=flag, r_min=float(d_min.mean() / summ[h]["minutes"]), d_acc=float(d_acc.mean()), ci_min=ci_min, ci_acc=ci_acc)
            entry["secondary"] = SR.secondary_label(entry)
            ctx[f"{st}|{h}"] = entry
            labs.append(lab)
        ctx[st] = S.combine(labs)
    return dict(idx=res["idx"], cell=res["cell"], summary=summ, cmp=cmp_, ctx=ctx)


# ---------------------------------------------------------------------------------------------- groups, expected change, break-even, decision
def group_cells(analyses: list[dict], condition: str, world: str, regime: str | None = None) -> list[dict]:
    return [a for a in analyses if a["cell"].condition == condition and a["cell"].world == world and (regime is None or a["cell"].regime == regime)]


def mean_delta(cells: list[dict], state: str) -> dict:
    """Mean over the buildings (cells) of the per-cell paired mean differences to `off`; zero for `off` itself."""
    if state == BASE:
        return {k: 0.0 for k in METRICS}
    return {k: float(np.mean([a["cmp"][state][k] for a in cells])) for k in METRICS}


def deltas(analyses: list[dict], state: str = "on") -> dict:
    """{condition: {regime: {world: mean deltas of `state` against `off`}}}."""
    return {c: {reg: {w: mean_delta(group_cells(analyses, c, w, reg), state) for w in WORLDS} for reg in REGIMES} for c in CONDITIONS}


def group_readings(analyses: list[dict]) -> dict:
    """{(condition, world): reading of `on`}: the map reading where the switch is right (5% wrong), the harm reading where it is wrongly on; 50 cells (both regimes) each."""
    out = {}
    for c in CONDITIONS:
        for w in WORLDS:
            fr = SG.fractions(group_cells(analyses, c, w), "on")
            out[(c, w)] = SG.matched_reading(fr) if w == RIGHT_WORLD else SG.harm_reading(fr)
    return out


def p_on(world: str, s: float, f: float) -> float:
    return s if world == RIGHT_WORLD else f


def expected_change(by_world: dict, s: float, f: float, mix: tuple) -> dict:
    """Expected change against never switching on when the technician flips the switch on with probability s in a 5%-wrong building and f in a 15%- or 30%-wrong one, worlds weighted by
    `mix`; `by_world[world]` = mean deltas of `on` against `off`."""
    out = {k: 0.0 for k in METRICS}
    for w, pi in zip(WORLDS, mix):
        for k in METRICS:
            out[k] += pi * p_on(w, s, f) * by_world[w][k]
    return out


def favourable(ch: dict, tol: float = 1e-12) -> bool:
    """Minutes not above 0, accuracy not more than BUDGET_ACC below and wrong-and-confident not more than BUDGET_WC above the default's."""
    return ch["d_min"] <= tol and ch["d_acc"] >= -BUDGET_ACC - tol and ch["d_wc"] <= BUDGET_WC + tol


def break_even_f(by_world: dict, s: float, mix: tuple) -> float | None:
    """The largest f on F_GRID at which the change is favourable at every grid value up to f; None if it is not favourable at f = 0."""
    best = None
    for f in F_GRID:
        if not favourable(expected_change(by_world, s, f, mix)):
            break
        best = f
    return best


def break_even_table(analyses: list[dict]) -> dict:
    """{(condition, regime, mix, s): f*}."""
    dl = deltas(analyses)
    return {(c, reg, m, s): break_even_f(dl[c][reg], s, MIXES[m]) for c in CONDITIONS for reg in REGIMES for m in MIXES for s in S_LEVELS}


def condition_ok(readings: dict, fstar: dict, condition: str) -> bool:
    """C: no wrongly-on group (15% or 30% wrong) of the condition reads HARMFUL and f* >= F_BAR at s = 1.0 for both mixes and both regimes."""
    if any(readings[(condition, w)] == "HARMFUL" for w in WRONG_WORLDS):
        return False
    return all(fstar[(condition, reg, m, 1.0)] is not None and fstar[(condition, reg, m, 1.0)] >= F_BAR - 1e-9 for reg in REGIMES for m in MIXES)


def decide(readings: dict, fstar: dict) -> tuple[str, bool, dict]:
    """(decision, Q, {condition: C}). Q = the X0 5%-wrong group reads at least HELPS IN PART."""
    q = readings[("X0", RIGHT_WORLD)] != "DOES NOT HELP"
    c = {x: condition_ok(readings, fstar, x) for x in CONDITIONS}
    if not q:
        return "NOT WORTH OFFERING", q, c
    if all(c.values()):
        return "WORTH OFFERING", q, c
    if c["X0"] and c["X1"]:
        return "CONDITIONAL ON RELIABLE CHECKS", q, c
    return "NOT WORTH OFFERING", q, c


def switch_predictions(analyses: list[dict]) -> dict:
    """P1-P5 as registered before the run; each strict."""
    on, mild = deltas(analyses, "on"), deltas(analyses, "on_mild")
    readings, fstar = group_readings(analyses), break_even_table(analyses)
    decision = decide(readings, fstar)[0]
    p1 = {reg: (on["X0"][reg][RIGHT_WORLD]["d_min"], on["X0"][reg][RIGHT_WORLD]["d_acc"]) for reg in REGIMES}
    p2 = {reg: (on["X2"][reg]["p30"]["d_wc"], on["X0"][reg]["p30"]["d_wc"]) for reg in REGIMES}
    p3 = {(c, reg, w): on[c][reg][w]["d_min"] for c in CONDITIONS for reg in REGIMES for w in WORLDS}
    p4 = {(c, reg): (mild[c][reg][RIGHT_WORLD]["d_min"], on[c][reg][RIGHT_WORLD]["d_min"], mild[c][reg]["p30"]["d_wc"], on[c][reg]["p30"]["d_wc"]) for c in CONDITIONS for reg in REGIMES}
    return dict(P1=dict(holds=all(m < 0 and a >= -0.01 for m, a in p1.values()), values=p1), P2=dict(holds=all(x > y for x, y in p2.values()), values=p2),
                P3=dict(holds=all(v < 0 for v in p3.values()), values=p3), P4=dict(holds=all(mm > mo and wm < wo for mm, mo, wm, wo in p4.values()), values=p4),
                P5=dict(holds=decision == "CONDITIONAL ON RELIABLE CHECKS", values=decision))


# ---------------------------------------------------------------------------------------------- gates
def gate_g1_switch(layout: Building, n: int = 30) -> tuple[bool, str]:
    """G1: `off` is exactly `Settings()`, `on` is `with_drawings('mostly_right')`, episodes under `off` are identical to the tool as it was, and the runners reproduce `sim.simulate`."""
    if settings_for("off") != M.Settings() or settings_for("on") != M.Settings().with_drawings("mostly_right"):
        return False, "a switch state differs from the settings it is defined as"
    if [settings_for(x).p_wrong for x in ("on", "on_mild", "off")] != [0.05, 0.10, 0.15]:
        return False, "the switch levels are not on 0.05, on_mild 0.10, off 0.15"
    room = sorted(layout.claims["vav_zone"])[0]
    a = assumed_case(layout, room, "R_narrow", "off")
    b = make_case(layout, room, "vav_zone", M.Settings(), max_candidates=REGIMES["R_narrow"])
    real = real_case(layout, room, "X0", "p15", "R_narrow")
    tm = {c.name: c for c in real.settings.menu("vav_zone")}
    rng = np.random.default_rng(1)
    for seed in range(n):
        t = sim.sample_truth(real, rng)
        x, y = S.run_tool(a, t, np.random.default_rng(seed), tm), S.run_tool(b, t, np.random.default_rng(seed), tm)
        if (x["guess"], x["n_checks"], x["sequence"]) != (y["guess"], y["n_checks"], y["sequence"]) or not np.isclose(x["minutes"], y["minutes"]):
            return False, f"episode {seed} differs between `off` and Settings()"
    ok, detail = SR.gate_g1_real(layout)
    return ok, f"{n} episodes identical; {detail}"


def gate_habits_independent(layout: Building, n: int = 20) -> tuple[bool, str]:
    """The stand-in habits give identical results whatever state the case holds (they never read `p_wrong`)."""
    room = sorted(layout.claims["vav_zone"])[0]
    real = real_case(layout, room, "X3", "p30", "R_narrow")
    tm = {c.name: c for c in real.settings.menu("vav_zone")}
    rng = np.random.default_rng(3)
    for seed in range(n):
        t = sim.sample_truth(real, rng)
        for h in HABITS:
            runs = [S.RUNNERS[h](assumed_case(layout, room, "R_narrow", st), t, np.random.default_rng(seed), tm) for st in STATES]
            if any((x["guess"], x["sequence"]) != (runs[0]["guess"], runs[0]["sequence"]) or not np.isclose(x["minutes"], runs[0]["minutes"]) for x in runs[1:]):
                return False, f"{h} differs across switch states at seed {seed}"
    return True, f"{n} episodes x {len(HABITS)} habits x {len(STATES)} states identical"


def g3_honesty_switch(results: list[dict]) -> tuple[bool, dict]:
    """In X0, accuracy among CONCLUDED `entropy` episodes (mean over the buildings) is at least G3_MIN for `off` in the 15%-wrong world and for `on` in the 5%-wrong world, in each regime."""
    vals = {}
    for state, world in (("off", "p15"), ("on", RIGHT_WORLD)):
        for reg in REGIMES:
            accs = []
            for x in results:
                c = x["cell"]
                if (c.condition, c.world, c.regime) == ("X0", world, reg):
                    p = x["policy"][tool_name(state)]
                    accs.append(float(p["correct"][p["concluded"]].mean()) if p["concluded"].any() else float("nan"))
            vals[(state, world, reg)] = float(np.mean(accs)) if accs else float("nan")
    return bool(vals) and all(np.isfinite(v) and v >= G3_MIN for v in vals.values()), vals


def g5_complete_switch(results: list[dict], n_cells: int = 600, expected_idx: list[int] | None = None) -> tuple[bool, str]:
    """All expected cells present, every policy finite, identical (room, cause) draws across the five policies of a cell."""
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
