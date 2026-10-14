"""Part B of TREND_NOTES.md (EXPLORATORY; protocol and predictions hashed before any trend-window value was computed): what the trend-window rates measured on the LBNL simulated data do to the demo's visit.

  .venv/bin/python doc_mismatch/live_demo_bldg11/study_trend.py        # needs results/docmismatch/trend_study/trend_pfpu_summary.json (run trend_pfpu.py first)

Arms (tool and world use the arm's catalogue; W1 degrades the world's rates by 25%):
  base            the catalogue as shipped
  snapshot-meas.  (added after Part A, before Part B ran, to separate "the assumption was wrong" from "a trend is sharper") the mapped pairs take the SNAPSHOT rates measured on the simulated data
  trend           the mapped pairs take the 24 h window rates, bas_airflow / bas_reheat cost 4 minutes instead of 2; trend_2min and trend_8min are the time sensitivities
  sharp10, sharp25  CONTEXT, not measured by this data: every reading check 10% / 25% sharper
"""
import dataclasses
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import simulate as S  # noqa: E402
import visit as V  # noqa: E402
import world as Wd  # noqa: E402
from docmismatch.troubleshoot.v1 import catalogue as K  # noqa: E402
from docmismatch.troubleshoot.v1.engine import make_case_v1  # noqa: E402
from docmismatch.troubleshoot.v2.policies import run_policy  # noqa: E402

OUT = HERE.parent.parent / "results" / "docmismatch" / "trend_study"
STORED = {"W0": 0.7483333333333333, "W1": 0.5466666666666666}
WORLDS = {"W0": (0, 0.0), "W1": (1, 0.25)}
CLIP = (0.05, 0.95)
MAP_AIR = {"damper_stuck": ("actuator_fail", "damper_mech", "no_power", "signal_fault"), "airflow_bias": ("flow_sensor",), "pi2_unstable": ("controller_config",)}
MAP_RH = {"reheat_valve": ("reheat_fail",)}


def clip(x):
    return float(min(max(x, CLIP[0]), CLIP[1]))


def with_rates(checks, rates, do_min=None):
    out = []
    for c in checks:
        if c.name == "bas_airflow":
            d = dict(c.detects)
            for fam, causes in MAP_AIR.items():
                for cause in causes:
                    d[cause] = clip(rates[fam])
            c = dataclasses.replace(c, detects=d, do_min=c.do_min if do_min is None else do_min)
        elif c.name == "bas_reheat":
            d = dict(c.detects)
            for fam, causes in MAP_RH.items():
                for cause in causes:
                    d[cause] = clip(rates[fam])
            c = dataclasses.replace(c, detects=d, do_min=c.do_min if do_min is None else do_min)
        out.append(c)
    return tuple(out)


def shift(check, a):
    """Every rate moves the fraction `a` of the way toward 0.5 (a < 0: away from it); the same function as sweep_reliability.py."""
    if a == 0.0:
        return check
    f = lambda p: float(np.clip(0.5 + (p - 0.5) * (1.0 - a), S.M.RATE_FLOOR, 1.0 - S.M.RATE_FLOOR))  # noqa: E731
    if check.is_reading:
        return dataclasses.replace(check, detects={k: f(v) for k, v in check.detects.items()}, bg=f(check.bg))
    return dataclasses.replace(check, v0=dataclasses.replace(check.v0, tpr=f(check.v0.tpr), fpr=f(check.v0.fpr)), overrides={k: f(v) for k, v in check.overrides.items()})


def arms(r24, rsnap):
    base = V.CHECKS
    return {"base": base,
            "snapshot-measured": with_rates(base, rsnap),
            "trend": with_rates(base, r24, do_min=4.0),
            "trend_2min": with_rates(base, r24, do_min=2.0),
            "trend_8min": with_rates(base, r24, do_min=8.0),
            "sharp10 (context)": tuple(shift(c, -0.10) for c in base),
            "sharp25 (context)": tuple(shift(c, -0.25) for c in base)}


class ArmOracle(S.NoisyOracle):
    def __init__(self, visit, cases, world, a, checks):
        super().__init__(visit, cases, world, a)
        self.tc = {c.name: c for c in K.degrade_all(checks, a)}


def make_cases(checks):
    b = V.load_building()
    ctx = S.D.Context(**S.CTX)
    return {r: make_case_v1(b, r, V.ITEMS, V.SETTINGS, context=ctx, checks=checks, min_rate=V.MIN_RATE) for r in b.base.claims["vav_zone"]}


def boot(d, B=2000, seed=13):
    rng = np.random.default_rng(seed); n = len(d)
    return np.percentile([d[rng.integers(n, size=n)].mean() for _ in range(B)], [2.5, 97.5])


def main():
    summ = json.load(open(OUT / "trend_pfpu_summary.json"))
    assert summ["gate_ga1"], "Part A's gate failed: NO RESULT"
    r24, rsnap = summ["windows_24h"], summ["snapshot"]
    sc = Wd.load_scenario(); js = V.joint_settings(sc, "mixed")
    S._init()
    A = arms(r24, rsnap)
    rec = {}
    for name, checks in A.items():
        cases = make_cases(checks)
        for wname, (wi, a) in WORLDS.items():
            ok, conc, seg, vis_ix, vmin, vchk, uses = [], [], [], [], [], [], []
            for v in range(100):
                visit = S.draw_visit(v, cases)
                cl = [cases[r] for r in visit["rooms"]]
                orc = ArmOracle(visit, cl, wi, a, checks)
                r = run_policy("tool_ticket_memo2", cl, orc, [S.CTX] * len(cl), js)
                truth = [tuple(c) for c in visit["causes"]]
                ok += [tuple(g) == t for g, t in zip(r["guess"], truth)]; conc += [bool(c) for c in r["concluded"]]
                for room, t in zip(visit["rooms"], truth):
                    sg = S.segment(visit, t)
                    seg.append("shared" if sg == "shared" else "own fault, no shared cause" if sg == "local_in_local" else ("own fault, faulty handler" if cases[room].ahu == S.SHARED_AHU else "own fault, healthy handler"))
                vis_ix += [v] * len(cl); vmin.append(float(r["minutes"])); vchk.append(int(r["n_checks"]))
                uses.append(sum(1 for t in r["trace"] if t[1] in ("bas_airflow", "bas_reheat")))
            rec[wname, name] = dict(ok=np.array(ok), conc=np.array(conc), seg=np.array(seg), visit=np.array(vis_ix), vmin=np.array(vmin), vchk=np.array(vchk), uses=np.array(uses))
    gb1 = {w: abs(rec[w, "base"]["ok"].mean() - STORED[w]) <= 0.002 for w in WORLDS}
    L = ["# Trend-window checks in the visit (exploratory; TREND_NOTES.md hashed before any trend-window value was computed)", "",
         "The same 100 visits (6 rooms each), the demo's mixed setting, `min_rate` 0.02, T3-noattr. Tool and world use the arm's catalogue; W0 = as it says, W1 = every rate 25% toward 0.5. The simulated data are a best case, so the trend rates are upper bounds.", "",
         "## Rates used (mapped pairs only; clipped to [0.05, 0.95])", "", "| catalogue cause(s) | check | catalogue | snapshot measured | 24 h window measured |", "|---|---|---|---|---|"]
    cat = {"damper_stuck": 0.75, "airflow_bias": 0.50, "pi2_unstable": 0.50, "reheat_valve": 0.75}
    for fam, causes in {**MAP_AIR, **MAP_RH}.items():
        L.append(f"| {', '.join(causes)} | {'bas_reheat' if fam == 'reheat_valve' else 'bas_airflow'} | {cat[fam]:.2f} | {clip(rsnap[fam]):.2f} | {clip(r24[fam]):.2f} |")
    L += ["", "## Gates", "", *[f"- GB1 the unmodified catalogue equals the stored mixture-study accuracy, {w}: **{'PASS' if gb1[w] else 'FAIL'}** ({100*rec[w, 'base']['ok'].mean():.2f}%)" for w in WORLDS], "- GB2 every answer in the check's vocabulary: asserted by the oracle", ""]
    if not all(gb1.values()):
        L += ["**REGISTERED OUTCOME: NO RESULT (a gate failed).**", ""]
    SEGS = ["shared", "own fault, faulty handler", "own fault, healthy handler", "own fault, no shared cause"]
    res = {}
    for w in WORLDS:
        b = rec[w, "base"]
        vb = np.array([b["ok"][b["visit"] == v].mean() for v in range(100)])
        L += [f"## {w}", "", "| arm | accuracy | shared | own fault, faulty handler | own fault, healthy handler | own fault, no shared cause | wrong and confident | minutes / visit | bas_airflow + bas_reheat looks / visit | accuracy gain vs base (95% CI) | added minutes (95% CI) | verdict at W0 |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for name in A:
            d = rec[w, name]
            wc = float(((~d["ok"]) & d["conc"]).mean())
            segacc = [100 * d["ok"][d["seg"] == s].mean() for s in SEGS]
            vo = np.array([d["ok"][d["visit"] == v].mean() for v in range(100)])
            gain = 100 * (vo - vb); ci = boot(gain)
            dm = d["vmin"] - b["vmin"]; cim = boot(dm)
            dwc = 100 * (wc - float(((~b["ok"]) & b["conc"]).mean()))
            verdict = "-"
            if name != "base":
                worth = ci[0] > 0 and gain.mean() >= 3 and dm.mean() <= 0.10 * b["vmin"].mean() and dwc <= 1
                trade = ci[0] > 0 and gain.mean() >= 3 and not worth
                verdict = ("WORTH IT" if worth else "TRADE" if trade else "NEITHER") if w == "W0" else "(not part of the verdict)"
            res[w, name] = dict(acc=float(100 * d["ok"].mean()), gain=float(gain.mean()), ci=ci.tolist(), added=float(dm.mean()), wc=100 * wc, dwc=dwc, verdict=verdict, minutes=float(d["vmin"].mean()))
            L.append(f"| {name} | {100*d['ok'].mean():.1f}% | " + " | ".join(f"{x:.1f}%" for x in segacc) + f" | {100*wc:.1f}% | {d['vmin'].mean():.0f} | {d['uses'].mean():.2f} | " + ("-" if name == "base" else f"{gain.mean():+.1f} ({ci[0]:+.1f}, {ci[1]:+.1f})") + " | " + ("-" if name == "base" else f"{dm.mean():+.0f} ({cim[0]:+.0f}, {cim[1]:+.0f})") + f" | {verdict} |")
        L.append("")
    t, s25 = res["W0", "trend"], res["W0", "sharp25 (context)"]
    P = [("B1 (the trend catalogue raises W0 accuracy by 0.5 to 3 points)", 0.5 <= t["gain"] <= 3, f"{t['gain']:+.1f}"),
         ("B2 (every check 25% sharper: W0 accuracy between 82% and 90%, not 90%)", 82 <= s25["acc"] < 90, f"{s25['acc']:.1f}%"),
         ("B3 (the 4-minute trend look changes minutes per visit by less than 5%)", abs(t["added"]) < 0.05 * res["W0", "base"]["minutes"], f"{t['added']:+.0f} min on {res['W0','base']['minutes']:.0f}"),
         ("B4 (wrong-and-confident does not rise by more than 1 point under the trend catalogue)", t["dwc"] <= 1, f"{t['dwc']:+.1f}")]
    L += ["## Predictions (written before any trend-window value was computed)", ""] + [f"- {p}: **{'HELD' if ok else 'FAILED'}** ({d})" for p, ok, d in P]
    L += ["", "Sim conventions that flatter the checks: the oracle answers a room check from the room's own first-order cause; the window rates come from a clean simulation. The 'sharper' rows are not measured by any data.", ""]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "trend_visit_report.md").write_text("\n".join(L))
    (OUT / "trend_visit_summary.json").write_text(json.dumps(dict(gates=dict(gb1={w: bool(x) for w, x in gb1.items()}), results={f"{w}|{n}": v for (w, n), v in res.items()}, protocol_sha256=hashlib.sha256((HERE / "TREND_NOTES.md").read_bytes()).hexdigest()), indent=1))
    print("\n".join(L))


if __name__ == "__main__":
    main()
