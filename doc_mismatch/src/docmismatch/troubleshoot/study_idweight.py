"""Does weighting the candidates by their distance in id order make the tool find wrong feeders that an equal-weight id-neighbour list cannot, and is it harmless where errors are not
id-local? (PREREGISTRATION_DR.md Addendum 25.) Cached Mortar Brick metadata and simulation only.

Levels: `min` (Addendum 23), `idnear` (Addendum 24: the id-near list, equal weights), `idw2` / `idw4` / `idw8` (the same list produced by the tool's `nearness = "id"` option with
`id_decay` 2 / 4 / 8) and `grouped` (Addendum 20). Worlds: Addendum 24's four plus `idlocal4`. The adjacency worlds are ASSUMED and favour the id levels by construction.
"""

from __future__ import annotations

import itertools
import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, replace

import numpy as np

from . import idproximity as ID
from . import model as M
from . import sim
from . import study as S
from . import study_minimum as SM
from . import study_real as SR
from .building import Building, make_case
from .realmaps import layout_problems  # noqa: F401  (re-exported for the script)

SEED = 23
N_EPISODES = 300
BOOT_B = 1000
CAPS = SM.CAPS
WORLDS = ("local", "anywhere", "idlocal2", "idlocal8", "idlocal4")
DECAY = {"idlocal2": 2.0, "idlocal8": 8.0, "idlocal4": 4.0}                # the ASSUMED adjacency worlds
ADJACENCY = ("idlocal2", "idlocal4", "idlocal8")
TOOL_DECAY = {"idw2": 2.0, "idw4": 4.0, "idw8": 8.0}                        # the tool's `id_decay`
PRIMARY = "idw4"
LEVELS = ("min", "idnear", "idw2", "idw4", "idw8", "grouped")
POLICIES = tuple(f"entropy@{lv}" for lv in LEVELS)
PAIRS = (("idnear", "min"), ("grouped", "min"), ("idw2", "idnear"), ("idw4", "idnear"), ("idw8", "idnear"), ("idw4", "min"))   # (treatment, baseline)


def name_of(level: str) -> str:
    return f"entropy@{level}"


@dataclass(frozen=True)
class IdwCell:
    world: str
    cap: str
    building: str


def all_idw_cells(buildings: list[str]) -> list[IdwCell]:
    """Lexicographic: world outermost (local, anywhere, idlocal2, idlocal8, idlocal4: the first 200 cells are Addendum 24's), then cap, then building (in the order given)."""
    return [IdwCell(w, c, b) for w, c, b in itertools.product(WORLDS, CAPS, buildings)]


def assumed_case(layout: Building, room: str, cap: str, level: str):
    """The case as the tool sees it at one level. The `idw` levels use the tool's own `nearness = "id"` option."""
    if level in TOOL_DECAY:
        return make_case(layout, room, "vav_zone", M.Settings(nearness="id", id_decay=TOOL_DECAY[level]), max_candidates=SM.CAPS[cap])
    return ID.assumed_case(layout, room, cap, level)


def world_weights(layout: Building, room: str, world: str) -> dict[str, float]:
    """The weight of each box (except the documented one) as the TRUE feeder of `room` when the documented feeder is wrong."""
    if world in DECAY:
        rk, doc = ID.ranks(layout), layout.claims["vav_zone"][room]
        return {b: float(np.exp(-abs(rk[b] - rk[doc]) / DECAY[world])) for b in rk if b != doc}
    return ID.world_weights(layout, room, world)


def draw_picks(idx: int, spec: IdwCell, layout: Building, n: int) -> list[tuple[str, M.Cause]]:
    """The `n` (room, cause) draws of a cell (seed [SEED, idx]); the cause is drawn over all boxes of the building with the world's weights."""
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


def run_idw_cell(idx: int, spec: IdwCell, layout: Building, n: int = N_EPISODES) -> dict:
    """`n` episodes per policy on the same `n` (room, cause) draws; all levels share the outcome stream [SEED, idx, 0, episode]. Raw arrays only."""
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
    return run_idw_cell(*args)


def compute_idw_cells(jobs: list[tuple[int, IdwCell, Building]], n: int = N_EPISODES, workers: int | None = None) -> list[dict]:
    """Deterministic whatever the number of workers."""
    args = [(i, c, lay, n) for i, c, lay in jobs]
    workers = workers if workers is not None else min(8, os.cpu_count() or 1)
    if workers <= 1 or len(args) == 1:
        return [_run_args(a) for a in args]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_run_args, args, chunksize=1))


# ---------------------------------------------------------------------------------------------- analysis of one cell
def analyze_idw_cell(res: dict, B_: int = BOOT_B) -> dict:
    """Each treatment against its baseline on the same episodes (Addendum 21's labels): `cmp["idw4|idnear"]` etc."""
    n = res["n"]
    boot = np.random.default_rng([SEED, res["idx"], 99]).integers(0, n, (B_, n))
    summ = SM.summarize_min(res)
    return dict(idx=res["idx"], cell=res["cell"], summary=summ, cmp={f"{t}|{b}": ID._compare(res["policy"], boot, summ, name_of(t), name_of(b)) for t, b in PAIRS})


# ---------------------------------------------------------------------------------------------- groups, predictions, decision
def group_cells(analyses: list[dict], world: str, cap: str) -> list[dict]:
    return [a for a in analyses if a["cell"].world == world and a["cell"].cap == cap]


def gmean(cells: list[dict], level: str, key: str) -> float:
    return float(np.mean([a["summary"][name_of(level)][key] for a in cells]))


def idw_predictions(analyses: list[dict]) -> dict:
    """P1-P6 as registered before the run; each strict; means over the buildings of a group."""
    g = lambda w, c: group_cells(analyses, w, c)  # noqa: E731
    m = lambda w, c, lv, k: gmean(g(w, c), lv, k)  # noqa: E731
    p1 = {w: (m(w, "K40", PRIMARY, "actionable"), m(w, "K40", "idnear", "actionable")) for w in ADJACENCY}
    p2 = {w: (m(w, "K40", PRIMARY, "actionable"), m(w, "K40", "min", "actionable")) for w in ("idlocal2", "idlocal4")}
    p3 = {c: (m("anywhere", c, PRIMARY, "actionable"), m("anywhere", c, "min", "actionable"), m("anywhere", c, PRIMARY, "wrong_confident"), m("anywhere", c, "min", "wrong_confident")) for c in CAPS}
    p4 = {c: (m("local", c, PRIMARY, "actionable"), m("local", c, "idnear", "actionable")) for c in CAPS}
    p5 = {w: (m(w, "K40", "idw2", "actionable"), m(w, "K40", "idw8", "actionable"), m(w, "K40", "idnear", "actionable")) for w in ADJACENCY}
    p6 = {(w, c): (m(w, c, PRIMARY, "wrong_confident"), m(w, c, "idnear", "wrong_confident")) for w in WORLDS for c in CAPS}
    return dict(P1=dict(holds=all(a > b for a, b in p1.values()), values=p1), P2=dict(holds=all(a >= b + 0.04 for a, b in p2.values()), values=p2),
                P3=dict(holds=all(abs(a - b) <= 0.01 and wa - wb <= 0.01 for a, b, wa, wb in p3.values()), values=p3),
                P4=dict(holds=all(a >= b - 0.005 for a, b in p4.values()), values=p4), P5=dict(holds=all(a > i and b > i for a, b, i in p5.values()), values=p5),
                P6=dict(holds=all(a - b <= 0.01 for a, b in p6.values()), values=p6))


def decision(predictions: dict) -> str:
    """WORTH KEEPING AS AN OPTION if P1, P3 and P6 all hold; otherwise NOT WORTH KEEPING. P2, P4 and P5 carry no verdict."""
    return "WORTH KEEPING AS AN OPTION" if all(predictions[k]["holds"] for k in ("P1", "P3", "P6")) else "NOT WORTH KEEPING"


# ---------------------------------------------------------------------------------------------- gates
def gate_g1_idw(layout: Building, n: int = 20) -> tuple[bool, str]:
    """G1 (part): the tool's id-mode case has Addendum 24's id-near list and weights exp(-|rank difference| / lambda) for every room, cap and lambda; the defaults are unchanged; the runners
    reproduce `sim.simulate`."""
    if M.Settings().nearness != "area" or M.Settings().id_decay != 4.0:
        return False, "the default settings changed"
    rk = ID.ranks(layout)
    for room in sorted(layout.claims["vav_zone"]):
        doc = layout.claims["vav_zone"][room]
        plain = make_case(layout, room, "vav_zone", M.Settings(), max_candidates=8)
        area = make_case(layout, room, "vav_zone", M.Settings(nearness="area"), max_candidates=8)
        if (plain.candidates, plain.weights) != (area.candidates, area.weights):
            return False, f"{room}: nearness='area' differs from the default"
        for cap, k in SM.CAPS.items():
            for lv, lam in TOOL_DECAY.items():
                case = assumed_case(layout, room, cap, lv)
                if case.candidates != ID.id_near_list(layout, doc, k):
                    return False, f"{room}/{cap}/{lv}: candidates differ from Addendum 24's id-near list"
                if any(not np.isclose(case.weights[c], np.exp(-abs(rk[c] - rk[doc]) / lam)) for c in case.candidates):
                    return False, f"{room}/{cap}/{lv}: weights differ from exp(-distance / lambda)"
    ok, detail = SR.gate_g1_real(layout, n=n)
    return ok, f"id-mode cases of {len(layout.claims['vav_zone'])} rooms x {len(SM.CAPS)} caps x {len(TOOL_DECAY)} decays checked; {detail}"


def gate_g1_a24(results: list[dict], a24: list[dict]) -> tuple[bool, str]:
    """G1 (part): the `min`, `idnear` and `grouped` levels of every cell that Addendum 24 also ran reproduce its stored episodes exactly."""
    ref = {r["idx"]: r for r in a24}
    keys = ("minutes", "checks", "guess_idx", "truth_idx", "off_list", "named")
    checked = 0
    for r in results:
        if r["idx"] not in ref:
            continue
        a = ref[r["idx"]]
        if (a["cell"].world, a["cell"].cap, a["cell"].building) != (r["cell"].world, r["cell"].cap, r["cell"].building):
            return False, f"cell {r['idx']} is not the same cell as in Addendum 24"
        for lv in ("min", "idnear", "grouped"):
            for key in keys:
                if not np.array_equal(r["policy"][name_of(lv)][key], a["policy"][name_of(lv)][key]):
                    return False, f"cell {r['idx']} {lv}: {key} differs from Addendum 24"
        checked += 1
    return checked > 0, f"{checked} cells reproduce Addendum 24 exactly"


def wrong_feeder_distance(results: list[dict], layouts: dict[str, Building]) -> dict[str, float]:
    """{world: mean absolute rank distance between the documented box and the drawn wrong feeder, over all drawn wrong feeders of the world}."""
    tot, cnt = {}, {}
    for r in results:
        spec, lay = r["cell"], layouts[r["cell"].building]
        rk = ID.ranks(lay)
        for room, t in draw_picks(r["idx"], spec, lay, r["n"]):
            if t[0] == "wrong":
                tot[spec.world] = tot.get(spec.world, 0.0) + abs(rk[t[1]] - rk[lay.claims["vav_zone"][room]])
                cnt[spec.world] = cnt.get(spec.world, 0) + 1
    return {w: tot[w] / cnt[w] for w in tot}


def gate_g3(results: list[dict], layouts: dict[str, Building]) -> tuple[bool, str]:
    """G3: off-list flags equal a direct count recomputed from the seeds for every policy of every cell, every mapped truth is a cause, the off-list share is exactly 0 wherever the building has at
    most K boxes, and the drawn wrong feeders are ordered by rank distance as they should be (idlocal2 < idlocal4 < idlocal8 < anywhere)."""
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
    dist = wrong_feeder_distance(results, layouts)
    order = [dist.get(w) for w in ("idlocal2", "idlocal4", "idlocal8", "anywhere")]
    if any(d is None for d in order) or not all(a < b for a, b in zip(order, order[1:])):
        return False, f"the drawn wrong feeders are not ordered by rank distance: {dist}"
    return True, f"{len(results)} cells recomputed; mean rank distance of a wrong feeder " + ", ".join(f"{w} {dist[w]:.1f}" for w in ("idlocal2", "idlocal4", "idlocal8", "anywhere"))


def g5_complete_idw(results: list[dict], n_cells: int = 250, expected_idx: list[int] | None = None) -> tuple[bool, str]:
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
