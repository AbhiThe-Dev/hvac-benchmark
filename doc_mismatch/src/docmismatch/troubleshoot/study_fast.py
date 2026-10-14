"""How does the id-weighted tool compare with the fast trial-and-error stand-in when both get the same information? (PREREGISTRATION_DR.md Addendum 26.) Cached Mortar Brick metadata and
simulation only.

Six policies per cell: the tool on the arbitrary first-K list (`entropy@min`) and on the id-near list weighted by id distance (`entropy@idw4`), and the two stand-in habits, which read the
candidate ORDER only, on the first-K list (`@min`) and on the id-near list (`@idnear`, the tool's own candidates in the tool's order of distance). `habit_A` is the "fast technician".
Worlds, cells, draws and the true-cause mapping are Addendum 25's; the habits and their streams are Addendum 23's.
"""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from . import model as M
from . import sim
from . import study as S
from . import study_idweight as IW
from . import study_minimum as SM
from . import study_real as SR
from .building import Building
from .realmaps import layout_problems  # noqa: F401  (re-exported for the script)

SEED = 23
N_EPISODES = 300
BOOT_B = 1000
CAPS = SM.CAPS
WORLDS = IW.WORLDS
STREAM = {"entropy": 0, "habit_A": 1, "habit_B": 2}
POLICIES = ("entropy@min", "entropy@idw4", "habit_A@min", "habit_A@idnear", "habit_B@min", "habit_B@idnear")
TOOL, FAST, SLOW = "entropy@idw4", "habit_A@idnear", "habit_B@idnear"
# (tool, habit) pairs: (a) primary, same information; (b) context
PAIRS = ((TOOL, FAST), (TOOL, SLOW), ("entropy@min", "habit_A@min"), ("entropy@min", "habit_B@min"), (TOOL, "habit_A@min"), (TOOL, "habit_B@min"))
COMBOS = {"same information": (TOOL, (FAST, SLOW)), "arbitrary list": ("entropy@min", ("habit_A@min", "habit_B@min")), "tool with ids, technician without": (TOOL, ("habit_A@min", "habit_B@min"))}
GAINS = (("habit_A@idnear", "habit_A@min"), ("habit_B@idnear", "habit_B@min"))


FastCell = IW.IdwCell
all_fast_cells = IW.all_idw_cells


def assumed_case(layout: Building, room: str, cap: str, level: str):
    """min and idnear are Addenda 23-24's lists; idw4 is the tool's own id-weighted option (the same candidates as idnear)."""
    return IW.assumed_case(layout, room, cap, level)


# ---------------------------------------------------------------------------------------------- one cell
def run_fast_cell(idx: int, spec: FastCell, layout: Building, n: int = N_EPISODES) -> dict:
    """`n` episodes per policy on the same `n` (room, cause) draws (Addendum 25's); each kind of policy has its own outcome stream, shared by its levels. Raw arrays only."""
    true_menu = {c.name: c for c in S.true_settings(SM.world_cell("local")).menu("vav_zone")}
    picks = IW.draw_picks(idx, spec, layout, n)
    rooms = sorted(layout.claims["vav_zone"])
    cache = {}

    def assumed(room, level):
        if (room, level) not in cache:
            case = assumed_case(layout, room, spec.cap, level)
            cache[(room, level)] = (case, M.make_prior("vav_zone", case.candidates, case.doc, case.settings, None, case.weights)[0])
        return cache[(room, level)]

    out = dict(idx=idx, cell=spec, n=n, rooms=len(rooms), boxes=SM.n_boxes(layout), room_idx=np.array([rooms.index(r) for r, _ in picks]), truth_kind=np.array([t[0] for _, t in picks]), policy={})
    for name in POLICIES:
        kind, level = name.split("@")
        runner = (lambda c, t, r, m: S.run_tool(c, t, r, m, "entropy")) if kind == "entropy" else S.RUNNERS[kind]
        truth_idx, guess_idx, off, rows = [], [], [], []
        for i, (room, truth) in enumerate(picks):
            case, causes = assumed(room, level)
            o = SM.is_off_list(truth, case.candidates)
            mapped = SM.UNLISTED if o else truth
            rows.append(runner(case, mapped, np.random.default_rng([SEED, idx, STREAM[kind], i]), true_menu))
            truth_idx.append(causes.index(mapped))
            guess_idx.append(causes.index(rows[-1]["guess"]))
            off.append(o)
        out["policy"][name] = dict(
            truth_idx=np.array(truth_idx), guess_idx=np.array(guess_idx), minutes=np.array([r["minutes"] for r in rows], float), checks=np.array([r["n_checks"] for r in rows], float),
            concluded=np.array([r["concluded"] for r in rows], bool), correct=np.array([r["correct"] for r in rows], bool), off_list=np.array(off, bool),
            named=np.array([r["guess"] != SM.UNLISTED for r in rows], bool))
    return out


def _run_args(args):
    return run_fast_cell(*args)


def compute_fast_cells(jobs: list[tuple[int, FastCell, Building]], n: int = N_EPISODES, workers: int | None = None) -> list[dict]:
    """Deterministic whatever the number of workers."""
    args = [(i, c, lay, n) for i, c, lay in jobs]
    workers = workers if workers is not None else min(8, os.cpu_count() or 1)
    if workers <= 1 or len(args) == 1:
        return [_run_args(a) for a in args]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_run_args, args, chunksize=1))


# ---------------------------------------------------------------------------------------------- analysis of one cell
def analyze_fast_cell(res: dict, B: int = BOOT_B) -> dict:
    """Each tool policy against each habit with Addendum 19's classification and Addendum 20's BUYS ACCURACY label, the combination against both habits, and what each habit gains from the
    id list."""
    n = res["n"]
    boot = np.random.default_rng([SEED, res["idx"], 99]).integers(0, n, (B, n))
    summ = SM.summarize_min(res)
    pol = res["policy"]
    cmp_ = {}
    for t, h in PAIRS:
        d_min, d_acc = pol[t]["minutes"] - pol[h]["minutes"], pol[t]["correct"].astype(float) - pol[h]["correct"].astype(float)
        ci_min, ci_acc = S.paired_ci(d_min, boot), S.paired_ci(d_acc, boot)
        lab, flag = S.classify_pair(summ[t]["minutes"], summ[h]["minutes"], summ[t]["accuracy"], summ[h]["accuracy"], ci_min)
        entry = dict(label=lab, tradeoff=flag, r_min=float(d_min.mean() / summ[h]["minutes"]), d_min=float(d_min.mean()), d_acc=float(d_acc.mean()), ci_min=ci_min, ci_acc=ci_acc)
        entry["secondary"] = SR.secondary_label(entry)
        cmp_[f"{t}|{h}"] = entry
    combo = {k: S.combine([cmp_[f"{t}|{h}"]["label"] for h in hs]) for k, (t, hs) in COMBOS.items()}
    gain = {}
    for a, b in GAINS:
        d_min = pol[a]["minutes"] - pol[b]["minutes"]
        d_acc = pol[a]["correct"].astype(float) - pol[b]["correct"].astype(float)
        d_act = (pol[a]["correct"] & pol[a]["named"]).astype(float) - (pol[b]["correct"] & pol[b]["named"]).astype(float)
        gain[f"{a}|{b}"] = dict(d_min=float(d_min.mean()), d_acc=float(d_acc.mean()), d_act=float(d_act.mean()))
    return dict(idx=res["idx"], cell=res["cell"], summary=summ, cmp=cmp_, combo=combo, gain=gain)


# ---------------------------------------------------------------------------------------------- groups and predictions
def group_cells(analyses: list[dict], world: str, cap: str) -> list[dict]:
    return [a for a in analyses if a["cell"].world == world and a["cell"].cap == cap]


def gmean(cells: list[dict], policy: str, key: str) -> float:
    return float(np.mean([a["summary"][policy][key] for a in cells]))


def fast_predictions(analyses: list[dict]) -> dict:
    """P1-P5 as registered before the run; each strict; means over the buildings of a group; 'all groups' = the 10 (world, cap) groups."""
    groups = {(w, c): group_cells(analyses, w, c) for w in WORLDS for c in CAPS}
    m = lambda k, pol, key: gmean(groups[k], pol, key)  # noqa: E731
    p1 = {k: (m(k, FAST, "minutes"), m(k, TOOL, "minutes")) for k in groups}
    p2 = {k: (m(k, TOOL, "accuracy"), m(k, FAST, "accuracy")) for k in groups}
    p3 = {k: (m(k, TOOL, "wrong_confident"), m(k, FAST, "wrong_confident")) for k in groups}
    p4 = {k: (m(k, TOOL, "minutes"), m(k, SLOW, "minutes")) for k in groups}
    p5 = {c: (m(("idlocal2", c), "habit_A@idnear", "actionable"), m(("idlocal2", c), "habit_A@min", "actionable")) for c in CAPS}
    return dict(P1=dict(holds=all(f < t for f, t in p1.values()), values=p1), P2=dict(holds=all(t > f for t, f in p2.values()), values=p2),
                P3=dict(holds=all(f - t >= 0.05 for t, f in p3.values()), values=p3), P4=dict(holds=all(t < s for t, s in p4.values()), values=p4),
                P5=dict(holds=all(a >= b + 0.03 for a, b in p5.values()), values=p5))


# ---------------------------------------------------------------------------------------------- gates
def _compare_stored(results: list[dict], ref: dict, policies: tuple, keys: tuple, source: str) -> tuple[bool, str]:
    checked = 0
    for r in results:
        if r["idx"] not in ref:
            continue
        a = ref[r["idx"]]
        if (a["cell"].world, a["cell"].cap, a["cell"].building) != (r["cell"].world, r["cell"].cap, r["cell"].building):
            return False, f"cell {r['idx']} is not the same cell as in {source}"
        for name in policies:
            for key in keys:
                if not np.array_equal(r["policy"][name][key], a["policy"][name][key]):
                    return False, f"cell {r['idx']} {name}: {key} differs from {source}"
        checked += 1
    return checked > 0, f"{checked} cells reproduce {source} exactly"


KEYS = ("minutes", "checks", "guess_idx", "truth_idx", "off_list", "named")


def gate_g1_a25(results: list[dict], a25: list[dict]) -> tuple[bool, str]:
    """G1 (part): `entropy@min` and `entropy@idw4` reproduce Addendum 25's stored episodes exactly in every cell that it also ran."""
    return _compare_stored(results, {r["idx"]: r for r in a25}, ("entropy@min", "entropy@idw4"), KEYS, "Addendum 25")


def gate_g1_a23(results: list[dict], a23: list[dict]) -> tuple[bool, str]:
    """G1 (part): `habit_A@min` and `habit_B@min` reproduce Addendum 23's stored episodes exactly in every cell that it also ran (the first 100)."""
    return _compare_stored(results, {r["idx"]: r for r in a23}, ("habit_A@min", "habit_B@min"), KEYS, "Addendum 23")


def gate_habits_ignore_weights(layout: Building, n: int = 20) -> tuple[bool, str]:
    """The habits give identical results on the id-near list whether the case carries equal weights (idnear) or the tool's id weights (idw4): they read the order only."""
    room = sorted(layout.claims["vav_zone"])[0]
    base = assumed_case(layout, room, "K8", "idnear")
    tm = {c.name: c for c in S.true_settings(SM.world_cell("local")).menu("vav_zone")}
    rng = np.random.default_rng(3)
    for seed in range(n):
        t = sim.sample_truth(base, rng)
        for h in ("habit_A", "habit_B"):
            runs = [S.RUNNERS[h](assumed_case(layout, room, "K8", lv), t, np.random.default_rng(seed), tm) for lv in ("idnear", "idw4")]
            if (runs[0]["guess"], runs[0]["sequence"]) != (runs[1]["guess"], runs[1]["sequence"]) or not np.isclose(runs[0]["minutes"], runs[1]["minutes"]):
                return False, f"{h} differs between equal and id weights at seed {seed}"
    return True, f"{n} episodes x 2 habits identical"


def gate_g3(results: list[dict], layouts: dict[str, Building]) -> tuple[bool, str]:
    """G3: off-list flags equal a direct count recomputed from the seeds for every policy of every cell (each against its own list), every mapped truth is a cause, and the off-list share is
    exactly 0 wherever the building has at most K boxes."""
    for r in results:
        spec, lay = r["cell"], layouts[r["cell"].building]
        picks = IW.draw_picks(r["idx"], spec, lay, r["n"])
        for name, p in r["policy"].items():
            level = name.split("@")[1]
            want = np.array([SM.is_off_list(t, assumed_case(lay, room, spec.cap, level).candidates) for room, t in picks])
            if not np.array_equal(p["off_list"], want):
                return False, f"cell {r['idx']} {name}: off-list flags differ from a direct count"
            if p["truth_idx"].min() < 0:
                return False, f"cell {r['idx']} {name}: a truth is not a cause of the policy"
            if r["boxes"] <= SM.CAPS[spec.cap] and p["off_list"].any():
                return False, f"cell {r['idx']} {name}: off-list episodes in a building with at most K boxes"
    return True, f"{len(results)} cells recomputed"


def g5_complete_fast(results: list[dict], n_cells: int = 250, expected_idx: list[int] | None = None) -> tuple[bool, str]:
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
