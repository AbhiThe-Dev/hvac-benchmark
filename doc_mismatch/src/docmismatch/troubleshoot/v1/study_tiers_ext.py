"""Exploratory note E2 (PREREGISTRATION_DR.md): the tiers of Addendum 27 are CUMULATIVE (T3 = T2 + access + point map, so T3 always has T2's attributes too). A reported real-world
documentation profile has T1 and T3 commonly available but T2 rarely so -- i.e. control-system access and a point map, without documented attributes / design values. No existing
result covers that combination. This module answers it by reusing Addendum 27's exact machinery (study_tiers.py): the same synthetic building, the same per-episode draws, the same
seed. It adds exactly one more arm at the next free RNG channel (index 5; the original five arms use 0-4), so those five arms are provably untouched -- verified below by diffing
against a fresh run of the original `run_cell`. Simulation only; every probability and every minute is a placeholder; nothing here is evidence about real technicians or real buildings.
"""

from __future__ import annotations

import numpy as np

from . import catalogue as K
from . import data as D
from . import study_tiers as T
from .engine import make_case_v1
from .sim1 import World, simulate_v1

EXT_ARM = "T3-noattr"                                              # T1's items + bas_access + point_map, but no attributes / design values
EXT_ITEMS: frozenset = D.TIERS["T1"] | {"bas_access", "point_map"}
CHAIN = ("T1", "T2", "T2+access", EXT_ARM, "T3")                   # attrs alone -> access alone -> access+map alone (no attrs) -> everything
AI = {"T1": 1, "T2": 2, "T2+access": 3, "T3": 4, EXT_ARM: 5}       # 0-4 match study_tiers.ARM_NAMES exactly (T0,T1,T2,T2+access,T3); 5 is the first free channel


def make_cases_ext(cover: str) -> dict:
    cases = T.make_cases(cover)
    b = T.make_building1(cover)
    for room in range(T.N_BOXES):
        cases[(EXT_ARM, room)] = make_case_v1(b, f"Room-{room}", EXT_ITEMS, member_name=f"Room {room}")
    return cases


def _items_of(arm: str) -> frozenset:
    return T.ARMS[arm] if arm in T.ARMS else EXT_ITEMS


def run_cell_ext(idx: int, cell: T.Cell, n: int = T.N_EPISODES) -> dict:
    """Like `study_tiers.run_cell`, restricted to `CHAIN` (none of which is T0, so every episode is valid for every arm) and reusing each arm's original RNG channel."""
    cases = make_cases_ext(cell.cover)
    true_checks = K.degrade_all(K.CATALOGUE, T.REL_A[cell.rel])
    eps = [T.draw_episode(idx, i, cell.mix, cases) for i in range(n)]
    out = dict(idx=idx, cell=cell, n=n, room=np.array([e["room"] for e in eps]), truth_idx=np.array([T.CAUSE_INDEX[e["truth"]] for e in eps]),
               instrument=np.array([e["instrument"] for e in eps]), occupant=np.array([e["occupant"] for e in eps]), arm={})
    for arm in CHAIN:
        ai, items = AI[arm], _items_of(arm)
        rows = []
        for i, e in enumerate(eps):
            ctx = dict(reheat="yes" if T.true_reheat(e["room"]) else "no", bas_access="yes" if "bas_access" in items else "no",
                       instrument="yes" if e["instrument"] else "no", occupant="yes" if e["occupant"] else "no")
            rows.append(simulate_v1(cases[(arm, e["room"])], World(e["truth"], ctx, true_checks), "entropy", np.random.default_rng([T.SEED, idx, 1 + ai, i]), T.MAX_CHECKS))
        num = lambda k: np.array([r[k] for r in rows], float)  # noqa: E731
        flag = lambda k: np.array([bool(r[k]) for r in rows], bool)  # noqa: E731
        out["arm"][arm] = dict(
            valid=np.ones(n, bool), minutes=num("minutes"), checks=num("n_checks"), questions=num("n_questions"), entries=num("entries"), concluded=flag("concluded"),
            stalled=flag("stalled"), correct=flag("correct"), guess_idx=np.array([T.CAUSE_INDEX[r["guess"]] for r in rows]),
            group_ok=np.array([T.group_of(r["guess"]) == T.group_of(e["truth"]) for r, e in zip(rows, eps)]), sequence=[tuple(c for c, _ in r["sequence"]) for r in rows],
            trace=[r["trace"] for r in rows])
    return out


def compute_cells_ext(cells: list[tuple[int, T.Cell]], n: int = T.N_EPISODES) -> list[dict]:
    return [run_cell_ext(i, c, n) for i, c in cells]


# ---------------------------------------------------------------------------------------------- non-perturbation check
def verify_non_perturbation(n: int = 100) -> tuple[bool, str]:
    """The four original arms in CHAIN (T1, T2, T2+access, T3), computed here, must be byte-identical to a fresh call of the original, untouched `study_tiers.run_cell` -- proof that
    adding the new arm at RNG channel 5 does not perturb any arm Addendum 27 already reported."""
    cell = T.Cell(**T.PRIMARY)
    orig = T.run_cell(0, cell, n)
    ext = run_cell_ext(0, cell, n)
    for arm in ("T1", "T2", "T2+access", "T3"):
        for k in ("minutes", "checks", "questions", "entries", "concluded", "stalled", "correct", "guess_idx"):
            x, y = orig["arm"][arm][k], ext["arm"][arm][k]
            same = np.array_equal(x, y, equal_nan=True) if np.asarray(x).dtype.kind == "f" else np.array_equal(x, y)
            if not same:
                return False, f"arm {arm} field {k} differs from the original run_cell"
        if orig["arm"][arm]["sequence"] != ext["arm"][arm]["sequence"]:
            return False, f"arm {arm} sequences differ from the original run_cell"
    return True, f"{n} episodes of T1, T2, T2+access and T3 reproduce study_tiers.run_cell exactly"


# ---------------------------------------------------------------------------------------------- analysis (reuses study_tiers's own summaries and labels)
PAIRS_EXT = ((EXT_ARM, "T1"), (EXT_ARM, "T2"), (EXT_ARM, "T2+access"), ("T3", EXT_ARM))
PAIR_TEXT_EXT = {
    (EXT_ARM, "T1"): f"{EXT_ARM} vs T1 (what BAS access + a point map buy, with no attributes at all)",
    (EXT_ARM, "T2"): f"{EXT_ARM} vs T2 (access + map without attributes, vs. attributes alone)",
    (EXT_ARM, "T2+access"): f"{EXT_ARM} vs T2+access (adding the point map, when attributes were never there to begin with)",
    ("T3", EXT_ARM): f"T3 vs {EXT_ARM} (what having attributes too, on top of access + map, still buys)",
}


def analyze_cell_ext(res: dict, B: int = T.BOOT_B) -> dict:
    hw = T.hw_mask(res)
    idx_hw = np.flatnonzero(hw)
    boot = np.random.default_rng([T.SEED, res["idx"], 199]).integers(0, len(idx_hw), (B, len(idx_hw)))
    return dict(idx=res["idx"], cell=res["cell"], n_hw=int(hw.sum()), hw={arm: T.summarize_arm(res, arm, hw) for arm in CHAIN},
                cmp={f"{a}|{b}": T.compare_pair(res, a, b, boot, idx_hw) for a, b in PAIRS_EXT})
