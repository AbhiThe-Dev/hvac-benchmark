"""100-visit simulation of the bldg11 scenario, exactly as frozen in SIM_PROTOCOL.md (read that first; this file implements it and changes nothing in it).

  .venv/bin/python doc_mismatch/live_demo_bldg11/simulate.py                       # the registered run: 100 visits, refuses to run if SIM_PROTOCOL.md changed since it was frozen
  .venv/bin/python doc_mismatch/live_demo_bldg11/simulate.py --smoke --out DIR     # plumbing check on 6 visits: prints timings and gates only, never accuracy; numbers are meaningless

Outputs (results/docmismatch/bldg11_sim/): complaints.csv (one row per world x policy x visit x complaint), summary.json, report.md.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
import zlib
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from docmismatch.troubleshoot import model as M  # noqa: E402
from docmismatch.troubleshoot.v1 import catalogue as K  # noqa: E402
from docmismatch.troubleshoot.v1 import data as D  # noqa: E402
from docmismatch.troubleshoot.v1.engine import make_case_v1  # noqa: E402
from docmismatch.troubleshoot.v2.joint import JointSettings  # noqa: E402
from docmismatch.troubleshoot.v2.policies import run_policy  # noqa: E402

import visit as V  # noqa: E402
from world import ScriptedWorld, load_scenario  # noqa: E402

PROTOCOL, FROZEN = HERE / "SIM_PROTOCOL.md", HERE / "SIM_PROTOCOL.sha256"
OUT = ROOT.parent / "results" / "docmismatch" / "bldg11_sim"
SEED = 20261011
N_VISITS, N_SHARED, N_COMPLAINTS = 100, 50, 6
SHARED_AHU, OTHER_AHU = "AHU06", "AHU05"
LOCAL_CAUSES = ("actuator_fail", "damper_mech", "no_power", "signal_fault", "controller_comms", "controller_config", "flow_sensor", "zone_sensor_setpoint", "duct_diffuser",
                "capacity_design", "reheat_fail")
P_DOC_WRONG, P_UNLISTED = 0.10, 0.10
WORLDS = {"W0": 0.0, "W1": 0.25}                                   # reliability a: every response probability moved this far toward 0.5
R_LOW = {"tool_shipped": None, "tool_adjusted": 0.10, "tool_r0.25": 0.25, "tool_r0.05": 0.05}
STANDINS = ("fast_ticket", "fast_parent")
POLICIES = tuple(R_LOW) + STANDINS
SCORED = ("tool_shipped", "tool_adjusted") + STANDINS
CTX = dict(reheat="yes", bas_access="yes", instrument="yes", occupant="no")
N_BOOT = 2000


# ---------------------------------------------------------------------------------------------- the tool's cases (identical to the demo's)
def make_cases() -> dict:
    b = V.load_building()
    ctx = D.Context(**CTX)
    return {r: make_case_v1(b, r, V.ITEMS, V.SETTINGS, context=ctx, checks=V.CHECKS, min_rate=V.MIN_RATE) for r in b.base.claims["vav_zone"]}


# ---------------------------------------------------------------------------------------------- the visits
def draw_visit(v: int, cases: dict) -> dict:
    rng = np.random.default_rng([SEED, v, 0])
    shared = v < N_SHARED
    rooms = sorted(cases)
    by_ahu = {a: [r for r in rooms if cases[r].ahu == a] for a in (SHARED_AHU, OTHER_AHU)}
    if shared:
        k = (3, 4, 5)[v % 3]
        sh = [by_ahu[SHARED_AHU][i] for i in rng.choice(len(by_ahu[SHARED_AHU]), k, replace=False)]
        pool = [r for r in rooms if r not in sh]
        loc = [pool[i] for i in rng.choice(len(pool), N_COMPLAINTS - k, replace=False)]
    else:
        k, sh = 0, []
        loc = [rooms[i] for i in rng.choice(len(rooms), N_COMPLAINTS, replace=False)]
    items = [(r, ("low_static",)) for r in sh]
    for r in loc:
        if rng.random() < P_DOC_WRONG:
            alts = cases[r].candidates[1:]
            items.append((r, ("unlisted",) if rng.random() < P_UNLISTED else ("wrong", alts[int(rng.integers(len(alts)))])))
        else:
            items.append((r, (LOCAL_CAUSES[int(rng.integers(len(LOCAL_CAUSES)))],)))
    order = rng.permutation(len(items))
    items = [items[int(i)] for i in order]
    return dict(v=v, kind="shared" if shared else "local", k=k, rooms=[r for r, _ in items], causes=[c for _, c in items],
                ahu_state={SHARED_AHU: "low_static" if shared else "ok", OTHER_AHU: "ok"})


def segment(visit: dict, truth: tuple) -> str:
    return "shared" if truth == ("low_static",) else "local_in_shared" if visit["kind"] == "shared" else "local_in_local"


# ---------------------------------------------------------------------------------------------- the simulated technician
def _crc(s: str) -> int:
    return zlib.crc32(s.encode())


class NoisyOracle:
    """Every answer is one draw, a pure function of (seed, visit, world, who, check, target): the same question has the same answer under every policy and in any order."""

    def __init__(self, visit: dict, cases: list, world: int, a: float):
        self.visit, self.cases, self.world = visit, cases, world
        self.tc = {c.name: c for c in K.degrade_all(V.CHECKS, a)}

    def _u(self, tag: str, k1: str, k2: str) -> float:
        return float(np.random.default_rng([SEED, self.visit["v"], self.world, _crc(tag), _crc(k1), _crc(k2)]).random())

    def ask_room(self, i: int, ck: K.CheckV1, target: str) -> str:
        c = self.tc[ck.name]
        p = float(np.clip(K.p_pos(c, self.visit["causes"][i], target, self.cases[i].doc), M.RATE_FLOOR, 1.0 - M.RATE_FLOOR))
        word = ck.words[0] if self._u("room", self.cases[i].member, f"{ck.name}|{target}") < p else ck.words[1]
        assert word in ck.words                                                  # gate G5
        return word

    def ask_ahu(self, a: str, ck: K.CheckV1) -> str:
        c = self.tc[ck.name]
        st = self.visit["ahu_state"][a]
        p = float(np.clip(c.bg if st == "ok" else c.detects.get(st, c.bg), M.RATE_FLOOR, 1.0 - M.RATE_FLOOR))
        word = ck.words[0] if self._u("ahu", a, ck.name) < p else ck.words[1]
        assert word in ck.words
        return word


def run_visit(args) -> dict:
    """One visit under both worlds and every policy. Top-level so a process pool can run it."""
    v, only = args
    cases = _CASES
    visit = draw_visit(v, cases)
    cl = [cases[r] for r in visit["rooms"]]
    out = {"visit": visit, "runs": {}}
    for wname, a in WORLDS.items():
        orc = NoisyOracle(visit, cl, list(WORLDS).index(wname), a)
        for pol in POLICIES:
            if only and pol not in only:
                continue
            if pol in R_LOW:
                js = JointSettings() if R_LOW[pol] is None else JointSettings(r_low=R_LOW[pol])
                r = run_policy("tool_ticket_memo2", cl, orc, [CTX] * len(cl), js)
            else:
                r = run_policy(pol, cl, orc, [CTX] * len(cl))
            out["runs"][(wname, pol)] = dict(minutes=float(r["minutes"]), n_checks=int(r["n_checks"]), guess=[tuple(g) for g in r["guess"]], concluded=[bool(c) for c in r["concluded"]])
    return out


_CASES = None


def _init():
    global _CASES
    _CASES = make_cases()


# ---------------------------------------------------------------------------------------------- gates
def gate_g1() -> tuple[bool, str]:
    """The harness reproduces the demo: scripted modal answers through `run_policy` give the demo's own trace and minutes, for both settings."""
    detail = []
    for model, want in (("shipped", 219.0), ("adjusted", 119.0)):
        vis = V.Visit(model)
        w = ScriptedWorld(vis.scenario, vis.cases)

        class O:
            def ask_room(self, i, ck, target):
                return w.room(i, ck, target)

            def ask_ahu(self, a, ck):
                return w.ahu(a, ck)
        js = V.joint_settings(vis.scenario, model)
        r = run_policy("tool_ticket_memo2", vis.cases, O(), [CTX] * len(vis.cases), js)
        demo = V.autoplay(model)
        mine = [(t[0], t[1], t[3]) for t in r["trace"]]
        theirs = [(t["room"], t["check"], t["answer"]) for t in demo["trace"] if "check" in t]
        ok = mine == theirs and abs(r["minutes"] - demo["done"]["visit_minutes"]) < 1e-6 and abs(r["minutes"] - want) < 1e-6
        detail.append(f"{model}: {'same trace' if mine == theirs else 'TRACE DIFFERS'}, {r['minutes']:.1f} min (demo {demo['done']['visit_minutes']}, want {want})")
        if not ok:
            return False, "; ".join(detail)
    return True, "; ".join(detail)


def gate_g2_oracle() -> tuple[bool, str]:
    cases = make_cases()
    visit = draw_visit(3, cases)
    cl = [cases[r] for r in visit["rooms"]]
    o1, o2 = NoisyOracle(visit, cl, 0, 0.0), NoisyOracle(visit, cl, 0, 0.0)
    qs = [(i, ck, cl[i].doc) for i in range(len(cl)) for ck in V.CHECKS if ck.subject != "ahu" and ck.is_reading]
    fwd = [o1.ask_room(*q) for q in qs]
    rev = [o2.ask_room(*q) for q in reversed(qs)][::-1]
    return fwd == rev, f"{len(qs)} questions asked forward and backward gave {'identical' if fwd == rev else 'DIFFERENT'} answers"


def gate_g3(visits: list) -> tuple[bool, str]:
    for vis in visits:
        if len(vis["rooms"]) != N_COMPLAINTS or len(set(vis["rooms"])) != N_COMPLAINTS:
            return False, f"visit {vis['v']}: rooms not six distinct"
        ls = [r for r, c in zip(vis["rooms"], vis["causes"]) if c == ("low_static",)]
        if vis["kind"] == "shared":
            if vis["k"] not in (3, 4, 5) or len(ls) != vis["k"] or any(_CASES[r].ahu != SHARED_AHU for r in ls):
                return False, f"visit {vis['v']}: shared composition wrong"
        elif ls:
            return False, f"visit {vis['v']}: local visit with a low-static complaint"
    return True, f"{len(visits)} visits: six distinct rooms each; shared visits k in 3..5 all on {SHARED_AHU}; local visits none"


# ---------------------------------------------------------------------------------------------- statistics
def tabulate(results: list) -> dict:
    """{(world, policy): arrays of per-visit counts}"""
    V_ = len(results)
    T = {}
    keys = list(results[0]["runs"])
    for key in keys:
        t = {n: np.zeros(V_) for n in ("n", "correct", "wc", "nc", "nonls", "fsc", "minutes", "checks", "ls_diag")}
        for seg in ("shared", "local_in_shared", "local_in_local", "docwrong"):
            t["n_" + seg], t["c_" + seg] = np.zeros(V_), np.zeros(V_)
        T[key] = t
    rows = []
    for vi, res in enumerate(results):
        vis = res["visit"]
        for key, run in res["runs"].items():
            t = T[key]
            t["minutes"][vi], t["checks"][vi] = run["minutes"], run["n_checks"]
            for j, (truth, guess, conc) in enumerate(zip(vis["causes"], run["guess"], run["concluded"])):
                ok = tuple(guess) == tuple(truth)
                seg = segment(vis, truth)
                t["n"][vi] += 1
                t["correct"][vi] += ok
                t["wc"][vi] += conc and not ok
                t["nc"][vi] += not conc
                if truth != ("low_static",):
                    t["nonls"][vi] += 1
                    t["fsc"][vi] += tuple(guess) == ("low_static",)
                else:
                    t["ls_diag"][vi] += tuple(guess) == ("low_static",)
                for s in (seg,) + (("docwrong",) if truth[0] in ("wrong", "unlisted") else ()):
                    t["n_" + s][vi] += 1
                    t["c_" + s][vi] += ok
                rows.append(dict(world=key[0], policy=key[1], visit=vis["v"], kind=vis["kind"], room=vis["rooms"][j], truth=":".join(truth), guess=":".join(guess), concluded=int(conc),
                                 correct=int(ok), segment=seg))
    return T, rows


def boot_idx() -> np.ndarray:
    return np.random.default_rng([SEED, 999]).integers(0, N_VISITS, size=(N_BOOT, N_VISITS))


def ratio(num: np.ndarray, den: np.ndarray, idx: np.ndarray) -> dict:
    with np.errstate(invalid="ignore", divide="ignore"):
        point = num.sum() / den.sum() if den.sum() else float("nan")
        b = num[idx].sum(axis=1) / den[idx].sum(axis=1)
    lo, hi = np.nanpercentile(b, [2.5, 97.5])
    return dict(p=float(point), lo=float(lo), hi=float(hi))


def mean_ci(x: np.ndarray, idx: np.ndarray) -> dict:
    b = x[idx].mean(axis=1)
    return dict(p=float(x.mean()), lo=float(np.percentile(b, 2.5)), hi=float(np.percentile(b, 97.5)))


def stats_for(T: dict, idx: np.ndarray) -> dict:
    out = {}
    for key, t in T.items():
        s = dict(acc=ratio(t["correct"], t["n"], idx), wc=ratio(t["wc"], t["n"], idx), nc=ratio(t["nc"], t["n"], idx), fsc=ratio(t["fsc"], t["nonls"], idx),
                 minutes=mean_ci(t["minutes"], idx), checks=mean_ci(t["checks"], idx))
        for seg in ("shared", "local_in_shared", "local_in_local", "docwrong"):
            s["acc_" + seg] = ratio(t["c_" + seg], t["n_" + seg], idx)
        s["ls_diag_shared"] = ratio(t["ls_diag"], t["n_shared"], idx)
        out[key] = s
    return out


def paired(T: dict, idx: np.ndarray, world: str, a: str, b: str) -> dict:
    """a minus b on accuracy (points) and on mean minutes, same visits, same resamples."""
    ta, tb = T[(world, a)], T[(world, b)]
    with np.errstate(invalid="ignore", divide="ignore"):
        acc = ta["correct"].sum() / ta["n"].sum() - tb["correct"].sum() / tb["n"].sum()
        ba = ta["correct"][idx].sum(axis=1) / ta["n"][idx].sum(axis=1) - tb["correct"][idx].sum(axis=1) / tb["n"][idx].sum(axis=1)
    mins = (ta["minutes"] - tb["minutes"])
    bm = mins[idx].mean(axis=1)
    return dict(acc=dict(p=float(acc), lo=float(np.percentile(ba, 2.5)), hi=float(np.percentile(ba, 97.5))),
                minutes=dict(p=float(mins.mean()), lo=float(np.percentile(bm, 2.5)), hi=float(np.percentile(bm, 97.5))))


def predictions(S: dict, P: dict) -> list:
    a0, s0, a1 = S[("W0", "tool_adjusted")], S[("W0", "tool_shipped")], S[("W1", "tool_adjusted")]
    d = P["W0:adj-ship"]["acc"]
    return [
        ("P1", "W0: adjusted exceeds shipped by >= 15 points overall, interval lower bound above 0", d["p"] >= 0.15 and d["lo"] > 0, f"difference {100 * d['p']:.1f} points ({100 * d['lo']:.1f} to {100 * d['hi']:.1f})"),
        ("P2", "W0 shared-cause complaints: shipped < 30% and adjusted > 80%", s0["acc_shared"]["p"] < 0.30 and a0["acc_shared"]["p"] > 0.80, f"shipped {100 * s0['acc_shared']['p']:.0f}%, adjusted {100 * a0['acc_shared']['p']:.0f}%"),
        ("P3", "W0: adjusted false shared-cause call rate <= 3%", a0["fsc"]["p"] <= 0.03, f"{100 * a0['fsc']['p']:.1f}% ({100 * a0['fsc']['lo']:.1f} to {100 * a0['fsc']['hi']:.1f})"),
        ("P4", "SAFETY BAR: adjusted wrong-and-confident <= 5% at W0 and <= 10% at W1", a0["wc"]["p"] <= 0.05 and a1["wc"]["p"] <= 0.10, f"W0 {100 * a0['wc']['p']:.1f}% ({100 * a0['wc']['lo']:.1f} to {100 * a0['wc']['hi']:.1f}), W1 {100 * a1['wc']['p']:.1f}% ({100 * a1['wc']['lo']:.1f} to {100 * a1['wc']['hi']:.1f})"),
        ("P5", "adjusted accuracy at W1 is at least 3 points below W0", a0["acc"]["p"] - a1["acc"]["p"] >= 0.03, f"W0 {100 * a0['acc']['p']:.1f}%, W1 {100 * a1['acc']['p']:.1f}%"),
        ("P6", "W0: adjusted mean visit minutes below fast_ticket's", a0["minutes"]["p"] < S[("W0", "fast_ticket")]["minutes"]["p"], f"adjusted {a0['minutes']['p']:.0f}, fast_ticket {S[('W0', 'fast_ticket')]['minutes']['p']:.0f}"),
        ("P7", "W0: adjusted overall accuracy between 65% and 90%", 0.65 <= a0["acc"]["p"] <= 0.90, f"{100 * a0['acc']['p']:.1f}%"),
    ]


def f(x: dict, pct=True) -> str:
    return f"{100 * x['p']:.1f}% ({100 * x['lo']:.0f}-{100 * x['hi']:.0f})" if pct else f"{x['p']:.0f} ({x['lo']:.0f}-{x['hi']:.0f})"


def report(S: dict, P: dict, preds: list, gates: dict, meta: dict) -> str:
    L = ["# bldg11 scenario: 100-visit simulation (SIM_PROTOCOL.md)", "",
         "Layout and point map real (Mortar bldg11, AHU06 and AHU05); visits, causes and answers simulated by me. **W0 is home-field for the tool** (answers drawn from the catalogue's own rates), so a "
         "good W0 number is weak evidence; **W1** moves every response probability 25% toward 0.5. The stand-ins are my constructions. Minutes are placeholders. 95% intervals are a bootstrap "
         "over visits. Nothing here validates the tool or the `r_low = 0.10` setting.", "", f"{meta['n']} visits x 6 complaints = {meta['n'] * 6} complaints per row. Run {meta['when']}, {meta['secs']:.0f} s.", "",
         "## Gates", "", "| gate | result | detail |", "|---|---|---|"]
    for g, (ok, d) in gates.items():
        L.append(f"| {g} | {'PASS' if ok else 'FAIL'} | {d} |")
    for w in WORLDS:
        label = "the tool's own rates" if w == "W0" else "checks less reliable than the tool assumes"
        L += ["", f"## World {w} ({label})", "",
              "| policy | accuracy | wrong-and-confident | not concluded | false shared-cause call | minutes / visit | checks / visit |", "|---|---|---|---|---|---|---|"]
        for pol in POLICIES:
            s = S[(w, pol)]
            tag = " (exploratory)" if pol in ("tool_r0.25", "tool_r0.05") else ""
            L.append(f"| {pol}{tag} | {f(s['acc'])} | {f(s['wc'])} | {f(s['nc']) if pol in R_LOW else 'n/a (always concludes)'} | {f(s['fsc'])} | {f(s['minutes'], False)} | {f(s['checks'], False)} |")
        L += ["", f"Accuracy by segment ({w}):", "", "| policy | shared-cause complaints | local, in shared visits | local, in local visits | documentation-wrong | shared-cause complaints called low static |", "|---|---|---|---|---|---|"]
        for pol in POLICIES:
            s = S[(w, pol)]
            L.append(f"| {pol} | {f(s['acc_shared'])} | {f(s['acc_local_in_shared'])} | {f(s['acc_local_in_local'])} | {f(s['acc_docwrong'])} | {f(s['ls_diag_shared'])} |")
    L += ["", "## Paired differences (same visits, same answers; a minus b)", "", "| world | a - b | accuracy (points) | minutes / visit |", "|---|---|---|---|"]
    for k, v in P.items():
        w, pair = k.split(":")
        L.append(f"| {w} | {pair} | {100 * v['acc']['p']:+.1f} ({100 * v['acc']['lo']:+.0f} to {100 * v['acc']['hi']:+.0f}) | {v['minutes']['p']:+.0f} ({v['minutes']['lo']:+.0f} to {v['minutes']['hi']:+.0f}) |")
    L += ["", "## Predictions (registered before the run)", "", "| # | prediction | result | detail |", "|---|---|---|---|"]
    for pid, text, ok, det in preds:
        L.append(f"| {pid} | {text} | {'HOLDS' if ok else 'DOES NOT HOLD'} | {det} |")
    L += ["", f"Safety bar (P4): **{'SAFE' if preds[3][2] else 'UNSAFE'}** for `tool_adjusted`.", ""]
    return "\n".join(L)


# ---------------------------------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    want = FROZEN.read_text().split()[0]
    have = hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()
    if have != want:
        raise SystemExit("SIM_PROTOCOL.md has changed since it was frozen (SIM_PROTOCOL.sha256): a change after the freeze is a logged deviation, not a silent edit")
    global _CASES
    _init()
    t0 = time.time()
    n = 6 if a.smoke else N_VISITS
    ids = [0, 1, 2, 50, 51, 52] if a.smoke else list(range(N_VISITS))
    gates = {}
    gates["G1 harness = demo"] = gate_g1()
    gates["G2a oracle order-independent"] = gate_g2_oracle()
    with ProcessPoolExecutor(a.workers, initializer=_init) as ex:
        results = list(ex.map(run_visit, [(v, None) for v in ids], chunksize=1))
    visits = [r["visit"] for r in results]
    gates["G3 composition"] = gate_g3(visits)
    expect = len(ids) * len(WORLDS) * len(POLICIES)
    got = sum(len(r["runs"]) for r in results)
    fin = all(np.isfinite(run["minutes"]) for r in results for run in r["runs"].values())
    gates["G4 completeness"] = (got == expect and fin, f"{got} of {expect} (visit, world, policy) runs, minutes finite: {fin}")
    gates["G5 answers in vocabulary"] = (True, "asserted on every draw")
    if a.smoke:
        again = run_visit((ids[0], None))
        same = all(again["runs"][k] == results[0]["runs"][k] for k in again["runs"])
        gates["G2b run twice identical"] = (same, "visit 0, every world and policy")
    else:
        again = [run_visit((v, None)) for v in (0, 1, 2, 50, 51)]
        same = all(x["runs"][k] == results[r]["runs"][k] for x, r in zip(again, (0, 1, 2, 50, 51)) for k in x["runs"])
        gates["G2b run twice identical"] = (same, "visits 0, 1, 2, 50, 51: every world and policy")
    secs = time.time() - t0
    if a.smoke:
        print(f"SMOKE ({n} visits, {secs:.0f} s) -- gates only, accuracy deliberately not printed")
        for g, (ok, d) in gates.items():
            print(f"  {g}: {'PASS' if ok else 'FAIL'} - {d}")
        return
    if not all(ok for ok, _ in gates.values()):
        for g, (ok, d) in gates.items():
            print(f"  {g}: {'PASS' if ok else 'FAIL'} - {d}")
        raise SystemExit("a gate failed: NO RESULT")
    T, rows = tabulate(results)
    idx = boot_idx()
    S = stats_for(T, idx)
    P = {}
    for w in WORLDS:
        P[f"{w}:adj-ship"] = paired(T, idx, w, "tool_adjusted", "tool_shipped")
        P[f"{w}:adj-fast_ticket"] = paired(T, idx, w, "tool_adjusted", "fast_ticket")
        P[f"{w}:adj-fast_parent"] = paired(T, idx, w, "tool_adjusted", "fast_parent")
        P[f"{w}:ship-fast_ticket"] = paired(T, idx, w, "tool_shipped", "fast_ticket")
    preds = predictions(S, P)
    a.out.mkdir(parents=True, exist_ok=True)
    with open(a.out / "complaints.csv", "w", newline="") as fh:
        w_ = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w_.writeheader()
        w_.writerows(rows)
    meta = dict(n=N_VISITS, when=time.strftime("%Y-%m-%d"), secs=secs)
    (a.out / "summary.json").write_text(json.dumps(dict(meta=meta, stats={f"{k[0]}|{k[1]}": v for k, v in S.items()}, paired=P,
                                                         predictions=[dict(id=p, text=t, holds=bool(ok), detail=d) for p, t, ok, d in preds], protocol_sha256=have), indent=1))
    (a.out / "report.md").write_text(report(S, P, preds, gates, meta))
    print("wrote", a.out / "report.md")


if __name__ == "__main__":
    main()
