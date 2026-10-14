"""The v1 tool against the tool as it was before (v0) on the same complaints (PREREGISTRATION_DR.md Addendum 29). Simulation only.

Addendum 27's episodes and answers; the v1 arms are Addendum 27's, reproduced by its runner. The v0 policy is the v0-equivalent tree of v1 (`compat_v0=True`), which reproduces v0's sessions
exactly; it has the data of T1 and can answer only in v0's four lumps, so the comparison is at v0's level. Nothing here is evidence about real technicians.
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
from . import study_fast_v1 as F
from . import study_tiers as T
from .engine import Session, make_case_v1
from .sim1 import World

SEED = 29
N_EPISODES = T.N_EPISODES
BOOT_B = T.BOOT_B
V1_ARMS = ("T1", "T2", "T2+access", "T3")
SUBSETS = F.SUBSETS
RAW27 = F.RAW27


def compat_cases(cover: str) -> dict:
    b = T.make_building1(cover)
    return {room: make_case_v1(b, f"Room-{room}", "T1", compat_v0=True, max_candidates=T.N_BOXES) for room in range(T.N_BOXES)}


def run_v0(case, ask, max_checks: int = T.MAX_CHECKS) -> dict:
    """A session of the v0-equivalent tree; `ask(check, target)` gives the answer word. Stops at tau, at `max_checks`, or when nothing more would help."""
    sess = Session(case, "entropy", None)
    trace = []
    while len(sess.log) < max_checks:
        step = sess.next_step()
        if step is None:
            break
        word = ask(step.check, step.target)
        trace.append(("C", step.check.name, step.target, word))
        sess.report(word)
    st = sess.status()
    return dict(guess=st["ranked"][0][0], concluded=st["concluded"], minutes=sess.elapsed, n_checks=st["n_checks"], entries=st["entries"], trace=trace)


def replay(case, trace: list) -> bool:
    try:
        return run_v0(case, F.ask_from_trace(trace))["trace"] == [tuple(x) for x in trace]
    except ValueError:
        return False


def run_cell(idx: int, cell: T.Cell, n: int = N_EPISODES) -> dict:
    base = T.run_cell(idx, cell, n)
    ccases, cases = compat_cases(cell.cover), T.make_cases(cell.cover)
    tc = K.degrade_all(K.CATALOGUE, T.REL_A[cell.rel])
    rows = []
    for i in range(n):
        e = T.draw_episode(idx, i, cell.mix, cases)
        w = T.world_for(e, "T1", tc)
        case = ccases[e["room"]]
        rows.append(run_v0(case, F.ask_from_world(case, w, np.random.default_rng([SEED, idx, 0, i]))))
    v0 = dict(minutes=np.array([r["minutes"] for r in rows], float), checks=np.array([r["n_checks"] for r in rows], float), entries=np.array([r["entries"] for r in rows], float),
              concluded=np.array([r["concluded"] for r in rows], bool), guess_idx=np.array([F.GUESS_INDEX[r["guess"]] for r in rows]), trace=[r["trace"] for r in rows])
    return dict(idx=idx, cell=cell, n=n, base=base, v0=v0)


def _run_args(args):
    return run_cell(*args)


def compute_cells(cells: list[tuple[int, T.Cell]], n: int = N_EPISODES, workers: int | None = None) -> list[dict]:
    jobs = [(i, c, n) for i, c in cells]
    workers = workers if workers is not None else min(8, os.cpu_count() or 1)
    if workers <= 1 or len(jobs) == 1:
        return [_run_args(j) for j in jobs]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_run_args, jobs, chunksize=1))


# ---------------------------------------------------------------------------------------------- views, comparisons
def view_v0(res: dict) -> dict:
    a = res["v0"]
    truth = [T.ALL_CAUSES[t] for t in res["base"]["truth_idx"]]
    ok = np.array([C.v0_tag(F.GUESS_CAUSES[g]) == C.v0_tag(t) for g, t in zip(a["guess_idx"], truth)], bool)
    return dict(valid=np.ones(res["n"], bool), minutes=a["minutes"], checks=a["checks"], entries=a["entries"], questions=np.zeros(res["n"]), concluded=a["concluded"], v0=ok, exact=ok)


def compare(A: dict, B: dict, idx: np.ndarray, boot: np.ndarray) -> dict:
    """v1 (A) minus v0 (B) on the same episodes of `idx`, at v0's level, with Addendum 21's frozen labels."""
    d_min = A["minutes"][idx] - B["minutes"][idx]
    d_acc = A["v0"][idx].astype(float) - B["v0"][idx].astype(float)
    d_wc = (A["concluded"] & ~A["v0"])[idx].astype(float) - (B["concluded"] & ~B["v0"])[idx].astype(float)
    ci_min, ci_acc, ci_wc = S.paired_ci(d_min, boot), S.paired_ci(d_acc, boot), S.paired_ci(d_wc, boot)
    r_min = float(d_min.mean() / B["minutes"][idx].mean())
    ts, as_ = SG.time_state(r_min, ci_min), SG.acc_state(float(d_acc.mean()), ci_acc)
    kind, wstar = F.break_even(float(A["minutes"][idx].mean()), float(A["v0"][idx].mean()), float(B["minutes"][idx].mean()), float(B["v0"][idx].mean()))
    return dict(d_min=float(d_min.mean()), r_min=r_min, d_acc=float(d_acc.mean()), d_wc=float(d_wc.mean()), d_checks=float((A["checks"][idx] - B["checks"][idx]).mean()), ci_min=ci_min, ci_acc=ci_acc,
                ci_wc=ci_wc, time=ts, acc=as_, label=SG.label(ts, as_), safety=SG.safety_flag(float(d_wc.mean()), ci_wc), break_even=kind, wrong_cost=wstar)


def analyze_cell(res: dict, B: int = BOOT_B) -> dict:
    masks = F.subset_masks(res)
    v0 = view_v0(res)
    summ, cmp_ = {}, {}
    for si, sub in enumerate(SUBSETS):
        idx = np.flatnonzero(masks[sub])
        summ[("v0", sub)] = F.summarize(v0, masks[sub], "v0")
        summ[("baseline", sub)] = dict(n=int(len(idx)), accuracy=float(np.mean([C.v0_tag(T.ALL_CAUSES[t]) == F.LUMPS[0] for t in res["base"]["truth_idx"][idx]])) if len(idx) else float("nan"))
        boot = np.random.default_rng([SEED, res["idx"], 99, si]).integers(0, len(idx), (B, len(idx))) if len(idx) else None
        for arm in V1_ARMS:
            v1 = F.episode_view(res, "tool", arm)
            for level in ("v0", "exact"):
                summ[("v1", arm, sub, level)] = F.summarize(v1, masks[sub], level)
            if boot is not None:
                cmp_[(arm, sub)] = compare(v1, v0, idx, boot)
    return dict(idx=res["idx"], cell=res["cell"], n_hw=int(masks["hw"].sum()), n_doc=int(masks["doc"].sum()), sum=summ, cmp=cmp_)


def shares(analyses: list[dict], key: tuple) -> dict:
    es = [a["cmp"][key] for a in analyses if key in a["cmp"]]
    n = max(len(es), 1)
    out = {k: sum(e["label"] == k for e in es) / n for k in ("IMPROVES", "WORSE", "TRADE", "NEITHER")}
    out["FASTER_LESS"] = sum(e["time"] == "FASTER" and e["acc"] == "LESS" for e in es) / n
    out["SLOWER_MORE"] = sum(e["time"] == "SLOWER" and e["acc"] == "MORE" for e in es) / n
    out["SAFETY_REGRESSION"] = sum(e["safety"] == "REGRESSION" for e in es) / n
    out["SAFETY_GAIN"] = sum(e["safety"] == "GAIN" for e in es) / n
    out["n_cells"] = len(es)
    return out


def predictions(analyses: list[dict]) -> dict:
    """P1-P7 of Addendum 29 (each strict; primary cell, hardware-cause episodes, v0's level unless stated)."""
    pc = T.cell_of(analyses, **T.PRIMARY)["sum"]
    r2 = T.cell_of(analyses, rel="R2", mix="assumed", cover="full")["sum"]
    v1 = lambda s, arm, sub="hw": s[("v1", arm, sub, "v0")]  # noqa: E731
    v0 = lambda s, sub="hw": s[("v0", sub)]  # noqa: E731
    p = {}
    p["P1"] = dict(values={a: (v1(pc, a)["minutes"], v0(pc)["minutes"]) for a in V1_ARMS}, holds=all(v1(pc, a)["minutes"] > v0(pc)["minutes"] for a in V1_ARMS))
    p["P2"] = dict(values=(v1(pc, "T1")["checks"], v0(pc)["checks"]), holds=v1(pc, "T1")["checks"] > v0(pc)["checks"])
    p["P3"] = dict(values=(v1(pc, "T1")["accuracy"], v0(pc)["accuracy"]), holds=v1(pc, "T1")["accuracy"] - v0(pc)["accuracy"] >= 0.05)
    p["P4"] = dict(values=(v0(pc)["wrong_confident"], v1(pc, "T1")["wrong_confident"]), holds=v0(pc)["wrong_confident"] > v1(pc, "T1")["wrong_confident"])
    p["P5"] = dict(values=(v1(pc, "T1", "doc")["accuracy"], v0(pc, "doc")["accuracy"]), holds=v1(pc, "T1", "doc")["accuracy"] >= v0(pc, "doc")["accuracy"] - 0.02)
    every = [a["sum"][("v1", "T1", "hw", "v0")]["minutes"] > a["sum"][("v0", "hw")]["minutes"] for a in analyses]
    p["P6"] = dict(values=(sum(every), len(every)), holds=all(every))
    adv = lambda s: v1(s, "T1")["accuracy"] - v0(s)["accuracy"]  # noqa: E731
    p["P7"] = dict(values=(adv(r2), adv(pc)), holds=adv(r2) < adv(pc))
    return p


# ---------------------------------------------------------------------------------------------- gates
def gate_g1(results: list[dict], raw_path: Path | None = RAW27) -> tuple[bool, str]:
    """(a) The v0 policy reproduces v0's `sim.simulate` exactly on v0's own causes; (b) if Addendum 27's raw file exists the v1 arms equal it exactly (skipped and said so if not)."""
    from ..building import make_case
    b = T.make_building1("full")
    n = 0
    for room in (0, 5):
        c0 = make_case(b.base, f"Room-{room}", max_candidates=T.N_BOXES)
        c1 = make_case_v1(b, f"Room-{room}", "T1", compat_v0=True, max_candidates=T.N_BOXES)
        causes = M.make_prior("vav_zone", c0.candidates, c0.doc, c0.settings, None, c0.weights)[0]
        for k, truth in enumerate(causes[:6]):
            r0 = sim.simulate(c0, truth, "entropy", np.random.default_rng(k))
            r1 = run_v0(c1, F.ask_from_world(c1, World(truth), np.random.default_rng(k)))
            if (r0["guess"], r0["n_checks"], r0["concluded"]) != (r1["guess"], r1["n_checks"], r1["concluded"]) or abs(r0["minutes"] - r1["minutes"]) > 1e-9:
                return False, f"the v0 policy differs from v0's simulate (room {room}, truth {truth!r})"
            n += 1
    if raw_path is None or not Path(raw_path).exists():
        return True, f"v0 policy = v0's simulate on {n} episodes; Addendum 27's raw file not found: the v1 comparison is SKIPPED"
    old = {r["idx"]: r for r in pickle.loads(Path(raw_path).read_bytes())}
    for r in results:
        o = old.get(r["idx"])
        if o is None:
            return False, f"cell {r['idx']} is not in Addendum 27's raw file"
        for arm in T.ARM_NAMES:
            for k in ("minutes", "checks", "questions", "entries", "concluded", "stalled", "correct", "guess_idx", "valid"):
                x, y = r["base"]["arm"][arm][k][: o["n"]], o["arm"][arm][k][: r["n"]]
                if not (np.array_equal(x, y, equal_nan=True) if x.dtype.kind == "f" else np.array_equal(x, y)):
                    return False, f"the v1 arm {arm}'s {k} differs from Addendum 27's in cell {r['idx']}"
    return True, f"v0 policy = v0's simulate on {n} episodes; the v1 arms equal Addendum 27's raw file in all {len(results)} cells"


def gate_g2(results: list[dict] | None = None, per_cell: int = 10) -> tuple[bool, str]:
    """(a) Two yes answers cost the hand-summed 9 + 5 = 14 minutes (confirm_acts, then the diffuser override on the documented box) and conclude 'the box acts, cause elsewhere'; (b) the first
    `per_cell` v0 episodes of every degraded-reliability cell replay identically from their recorded answers alone."""
    cc = compat_cases("full")
    r = run_v0(cc[0], lambda ck, target: ck.words[0])
    if r["guess"] != ("doc_other",) or r["minutes"] != 14 or [t[1] for t in r["trace"]] != ["confirm_acts", "override_diffuser"] or not r["concluded"]:
        return False, f"scripted v0 transcript: {[t[1] for t in r['trace']]} costs {r['minutes']} -> {r['guess']}"
    n = 0
    for res in results or []:
        if res["cell"].rel == "R0":
            continue
        cs = compat_cases(res["cell"].cover)
        for i in range(min(per_cell, res["n"])):
            n += 1
            if not replay(cs[int(res["base"]["room"][i])], res["v0"]["trace"][i]):
                return False, f"cell {res['idx']} episode {i}: replaying the recorded answers gives different checks"
    return True, f"hand-summed minutes agree; {n} degraded-reliability v0 episodes replay identically from their answers alone"


def gate_g3(results: list[dict], n: int = 50) -> tuple[bool, str]:
    first = min(results, key=lambda r: r["idx"])
    again = run_cell(first["idx"], first["cell"], n)
    for k in ("minutes", "checks", "entries", "concluded", "guess_idx"):
        if not np.array_equal(first["v0"][k][:n], again["v0"][k]):
            return False, f"v0 field {k} differs on re-run"
    if first["v0"]["trace"][:n] != again["v0"]["trace"]:
        return False, "v0 traces differ on re-run"
    return True, f"first {n} episodes of cell {first['idx']} reproduce"


def gate_g4(results: list[dict], n_cells: int = 12, expected_idx: list[int] | None = None) -> tuple[bool, str]:
    want = list(range(n_cells)) if expected_idx is None else sorted(expected_idx)
    if len(results) != len(want) or sorted(r["idx"] for r in results) != want:
        return False, f"{len(results)} cells present, expected {len(want)}"
    for r in results:
        a = r["v0"]
        if len(a["minutes"]) != r["n"] or not np.isfinite(a["minutes"]).all() or (a["guess_idx"] < 0).any():
            return False, f"cell {r['idx']}: v0 arrays incomplete"
        for arm in V1_ARMS:
            if not r["base"]["arm"][arm]["valid"].all():
                return False, f"cell {r['idx']}: v1 arm {arm} is not valid on every episode"
    return True, "ok"
