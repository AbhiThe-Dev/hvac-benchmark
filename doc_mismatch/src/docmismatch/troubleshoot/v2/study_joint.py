"""Does investigating several complaints together save technician time? (PREREGISTRATION_DR.md Addendum 30.) Simulation only; nothing is fitted; nothing here is evidence about real
technicians or buildings.

A synthetic well-documented building (3 air handlers x 8 boxes and rooms) is visited with several complaints drawn from a generative model (world2.py). The same visits are worked by
seven policies (policies.py): the v1 tool ticket by ticket (three variants: plain, with the neighbour-informed prior, and also reusing air handler readings), the joint session (and the
same with two-step look-ahead), and two stand-in technicians that are my constructions. Two data tiers (T2: the drawings and design values; T3: also the control system) on the same events.
"""

from __future__ import annotations

import itertools
import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

import numpy as np

from .. import study as S
from .. import study_rating as SG
from ..v1.study_fast_v1 import break_even
from . import policies as P
from . import world2 as W
from .joint import JointModel, JointSession, JointSettings, State

# ---------------------------------------------------------------------------------------------- frozen constants (Addendum 30)
SEED = W.SEED
N_EPISODES = 1000                      # 300 in the pre-registration; raised before any comparison was read (clarification 2)
BOOT_B = 1000
TRACE_EVENTS = 12                      # events per cell whose full traces are stored (for the replay gate)
LEVELS = dict(shared=("rare", "assumed", "common"), map=("M0", "M1", "M2"), rel=("R0", "R1"))
F_OF = dict(rare=0.01, assumed=0.03, common=0.09)
MAP_OF = dict(M0=(0.0, 0.05), M1=(0.10, 0.05), M2=(0.10, 0.15))                  # (q_ahu, world P(documented box wrong))
REL_A = dict(R0=0.0, R1=0.25)
PRIMARY = dict(shared="assumed", map="M0", rel="R0")
SUBSETS = ("all", "shared", "multi", "single")
TIERS = W.TIER_NAMES
COMPS = dict(A=("tool_joint", "tool_ticket"), B=("tool_joint", "tool_ticket_memo"), C=("tool_ticket_memo", "tool_ticket"), D=("tool_ticket_nb", "tool_ticket"),
             E=("tool_joint", "fast_parent"), F=("tool_joint", "fast_ticket"), G=("tool_joint_la2", "tool_joint"))
SHARE_BAR = 0.15                       # P1: at least this fraction fewer minutes
P2_BAR, P3_BAR, P5_BAR, P6_MIN, P6_ACC, P7_MIN, P7_ACC, P8_BAR, P9_BAR = 0.10, 0.0, 0.01, 0.05, 0.10, 0.03, 0.02, 0.05, 0.03
UNSAFE_BAR, UNSAFE_CELLS = 0.02, 2
ALLOWED_FAILS = 0


@dataclass(frozen=True)
class Cell:
    shared: str
    map: str
    rel: str

    @property
    def is_primary(self) -> bool:
        return all(getattr(self, k) == v for k, v in PRIMARY.items())

    @property
    def has_lookahead(self) -> bool:
        return self.map == "M0" and self.rel == "R0"

    def params(self) -> W.WorldParams:
        q, pw = MAP_OF[self.map]
        return W.WorldParams(F_OF[self.shared], q, pw, REL_A[self.rel])


def all_cells() -> list[Cell]:
    """The 18 cells, indexed in the lexicographic order of the factor levels as listed (the last factor varies fastest)."""
    return [Cell(*lv) for lv in itertools.product(*(LEVELS[f] for f in LEVELS))]


def policies_for(cell: Cell) -> tuple:
    return tuple(p for p in P.POLICIES if p not in P.LOOKAHEAD_POLICIES or cell.has_lookahead)


def tool_settings_tag() -> tuple:
    """What the tool assumes, identical in every cell (gate G6)."""
    s, js = W.tool_settings(), JointSettings()
    return (s.p_wrong, s.p_acts_fail, s.unlisted_share, s.tau, s.min_gain, js.f, js.fan_share, js.rho, js.r_fan, js.r_low)


# ---------------------------------------------------------------------------------------------- one cell
def score(res: dict, ev: W.Event) -> tuple[int, int, int]:
    """(complaints diagnosed correctly, concluded and wrong, concluded) for one policy's result on one event."""
    ok = [g == t for g, t in zip(res["guess"], ev.causes)]
    conc = res["concluded"]
    return sum(ok), sum(1 for o, c in zip(ok, conc) if c and not o), sum(1 for c in conc if c)


def run_cell(idx: int, cell: Cell, n: int = N_EPISODES) -> dict:
    """`n` events per policy and tier on the same `n` draws (stream [SEED, cell, 0, event]); the answers of policy p at tier t use [SEED, cell, 100 + 10 t + p, event]. Raw arrays only."""
    cases = W.make_cases()
    wp = cell.params()
    events = [W.draw_event(idx, i, wp, cases) for i in range(n)]
    out = dict(idx=idx, cell=cell, n=n, tag=tool_settings_tag(), n_compl=np.array([e.n for e in events]), kind=np.array([e.kind for e in events]),
               shared_states=[tuple(e.u.values()) for e in events[:TRACE_EVENTS]], truth=[e.causes for e in events[:TRACE_EVENTS]], rooms=[e.rooms for e in events[:TRACE_EVENTS]], pol={})
    for ti, tier in enumerate(TIERS):
        for pol in policies_for(cell):
            mins, chk, ok, wc, cn, tr, gs = [], [], [], [], [], [], []
            for i, ev in enumerate(events):
                cs = [cases[(tier, r)] for r in ev.rooms]
                ctxs = [W.context_dict(tier, r) for r in ev.rooms]
                oracle = W.Oracle(ev, wp.rel_a, np.random.default_rng([SEED, idx, 100 + 10 * ti + P.POLICY_INDEX[pol], i]))
                r = P.run_policy(pol, cs, oracle, ctxs)
                a, b, c = score(r, ev)
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
def subset_masks(res: dict) -> dict:
    k = res["kind"]
    return dict(all=np.ones(len(k), bool), shared=k == "shared", multi=k == "multi", single=k == "single")


def per_event(res: dict, tier: str, pol: str) -> dict:
    a, n = res["pol"][(tier, pol)], res["n_compl"].astype(float)
    return dict(minutes=a["minutes"], checks=a["checks"], acc=a["correct"] / n, wc=a["wc"] / n, conc=a["concluded"] / n, correct=a["correct"], n=n)


def summarize(v: dict, mask: np.ndarray) -> dict:
    if not mask.any():
        return dict(n=0)
    return dict(n=int(mask.sum()), minutes=float(v["minutes"][mask].mean()), checks=float(v["checks"][mask].mean()), accuracy=float(v["acc"][mask].mean()),
                accuracy_c=float(v["correct"][mask].sum() / v["n"][mask].sum()), wrong_confident=float(v["wc"][mask].mean()), concluded=float(v["conc"][mask].mean()),
                complaints=float(v["n"][mask].mean()))


def compare(res: dict, tier: str, a: str, b: str, idx: np.ndarray, boot: np.ndarray) -> dict:
    """Policy a minus policy b on the same events of `idx`, with Addendum 21's frozen labels (5% minutes, 0.02 accuracy, safety 0.02, paired 95% intervals)."""
    A, B = per_event(res, tier, a), per_event(res, tier, b)
    d_min, d_acc, d_wc = A["minutes"][idx] - B["minutes"][idx], A["acc"][idx] - B["acc"][idx], A["wc"][idx] - B["wc"][idx]
    ci_min, ci_acc, ci_wc = S.paired_ci(d_min, boot), S.paired_ci(d_acc, boot), S.paired_ci(d_wc, boot)
    base = float(B["minutes"][idx].mean())
    r_min = float(d_min.mean() / base) if base > 0 else float("nan")
    ts, as_ = SG.time_state(r_min, ci_min), SG.acc_state(float(d_acc.mean()), ci_acc)
    kind, wstar = break_even(float(A["minutes"][idx].mean()), float(A["acc"][idx].mean()), base, float(B["acc"][idx].mean()))
    return dict(d_min=float(d_min.mean()), r_min=r_min, d_acc=float(d_acc.mean()), d_wc=float(d_wc.mean()), d_checks=float((A["checks"][idx] - B["checks"][idx]).mean()), ci_min=ci_min,
                ci_acc=ci_acc, ci_wc=ci_wc, time=ts, acc=as_, label=SG.label(ts, as_), safety=SG.safety_flag(float(d_wc.mean()), ci_wc), break_even=kind, wrong_cost=wstar,
                minutes_a=float(A["minutes"][idx].mean()), minutes_b=base)


def analyze_cell(res: dict, B: int = BOOT_B) -> dict:
    masks = subset_masks(res)
    boot = {}
    for si, sub in enumerate(SUBSETS):
        idx = np.flatnonzero(masks[sub])
        boot[sub] = (idx, np.random.default_rng([SEED, res["idx"], 99, si]).integers(0, len(idx), (B, len(idx))) if len(idx) else None)
    summ, cmp_ = {}, {}
    for tier in TIERS:
        views = {p: per_event(res, tier, p) for (t, p) in res["pol"] if t == tier}
        for pol, v in views.items():
            for sub in SUBSETS:
                summ[(tier, pol, sub)] = summarize(v, masks[sub])
        for name, (a, b) in COMPS.items():
            if a not in views or b not in views:
                continue
            for sub in SUBSETS:
                idx, bt = boot[sub]
                if bt is not None:
                    cmp_[(tier, name, sub)] = compare(res, tier, a, b, idx, bt)
    return dict(idx=res["idx"], cell=res["cell"], n=res["n"], counts={s: int(masks[s].sum()) for s in SUBSETS}, sum=summ, cmp=cmp_,
                mean_complaints=float(res["n_compl"].mean()))


def cell_of(analyses: list[dict], **kw) -> dict:
    hits = [a for a in analyses if all(getattr(a["cell"], k) == v for k, v in kw.items())]
    if len(hits) != 1:
        raise KeyError(f"{len(hits)} cells match {kw}")
    return hits[0]


def shares(analyses: list[dict], key: tuple) -> dict:
    """Shares of the cells by label for one (tier, comparison, subset); the two kinds of TRADE; safety."""
    es = [a["cmp"][key] for a in analyses if key in a["cmp"]]
    n = max(len(es), 1)
    out = {k: sum(e["label"] == k for e in es) / n for k in ("IMPROVES", "WORSE", "TRADE", "NEITHER")}
    out["FASTER_LESS"] = sum(e["time"] == "FASTER" and e["acc"] == "LESS" for e in es) / n
    out["SLOWER_MORE"] = sum(e["time"] == "SLOWER" and e["acc"] == "MORE" for e in es) / n
    out["SAFETY_REGRESSION"] = sum(e["safety"] == "REGRESSION" for e in es) / n
    out["SAFETY_GAIN"] = sum(e["safety"] == "GAIN" for e in es) / n
    out["n_cells"] = len(es)
    return out


# ---------------------------------------------------------------------------------------------- predictions and decision (frozen operationalisation)
def joint_predictions(analyses: list[dict]) -> dict:
    """P1-P9 of Addendum 30, each strict, exactly as registered."""
    pc = cell_of(analyses, **PRIMARY)
    S_, C_ = pc["sum"], pc["cmp"]
    p = {}
    a = C_[("T2", "A", "shared")]
    p["P1"] = (a["r_min"] <= -SHARE_BAR and a["acc"] != "LESS", f"joint vs ticket, T2, shared: {100 * a['r_min']:+.0f}% minutes, accuracy {a['acc']}")
    b = C_[("T2", "B", "shared")]
    p["P2"] = (b["r_min"] > -P2_BAR, f"joint vs ticket_memo, T2, shared: {100 * b['r_min']:+.0f}% minutes")
    d = C_[("T2", "D", "all")]
    p["P3"] = (d["r_min"] < P3_BAR, f"ticket_nb vs ticket, T2, all: {100 * d['r_min']:+.0f}% minutes")
    save = {t: -C_[(t, "A", "shared")]["d_min"] for t in TIERS}
    p["P4"] = (save["T3"] < save["T2"], f"minutes joint saves against ticket on shared events: T2 {save['T2']:.1f}, T3 {save['T3']:.1f}")
    m0 = cell_of(analyses, shared="assumed", map="M0", rel="R0")["sum"]
    m1 = cell_of(analyses, shared="assumed", map="M1", rel="R0")["sum"]
    wj0, wj1, wm1 = m0[("T2", "tool_joint", "all")]["wrong_confident"], m1[("T2", "tool_joint", "all")]["wrong_confident"], m1[("T2", "tool_ticket_memo", "all")]["wrong_confident"]
    p["P5"] = (wj1 - wj0 >= P5_BAR and wj1 >= wm1, f"T2 wrong-and-confident: joint M0 {wj0:.3f}, joint M1 {wj1:.3f}, ticket_memo M1 {wm1:.3f}")
    fa, fj = S_[("T2", "fast_parent", "all")], S_[("T2", "tool_joint", "all")]
    p["P6"] = (fa["minutes"] <= (1 - P6_MIN) * fj["minutes"] and fj["accuracy"] - fa["accuracy"] >= P6_ACC,
               f"T2 all: fast_parent {fa['minutes']:.0f} min {fa['accuracy']:.2f}, joint {fj['minutes']:.0f} min {fj['accuracy']:.2f}")
    ok7, det = True, []
    for sh in LEVELS["shared"]:
        for t in TIERS:
            s = cell_of(analyses, shared=sh, map="M0", rel="R0")["sum"]
            la, jo = s[(t, "tool_joint_la2", "all")], s[(t, "tool_joint", "all")]
            dm, da = abs(la["minutes"] - jo["minutes"]) / jo["minutes"], abs(la["accuracy"] - jo["accuracy"])
            ok7 &= dm < P7_MIN and da < P7_ACC
            det.append(f"{sh}/{t}: {100 * dm:.1f}%, {da:.3f}")
    p["P7"] = (ok7, "look-ahead vs one-step |minutes| / |accuracy|: " + "; ".join(det))
    ok8, det = True, []
    for t in TIERS:
        j, nb = S_[(t, "tool_joint", "single")], S_[(t, "tool_ticket_nb", "single")]
        dm = abs(j["minutes"] - nb["minutes"]) / nb["minutes"]
        ok8 &= dm <= P8_BAR
        det.append(f"{t}: {100 * dm:.1f}%")
    p["P8"] = (ok8, "single events, joint vs ticket_nb: " + "; ".join(det))
    r = cell_of(analyses, shared="rare", map="M0", rel="R0")["sum"]
    ok9, det = True, []
    for t in TIERS:
        me, jo = r[(t, "tool_ticket_memo", "all")], r[(t, "tool_joint", "all")]
        adv = (me["minutes"] - jo["minutes"]) / me["minutes"]
        ok9 &= adv < P9_BAR
        det.append(f"{t}: {100 * adv:+.1f}%")
    p["P9"] = (ok9, "rare shared, all events, advantage of joint over ticket_memo: " + "; ".join(det))
    return p


def decision(analyses: list[dict]) -> str:
    """The frozen decision on the primary cell's `shared` events (T2 decides, T3 must not be WORSE), with the safety qualifier."""
    pc = cell_of(analyses, **PRIMARY)["cmp"]
    b2, b3, c2 = pc[("T2", "B", "shared")]["label"], pc[("T3", "B", "shared")]["label"], pc[("T2", "C", "shared")]["label"]
    if b2 == "IMPROVES" and b3 != "WORSE":
        d = "JOINT MACHINERY ADDS VALUE"
    elif c2 == "IMPROVES":
        d = "THE ROUTINE CAPTURES IT"
    else:
        d = "NO GAIN FROM SHARING"
    n = 0
    for mp in ("M1", "M2"):
        s = cell_of(analyses, shared="assumed", map=mp, rel="R0")["sum"]
        for t in TIERS:
            n += s[(t, "tool_joint", "all")]["wrong_confident"] - s[(t, "tool_ticket_memo", "all")]["wrong_confident"] >= UNSAFE_BAR
    return d + (" + UNSAFE UNDER MAP FAULTS" if n >= UNSAFE_CELLS else "")


# ---------------------------------------------------------------------------------------------- gates
def brute_force(model: JointModel, s: State) -> tuple[dict, list]:
    """An independent computation of the joint model's beliefs: for each group and state, the explicit joint table over (cause of complaint 1, ..., cause of complaint k) is built as an
    outer product and summed, then marginalised. It uses the model's tables and the definition of the model, not its factorised formulas for the group weights and marginals."""
    js = model.js
    post, marg = {}, [None] * model.n
    for a, idx in model.groups.items():
        tot = np.zeros(model.n_states)
        cm = [np.zeros(len(model.causes[i])) for i in idx]
        for u in range(model.n_states):
            base = js.state_prior[u] * np.exp((model.children[a] - len(idx)) * model.log_quiet[u] + s.ahu_ll[a][u])
            joint = np.asarray(base, float)
            for i in idx:
                joint = np.multiply.outer(joint, model.J[i][u] * s.lik[i])
            tot[u] = joint.sum()
            for t in range(len(idx)):
                axes = tuple(ax for ax in range(len(idx)) if ax != t)
                cm[t] += joint.sum(axis=axes) if axes else joint
        z = tot.sum()
        post[a] = tot / z
        for t, i in enumerate(idx):
            marg[i] = cm[t] / z
    return post, marg


def gate_g1(n_groups: int = 200, seed: int = 5) -> tuple[bool, str]:
    """Exactness: the joint model against brute-force enumeration on random groups of 1-3 complaints with random observations (air handler and room checks)."""
    rng = np.random.default_rng([SEED, seed])
    cases = W.make_cases()
    worst = 0.0
    for g in range(n_groups):
        tier = TIERS[g % 2]
        a = int(rng.integers(W.N_AHU))
        k = int(rng.integers(1, 4))
        rooms = [int(r) for r in rng.choice(np.arange(a * W.PER_AHU, (a + 1) * W.PER_AHU), size=k, replace=False)]
        model = JointModel([cases[(tier, r)] for r in rooms], JointSettings(f=float(rng.uniform(0.005, 0.2)), rho=float(rng.uniform(0.005, 0.2)), r_fan=float(rng.uniform(0.3, 1.0)),
                                                                                r_low=float(rng.uniform(0.2, 1.0))))
        s = model.initial()
        for _ in range(int(rng.integers(0, 5))):
            opts = model.options(s, model.all_stats(s), 2.0, 0.0, 0.0)
            if not opts:
                break
            o = opts[int(rng.integers(len(opts)))]
            s = model.apply(s, o, bool(rng.random() < 0.5))
        post, marg = brute_force(model, s)
        stats = model.all_stats(s)
        for aa, gs in stats.items():
            worst = max(worst, float(np.abs(gs.W - post[aa]).max()))
            for t, i in enumerate(gs.idx):
                worst = max(worst, float(np.abs(gs.marg[t] - marg[i]).max()))
    return worst < 1e-9, f"{n_groups} random groups: largest difference from brute-force enumeration {worst:.2e}"


def _consistent_single(ev: W.Event) -> bool:
    """A single-complaint event on which v1's world and this one agree: the complaint's documented air handler is in exactly the state its cause implies."""
    if ev.n != 1:
        return False
    a = f"AHU-{ev.rooms[0] // W.PER_AHU}"
    c = ev.causes[0]
    return ev.u[a] == (c[0] if c[0] in ("ahu_fan_off", "low_static") else "ok") and all(ev.true_ahu[f"VAV-{b}"] == f"AHU-{b // W.PER_AHU}" for b in range(W.N_BOX))


def gate_g2(per_tier: int = 25) -> tuple[bool, str]:
    """Code path: `tool_ticket` reproduces v1's `simulate_v1` exactly on consistent single-complaint events; and a scripted joint transcript costs the hand-summed minutes."""
    from ..v1.sim1 import World, simulate_v1
    cases = W.make_cases()
    wp = W.WorldParams(0.03, 0.0, 0.05, 0.0)
    bad, done = 0, 0
    for ti, tier in enumerate(TIERS):
        i, got = 0, 0
        while got < per_tier and i < 5000:
            ev = W.draw_event(9, i, wp, cases)
            i += 1
            if not _consistent_single(ev):
                continue
            got += 1
            r0 = ev.rooms[0]
            case = cases[(tier, r0)]
            mine = P.run_ticket([case], W.Oracle(ev, 0.0, np.random.default_rng([SEED, 9, ti, i])), "plain")
            ref = simulate_v1(case, World(ev.causes[0], W.context_dict(tier, r0), None), "entropy", np.random.default_rng([SEED, 9, ti, i]), 12)
            same = mine["guess"][0] == ref["guess"] and abs(mine["minutes"] - ref["minutes"]) < 1e-9 and mine["n_checks"] == ref["n_checks"]
            bad += not same
            done += 1
    # scripted transcript: two rooms on AHU-0 at T2; the air handler gauge (15 to get there + 2 to read), then the 24 VAC reading at each box (6 + 4 each: the location changes)
    cs = [cases[("T2", 0)], cases[("T2", 1)]]
    sess = JointSession(cs)
    minutes_ok = True
    everything = lambda: sess.model.options(sess.state, sess.model.all_stats(sess.state), sess.tau, 0.0, 0.0)  # noqa: E731  (the scripted transcript ignores the value thresholds)
    o1 = next(o for o in everything() if o.kind == "ahu" and o.check.name == "ahu_gauge")
    minutes_ok &= abs(o1.minutes - 17.0) < 1e-9
    sess.report("normal", o1)
    o2 = next(o for o in everything() if o.check.name == "power_24vac" and o.who == 0)
    minutes_ok &= abs(o2.minutes - 10.0) < 1e-9
    sess.report("normal", o2)
    o3 = next(o for o in everything() if o.check.name == "power_24vac" and o.who == 1)
    minutes_ok &= abs(o3.minutes - 10.0) < 1e-9
    sess.report("normal", o3)
    minutes_ok &= abs(sess.elapsed - 37.0) < 1e-9
    return bad == 0 and minutes_ok, f"{done} single-complaint events: {bad} differ from simulate_v1; scripted joint transcript costs {sess.elapsed:g} minutes (hand sum 37)"


def gate_g3(results: list[dict], per_cell: int = 10) -> tuple[bool, str]:
    """Replay: the first events of `tool_joint`, `tool_ticket_memo` and `fast_parent` in every R1 cell, fed only their recorded answers, ask for the same checks in the same order and end
    with the same guesses (their choices depend on the answers and on nothing about the world that produced them)."""
    cases = W.make_cases()
    checked, bad = 0, 0
    for res in results:
        if res["cell"].rel != "R1":
            continue
        wp = res["cell"].params()
        for ti, tier in enumerate(TIERS):
            for pol in ("tool_joint", "tool_ticket_memo", "fast_parent"):
                if (tier, pol) not in res["pol"]:
                    continue
                for i in range(min(per_cell, TRACE_EVENTS)):
                    ev = W.draw_event(res["idx"], i, wp, cases)
                    cs = [cases[(tier, r)] for r in ev.rooms]
                    ctxs = [W.context_dict(tier, r) for r in ev.rooms]
                    rec = res["pol"][(tier, pol)]["trace"][i]
                    rep = _ReplayJoint(rec) if pol == "tool_joint" else _ReplayTicket(rec, cs)
                    try:
                        r = P.run_policy(pol, cs, rep, ctxs)
                        same = r["guess"] == res["pol"][(tier, pol)]["guess"][i]
                    except ValueError:
                        same = False
                    checked += 1
                    bad += not same
    return bad == 0, f"{checked} replayed events: {bad} differ"


class _ReplayJoint:
    def __init__(self, trace: list):
        self.it = iter(trace)

    def ask_room(self, i, ck, target):
        item = next(self.it, None)
        if item is None or item[:4] != ("complaint", i, ck.name, target):
            raise ValueError("the replayed policy asked for something else")
        return item[4]

    def ask_ahu(self, a, ck):
        item = next(self.it, None)
        if item is None or item[:4] != ("ahu", a, ck.name, a):
            raise ValueError("the replayed policy asked for something else")
        return item[4]


class _ReplayTicket:
    """Ticket policies and stand-ins: traces are (complaint, check, target, answer), and ("group", ahu, check, target, answer) for the parent-first stand-in's air handler checks."""

    def __init__(self, trace: list, cases: list):
        self.trace, self.pos, self.cases = list(trace), 0, cases

    def _take(self):
        item = self.trace[self.pos] if self.pos < len(self.trace) else None
        self.pos += 1
        return item

    def ask_room(self, i, ck, target):
        item = self._take()
        if item is None or item[0] != i or item[1] != ck.name or item[2] != target:
            raise ValueError("the replayed policy asked for something else")
        return item[3]

    def ask_ahu(self, a, ck):
        item = self._take()
        if item is None:
            raise ValueError("the replayed policy asked for something else")
        if item[0] == "group":
            if item[1] != a or item[2] != ck.name:
                raise ValueError("the replayed policy asked for something else")
            return item[4]
        if self.cases[item[0]].ahu != a or item[1] != ck.name:
            raise ValueError("the replayed policy asked for something else")
        return item[3]


def gate_g4(results: list[dict], n: int = 30) -> tuple[bool, str]:
    """Reproducibility: the first cell re-run with `n` events reproduces its first `n` stored events, for every stored policy and tier."""
    first = min(results, key=lambda r: r["idx"])
    again = run_cell(first["idx"], first["cell"], n)
    bad = [k for k, v in again["pol"].items() if not (np.array_equal(v["minutes"], first["pol"][k]["minutes"][:n]) and np.array_equal(v["correct"], first["pol"][k]["correct"][:n]))]
    return not bad and np.array_equal(again["n_compl"], first["n_compl"][:n]), f"cell {first['idx']}: {len(bad)} policy/tier series differ in the first {n} events"


def gate_g5(results: list[dict], n_cells: int = 18, expected_idx: list[int] | None = None, n: int | None = None) -> tuple[bool, str]:
    """Completeness and pairing: all cells, every policy at both tiers (look-ahead only in its three cells), finite outputs, one event count."""
    want = expected_idx if expected_idx is not None else list(range(n_cells))
    got = sorted(r["idx"] for r in results)
    if got != want:
        return False, f"cells {got} != {want}"
    for r in results:
        pols = policies_for(r["cell"])
        for t in TIERS:
            for p in pols:
                v = r["pol"].get((t, p))
                if v is None or len(v["minutes"]) != r["n"] or not (np.isfinite(v["minutes"]).all() and np.isfinite(v["correct"]).all()) or (v["minutes"] < 0).any():
                    return False, f"cell {r['idx']} {t} {p} incomplete or not finite"
        extra = [k for k in r["pol"] if k[1] not in pols]
        if extra:
            return False, f"cell {r['idx']} has policies that should not be there: {extra}"
        if n is not None and r["n"] != n:
            return False, f"cell {r['idx']} has {r['n']} events, not {n}"
    return True, f"{len(results)} cells, every policy at both tiers on identical events"


def gate_g6(results: list[dict]) -> tuple[bool, str]:
    """World sanity: the share of `shared` events rises strictly with f within each (map, rel); the tool's settings are the same in every cell."""
    if len({r["tag"] for r in results}) != 1:
        return False, "the tool's settings differ between cells"
    by = {(r["cell"].map, r["cell"].rel, r["cell"].shared): float((r["kind"] == "shared").mean()) for r in results}
    for mp in LEVELS["map"]:
        for rl in LEVELS["rel"]:
            xs = [by.get((mp, rl, sh)) for sh in LEVELS["shared"]]
            if None in xs:
                continue
            if not xs[0] < xs[1] < xs[2]:
                return False, f"share of shared events not increasing with f at {mp}/{rl}: {xs}"
    means = {sh: [v for k, v in by.items() if k[2] == sh] for sh in LEVELS["shared"]}
    return True, "shared-event share rises with f in every (map, rel) that has all three levels: " + ", ".join(f"{sh} {100 * np.mean(v):.0f}%" for sh, v in means.items() if v)
