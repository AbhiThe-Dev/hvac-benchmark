"""Does a less conservative stopping rule, on its own, recover the language model's T2 speed edge over the routine? (PREREGISTRATION_DR.md Addendum 34.) A parameter sweep of the tool's own
engine (`tau`, `min_rate`) on Addendum 30's primary cell at T2; no LLM. Simulation only; nothing here is evidence about real technicians.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from .. import model as M
from .. import study as S
from .. import study_rating as SG
from ..v1.engine import make_case_v1
from ..v1.study_fast_v1 import break_even
from . import policies as P
from . import study_joint as J
from . import world2 as W
from .joint import JointSettings
from .study_llm import TableOracle

# ---------------------------------------------------------------------------------------------- frozen constants (Addendum 34)
SEED = 34
TIER = "T2"
N_EPISODES = J.N_EPISODES                  # 1000, Addendum 30's primary-cell size
BOOT_B = J.BOOT_B
PRIMARY_IDX = next(i for i, c in enumerate(J.all_cells()) if c.is_primary)
BASE_TAU, BASE_MIN_RATE = M.Settings().tau, 0.003
TAU_GRID = (0.99, 0.95, 0.90, 0.85, 0.80, 0.75, 0.70, 0.60, 0.50)
MIN_RATE_GRID = (0.003, 0.01, 0.02, 0.05, 0.10)
TIME_R, ACC_TOL, SAFE_TOL = SG.TIME_R, SG.ACC_TOL, SG.SAFE_TOL
RECOVER_BAR = 0.085                        # half of Addendum 33's measured T2 gap (17%)


def world():
    cases = W.make_cases()
    wp = J.all_cells()[PRIMARY_IDX].params()
    events = [W.draw_event(PRIMARY_IDX, i, wp, cases) for i in range(N_EPISODES)]
    return cases, wp, events


def cases_with(tau: float = BASE_TAU, min_rate: float = BASE_MIN_RATE) -> dict:
    """{room -> CaseV1}, tier T2, the routine's engine with `tau` and `min_rate` swept; everything else (drawings rating, checks, priors) is the tool's own."""
    bld = W.make_building2()
    s = replace(W.tool_settings(), tau=tau)
    return {r: make_case_v1(bld, f"Room-{r}", W.TIER_ITEMS[TIER], settings=s, context=W.tier_context(TIER, r), member_name=f"Room {r}", min_rate=min_rate) for r in range(W.N_BOX)}


def run_variant(cases_by_room: dict, wp: W.WorldParams, events: list) -> dict:
    """The routine (`tool_ticket_memo2`) worked over every event with this variant's cases; identical answers to identical questions (`TableOracle`), whatever the variant."""
    js = JointSettings()
    mins, chk, ok, wc, cn = [], [], [], [], []
    for ev in events:
        cs = [cases_by_room[r] for r in ev.rooms]
        ctxs = [W.context_dict(TIER, r) for r in ev.rooms]
        r = P.run_policy("tool_ticket_memo2", cs, TableOracle(ev, wp.rel_a), ctxs, js)
        a, b, c = J.score(r, ev)
        mins.append(r["minutes"])
        chk.append(r["n_checks"])
        ok.append(a)
        wc.append(b)
        cn.append(c)
    n = np.array([e.n for e in events], float)
    return dict(minutes=np.array(mins, float), checks=np.array(chk, float), correct=np.array(ok, float), wc=np.array(wc, float), concluded=np.array(cn, float), n=n)


def summarize(v: dict) -> dict:
    return dict(minutes=float(v["minutes"].mean()), checks=float(v["checks"].mean()), accuracy=float((v["correct"] / v["n"]).mean()), wrong_confident=float((v["wc"] / v["n"]).mean()),
                concluded=float((v["concluded"] / v["n"]).mean()))


def compare(a: dict, base: dict, boot: np.ndarray) -> dict:
    """`a` minus the baseline variant, paired on the same events (Addendum 21's labels)."""
    acc_a, acc_b = a["correct"] / a["n"], base["correct"] / base["n"]
    wc_a, wc_b = a["wc"] / a["n"], base["wc"] / base["n"]
    d_min, d_acc, d_wc = a["minutes"] - base["minutes"], acc_a - acc_b, wc_a - wc_b
    ci_min, ci_acc, ci_wc = S.paired_ci(d_min, boot), S.paired_ci(d_acc, boot), S.paired_ci(d_wc, boot)
    r_min = float(d_min.mean() / base["minutes"].mean())
    ts, as_ = SG.time_state(r_min, ci_min), SG.acc_state(float(d_acc.mean()), ci_acc)
    kind, wstar = break_even(float(a["minutes"].mean()), float(acc_a.mean()), float(base["minutes"].mean()), float(acc_b.mean()))
    return dict(d_min=float(d_min.mean()), r_min=r_min, d_acc=float(d_acc.mean()), d_wc=float(d_wc.mean()), ci_min=ci_min, ci_acc=ci_acc, ci_wc=ci_wc, time=ts, acc=as_,
                label=SG.label(ts, as_), safety=SG.safety_flag(float(d_wc.mean()), ci_wc), break_even=kind, wrong_cost=wstar)


def run_sweep(events: list | None = None, wp: W.WorldParams | None = None, n: int = N_EPISODES) -> dict:
    """{"tau": {tau: raw}, "min_rate": {rate: raw}}, plus the shared `events`/`wp` (so a caller can re-check gates on them)."""
    _, wp0, events0 = world()
    events, wp = (events0[:n], wp0) if events is None else (events, wp)
    tau_raw = {tau: run_variant(cases_with(tau=tau), wp, events) for tau in TAU_GRID}
    rate_raw = {r: run_variant(cases_with(min_rate=r), wp, events) for r in MIN_RATE_GRID if r != BASE_MIN_RATE}
    rate_raw[BASE_MIN_RATE] = tau_raw[BASE_TAU]
    return dict(events=events, wp=wp, tau=tau_raw, min_rate=rate_raw)


def analyze(sweep: dict, B: int = BOOT_B) -> dict:
    n = len(sweep["events"])
    boot = np.random.default_rng([SEED, 99]).integers(0, n, (B, n))
    base = sweep["tau"][BASE_TAU]
    out = dict(base=base, boot=boot)
    for axis in ("tau", "min_rate"):
        out[axis] = {k: dict(raw=v, sum=summarize(v), cmp=compare(v, base, boot)) for k, v in sweep[axis].items()}
    return out


def predictions(an: dict) -> dict:
    tau = sorted(TAU_GRID)                                    # ascending; minutes should fall as tau falls, i.e. rise along this list reversed
    mins_desc = [an["tau"][t]["sum"]["minutes"] for t in sorted(TAU_GRID, reverse=True)]      # tau descending 0.99 -> 0.50
    accs_desc = [an["tau"][t]["sum"]["accuracy"] for t in sorted(TAU_GRID, reverse=True)]
    p = {}
    p["P1"] = (all(mins_desc[i] <= mins_desc[i - 1] + 1e-9 for i in range(1, len(mins_desc))), f"minutes by tau (0.99->0.50): {[round(m, 1) for m in mins_desc]}")
    p["P2"] = (all(accs_desc[i] <= accs_desc[i - 1] + 1e-9 for i in range(1, len(accs_desc))), f"accuracy by tau (0.99->0.50): {[round(a, 3) for a in accs_desc]}")
    e90 = an["tau"][0.90]["cmp"]
    p["P3"] = (e90["time"] == "FASTER" and e90["acc"] != "LESS", f"tau=0.90: {100 * e90['r_min']:+.0f}% minutes, accuracy {e90['acc']}")
    best = max(an["tau"].values(), key=lambda v: -v["cmp"]["r_min"])
    hit = any(v["cmp"]["r_min"] <= -RECOVER_BAR and v["cmp"]["acc"] != "LESS" and v["cmp"]["d_wc"] < SAFE_TOL for v in an["tau"].values())
    p["P4"] = (hit, f"best tau's minutes: {100 * best['cmp']['r_min']:+.0f}%, accuracy {best['cmp']['acc']}, d_wc {best['cmp']['d_wc']:+.3f}")
    e99 = an["tau"][0.99]["cmp"]
    p["P5"] = (e99["d_min"] >= 0, f"tau=0.99: {e99['d_min']:+.1f} min")
    return p


def decision(an: dict) -> str:
    def ok(v):
        return v["cmp"]["time"] == "FASTER" and v["cmp"]["r_min"] <= -TIME_R and v["cmp"]["acc"] != "LESS" and v["cmp"]["d_wc"] < SAFE_TOL

    largely = any(v["cmp"]["r_min"] <= -RECOVER_BAR and ok(v) for v in an["tau"].values())
    partly = any(ok(v) for v in an["tau"].values())
    if largely:
        return "THE STOPPING RULE LARGELY EXPLAINS IT"
    if partly:
        return "THE STOPPING RULE PARTLY EXPLAINS IT"
    return "THE STOPPING RULE DOES NOT EXPLAIN IT"


# ---------------------------------------------------------------------------------------------- gates
def gate_g1(events: list, n: int = 50) -> tuple[bool, str]:
    import pickle
    from pathlib import Path
    raw30 = Path(__file__).resolve().parents[5] / "results" / "docmismatch" / "troubleshoot_joint" / "joint_raw.pkl"
    if not raw30.exists():
        return False, f"Addendum 30's raw results are needed: {raw30}"
    stored = next(r for r in pickle.loads(raw30.read_bytes()) if r["idx"] == PRIMARY_IDX)
    ok = all(events[i].kind == stored["kind"][i] for i in range(n))
    return ok, f"first {n} of {len(events)} events match Addendum 30's stored primary-cell kinds"


def gate_g2(an: dict) -> tuple[bool, str]:
    base = an["tau"][BASE_TAU]["sum"]
    stored_min, stored_acc = 112.0, 0.80                   # Addendum 31, primary cell, T2, tool_ticket_memo2, all events (results/docmismatch/troubleshoot_joint2/joint2_report.md)
    ok = abs(base["minutes"] - stored_min) / stored_min < 0.05 and abs(base["accuracy"] - stored_acc) < 0.05
    return ok, f"baseline (tau={BASE_TAU}, min_rate={BASE_MIN_RATE}): {base['minutes']:.1f} min / {base['accuracy']:.0%} against Addendum 31's {stored_min:.0f} min / {stored_acc:.0%}"


def gate_g3() -> tuple[bool, str]:
    cases, wp, events = world()
    ev = events[0]
    cs = [cases[(TIER, r)] for r in ev.rooms]
    qs = [(i, ck) for i, c in enumerate(cs) for ck in c.checks if ck.subject != "ahu"][:60]
    a = [TableOracle(ev, wp.rel_a).ask_room(i, ck, cs[i].doc) for i, ck in qs]
    b = [TableOracle(ev, wp.rel_a).ask_room(i, ck, cs[i].doc) for i, ck in reversed(qs)][::-1]
    return a == b, "the answer table is deterministic and independent of question order"


def gate_g4(an: dict) -> tuple[bool, str]:
    e = an["tau"][0.99]["cmp"]
    return e["d_min"] >= -1e-9, f"tau=0.99 against baseline: {e['d_min']:+.1f} min (should not be faster)"


def gate_g5(sweep_a: dict, sweep_b: dict) -> tuple[bool, str]:
    ok = all(np.array_equal(sweep_a["tau"][t]["minutes"], sweep_b["tau"][t]["minutes"]) for t in TAU_GRID)
    return ok, "the sweep reproduces exactly on a second run with the same seed"
