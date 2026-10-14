"""How does the v1 tool compare with fast trial-and-error stand-in technicians at each data tier? (PREREGISTRATION_DR.md Addendum 28.) Simulation only.

The complaints, the data tiers, the simulated technician's answers and the accounting are Addendum 27's (`study_tiers`); the tool's results are Addendum 27's, reproduced by calling its runner.
Three stand-ins, all MY CONSTRUCTIONS and none a real technician, work the same episodes: `habit_A` (v0's fast stand-in, logic unchanged: it can answer only in v0's four lumps),
`fast_list` (cheapest-first checklist of single-cause reading checks, first abnormal reading concludes) and `fast_confirm` (as `fast_list`, but a first abnormal reading must be confirmed).
Each is charged the tool's own minutes by the tool's own accounting (a `Session` used only as an accountant), draws its answers from the same TRUE responses, and reads no belief.
"""

from __future__ import annotations

import os
import pickle
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from .. import model as M
from .. import sim
from .. import study as S
from .. import study_rating as SG
from . import catalogue as K
from . import causes as C
from . import data as D
from . import study_tiers as T
from .engine import Session, make_case_v1
from .sim1 import World, p_true

# ---------------------------------------------------------------------------------------------- frozen constants (Addendum 28)
SEED = 28
N_EPISODES = T.N_EPISODES
BOOT_B = T.BOOT_B
POLICIES = ("habit_A", "fast_list", "fast_confirm")
SINGLE_P, CONFIRM_P = 0.75, 0.5
LUMPS = (("doc_other",), ("doc_acts_fail",))
GUESS_CAUSES = T.ALL_CAUSES + list(LUMPS)
GUESS_INDEX = {c: i for i, c in enumerate(GUESS_CAUSES)}
EXACT_STANDS = ("fast_list", "fast_confirm")
SUBSETS = ("hw", "doc")
LEVELS = ("exact", "v0")
RAW27 = Path(__file__).resolve().parents[5] / "results" / "docmismatch" / "troubleshoot_tiers" / "tiers_raw.pkl"
WRONG_COST_KINDS = ("DOMINATES", "DOMINATED", "SLOWER-MORE", "FASTER-LESS")


# ---------------------------------------------------------------------------------------------- the stand-ins
class Doer:
    """Charges a stand-in's checks with the tool's own accounting (a Session used only as an accountant: minutes, location, fallback costs) and asks the world."""

    def __init__(self, case, ctx: dict, ask):
        self.case, self.ask = case, ask
        self.s = Session(case)
        self.s.ctx = D.Context(**ctx)                    # every fact declared: nothing to ask, availability follows the world
        self.trace: list = []
        self.done: set = set()

    def do(self, ck: K.CheckV1, target: str) -> bool:
        """Do the check on the target; True if it comes back positive (yes / abnormal)."""
        if (ck.name, target) in self.done:
            raise ValueError(f"{ck.name!r} on {target!r} was already done")
        word = self.ask(ck, target)
        self.s.report(word, ck.name, target)
        self.done.add((ck.name, target))
        self.trace.append(("C", ck.name, target, word))
        return word == ck.words[0]

    def result(self, guess: tuple) -> dict:
        return dict(guess=guess, minutes=self.s.elapsed, n_checks=len(self.trace), entries=1 + len(self.trace), sequence=tuple(t[1] for t in self.trace), trace=list(self.trace))


def available_readings(case, doer: Doer) -> list[tuple]:
    """[(cost from scratch, name, check)] of the reading checks available at this arm given the world's facts, cheapest first (ties by name)."""
    out = []
    for ck in case.checks:
        if not ck.is_reading:
            continue
        av = D.availability(ck, doer.s.view(), doer.s._eq(ck))
        if av.state == "unavailable":
            continue
        out.append((ck.access_min + ck.do_min + ck.wait_min + av.extra_min, ck.name, ck))
    return sorted(out, key=lambda t: (t[0], t[1]))


def single_cause(ck: K.CheckV1) -> tuple | None:
    """The one cause a reading check names: the only cause with P(abnormal) of at least SINGLE_P, else None."""
    strong = [c for c, p in ck.detects.items() if p >= SINGLE_P]
    return (strong[0],) if len(strong) == 1 else None


def walk_alternatives(case, doer: Doer):
    """habit_A's way of looking for a wrong claim: the cheaper act-and-watch check on each alternative box in candidate order; the first yes names that box."""
    observers = [c for c in case.checks if c.kind == "act_observe"]
    for j in case.candidates:
        if j == case.doc:
            continue
        if doer.do(min(observers, key=lambda c: c.minutes(doer.s.at, j)), j):
            return ("wrong", j)
    return None


def run_habit_A(case, ctx: dict, ask) -> dict:
    """v0's `sim.simulate_habit`, logic unchanged: confirm the documented box acts (no: the box does not act); then the cheaper of the two act-and-watch checks on the documented box and each
    alternative in candidate order; the first yes concludes (documented box: it feeds the room and acts, cause elsewhere; another box: fed by it); all no: unlisted."""
    d = Doer(case, ctx, ask)
    by = {c.name: c for c in case.checks}
    if "confirm_acts" in by and not d.do(by["confirm_acts"], case.doc):
        return d.result(("doc_acts_fail",))
    observers = [c for c in case.checks if c.kind == "act_observe"]
    for j in case.candidates:
        if d.do(min(observers, key=lambda c: c.minutes(d.s.at, j)), j):
            return d.result(("doc_other",) if j == case.doc else ("wrong", j))
    return d.result(("unlisted",))


def run_fast(case, ctx: dict, ask, confirm: bool = False) -> dict:
    """The checklist stand-ins (see the module docstring). The checklist is the available reading checks that name exactly one cause, cheapest first; the first abnormal reading concludes that
    cause (`confirm`: only if the cheapest other available check that sees the cause, at P(abnormal) >= CONFIRM_P, is also abnormal, else the finding is discarded). If the list is exhausted,
    with the drawings' claims the alternative boxes are walked as habit_A does; nothing found: 'other'."""
    d = Doer(case, ctx, ask)
    avail = available_readings(case, d)
    for _, name, ck in avail:
        cause = single_cause(ck)
        if cause is None or (name, case.doc) in d.done:
            continue
        if not d.do(ck, case.doc):
            continue
        if not confirm:
            return d.result(cause)
        others = [c2 for _, n2, c2 in avail if (n2, case.doc) not in d.done and c2.detects.get(cause[0], 0.0) >= CONFIRM_P]
        if not others or d.do(others[0], case.doc):
            return d.result(cause)
    if case.docs:
        found = walk_alternatives(case, d)
        if found is not None:
            return d.result(found)
    return d.result(("other",))


def run_policy(pol: str, case, world: World, ask) -> dict:
    if pol == "habit_A":
        return run_habit_A(case, world.context, ask)
    if pol in EXACT_STANDS:
        return run_fast(case, world.context, ask, confirm=pol == "fast_confirm")
    raise ValueError(f"unknown stand-in {pol!r}")


def ask_from_world(case, world: World, rng: np.random.Generator):
    """The answer of the simulated technician: drawn from the TRUE response of the check under the real cause."""
    def ask(ck: K.CheckV1, target: str) -> str:
        return ck.words[0] if rng.random() < p_true(case, world, ck.name, target) else ck.words[1]
    return ask


def ask_from_trace(trace: list):
    """Answers a stand-in from a recorded trace only, refusing (ValueError) any request that is not the next recorded one."""
    it = iter(trace)

    def ask(ck: K.CheckV1, target: str) -> str:
        item = next(it, None)
        if item is None or (item[1], item[2]) != (ck.name, target):
            raise ValueError("the replayed stand-in asked for something else")
        return item[3]
    return ask


def replay(pol: str, case, ctx: dict, trace: list) -> bool:
    """A stand-in fed only the recorded answers must ask for the same checks in the same order: its choices depend on nothing about the world that produced the answers."""
    try:
        return run_policy(pol, case, World(("other",), ctx), ask_from_trace(trace))["trace"] == [tuple(x) for x in trace]
    except ValueError:
        return False


# ---------------------------------------------------------------------------------------------- one cell
def run_cell(idx: int, cell: T.Cell, n: int = N_EPISODES) -> dict:
    """Addendum 27's runner for the tool (same draws and seeds), then each stand-in on the same episodes with outcome draws from [SEED, cell, policy, episode]."""
    base = T.run_cell(idx, cell, n)
    cases = T.make_cases(cell.cover)
    tc = K.degrade_all(K.CATALOGUE, T.REL_A[cell.rel])
    eps = [T.draw_episode(idx, i, cell.mix, cases) for i in range(n)]
    out = dict(idx=idx, cell=cell, n=n, base=base, pol={})
    for pi, pol in enumerate(POLICIES):
        out["pol"][pol] = {}
        for arm in T.ARM_NAMES:
            rows = []
            for i, e in enumerate(eps):
                if arm == "T0" and not T.is_hardware(e["truth"]):
                    rows.append(None)                                              # no drawings at T0, so no documentation cause: not run
                    continue
                case, world = cases[(arm, e["room"])], T.world_for(e, arm, tc)
                rows.append(run_policy(pol, case, world, ask_from_world(case, world, np.random.default_rng([SEED, idx, pi, i]))))
            num = lambda k: np.array([r[k] if r is not None else np.nan for r in rows], float)  # noqa: E731
            out["pol"][pol][arm] = dict(valid=np.array([r is not None for r in rows]), minutes=num("minutes"), checks=num("n_checks"), entries=num("entries"),
                                        guess_idx=np.array([GUESS_INDEX[r["guess"]] if r is not None else -1 for r in rows]),
                                        sequence=[r["sequence"] if r else () for r in rows], trace=[r["trace"] if r else [] for r in rows])
    return out


def _run_args(args):
    return run_cell(*args)


def compute_cells(cells: list[tuple[int, T.Cell]], n: int = N_EPISODES, workers: int | None = None) -> list[dict]:
    jobs = [(i, c, n) for i, c in cells]
    workers = workers if workers is not None else min(8, os.cpu_count() or 1)
    if workers <= 1 or len(jobs) == 1:
        return [_run_args(j) for j in jobs]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_run_args, jobs, chunksize=1))


# ---------------------------------------------------------------------------------------------- levels, summaries, comparisons
def episode_view(res: dict, policy: str, arm: str) -> dict:
    """Per-episode arrays of one policy at one arm: valid, minutes, checks, entries, concluded, and whether the guess is right at the exact level and at v0's level."""
    base = res["base"]
    truth = [T.ALL_CAUSES[t] for t in base["truth_idx"]]
    if policy == "tool":
        a = base["arm"][arm]
        guess = [T.ALL_CAUSES[g] if v else None for g, v in zip(a["guess_idx"], a["valid"])]
        conc = a["concluded"] & a["valid"]
        q = a["questions"]
    else:
        a = res["pol"][policy][arm]
        guess = [GUESS_CAUSES[g] if v else None for g, v in zip(a["guess_idx"], a["valid"])]
        conc = a["valid"].copy()                                                    # a stand-in always concludes something
        q = np.zeros(res["n"])
    ok = lambda f: np.array([g is not None and f(g, t) for g, t in zip(guess, truth)], bool)  # noqa: E731
    return dict(valid=a["valid"], minutes=a["minutes"], checks=a["checks"], entries=a["entries"], questions=q, concluded=conc,
                exact=ok(lambda g, t: g == t), v0=ok(lambda g, t: C.v0_tag(g) == C.v0_tag(t)))


def subset_masks(res: dict) -> dict:
    hw = T.hw_mask(res["base"])
    return dict(hw=hw, doc=~hw)


def summarize(v: dict, mask: np.ndarray, level: str) -> dict:
    m = mask & v["valid"]
    if not m.any():
        return dict(n=0)
    ok, conc = v[level][m], v["concluded"][m]
    return dict(n=int(m.sum()), minutes=float(v["minutes"][m].mean()), accuracy=float(ok.mean()), wrong_confident=float((conc & ~ok).mean()), checks=float(v["checks"][m].mean()),
                entries=float(v["entries"][m].mean()), concluded=float(conc.mean()), per_correct=float(v["minutes"][m].mean() / max(ok.mean(), 1e-12)))


def break_even(m_t: float, a_t: float, m_s: float, a_s: float) -> tuple[str, float]:
    """The cost of a wrong diagnosis, in minutes, at which the tool and the stand-in tie. DOMINATES: the tool is no slower and no less accurate (0). DOMINATED: no faster and no more
    accurate (inf). SLOWER-MORE: slower and more accurate: the extra minutes a wrong diagnosis must cost before the tool's extra time pays. FASTER-LESS: faster and less accurate: the cost
    below which the tool is ahead."""
    if m_t <= m_s and a_t >= a_s:
        return "DOMINATES", 0.0
    if m_t >= m_s and a_t <= a_s:
        return "DOMINATED", float("inf")
    if m_t > m_s:
        return "SLOWER-MORE", (m_t - m_s) / (a_t - a_s)
    return "FASTER-LESS", (m_s - m_t) / (a_s - a_t)


def compare(res: dict, arm: str, stand: str, level: str, idx: np.ndarray, boot: np.ndarray) -> dict:
    """The tool minus a stand-in on the same episodes of `idx`, with Addendum 21's frozen labels (5% minutes, 0.02 accuracy, safety 0.02, paired 95% intervals)."""
    A, B = episode_view(res, "tool", arm), episode_view(res, stand, arm)
    d_min = A["minutes"][idx] - B["minutes"][idx]
    d_acc = A[level][idx].astype(float) - B[level][idx].astype(float)
    wcA, wcB = (A["concluded"] & ~A[level])[idx].astype(float), (B["concluded"] & ~B[level])[idx].astype(float)
    d_wc = wcA - wcB
    ci_min, ci_acc, ci_wc = S.paired_ci(d_min, boot), S.paired_ci(d_acc, boot), S.paired_ci(d_wc, boot)
    r_min = float(d_min.mean() / B["minutes"][idx].mean())
    ts, as_ = SG.time_state(r_min, ci_min), SG.acc_state(float(d_acc.mean()), ci_acc)
    kind, wstar = break_even(float(A["minutes"][idx].mean()), float(A[level][idx].mean()), float(B["minutes"][idx].mean()), float(B[level][idx].mean()))
    return dict(d_min=float(d_min.mean()), r_min=r_min, d_acc=float(d_acc.mean()), d_wc=float(d_wc.mean()), d_checks=float((A["checks"][idx] - B["checks"][idx]).mean()), ci_min=ci_min, ci_acc=ci_acc,
                ci_wc=ci_wc, time=ts, acc=as_, label=SG.label(ts, as_), safety=SG.safety_flag(float(d_wc.mean()), ci_wc), break_even=kind, wrong_cost=wstar)


def combos() -> list[tuple[str, str, str]]:
    """(stand-in, level, arm-independent tag) of every registered comparison: exact level against the checklists, v0 level against all three."""
    return [(s, "exact") for s in EXACT_STANDS] + [(s, "v0") for s in POLICIES]


def analyze_cell(res: dict, B: int = BOOT_B) -> dict:
    masks = subset_masks(res)
    boot = {}
    for si, sub in enumerate(SUBSETS):
        idx = np.flatnonzero(masks[sub])
        boot[sub] = (idx, np.random.default_rng([SEED, res["idx"], 99, si]).integers(0, len(idx), (B, len(idx))) if len(idx) else None)
    summ, cmp_ = {}, {}
    for arm in T.ARM_NAMES:
        views = {p: episode_view(res, p, arm) for p in ("tool",) + POLICIES}
        base_v0 = None
        for sub in SUBSETS:
            if arm == "T0" and sub == "doc":
                continue
            for p, v in views.items():
                for level in LEVELS:
                    if level == "exact" and p == "habit_A":
                        continue
                    summ[(p, arm, sub, level)] = summarize(v, masks[sub], level)
            m = masks[sub] & views["tool"]["valid"]
            base_v0 = float(np.mean([C.v0_tag(T.ALL_CAUSES[t]) == LUMPS[0] for t in res["base"]["truth_idx"][m]])) if m.any() else float("nan")
            summ[("baseline", arm, sub, "v0")] = dict(n=int(m.sum()), accuracy=base_v0)
            idx, bt = boot[sub]
            for stand, level in combos():
                if bt is not None and m.sum() == len(idx):
                    cmp_[(arm, stand, sub, level)] = compare(res, arm, stand, level, idx, bt)
    return dict(idx=res["idx"], cell=res["cell"], n_hw=int(masks["hw"].sum()), n_doc=int(masks["doc"].sum()), sum=summ, cmp=cmp_)


def cell_of(analyses: list[dict], **kw) -> dict:
    return T.cell_of(analyses, **kw)


def shares(analyses: list[dict], key: tuple) -> dict:
    """Shares of the cells by label for one (arm, stand-in, subset, level) comparison; the two kinds of TRADE; safety."""
    es = [a["cmp"][key] for a in analyses if key in a["cmp"]]
    n = max(len(es), 1)
    out = {k: sum(e["label"] == k for e in es) / n for k in ("IMPROVES", "WORSE", "TRADE", "NEITHER")}
    out["FASTER_LESS"] = sum(e["time"] == "FASTER" and e["acc"] == "LESS" for e in es) / n
    out["SLOWER_MORE"] = sum(e["time"] == "SLOWER" and e["acc"] == "MORE" for e in es) / n
    out["SAFETY_REGRESSION"] = sum(e["safety"] == "REGRESSION" for e in es) / n
    out["SAFETY_GAIN"] = sum(e["safety"] == "GAIN" for e in es) / n
    out["n_cells"] = len(es)
    return out


# ---------------------------------------------------------------------------------------------- predictions (frozen operationalisation)
def fast_predictions(analyses: list[dict]) -> dict:
    """P1-P9 of Addendum 28: each strict; P1-P8 in the primary cell on hardware-cause episodes (P6 at v0 level, the rest exact), P9 on documentation-wrong episodes."""
    pc = cell_of(analyses, **T.PRIMARY)["sum"]
    r2 = cell_of(analyses, rel="R2", mix="assumed", cover="full")["sum"]
    g = lambda s, p, a, sub="hw", lv="exact": s[(p, a, sub, lv)]  # noqa: E731
    arms = T.ARM_NAMES
    p = {}
    p["P1"] = dict(values={a: (g(pc, "fast_list", a)["minutes"], g(pc, "tool", a)["minutes"]) for a in arms[:4]}, holds=all(g(pc, "fast_list", a)["minutes"] < g(pc, "tool", a)["minutes"] for a in arms[:4]))
    p["P2"] = dict(values={a: (g(pc, "tool", a)["accuracy"], g(pc, "fast_list", a)["accuracy"]) for a in arms}, holds=all(g(pc, "tool", a)["accuracy"] > g(pc, "fast_list", a)["accuracy"] for a in arms))
    p["P3"] = dict(values={a: (g(pc, "tool", a)["wrong_confident"], g(pc, "fast_list", a)["wrong_confident"]) for a in arms},
                   holds=all(g(pc, "tool", a)["wrong_confident"] < g(pc, "fast_list", a)["wrong_confident"] for a in arms))
    p["P4"] = dict(values={a: (g(pc, "fast_confirm", a)["minutes"], g(pc, "fast_list", a)["minutes"], g(pc, "fast_confirm", a)["accuracy"], g(pc, "fast_list", a)["accuracy"]) for a in arms},
                   holds=all(g(pc, "fast_confirm", a)["minutes"] > g(pc, "fast_list", a)["minutes"] and g(pc, "fast_confirm", a)["accuracy"] >= g(pc, "fast_list", a)["accuracy"] for a in arms))
    p["P5"] = dict(values={a: (g(pc, "tool", a)["accuracy"], g(pc, "fast_confirm", a)["accuracy"]) for a in arms}, holds=all(g(pc, "tool", a)["accuracy"] > g(pc, "fast_confirm", a)["accuracy"] for a in arms))
    p["P6"] = dict(values={a: (g(pc, "tool", a, lv="v0")["accuracy"], g(pc, "habit_A", a, lv="v0")["accuracy"]) for a in arms[1:]},
                   holds=all(g(pc, "tool", a, lv="v0")["accuracy"] > g(pc, "habit_A", a, lv="v0")["accuracy"] for a in arms[1:]))
    adv = lambda s, a: g(s, "tool", a)["accuracy"] - g(s, "fast_list", a)["accuracy"]  # noqa: E731
    p["P7"] = dict(values={a: (adv(r2, a), adv(pc, a)) for a in arms}, holds=all(adv(r2, a) < adv(pc, a) for a in arms))
    ratio = lambda a: g(pc, "tool", a)["minutes"] / g(pc, "fast_list", a)["minutes"]  # noqa: E731
    p["P8"] = dict(values=(ratio("T3"), ratio("T0")), holds=ratio("T3") < ratio("T0"))
    p["P9"] = dict(values={a: (g(pc, "tool", a, "doc")["accuracy"], g(pc, "fast_list", a, "doc")["accuracy"]) for a in arms[1:]},
                   holds=all(g(pc, "tool", a, "doc").get("n", 0) > 0 and g(pc, "tool", a, "doc")["accuracy"] > g(pc, "fast_list", a, "doc")["accuracy"] for a in arms[1:]))
    return p


# ---------------------------------------------------------------------------------------------- gates
def gate_g1(results: list[dict], raw_path: Path | None = RAW27) -> tuple[bool, str]:
    """Code path. (a) On the v0-equivalent tree `habit_A` reproduces v0's `sim.simulate_habit` exactly (guess, minutes, checks) on the study's building. (b) If Addendum 27's raw file exists, the
    tool's arrays in every cell equal it exactly (the tool has not drifted since); if it does not, that part is skipped and said so."""
    from ..building import make_case
    b = T.make_building1("full")
    n = 0
    for room in (0, 5):
        c0 = make_case(b.base, f"Room-{room}", max_candidates=T.N_BOXES)
        c1 = make_case_v1(b, f"Room-{room}", "T1", compat_v0=True, max_candidates=T.N_BOXES)
        causes = M.make_prior("vav_zone", c0.candidates, c0.doc, c0.settings, None, c0.weights)[0]
        for k, truth in enumerate(causes):
            r0 = sim.simulate_habit(c0, truth, np.random.default_rng(k))
            w = World(truth)
            r1 = run_habit_A(c1, w.context, ask_from_world(c1, w, np.random.default_rng(k)))
            if (r0["guess"], r0["n_checks"]) != (r1["guess"], r1["n_checks"]) or abs(r0["minutes"] - r1["minutes"]) > 1e-9:
                return False, f"habit_A differs from v0's simulate_habit (room {room}, truth {truth!r})"
            n += 1
    if raw_path is None or not Path(raw_path).exists():
        return True, f"habit_A = v0's simulate_habit on {n} episodes; Addendum 27's raw file not found: the tool comparison is SKIPPED"
    old = {r["idx"]: r for r in pickle.loads(Path(raw_path).read_bytes())}
    for r in results:
        o = old.get(r["idx"])
        if o is None:
            return False, f"cell {r['idx']} is not in Addendum 27's raw file"
        for arm in T.ARM_NAMES:
            for k in ("minutes", "checks", "questions", "entries", "concluded", "stalled", "correct", "guess_idx", "valid"):
                x, y = r["base"]["arm"][arm][k][: o["n"]], o["arm"][arm][k][: r["n"]]
                if not (np.array_equal(x, y, equal_nan=True) if x.dtype.kind == "f" else np.array_equal(x, y)):
                    return False, f"the tool's {k} differs from Addendum 27's in cell {r['idx']} arm {arm}"
            if r["base"]["arm"][arm]["sequence"][: o["n"]] != o["arm"][arm]["sequence"][: r["n"]]:
                return False, f"the tool's check sequences differ from Addendum 27's in cell {r['idx']} arm {arm}"
    return True, f"habit_A = v0's simulate_habit on {n} episodes; the tool's episodes equal Addendum 27's raw file in all {len(results)} cells"


def _script(cases_arm, ctx, answers):
    """Run fast_list / fast_confirm with a fixed answer script (a list of words, in order asked)."""
    it = iter(answers)
    return lambda ck, target: next(it)


def gate_g2(results: list[dict] | None = None, per_arm: int = 10) -> tuple[bool, str]:
    """Accounting. (a) Scripted transcripts cost the hand-summed minutes. At T2 (room 0, no reheat, every fact true except control-system access): the checklist starts with design_load (0 + 6 = 6), then
    controller lights (walk to the box 6 + 3 = 9) then the 24 VAC reading (already at the box: 4); with the third abnormal, 6 + 9 + 4 = 19 concluding no_power. At T3 (room 1): fan status 2 (abnormal) and,
    for `fast_confirm`, the cheapest other check that sees a fan fault (airflow against setpoint: 2 minutes; ties by name) = 4, concluding ahu_fan_off. (b) Replay: the first `per_arm` valid episodes of every stand-in and arm in every degraded-reliability cell of
    `results`, fed only their recorded answers, ask for the same checks in the same order."""
    cases = T.make_cases("full")
    ctx2 = dict(reheat="no", bas_access="no", instrument="yes", occupant="yes")
    r = run_fast(cases[("T2", 0)], ctx2, _script(None, ctx2, ["normal", "normal", "abnormal"]))
    if r["guess"] != ("no_power",) or r["minutes"] != 19 or r["sequence"] != ("design_load", "controller_leds", "power_24vac"):
        return False, f"T2 fast_list transcript costs {r['minutes']}: {r['sequence']} -> {r['guess']}"
    ctx3 = dict(reheat="yes", bas_access="yes", instrument="yes", occupant="yes")
    r = run_fast(cases[("T3", 1)], ctx3, _script(None, ctx3, ["abnormal"]))
    if r["guess"] != ("ahu_fan_off",) or r["minutes"] != 2 or r["sequence"] != ("bas_ahu_fan",):
        return False, f"T3 fast_list transcript costs {r['minutes']}: {r['sequence']}"
    r = run_fast(cases[("T3", 1)], ctx3, _script(None, ctx3, ["abnormal", "abnormal"]), confirm=True)
    if r["guess"] != ("ahu_fan_off",) or r["minutes"] != 4 or r["sequence"] != ("bas_ahu_fan", "bas_airflow"):
        return False, f"T3 fast_confirm transcript costs {r['minutes']}: {r['sequence']}"
    n = 0
    for res in results or []:
        if res["cell"].rel == "R0":
            continue
        cs = T.make_cases(res["cell"].cover)
        for pol in POLICIES:
            for arm in T.ARM_NAMES:
                a = res["pol"][pol][arm]
                for i in np.flatnonzero(a["valid"])[:per_arm]:
                    n += 1
                    room = int(res["base"]["room"][i])
                    ep = dict(room=room, truth=("other",), instrument=bool(res["base"]["instrument"][i]), occupant=bool(res["base"]["occupant"][i]))
                    if not replay(pol, cs[(arm, room)], T.world_for(ep, arm, None).context, a["trace"][i]):
                        return False, f"cell {res['idx']} {pol} {arm} episode {i}: replaying the recorded answers gives different checks"
    return True, f"hand-summed minutes agree; {n} degraded-reliability stand-in episodes replay identically from their answers alone"


def gate_g3(results: list[dict]) -> tuple[bool, str]:
    """Availability: every check a stand-in performed was available at its arm given the world's true facts, and none was done twice on the same target."""
    for res in results:
        cases = T.make_cases(res["cell"].cover)
        for pol in POLICIES:
            for arm in T.ARM_NAMES:
                a = res["pol"][pol][arm]
                for i in np.flatnonzero(a["valid"]):
                    room = int(res["base"]["room"][i])
                    s = Session(cases[(arm, room)])
                    s.ctx = D.Context(reheat="yes" if T.true_reheat(room) else "no", bas_access="yes" if "bas_access" in T.ARMS[arm] else "no",
                                      instrument="yes" if res["base"]["instrument"][i] else "no", occupant="yes" if res["base"]["occupant"][i] else "no")
                    pairs = [(x[1], x[2]) for x in a["trace"][i]]
                    if len(set(pairs)) != len(pairs):
                        return False, f"cell {res['idx']} {pol} {arm} episode {i}: a check was done twice"
                    for name, _ in pairs:
                        ck = s._check(name)
                        if D.availability(ck, s.view(), s._eq(ck)).state == "unavailable":
                            return False, f"cell {res['idx']} {pol} {arm} episode {i}: {name} was performed but is unavailable there"
    return True, "ok"


def gate_g4(results: list[dict], n: int = 50) -> tuple[bool, str]:
    """Reproducibility: the first cell re-run with `n` episodes reproduces its first `n` stored episodes of every stand-in and arm (numbers, guesses, traces)."""
    first = min(results, key=lambda r: r["idx"])
    again = run_cell(first["idx"], first["cell"], n)
    for pol in POLICIES:
        for arm in T.ARM_NAMES:
            for k in ("minutes", "checks", "entries", "guess_idx", "valid"):
                x, y = first["pol"][pol][arm][k][:n], again["pol"][pol][arm][k]
                same = np.array_equal(x, y, equal_nan=True) if x.dtype.kind == "f" else np.array_equal(x, y)
                if not same:
                    return False, f"{pol} {arm} field {k} differs on re-run"
            if first["pol"][pol][arm]["trace"][:n] != again["pol"][pol][arm]["trace"]:
                return False, f"{pol} {arm} traces differ on re-run"
    return True, f"first {n} episodes of cell {first['idx']} reproduce"


def gate_g5(results: list[dict], n_cells: int = 12, expected_idx: list[int] | None = None) -> tuple[bool, str]:
    """Completeness and pairing: all cells, arms and policies present; valid exactly where the tool's are (T0 on hardware-cause episodes only); minutes finite, of full length, and a guess for every
    valid episode; and `habit_A` identical at T1, T2, T2+access and T3 (it uses none of the arm's data)."""
    want = list(range(n_cells)) if expected_idx is None else sorted(expected_idx)
    if len(results) != len(want) or sorted(r["idx"] for r in results) != want:
        return False, f"{len(results)} cells present, expected {len(want)}"
    for r in results:
        if set(r["pol"]) != set(POLICIES):
            return False, f"cell {r['idx']}: policies {sorted(r['pol'])}"
        for pol in POLICIES:
            if set(r["pol"][pol]) != set(T.ARM_NAMES):
                return False, f"cell {r['idx']} {pol}: arms {sorted(r['pol'][pol])}"
            for arm, a in r["pol"][pol].items():
                if not np.array_equal(a["valid"], r["base"]["arm"][arm]["valid"]):
                    return False, f"cell {r['idx']} {pol} {arm}: valid episodes differ from the tool's"
                if len(a["minutes"]) != r["n"] or not np.isfinite(a["minutes"][a["valid"]]).all():
                    return False, f"cell {r['idx']} {pol} {arm}: non-finite or short minutes"
                if (a["guess_idx"][a["valid"]] < 0).any():
                    return False, f"cell {r['idx']} {pol} {arm}: a valid episode has no guess"
        h = r["pol"]["habit_A"]
        for arm in ("T2", "T2+access", "T3"):
            if not (np.array_equal(h["T1"]["guess_idx"], h[arm]["guess_idx"]) and np.array_equal(h["T1"]["minutes"], h[arm]["minutes"])):
                return False, f"cell {r['idx']}: habit_A at {arm} differs from T1"
    return True, "ok"
