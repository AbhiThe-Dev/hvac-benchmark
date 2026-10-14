"""Does letting a reading that bears on the air handler count for the whole group change the verdict of Addendum 30? (PREREGISTRATION_DR.md Addendum 31.) Simulation only; nothing is fitted;
nothing here is evidence about real technicians or buildings.

The world, the cells and the events are Addendum 30's (same draws). Three new policies work them with the repaired conclusion rule: `tool_ticket_memo2` (the routine, which also carries an
abnormal inlet static reading to the other tickets of the same air handler), `tool_joint2` (the joint session with the rule on) and `tool_joint2_la2` (the same with two-step look-ahead, in
three cells). Addendum 30's policies are not re-run except in gate G1: their stored results are the comparison partners.
"""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from ..v1 import catalogue as K
from . import policies as P
from . import study_joint as J
from . import world2 as W
from .joint import JointModel, JointSettings, bears_on_ahu

# ---------------------------------------------------------------------------------------------- frozen constants (Addendum 31)
SEED = 31
N_EPISODES = J.N_EPISODES
BOOT_B = J.BOOT_B
TRACE_EVENTS = J.TRACE_EVENTS
TIERS = J.TIERS
SUBSETS = J.SUBSETS
POLICIES2 = P.POLICIES2
RAW30 = Path(__file__).resolve().parents[5] / "results" / "docmismatch" / "troubleshoot_joint" / "joint_raw.pkl"
COMPS2 = dict(H=("tool_joint2", "tool_ticket_memo2"), I=("tool_joint2", "tool_joint"), J=("tool_ticket_memo2", "tool_ticket_memo"), K=("tool_joint2", "fast_parent"),
              L=("tool_joint2", "tool_ticket"), M=("tool_joint2_la2", "tool_joint2"), N=("tool_joint3", "tool_ticket_memo2"), O=("tool_joint3", "tool_joint2"))
P1_BAR, P2_BAR, P3_BAR, P4_LABEL, P5_BAR, P6_BAR, P7_BAR, P8_BAR, P10_BAR, P11_BAR = 0.15, 0.10, 0.10, "IMPROVES", 0.15, 0.01, 0.02, 0.02, 0.05, 0.10
UNSAFE_BAR, UNSAFE_CELLS = J.UNSAFE_BAR, J.UNSAFE_CELLS
G1_EVENTS = 20


def policies_for2(cell: J.Cell) -> tuple:
    return tuple(p for p in POLICIES2 if p not in P.LOOKAHEAD_POLICIES2 or cell.has_lookahead)


# ---------------------------------------------------------------------------------------------- one cell
def run_cell2(idx: int, cell: J.Cell, n: int = N_EPISODES) -> dict:
    """`n` events per new policy and tier on Addendum 30's `n` draws (stream [30, cell, 0, event]); the answers of policy p at tier t use [SEED, cell, 100 + 10 t + p, event]. Raw arrays only."""
    cases = W.make_cases()
    wp = cell.params()
    events = [W.draw_event(idx, i, wp, cases) for i in range(n)]
    out = dict(idx=idx, cell=cell, n=n, tag=J.tool_settings_tag(), n_compl=np.array([e.n for e in events]), kind=np.array([e.kind for e in events]), pol={})
    for ti, tier in enumerate(TIERS):
        for pol in policies_for2(cell):
            mins, chk, ok, wc, cn, tr, gs = [], [], [], [], [], [], []
            for i, ev in enumerate(events):
                cs = [cases[(tier, r)] for r in ev.rooms]
                ctxs = [W.context_dict(tier, r) for r in ev.rooms]
                oracle = W.Oracle(ev, wp.rel_a, np.random.default_rng([SEED, idx, 100 + 10 * ti + P.POLICY_INDEX[pol], i]))
                r = P.run_policy(pol, cs, oracle, ctxs)
                a, b, c = J.score(r, ev)
                mins.append(r["minutes"])
                chk.append(r["n_checks"])
                ok.append(a)
                wc.append(b)
                cn.append(c)
                if i < TRACE_EVENTS:
                    tr.append(r["trace"])
                    gs.append(r["guess"])
            out["pol"][(tier, pol)] = dict(minutes=np.array(mins, float), checks=np.array(chk, float), correct=np.array(ok, float), wc=np.array(wc, float), concluded=np.array(cn, float),
                                           trace=tr, guess=gs)
    return out


def _run_args(args):
    return run_cell2(*args)


def compute_cells2(cells: list[tuple[int, J.Cell]], n: int = N_EPISODES, workers: int | None = None) -> list[dict]:
    """Deterministic whatever the number of workers."""
    jobs = [(i, c, n) for i, c in cells]
    workers = workers if workers is not None else min(8, os.cpu_count() or 1)
    if workers <= 1 or len(jobs) == 1:
        return [_run_args(j) for j in jobs]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_run_args, jobs, chunksize=1))


# ---------------------------------------------------------------------------------------------- merging with Addendum 30's stored results, and the analysis
def merged(r2: dict, r30: dict) -> dict:
    """Addendum 30's cell result (cut to the first `n` events of `r2`; the events are identical by construction) with the new policies added."""
    n = r2["n"]
    if r30["idx"] != r2["idx"] or r30["n"] < n:
        raise ValueError("the stored Addendum 30 cell does not match")
    m = dict(r30)
    m["n"], m["n_compl"], m["kind"] = n, r30["n_compl"][:n], r30["kind"][:n]
    cut = {k: dict(v, minutes=v["minutes"][:n], checks=v["checks"][:n], correct=v["correct"][:n], wc=v["wc"][:n], concluded=v["concluded"][:n]) for k, v in r30["pol"].items()}
    m["pol"] = {**cut, **r2["pol"]}
    return m


def analyze_cell2(res: dict, B: int = BOOT_B) -> dict:
    """`res` is a merged cell. Bootstrap `[SEED, cell, 99, subset]`."""
    masks = J.subset_masks(res)
    boot = {}
    for si, sub in enumerate(SUBSETS):
        idx = np.flatnonzero(masks[sub])
        boot[sub] = (idx, np.random.default_rng([SEED, res["idx"], 99, si]).integers(0, len(idx), (B, len(idx))) if len(idx) else None)
    summ, cmp_ = {}, {}
    for tier in TIERS:
        views = {p: J.per_event(res, tier, p) for (t, p) in res["pol"] if t == tier}
        for pol, v in views.items():
            for sub in SUBSETS:
                summ[(tier, pol, sub)] = J.summarize(v, masks[sub])
        for name, (a, b) in COMPS2.items():
            if a not in views or b not in views:
                continue
            for sub in SUBSETS:
                idx, bt = boot[sub]
                if bt is not None:
                    cmp_[(tier, name, sub)] = J.compare(res, tier, a, b, idx, bt)
    return dict(idx=res["idx"], cell=res["cell"], n=res["n"], counts={s: int(masks[s].sum()) for s in SUBSETS}, sum=summ, cmp=cmp_, mean_complaints=float(res["n_compl"].mean()))


cell_of = J.cell_of
shares = J.shares


# ---------------------------------------------------------------------------------------------- predictions and decision (frozen operationalisation)
def predictions2(analyses: list[dict]) -> dict:
    """P1-P11 of Addendum 31, each strict, exactly as registered (P9 on `shared` events, the default of the registration)."""
    pc = cell_of(analyses, **J.PRIMARY)
    S_, C_ = pc["sum"], pc["cmp"]
    p = {}
    i2 = C_[("T2", "I", "shared")]
    p["P1"] = (i2["r_min"] <= -P1_BAR, f"joint2 vs joint, T2, shared: {100 * i2['r_min']:+.0f}% minutes")
    j2 = C_[("T2", "J", "shared")]
    p["P2"] = (j2["r_min"] <= -P2_BAR, f"ticket_memo2 vs ticket_memo, T2, shared: {100 * j2['r_min']:+.0f}% minutes")
    i3 = C_[("T3", "I", "shared")]
    p["P3"] = (abs(i3["r_min"]) < P3_BAR, f"joint2 vs joint, T3, shared: {100 * i3['r_min']:+.0f}% minutes")
    h2 = C_[("T2", "H", "shared")]
    p["P4"] = (h2["label"] != P4_LABEL, f"joint2 vs ticket_memo2, T2, shared: {h2['label']} ({100 * h2['r_min']:+.0f}% minutes, accuracy {h2['acc']})")
    p["P5"] = (abs(h2["r_min"]) < P5_BAR, f"joint2 vs ticket_memo2, T2, shared: {100 * h2['r_min']:+.0f}% minutes")
    ok6, ok7, d6, d7 = True, True, [], []
    for t in J.TIERS:
        a, b = S_[(t, "tool_joint2", "all")], S_[(t, "tool_joint", "all")]
        ok6 &= a["wrong_confident"] <= b["wrong_confident"] + P6_BAR
        ok7 &= a["accuracy"] >= b["accuracy"] - P7_BAR
        d6.append(f"{t}: {a['wrong_confident']:.3f} vs {b['wrong_confident']:.3f}")
        d7.append(f"{t}: {a['accuracy']:.3f} vs {b['accuracy']:.3f}")
    p["P6"] = (ok6, "wrong-and-confident, joint2 vs joint, all events: " + "; ".join(d6))
    p["P7"] = (ok7, "accuracy, joint2 vs joint, all events: " + "; ".join(d7))
    ok8, d8 = True, []
    for mp in ("M1", "M2"):
        s = cell_of(analyses, shared="assumed", map=mp, rel="R0")["sum"]
        d = s[("T2", "tool_joint2", "all")]["wrong_confident"] - s[("T2", "tool_ticket_memo2", "all")]["wrong_confident"]
        ok8 &= d < P8_BAR
        d8.append(f"{mp}: {d:+.3f}")
    p["P8"] = (ok8, "T2 wrong-and-confident, joint2 minus ticket_memo2, all events: " + "; ".join(d8))
    ok9, d9 = True, []
    for t in J.TIERS:
        labels = [cell_of(analyses, shared=sh, map="M0", rel="R0")["cmp"][(t, "M", "shared")]["label"] for sh in J.LEVELS["shared"]]
        n_not = sum(1 for x in labels if x != "IMPROVES")
        ok9 &= n_not >= 2
        d9.append(f"{t}: {labels}")
    p["P9"] = (ok9, "look-ahead vs one-step, shared events, three cells: " + "; ".join(d9))
    ok10, d10 = True, []
    for t in J.TIERS:
        a, b = S_[(t, "tool_joint2", "single")], S_[(t, "tool_joint", "single")]
        d = abs(a["minutes"] - b["minutes"]) / b["minutes"]
        ok10 &= d <= P10_BAR
        d10.append(f"{t}: {100 * d:.1f}%")
    p["P10"] = (ok10, "single events, joint2 vs joint: " + "; ".join(d10))
    o2 = C_[("T2", "O", "shared")]
    p["P11"] = (o2["r_min"] <= -P11_BAR, f"joint3 vs joint2, T2, shared: {100 * o2['r_min']:+.0f}% minutes")
    return p


def decision2(analyses: list[dict]) -> str:
    """The frozen decision on the primary cell's `shared` events, with the safety qualifier."""
    pc = cell_of(analyses, **J.PRIMARY)["cmp"]
    h2, h3 = pc[("T2", "H", "shared")]["label"], pc[("T3", "H", "shared")]["label"]
    if h2 == "IMPROVES" and h3 != "WORSE":
        d = "JOINT MACHINERY NOW ADDS VALUE"
    elif h2 == "WORSE" or h3 == "WORSE":
        d = "THE ROUTINE STILL WINS"
    else:
        d = "NO EDGE EITHER WAY"
    n = 0
    for mp in ("M1", "M2"):
        s = cell_of(analyses, shared="assumed", map=mp, rel="R0")["sum"]
        for t in J.TIERS:
            n += s[(t, "tool_joint2", "all")]["wrong_confident"] - s[(t, "tool_ticket_memo2", "all")]["wrong_confident"] >= UNSAFE_BAR
    return d + (" + UNSAFE UNDER MAP FAULTS" if n >= UNSAFE_CELLS else "")


# ---------------------------------------------------------------------------------------------- gates
def gate_g1(results: list[dict], raw30: list[dict] | None, n: int = G1_EVENTS) -> tuple[bool, str]:
    """Regression: the events equal Addendum 30's stored ones in every cell, and Addendum 30's `tool_joint` and `tool_ticket_memo`, re-run on the first `n` events of every cell at both tiers
    with Addendum 30's streams, reproduce its stored minutes and correct counts exactly (the rule off changes nothing)."""
    if raw30 is None:
        return False, "Addendum 30's raw results are not available"
    by = {r["idx"]: r for r in raw30}
    cases = W.make_cases()
    bad_events, bad_runs, runs = [], 0, 0
    for r in results:
        old = by.get(r["idx"])
        if old is None or not (np.array_equal(r["n_compl"], old["n_compl"][:r["n"]]) and np.array_equal(r["kind"], old["kind"][:r["n"]])):
            bad_events.append(r["idx"])
            continue
        wp = r["cell"].params()
        for ti, tier in enumerate(TIERS):
            for pol in ("tool_joint", "tool_ticket_memo"):
                for i in range(min(n, r["n"])):
                    ev = W.draw_event(r["idx"], i, wp, cases)
                    cs = [cases[(tier, x)] for x in ev.rooms]
                    res = P.run_policy(pol, cs, W.Oracle(ev, wp.rel_a, np.random.default_rng([J.SEED, r["idx"], 100 + 10 * ti + P.POLICY_INDEX[pol], i])), [W.context_dict(tier, x) for x in ev.rooms])
                    a, _, _ = J.score(res, ev)
                    st = old["pol"][(tier, pol)]
                    runs += 1
                    bad_runs += not (res["minutes"] == st["minutes"][i] and a == st["correct"][i])
    return not bad_events and bad_runs == 0, f"events differ in cells {bad_events}; {runs} re-run Addendum 30 episodes: {bad_runs} differ"


def gate_g2(n_groups: int = 100, seed: int = 6) -> tuple[bool, str]:
    """The rule: exactly one catalogue check bears on the air handler; the rule changes only who is informed (beliefs equal brute force and equal the rule-off beliefs); a
    `static_at_box` answer either way informs the whole group with the rule on and only its complaint with it off; any other room or box reading informs only its complaint; an `unsure`
    informs nobody; an air-handler reading informs the group either way."""
    bears = [c.name for c in K.CATALOGUE if bears_on_ahu(c)]
    if bears != ["static_at_box"]:
        return False, f"checks that bear on the air handler: {bears}"
    rng = np.random.default_rng([J.SEED, seed])
    cases = W.make_cases()
    worst = 0.0
    for g in range(n_groups):
        tier = TIERS[g % 2]
        a = int(rng.integers(W.N_AHU))
        k = int(rng.integers(2, 5))
        rooms = [int(r) for r in rng.choice(np.arange(a * W.PER_AHU, (a + 1) * W.PER_AHU), size=k, replace=False)]
        cs = [cases[(tier, r)] for r in rooms]
        js = JointSettings(f=float(rng.uniform(0.005, 0.2)), rho=float(rng.uniform(0.005, 0.2)))
        off, on = JointModel(cs, js), JointModel(cs, js, group_informing=True)
        so, sn = off.initial(), on.initial()
        for _ in range(int(rng.integers(1, 5))):
            opts = off.options(so, off.all_stats(so), 2.0, 0.0, 0.0)
            o = opts[int(rng.integers(len(opts)))]
            twin = next(x for x in on.options(sn, on.all_stats(sn), 2.0, 0.0, 0.0) if x.key == o.key)
            pos = bool(rng.random() < 0.5)
            so, sn = off.apply(so, o, pos), on.apply(sn, twin, pos)
            if not sn.informed >= so.informed:
                return False, "the rule on informs fewer complaints than the rule off"
        post, marg = J.brute_force(on, sn)
        for aa, gs in on.all_stats(sn).items():
            worst = max(worst, float(np.abs(gs.W - post[aa]).max()))
            for t, i in enumerate(gs.idx):
                worst = max(worst, float(np.abs(gs.marg[t] - marg[i]).max()), float(np.abs(gs.marg[t] - off.marginals(so)[i]).max()))
    cs = [cases[("T2", r)] for r in (0, 1, 2)]
    off, on = JointModel(cs), JointModel(cs, group_informing=True)
    s0 = off.initial()
    find = lambda m, kind, name, who: next(o for o in m.options(s0, m.all_stats(s0), 2.0, 0.0, 0.0) if o.kind == kind and o.check.name == name and o.who == who)  # noqa: E731
    checks = True
    for positive in (True, False):
        checks &= on.apply(s0, find(on, "complaint", "static_at_box", 0), positive).informed == {0, 1, 2} and off.apply(s0, find(off, "complaint", "static_at_box", 0), positive).informed == {0}
        checks &= on.apply(s0, find(on, "complaint", "power_24vac", 0), positive).informed == {0} and on.apply(s0, find(on, "ahu", "ahu_visit", "AHU-0"), positive).informed == {0, 1, 2}
        checks &= off.apply(s0, find(off, "ahu", "ahu_visit", "AHU-0"), positive).informed == {0, 1, 2}
    checks &= on.apply(s0, find(on, "complaint", "static_at_box", 0), None).informed == frozenset()
    return worst < 1e-9 and bool(checks), f"one bearing check ({bears[0]}); {n_groups} random groups: largest difference from brute force or from the rule-off beliefs {worst:.2e}; informing semantics {'as registered' if checks else 'WRONG'}"


def gate_g3(results: list[dict], per_cell: int = 10) -> tuple[bool, str]:
    """Replay: the first events of `tool_joint2` and `tool_ticket_memo2` in every R1 cell, fed only their recorded answers, ask for the same checks in the same order and end with the same guesses."""
    cases = W.make_cases()
    checked, bad = 0, 0
    for res in results:
        if res["cell"].rel != "R1":
            continue
        wp = res["cell"].params()
        for tier in TIERS:
            for pol in ("tool_joint2", "tool_ticket_memo2"):
                for i in range(min(per_cell, TRACE_EVENTS, res["n"])):
                    ev = W.draw_event(res["idx"], i, wp, cases)
                    cs = [cases[(tier, r)] for r in ev.rooms]
                    rec = res["pol"][(tier, pol)]["trace"][i]
                    rep = J._ReplayJoint(rec) if pol == "tool_joint2" else J._ReplayTicket(rec, cs)
                    try:
                        r = P.run_policy(pol, cs, rep, [W.context_dict(tier, x) for x in ev.rooms])
                        same = r["guess"] == res["pol"][(tier, pol)]["guess"][i]
                    except ValueError:
                        same = False
                    checked += 1
                    bad += not same
    return bad == 0, f"{checked} replayed events: {bad} differ"


def gate_g4(results: list[dict], n: int = 30) -> tuple[bool, str]:
    """Reproducibility: the first cell re-run with `n` events reproduces its first `n` stored events, for every stored policy and tier."""
    first = min(results, key=lambda r: r["idx"])
    again = run_cell2(first["idx"], first["cell"], n)
    bad = [k for k, v in again["pol"].items() if not (np.array_equal(v["minutes"], first["pol"][k]["minutes"][:n]) and np.array_equal(v["correct"], first["pol"][k]["correct"][:n]))]
    return not bad and np.array_equal(again["n_compl"], first["n_compl"][:n]), f"cell {first['idx']}: {len(bad)} policy/tier series differ in the first {n} events"


def gate_g5(results: list[dict], n_cells: int = 18, expected_idx: list[int] | None = None, n: int | None = None) -> tuple[bool, str]:
    """Completeness and pairing: all cells, every new policy at both tiers (look-ahead only in its three cells), finite outputs, one event count."""
    want = expected_idx if expected_idx is not None else list(range(n_cells))
    got = sorted(r["idx"] for r in results)
    if got != want:
        return False, f"cells {got} != {want}"
    for r in results:
        pols = policies_for2(r["cell"])
        for t in TIERS:
            for p in pols:
                v = r["pol"].get((t, p))
                if v is None or len(v["minutes"]) != r["n"] or not (np.isfinite(v["minutes"]).all() and np.isfinite(v["correct"]).all()) or (v["minutes"] < 0).any():
                    return False, f"cell {r['idx']} {t} {p} incomplete or not finite"
        if [k for k in r["pol"] if k[1] not in pols]:
            return False, f"cell {r['idx']} has policies that should not be there"
        if n is not None and r["n"] != n:
            return False, f"cell {r['idx']} has {r['n']} events, not {n}"
    return True, f"{len(results)} cells, every new policy at both tiers on Addendum 30's events"


def gate_g6(results: list[dict], raw30: list[dict] | None = None) -> tuple[bool, str]:
    """The tool's settings equal Addendum 30's in every cell."""
    tags = {r["tag"] for r in results}
    if tags != {J.tool_settings_tag()}:
        return False, "the tool's settings differ from Addendum 30's"
    if raw30 is not None and {r["tag"] for r in raw30} != tags:
        return False, "the tool's settings differ from the stored Addendum 30 cells'"
    return True, "the tool's settings are Addendum 30's in every cell"
