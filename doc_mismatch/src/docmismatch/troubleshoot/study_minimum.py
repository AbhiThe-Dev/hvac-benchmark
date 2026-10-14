"""How does the tool do with only the minimum data it needs, and how does it compare with the two stand-in habits there? (PREREGISTRATION_DR.md Addendum 23.) Layouts real (Mortar Brick
metadata); errors and answers simulated.

Level `min`: the equipment list and the drawings' claims only: no area for any box, so the candidate list is the documented box then the other boxes in identifier order, capped at K, all with
equal weight. Level `grouped`: Addendum 20's setting (same air handler first, weights 1 and 0.25). The TRUE cause is drawn over ALL boxes of the building; a wrong feeder that is not on the
tool's list is, from the tool's side, the cause "unlisted". A cell is (world, cap, building); the three policies run at both levels on the same draws.
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
from . import study_rating as SG
from . import study_real as SR
from .building import Building, Equipment, make_case
from .realmaps import layout_problems  # noqa: F401  (re-exported for the script)

SEED = 23
N_EPISODES = 300
BOOT_B = 1000
CAPS = {"K8": 8, "K40": 40}
WORLD_NEAR = {"local": 0.25, "anywhere": 1.0}                     # where a wrong feeder lies: same air handler counts 1, another 0.25 | anywhere equally
WORLDS = tuple(WORLD_NEAR)
LEVELS = ("min", "grouped")
KINDS = ("entropy", "habit_A", "habit_B")
STREAM = {"entropy": 0, "habit_A": 1, "habit_B": 2}
POLICIES = tuple(f"{k}@{lv}" for k in KINDS for lv in LEVELS)
UNLISTED = ("unlisted",)
P_WRONG, P_ACT = 0.15, 0.15


def name_of(kind: str, level: str) -> str:
    return f"{kind}@{level}"


def world_cell(world: str) -> S.Cell:
    return S.Cell(0, P_WRONG, P_ACT, WORLD_NEAR[world], "assumed", "assumed")


@dataclass(frozen=True)
class MinCell:
    world: str
    cap: str
    building: str


def all_min_cells(buildings: list[str]) -> list[MinCell]:
    """Lexicographic: world outermost (local, anywhere), then cap (K8, K40), then building (in the order given)."""
    return [MinCell(w, c, b) for w, c, b in itertools.product(WORLDS, CAPS, buildings)]


def strip_areas(b: Building) -> Building:
    """The minimum-data version of a building: the same equipment and claims, no area for any box."""
    return Building(b.name, {k: Equipment(e.id, e.kind, None, e.tag) for k, e in b.equipment.items()}, {s: dict(m) for s, m in b.claims.items()})


def level_layout(layout: Building, level: str) -> Building:
    if level == "grouped":
        return layout
    if level == "min":
        return strip_areas(layout)
    raise ValueError(f"unknown level {level!r}")


def n_boxes(layout: Building) -> int:
    return sum(1 for e in layout.equipment.values() if e.kind == "VAV")


def assumed_case(layout: Building, room: str, cap: str, level: str):
    return make_case(level_layout(layout, level), room, "vav_zone", M.Settings(), max_candidates=CAPS[cap])


def full_case(layout: Building, room: str, world: str):
    """The case with the TRUE numbers and EVERY box of the building as a candidate: the truth is drawn from it."""
    return make_case(layout, room, "vav_zone", S.true_settings(world_cell(world)), max_candidates=n_boxes(layout))


def draw_picks(idx: int, spec: MinCell, layout: Building, n: int) -> list[tuple[str, M.Cause]]:
    """The `n` (room, cause) draws of a cell (seed [SEED, idx]); the cause is drawn over all boxes of the building."""
    rooms = sorted(layout.claims["vav_zone"])
    cases, rng, picks = {}, np.random.default_rng([SEED, idx]), []
    for _ in range(n):
        room = rooms[int(rng.integers(len(rooms)))]
        if room not in cases:
            cases[room] = full_case(layout, room, spec.world)
        picks.append((room, sim.sample_truth(cases[room], rng)))
    return picks


def is_off_list(truth: M.Cause, candidates: list[str]) -> bool:
    """A wrong feeder that the tool's candidate list does not contain."""
    return truth[0] == "wrong" and truth[1] not in candidates


# ---------------------------------------------------------------------------------------------- one cell
def run_min_cell(idx: int, spec: MinCell, layout: Building, n: int = N_EPISODES) -> dict:
    """`n` episodes per policy on the same `n` (room, cause) draws. The two levels of a policy share the outcome stream [SEED, idx, STREAM[kind], episode]. Raw arrays only."""
    true_menu = {c.name: c for c in S.true_settings(world_cell(spec.world)).menu("vav_zone")}
    picks = draw_picks(idx, spec, layout, n)
    rooms = sorted(layout.claims["vav_zone"])
    lay = {lv: level_layout(layout, lv) for lv in LEVELS}
    cache = {}

    def assumed(room, level):
        if (room, level) not in cache:
            case = make_case(lay[level], room, "vav_zone", M.Settings(), max_candidates=CAPS[spec.cap])
            cache[(room, level)] = (case, M.make_prior("vav_zone", case.candidates, case.doc, case.settings, None, case.weights)[0])
        return cache[(room, level)]

    out = dict(idx=idx, cell=spec, n=n, rooms=len(rooms), boxes=n_boxes(layout), room_idx=np.array([rooms.index(r) for r, _ in picks]),
               truth_kind=np.array([t[0] for _, t in picks]), K=np.array([len(assumed(r, "grouped")[0].candidates) for r, _ in picks], float), policy={})
    for name in POLICIES:
        kind, level = name.split("@")
        runner = (lambda c, t, r, m: S.run_tool(c, t, r, m, "entropy")) if kind == "entropy" else S.RUNNERS[kind]
        truth_idx, guess_idx, off, rows = [], [], [], []
        for i, (room, truth) in enumerate(picks):
            case, causes = assumed(room, level)
            o = is_off_list(truth, case.candidates)
            mapped = UNLISTED if o else truth
            rows.append(runner(case, mapped, np.random.default_rng([SEED, idx, STREAM[kind], i]), true_menu))
            truth_idx.append(causes.index(mapped))
            guess_idx.append(causes.index(rows[-1]["guess"]))
            off.append(o)
        out["policy"][name] = dict(
            truth_idx=np.array(truth_idx), guess_idx=np.array(guess_idx), minutes=np.array([r["minutes"] for r in rows], float), checks=np.array([r["n_checks"] for r in rows], float),
            concluded=np.array([r["concluded"] for r in rows], bool), correct=np.array([r["correct"] for r in rows], bool), off_list=np.array(off, bool),
            named=np.array([r["guess"] != UNLISTED for r in rows], bool))
    return out


def _run_args(args):
    return run_min_cell(*args)


def compute_min_cells(jobs: list[tuple[int, MinCell, Building]], n: int = N_EPISODES, workers: int | None = None) -> list[dict]:
    """Deterministic whatever the number of workers."""
    args = [(i, c, lay, n) for i, c, lay in jobs]
    workers = workers if workers is not None else min(8, os.cpu_count() or 1)
    if workers <= 1 or len(args) == 1:
        return [_run_args(a) for a in args]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_run_args, args, chunksize=1))


# ---------------------------------------------------------------------------------------------- analysis of one cell
def summarize_min(res: dict) -> dict:
    """`study.summarize` plus the two new metrics: `actionable` (correct and names a cause) and `off_list` (the true wrong feeder is not on the list)."""
    out = S.summarize(res)
    for name, p in res["policy"].items():
        out[name]["actionable"] = float((p["correct"] & p["named"]).mean())
        out[name]["off_list"] = float(p["off_list"].mean())
    return out


def analyze_min_cell(res: dict, B: int = BOOT_B) -> dict:
    """`entropy` against each habit within a level (Addendum 19's rule and Addendum 20's BUYS ACCURACY; context) and, for the tool, level grouped against level min (Addendum 21's labels)."""
    n = res["n"]
    boot = np.random.default_rng([SEED, res["idx"], 99]).integers(0, n, (B, n))
    summ = summarize_min(res)
    pol = res["policy"]
    ctx = {}
    for lv in LEVELS:
        t, labs = name_of("entropy", lv), []
        for h in ("habit_A", "habit_B"):
            hn = name_of(h, lv)
            d_min, d_acc = pol[t]["minutes"] - pol[hn]["minutes"], pol[t]["correct"].astype(float) - pol[hn]["correct"].astype(float)
            ci_min, ci_acc = S.paired_ci(d_min, boot), S.paired_ci(d_acc, boot)
            lab, flag = S.classify_pair(summ[t]["minutes"], summ[hn]["minutes"], summ[t]["accuracy"], summ[hn]["accuracy"], ci_min)
            entry = dict(label=lab, tradeoff=flag, r_min=float(d_min.mean() / summ[hn]["minutes"]), d_acc=float(d_acc.mean()), ci_min=ci_min, ci_acc=ci_acc)
            entry["secondary"] = SR.secondary_label(entry)
            ctx[f"{lv}|{h}"] = entry
            labs.append(lab)
        ctx[lv] = S.combine(labs)
    g, m = pol[name_of("entropy", "grouped")], pol[name_of("entropy", "min")]
    d_min, d_acc = g["minutes"] - m["minutes"], g["correct"].astype(float) - m["correct"].astype(float)
    d_act = (g["correct"] & g["named"]).astype(float) - (m["correct"] & m["named"]).astype(float)
    d_off = g["off_list"].astype(float) - m["off_list"].astype(float)
    ci_min, ci_acc = S.paired_ci(d_min, boot), S.paired_ci(d_acc, boot)
    r_min = float(d_min.mean() / summ[name_of("entropy", "min")]["minutes"])
    ts, as_ = SG.time_state(r_min, ci_min), SG.acc_state(float(d_acc.mean()), ci_acc)
    grp = dict(d_min=float(d_min.mean()), r_min=r_min, d_acc=float(d_acc.mean()), d_act=float(d_act.mean()), d_off=float(d_off.mean()), ci_min=ci_min, ci_acc=ci_acc, time=ts, acc=as_, label=SG.label(ts, as_))
    return dict(idx=res["idx"], cell=res["cell"], summary=summ, ctx=ctx, grp=grp)


# ---------------------------------------------------------------------------------------------- groups and predictions
def group_cells(analyses: list[dict], world: str, cap: str) -> list[dict]:
    return [a for a in analyses if a["cell"].world == world and a["cell"].cap == cap]


def gmean(cells: list[dict], policy: str, key: str) -> float:
    return float(np.mean([a["summary"][policy][key] for a in cells]))


def min_predictions(analyses: list[dict]) -> dict:
    """P1-P5 as registered before the run; each strict, means over the buildings of a group."""
    grp = {(w, c): group_cells(analyses, w, c) for w in WORLDS for c in CAPS}
    tm, tg = name_of("entropy", "min"), name_of("entropy", "grouped")
    p1 = {c: (gmean(grp[("local", c)], tm, "off_list"), gmean(grp[("local", c)], tg, "off_list"), gmean(grp[("local", c)], tm, "minutes"), gmean(grp[("local", c)], tg, "minutes")) for c in CAPS}
    p2 = {c: (gmean(grp[("anywhere", c)], tm, "minutes"), gmean(grp[("anywhere", c)], tg, "minutes"), gmean(grp[("anywhere", c)], tm, "off_list"), gmean(grp[("anywhere", c)], tg, "off_list")) for c in CAPS}
    p3 = {c: gmean(grp[("anywhere", c)], tm, "off_list") for c in CAPS}
    p4 = {k: (gmean(v, tm, "accuracy"), gmean(v, name_of("habit_A", "min"), "accuracy")) for k, v in grp.items()}
    p5 = {k: (gmean(v, tm, "minutes"), gmean(v, name_of("habit_B", "min"), "minutes")) for k, v in grp.items()}
    return dict(P1=dict(holds=all(om > og and mm > mg for om, og, mm, mg in p1.values()), values=p1),
                P2=dict(holds=all(abs(mm - mg) <= 0.10 * mg and abs(om - og) <= 0.02 for mm, mg, om, og in p2.values()), values=p2),
                P3=dict(holds=p3["K8"] >= 0.08 and p3["K40"] < p3["K8"], values=p3), P4=dict(holds=all(a > b for a, b in p4.values()), values=p4),
                P5=dict(holds=all(a < b for a, b in p5.values()), values=p5))


# ---------------------------------------------------------------------------------------------- gates
def one_area(layout: Building) -> Building:
    """Every box (and zone) hangs on the same air handler: grouping carries no information."""
    return Building(layout.name, {k: Equipment(e.id, e.kind, "A", e.tag) for k, e in layout.equipment.items()}, {s: dict(m) for s, m in layout.claims.items()})


def gate_g1_min(layout: Building, n: int = 30) -> tuple[bool, str]:
    """G1: with no grouping information the two levels give identical episodes (every policy), and the runners reproduce `sim.simulate` (Addendum 20's G1)."""
    flat = one_area(layout)
    room = sorted(flat.claims["vav_zone"])[0]
    real = make_case(flat, room, "vav_zone", S.true_settings(world_cell("local")), max_candidates=8)
    tm = {c.name: c for c in real.settings.menu("vav_zone")}
    rng = np.random.default_rng(1)
    for seed in range(n):
        t = sim.sample_truth(real, rng)
        for kind in KINDS:
            runner = (lambda c, tr, r, m: S.run_tool(c, tr, r, m, "entropy")) if kind == "entropy" else S.RUNNERS[kind]
            a, b = (runner(assumed_case(flat, room, "K8", lv), t, np.random.default_rng(seed), tm) for lv in LEVELS)
            if (a["guess"], a["sequence"]) != (b["guess"], b["sequence"]) or not np.isclose(a["minutes"], b["minutes"]):
                return False, f"{kind} differs between the levels without grouping information at seed {seed}"
    ok, detail = SR.gate_g1_real(layout)
    return ok, f"{n} episodes x {len(KINDS)} policies identical across levels; {detail}"


def gate_g3_coverage(results: list[dict], layouts: dict[str, Building]) -> tuple[bool, str]:
    """G3: recomputed from the stored seeds, the off-list flags equal a direct count for every policy of every cell, every mapped truth is a valid cause, and the off-list share is exactly 0
    wherever the building has at most K boxes."""
    for r in results:
        spec, lay = r["cell"], layouts[r["cell"].building]
        picks = draw_picks(r["idx"], spec, lay, r["n"])
        for name, p in r["policy"].items():
            level = name.split("@")[1]
            want = np.array([is_off_list(t, assumed_case(lay, room, spec.cap, level).candidates) for room, t in picks])
            if not np.array_equal(p["off_list"], want):
                return False, f"cell {r['idx']} {name}: off-list flags differ from a direct count"
            if p["truth_idx"].min() < 0:
                return False, f"cell {r['idx']} {name}: a truth is not a cause of the tool"
            if r["boxes"] <= CAPS[spec.cap] and p["off_list"].any():
                return False, f"cell {r['idx']} {name}: off-list episodes in a building with at most K boxes"
    return True, f"{len(results)} cells recomputed"


def g5_complete_min(results: list[dict], n_cells: int = 100, expected_idx: list[int] | None = None) -> tuple[bool, str]:
    """All expected cells present, every policy finite and of full length, one set of (room, cause) draws per cell (every policy saw the same rooms and the same kinds of truth)."""
    want = list(range(n_cells)) if expected_idx is None else sorted(expected_idx)
    if len(results) != len(want) or sorted(r["idx"] for r in results) != want:
        return False, f"{len(results)} cells present, expected {len(want)}"
    for r in results:
        if set(r["policy"]) != set(POLICIES):
            return False, f"cell {r['idx']}: policies {sorted(r['policy'])}"
        if len(r["room_idx"]) != r["n"] or len(r["truth_kind"]) != r["n"]:
            return False, f"cell {r['idx']}: draws of the wrong length"
        wrong = r["truth_kind"] == "wrong"
        for name, p in r["policy"].items():
            if not np.isfinite(p["minutes"]).all() or len(p["minutes"]) != r["n"] or len(p["off_list"]) != r["n"]:
                return False, f"cell {r['idx']} {name}: non-finite or short arrays"
            if (p["off_list"] & ~wrong).any():
                return False, f"cell {r['idx']} {name}: off-list episodes that are not wrong-feeder truths"
    return True, "ok"
