"""If the answers to the tool's checks are MORE reliable than the tool assumes, how much more accurate is it, and does a lower conclusion threshold become safe? (PREREGISTRATION_DR.md
Addendum 42.) The other half of Addendum 41's reliability axis: Addendum 30's R1 worlds pull the world's response probabilities toward 0.5 (worse than the tool assumes); here they are
pushed toward 0 or 1 by a fraction `b` (better than the tool assumes), while the tool keeps its own response model. `b` = 0 is the world as assumed and must reproduce Addendum 41's R0 cells
exactly; `b` = 1.0 is a ceiling (every check answers deterministically), not a forecast. Simulation only; no LLM; nothing here changes the tool.
"""

from __future__ import annotations

import collections
import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace

import numpy as np

from ..v1 import catalogue as K
from . import policies as P
from . import study_joint as J
from . import study_minrate as MR
from . import study_tau as T
from . import world2 as W
from .joint import JointSettings
from .study_llm import TableOracle

# ---------------------------------------------------------------------------------------------- frozen constants (Addendum 42)
SEED = 42
N_EPISODES = J.N_EPISODES
BOOT_B = J.BOOT_B
SUBSETS = J.SUBSETS
B_LEVELS = (0.0, 0.5, 1.0)
TAU_GRID, BASE_TAU, LEVELS = T.TAU_GRID, T.BASE_TAU, T.LEVELS
TIERS, POLICIES = T.TIERS, T.POLICIES
PRIMARY_TIER, PRIMARY_POLICY = T.PRIMARY_TIER, T.PRIMARY_POLICY
CELLS = [(i, c) for i, c in enumerate(J.all_cells()) if c.rel == "R0"]      # the nine R0 cells of Addendum 30 (their own event streams)
N_CELLS = 9
UNSAFE_MIN, IMPROVES_MIN, WORSE_MAX, NO_EFFECT_MIN = 2, 8, 0, 8           # Addendum 41's bars scaled from 18 cells to 9, rounded to the stricter integer
DETAIL_KEY = (PRIMARY_TIER, PRIMARY_POLICY, BASE_TAU)                      # the variant whose per-complaint truth and guess are kept for the wrong-answer breakdown


# ---------------------------------------------------------------------------------------------- the sharpened world
def toward_certain(p: float, b: float) -> float:
    """A probability moved a fraction `b` of the way to certainty: up toward 1 if above 0.5, down toward 0 if below, unchanged at exactly 0.5."""
    if p > 0.5:
        return min(1.0, p + b * (1.0 - p))
    if p < 0.5:
        return max(0.0, p * (1.0 - b))
    return p


def sharpen(check: K.CheckV1, b: float) -> K.CheckV1:
    """The check as it would behave if its readings were MORE reliable than the tool assumes (the mirror image of `catalogue.degrade`). b = 0 returns the check itself."""
    if not 0.0 <= b <= 1.0:
        raise ValueError("b must be in [0, 1]")
    if b == 0.0:
        return check
    f = lambda p: toward_certain(p, b)  # noqa: E731
    if check.is_reading:
        return replace(check, detects={k: f(v) for k, v in check.detects.items()}, bg=f(check.bg))
    return replace(check, v0=replace(check.v0, tpr=f(check.v0.tpr), fpr=f(check.v0.fpr)), overrides={k: f(v) for k, v in check.overrides.items()})


def sharpen_all(checks: tuple, b: float) -> tuple:
    return tuple(sharpen(c, b) for c in checks)


class SharpOracle(TableOracle):
    """`TableOracle`'s answers, from a world whose checks are sharpened by `b` (b = 0 is `TableOracle(event, 0.0)` exactly)."""

    def __init__(self, event: W.Event, b: float):
        super().__init__(event, 0.0)
        self.b = b
        self.tc = {c.name: c for c in sharpen_all(K.CATALOGUE, b)}


# ---------------------------------------------------------------------------------------------- one cell
def run_variant(tier: str, tau: float, policy: str, events: list, wp: W.WorldParams, bld, b: float, detail: bool = False) -> dict:
    cases_by_room = T.cases_with(tier, tau, T.MIN_RATE, bld)
    js = JointSettings()
    mins, chk, ok, wc, cn, det = [], [], [], [], [], []
    for ev in events:
        cs = [cases_by_room[r] for r in ev.rooms]
        ctxs = [W.context_dict(tier, r) for r in ev.rooms]
        r = P.run_policy(policy, cs, SharpOracle(ev, b), ctxs, js)
        a, bb, c = J.score(r, ev)
        mins.append(r["minutes"])
        chk.append(r["n_checks"])
        ok.append(a)
        wc.append(bb)
        cn.append(c)
        if detail:
            det.extend((t, g, bool(c_)) for t, g, c_ in zip(ev.causes, r["guess"], r["concluded"]))
    n = np.array([e.n for e in events], float)
    correct, wca, cna = np.array(ok, float), np.array(wc, float), np.array(cn, float)
    out = dict(minutes=np.array(mins, float), checks=np.array(chk, float), correct=correct, wc=wca / n, concluded=cna, n=n, acc=correct / n, conc=cna / n)
    if detail:
        out["detail"] = det
    return out


def run_cell(idx: int, cell: J.Cell, n: int = N_EPISODES) -> dict:
    """Every (b, tier, policy, tau) variant of one R0 cell on the SAME `n` events as Addendum 30 and 41 (stream `[30, idx, 0, i]`)."""
    bld = W.make_building2()
    cases_all = W.make_cases(bld)
    wp = cell.params()
    events = [W.draw_event(idx, i, wp, cases_all) for i in range(n)]
    out = dict(idx=idx, cell=cell, n=n, kind=np.array([e.kind for e in events]))
    for b in B_LEVELS:
        for tier in TIERS:
            for pol in POLICIES:
                for tau in TAU_GRID:
                    out[(b, tier, pol, tau)] = run_variant(tier, tau, pol, events, wp, bld, b, detail=(tier, pol, tau) == DETAIL_KEY)
    return out


def _run_args(args):
    return run_cell(*args)


def compute_cells(cells: list[tuple[int, J.Cell]], n: int = N_EPISODES, workers: int | None = None) -> list[dict]:
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
    for b in B_LEVELS:
        for tier in TIERS:
            for pol in POLICIES:
                for tau in TAU_GRID:
                    v = out[(b, tier, pol, tau)]
                    for sub in SUBSETS:
                        summ[(b, tier, pol, tau, sub)] = J.summarize(v, masks[sub])
                        idx, bt = boot[sub]
                        if bt is None:
                            continue
                        if tau != BASE_TAU:
                            cmp_[("tau", b, tier, pol, tau, sub)] = MR.compare(v, out[(b, tier, pol, BASE_TAU)], idx, bt)
                        if b != 0.0:
                            cmp_[("rel", b, tier, pol, tau, sub)] = MR.compare(v, out[(0.0, tier, pol, tau)], idx, bt)
    return dict(idx=out["idx"], cell=out["cell"], n=out["n"], counts={s: int(masks[s].sum()) for s in SUBSETS}, sum=summ, cmp=cmp_)


# ---------------------------------------------------------------------------------------------- labels (Addendum 41's, scaled to nine cells)
def _counts(es: list[dict]) -> dict:
    return dict(n=len(es), improves=sum(e["label"] == "IMPROVES" for e in es), worse=sum(e["label"] == "WORSE" for e in es), trade=sum(e["label"] == "TRADE" for e in es),
                neither=sum(e["label"] == "NEITHER" for e in es), safety=sum(e["safety"] == "REGRESSION" for e in es), faster=sum(e["time"] == "FASTER" for e in es))


def level_counts(analyses: list[dict], b: float, tier: str, pol: str, tau: float) -> dict:
    return _counts([a["cmp"][("tau", b, tier, pol, tau, "all")] for a in analyses])


def level_label(analyses: list[dict], b: float, tier: str, pol: str, tau: float) -> str:
    if len(analyses) != N_CELLS:
        raise ValueError(f"the scaled bars are defined for {N_CELLS} cells, not {len(analyses)}")
    c = level_counts(analyses, b, tier, pol, tau)
    if c["safety"] >= UNSAFE_MIN:
        return "UNSAFE"
    if c["improves"] >= IMPROVES_MIN and c["worse"] <= WORSE_MAX:
        return "PASSES"
    if c["neither"] >= NO_EFFECT_MIN:
        return "NO EFFECT"
    return "TRADES"


def lowest_passing(analyses: list[dict], b: float, tier: str = PRIMARY_TIER, pol: str = PRIMARY_POLICY) -> float | None:
    ok = [tau for tau in LEVELS if level_label(analyses, b, tier, pol, tau) == "PASSES"]
    return min(ok) if ok else None


def cell_means(analyses: list[dict], b: float, tier: str, pol: str, tau: float, sub: str = "all") -> dict:
    ss = [a["sum"][(b, tier, pol, tau, sub)] for a in analyses]
    return {k: float(np.mean([s[k] for s in ss])) for k in ("minutes", "checks", "accuracy", "wrong_confident", "concluded")}


def rel_effect(analyses: list[dict], b: float, tier: str, pol: str, tau: float) -> dict:
    """Reliability b against b = 0 on the same events: cell-mean paired differences and the label counts."""
    es = [a["cmp"][("rel", b, tier, pol, tau, "all")] for a in analyses]
    c = _counts(es)
    c.update(d_acc=float(np.mean([e["d_acc"] for e in es])), d_min=float(np.mean([e["d_min"] for e in es])), d_wc=float(np.mean([e["d_wc"] for e in es])),
             r_min=float(np.mean([e["r_min"] for e in es])))
    return c


# ---------------------------------------------------------------------------------------------- predictions (frozen operationalisation)
def predictions(analyses: list[dict]) -> dict:
    t, p = PRIMARY_TIER, PRIMARY_POLICY
    m = {b: cell_means(analyses, b, t, p, BASE_TAU) for b in B_LEVELS}
    out = {}
    out["P1"] = (m[1.0]["accuracy"] - m[0.0]["accuracy"] >= 0.10, f"accuracy {m[0.0]['accuracy']:.3f} at b=0, {m[0.5]['accuracy']:.3f} at 0.5, {m[1.0]['accuracy']:.3f} at 1.0 (rise {m[1.0]['accuracy'] - m[0.0]['accuracy']:+.3f})")
    out["P2"] = (m[1.0]["accuracy"] < 0.97, f"accuracy at b=1.0 is {m[1.0]['accuracy']:.3f}")
    out["P3"] = (m[0.5]["accuracy"] > m[0.0]["accuracy"] + 0.03 and m[1.0]["accuracy"] > m[0.5]["accuracy"], f"{m[0.0]['accuracy']:.3f} < {m[0.5]['accuracy']:.3f} < {m[1.0]['accuracy']:.3f}")
    out["P4"] = (m[1.0]["wrong_confident"] <= m[0.0]["wrong_confident"], f"wrong-and-confident {m[0.0]['wrong_confident']:.4f} at b=0, {m[1.0]['wrong_confident']:.4f} at b=1.0")
    out["P5"] = (m[1.0]["minutes"] <= 0.90 * m[0.0]["minutes"], f"minutes {m[0.0]['minutes']:.1f} at b=0, {m[1.0]['minutes']:.1f} at b=1.0 ({100 * (m[1.0]['minutes'] / m[0.0]['minutes'] - 1):+.0f}%)")
    s10 = level_counts(analyses, 1.0, t, p, 0.85)["safety"]
    out["P6"] = (s10 <= 1, f"b=1.0, tau 0.85: safety regressions in {s10} of 9 cells ({level_label(analyses, 1.0, t, p, 0.85)})")
    s05 = level_counts(analyses, 0.5, t, p, 0.85)["safety"]
    out["P7"] = (s05 >= 2, f"b=0.5, tau 0.85: safety regressions in {s05} of 9 cells ({level_label(analyses, 0.5, t, p, 0.85)})")
    gain = {sub: float(np.mean([a["sum"][(1.0, t, p, BASE_TAU, sub)]["accuracy"] - a["sum"][(0.0, t, p, BASE_TAU, sub)]["accuracy"] for a in analyses if a["counts"][sub] > 0])) for sub in ("single", "shared")}
    out["P8"] = (gain["single"] > gain["shared"], f"accuracy gain at b=1.0: single {gain['single']:+.3f}, shared {gain['shared']:+.3f}")
    return out


# ---------------------------------------------------------------------------------------------- what is left wrong
def cause_str(c: tuple) -> str:
    return "wrong box" if c[0] == "wrong" else c[0]


def breakdown(results: list[dict], b: float, top: int = 3) -> list[dict]:
    """Per true cause, for tool_joint at T3-noattr and `tau` 0.95: how often the tool's leading cause is exactly right, and its most common wrong answers."""
    det = [d for r in results for d in r[(b,) + DETAIL_KEY]["detail"]]
    by = collections.defaultdict(list)
    for t, g, c in det:
        by[cause_str(t)].append((cause_str(g), c))
    rows = []
    for cause, items in by.items():
        wrong = collections.Counter(g for g, _ in items if g != cause)
        rows.append(dict(cause=cause, n=len(items), exact=sum(g == cause for g, _ in items) / len(items), concluded_wrong=sum(1 for g, c in items if c and g != cause) / len(items),
                         top_wrong=sorted(wrong.items(), key=lambda kv: (-kv[1], kv[0]))[:top]))
    return sorted(rows, key=lambda r: (-r["n"], r["cause"]))


# ---------------------------------------------------------------------------------------------- gates
def gate_g1(results: list[dict]) -> tuple[bool, str]:
    return MR.gate_g1(results, 50)


def gate_g2(results: list[dict]) -> tuple[bool, str]:
    """At b = 0 every variant reproduces Addendum 41's stored R0-cell arrays exactly."""
    import pickle
    from pathlib import Path
    raw41 = Path(__file__).resolve().parents[5] / "results" / "docmismatch" / "troubleshoot_tau" / "raw.pkl"
    if not raw41.exists():
        return False, f"Addendum 41's raw results are needed: {raw41}"
    stored = {r["idx"]: r for r in pickle.loads(raw41.read_bytes())}
    bad = []
    for r in results:
        for tier in TIERS:
            for pol in POLICIES:
                for tau in TAU_GRID:
                    a, s = r[(0.0, tier, pol, tau)], stored[r["idx"]][(tier, pol, tau)]
                    if not all(np.array_equal(a[k], s[k]) for k in ("minutes", "checks", "acc", "wc")):
                        bad.append((r["idx"], tier, pol, tau))
    return not bad, f"b = 0 reproduces Addendum 41's R0 cells exactly for {len(results)} cells x {len(TIERS) * len(POLICIES) * len(TAU_GRID)} variants" + (f"; MISMATCHES: {bad[:3]}" if bad else "")


def gate_g3() -> tuple[bool, str]:
    ok, msg = MR.gate_g3()
    cells = J.all_cells()
    wp, bld = cells[0].params(), W.make_building2()
    ev = W.draw_event(0, 0, wp, W.make_cases(bld))
    cases = T.cases_with(PRIMARY_TIER, BASE_TAU, T.MIN_RATE, bld)
    cs = [cases[r] for r in ev.rooms]
    qs = [(i, ck) for i, c in enumerate(cs) for ck in c.checks if ck.subject != "ahu"][:60]
    a = [TableOracle(ev, 0.0).ask_room(i, ck, cs[i].doc) for i, ck in qs]
    b = [SharpOracle(ev, 0.0).ask_room(i, ck, cs[i].doc) for i, ck in qs]
    return ok and a == b, "the answer table is deterministic and independent of question order; the sharpened oracle at b = 0 answers exactly as TableOracle"


def gate_g4() -> tuple[bool, str]:
    problems = []
    for c in K.CATALOGUE:
        if sharpen(c, 0.0) is not c:
            problems.append(f"{c.name}: b=0 is not the identity")
        for b in (0.5, 1.0):
            s = sharpen(c, b)
            pairs = ([(c.detects[k], s.detects[k]) for k in c.detects] + [(c.bg, s.bg)]) if c.is_reading else \
                    [(c.v0.tpr, s.v0.tpr), (c.v0.fpr, s.v0.fpr)] + [(c.overrides[k], s.overrides[k]) for k in c.overrides]
            for p, q in pairs:
                if not 0.0 <= q <= 1.0 or (p > 0.5 and q < p) or (p < 0.5 and q > p) or (p == 0.5 and q != p) or (b == 1.0 and p != 0.5 and abs(q - round(q)) > 1e-12):
                    problems.append(f"{c.name}: {p} -> {q} at b={b}")
    s0 = sharpen(next(c for c in K.CATALOGUE if c.name == "bas_ahu_fan"), 0.5)
    ok_hit = abs(s0.detects["ahu_fan_off"] - 0.96) < 1e-12
    return not problems and ok_hit, ("sharpening is the identity at 0, stays in [0, 1], moves toward 0 or 1 and never across 0.5, is binary at 1.0, and gives bas_ahu_fan's 0.92 hit rate 0.96 at b = 0.5"
                                     + (f"; PROBLEMS: {problems[:3]}" if problems else ""))


def gate_g5(results_a: list[dict], results_b: list[dict]) -> tuple[bool, str]:
    keys = [(b, t, p, tau) for b in B_LEVELS for t in TIERS for p in POLICIES for tau in TAU_GRID]
    ok = all(np.array_equal(a[k][f], c[k][f]) for a, c in zip(results_a, results_b) for k in keys for f in ("minutes", "checks", "acc", "wc"))
    return ok, f"{len(results_a)} cells reproduce exactly on a second run (one worker against many) with the same seed"


# ---------------------------------------------------------------------------------------------- report
def pct(x: float) -> str:
    return f"{100 * x:.0f}%"


def report(analyses: list[dict], results: list[dict], gates: list[tuple[str, bool, str]], preds: dict, n: int) -> str:
    L = ["# More reliable answers: accuracy and the threshold (Addendum 42)", "",
         f"Simulation only: the nine R0 cells of Addendum 30 ({n} events each, the same events as Addendum 41), answers from a world sharpened by `b` (0 = as the tool assumes; 0.5 = half the way "
         "to certainty; 1.0 = every check deterministic, a ceiling not a forecast), `min_rate` 0.02. The tool keeps its own response model throughout. Labels are Addendum 21's, with Addendum 41's "
         "bars scaled to nine cells. Nothing here is evidence about real technicians and nothing changes the tool's defaults.", "", "## Gates", ""]
    for g, ok, d in gates:
        L.append(f"- **{g}: {'PASS' if ok else 'FAIL'}.** {d}")
    t, p = PRIMARY_TIER, PRIMARY_POLICY
    L += ["", f"## Reliability effect at tau {BASE_TAU} ({p}, {t}; cell means; paired against b = 0 on the same events)", "",
          "| b | minutes | checks | accuracy | wrong-and-confident | concluded | accuracy change (cells labelled IMPROVES, of 9) | minutes change |", "|---|---|---|---|---|---|---|---|"]
    for b in B_LEVELS:
        m = cell_means(analyses, b, t, p, BASE_TAU)
        e = rel_effect(analyses, b, t, p, BASE_TAU) if b != 0.0 else None
        L.append(f"| {b} | {m['minutes']:.1f} | {m['checks']:.2f} | {pct(m['accuracy'])} | {m['wrong_confident']:.4f} | {pct(m['concluded'])} | "
                 + (f"{100 * e['d_acc']:+.1f} pts ({e['improves']}) | {100 * e['r_min']:+.0f}% |" if e else "- | - |"))
    L += ["", "Accuracy by visit kind (cell means):", "", "| b | single | multi (no shared cause) | shared cause |", "|---|---|---|---|"]
    for b in B_LEVELS:
        row = [np.mean([a["sum"][(b, t, p, BASE_TAU, k)]["accuracy"] for a in analyses if a["counts"][k] > 0]) for k in ("single", "multi", "shared")]
        L.append(f"| {b} | " + " | ".join(pct(x) for x in row) + " |")
    for tier in TIERS:
        for pol in POLICIES:
            for b in B_LEVELS:
                L += ["", f"### {pol}, {tier}, b = {b}: lowering tau", "", "| tau | label | IMPROVES | NEITHER | TRADE | WORSE | safety regressions (of 9) | minutes | accuracy | wrong-and-confident |", "|---|---|---|---|---|---|---|---|---|---|"]
                base = cell_means(analyses, b, tier, pol, BASE_TAU)
                L.append(f"| {BASE_TAU} (baseline) | - | - | - | - | - | - | {base['minutes']:.1f} | {pct(base['accuracy'])} | {base['wrong_confident']:.4f} |")
                for tau in LEVELS:
                    c = level_counts(analyses, b, tier, pol, tau)
                    m = cell_means(analyses, b, tier, pol, tau)
                    L.append(f"| {tau} | **{level_label(analyses, b, tier, pol, tau)}** | {c['improves']} | {c['neither']} | {c['trade']} | {c['worse']} | {c['safety']} | "
                             f"{m['minutes']:.1f} ({100 * (m['minutes'] / base['minutes'] - 1):+.0f}%) | {pct(m['accuracy'])} ({100 * (m['accuracy'] - base['accuracy']):+.1f} pts) | {m['wrong_confident']:.4f} |")
    L += ["", f"Lowest passing tau ({p}, {t}): " + ", ".join(f"b = {b}: {lowest_passing(analyses, b) or 'none'}" for b in B_LEVELS) + ".", "", "## Registered predictions", "", "| | held | detail |", "|---|---|---|"]
    for k in sorted(preds):
        L.append(f"| {k} | {'yes' if preds[k][0] else 'NO'} | {preds[k][1]} |")
    for b in (0.0, 1.0):
        L += ["", f"## What is left wrong at b = {b} ({p}, {t}, tau {BASE_TAU}; all 9 cells pooled)", "", "| true cause | complaints | exactly right | concluded and wrong | most common wrong answers |", "|---|---|---|---|---|"]
        for r in breakdown(results, b):
            L.append(f"| {r['cause']} | {r['n']} | {pct(r['exact'])} | {pct(r['concluded_wrong'])} | " + ", ".join(f"{g} ({n})" for g, n in r["top_wrong"]) + " |")
    return "\n".join(L)
