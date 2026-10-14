"""Does lowering the conclusion threshold `tau` cut checks and minutes without costing accuracy or safety, across Addendum 30's 18 cells? (PREREGISTRATION_DR.md Addendum 41.)

A parameter sweep of the tool's own engine (`tau` only; `min_rate` is the live 0.02 throughout) on all 18 cells of Addendum 30, at T3-noattr (primary) and T3, for two policies: `tool_joint`
(the JointSession the CLI runs; primary) and `tool_ticket_memo2` (the routine Addenda 34-36 swept; secondary). Same events as Addendum 30 (stream `[30, cell, 0, i]`), answers from
`TableOracle` (identical answers to identical questions whichever variant asks), Addendum 21's labels and tolerances, the bars of Addendum 35. Simulation only; no LLM; nothing here is
evidence about real technicians, and nothing here changes the tool's defaults.
"""

from __future__ import annotations

import dataclasses
import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from .. import study as S
from .. import study_rating as SG
from ..v1.engine import make_case_v1
from . import policies as P
from . import study_joint as J
from . import study_llm_ext as E
from . import study_minrate as MR
from . import world2 as W
from .joint import JointSettings
from .study_llm import TableOracle

# ---------------------------------------------------------------------------------------------- frozen constants (Addendum 41)
SEED = 41
N_EPISODES = J.N_EPISODES                  # 1000, Addendum 30's cell size
BOOT_B = J.BOOT_B
SUBSETS = J.SUBSETS
BASE_TAU = 0.95
TAU_GRID = (0.95, 0.90, 0.85, 0.80, 0.75)  # the baseline first, then the four registered levels
LEVELS = TAU_GRID[1:]
MIN_RATE = 0.02                            # the live default at registration (2026-10-08), frozen here: a later change of the CLI default must not move this study
TIERS = (E.EXT_ARM, "T3")                  # T3-noattr (primary) and T3; T2 is not run (named omission)
POLICIES = ("tool_joint", "tool_ticket_memo2")
PRIMARY_POLICY, PRIMARY_TIER = "tool_joint", E.EXT_ARM
N_CELLS = 18
IMPROVES_CELLS = 15                        # Addendum 35's 15-of-18 bar
WORSE_MAX = 1
UNSAFE_CELLS_MIN = 3                       # UNSAFE if a safety regression in this many cells or more
NO_EFFECT_CELLS = 15
R1_IMPROVES_MIN, R1_WORSE_MAX, R1_SAFETY_MAX = 8, 0, 1     # the stress check, on the 9 R1 cells
UNSAFE_RATE_BAR = 0.02                     # P5: cell-mean wrong-and-confident rise
STATES = ("UNSAFE", "PASSES", "PASSES ONLY WHERE CHECKS ARE AS RELIABLE AS ASSUMED", "NO EFFECT", "TRADES")


def cases_with(tier: str, tau: float, min_rate: float = MIN_RATE, bld=None) -> dict:
    """{room -> CaseV1}: the tool's own settings and engine, with `tau` and `min_rate` as given and nothing else changed."""
    bld = bld or W.make_building2()
    s = dataclasses.replace(W.tool_settings(), tau=tau)
    return {r: make_case_v1(bld, f"Room-{r}", W.TIER_ITEMS[tier], settings=s, context=W.tier_context(tier, r), member_name=f"Room {r}", min_rate=min_rate) for r in range(W.N_BOX)}


def run_variant(tier: str, tau: float, min_rate: float, policy: str, events: list, wp: W.WorldParams, bld) -> dict:
    cases_by_room = cases_with(tier, tau, min_rate, bld)
    js = JointSettings()
    mins, chk, ok, wc, cn = [], [], [], [], []
    for ev in events:
        cs = [cases_by_room[r] for r in ev.rooms]
        ctxs = [W.context_dict(tier, r) for r in ev.rooms]
        r = P.run_policy(policy, cs, TableOracle(ev, wp.rel_a), ctxs, js)
        a, b, c = J.score(r, ev)
        mins.append(r["minutes"])
        chk.append(r["n_checks"])
        ok.append(a)
        wc.append(b)
        cn.append(c)
    n = np.array([e.n for e in events], float)
    correct, wca, cna = np.array(ok, float), np.array(wc, float), np.array(cn, float)
    return dict(minutes=np.array(mins, float), checks=np.array(chk, float), correct=correct, wc=wca / n, concluded=cna, n=n, acc=correct / n, conc=cna / n)


def run_cell(idx: int, cell: J.Cell, n: int = N_EPISODES) -> dict:
    """Every (tier, policy, tau) variant of one cell on the SAME `n` events (stream `[30, idx, 0, i]`, exactly Addendum 30's)."""
    bld = W.make_building2()
    cases_all = W.make_cases(bld)
    wp = cell.params()
    events = [W.draw_event(idx, i, wp, cases_all) for i in range(n)]
    out = dict(idx=idx, cell=cell, n=n, kind=np.array([e.kind for e in events]))
    for tier in TIERS:
        for pol in POLICIES:
            for tau in TAU_GRID:
                out[(tier, pol, tau)] = run_variant(tier, tau, MIN_RATE, pol, events, wp, bld)
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


def analyze_cell(out: dict, B: int = BOOT_B) -> dict:
    masks = J.subset_masks(out)
    boot = {}
    for si, sub in enumerate(SUBSETS):
        idx = np.flatnonzero(masks[sub])
        boot[sub] = (idx, np.random.default_rng([SEED, out["idx"], 99, si]).integers(0, len(idx), (B, len(idx))) if len(idx) else None)
    summ, cmp_ = {}, {}
    for tier in TIERS:
        for pol in POLICIES:
            base_v = out[(tier, pol, BASE_TAU)]
            for tau in TAU_GRID:
                v = out[(tier, pol, tau)]
                for sub in SUBSETS:
                    summ[(tier, pol, tau, sub)] = J.summarize(v, masks[sub])
                    if tau != BASE_TAU:
                        idx, bt = boot[sub]
                        if bt is not None:
                            cmp_[(tier, pol, tau, sub)] = MR.compare(v, base_v, idx, bt)
    return dict(idx=out["idx"], cell=out["cell"], n=out["n"], counts={s: int(masks[s].sum()) for s in SUBSETS}, sum=summ, cmp=cmp_)


# ---------------------------------------------------------------------------------------------- the level label (frozen operationalisation of Addendum 41)
def _counts(es: list[dict]) -> dict:
    return dict(n=len(es), improves=sum(e["label"] == "IMPROVES" for e in es), worse=sum(e["label"] == "WORSE" for e in es), trade=sum(e["label"] == "TRADE" for e in es),
                neither=sum(e["label"] == "NEITHER" for e in es), safety=sum(e["safety"] == "REGRESSION" for e in es), faster=sum(e["time"] == "FASTER" for e in es),
                minutes_lower=sum(e["d_min"] < 0 for e in es))


def level_counts(analyses: list[dict], tier: str, pol: str, tau: float) -> dict:
    """Cell counts by Addendum 21 label (all subset), and the same restricted to the nine R1 (stress) cells and the nine R0 cells."""
    items = [(a["cell"], a["cmp"][(tier, pol, tau, "all")]) for a in analyses]
    return dict(all=_counts([e for _, e in items]), R1=_counts([e for c, e in items if c.rel == "R1"]), R0=_counts([e for c, e in items if c.rel == "R0"]))


def level_label(analyses: list[dict], tier: str, pol: str, tau: float) -> str:
    """UNSAFE > PASSES (with the R1 stress check) > NO EFFECT > TRADES. The bars are the registered ones and need all 18 cells."""
    if len(analyses) != N_CELLS:
        raise ValueError(f"the registered bars are defined for {N_CELLS} cells, not {len(analyses)}")
    c = level_counts(analyses, tier, pol, tau)
    a, r1 = c["all"], c["R1"]
    if a["safety"] >= UNSAFE_CELLS_MIN:
        return "UNSAFE"
    if a["improves"] >= IMPROVES_CELLS and a["worse"] <= WORSE_MAX:
        if r1["improves"] >= R1_IMPROVES_MIN and r1["worse"] <= R1_WORSE_MAX and r1["safety"] <= R1_SAFETY_MAX:
            return "PASSES"
        return "PASSES ONLY WHERE CHECKS ARE AS RELIABLE AS ASSUMED"
    if a["neither"] >= NO_EFFECT_CELLS:
        return "NO EFFECT"
    return "TRADES"


def all_labels(analyses: list[dict]) -> dict:
    return {(t, p, tau): level_label(analyses, t, p, tau) for t in TIERS for p in POLICIES for tau in LEVELS}


def outcome(labels: dict) -> tuple[str, float | None]:
    """The frozen overall outcome, read on tool_joint at T3-noattr. tau* = the lowest level labelled PASSES (with the stress check satisfied). If none, but some level passes overall
    while failing the stress check: ONLY WHERE CHECKS ARE AS RELIABLE AS ASSUMED. Otherwise: NO LEVEL BELOW 0.95 PASSES."""
    ls = {tau: labels[(PRIMARY_TIER, PRIMARY_POLICY, tau)] for tau in LEVELS}
    ok = [tau for tau, l in ls.items() if l == "PASSES"]
    if ok:
        return "A LOWER THRESHOLD IS SAFE TO OFFER", min(ok)
    if any(l == "PASSES ONLY WHERE CHECKS ARE AS RELIABLE AS ASSUMED" for l in ls.values()):
        return "ONLY WHERE CHECKS ARE AS RELIABLE AS ASSUMED", None
    return "NO LEVEL BELOW 0.95 PASSES", None


def cell_means(analyses: list[dict], tier: str, pol: str, tau: float, sub: str = "all") -> dict:
    ss = [a["sum"][(tier, pol, tau, sub)] for a in analyses]
    return {k: float(np.mean([s[k] for s in ss])) for k in ("minutes", "checks", "accuracy", "wrong_confident", "concluded")}


# ---------------------------------------------------------------------------------------------- predictions (frozen operationalisation; P7 is evaluated on the real calls by the script)
def predictions(analyses: list[dict]) -> dict:
    t, p = PRIMARY_TIER, PRIMARY_POLICY
    out = {}
    c90 = level_counts(analyses, t, p, 0.90)
    out["P1"] = (c90["all"]["neither"] >= NO_EFFECT_CELLS, f"tau 0.90: NEITHER in {c90['all']['neither']} of 18 cells")
    c80 = level_counts(analyses, t, p, 0.80)
    out["P2"] = (c80["all"]["faster"] >= 12, f"tau 0.80: at least 5% faster in {c80['all']['faster']} of 18 cells")
    l80 = level_label(analyses, t, p, 0.80)
    out["P3"] = (l80 in ("TRADES", "UNSAFE"), f"tau 0.80 is {l80}")
    l75 = level_label(analyses, t, p, 0.75)
    out["P4"] = (l80 != "PASSES" and l75 != "PASSES", f"tau 0.80 is {l80}, 0.75 is {l75}")
    base, low = cell_means(analyses, t, p, BASE_TAU), cell_means(analyses, t, p, 0.75)
    out["P5"] = (low["wrong_confident"] - base["wrong_confident"] >= UNSAFE_RATE_BAR,
                 f"cell-mean wrong-and-confident {base['wrong_confident']:.4f} at 0.95, {low['wrong_confident']:.4f} at 0.75 (difference {low['wrong_confident'] - base['wrong_confident']:+.4f})")
    r1, r0 = c80["R1"]["safety"], c80["R0"]["safety"]
    out["P6"] = (r1 > r0 or (r1 == 0 and r0 == 0), f"tau 0.80 safety regressions: {r1} of 9 R1 cells, {r0} of 9 R0 cells")
    c80r = level_counts(analyses, t, "tool_ticket_memo2", 0.80)
    out["P8"] = (c80r["all"]["minutes_lower"] >= 12, f"routine, tau 0.80, T3-noattr: minutes lower in {c80r['all']['minutes_lower']} of 18 cells")
    return out


# ---------------------------------------------------------------------------------------------- gates
def gate_g1(results: list[dict], n: int = 50) -> tuple[bool, str]:
    return MR.gate_g1(results, n)


def gate_g2(n: int = 200) -> tuple[bool, str]:
    """(a) Plumbing for the new policy path: with `tau` 0.95 and `min_rate` 0.003 and Addendum 30's own oracle streams, `tool_joint` at T3 on the primary cell reproduces Addendum 30's stored
    per-event minutes, correct and wrong-and-confident counts exactly. (b) The routine at the same settings under TableOracle reproduces Addendum 31's primary-cell T3 numbers within 5%."""
    import pickle
    from pathlib import Path
    raw30 = Path(__file__).resolve().parents[5] / "results" / "docmismatch" / "troubleshoot_joint" / "joint_raw.pkl"
    if not raw30.exists():
        return False, f"Addendum 30's raw results are needed: {raw30}"
    stored = {r["idx"]: r for r in pickle.loads(raw30.read_bytes())}
    cells = J.all_cells()
    idx = next(i for i, c in enumerate(cells) if c.is_primary)
    wp = cells[idx].params()
    bld = W.make_building2()
    cases_all = W.make_cases(bld)
    events = [W.draw_event(idx, i, wp, cases_all) for i in range(n)]
    cases_by_room = cases_with("T3", BASE_TAU, MR.BASE_MIN_RATE, bld)
    ti = W.TIER_NAMES.index("T3")
    mins, ok, wc = [], [], []
    for i, ev in enumerate(events):
        cs = [cases_by_room[r] for r in ev.rooms]
        ctxs = [W.context_dict("T3", r) for r in ev.rooms]
        oracle = W.Oracle(ev, wp.rel_a, np.random.default_rng([J.SEED, idx, 100 + 10 * ti + P.POLICY_INDEX["tool_joint"], i]))
        r = P.run_policy("tool_joint", cs, oracle, ctxs)
        a, b, _ = J.score(r, ev)
        mins.append(r["minutes"])
        ok.append(a)
        wc.append(b)
    s = stored[idx]["pol"][("T3", "tool_joint")]
    exact = np.array_equal(np.array(mins, float), s["minutes"][:n]) and np.array_equal(np.array(ok, float), s["correct"][:n]) and np.array_equal(np.array(wc, float), s["wc"][:n])
    r_all = run_variant("T3", BASE_TAU, MR.BASE_MIN_RATE, "tool_ticket_memo2", [W.draw_event(idx, i, wp, cases_all) for i in range(1000)], wp, bld)
    m, a = float(r_all["minutes"].mean()), float(r_all["acc"].mean())
    near = abs(m - 65.0) / 65.0 < 0.05 and abs(a - 0.82) < 0.05
    return exact and near, (f"(a) tool_joint at T3, primary cell, first {n} events: {'identical to' if exact else 'DIFFERENT FROM'} Addendum 30's stored per-event results; "
                            f"(b) routine at 0.95/0.003, T3, primary cell: {m:.1f} min / {a:.0%} against Addendum 31's 65 / 82%")


def gate_g3(n: int = 1000) -> tuple[bool, str]:
    """The routine at tau 0.95 and the live min_rate 0.02, T3-noattr, primary cell reproduces Exploratory note E2's stored numbers (58.3 min, 80.4%) within 2%, and equals
    `study_minrate.run_variant_events` on the same events exactly (the new code path changes nothing at the baseline)."""
    cells = J.all_cells()
    idx = next(i for i, c in enumerate(cells) if c.is_primary)
    wp = cells[idx].params()
    bld = W.make_building2()
    cases_all = W.make_cases(bld)
    events = [W.draw_event(idx, i, wp, cases_all) for i in range(n)]
    mine = run_variant(E.EXT_ARM, BASE_TAU, MIN_RATE, "tool_ticket_memo2", events, wp, bld)
    old = MR.run_variant_events(E.EXT_ARM, MIN_RATE, events, wp, bld)
    same = all(np.array_equal(mine[k], old[k]) for k in ("minutes", "checks", "acc", "wc"))
    m, a = float(mine["minutes"].mean()), float(mine["acc"].mean())
    near = abs(m - 58.3) / 58.3 < 0.02 and abs(a - 0.804) < 0.02
    return same and near, f"routine, 0.95/0.02, T3-noattr, primary cell: {m:.1f} min / {a:.1%} against E2's 58.3 / 80.4%; identical to study_minrate's own run: {same}"


def gate_g4() -> tuple[bool, str]:
    return MR.gate_g3()


def gate_g6(results_a: list[dict], results_b: list[dict]) -> tuple[bool, str]:
    keys = [(t, p, tau) for t in TIERS for p in POLICIES for tau in TAU_GRID]
    ok = all(np.array_equal(a[k][f], b[k][f]) for a, b in zip(results_a, results_b) for k in keys for f in ("minutes", "checks", "acc", "wc"))
    return ok, f"{len(results_a)} cells reproduce exactly on a second run (one worker against many) with the same seed"


# ---------------------------------------------------------------------------------------------- report
def pct(x: float) -> str:
    return f"{100 * x:.0f}%"


def report(analyses: list[dict], gates: list[tuple[str, bool, str]], preds: dict, real: dict | None, n: int) -> str:
    labels = all_labels(analyses)
    oc, tau_star = outcome(labels)
    L = ["# Does lowering `tau` cut checks without costing accuracy or safety? (Addendum 41)", "",
         f"Simulation only: Addendum 30's 18 cells ({n} events each), answers from `TableOracle`, `min_rate` = {MIN_RATE} throughout, baseline `tau` = {BASE_TAU}. Labels are Addendum 21's "
         "(5% minutes, 0.02 accuracy, 0.02 safety, paired 95% intervals) over the `all` subset; bars are Addendum 35's. Nothing here is evidence about real technicians and nothing changes the tool's defaults.", "",
         "## Gates", ""]
    for g, ok, d in gates:
        L.append(f"- **{g}: {'PASS' if ok else 'FAIL'}.** {d}")
    L += ["", f"## Overall outcome (tool_joint, {PRIMARY_TIER}): **{oc}**" + (f" (tau* = {tau_star})" if tau_star is not None else ""), ""]
    for tier in TIERS:
        for pol in POLICIES:
            L += [f"### {pol}, {tier}", "", "| tau | label | IMPROVES | NEITHER | TRADE | WORSE | safety regressions | R1: IMPROVES / WORSE / safety (of 9) | cell-mean minutes | checks | accuracy | wrong-and-confident |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|"]
            b = cell_means(analyses, tier, pol, BASE_TAU)
            L.append(f"| {BASE_TAU} (baseline) | - | - | - | - | - | - | - | {b['minutes']:.1f} | {b['checks']:.2f} | {pct(b['accuracy'])} | {b['wrong_confident']:.4f} |")
            for tau in LEVELS:
                c = level_counts(analyses, tier, pol, tau)
                m = cell_means(analyses, tier, pol, tau)
                a, r1 = c["all"], c["R1"]
                L.append(f"| {tau} | **{labels[(tier, pol, tau)]}** | {a['improves']} | {a['neither']} | {a['trade']} | {a['worse']} | {a['safety']} | {r1['improves']} / {r1['worse']} / {r1['safety']} | "
                         f"{m['minutes']:.1f} ({100 * (m['minutes'] / b['minutes'] - 1):+.0f}%) | {m['checks']:.2f} | {pct(m['accuracy'])} ({100 * (m['accuracy'] - b['accuracy']):+.1f} pts) | {m['wrong_confident']:.4f} |")
            L.append("")
    L += ["## Registered predictions", "", "| | held | detail |", "|---|---|---|"]
    for k in sorted(preds):
        L.append(f"| {k} | {'yes' if preds[k][0] else 'NO'} | {preds[k][1]} |")
    if real:
        L += ["", "## The two real calls (descriptive; the live CLI path, k = 6, the consistent worlds of Addendum 40; time at the CENTRAL pace)", "",
              "| call | tau | steps | working time (min) | / technician | right on every complaint | wrong and confident | concluded |", "|---|---|---|---|---|---|---|---|"]
        for cid, rows in real["rows"].items():
            for r in rows:
                L.append(f"| {cid} | {r['tau']} | {r['steps']:.0f} | {r['time']:.2f} | {r['ratio']:.2f} | {pct(r['right'])} | {100 * r['wc']:.1f}% | {pct(r['concluded'])} |")
    return "\n".join(L)
