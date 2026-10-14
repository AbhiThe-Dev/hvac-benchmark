"""Does telling the tool how far to trust the drawings make it better? (PREREGISTRATION_DR.md Addendum 21.) Layouts real (Mortar Brick metadata); errors and answers simulated.

The technician's one-word rating of a building's drawings sets the tool's prior that the documented box is wrong (`model.DRAWINGS`). A cell is (world, regime, building); the world is the
TRUE P(documented feeder wrong). In every cell the same 500 (room, cause) episodes are run by `entropy` under each of the three ratings and by the two stand-in habits, which never read
the rating. Everything not stated here (regimes, layouts, TRUE accounting, bootstrap, classification of the tool against the habits) is that of Addenda 19 and 20.
"""

from __future__ import annotations

import itertools
import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

import numpy as np

from . import model as M
from . import sim
from . import study as S
from . import study_real as SR
from .building import Building, make_case
from .realmaps import REGIME_CAPS, layout_problems  # noqa: F401  (re-exported for the script)

SEED = 21
N_EPISODES = 500
BOOT_B = 1000
RATINGS = tuple(M.DRAWINGS)                       # mostly_right, mixed, poor
BASE = "mixed"                                    # the default prior: the tool as it was
REGIMES = REGIME_CAPS
WORLDS = {f"p{int(round(100 * p)):02d}": S.Cell(0, p, 0.15, 0.25, "assumed", "assumed") for p in (0.05, 0.10, 0.15, 0.22, 0.30)}
PRIMARY = ("p05", "p15", "p30")
MATCHED = {"p05": "mostly_right", "p15": "mixed", "p30": "poor"}
POLICIES = tuple(f"entropy@{r}" for r in RATINGS) + S.HABITS
HABITS = S.HABITS
TIME_R, ACC_TOL, SAFE_TOL = 0.05, 0.02, 0.02
SCENARIOS = {"S1": ("p05", "mostly_right"), "S2": ("p30", "poor"), "S3": ("p15", "mostly_right"), "S4": ("p30", "mostly_right"), "S5": ("p15", "poor"), "S6": ("p05", "poor")}
MATCHED_SCENARIOS = ("S1", "S2")
SECONDARY = (("p10", "mostly_right"), ("p10", "poor"), ("p22", "mostly_right"), ("p22", "poor"))
G3_MIN = 0.92
Q_GRID = [1 / 3] + [round(0.34 + 0.01 * i, 2) for i in range(67)]     # 1/3, 0.34, ..., 1.00
Q_REPORT = (1 / 3, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
Q_BAR = 0.75
METRICS = ("d_min", "d_acc", "d_wc", "d_checks")


def tool_name(rating: str) -> str:
    return f"entropy@{rating}"


@dataclass(frozen=True)
class RatingCell:
    world: str
    regime: str
    building: str


def all_rating_cells(buildings: list[str]) -> list[RatingCell]:
    """Lexicographic: world outermost (0.05, 0.10, 0.15, 0.22, 0.30), then regime, then building (in the order given)."""
    return [RatingCell(w, r, b) for w, r, b in itertools.product(WORLDS, REGIMES, buildings)]


def assumed_case(layout: Building, room: str, regime: str, rating: str):
    return make_case(layout, room, "vav_zone", M.Settings().with_drawings(rating), max_candidates=REGIMES[regime])


def real_case(layout: Building, room: str, world: str, regime: str):
    return make_case(layout, room, "vav_zone", S.true_settings(WORLDS[world]), max_candidates=REGIMES[regime])


# ---------------------------------------------------------------------------------------------- one cell
def run_rating_cell(idx: int, spec: RatingCell, layout: Building, n: int = N_EPISODES) -> dict:
    """`n` episodes per policy on the same `n` (room, cause) draws (seed [SEED, idx]). The three ratings share the outcome stream [SEED, idx, 0, episode]; habit_A uses stream 1 and habit_B
    stream 2. Raw arrays only."""
    true_menu = {c.name: c for c in S.true_settings(WORLDS[spec.world]).menu("vav_zone")}
    rooms = sorted(layout.claims["vav_zone"])
    cases, reals = {}, {}

    def assumed(room, rating):
        if (room, rating) not in cases:
            cases[(room, rating)] = assumed_case(layout, room, spec.regime, rating)
        return cases[(room, rating)]

    def real(room):
        if room not in reals:
            reals[room] = real_case(layout, room, spec.world, spec.regime)
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
            rating, stream, runner = name.split("@")[1], 0, (lambda c, t, r, m: S.run_tool(c, t, r, m, "entropy"))
        else:
            rating, stream, runner = BASE, 1 + HABITS.index(name), S.RUNNERS[name]                 # the habits never read the rating: they run on the default case
        rows = [runner(assumed(room, rating), t, np.random.default_rng([SEED, idx, stream, i]), true_menu) for i, (room, t) in enumerate(picks)]
        out["policy"][name] = dict(
            truth_idx=np.array([causes(room).index(t) for room, t in picks]), guess_idx=np.array([causes(room).index(r["guess"]) for (room, _), r in zip(picks, rows)]),
            minutes=np.array([r["minutes"] for r in rows], float), checks=np.array([r["n_checks"] for r in rows], float),
            concluded=np.array([r["concluded"] for r in rows], bool), correct=np.array([r["correct"] for r in rows], bool))
    return out


def _run_args(args):
    return run_rating_cell(*args)


def compute_rating_cells(jobs: list[tuple[int, RatingCell, Building]], n: int = N_EPISODES, workers: int | None = None) -> list[dict]:
    """Deterministic whatever the number of workers."""
    args = [(i, c, lay, n) for i, c, lay in jobs]
    workers = workers if workers is not None else min(8, os.cpu_count() or 1)
    if workers <= 1 or len(args) == 1:
        return [_run_args(a) for a in args]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_run_args, args, chunksize=1))


# ---------------------------------------------------------------------------------------------- labels
def time_state(r_min: float, ci_min: tuple[float, float]) -> str:
    if r_min <= -TIME_R and ci_min[1] < 0:
        return "FASTER"
    if r_min >= TIME_R and ci_min[0] > 0:
        return "SLOWER"
    return "SAME"


def acc_state(d_acc: float, ci_acc: tuple[float, float]) -> str:
    if d_acc >= ACC_TOL and ci_acc[0] > 0:
        return "MORE"
    if d_acc <= -ACC_TOL and ci_acc[1] < 0:
        return "LESS"
    return "SAME"


def label(t: str, a: str) -> str:
    """IMPROVES = (FASTER and not LESS) or (MORE and not SLOWER); WORSE = (SLOWER and not MORE) or (LESS and not FASTER); TRADE = (FASTER and LESS) or (SLOWER and MORE)."""
    if (t == "FASTER" and a == "LESS") or (t == "SLOWER" and a == "MORE"):
        return "TRADE"
    if (t == "FASTER" and a != "LESS") or (a == "MORE" and t != "SLOWER"):
        return "IMPROVES"
    if (t == "SLOWER" and a != "MORE") or (a == "LESS" and t != "FASTER"):
        return "WORSE"
    return "NEITHER"


def safety_flag(d_wc: float, ci_wc: tuple[float, float]) -> str:
    if d_wc >= SAFE_TOL and ci_wc[0] > 0:
        return "REGRESSION"
    if d_wc <= -SAFE_TOL and ci_wc[1] < 0:
        return "GAIN"
    return "NONE"


def analyze_rating_cell(res: dict, B: int = BOOT_B) -> dict:
    n = res["n"]
    boot = np.random.default_rng([SEED, res["idx"], 99]).integers(0, n, (B, n))
    summ = S.summarize(res)
    pol = res["policy"]
    wc = {p: (v["concluded"] & ~v["correct"]).astype(float) for p, v in pol.items()}
    base = tool_name(BASE)
    cmp_ = {}
    for r in RATINGS:
        if r == BASE:
            continue
        t = tool_name(r)
        d_min, d_acc = pol[t]["minutes"] - pol[base]["minutes"], pol[t]["correct"].astype(float) - pol[base]["correct"].astype(float)
        d_wc, d_chk = wc[t] - wc[base], pol[t]["checks"] - pol[base]["checks"]
        ci_min, ci_acc, ci_wc = S.paired_ci(d_min, boot), S.paired_ci(d_acc, boot), S.paired_ci(d_wc, boot)
        r_min = float(d_min.mean() / summ[base]["minutes"])
        ts, as_ = time_state(r_min, ci_min), acc_state(float(d_acc.mean()), ci_acc)
        cmp_[r] = dict(d_min=float(d_min.mean()), r_min=r_min, d_acc=float(d_acc.mean()), d_wc=float(d_wc.mean()), d_checks=float(d_chk.mean()), ci_min=ci_min, ci_acc=ci_acc, ci_wc=ci_wc,
                       time=ts, acc=as_, label=label(ts, as_), safety=safety_flag(float(d_wc.mean()), ci_wc))
    ctx = {}                                                              # each rating's tool against each habit (Addendum 19's rule; context only)
    for r in RATINGS:
        t, labs = tool_name(r), []
        for h in HABITS:
            d_min, d_acc = pol[t]["minutes"] - pol[h]["minutes"], pol[t]["correct"].astype(float) - pol[h]["correct"].astype(float)
            ci_min, ci_acc = S.paired_ci(d_min, boot), S.paired_ci(d_acc, boot)
            lab, flag = S.classify_pair(summ[t]["minutes"], summ[h]["minutes"], summ[t]["accuracy"], summ[h]["accuracy"], ci_min)
            entry = dict(label=lab, tradeoff=flag, r_min=float(d_min.mean() / summ[h]["minutes"]), d_acc=float(d_acc.mean()), ci_min=ci_min, ci_acc=ci_acc)
            entry["secondary"] = SR.secondary_label(entry)
            ctx[f"{r}|{h}"] = entry
            labs.append(lab)
        ctx[r] = S.combine(labs)
    return dict(idx=res["idx"], cell=res["cell"], summary=summ, cmp=cmp_, ctx=ctx)


# ---------------------------------------------------------------------------------------------- scenarios, break-even, predictions
def scenario_cells(analyses: list[dict], world: str, regime: str | None = None) -> list[dict]:
    return [a for a in analyses if a["cell"].world == world and (regime is None or a["cell"].regime == regime)]


def fractions(cells: list[dict], rating: str) -> dict:
    """Shares of cells by label, the safety flags and the cost share (WORSE, TRADE or a safety regression)."""
    n = max(len(cells), 1)
    labs = [a["cmp"][rating]["label"] for a in cells]
    safe = [a["cmp"][rating]["safety"] for a in cells]
    out = {k: labs.count(k) / n for k in ("IMPROVES", "WORSE", "TRADE", "NEITHER")}
    out["SAFETY_REGRESSION"] = safe.count("REGRESSION") / n
    out["SAFETY_GAIN"] = safe.count("GAIN") / n
    out["COST"] = sum(1 for a in cells if a["cmp"][rating]["label"] in ("WORSE", "TRADE") or a["cmp"][rating]["safety"] == "REGRESSION") / n
    return out


def matched_reading(fr: dict) -> str:
    return S.map_reading(fr["IMPROVES"], fr["WORSE"])


def harm_reading(fr: dict) -> str:
    if fr["COST"] > 0.25:
        return "HARMFUL"
    return "HARMLESS" if fr["COST"] <= 0.10 else "COSTS SOMETHING"


def mean_delta(cells: list[dict], rating: str) -> dict:
    """Mean over the buildings (cells) of the per-cell paired mean differences to the default rating; zero for the default rating itself."""
    if rating == BASE:
        return {k: 0.0 for k in METRICS}
    return {k: float(np.mean([a["cmp"][rating][k] for a in cells])) for k in METRICS}


def deltas_by_regime(analyses: list[dict]) -> dict:
    """{regime: {(world, rating): mean deltas}} for the primary worlds."""
    return {reg: {(w, r): mean_delta(scenario_cells(analyses, w, reg), r) for w in PRIMARY for r in RATINGS} for reg in REGIMES}


def expected_change(delta: dict, q: float, worlds: tuple = PRIMARY) -> dict:
    """Expected change against always using the default rating when the technician rates correctly with probability q and otherwise picks either other level with equal
    probability, the worlds equally weighted. `delta[(world, rating)]` = mean deltas."""
    out = {k: 0.0 for k in METRICS}
    for w in worlds:
        m = MATCHED[w]
        others = [r for r in RATINGS if r != m]
        for k in METRICS:
            out[k] += (q * delta[(w, m)][k] + (1 - q) / len(others) * sum(delta[(w, r)][k] for r in others)) / len(worlds)
    return out


def favourable(ch: dict, metric: str | None = None, tol: float = 1e-12) -> bool:
    """Minutes not above, accuracy not below and wrong-and-confident not above the default's (one metric alone if named: 'd_min', 'd_acc', 'd_wc')."""
    ok = {"d_min": ch["d_min"] <= tol, "d_acc": ch["d_acc"] >= -tol, "d_wc": ch["d_wc"] <= tol}
    return ok[metric] if metric else all(ok.values())


def break_even(delta: dict, metric: str | None = None) -> dict:
    """{'q_star': smallest favourable q on Q_GRID or None, 'q_max': largest, 'at_one': favourable at q = 1}."""
    good = [q for q in Q_GRID if favourable(expected_change(delta, q), metric)]
    return dict(q_star=min(good) if good else None, q_max=max(good) if good else None, at_one=1.0 in good)


def decision(readings: dict, be: dict) -> str:
    """WORTH OFFERING if S1 and S2 read at least HELPS IN PART, the joint q* is at most Q_BAR in both regimes and q = 1 is favourable; otherwise NOT WORTH OFFERING AS BUILT."""
    ok = all(readings[s] != "DOES NOT HELP" for s in MATCHED_SCENARIOS)
    ok = ok and all(be[reg]["q_star"] is not None and be[reg]["q_star"] <= Q_BAR and be[reg]["at_one"] for reg in REGIMES)
    return "WORTH OFFERING" if ok else "NOT WORTH OFFERING AS BUILT"


def rating_predictions(analyses: list[dict]) -> dict:
    """P1-P5 as registered before the run; each strict, both regimes."""
    dl = deltas_by_regime(analyses)
    d = lambda reg, s: dl[reg][SCENARIOS[s]]  # noqa: E731
    p1 = {reg: (d(reg, "S1")["d_min"], d(reg, "S1")["d_acc"]) for reg in REGIMES}
    p2 = {reg: (d(reg, "S2")["d_wc"], d(reg, "S2")["d_acc"]) for reg in REGIMES}
    p3 = {reg: d(reg, "S4")["d_wc"] for reg in REGIMES}
    p4 = {reg: d(reg, "S6")["d_min"] for reg in REGIMES}
    p5 = {reg: expected_change(dl[reg], 0.70) for reg in REGIMES}
    return dict(P1=dict(holds=all(m < 0 and a >= -0.01 for m, a in p1.values()), values=p1), P2=dict(holds=all(w < 0 and a >= 0 for w, a in p2.values()), values=p2),
                P3=dict(holds=all(v >= 0.02 for v in p3.values()), values=p3), P4=dict(holds=all(v > 0 for v in p4.values()), values=p4),
                P5=dict(holds=all(favourable(c) for c in p5.values()), values={reg: (c["d_min"], c["d_acc"], c["d_wc"]) for reg, c in p5.items()}))


# ---------------------------------------------------------------------------------------------- gates
def _paired_layout_case(layout: Building, rating: str, regime: str = "R_narrow"):
    room = sorted(layout.claims["vav_zone"])[0]
    return assumed_case(layout, room, regime, rating), real_case(layout, room, "p15", regime)


def gate_g1_default_off(layout: Building, n: int = 30) -> tuple[bool, str]:
    """G1: the default rating is the default (settings and whole episodes identical) and the runners reproduce `sim.simulate` (Addendum 20's G1)."""
    if M.Settings().with_drawings(BASE) != M.Settings():
        return False, "with_drawings('mixed') differs from Settings()"
    room = sorted(layout.claims["vav_zone"])[0]
    a, real = _paired_layout_case(layout, BASE)
    b = make_case(layout, room, "vav_zone", M.Settings(), max_candidates=REGIMES["R_narrow"])
    tm = {c.name: c for c in real.settings.menu("vav_zone")}
    rng = np.random.default_rng(1)
    for seed in range(n):
        t = sim.sample_truth(real, rng)
        x, y = S.run_tool(a, t, np.random.default_rng(seed), tm), S.run_tool(b, t, np.random.default_rng(seed), tm)
        if (x["guess"], x["n_checks"], x["sequence"]) != (y["guess"], y["n_checks"], y["sequence"]) or not np.isclose(x["minutes"], y["minutes"]):
            return False, f"episode {seed} differs between the default rating and Settings()"
    ok, detail = SR.gate_g1_real(layout)
    return ok, f"{n} episodes identical; {detail}"


def gate_habits_independent(layout: Building, n: int = 20) -> tuple[bool, str]:
    """The stand-in habits give identical results whatever rating the case holds (they never read `p_wrong`)."""
    room = sorted(layout.claims["vav_zone"])[0]
    real = real_case(layout, room, "p15", "R_narrow")
    tm = {c.name: c for c in real.settings.menu("vav_zone")}
    rng = np.random.default_rng(3)
    for seed in range(n):
        t = sim.sample_truth(real, rng)
        for h in HABITS:
            runs = [S.RUNNERS[h](assumed_case(layout, room, "R_narrow", r), t, np.random.default_rng(seed), tm) for r in RATINGS]
            if any((x["guess"], x["sequence"]) != (runs[0]["guess"], runs[0]["sequence"]) or not np.isclose(x["minutes"], runs[0]["minutes"]) for x in runs[1:]):
                return False, f"{h} differs across ratings at seed {seed}"
    return True, f"{n} episodes x {len(HABITS)} habits x {len(RATINGS)} ratings identical"


def g3_honesty_rating(results: list[dict]) -> tuple[bool, dict]:
    """With the MATCHED rating in each primary world, accuracy among CONCLUDED `entropy` episodes (mean over the buildings) is at least G3_MIN in each (world, regime) group."""
    vals = {}
    for w in PRIMARY:
        for reg in REGIMES:
            accs = []
            for x in results:
                if x["cell"].world == w and x["cell"].regime == reg:
                    p = x["policy"][tool_name(MATCHED[w])]
                    accs.append(float(p["correct"][p["concluded"]].mean()) if p["concluded"].any() else float("nan"))
            vals[(w, reg)] = float(np.mean(accs)) if accs else float("nan")
    return bool(vals) and all(np.isfinite(v) and v >= G3_MIN for v in vals.values()), vals


def g5_complete_rating(results: list[dict], n_cells: int = 250, expected_idx: list[int] | None = None) -> tuple[bool, str]:
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
