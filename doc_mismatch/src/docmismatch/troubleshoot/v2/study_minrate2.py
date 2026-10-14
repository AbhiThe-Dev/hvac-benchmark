"""Does the live default (`min_rate` = 0.015, chosen by the user beyond Addendum 35's confirmed 0.01) hold up across both tiers and the other cells? (PREREGISTRATION_DR.md Addendum 36.) A
parameter sweep of the tool's own engine (`min_rate` only; `tau` fixed at its default) on all 18 of Addendum 30's cells; no LLM. Simulation only; nothing here is evidence about real
technicians. A separate, frozen module from `study_minrate.py` (Addendum 35): nothing here changes that addendum's own reproducibility, and nothing there changes this one's.
"""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from .. import study as S
from .. import study_rating as SG
from ..v1.engine import make_case_v1
from ..v1.study_fast_v1 import break_even
from . import policies as P
from . import study_joint as J
from . import world2 as W
from .joint import JointSettings
from .study_llm import TableOracle

# ---------------------------------------------------------------------------------------------- frozen constants (Addendum 36)
SEED = 36
N_EPISODES = J.N_EPISODES                  # 1000, Addendum 30's cell size
BOOT_B = J.BOOT_B
TIERS = J.TIERS
SUBSETS = J.SUBSETS
BASE_MIN_RATE = 0.003
CHALLENGER = 0.015                         # frozen: this addendum's own value, chosen by the user beyond Addendum 35's confirmed 0.01. Was also v2/cli.py's live default until 2026-09-29,
                                            # when the live default moved to 0.02 (a later, separate decision); this constant does not track that and must not change.
GRID = (BASE_MIN_RATE, CHALLENGER)
TIME_R, ACC_TOL, SAFE_TOL = SG.TIME_R, SG.ACC_TOL, SG.SAFE_TOL
UNSAFE_BAR, UNSAFE_CELLS = J.UNSAFE_BAR, J.UNSAFE_CELLS   # 0.02, 2 (Addendum 30's convention)
MAJORITY_CELLS = 15                        # of 18
WORSE_BAR = 1                               # at most this many cells may be WORSE
# Reference for P6/gate G4: this session's own primary-cell numbers for 0.015, computed and given to the user BEFORE they chose it and before this addendum's cells were run
# (no earlier addendum measured 0.015; Addendum 34/35's own reference numbers are for 0.01 and live in study_minrate.py, untouched by this module).
REF_T2_MIN, REF_T2_ACC = 67.9, 0.770
REF_T3_MIN, REF_T3_ACC = 52.1, 0.827


def cases_with(tier: str, min_rate: float, bld=None) -> dict:
    """{room -> CaseV1}, the routine's engine with `min_rate` swept; `tau` and everything else are the tool's own defaults."""
    bld = bld or W.make_building2()
    s = W.tool_settings()
    return {r: make_case_v1(bld, f"Room-{r}", W.TIER_ITEMS[tier], settings=s, context=W.tier_context(tier, r), member_name=f"Room {r}", min_rate=min_rate) for r in range(W.N_BOX)}


def run_variant_events(tier: str, min_rate: float, events: list, wp: W.WorldParams, bld) -> dict:
    cases_by_room = cases_with(tier, min_rate, bld)
    js = JointSettings()
    mins, chk, ok, wc, cn = [], [], [], [], []
    for ev in events:
        cs = [cases_by_room[r] for r in ev.rooms]
        ctxs = [W.context_dict(tier, r) for r in ev.rooms]
        r = P.run_policy("tool_ticket_memo2", cs, TableOracle(ev, wp.rel_a), ctxs, js)
        a, b, c = J.score(r, ev)
        mins.append(r["minutes"])
        chk.append(r["n_checks"])
        ok.append(a)
        wc.append(b)
        cn.append(c)
    n = np.array([e.n for e in events], float)
    correct, wca, cna = np.array(ok, float), np.array(wc, float), np.array(cn, float)
    # `acc`, `conc` and `wc` are per-visit RATES (Addendum 30's `per_event` convention, which `J.summarize` and `J.subset_masks`-based code expect); `correct` stays a raw count.
    return dict(minutes=np.array(mins, float), checks=np.array(chk, float), correct=correct, wc=wca / n, concluded=cna, n=n, acc=correct / n, conc=cna / n)


def run_cell(idx: int, cell: J.Cell, n: int = N_EPISODES) -> dict:
    """Every (tier, min_rate) variant of one cell, on the SAME `n` events (stream `[30, idx, 0, i]`, exactly Addendum 30's)."""
    bld = W.make_building2()
    cases_all = W.make_cases(bld)
    wp = cell.params()
    events = [W.draw_event(idx, i, wp, cases_all) for i in range(n)]
    out = dict(idx=idx, cell=cell, n=n, kind=np.array([e.kind for e in events]))
    for tier in TIERS:
        for mr in GRID:
            out[(tier, mr)] = run_variant_events(tier, mr, events, wp, bld)
    return out


def _run_args(args):
    return run_cell(*args)


def compute_cells(cells: list[tuple[int, J.Cell]], n: int = N_EPISODES, workers: int | None = None) -> list[dict]:
    """Deterministic whatever the number of workers (every cell has its own seeds)."""
    jobs = [(i, c, n) for i, c in cells]
    workers = workers if workers is not None else min(8, os.cpu_count() or 1)
    if workers <= 1 or len(jobs) == 1:
        return [_run_args(j) for j in jobs]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_run_args, jobs, chunksize=1))


def compare(a: dict, base: dict, idx: np.ndarray, boot: np.ndarray) -> dict:
    """`a` minus the baseline variant, paired on the same events (Addendum 21's labels)."""
    d_min, d_acc, d_wc = a["minutes"][idx] - base["minutes"][idx], a["acc"][idx] - base["acc"][idx], a["wc"][idx] - base["wc"][idx]
    ci_min, ci_acc, ci_wc = S.paired_ci(d_min, boot), S.paired_ci(d_acc, boot), S.paired_ci(d_wc, boot)
    base_min = float(base["minutes"][idx].mean())
    r_min = float(d_min.mean() / base_min) if base_min > 0 else float("nan")
    ts, as_ = SG.time_state(r_min, ci_min), SG.acc_state(float(d_acc.mean()), ci_acc)
    kind, wstar = break_even(float(a["minutes"][idx].mean()), float(a["acc"][idx].mean()), base_min, float(base["acc"][idx].mean()))
    return dict(d_min=float(d_min.mean()), r_min=r_min, d_acc=float(d_acc.mean()), d_wc=float(d_wc.mean()), ci_min=ci_min, ci_acc=ci_acc, ci_wc=ci_wc, time=ts, acc=as_,
                label=SG.label(ts, as_), safety=SG.safety_flag(float(d_wc.mean()), ci_wc), break_even=kind, wrong_cost=wstar)


def analyze_cell(out: dict, B: int = BOOT_B) -> dict:
    masks = J.subset_masks(out)
    boot = {}
    for si, sub in enumerate(SUBSETS):
        idx = np.flatnonzero(masks[sub])
        boot[sub] = (idx, np.random.default_rng([SEED, out["idx"], 99, si]).integers(0, len(idx), (B, len(idx))) if len(idx) else None)
    summ, cmp_ = {}, {}
    for tier in TIERS:
        for mr in GRID:
            v = out[(tier, mr)]
            for sub in SUBSETS:
                summ[(tier, mr, sub)] = J.summarize(v, masks[sub])
        base_v = out[(tier, BASE_MIN_RATE)]
        v = out[(tier, CHALLENGER)]
        for sub in SUBSETS:
            idx, bt = boot[sub]
            if bt is not None:
                cmp_[(tier, CHALLENGER, sub)] = compare(v, base_v, idx, bt)
    return dict(idx=out["idx"], cell=out["cell"], n=out["n"], counts={s: int(masks[s].sum()) for s in SUBSETS}, sum=summ, cmp=cmp_)


def shares(analyses: list[dict], key: tuple) -> dict:
    return J.shares(analyses, key)


def cell_of(analyses: list[dict], **kw) -> dict:
    return J.cell_of(analyses, **kw)


# ---------------------------------------------------------------------------------------------- predictions and decision (frozen operationalisation)
def predictions(analyses: list[dict]) -> dict:
    p = {}
    sh_t2 = shares(analyses, ("T2", CHALLENGER, "all"))
    sh_t3 = shares(analyses, ("T3", CHALLENGER, "all"))
    real_t2 = sh_t2["IMPROVES"]
    real_t3 = sh_t3["IMPROVES"]
    p["P1"] = (round(real_t2 * 18) >= MAJORITY_CELLS, f"T2: IMPROVES in {round(real_t2 * 18)} of 18 cells")
    p["P2"] = (round(real_t3 * 18) >= MAJORITY_CELLS, f"T3: IMPROVES in {round(real_t3 * 18)} of 18 cells")
    worse = max(round(sh_t2["WORSE"] * 18), round(sh_t3["WORSE"] * 18))
    p["P3"] = (worse <= WORSE_BAR, f"WORSE in {round(sh_t2['WORSE'] * 18)} of 18 cells at T2, {round(sh_t3['WORSE'] * 18)} at T3")
    unsafe_t2, unsafe_t3 = round(sh_t2["SAFETY_REGRESSION"] * 18), round(sh_t3["SAFETY_REGRESSION"] * 18)
    p["P4"] = (unsafe_t2 <= UNSAFE_CELLS and unsafe_t3 <= UNSAFE_CELLS, f"safety regressions: {unsafe_t2} of 18 at T2, {unsafe_t3} at T3")
    m0 = sum(1 for a in analyses if a["cell"].map == "M0" and ("T2", CHALLENGER, "all") in a["cmp"] and a["cmp"][("T2", CHALLENGER, "all")]["safety"] == "REGRESSION")
    m0 += sum(1 for a in analyses if a["cell"].map == "M0" and ("T3", CHALLENGER, "all") in a["cmp"] and a["cmp"][("T3", CHALLENGER, "all")]["safety"] == "REGRESSION")
    m12 = sum(1 for a in analyses if a["cell"].map in ("M1", "M2") and ("T2", CHALLENGER, "all") in a["cmp"] and a["cmp"][("T2", CHALLENGER, "all")]["safety"] == "REGRESSION")
    m12 += sum(1 for a in analyses if a["cell"].map in ("M1", "M2") and ("T3", CHALLENGER, "all") in a["cmp"] and a["cmp"][("T3", CHALLENGER, "all")]["safety"] == "REGRESSION")
    p["P5"] = (m12 <= 2 * m0, f"safety regressions: {m0} of 12 (M0 x 2 tiers), {m12} of 24 (M1/M2 x 2 tiers)")
    return p


def check_p6(analyses: list[dict]) -> tuple[bool, str]:
    """Reproduces this session's own pre-computed primary-cell reference for 0.015 (no earlier addendum measured it)."""
    if not any(a["cell"].is_primary for a in analyses):
        return False, "the primary cell is not among the cells run (expected in a --smoke subset)"
    pc = cell_of(analyses, **J.PRIMARY)
    s2, s3 = pc["sum"][("T2", CHALLENGER, "all")], pc["sum"][("T3", CHALLENGER, "all")]
    ok = abs(s2["minutes"] - REF_T2_MIN) < 0.5 and abs(s2["accuracy"] - REF_T2_ACC) < 0.01 and abs(s3["minutes"] - REF_T3_MIN) < 0.5 and abs(s3["accuracy"] - REF_T3_ACC) < 0.01
    return ok, (f"primary cell: T2 {s2['minutes']:.2f} min / {s2['accuracy']:.3f} against the reference {REF_T2_MIN:.1f} / {REF_T2_ACC:.3f}; "
                f"T3 {s3['minutes']:.2f} / {s3['accuracy']:.3f} against {REF_T3_MIN:.1f} / {REF_T3_ACC:.3f}")


def decision(analyses: list[dict], p6_ok: bool) -> str:
    if not p6_ok:
        return "NO RESULT (P6 failed: the sweep does not reproduce the pre-computed primary-cell reference for 0.015)"
    p = predictions(analyses)
    if p["P1"][0] and p["P2"][0] and p["P3"][0] and p["P4"][0]:
        return "CONFIRMED"
    if p["P1"][0] and p["P2"][0] and p["P3"][0] and not p["P5"][0]:
        return "CONFIRMED, UNSAFE UNDER MAP FAULTS"
    return "NOT CONFIRMED"


# ---------------------------------------------------------------------------------------------- gates
def gate_g1(results: list[dict], n: int = 50) -> tuple[bool, str]:
    import pickle
    from pathlib import Path
    raw30 = Path(__file__).resolve().parents[5] / "results" / "docmismatch" / "troubleshoot_joint" / "joint_raw.pkl"
    if not raw30.exists():
        return False, f"Addendum 30's raw results are needed: {raw30}"
    stored = {r["idx"]: r for r in pickle.loads(raw30.read_bytes())}
    bad = [r["idx"] for r in results if r["idx"] not in stored or not (r["kind"][:n] == stored[r["idx"]]["kind"][:n]).all()]
    return not bad, f"first {n} events of every cell match Addendum 30's stored kinds" + (f"; mismatches: {bad}" if bad else "")


def gate_g2(analyses: list[dict]) -> tuple[bool, str]:
    if not any(a["cell"].is_primary for a in analyses):
        return False, "the primary cell is not among the cells run (expected in a --smoke subset)"
    pc = cell_of(analyses, **J.PRIMARY)
    ok = True
    detail = []
    for tier, (m, a) in (("T2", (112.0, 0.80)), ("T3", (65.0, 0.82))):        # Addendum 31, primary cell, tool_ticket_memo2, all events (results/docmismatch/troubleshoot_joint2/joint2_report.md)
        s = pc["sum"][(tier, BASE_MIN_RATE, "all")]
        c = abs(s["minutes"] - m) / m < 0.05 and abs(s["accuracy"] - a) < 0.05
        ok &= c
        detail.append(f"{tier}: {s['minutes']:.1f} min / {s['accuracy']:.0%} against Addendum 31's {m:.0f} / {a:.0%}")
    return ok, "; ".join(detail)


def gate_g3() -> tuple[bool, str]:
    cases, wp = W.make_cases(), J.all_cells()[0].params()
    ev = W.draw_event(0, 0, wp, cases)
    cs = [cases[("T2", r)] for r in ev.rooms]
    qs = [(i, ck) for i, c in enumerate(cs) for ck in c.checks if ck.subject != "ahu"][:60]
    a = [TableOracle(ev, wp.rel_a).ask_room(i, ck, cs[i].doc) for i, ck in qs]
    b = [TableOracle(ev, wp.rel_a).ask_room(i, ck, cs[i].doc) for i, ck in reversed(qs)][::-1]
    return a == b, "the answer table is deterministic and independent of question order"


def gate_g4(analyses: list[dict]) -> tuple[bool, str]:
    return check_p6(analyses)


def gate_g5(results_a: list[dict], results_b: list[dict]) -> tuple[bool, str]:
    ok = all(np.array_equal(a[("T2", CHALLENGER)]["minutes"], b[("T2", CHALLENGER)]["minutes"]) for a, b in zip(results_a, results_b))
    return ok, "the sweep reproduces exactly on a second run with the same seed"
