"""Do the identifiers of real campus buildings carry location information, and how much would a candidate list built from id neighbours recover of the wrong feeders that the
minimum-data list misses? (PREREGISTRATION_DR.md Addendum 24.) Cached Mortar Brick metadata and simulation only.

Part A (descriptive): name consistency of the documented claims and the air-handler lift of id neighbours. Part B: exact coverage of wrong feeders by three candidate lists (`min` = first K
boxes of the equipment list, `idnear` = the K - 1 nearest boxes in natural id order, `grouped` = same air handler first) in four worlds, and the tool's outcomes on the same episodes. The
first two worlds and the `min` / `grouped` levels are Addendum 23's; the adjacency worlds (`idlocal2`, `idlocal8`) are ASSUMED and favour the id list by construction.
"""

from __future__ import annotations

import itertools
import os
import re
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, replace

import numpy as np

from . import model as M
from . import sim
from . import study as S
from . import study_minimum as SM
from . import study_rating as SG
from . import study_real as SR
from .building import Building
from .realmaps import layout_problems  # noqa: F401  (re-exported for the script)

SEED = 23
N_EPISODES = 300
BOOT_B = 1000
CAPS = SM.CAPS
WORLDS = ("local", "anywhere", "idlocal2", "idlocal8")
DECAY = {"idlocal2": 2.0, "idlocal8": 8.0}
LEVELS = ("min", "idnear", "grouped")
POLICIES = tuple(f"entropy@{lv}" for lv in LEVELS)
WRONG_LISTED = 0.15 * (1 - 0.10)                          # P(documented feeder wrong) x (1 - unlisted share): the visits with a wrong feeder that is a box
LIFT_K = 8


def name_of(level: str) -> str:
    return f"entropy@{level}"


@dataclass(frozen=True)
class IdCell:
    world: str
    cap: str
    building: str


def all_id_cells(buildings: list[str]) -> list[IdCell]:
    """Lexicographic: world outermost (local, anywhere, idlocal2, idlocal8), then cap (K8, K40), then building (in the order given)."""
    return [IdCell(w, c, b) for w, c, b in itertools.product(WORLDS, CAPS, buildings)]


# ---------------------------------------------------------------------------------------------- natural order and id-near lists
def natural_key(s: str) -> tuple:
    """Digit runs compare as integers, other runs case-insensitively."""
    return tuple((0, int(t), "") if t.isdigit() else (1, 0, t.upper()) for t in re.findall(r"\d+|\D+", s))


def boxes_in_id_order(layout: Building) -> list[str]:
    return sorted((e.id for e in layout.equipment.values() if e.kind == "VAV"), key=lambda b: (natural_key(b), b))


def ranks(layout: Building) -> dict[str, int]:
    return {b: i for i, b in enumerate(boxes_in_id_order(layout))}


def id_near_list(layout: Building, doc: str, k: int) -> list[str]:
    """The documented box, then the k - 1 other boxes with the smallest absolute rank difference from it (ties: the lower rank first)."""
    rk = ranks(layout)
    others = sorted((b for b in rk if b != doc), key=lambda b: (abs(rk[b] - rk[doc]), rk[b]))
    return [doc] + others[: k - 1]


def assumed_case(layout: Building, room: str, cap: str, level: str):
    """The case as the tool sees it at one level: min and grouped are Addendum 23's; idnear replaces the candidate list of `min` by the id-near list (equal weights)."""
    if level in ("min", "grouped"):
        return SM.assumed_case(layout, room, cap, level)
    if level == "idnear":
        base = SM.assumed_case(layout, room, cap, "min")
        cands = id_near_list(layout, base.doc, SM.CAPS[cap])
        return replace(base, candidates=cands, weights={c: 1.0 for c in cands})
    raise ValueError(f"unknown level {level!r}")


# ---------------------------------------------------------------------------------------------- worlds and exact coverage
def world_weights(layout: Building, room: str, world: str) -> dict[str, float]:
    """The weight of each box (except the documented one) as the TRUE feeder of `room` when the documented feeder is wrong."""
    if world in SM.WORLD_NEAR:
        full = SM.full_case(layout, room, world)
        return {c: float(full.weights[c]) for c in full.candidates if c != full.doc}
    if world not in DECAY:
        raise ValueError(f"unknown world {world!r}")
    rk, doc = ranks(layout), layout.claims["vav_zone"][room]
    return {b: float(np.exp(-abs(rk[b] - rk[doc]) / DECAY[world])) for b in rk if b != doc}


def coverage_table(layout: Building) -> dict[tuple[str, str, str], float]:
    """{(world, cap, level): mean over the rooms of the share of the wrong-feeder weight that lies on the list} (each room equally likely, as in the episodes)."""
    acc = {(w, c, lv): [] for w in WORLDS for c in CAPS for lv in LEVELS}
    for room in sorted(layout.claims["vav_zone"]):
        weights = {w: world_weights(layout, room, w) for w in WORLDS}
        for c in CAPS:
            for lv in LEVELS:
                case = assumed_case(layout, room, c, lv)
                for w in WORLDS:
                    total = sum(weights[w].values())
                    acc[(w, c, lv)].append(sum(weights[w][b] for b in case.candidates if b != case.doc) / total if total > 0 else 1.0)
    return {k: float(np.mean(v)) for k, v in acc.items()}


def expected_off_list(coverage: float) -> float:
    return WRONG_LISTED * (1.0 - coverage)


# ---------------------------------------------------------------------------------------------- Part A: what the identifiers carry
def name_consistency(pairs: list[tuple[str, str]]) -> tuple[int, int]:
    """(claims whose zone id, upper-cased, is a substring of the box id, upper-cased ; claims)."""
    return sum(1 for box, zone in pairs if zone.upper() in box.upper()), len(pairs)


def handler_lift(layout: Building, k: int = LIFT_K) -> dict | None:
    """For a building with at least 2 documented handlers: over the boxes that have a handler, the share of the k - 1 id-nearest boxes on the same handler (`s_id`), the same for the first k - 1
    boxes of the equipment order (`s_first`), the share a random list would give (`base`), and the lift `s_id / base`. None if there is only one handler (or none)."""
    rk = ranks(layout)
    plain = [e.id for e in layout.equipment.values() if e.kind == "VAV"]
    handler = {b: layout.equipment[b].area for b in rk}
    handled = [b for b in rk if handler[b] is not None]
    counts = Counter(handler[b] for b in handled)
    if len(counts) < 2:
        return None
    plain_handled = [b for b in plain if handler[b] is not None]
    s_id, s_first, base = [], [], []
    for d in handled:
        near = sorted((b for b in handled if b != d), key=lambda b: (abs(rk[b] - rk[d]), rk[b]))[: k - 1]
        first = [b for b in plain_handled if b != d][: k - 1]
        s_id.append(float(np.mean([handler[b] == handler[d] for b in near])))
        s_first.append(float(np.mean([handler[b] == handler[d] for b in first])))
        base.append((counts[handler[d]] - 1) / (len(handled) - 1))
    m_id, m_first, m_base = float(np.mean(s_id)), float(np.mean(s_first)), float(np.mean(base))
    return dict(s_id=m_id, s_first=m_first, base=m_base, lift=m_id / m_base if m_base > 0 else float("nan"), n_handled=len(handled), n_handlers=len(counts), full=len(handled) <= k)


# ---------------------------------------------------------------------------------------------- simulation
def draw_picks(idx: int, spec: IdCell, layout: Building, n: int) -> list[tuple[str, M.Cause]]:
    """The `n` (room, cause) draws of a cell (seed [SEED, idx]); the cause is drawn over all boxes of the building with the world's weights. The first two worlds are Addendum 23's draws."""
    if spec.world in SM.WORLD_NEAR:
        return SM.draw_picks(idx, spec, layout, n)
    rooms = sorted(layout.claims["vav_zone"])
    cases, rng, picks = {}, np.random.default_rng([SEED, idx]), []
    for _ in range(n):
        room = rooms[int(rng.integers(len(rooms)))]
        if room not in cases:
            full = SM.full_case(layout, room, "local")
            cases[room] = replace(full, weights={**world_weights(layout, room, spec.world), full.doc: 1.0})
        picks.append((room, sim.sample_truth(cases[room], rng)))
    return picks


def run_id_cell(idx: int, spec: IdCell, layout: Building, n: int = N_EPISODES) -> dict:
    """`n` episodes per policy on the same `n` (room, cause) draws; the three levels share the outcome stream [SEED, idx, 0, episode]. Raw arrays only."""
    true_menu = {c.name: c for c in S.true_settings(SM.world_cell("local")).menu("vav_zone")}
    picks = draw_picks(idx, spec, layout, n)
    rooms = sorted(layout.claims["vav_zone"])
    cache = {}

    def assumed(room, level):
        if (room, level) not in cache:
            case = assumed_case(layout, room, spec.cap, level)
            cache[(room, level)] = (case, M.make_prior("vav_zone", case.candidates, case.doc, case.settings, None, case.weights)[0])
        return cache[(room, level)]

    out = dict(idx=idx, cell=spec, n=n, rooms=len(rooms), boxes=SM.n_boxes(layout), room_idx=np.array([rooms.index(r) for r, _ in picks]), truth_kind=np.array([t[0] for _, t in picks]), policy={})
    for name in POLICIES:
        level = name.split("@")[1]
        truth_idx, guess_idx, off, rows = [], [], [], []
        for i, (room, truth) in enumerate(picks):
            case, causes = assumed(room, level)
            o = SM.is_off_list(truth, case.candidates)
            mapped = SM.UNLISTED if o else truth
            rows.append(S.run_tool(case, mapped, np.random.default_rng([SEED, idx, 0, i]), true_menu, "entropy"))
            truth_idx.append(causes.index(mapped))
            guess_idx.append(causes.index(rows[-1]["guess"]))
            off.append(o)
        out["policy"][name] = dict(
            truth_idx=np.array(truth_idx), guess_idx=np.array(guess_idx), minutes=np.array([r["minutes"] for r in rows], float), checks=np.array([r["n_checks"] for r in rows], float),
            concluded=np.array([r["concluded"] for r in rows], bool), correct=np.array([r["correct"] for r in rows], bool), off_list=np.array(off, bool),
            named=np.array([r["guess"] != SM.UNLISTED for r in rows], bool))
    return out


def _run_args(args):
    return run_id_cell(*args)


def compute_id_cells(jobs: list[tuple[int, IdCell, Building]], n: int = N_EPISODES, workers: int | None = None) -> list[dict]:
    """Deterministic whatever the number of workers."""
    args = [(i, c, lay, n) for i, c, lay in jobs]
    workers = workers if workers is not None else min(8, os.cpu_count() or 1)
    if workers <= 1 or len(args) == 1:
        return [_run_args(a) for a in args]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_run_args, args, chunksize=1))


# ---------------------------------------------------------------------------------------------- analysis of one cell
def _compare(pol: dict, boot: np.ndarray, summ: dict, treat: str, base: str) -> dict:
    t, m = pol[treat], pol[base]
    d_min, d_acc = t["minutes"] - m["minutes"], t["correct"].astype(float) - m["correct"].astype(float)
    d_act = (t["correct"] & t["named"]).astype(float) - (m["correct"] & m["named"]).astype(float)
    d_off = t["off_list"].astype(float) - m["off_list"].astype(float)
    ci_min, ci_acc = S.paired_ci(d_min, boot), S.paired_ci(d_acc, boot)
    r_min = float(d_min.mean() / summ[base]["minutes"])
    ts, as_ = SG.time_state(r_min, ci_min), SG.acc_state(float(d_acc.mean()), ci_acc)
    return dict(d_min=float(d_min.mean()), r_min=r_min, d_acc=float(d_acc.mean()), d_act=float(d_act.mean()), d_off=float(d_off.mean()), ci_min=ci_min, ci_acc=ci_acc, time=ts, acc=as_, label=SG.label(ts, as_))


def analyze_id_cell(res: dict, B: int = BOOT_B) -> dict:
    """`idnear` and `grouped` against `min` on the same episodes (Addendum 21's labels)."""
    n = res["n"]
    boot = np.random.default_rng([SEED, res["idx"], 99]).integers(0, n, (B, n))
    summ = SM.summarize_min(res)
    base = name_of("min")
    return dict(idx=res["idx"], cell=res["cell"], summary=summ, cmp={lv: _compare(res["policy"], boot, summ, name_of(lv), base) for lv in ("idnear", "grouped")})


# ---------------------------------------------------------------------------------------------- groups and predictions
def group_cells(analyses: list[dict], world: str, cap: str) -> list[dict]:
    return [a for a in analyses if a["cell"].world == world and a["cell"].cap == cap]


def gmean(cells: list[dict], level: str, key: str) -> float:
    return float(np.mean([a["summary"][name_of(level)][key] for a in cells]))


def mean_cov(cov: dict, world: str, cap: str, level: str) -> float:
    """Mean over the buildings of the exact coverage; `cov[(building, world, cap, level)]`."""
    return float(np.mean([v for (b, w, c, lv), v in cov.items() if (w, c, lv) == (world, cap, level)]))


def id_predictions(analyses: list[dict], part_a: dict, cov: dict) -> dict:
    """P1-P6 as registered before the run; each strict. `part_a[building] = dict(consistent, total, lift)` (lift None or the `handler_lift` dict)."""
    consistent, total = sum(v["consistent"] for v in part_a.values()), sum(v["total"] for v in part_a.values())
    lifts = [v["lift"] for v in part_a.values() if v["lift"] is not None and v["lift"]["n_handled"] > LIFT_K]
    beat = [x["s_id"] > x["s_first"] for x in lifts]
    p1 = consistent / total if total else float("nan")
    p2 = (float(np.mean(beat)) if beat else float("nan"), float(np.mean([x["lift"] for x in lifts])) if lifts else float("nan"), len(lifts))
    mc = lambda w, c, lv: mean_cov(cov, w, c, lv)  # noqa: E731
    p3 = {c: (mc("local", c, "min"), mc("local", c, "idnear"), mc("local", c, "grouped")) for c in CAPS}
    p4 = {c: (expected_off_list(mc("local", c, "min")), expected_off_list(mc("local", c, "grouped"))) for c in CAPS}
    p5 = (expected_off_list(mc("idlocal2", "K8", "idnear")), expected_off_list(mc("idlocal2", "K8", "min")))
    p6 = {(w, c): (gmean(group_cells(analyses, w, c), "idnear", "actionable"), gmean(group_cells(analyses, w, c), "min", "actionable")) for w in ("local", "idlocal2", "idlocal8") for c in CAPS}
    return dict(P1=dict(holds=bool(total) and p1 >= 0.90, values=p1),
                P2=dict(holds=bool(beat) and p2[0] >= 0.70 and p2[1] >= 1.5, values=p2),
                P3=dict(holds=all(a < b and b <= g for a, b, g in p3.values()), values=p3),
                P4=dict(holds=all(abs(a - g) <= 0.015 for a, g in p4.values()), values=p4),
                P5=dict(holds=p5[0] <= 0.4 * p5[1], values=p5),
                P6=dict(holds=all(i > m for i, m in p6.values()), values=p6))


# ---------------------------------------------------------------------------------------------- gates
def brute_force_near(layout: Building, doc: str, k: int) -> list[str]:
    """An independent implementation of the id-near list: repeatedly take the closest unused box by rank distance, the lower rank first."""
    order = boxes_in_id_order(layout)
    pos = {b: i for i, b in enumerate(order)}
    chosen, left = [doc], [b for b in order if b != doc]
    while left and len(chosen) < k:
        best = min(left, key=lambda b: (abs(pos[b] - pos[doc]), pos[b]))
        chosen.append(best)
        left.remove(best)
    return chosen


def gate_g1_idnear(layout: Building, n: int = 20) -> tuple[bool, str]:
    """G1 (part): every id-near list starts with the documented box, has no duplicates, has length min(K, boxes) and equals the brute-force list; the runners reproduce `sim.simulate`."""
    for room in sorted(layout.claims["vav_zone"]):
        doc = layout.claims["vav_zone"][room]
        for cap, k in SM.CAPS.items():
            got = assumed_case(layout, room, cap, "idnear").candidates
            if got[0] != doc or len(set(got)) != len(got) or len(got) != min(k, SM.n_boxes(layout)) or got != brute_force_near(layout, doc, k):
                return False, f"{room}/{cap}: the id-near list is wrong"
    ok, detail = SR.gate_g1_real(layout, n=n)
    return ok, f"id-near lists of {len(layout.claims['vav_zone'])} rooms x {len(SM.CAPS)} caps checked; {detail}"


def gate_g1_a23(results: list[dict], a23: list[dict]) -> tuple[bool, str]:
    """G1 (part): the `min` and `grouped` levels of every cell that Addendum 23 also ran reproduce its stored episodes exactly."""
    ref = {r["idx"]: r for r in a23}
    keys = ("minutes", "checks", "guess_idx", "truth_idx", "off_list", "named")
    checked = 0
    for r in results:
        if r["idx"] not in ref:
            continue
        a = ref[r["idx"]]
        if (a["cell"].world, a["cell"].cap, a["cell"].building) != (r["cell"].world, r["cell"].cap, r["cell"].building):
            return False, f"cell {r['idx']} is not the same cell as in Addendum 23"
        for lv in ("min", "grouped"):
            for key in keys:
                if not np.array_equal(r["policy"][name_of(lv)][key], a["policy"][name_of(lv)][key]):
                    return False, f"cell {r['idx']} {lv}: {key} differs from Addendum 23"
        checked += 1
    return checked > 0, f"{checked} cells reproduce Addendum 23 exactly"


def gate_g3_coverage(results: list[dict], layouts: dict[str, Building]) -> tuple[bool, str]:
    """G3 (part): off-list flags equal a direct count recomputed from the seeds for every policy of every cell, every mapped truth is a cause, and the off-list share is exactly 0 wherever the
    building has at most K boxes."""
    for r in results:
        spec, lay = r["cell"], layouts[r["cell"].building]
        picks = draw_picks(r["idx"], spec, lay, r["n"])
        for name, p in r["policy"].items():
            level = name.split("@")[1]
            want = np.array([SM.is_off_list(t, assumed_case(lay, room, spec.cap, level).candidates) for room, t in picks])
            if not np.array_equal(p["off_list"], want):
                return False, f"cell {r['idx']} {name}: off-list flags differ from a direct count"
            if p["truth_idx"].min() < 0:
                return False, f"cell {r['idx']} {name}: a truth is not a cause of the tool"
            if r["boxes"] <= SM.CAPS[spec.cap] and p["off_list"].any():
                return False, f"cell {r['idx']} {name}: off-list episodes in a building with at most K boxes"
    return True, f"{len(results)} cells recomputed"


def gate_g3_exact(cov: dict, a23: list[dict], tol: float = 0.01) -> tuple[bool, str]:
    """G3 (part): the exact expected off-list shares of `min` and `grouped` in the local and anywhere worlds agree with Addendum 23's simulated group means within `tol`."""
    worst = 0.0
    for w in ("local", "anywhere"):
        for c in CAPS:
            for lv in ("min", "grouped"):
                sims = [float(r["policy"][name_of(lv)]["off_list"].mean()) for r in a23 if (r["cell"].world, r["cell"].cap) == (w, c)]
                if not sims:
                    return False, f"no Addendum 23 cells for {w}/{c}"
                diff = abs(float(np.mean(sims)) - expected_off_list(mean_cov(cov, w, c, lv)))
                worst = max(worst, diff)
                if diff > tol:
                    return False, f"{w}/{c}/{lv}: exact and simulated off-list shares differ by {diff:.4f}"
    return True, f"largest difference {worst:.4f} (tolerance {tol})"


def g5_complete_id(results: list[dict], n_cells: int = 200, expected_idx: list[int] | None = None) -> tuple[bool, str]:
    """All expected cells present, every policy finite and of full length, one set of (room, cause) draws per cell."""
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
