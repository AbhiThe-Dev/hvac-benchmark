"""The troubleshooting tool on real documented layouts (PREREGISTRATION_DR.md Addendum 20). The layouts are real (Mortar Brick models); the errors and the technician's answers are simulated.

A cell is (world, regime, building). Policies, TRUE accounting, classification and the paired bootstrap are those of `study.py` (Addendum 19); this module adds the worlds, the two
candidate regimes, the runner over real layouts, one secondary label ("BUYS ACCURACY"), group readings, the predictions and the gates.
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
from .building import Building, make_case
from .realmaps import REGIME_CAPS, layout_problems  # noqa: F401  (re-exported for the script)

SEED = 20
N_EPISODES = 500
REGIMES = REGIME_CAPS
WORLDS = {"W_default": S.Cell(0, 0.15, 0.15, 0.25, "assumed", "assumed"), "W_documented": S.Cell(0, 0.05, 0.15, 0.25, "assumed", "assumed"),
          "W_stress": S.Cell(0, 0.30, 0.30, 0.25, "degraded", "assumed")}
G3_MIN = 0.92
ACC_BUY_R, ACC_BUY_D = 0.10, 0.05


@dataclass(frozen=True)
class RealCell:
    world: str
    regime: str
    building: str


def all_real_cells(buildings: list[str]) -> list[RealCell]:
    """Lexicographic: world outermost, then regime, then building (in the order given)."""
    return [RealCell(w, r, b) for w, r, b in itertools.product(WORLDS, REGIMES, buildings)]


def cases_for(layout: Building, room: str, world: str, regime: str):
    """(the case as the tool believes it, the case with the TRUE numbers) for one room."""
    cap = REGIMES[regime]
    return (make_case(layout, room, "vav_zone", M.Settings(), max_candidates=cap), make_case(layout, room, "vav_zone", S.true_settings(WORLDS[world]), max_candidates=cap))


def run_real_cell(idx: int, spec: RealCell, layout: Building, n: int = N_EPISODES) -> dict:
    """`n` episodes per policy on the same `n` (room, cause) draws (seed [SEED, idx]); outcome draws use [SEED, idx, policy, episode]. Raw arrays only."""
    true_menu = {c.name: c for c in S.true_settings(WORLDS[spec.world]).menu("vav_zone")}
    rooms = sorted(layout.claims["vav_zone"])
    cache = {}

    def get(room):
        if room not in cache:
            assumed, real = cases_for(layout, room, spec.world, spec.regime)
            cache[room] = (assumed, real, M.make_prior("vav_zone", assumed.candidates, assumed.doc, assumed.settings, None, assumed.weights)[0])
        return cache[room]

    rng = np.random.default_rng([SEED, idx])
    picks = []
    for _ in range(n):
        room = rooms[int(rng.integers(len(rooms)))]
        picks.append((room, sim.sample_truth(get(room)[1], rng)))
    out = dict(idx=idx, cell=spec, n=n, rooms=len(rooms), boxes=len({b for b in layout.claims["vav_zone"].values()}), K=np.array([len(get(r)[0].candidates) for r, _ in picks], float), policy={})
    for pi, name in enumerate(S.POLICIES):
        rows = [S.RUNNERS[name](get(room)[0], t, np.random.default_rng([SEED, idx, pi, i]), true_menu) for i, (room, t) in enumerate(picks)]
        out["policy"][name] = dict(
            truth_idx=np.array([get(room)[2].index(t) for room, t in picks]), guess_idx=np.array([get(room)[2].index(r["guess"]) for (room, _), r in zip(picks, rows)]),
            minutes=np.array([r["minutes"] for r in rows], float), checks=np.array([r["n_checks"] for r in rows], float),
            concluded=np.array([r["concluded"] for r in rows], bool), correct=np.array([r["correct"] for r in rows], bool))
    return out


def _run_args(args):
    return run_real_cell(*args)


def compute_real_cells(jobs: list[tuple[int, RealCell, Building]], n: int = N_EPISODES, workers: int | None = None) -> list[dict]:
    """Deterministic whatever the number of workers."""
    args = [(i, c, lay, n) for i, c, lay in jobs]
    workers = workers if workers is not None else min(8, os.cpu_count() or 1)
    if workers <= 1 or len(args) == 1:
        return [_run_args(a) for a in args]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_run_args, args, chunksize=1))


# ---------------------------------------------------------------------------------------------- secondary label and group readings
def secondary_label(entry: dict) -> str:
    """WINS / LOSES / NEITHER as in Addendum 19, except that a cell that is neither is BUYS ACCURACY when the tool takes at least 10% more minutes, is at least 0.05 more accurate and
    the paired interval of the accuracy difference lies above 0."""
    if entry["label"] != "NEITHER":
        return entry["label"]
    return "BUYS ACCURACY" if entry["r_min"] >= ACC_BUY_R and entry["d_acc"] >= ACC_BUY_D and entry["ci_acc"][0] > 0 else "NEITHER"


def groups(analyses: list[dict]) -> dict:
    """{(world, regime): [analysis, ...]} in the order the cells were run."""
    out = {}
    for a in analyses:
        out.setdefault((a["cell"].world, a["cell"].regime), []).append(a)
    return out


def group_reading(group: list[dict], tool: str) -> tuple[float, float, str]:
    w, l = S.map_fractions([a["label"][tool] for a in group])
    return w, l, S.map_reading(w, l)


def _wins_vs(group: list[dict], tool: str, habit: str) -> float:
    return S.map_fractions([a["cmp"][f"{tool}|{habit}"]["label"] for a in group])[0]


def real_predictions(analyses: list[dict]) -> dict:
    """P1-P5 as registered before the run; each strict."""
    g = groups(analyses)
    pool = lambda keys: [a for k in keys for a in g[k]]  # noqa: E731
    mean = lambda grp, pol, key: float(np.mean([a["summary"][pol][key] for a in grp]))  # noqa: E731
    p1v = {k: group_reading(g[k], "entropy")[0] for k in g if k[0] in ("W_default", "W_stress")}
    w_by_world = {w: _wins_vs(pool([(w, r) for r in REGIMES]), "entropy", "habit_B") for w in WORLDS}
    w_by_regime = {r: _wins_vs(pool([(w, r) for w in WORLDS]), "entropy", "habit_B") for r in REGIMES}
    p4 = {r: (mean(g[("W_stress", r)], "entropy", "wrong_confident"), mean(g[("W_default", r)], "entropy", "wrong_confident")) for r in REGIMES}
    p5 = {k: (mean(v, "entropy", "accuracy"), mean(v, "habit_A", "accuracy")) for k, v in g.items()}
    return dict(P1=dict(holds=all(v == 0.0 for v in p1v.values()), values=p1v),
                P2=dict(holds=w_by_world["W_documented"] > max(w_by_world["W_default"], w_by_world["W_stress"]), values=w_by_world),
                P3=dict(holds=w_by_regime["R_wide"] > w_by_regime["R_narrow"], values=w_by_regime),
                P4=dict(holds=all(a > b for a, b in p4.values()), values=p4), P5=dict(holds=all(a > b for a, b in p5.values()), values=p5))


# ---------------------------------------------------------------------------------------------- gates
def g3_honesty_real(results: list[dict]) -> tuple[bool, dict]:
    """In W_default, accuracy among CONCLUDED `entropy` episodes, averaged over the buildings, is at least G3_MIN in each regime."""
    vals = {}
    for r in REGIMES:
        accs = []
        for x in results:
            if x["cell"].world == "W_default" and x["cell"].regime == r:
                p = x["policy"]["entropy"]
                accs.append(float(p["correct"][p["concluded"]].mean()) if p["concluded"].any() else float("nan"))
        vals[r] = float(np.mean(accs)) if accs else float("nan")
    return bool(vals) and all(np.isfinite(v) and v >= G3_MIN for v in vals.values()), vals


def _real_case_pair(layout: Building, world_cell: S.Cell = WORLDS["W_default"]):
    room = sorted(layout.claims["vav_zone"])[0]
    assumed = make_case(layout, room, "vav_zone", M.Settings(), max_candidates=8)
    real = make_case(layout, room, "vav_zone", S.true_settings(world_cell), max_candidates=8)
    return assumed, real, {c.name: c for c in real.settings.menu("vav_zone")}


def gate_g1_real(layout: Building, n: int = 30) -> tuple[bool, str]:
    """G1: with truth = assumptions the runners reproduce `sim.simulate` / `sim.simulate_habit` exactly on a real-layout case."""
    assumed, real, tm = _real_case_pair(layout)
    rng = np.random.default_rng(0)
    for seed in range(n):
        t = sim.sample_truth(real, rng)
        for strat in S.TOOL:
            a, b = S.run_tool(assumed, t, np.random.default_rng(seed), tm, strat), sim.simulate(assumed, t, strat, np.random.default_rng(seed))
            if (a["guess"], a["n_checks"], a["concluded"]) != (b["guess"], b["n_checks"], b["concluded"]) or not np.isclose(a["minutes"], b["minutes"]):
                return False, f"{strat} differs from sim.simulate at seed {seed}"
        a, b = S.run_habit_A(assumed, t, np.random.default_rng(seed), tm), sim.simulate_habit(assumed, t, np.random.default_rng(seed))
        if (a["guess"], a["n_checks"]) != (b["guess"], b["n_checks"]) or not np.isclose(a["minutes"], b["minutes"]):
            return False, f"habit_A differs from sim.simulate_habit at seed {seed}"
    return True, f"{n} episodes x 4 runners identical"


def gate_g2_real(layout: Building, n: int = 20) -> tuple[bool, str]:
    """G2: true minutes are charged as hand-summed and never change which check is chosen or what is answered."""
    assumed, real, tm1 = _real_case_pair(layout)
    tm3 = {c.name: c for c in S.true_settings(replace(WORLDS["W_default"], costs="access_x3")).menu("vav_zone")}
    rng = np.random.default_rng(2)
    for seed in range(n):
        t = sim.sample_truth(real, rng)
        for pol in S.POLICIES:
            a, b = S.RUNNERS[pol](assumed, t, np.random.default_rng(seed), tm1), S.RUNNERS[pol](assumed, t, np.random.default_rng(seed), tm3)
            at, tot = None, 0.0
            for name, tgt in b["sequence"]:
                tot += tm3[name].minutes(at, tgt)
                at = tgt
            if a["sequence"] != b["sequence"] or a["guess"] != b["guess"] or not np.isclose(tot, b["minutes"]) or not b["minutes"] > a["minutes"]:
                return False, f"{pol} seed {seed}"
    return True, f"{n} episodes x {len(S.POLICIES)} policies"
