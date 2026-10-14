"""Does the routine still capture the shared-cause saving once a cause exists that mostly does NOT make several rooms complain together? (PREREGISTRATION_DR.md Addendum 37.)
Simulation only; nothing is fitted; nothing here is evidence about real technicians or buildings.

Adds `causes.ECON_FAULT` ("the economizer is not delivering the free cooling it should") as a third upstream state, additively (see `causes.py`, `catalogue.py`, `joint.py`, `world2.py`):
every existing cell of Addenda 30/31/33-36 is untouched and reproduces exactly (gate G1). This module studies ONE new cell -- Addendum 30's primary shared/map/reliability levels, both
tiers -- with the third state added, not the full 18-cell sweep (registered as a deliberate, scoped-down first look, not an oversight).
"""

from __future__ import annotations

import numpy as np

from ..v1 import causes as C
from ..v1 import catalogue as K
from . import policies as P
from . import world2 as W
from .joint import JointSettings

# ---------------------------------------------------------------------------------------------- frozen constants (Addendum 37)
IDX = 18                              # one past study_joint's 18 cells (0-17): an independent RNG stream, no collision
SEED = W.SEED
N_EPISODES = 1000
TIERS = W.TIER_NAMES
SUBSETS = ("all", "shared", "multi", "single")
POLICIES = ("tool_ticket_memo2", "tool_joint2")
ECON = "econ_fault"

# the primary cell's shared/map/reliability levels (Addendum 30): f = 0.03 ("assumed"), q_ahu = 0.0 / p_wrong = 0.05 ("M0"), rel_a = 0.0 ("R0")
F0, Q_AHU0, P_WRONG0, REL_A0 = 0.03, 0.0, 0.05, 0.0

# placeholders (PREREGISTRATION_DR.md Addendum 37; PNNL_RTU, T24, CEC_ECON)
ECON_SHARE = 0.06                                              # econ_fault's causes.py share, between ahu_fan_off (0.05) and low_static (0.12)
ECON_F_SHARE = ECON_SHARE / (0.05 + 0.12 + ECON_SHARE)          # its share of f, on the same 5:12:x odds the module already uses for fan_share
ECON_R_AFFECT = 0.15                                            # P(a room on an econ-fault air handler complains): well under r_fan (0.9) / r_low (0.5)
ECON_SHARES = {**C.DEFAULT_SHARES, ECON: ECON_SHARE}
ECON_CHECKS = K.CATALOGUE + K.ECON_CHECKS


def wp_econ(f: float = F0) -> W.WorldParams:
    return W.WorldParams(f, Q_AHU0, P_WRONG0, REL_A0, extra_states=(ECON,), extra_share={ECON: ECON_F_SHARE}, extra_affect={ECON: ECON_R_AFFECT})


def js_econ() -> JointSettings:
    return JointSettings(extra_states=(ECON,), extra_affect={ECON: ECON_R_AFFECT}, extra_share={ECON: ECON_F_SHARE})


def make_cases_econ() -> dict:
    """{(tier, room): the tool's v1 case, econ-aware: extended checks, econ_fault enrolled via `shares`/`extra_causes`}."""
    bld = W.make_building2()
    s = W.tool_settings()
    return {(t, r): W.make_case_v1(bld, f"Room-{r}", W.TIER_ITEMS[t], settings=s, context=W.tier_context(t, r), member_name=f"Room {r}", shares=ECON_SHARES, extra_causes=(C.ECON_FAULT,),
                                   checks=ECON_CHECKS) for t in TIERS for r in range(W.N_BOX)}


def tool_settings_tag_econ() -> tuple:
    s, js = W.tool_settings(), js_econ()
    return (s.p_wrong, s.p_acts_fail, s.unlisted_share, s.tau, s.min_gain, js.f, js.fan_share, js.rho, js.r_fan, js.r_low, js.extra_states, tuple(sorted(js.extra_affect.items())),
            tuple(sorted(js.extra_share.items())), ECON_SHARE)


# ---------------------------------------------------------------------------------------------- one cell
def econ_shared(ev: W.Event) -> bool:
    """At least two complaints whose true cause is specifically `econ_fault` on the same (true) air handler (a stricter version of `Event.shared`, which counts any upstream cause)."""
    counts: dict = {}
    for c, a in zip(ev.causes, ev.true_ahu_of):
        if c[0] == ECON:
            counts[a] = counts.get(a, 0) + 1
    return any(v >= 2 for v in counts.values())


def score_econ(res: dict, ev: W.Event) -> dict:
    """Per event: overall (correct, wrong_confident) as `study_joint.score`, plus the same restricted to complaints whose true cause is `econ_fault`."""
    ok = [g == t for g, t in zip(res["guess"], ev.causes)]
    conc = res["concluded"]
    is_econ = [t[0] == ECON for t in ev.causes]
    return dict(n=len(ok), correct=sum(ok), wc=sum(1 for o, c in zip(ok, conc) if c and not o), concluded=sum(conc),
                econ_n=sum(is_econ), econ_correct=sum(o for o, e in zip(ok, is_econ) if e), econ_wc=sum(1 for o, c, e in zip(ok, conc, is_econ) if e and c and not o))


def run_cell_econ(n: int = N_EPISODES) -> dict:
    """`n` events from the econ-aware primary-cell world, both tiers, both policies. Raw arrays only, mirroring `study_joint.run_cell`."""
    cases = make_cases_econ()
    wp = wp_econ()
    js = js_econ()
    events = [W.draw_event(IDX, i, wp, cases, extra_causes=(C.ECON_FAULT,), shares=ECON_SHARES) for i in range(n)]
    out = dict(idx=IDX, n=n, tag=tool_settings_tag_econ(), n_compl=np.array([e.n for e in events]), kind=np.array([e.kind for e in events]),
               econ_shared=np.array([econ_shared(e) for e in events]), pol={})
    for ti, tier in enumerate(TIERS):
        for pol in POLICIES:
            keys = ("minutes", "checks", "correct", "wc", "concluded", "econ_n", "econ_correct", "econ_wc")
            cols = {k: [] for k in keys}
            for i, ev in enumerate(events):
                cs = [cases[(tier, r)] for r in ev.rooms]
                ctxs = [W.context_dict(tier, r) for r in ev.rooms]
                oracle = W.Oracle(ev, wp.rel_a, np.random.default_rng([SEED, IDX, 100 + 10 * ti + P.POLICY_INDEX[pol], i]), checks=ECON_CHECKS)
                r = P.run_policy(pol, cs, oracle, ctxs, js)
                sc = score_econ(r, ev)
                cols["minutes"].append(r["minutes"])
                cols["checks"].append(r["n_checks"])
                for k in keys[2:]:
                    cols[k].append(sc[k])
            out["pol"][(tier, pol)] = {k: np.array(v, float) for k, v in cols.items()}
    return out


def run_reference_low_static(n: int = N_EPISODES) -> dict:
    """The DEFAULT (non-econ, 2-state) primary-cell world, `tool_joint2`/`tool_ticket_memo2`, `n` fresh events: the wrong-and-confident rate on complaints whose true cause is
    `low_static`, the reference P4 compares `econ_fault`'s rate against. A separate draw (a fresh `idx`), not Addendum 31's own stored events, so no stored file is required to run this."""
    cases = W.make_cases()
    wp = W.WorldParams(F0, Q_AHU0, P_WRONG0, REL_A0)
    events = [W.draw_event(IDX + 1, i, wp, cases) for i in range(n)]
    out = {}
    for ti, tier in enumerate(TIERS):
        for pol in POLICIES:
            n_low = wc_low = 0
            for i, ev in enumerate(events):
                cs = [cases[(tier, r)] for r in ev.rooms]
                ctxs = [W.context_dict(tier, r) for r in ev.rooms]
                oracle = W.Oracle(ev, wp.rel_a, np.random.default_rng([SEED, IDX + 1, 100 + 10 * ti + P.POLICY_INDEX[pol], i]))
                r = P.run_policy(pol, cs, oracle, ctxs)
                ok = [g == t for g, t in zip(r["guess"], ev.causes)]
                is_low = [t[0] == "low_static" for t in ev.causes]
                n_low += sum(is_low)
                wc_low += sum(1 for o, c, low in zip(ok, r["concluded"], is_low) if low and c and not o)
            out[(tier, pol)] = wc_low / n_low if n_low else float("nan")
    return out


# ---------------------------------------------------------------------------------------------- gates
def gate_g1_additive(n_events: int = 200) -> tuple[bool, str]:
    """Regression (the addendum's P1): with no extra state requested, `tool_joint2`/`tool_ticket_memo2` on Addendum 30's own primary cell reproduce Addendum 31's stored minutes and
    correct counts exactly. A failed gate here means the additive refactor of joint.py/world2.py was not actually a no-op; nothing past this gate is meaningful."""
    from . import study_joint as J
    from . import study_joint2 as J2
    import pickle
    if not J2.RAW30.exists():
        return False, "Addendum 30's stored raw results are not available"
    raw30 = pickle.loads(J2.RAW30.read_bytes())
    ok, detail = J2.gate_g1(raw30, raw30, n_events)
    return ok, "tool_joint/tool_ticket_memo vs Addendum 30's stored results: " + detail


def gate_g2_probabilities() -> tuple[bool, str]:
    """Every probability this addendum adds is internally consistent: `make_prior_v1`'s own normalisation (not a pre-summed-to-1 `shares` dict: `ECON_SHARES` adds `econ_fault`'s share
    on top of `DEFAULT_SHARES`, which already summed to 1, and relies on `total[lump]` to renormalise) produces a prior that sums to 1 with `econ_fault` enrolled, and the three-way `f`
    split sums to `f`."""
    try:
        causes, prior = C.make_prior_v1(["VAV-0"], "VAV-0", W.tool_settings(), shares=ECON_SHARES, extra_causes=(C.ECON_FAULT,))
        prior_ok = abs(prior.sum() - 1.0) < 1e-9 and (ECON,) in causes and prior[causes.index((ECON,))] > 0
    except ValueError as e:
        return False, f"a prior with econ_fault enrolled could not be built: {e}"
    js = js_econ()
    f_ok = abs(js.state_prior.sum() - 1.0) < 1e-9 and abs(js.state_prior[1:].sum() - js.f) < 1e-9
    return prior_ok and f_ok, f"a prior with econ_fault enrolled sums to 1 and gives it positive mass: {prior_ok}; the f-split sums to f: {f_ok}"


def gate_g3_replay(res: dict, cases: dict, per: int = 10) -> tuple[bool, str]:
    """Replay: the first `per` events of each policy and tier, fed only their recorded answers, ask for the same checks in the same order and end with the same guess."""
    from .policies import PriorSession
    bad = 0
    wp = wp_econ()
    events = [W.draw_event(IDX, i, wp, cases, extra_causes=(C.ECON_FAULT,), shares=ECON_SHARES) for i in range(per)]
    js = js_econ()
    for ti, tier in enumerate(TIERS):
        for pol in POLICIES:
            for i, ev in enumerate(events):
                cs = [cases[(tier, r)] for r in ev.rooms]
                ctxs = [W.context_dict(tier, r) for r in ev.rooms]
                oracle = W.Oracle(ev, wp.rel_a, np.random.default_rng([SEED, IDX, 100 + 10 * ti + P.POLICY_INDEX[pol], i]), checks=ECON_CHECKS)
                r = P.run_policy(pol, cs, oracle, ctxs, js)
                trace = TraceOracle(r["trace"], cs)
                r2 = P.run_policy(pol, cs, trace, ctxs, js)
                if r2["minutes"] != r["minutes"] or r2["guess"] != r["guess"]:
                    bad += 1
    return bad == 0, f"{bad} of {2 * len(TIERS) * per} replays differ"


class TraceOracle:
    """Answers a check from a pre-recorded trace, in order, ignoring its own arguments (Addendum 30's replay pattern)."""

    def __init__(self, trace: list, cases: list):
        self.trace, self.pos, self.cases = list(trace), 0, cases

    def _next(self):
        item = self.trace[self.pos] if self.pos < len(self.trace) else None
        self.pos += 1
        return item

    def ask_room(self, i, ck, target):
        item = self._next()
        return item[-1] if item is not None else "unsure"

    def ask_ahu(self, a, ck):
        item = self._next()
        return item[-1] if item is not None else "unsure"


def gate_g4_reproducible(res: dict, n: int = 30) -> tuple[bool, str]:
    """Reproducibility: re-running with `n` events reproduces the first `n` events of `res` (the cell's own, already-computed, full run)."""
    n = min(n, res["n"])
    again = run_cell_econ(n)
    bad = [k for k in again["pol"] if not np.array_equal(again["pol"][k]["minutes"], res["pol"][k]["minutes"][:n])]
    return not bad, f"{len(bad)} policy/tier series differ in the first {n} events"


def gate_g5_complete(res: dict, n: int) -> tuple[bool, str]:
    ok = res["n"] == n and set(res["pol"]) == {(t, p) for t in TIERS for p in POLICIES} and all(np.isfinite(v["minutes"]).all() and (v["minutes"] >= 0).all() for v in res["pol"].values())
    return ok, f"{res['n']} events, {len(res['pol'])} policy/tier series"


def gates(res: dict, cases: dict, g1_events: int = 200) -> dict:
    g1 = gate_g1_additive(g1_events)
    g2 = gate_g2_probabilities()
    g3 = gate_g3_replay(res, cases)
    g4 = gate_g4_reproducible(res)
    g5 = gate_g5_complete(res, res["n"])
    return {"G1 the extension is additive": g1, "G2 probabilities are consistent": g2, "G3 replay": g3, "G4 reproducibility": g4, "G5 completeness": g5}


# ---------------------------------------------------------------------------------------------- analysis
def summarize(res: dict, tier: str, pol: str, mask: np.ndarray) -> dict:
    v, n_compl = res["pol"][(tier, pol)], res["n_compl"]
    if not mask.any():
        return dict(n=0)
    econ_n = v["econ_n"][mask].sum()
    return dict(n=int(mask.sum()), minutes=float(v["minutes"][mask].mean()), checks=float(v["checks"][mask].mean()), accuracy=float((v["correct"][mask] / n_compl[mask]).mean()),
                wrong_confident=float(v["wc"][mask].sum() / n_compl[mask].sum()), econ_n=int(econ_n),
                econ_accuracy=float(v["econ_correct"][mask].sum() / econ_n) if econ_n else float("nan"),
                econ_wrong_confident=float(v["econ_wc"][mask].sum() / econ_n) if econ_n else float("nan"))


def analyze(res: dict, ref_low_static: dict) -> dict:
    masks = {"all": np.ones(res["n"], bool), "shared": res["kind"] == "shared", "multi": res["kind"] == "multi", "single": res["kind"] == "single",
             "econ_shared": res["econ_shared"]}
    summ = {(tier, pol, sub): summarize(res, tier, pol, masks[sub]) for tier in TIERS for pol in POLICIES for sub in list(SUBSETS) + ["econ_shared"]}
    return dict(summary=summ, econ_shared_n=int(masks["econ_shared"].sum()), ref_low_static=ref_low_static)


def predictions(res: dict, an: dict, gate_results: dict) -> dict:
    p1_ok, p1_detail = gate_results["G1 the extension is additive"]
    out = {"P1 additive (gate)": (p1_ok, p1_detail)}
    for tier in TIERS:
        s = an["summary"][(tier, "tool_ticket_memo2", "all")]
        acc = s.get("econ_accuracy", float("nan"))
        out[f"P2 diagnosable at {tier} (>=70% correct on econ-caused complaints)"] = (bool(acc == acc and acc >= 0.70), f"econ_accuracy={acc:.2f} on {s.get('econ_n', 0)} complaints" if s.get("n") else "no data")
    for tier in TIERS:
        r = an["summary"][(tier, "tool_joint2", "econ_shared")]
        m = an["summary"][(tier, "tool_ticket_memo2", "econ_shared")]
        if r.get("n", 0) == 0 or m.get("n", 0) == 0:
            out[f"P3 the routine at {tier} (<=130% of joint2's minutes on econ-shared visits)"] = (None, f"{r.get('n', 0)} econ-shared events: not enough to say")
        else:
            ratio = m["minutes"] / r["minutes"]
            out[f"P3 the routine at {tier} (<=130% of joint2's minutes on econ-shared visits)"] = (bool(ratio <= 1.30), f"routine/joint2 minutes = {ratio:.2f} ({m['minutes']:.0f} / {r['minutes']:.0f} min, n={r['n']})")
    for tier in TIERS:
        s = an["summary"][(tier, "tool_ticket_memo2", "all")]
        econ_wc, low_wc = s.get("econ_wrong_confident", float("nan")), an["ref_low_static"].get((tier, "tool_ticket_memo2"), float("nan"))
        ok = econ_wc == econ_wc and low_wc == low_wc and econ_wc <= low_wc + 0.02
        out[f"P4 safety at {tier} (econ wrong-and-confident <= low_static's + 2 points)"] = (bool(ok), f"econ={econ_wc:.3f}, low_static reference={low_wc:.3f}" if econ_wc == econ_wc else "no data")
    return out


def decision(preds: dict) -> str:
    if preds["P1 additive (gate)"][0] is not True:
        return "NO RESULT (P1 failed: the extension is not additive)"
    p4 = [v[0] for k, v in preds.items() if k.startswith("P4")]
    if any(v is False for v in p4):
        return "UNSAFE"
    p3 = [v[0] for k, v in preds.items() if k.startswith("P3")]
    if all(v is True for v in p3):
        return "THE ROUTINE STILL CAPTURES IT"
    if any(v is False for v in p3):
        return "THE ROUTINE NEEDS HELP FOR THIS CAUSE"
    return "NOT ENOUGH ECON-SHARED EVENTS TO SAY"
