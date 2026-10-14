"""What does each data tier buy? (PREREGISTRATION_DR.md Addendum 27.) Simulation only; nothing is fitted; nothing here is evidence about real technicians.

A synthetic building (8 rooms, 8 boxes, 2 air handlers) is called out to with a complaint whose true cause is drawn from a TRUE prior over the 14 hardware / configuration causes of
the v1 tree plus 'the documented box is wrong'. The same complaints are worked by the tool given five different amounts of data (the ARMS). The simulated technician answers each check from
the TRUE response of the check (the tool's own by default, or worse: the reliability factor) and the tool always keeps its own, unchanged, assumptions.
Comparable across all arms are the episodes whose cause is a hardware / configuration cause (T0 has no drawings to be wrong); the documentation-wrong episodes are reported for T1 and up.
"""

from __future__ import annotations

import itertools
import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

import numpy as np

from .. import model as M
from .. import sim
from .. import study as S
from .. import study_rating as SG
from ..building import Building, Equipment
from . import catalogue as K
from . import causes as C
from . import data as D
from .engine import Session, make_case_v1
from .sim1 import World, replay, simulate_v1

# ---------------------------------------------------------------------------------------------- frozen constants (Addendum 27)
SEED = 27
N_EPISODES = 500
BOOT_B = 1000
MAX_CHECKS = 12
N_BOXES = 8
P_INSTRUMENT, P_OCCUPANT = 0.7, 0.7
G3_MIN, G3_MIN_N = 0.90, 30
ARMS: dict[str, frozenset] = {"T0": D.TIERS["T0"], "T1": D.TIERS["T1"], "T2": D.TIERS["T2"], "T2+access": D.TIERS["T2"] | {"bas_access"}, "T3": D.TIERS["T3"]}
ARM_NAMES = tuple(ARMS)
LEVELS = dict(rel=("R0", "R1", "R2"), mix=("assumed", "shifted"), cover=("full", "half"))
REL_A = {"R0": 0.0, "R1": 0.25, "R2": 0.5}
PAIRS = (("T1", "T0"), ("T2", "T1"), ("T2+access", "T2"), ("T3", "T2+access"), ("T3", "T2"), ("T3", "T0"))
ADJACENT = PAIRS[:4]
PRIMARY = dict(rel="R0", mix="assumed", cover="full")
HELPS_SHARE, COST_MAX, HURTS_SHARE = 0.75, 0.10, 0.25
ALL_CAUSES = [c.cause for c in C.CAUSES] + [("wrong", f"VAV-{i}") for i in range(N_BOXES)] + [("unlisted",)]
CAUSE_INDEX = {c: i for i, c in enumerate(ALL_CAUSES)}


def is_hardware(cause: tuple) -> bool:
    return cause[0] in C.ALL_BY_ID


def group_of(cause: tuple) -> str:
    return C.ALL_BY_ID[cause[0]].group if cause[0] in C.ALL_BY_ID else "documentation"


# ---------------------------------------------------------------------------------------------- the grid
@dataclass(frozen=True)
class Cell:
    rel: str
    mix: str
    cover: str

    @property
    def is_primary(self) -> bool:
        return all(getattr(self, k) == v for k, v in PRIMARY.items())


def all_cells() -> list[Cell]:
    """The 12 cells, indexed in the lexicographic order of the factor levels as listed (the last factor varies fastest)."""
    return [Cell(*lv) for lv in itertools.product(*(LEVELS[f] for f in LEVELS))]


def shifted_shares() -> dict:
    """The 'shifted' truth: within each lump the shares are reversed in rank (the tool's most common cause becomes the rarest and vice versa)."""
    out = {}
    for lump in C.LUMPS:
        members = sorted((c for c in C.CAUSES if c.lump == lump), key=lambda c: (-c.share, c.id))
        for c, m in zip(members, reversed(members)):
            out[c.id] = m.share
    return out


def true_world_settings(mix: str) -> tuple[M.Settings, dict]:
    """(settings, leaf shares) of the TRUE cause distribution. The tool's own assumptions never change."""
    if mix == "assumed":
        return M.Settings(), dict(C.DEFAULT_SHARES)
    if mix == "shifted":
        return M.Settings(p_wrong=0.05, p_acts_fail=0.30), shifted_shares()
    raise ValueError(f"mix must be one of {LEVELS['mix']}")


def true_reheat(i: int) -> bool:
    return i % 3 != 0


def make_building1(cover: str) -> D.Building1:
    """8 rooms each documented to their own box; boxes 0-3 on air handler 0 (area A), 4-7 on air handler 1 (area B). Documented attributes and control-system points for every
    box and handler ('full') or only for boxes 0-3 and handler 0 ('half'). The documented attributes are always right."""
    if cover not in LEVELS["cover"]:
        raise ValueError(f"cover must be one of {LEVELS['cover']}")
    eq = {f"AHU-{a}": Equipment(f"AHU-{a}", "AHU", "Roof") for a in range(2)}
    vz, av = {}, {}
    for i in range(N_BOXES):
        area = "A" if i < 4 else "B"
        eq[f"VAV-{i}"], eq[f"Room-{i}"] = Equipment(f"VAV-{i}", "VAV", area), Equipment(f"Room-{i}", "Zone", area)
        vz[f"Room-{i}"], av[f"VAV-{i}"] = f"VAV-{i}", f"AHU-{i // 4}"
    attrs, points = {}, {}
    boxes, ahus = (range(N_BOXES), range(2)) if cover == "full" else (range(4), range(1))
    for i in boxes:
        attrs[f"VAV-{i}"] = dict(reheat="hydronic" if true_reheat(i) else "none", pressure_independent=True, k_factor=1000 + 100 * i, design_airflow_cfm=600 + 50 * i, inlet_diameter_in=6 + 2 * (i % 3))
        points[f"VAV-{i}"] = dict(status=f"V{i}.STS", airflow=f"V{i}.CFM", damper=f"V{i}.DMPR", reheat=f"V{i}.RH")
        points[f"Room-{i}"] = dict(temperature=f"V{i}.ZNT")
    for a in ahus:
        attrs[f"AHU-{a}"] = dict(static_setpoint_inwc=1.2)
        points[f"AHU-{a}"] = dict(fan_status=f"AHU{a}.SF", static_pressure=f"AHU{a}.DSP")
    return D.Building1(Building("synthetic tiers", eq, {"vav_zone": vz, "ahu_vav": av}), attrs, points)


# ---------------------------------------------------------------------------------------------- one episode's draws (shared by all arms)
def draw_episode(idx: int, i: int, mix: str, cases: dict) -> dict:
    """(room, true cause, whether the technician has an instrument, whether the occupant is there) from the stream [SEED, cell, 0, episode]: independent of every arm and of n."""
    rng = np.random.default_rng([SEED, idx, 0, i])
    room = int(rng.integers(N_BOXES))
    c = cases[("T1", room)]
    settings, shares = true_world_settings(mix)
    causes, prior = C.make_prior_v1(c.candidates, c.doc, settings, docs=True, weights=c.weights, shares=shares, reheat=true_reheat(room))
    truth = causes[int(rng.choice(len(causes), p=prior))]
    return dict(room=room, truth=truth, instrument=bool(rng.random() < P_INSTRUMENT), occupant=bool(rng.random() < P_OCCUPANT))


def world_for(ep: dict, arm: str, true_checks: tuple | None) -> World:
    ctx = dict(reheat="yes" if true_reheat(ep["room"]) else "no", bas_access="yes" if "bas_access" in ARMS[arm] else "no",
               instrument="yes" if ep["instrument"] else "no", occupant="yes" if ep["occupant"] else "no")
    return World(ep["truth"], ctx, true_checks)


def make_cases(cover: str) -> dict:
    b = make_building1(cover)
    return {(arm, room): make_case_v1(b, f"Room-{room}", items, member_name=f"Room {room}") for arm, items in ARMS.items() for room in range(N_BOXES)}


# ---------------------------------------------------------------------------------------------- one cell
def run_cell(idx: int, cell: Cell, n: int = N_EPISODES) -> dict:
    """`n` episodes for each arm on the same `n` draws; the outcome draws of arm a use [SEED, cell, 1 + a, episode]. Raw arrays only."""
    cases = make_cases(cell.cover)
    true_checks = K.degrade_all(K.CATALOGUE, REL_A[cell.rel])
    eps = [draw_episode(idx, i, cell.mix, cases) for i in range(n)]
    out = dict(idx=idx, cell=cell, n=n, room=np.array([e["room"] for e in eps]), truth_idx=np.array([CAUSE_INDEX[e["truth"]] for e in eps]),
               instrument=np.array([e["instrument"] for e in eps]), occupant=np.array([e["occupant"] for e in eps]), arm={})
    for ai, arm in enumerate(ARM_NAMES):
        rows = []
        for i, e in enumerate(eps):
            if arm == "T0" and not is_hardware(e["truth"]):
                rows.append(None)                                              # T0 has no drawings, so no documentation cause: not comparable
                continue
            rows.append(simulate_v1(cases[(arm, e["room"])], world_for(e, arm, true_checks), "entropy", np.random.default_rng([SEED, idx, 1 + ai, i]), MAX_CHECKS))
        ok = [r is not None for r in rows]
        num = lambda k: np.array([r[k] if r is not None else np.nan for r in rows], float)  # noqa: E731
        flag = lambda k: np.array([bool(r[k]) if r is not None else False for r in rows], bool)  # noqa: E731
        out["arm"][arm] = dict(
            valid=np.array(ok), minutes=num("minutes"), checks=num("n_checks"), questions=num("n_questions"), entries=num("entries"), concluded=flag("concluded"), stalled=flag("stalled"),
            correct=flag("correct"), guess_idx=np.array([CAUSE_INDEX[r["guess"]] if r is not None else -1 for r in rows]),
            group_ok=np.array([r is not None and group_of(r["guess"]) == group_of(e["truth"]) for r, e in zip(rows, eps)]), sequence=[tuple(c for c, _ in r["sequence"]) if r else () for r in rows],
            trace=[r["trace"] if r else [] for r in rows])
    return out


def _run_args(args):
    return run_cell(*args)


def compute_cells(cells: list[tuple[int, Cell]], n: int = N_EPISODES, workers: int | None = None) -> list[dict]:
    """Deterministic whatever the number of workers (every cell has its own seeds)."""
    jobs = [(i, c, n) for i, c in cells]
    workers = workers if workers is not None else min(8, os.cpu_count() or 1)
    if workers <= 1 or len(jobs) == 1:
        return [_run_args(j) for j in jobs]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_run_args, jobs, chunksize=1))


# ---------------------------------------------------------------------------------------------- summaries and comparisons
def hw_mask(res: dict) -> np.ndarray:
    """The episodes whose true cause is a hardware / configuration cause: the ones every arm can be compared on."""
    return np.array([is_hardware(ALL_CAUSES[t]) for t in res["truth_idx"]], bool)


def summarize_arm(res: dict, arm: str, mask: np.ndarray) -> dict:
    """Means over the episodes of `mask` (restricted to those the arm ran). Unresolved = not concluded; it splits into 'stopped' (nothing left worth its time) and 'hit the check limit'."""
    a = res["arm"][arm]
    m = mask & a["valid"]
    if not m.any():
        return dict(n=0)
    conc = a["concluded"][m]
    cor = a["correct"][m]
    return dict(n=int(m.sum()), minutes=float(a["minutes"][m].mean()), accuracy=float(cor.mean()), group_accuracy=float(a["group_ok"][m].mean()), checks=float(a["checks"][m].mean()),
                questions=float(a["questions"][m].mean()), entries=float(a["entries"][m].mean()), concluded=float(conc.mean()), stopped=float(a["stalled"][m].mean()),
                limit=float((~conc & ~a["stalled"][m]).mean()), wrong_confident=float((conc & ~cor).mean()),
                acc_concluded=float(cor[conc].mean()) if conc.any() else float("nan"), n_concluded=int(conc.sum()))


def compare_pair(res: dict, rich: str, poor: str, boot: np.ndarray, idx_hw: np.ndarray) -> dict:
    """`rich` minus `poor` on the same hardware-cause episodes, with Addendum 21's frozen labels (5% minutes, 0.02 accuracy, safety 0.02, paired 95% intervals). A slower but more accurate
    richer arm is TRADE under those labels, so Addendum 20's BUYS ACCURACY (which only fires on NEITHER) is not used."""
    A, B = res["arm"][rich], res["arm"][poor]
    d_min, d_acc = A["minutes"][idx_hw] - B["minutes"][idx_hw], A["correct"][idx_hw].astype(float) - B["correct"][idx_hw].astype(float)
    wcA, wcB = (A["concluded"] & ~A["correct"])[idx_hw].astype(float), (B["concluded"] & ~B["correct"])[idx_hw].astype(float)
    d_wc, d_chk = wcA - wcB, A["checks"][idx_hw] - B["checks"][idx_hw]
    ci_min, ci_acc, ci_wc = S.paired_ci(d_min, boot), S.paired_ci(d_acc, boot), S.paired_ci(d_wc, boot)
    r_min = float(d_min.mean() / B["minutes"][idx_hw].mean())
    ts, as_ = SG.time_state(r_min, ci_min), SG.acc_state(float(d_acc.mean()), ci_acc)
    entry = dict(d_min=float(d_min.mean()), r_min=r_min, d_acc=float(d_acc.mean()), d_wc=float(d_wc.mean()), d_checks=float(d_chk.mean()), ci_min=ci_min, ci_acc=ci_acc, ci_wc=ci_wc, time=ts, acc=as_,
                 label=SG.label(ts, as_), safety=SG.safety_flag(float(d_wc.mean()), ci_wc))
    return entry


def analyze_cell(res: dict, B: int = BOOT_B) -> dict:
    hw = hw_mask(res)
    idx_hw = np.flatnonzero(hw)
    boot = np.random.default_rng([SEED, res["idx"], 99]).integers(0, len(idx_hw), (B, len(idx_hw)))
    return dict(idx=res["idx"], cell=res["cell"], n_hw=int(hw.sum()), hw={arm: summarize_arm(res, arm, hw) for arm in ARM_NAMES}, doc={arm: summarize_arm(res, arm, ~hw) for arm in ARM_NAMES},
                cmp={f"{a}|{b}": compare_pair(res, a, b, boot, idx_hw) for a, b in PAIRS})


def step_shares(analyses: list[dict], pair: tuple[str, str]) -> dict:
    """Shares of the cells by label for one comparison, and of safety regressions."""
    key = f"{pair[0]}|{pair[1]}"
    labs = [a["cmp"][key]["label"] for a in analyses]
    n = max(len(labs), 1)
    out = {k: labs.count(k) / n for k in ("IMPROVES", "WORSE", "TRADE", "NEITHER")}
    out["FASTER_LESS"] = sum(a["cmp"][key]["time"] == "FASTER" and a["cmp"][key]["acc"] == "LESS" for a in analyses) / n          # the two kinds of TRADE
    out["SLOWER_MORE"] = sum(a["cmp"][key]["time"] == "SLOWER" and a["cmp"][key]["acc"] == "MORE" for a in analyses) / n
    out["SAFETY_REGRESSION"] = sum(a["cmp"][key]["safety"] == "REGRESSION" for a in analyses) / n
    out["SAFETY_GAIN"] = sum(a["cmp"][key]["safety"] == "GAIN" for a in analyses) / n
    out["COST"] = out["WORSE"] + out["TRADE"]
    return out


def step_reading(sh: dict) -> str:
    """HELPS if IMPROVES in at least 75% of the cells and WORSE or TRADE in at most 10%; HURTS if WORSE or TRADE in more than 25%; MIXED otherwise."""
    if sh["IMPROVES"] >= HELPS_SHARE and sh["COST"] <= COST_MAX:
        return "HELPS"
    if sh["COST"] > HURTS_SHARE:
        return "HURTS"
    return "MIXED"


def cell_of(analyses: list[dict], **kw) -> dict:
    (a,) = [x for x in analyses if all(getattr(x["cell"], k) == v for k, v in kw.items())]
    return a


# ---------------------------------------------------------------------------------------------- predictions (frozen operationalisation)
def tier_predictions(analyses: list[dict]) -> dict:
    """P1-P9 as operationalised in Addendum 27 (each strict; P1-P4 and P9 in the primary cell, P5-P8 across the named cells)."""
    pc = cell_of(analyses, **PRIMARY)["hw"]
    at = lambda **kw: cell_of(analyses, **{**PRIMARY, **kw})["hw"]  # noqa: E731
    p = {}
    p["P1"] = dict(values=(pc["T3"]["minutes"], 0.75 * pc["T2"]["minutes"]), holds=pc["T3"]["minutes"] <= 0.75 * pc["T2"]["minutes"])
    p["P2"] = dict(values=(pc["T3"]["minutes"], 0.90 * pc["T2+access"]["minutes"]), holds=pc["T3"]["minutes"] <= 0.90 * pc["T2+access"]["minutes"])
    dm = abs(pc["T2"]["minutes"] - pc["T1"]["minutes"]) / pc["T1"]["minutes"]
    p["P3"] = dict(values=(dm, pc["T2"]["accuracy"] - pc["T1"]["accuracy"]), holds=dm <= 0.10 and pc["T2"]["accuracy"] >= pc["T1"]["accuracy"])
    p["P4"] = dict(values=(pc["T1"]["minutes"], pc["T0"]["minutes"]), holds=pc["T1"]["minutes"] >= pc["T0"]["minutes"])
    r2 = at(rel="R2")
    p["P5"] = dict(values={a: (r2[a]["wrong_confident"], pc[a]["wrong_confident"]) for a in ARM_NAMES}, holds=all(r2[a]["wrong_confident"] > pc[a]["wrong_confident"] for a in ARM_NAMES))
    inc = lambda arm: r2[arm]["wrong_confident"] - pc[arm]["wrong_confident"]  # noqa: E731
    p["P6"] = dict(values=(inc("T3"), inc("T1")), holds=inc("T3") >= inc("T1"))
    half = at(cover="half")
    gap = lambda h: abs(h["T3"]["minutes"] - h["T2+access"]["minutes"])  # noqa: E731
    p["P7"] = dict(values=(gap(half), gap(pc)), holds=gap(half) < gap(pc))
    sh = at(mix="shifted")
    p["P8"] = dict(values={a: (sh[a]["accuracy"], pc[a]["accuracy"]) for a in ARM_NAMES}, holds=all(sh[a]["accuracy"] < pc[a]["accuracy"] for a in ARM_NAMES))
    d1 = cell_of(analyses, **PRIMARY)["doc"]["T1"]
    p["P9"] = dict(values=(d1.get("accuracy", float("nan")), 0.5), holds=d1.get("n", 0) > 0 and d1["accuracy"] >= 0.5)
    return p


# ---------------------------------------------------------------------------------------------- gates
def gate_g1(n: int = 30) -> tuple[bool, str]:
    """Code path. (a) The v0-equivalent tree of v1 reproduces `sim.simulate` (v0) exactly on the study's synthetic building for `entropy` and `split_half`. (b) A cell's stored episodes
    equal direct `simulate_v1` calls on the same draws and seeds (the runner adds no accounting of its own)."""
    from ..building import make_case
    b = make_building1("full")
    for strat in ("entropy", "split_half"):
        for room in (0, 5):
            c0 = make_case(b.base, f"Room-{room}", max_candidates=N_BOXES)
            c1 = make_case_v1(b, f"Room-{room}", "T1", compat_v0=True, max_candidates=N_BOXES)
            causes = M.make_prior("vav_zone", c0.candidates, c0.doc, c0.settings, None, c0.weights)[0]
            for k, truth in enumerate(causes[: min(len(causes), 6)]):
                r0 = sim.simulate(c0, truth, strat, np.random.default_rng(k), max_checks=MAX_CHECKS)
                r1 = simulate_v1(c1, World(truth), strat, np.random.default_rng(k), MAX_CHECKS)
                if (r0["guess"], r0["n_checks"], r0["concluded"], r0["entries"]) != (r1["guess"], r1["n_checks"], r1["concluded"], r1["entries"]) or abs(r0["minutes"] - r1["minutes"]) > 1e-9:
                    return False, f"v0 and the v0-equivalent tree differ ({strat}, room {room}, episode {k})"
    cell = Cell(**PRIMARY)
    res = run_cell(0, cell, n)
    cases, tc = make_cases(cell.cover), K.degrade_all(K.CATALOGUE, REL_A[cell.rel])
    for i in range(n):
        e = draw_episode(0, i, cell.mix, cases)
        for ai, arm in enumerate(ARM_NAMES):
            if arm == "T0" and not is_hardware(e["truth"]):
                continue
            r = simulate_v1(cases[(arm, e["room"])], world_for(e, arm, tc), "entropy", np.random.default_rng([SEED, 0, 1 + ai, i]), MAX_CHECKS)
            a = res["arm"][arm]
            if (a["minutes"][i], a["checks"][i], a["correct"][i], a["concluded"][i], a["sequence"][i]) != (r["minutes"], r["n_checks"], r["correct"], r["concluded"], tuple(c for c, _ in r["sequence"])):
                return False, f"stored episode {i} of arm {arm} differs from a direct simulate_v1 call"
    return True, "v0-equivalent tree = v0 on 12 episodes x 2 strategies; stored episodes = direct calls"


def gate_g2(results: list[dict] | None = None, per_arm: int = 10) -> tuple[bool, str]:
    """Accounting. (a) A scripted transcript at 'T2+access' costs the hand-summed minutes: bas_airflow 0 + 2 + 8 (no point map) = 10, power_24vac 6 + 4 = 10, control_signal at the box
    0 + 4 + 2 = 6; at 'T3' the first is 2. (b) Which check the tool chooses depends only on the answers it has been given, not on the TRUE reliability of the world: the first `per_arm` valid
    episodes of every arm in every degraded-reliability cell of `results` are replayed through a fresh session that is given only the recorded answers, and must ask and recommend the same things."""
    cases = make_cases("full")
    s = Session(cases[("T2+access", 0)])
    for name in ("bas_airflow", "power_24vac", "control_signal"):
        s.report("normal", name)
    if s.elapsed != 26 or [o.minutes for o in s.log] != [10, 10, 6]:
        return False, f"T2+access transcript costs {s.elapsed}, expected 26"
    s3 = Session(cases[("T3", 0)])
    s3.report("normal", "bas_airflow")
    if s3.elapsed != 2:
        return False, "a control-system read at T3 does not cost 2 minutes"
    n = 0
    for r in results or []:
        if r["cell"].rel == "R0":
            continue
        cs = make_cases(r["cell"].cover)
        for arm in ARM_NAMES:
            a = r["arm"][arm]
            for i in np.flatnonzero(a["valid"])[:per_arm]:
                n += 1
                if not replay(cs[(arm, int(r["room"][i]))], a["trace"][i]):
                    return False, f"cell {r['idx']} arm {arm} episode {i}: replaying the recorded answers gives different checks"
    return True, f"hand-summed minutes agree; {n} degraded-reliability episodes replay identically from their answers alone"


def gate_g3(results: list[dict]) -> tuple[bool, dict]:
    """Honesty: at the assumed reliability and the assumed mix, accuracy among CONCLUDED hardware-cause episodes is at least 0.90 for every arm with at least 30 conclusions, in both coverages
    (a lower value would mean a defect in the belief update, not a finding), and every arm has at least 30 conclusions (or the gate says nothing)."""
    vals = {}
    for r in results:
        c = r["cell"]
        if c.rel == "R0" and c.mix == "assumed":
            for arm in ARM_NAMES:
                s = summarize_arm(r, arm, hw_mask(r))
                vals[(c.cover, arm)] = (s.get("acc_concluded", float("nan")), s.get("n_concluded", 0))
    ok = bool(vals) and all(n >= G3_MIN_N and acc >= G3_MIN for acc, n in vals.values())
    return ok, vals


def gate_g5(results: list[dict], n_cells: int = 12, expected_idx: list[int] | None = None) -> tuple[bool, str]:
    """Completeness and pairing: all cells present with every arm, finite where valid, identical draws (room, cause, instrument, occupant) across arms by construction, T0 valid exactly on the
    hardware-cause episodes and every other arm valid on all."""
    want = list(range(n_cells)) if expected_idx is None else sorted(expected_idx)
    if len(results) != len(want) or sorted(r["idx"] for r in results) != want:
        return False, f"{len(results)} cells present, expected {len(want)}"
    for r in results:
        if set(r["arm"]) != set(ARM_NAMES):
            return False, f"cell {r['idx']}: arms {sorted(r['arm'])}"
        hw = hw_mask(r)
        for arm, a in r["arm"].items():
            want_valid = hw if arm == "T0" else np.ones(r["n"], bool)
            if not np.array_equal(a["valid"], want_valid):
                return False, f"cell {r['idx']} {arm}: valid episodes are not the expected ones"
            if len(a["minutes"]) != r["n"] or not np.isfinite(a["minutes"][a["valid"]]).all():
                return False, f"cell {r['idx']} {arm}: non-finite or short minutes"
            if (a["guess_idx"][a["valid"]] < 0).any():
                return False, f"cell {r['idx']} {arm}: a valid episode has no guess"
    return True, "ok"


def gate_g6(results: list[dict]) -> tuple[bool, str]:
    """Availability: in every stored episode every check the tool performed was available at its arm given the world's true facts (no control-system read where the technician had no access,
    no gauge check without a gauge, no reheat check on a box without reheat, no design-load check without design values, ...)."""
    for r in results:
        cases = make_cases(r["cell"].cover)
        for arm in ARM_NAMES:
            a = r["arm"][arm]
            for i in np.flatnonzero(a["valid"]):
                room = int(r["room"][i])
                s = Session(cases[(arm, room)])
                s.ctx = D.Context(reheat="yes" if true_reheat(room) else "no", bas_access="yes" if "bas_access" in ARMS[arm] else "no", instrument="yes" if r["instrument"][i] else "no",
                                  occupant="yes" if r["occupant"][i] else "no")
                for name in a["sequence"][i]:
                    ck = s._check(name)
                    if D.availability(ck, s.view(), s._eq(ck)).state == "unavailable":
                        return False, f"cell {r['idx']} arm {arm} episode {i}: {name} was performed but is unavailable there"
    return True, "ok"


def gate_g4(results: list[dict], n: int = 50) -> tuple[bool, str]:
    """Reproducibility: the first cell re-run with `n` episodes reproduces its first `n` stored episodes of every arm."""
    first = min(results, key=lambda r: r["idx"])
    again = run_cell(first["idx"], first["cell"], n)
    for arm in ARM_NAMES:
        for k in ("minutes", "checks", "questions", "entries", "concluded", "stalled", "correct", "guess_idx", "valid"):
            x, y = first["arm"][arm][k][:n], again["arm"][arm][k]
            same = np.array_equal(x, y, equal_nan=True) if x.dtype.kind == "f" else np.array_equal(x, y)
            if not same:
                return False, f"arm {arm} field {k} differs on re-run"
        if first["arm"][arm]["sequence"][:n] != again["arm"][arm]["sequence"]:
            return False, f"arm {arm} sequences differ on re-run"
    return True, f"first {n} episodes of cell {first['idx']} reproduce"
